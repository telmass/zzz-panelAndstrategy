"""配装对比：音擎（D1-Wpn）、主词条（D1-Main）、两档门槛（D1-Tier）。

三者共用一个口径：**伤害目标函数**（``services/damage_service.score_build``），
比较的是**同一个代理人的不同配装**，不是不同代理人的面板。

主词条取舍**必须与副词条预算联动**：选了某个主词条，就等于把该盘上
「与主词条同名的副词条」的位置排除掉了——所以换主词条时副词条要重排，
不能把两件事分开算（这是规格里最容易做错的一处）。

副词条重排的模型（有意简化，写在这里以便复核）：

- 每个盘约 ``ceil(总条数 / 6)`` 条；
- 主词条排除了某类副词条时，该类在**这一个盘**上的份额作废；
- 作废的条数按**边际价值**从高到低，依次补给还有空间的副词条。
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

from ..core import options as option_table
from ..core.damage.targets import STANDARD_TARGET, TargetPreset
from ..core.panel_rows import SUB_STAT_DISPLAY_LABELS
from ..schemas.panel import PanelRequest
from .damage_service import score_build
from .benefit_service import SUBSTAT_BY_LABEL, one_roll_values

#: 主词条选项 -> 被排除的副词条（主副同名时互斥）。
#:
#: 真源在 ``core/options.py`` 的 ``MAIN_STAT_EXCLUDED_SUBSTATS``——
#: 与前端 ``calculatorOptions.ts`` 的 ``MAIN_STAT_OPTION_ID_TO_EXCLUDED_SUB_STAT`` 同源。
MAIN_STAT_EXCLUDES: dict[str, str] = dict(option_table.MAIN_STAT_EXCLUDES)


def _score(
    request: PanelRequest,
    target: TargetPreset,
    path: str | None,
    level: int,
    sub_stats: dict[str, int] | None = None,
    agent: Any = None,
) -> float:
    payload = request
    if sub_stats is not None:
        payload = request.model_copy(update={"sub_stats": sub_stats})
    return score_build(
        payload, target=target, path=path, level=level, agent=agent
    ).total


# ------------------------------------------------------------------ 音擎对比


def compare_weapons(
    request: PanelRequest,
    candidates: Sequence[dict],
    target: TargetPreset = STANDARD_TARGET,
    path: str | None = None,
    level: int = 60,
    agent: Any = None,
) -> list[dict]:
    """换音擎的伤害对比。

    ``candidates`` 是音擎条目（``data/catalog/weapons.json`` 的形状：
    ``{id, name, grade, base, substat}``）。每一把都按**同样的副词条与套装**
    重算一次，返回按伤害降序的列表。

    注意：面板口径的「基础攻击力」与「基础防御力」是**互斥**的——
    防御力音擎（DEF 口径）换上去，攻击侧收益会按防御力口径重算。
    """
    results: list[dict] = []
    for weapon in candidates:
        sub = weapon.get("substat") or {}
        variant = request.model_copy(
            update={
                "weapon": request.weapon.model_copy(
                    update={
                        "base_kind": (weapon.get("base") or {}).get("kind", "atk"),
                        "base_value": float((weapon.get("base") or {}).get("value", 0.0)),
                        "substat": (
                            request.weapon.substat.model_copy(
                                update={
                                    "label": sub.get("label", ""),
                                    "value": float(sub.get("value", 0.0)),
                                    "kind": sub.get("kind", "pct"),
                                    "target": sub.get("to", ""),
                                }
                            )
                            if sub
                            else None
                        ),
                    }
                )
            }
        )
        total = _score(variant, target, path, level, agent=agent)
        results.append(
            {
                "weaponId": weapon.get("id"),
                "name": weapon.get("name"),
                "grade": weapon.get("grade"),
                "damage": total,
            }
        )
    results.sort(key=lambda item: item["damage"], reverse=True)
    return results


# ------------------------------------------------------------------ 主词条取舍


def _reallocate(
    sub_stats: dict[str, int],
    excluded: str | None,
    disc_rolls: int,
    values: dict[str, float],
) -> dict[str, int]:
    """主词条排除了一类副词条时的重排。

    被排除的那类在**这一个盘**上的份额作废，作废的条数按边际价值从高到低
    补给还有空间的副词条。价值为 0 的（生存项）排在最后。
    """
    result = dict(sub_stats)
    if not excluded:
        return result
    freed = min(disc_rolls, result.get(excluded, 0))
    if freed <= 0:
        return result
    result[excluded] = result.get(excluded, 0) - freed
    order = sorted(
        (key for key in values if key != excluded),
        key=lambda key: values.get(key, 0.0),
        reverse=True,
    )
    remaining = freed
    for key in order:
        if remaining <= 0:
            break
        add = min(remaining, disc_rolls)
        result[key] = result.get(key, 0) + add
        remaining -= add
    return result


def compare_main_stats(
    request: PanelRequest,
    slot: str = "disc4",
    target: TargetPreset = STANDARD_TARGET,
    path: str | None = None,
    level: int = 60,
    agent: Any = None,
) -> list[dict]:
    """某个槽位（4/5/6 号位）的主词条取舍。

    对每个候选主词条：换主词条 → 按联动规则重排副词条 → 重算伤害。
    返回按伤害降序的列表，每项带**被排除的副词条**与重排后的条数，
    让人能看出「为什么它更好」。
    """
    options = {
        "disc4": option_table.DISC4_OPTIONS,
        "disc5": option_table.DISC5_OPTIONS,
        "disc6": option_table.DISC6_OPTIONS,
    }[slot]
    values = one_roll_values(request, target=target, path=path, level=level, agent=agent)
    total_rolls = sum(request.sub_stats.values())
    disc_rolls = math.ceil(total_rolls / 6) if total_rolls else 0

    results: list[dict] = []
    for option in options:
        excluded = MAIN_STAT_EXCLUDES.get(option.id)
        sub_stats = _reallocate(request.sub_stats, excluded, disc_rolls, values)
        variant = request.model_copy(
            update={
                "disc_main": request.disc_main.model_copy(update={slot: option.id}),
                "sub_stats": sub_stats,
            }
        )
        total = _score(variant, target, path, level, agent=agent)
        results.append(
            {
                "optionId": option.id,
                "label": option.label,
                "excluded": SUB_STAT_DISPLAY_LABELS.get(excluded or "", ""),
                "subStats": dict(sub_stats),
                "damage": total,
            }
        )
    results.sort(key=lambda item: item["damage"], reverse=True)
    return results


# ------------------------------------------------------------------ 两档门槛


def tier_curve(
    request: PanelRequest,
    target: TargetPreset = STANDARD_TARGET,
    path: str | None = None,
    level: int = 60,
    steps: int = 6,
    agent: Any = None,
) -> list[dict]:
    """逐步削减副词条条数，得到「多少条 = 多少伤害」的曲线。

    削减时**优先去掉边际价值最低的**（先掉最不值钱的词条）——
    这就是「从满配往下拆」的真实顺序。
    """
    values = one_roll_values(request, target=target, path=path, level=level, agent=agent)
    full = _score(request, target, path, level)
    total = sum(request.sub_stats.values())
    curve = [{"count": total, "damage": full, "ratio": 1.0}]
    current = dict(request.sub_stats)
    order = sorted(current, key=lambda key: values.get(key, 0.0))
    removed = 0
    for _ in range(steps):
        for key in order:
            if current.get(key, 0) <= 0:
                continue
            current[key] -= 1
            removed += 1
            break
        if removed >= total:
            break
        damage = _score(request, target, path, level, sub_stats=current, agent=agent)
        curve.append(
            {
                "count": total - removed,
                "damage": damage,
                "ratio": (damage / full) if full else 0.0,
            }
        )
    return curve


__all__ = [
    "MAIN_STAT_EXCLUDES",
    "compare_main_stats",
    "compare_weapons",
    "tier_curve",
]
