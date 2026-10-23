"""伤害目标函数——把**面板**变成**可比伤害**，用于配装比较。

面板（局外静态）只说明「属性有多少」，不说明「打起来有多疼」。配装取舍要的是后者，
所以需要一个把面板换算成伤害的**目标函数**。

口径（见 ``docs/design/damage-formulas.md``）：

- 面板与伤害**同口径**：局外、0 影画 + 专武。影画与专武局内加成不进引擎。
- 敌人是**基准目标**（默认 60 级以上首领），不指定就没有可比对象。
- **技能倍率取 1**（单位倍率伤害）。技能倍率对所有候选配装是同一个常数，
  不影响排序；等技能倍率数据到位，再把绝对值补上。

用法：

    from zzz_panel.services.damage_service import score_build
    result = score_build(request)          # -> DamageResult（总值 + 逐乘区明细）
"""

from __future__ import annotations

from typing import Any

from ..core.damage.engine import (
    DamageInput,
    DamagePath,
    DamageResult,
    RealtimeReadings,
    SnapshotReadings,
    compute_damage,
)
from ..core.damage.targets import STANDARD_TARGET, TargetPreset, to_params
from ..schemas.panel import PanelRequest
from .panel_service import calculate


def path_for_agent(panel_mode: str, role_tag: str) -> str:
    """按代理人的**面板模式**与**定位**选伤害路径。

    | 面板模式 / 定位 | 路径 | 基础属性 |
    | --- | --- | --- |
    | 面板模式 ``rupture``（命破） | ``piercing`` | **贯穿力** |
    | 面板模式 ``armorer``（锋御） | ``armorer`` | **防御力** |
    | 定位「异常」 | ``anomaly`` | 攻击力 |
    | 其余 | ``normal`` | 攻击力 |

    ⚠️ **异常伤害一律用攻击力**——命破与锋御只有**直伤**换口径（规格 §3.1）。

    ⚠️ 面板模式优先于定位：命破 / 锋御的角色**也可能是异常定位**，
    但它们的**直伤**才是贯穿 / 锐化，异常伤害另算。
    """
    if panel_mode == "rupture":
        return "piercing"
    if panel_mode == "armorer":
        return "armorer"
    if role_tag == "异常":
        return "anomaly"
    return "normal"


def _total(totals: dict, key: str, default: float = 0.0) -> float:
    value = totals.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def score_build(
    request: PanelRequest,
    target: TargetPreset = STANDARD_TARGET,
    path: DamagePath | None = None,
    level: int = 60,
    multiplier: float = 1.0,
    crit_mode: str = "expected",
    stunned: bool = False,
    attribute_resistance: float | None = None,
    agent: Any = None,
) -> DamageResult:
    """一次配装的伤害得分。

    返回 :class:`DamageResult`——``total`` 是可比较的伤害值（单位倍率），
    ``zones`` 是逐乘区明细（可做白盒）。

    ``attribute_resistance`` 覆盖目标的属性抗性（``None`` 用目标自身的设定）。

    ``agent`` 是**代理人预设**（``AgentPreset`` 或同形状的 dict）：它决定
    **伤害路径**（按面板模式与定位）与**锐暴伤害**。不给时按 ``request.mode``
    推断路径（面板模式那一维），定位那维取不到 → 异常定位的角色会走常规路径
    （调用方应把预设传进来）。

    各路径从面板取的行：

    - 常规直伤：攻击力 / 暴击率 / 属性伤害 / 穿透率 / 穿透值
    - 贯穿（命破）：**贯穿力** 作基础属性，防御区恒 1
    - 锐化（锋御）：**防御力** 作基础属性，暴击率取面板的 **actual_cr**
      （已含「暴击伤害 → 暴击率」的转模），暴击区用平方项结构
    - 异常伤害：攻击力 / 异常精通；**不吃**常规暴击区
    """
    response = calculate(request)
    totals = response.totals

    if path is None:
        path = path_for_agent(
            _get(agent, "panel_mode") or request.mode,
            _get(agent, "role_tag") or "",
        )

    # 锋御的暴击率用面板的 **actual_cr**——它已经是「面板暴击率 + 初始暴伤 ×
    # 转模比例」的结果（core/modes.py）；**不要在引擎里再转一次模**。
    crit_rate = (
        _total(totals, "actual_cr") / 100.0 if path == "armorer" else _total(totals, "cr") / 100.0
    )
    snapshot = SnapshotReadings(
        attack=_total(totals, "atk"),
        damage_bonus=_total(totals, "dmg") / 100.0,
        level=level,
        penetration_rate=_total(totals, "pr") / 100.0,
        penetration_value=_total(totals, "pv"),
        anomaly_mastery=_total(totals, "am"),
        sheer_force=_total(totals, "penforce"),
        defense=_total(totals, "def"),
    )
    resistance = (
        target.attribute_resistance
        if attribute_resistance is None
        else attribute_resistance
    )
    realtime = RealtimeReadings(
        resistance=resistance,
        # 失衡易伤**倍率**来自目标（首领 100% / 精英与普通 50%）
        stun_vulnerability=target.stun_vulnerability,
        unstunned_stun_vulnerability=target.unstunned_stun_vulnerability,
    )
    damage_input = DamageInput(
        path=path,
        multiplier=multiplier,
        snapshot=snapshot,
        realtime=realtime,
        target=to_params(target),
        crit_rate=crit_rate,
        crit_damage=_total(totals, "cd") / 100.0,
        crit_mode=crit_mode,  # type: ignore[arg-type]
        stunned=stunned,
        # 锐暴伤害：官方基础值 150%（可被额外能力 / 影画 / 套装 / Boss 抬升，
        # 那些来源尚未建模）→ 逐代理人化属二期后续项 B1。
        blast_damage=_get(agent, "armorer_blast_damage") or 150.0,
    )
    return compute_damage(damage_input)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """读属性或字典键（代理人预设是 pydantic 模型，也可能是 dict）。"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def compare_builds(
    requests: list[PanelRequest],
    target: TargetPreset = STANDARD_TARGET,
    path: DamagePath = "normal",
    level: int = 60,
) -> list[tuple[PanelRequest, float]]:
    """比较多套配装的伤害得分，按**得分降序**返回。

    这是「用伤害引擎反推最优配装」的最小内核：给定候选集，给出排序。
    """
    scored = [
        (request, score_build(request, target=target, path=path, level=level).total)
        for request in requests
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


__all__ = ["compare_builds", "score_build"]
