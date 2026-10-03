"""词条 / 二件套 / 音擎修正量的合成与分类。

对应 ``frontend/legacy/scripts/calculator.js`` 中累加器 ``S`` 与来源记录
``src``：把「选了什么」翻译成「各修正量加了多少、由谁贡献」。

保持不 import fastapi/pydantic、不读文件、不打印。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List

from .constants import DISC_FIXED_STATS
from .fmt import fmt
from .options import (
    CORE_OPTIONS,
    DISC4_OPTIONS,
    DISC5_OPTIONS,
    DISC6_OPTIONS,
    SET_OPTIONS,
    SUB_STATS,
    RuleOption,
    find_option,
)

#: 副词条中属于固定值的三类，明细里要单独累加用于「固定主词条」那行。
_SUB_FIXED_TARGETS = ("hp_flat", "atk_flat", "def_flat")

#: 音擎固定副词条按「固定值」计入的修正量。百分比类直接进同名键。
_WEAPON_FLAT_TARGETS = frozenset({"hp_flat", "atk_flat", "def_flat", "am", "pen_val"})


class ModifierAccumulator:
    """累加一个修正量并记录来源。

    值为 0 或来源为空时直接跳过，避免明细中出现无意义的「+0」。
    对应 legacy 的 ``add``。
    """

    def __init__(self) -> None:
        self.sum: Dict[str, float] = {}
        self.sources: Dict[str, List[str]] = {}

    def add(self, key: str, value: float | None, label: str) -> None:
        if value is None or value == 0:
            return
        self.sum[key] = self.sum.get(key, 0.0) + value
        if label:
            self.sources.setdefault(key, []).append(label)

    def add_option(self, option: RuleOption, label: str) -> None:
        self.add(option.to, option.value, label)

    def get(self, key: str) -> float:
        return self.sum.get(key, 0.0)


@dataclass
class PanelSelection:
    """一次计算的配装选择。只带 id 与条数，具体数值由本模块查表解析。"""

    mode: str = "standard"
    core: tuple[str, str] = ("", "")
    disc_main: Dict[str, str] = field(default_factory=dict)  # disc4/disc5/disc6 -> option id
    sub_stats: Dict[str, int] = field(default_factory=dict)  # 副词条 id -> 条数
    sets: tuple[str, str, str] = ("", "", "")
    # 音擎固定副词条：已从音擎预设解析出的目标修正量与数值
    weapon_sub_target: str = ""
    weapon_sub_value: float = 0.0
    weapon_sub_kind: str = "pct"
    weapon_sub_label: str = ""
    # 音擎基础值归属
    weapon_base_atk: float = 0.0
    weapon_base_def: float = 0.0


@dataclass
class ModifierResult:
    """修正量合成结果。

    ``sub_fixed`` 是副词条里固定值三类的小计，明细中与驱动盘固定主词条并排展示。
    """

    accumulator: ModifierAccumulator
    sub_fixed: Dict[str, float]

    @property
    def sums(self) -> Dict[str, float]:
        return self.accumulator.sum

    @property
    def sources(self) -> Dict[str, List[str]]:
        return self.accumulator.sources


def _apply_core(acc: ModifierAccumulator, core: tuple[str, str], label_fn) -> None:
    for index, ident in enumerate(core):
        option = find_option(CORE_OPTIONS, ident)
        if option:
            acc.add_option(option, f"核心{index + 1}({label_fn(option.label)})")


def _apply_disc_main(acc: ModifierAccumulator, disc_main: Dict[str, str], label_fn) -> None:
    for slot, options, key in (
        (4, DISC4_OPTIONS, "disc4"),
        (5, DISC5_OPTIONS, "disc5"),
        (6, DISC6_OPTIONS, "disc6"),
    ):
        option = find_option(options, disc_main.get(key, ""))
        if option:
            acc.add_option(option, f"{slot}号({label_fn(option.label)})")


def _apply_sub_stats(acc: ModifierAccumulator, sub_stats: Dict[str, int]) -> Dict[str, float]:
    """按条数 × 单条数值折算副词条，并回传固定值小计。"""
    sub_fixed = {target: 0.0 for target in _SUB_FIXED_TARGETS}
    for stat in SUB_STATS:
        raw = sub_stats.get(stat.id, 0) or 0
        count = max(0, int(math.floor(raw)))
        if count <= 0:
            continue
        value = count * stat.value
        unit = "%" if stat.kind == "pct" else ""
        acc.add(stat.to, value, f"副词条·{stat.label}×{count}={_trim(value)}{unit}")
        if stat.to in sub_fixed:
            sub_fixed[stat.to] += value
    return sub_fixed


def _apply_sets(acc: ModifierAccumulator, sets: tuple[str, str, str], label_fn) -> None:
    for ident in sets:
        option = find_option(SET_OPTIONS, ident)
        if option:
            acc.add_option(option, f"2件套·{label_fn(option.label)}")


def _apply_weapon_substat(acc: ModifierAccumulator, sel: PanelSelection, label_fn) -> None:
    if not sel.weapon_sub_target or sel.weapon_sub_value == 0:
        return
    unit = "%" if sel.weapon_sub_kind == "pct" else ""
    label = f"音擎固定副词条({label_fn(sel.weapon_sub_label)} {_trim(sel.weapon_sub_value)}{unit})"
    acc.add(sel.weapon_sub_target, sel.weapon_sub_value, label)


def _trim(value: float) -> str:
    """明细里的裸数值，直接复用 :func:`core.fmt.fmt` 以保证与前端逐字符一致。"""
    return fmt(value)


def build_modifiers(sel: PanelSelection, label_fn=lambda text: text) -> ModifierResult:
    """把配装选择合成为修正量与来源记录。

    ``label_fn`` 用于能量类文案的面板模式替换（锋御显示「锐能」），默认原样。
    """
    acc = ModifierAccumulator()

    # 核心（2 选）
    _apply_core(acc, sel.core, label_fn)
    # 音擎固定副词条
    _apply_weapon_substat(acc, sel, label_fn)
    # 驱动盘 1/2/3 号固定
    for stat in DISC_FIXED_STATS:
        acc.add(stat.target, stat.value, f"{stat.slot}号固定{stat.label}+{_trim(stat.value)}")
    # 4/5/6 号主词条
    _apply_disc_main(acc, sel.disc_main, label_fn)
    # 副词条
    sub_fixed = _apply_sub_stats(acc, sel.sub_stats)
    # 二件套（0~3 组）
    _apply_sets(acc, sel.sets, label_fn)

    return ModifierResult(accumulator=acc, sub_fixed=sub_fixed)


__all__ = [
    "ModifierAccumulator",
    "ModifierResult",
    "PanelSelection",
    "build_modifiers",
]
