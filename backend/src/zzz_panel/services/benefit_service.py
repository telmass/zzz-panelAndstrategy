"""副词条的**边际收益 / 等效 / 优先级验证**。

面板只说明「属性有多少」，不说明「多给 1 条某词条值多少伤害」。配装取舍要的是后者。

定义（与参考项目 ``analyzeDriveDiscStatGains`` 一致）：

    v(T) = score(当前分配 + 1 条 T) − score(当前分配)

即**多给 1 条 T 的伤害增量**。由此得到：

- **边际收益曲线**：v(T) 加到 N 条时的累计增量；
- **等效换算**：1 条 X ≈ v(X) / v(Y) 条 Y；
- **优先级验证**：把攻略页写的「暴击率 > 暴伤 > 攻击力%」逐对拿去比。

> **口径提醒**：这里算的是「多给一条」的边际值，**没有扣掉被替换掉的那条**。
> 固定预算下的**机会成本**由 D1-Main（主词条取舍）那条线处理。
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from ..core import options as option_table
from ..core.damage.targets import STANDARD_TARGET, TargetPreset
from ..core.panel_rows import SUB_STAT_DISPLAY_LABELS
from ..schemas.panel import PanelRequest
from .damage_service import path_for_agent, score_build

#: 副词条 id -> 攻略展示名（与 ``core/options.py`` 的 SUB_STATS 对应）。
SUBSTAT_IDS: tuple[str, ...] = tuple(
    substat.id for substat in option_table.SUB_STATS
)

#: 攻略展示名 -> 副词条 id。攻略页的 ``subPriority`` 用的是展示名。
SUBSTAT_BY_LABEL: dict[str, str] = {
    SUB_STAT_DISPLAY_LABELS[substat.id]: substat.id
    for substat in option_table.SUB_STATS
}

#: 副词条 id -> 每条的数值与种类（用于加一条时的换算）。
SUBSTAT_STEP: dict[str, tuple[float, str]] = {
    substat.id: (float(substat.value), substat.kind) for substat in option_table.SUB_STATS
}


def _with_extra(sub_stats: dict[str, int], substat_id: str, count: int = 1) -> dict[str, int]:
    result = dict(sub_stats)
    result[substat_id] = result.get(substat_id, 0) + count
    return result


def marginal_benefit(
    request: PanelRequest,
    target: TargetPreset = STANDARD_TARGET,
    path: str | None = None,
    level: int = 60,
    max_count: int = 4,
    agent: Any = None,
) -> dict[str, dict[int, float]]:
    """每条副词条的边际收益曲线。

    返回 ``{副词条 id: {加 N 条的累计伤害增量}}``，N 从 1 到 ``max_count``。
    """
    base = score_build(request, target=target, path=path, level=level).total
    curves: dict[str, dict[int, float]] = {}
    for substat_id in SUBSTAT_IDS:
        curve: dict[int, float] = {}
        for count in range(1, max_count + 1):
            extra = _with_extra(request.sub_stats, substat_id, count)
            variant = request.model_copy(update={"sub_stats": extra})
            total = score_build(variant, target=target, path=path, level=level).total
            curve[count] = total - base
        curves[substat_id] = curve
    return curves


def one_roll_values(
    request: PanelRequest,
    target: TargetPreset = STANDARD_TARGET,
    path: str | None = None,
    level: int = 60,
    agent: Any = None,
) -> dict[str, float]:
    """每条副词条**一条**的伤害价值 v(T)（用于等效换算与优先级比较）。"""
    curves = marginal_benefit(request, target=target, path=path, level=level, max_count=1, agent=agent)
    return {substat_id: curve[1] for substat_id, curve in curves.items()}


def equivalence(
    request: PanelRequest,
    target: TargetPreset = STANDARD_TARGET,
    path: str | None = None,
    level: int = 60,
    baseline: str = "cr",
    agent: Any = None,
) -> dict[str, float]:
    """等效换算：1 条 X ≈ 多少条 ``baseline``。

    ``equivalence[X] = v(X) / v(baseline)``——基准词条自身记 1.0。
    """
    values = one_roll_values(request, target=target, path=path, level=level, agent=agent)
    base_value = values.get(baseline, 0.0)
    if not base_value:
        return {substat_id: 0.0 for substat_id in values}
    return {substat_id: value / base_value for substat_id, value in values.items()}


#: 优先级符号 -> 判定口径。
#:
#: ``>`` 严格优先、``=`` 等价、``≈`` 近似。
PRIORITY_SIGNS = {
    ">": "strict",
    "=": "equal",
    "≈": "close",
}

#: 「=」与「≈」的容差。
#:
#: 「=」是**严格等价**（5% 内）；「≈」是**近似**（35% 内）——
#: 攻略里写「≈」的本来就是「差不多」，用同一个紧容差会把它们全判成不成立。
PRIORITY_TOLERANCE = {"=": 0.05, "≈": 0.35}


def path_for_role(role_tag: str, panel_mode: str = "") -> str:
    """按代理人的**定位**与**面板模式**判断伤害路径。

    口径真源在 :func:`damage_service.path_for_agent`（本函数是它的薄包装）：

    - 面板模式 ``rupture`` → **贯穿路径**；``armorer`` → **锐化路径**；
    - 定位「异常」→ **异常路径**（否则异常精通不进任何乘区，它的边际收益恒为 0，
      优先级链会被误判——实测 alice / aria / burnice 都踩过）；
    - 其余 → 常规路径。
    """
    return path_for_agent(panel_mode, role_tag)


def verify_priority(
    request: PanelRequest,
    chain: Sequence[dict],
    target: TargetPreset = STANDARD_TARGET,
    path: str | None = None,
    level: int = 60,
    tolerance: float = 0.05,
    agent: Any = None,
) -> list[dict]:
    """验证一条优先级链的每个符号。

    ``chain`` 是攻略页 ``driveBuilds[].subPriority`` 的形状：
    ``[{"label": "暴击率", "next": ">"}, {"label": "暴击伤害", "next": ">"}, …]``，
    每一项的 ``next`` 是它与**下一项**的关系，最后一项的 ``next`` 为空。

    返回逐对判定结果：``{a, b, sign, ratio, verdict}``——``verdict`` 为
    ``"ok"`` / ``"off"``（与写的符号不符）。
    """
    values = one_roll_values(request, target=target, path=path, level=level, agent=agent)
    results: list[dict] = []
    for index in range(len(chain) - 1):
        a_label = chain[index].get("label", "")
        b_label = chain[index + 1].get("label", "")
        sign = chain[index].get("next", "")
        a_id = SUBSTAT_BY_LABEL.get(a_label)
        b_id = SUBSTAT_BY_LABEL.get(b_label)
        if a_id is None or b_id is None or sign not in PRIORITY_SIGNS:
            results.append(
                {
                    "a": a_label,
                    "b": b_label,
                    "sign": sign,
                    "ratio": None,
                    "verdict": "unknown",
                }
            )
            continue
        a_value = values.get(a_id, 0.0)
        b_value = values.get(b_id, 0.0)
        ratio = (a_value / b_value) if b_value else float("inf")
        if a_value == 0.0 or b_value == 0.0:
            # 该词条在当前口径下**不进任何乘区**（生存项：生命值% / 防御力%；
            # 或异常角色的常规暴击——异常走异常暴击区）。这不是链写错了，
            # 是**伤害口径评价不了它**。
            verdict = "na"
        elif sign == ">":
            verdict = "ok" if a_value > b_value else "off"
        else:
            verdict = (
                "ok"
                if abs(ratio - 1.0) <= PRIORITY_TOLERANCE.get(sign, tolerance)
                else "off"
            )
        results.append(
            {
                "a": a_label,
                "b": b_label,
                "sign": sign,
                "ratio": ratio,
                "verdict": verdict,
            }
        )
    return results


__all__ = [
    "PRIORITY_SIGNS",
    "SUBSTAT_BY_LABEL",
    "SUBSTAT_IDS",
    "SUBSTAT_STEP",
    "equivalence",
    "marginal_benefit",
    "one_roll_values",
    "verify_priority",
]
