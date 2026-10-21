"""硬编码常量。

驱动盘 1/2/3 号固定主词条。数值来自
``frontend/tests/fixtures/legacy-calculator/scripts/calculator.js``，均为固定值，不随配装变化。

锋御固有属性「锐暴伤害」是面板模式专属公式的一部分，定义在 ``modes.py``。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiscFixedStat:
    """驱动盘固定主词条。``to`` 指明累加到哪个修正量。"""

    slot: int
    name: str
    label: str
    value: float
    to: str


# 顺序即 1/2/3 号槽位，明细文案中的「1号主词条」等按 slot 取。
DISC_FIXED_STATS: tuple[DiscFixedStat, ...] = (
    DiscFixedStat(slot=1, name="固定生命", label="固定生命", value=2200.0, to="hp_flat"),
    DiscFixedStat(slot=2, name="固定攻击", label="固定攻击", value=316.0, to="atk_flat"),
    DiscFixedStat(slot=3, name="固定防御", label="固定防御", value=184.0, to="def_flat"),
)

__all__ = [
    "DISC_FIXED_STATS",
    "DiscFixedStat",
]
