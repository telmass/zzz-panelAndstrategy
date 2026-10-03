"""硬编码常量。

驱动盘 1/2/3 号固定主词条与锋御固有属性「锐暴伤害」。
数值来自 ``frontend/legacy/scripts/calculator.js``，均为固定值，不随配装变化。
"""

from __future__ import annotations

from dataclasses import dataclass

from .options import RuleOption


@dataclass(frozen=True)
class DiscFixedStat:
    """驱动盘固定主词条。``target`` 指明累加到哪个修正量。"""

    slot: int
    label: str
    value: float
    target: str


# 顺序即 1/2/3 号槽位，明细文案中的「1号主词条」等按 slot 取。
DISC_FIXED_STATS: tuple[DiscFixedStat, ...] = (
    DiscFixedStat(slot=1, label="固定生命", value=2200.0, target="hp_flat"),
    DiscFixedStat(slot=2, label="固定攻击", value=316.0, target="atk_flat"),
    DiscFixedStat(slot=3, label="固定防御", value=184.0, target="def_flat"),
)

#: 锋御固有属性「锐暴伤害」，恒定 150%，不参与任何词条/音擎/套装加成。
FENGYU_BLAST_DMG = 150.0


def disc_fixed_stat(slot: int) -> DiscFixedStat:
    """按槽位取固定主词条。``slot`` 为 1/2/3。"""
    for stat in DISC_FIXED_STATS:
        if stat.slot == slot:
            return stat
    raise ValueError(f"Unsupported disc slot: {slot}")


__all__ = [
    "DISC_FIXED_STATS",
    "FENGYU_BLAST_DMG",
    "DiscFixedStat",
    "RuleOption",
    "disc_fixed_stat",
]
