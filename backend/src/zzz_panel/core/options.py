"""配装规则表。

这是词条、二件套与核心加成的**唯一权威来源**，取值逐条对齐
``frontend/legacy/scripts/calculator-config.js``。

前端 ``src/constants/calculatorOptions.ts`` 目前保留同一份副本，
因为下拉框需要在浏览器里渲染 label；第 3 步只要求计算下沉，
表格下发（``GET /api/options``）留到第 4 步与预设数据一起处理。

``id`` 缺失的条目按出现顺序补齐，与 legacy 用数组下拉定位的行为等价。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RuleOption:
    """一条配装规则。"""

    id: str
    label: str
    value: float
    kind: str
    to: str


def _with_ids(table: tuple[tuple[str, str, float, str, str], ...], prefix: str) -> tuple[RuleOption, ...]:
    """legacy 用数组下标定位，迁移后需要稳定 id。"""
    return tuple(
        RuleOption(id=ident, label=label, value=value, kind=kind, to=target)
        for ident, label, value, kind, target in table
    )


CORE_OPTIONS: tuple[RuleOption, ...] = (
    RuleOption("er_base", "基础能量自动回复 +0.36", 0.36, "flat", "er_flat"),
    RuleOption("atk_base", "基础攻击力 +75", 75, "base", "atk_base"),
    RuleOption("impact_base", "基础冲击力 +18", 18, "flat", "impact_flat"),
    RuleOption("cd", "暴击伤害 +28.8%", 28.8, "pct", "cd"),
    RuleOption("cr", "暴击率 +14.4%", 14.4, "pct", "cr"),
    RuleOption("hp_pct", "生命值百分比 +18%", 18, "pct", "hp_pct"),
    RuleOption("hp_base", "基础生命值 +420", 420, "base", "hp_base"),
    RuleOption("ac", "异常掌控 +36", 36, "flat", "ac_flat"),
    RuleOption("am", "异常精通 +54", 54, "flat", "am"),
    RuleOption("pr", "穿透率 +14.4%", 14.4, "pct", "pr"),
    RuleOption("am_90", "异常精通 +90", 90, "flat", "am"),
    RuleOption("atk_pct_21", "攻击力 +21%", 21, "pct", "atk_pct"),
)

DISC4_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("atk_pct_30", "攻击力 30%", 30, "pct", "atk_pct"),
        ("hp_pct_30", "生命值 30%", 30, "pct", "hp_pct"),
        ("def_pct_48", "防御力 48%", 48, "pct", "def_pct"),
        ("cr_24", "暴击率 24%", 24, "pct", "cr"),
        ("cd_48", "暴击伤害 48%", 48, "pct", "cd"),
        ("am_92", "异常精通 92", 92, "flat", "am"),
    ),
    "d4",
)

DISC5_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("atk_pct_30", "攻击力 30%", 30, "pct", "atk_pct"),
        ("hp_pct_30", "生命值 30%", 30, "pct", "hp_pct"),
        ("def_pct_48", "防御力 48%", 48, "pct", "def_pct"),
        ("pr_24", "穿透率 24%", 24, "pct", "pr"),
        ("dmg_30", "增伤 30%", 30, "pct", "dmg"),
    ),
    "d5",
)

DISC6_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("atk_pct_30", "攻击力 30%", 30, "pct", "atk_pct"),
        ("hp_pct_30", "生命值 30%", 30, "pct", "hp_pct"),
        ("def_pct_48", "防御力 48%", 48, "pct", "def_pct"),
        ("impact_pct_24", "冲击力 24%", 24, "pct", "impact_pct"),
        ("ac_pct_30", "异常掌控 30%", 30, "pct", "ac_pct"),
        ("er_pct_60", "能量回复 60%", 60, "pct", "er_pct"),
    ),
    "d6",
)

SUB_STATS: tuple[RuleOption, ...] = (
    RuleOption("hp_flat", "小生命", 112, "flat", "hp_flat"),
    RuleOption("hp_pct", "大生命%", 3, "pct", "hp_pct"),
    RuleOption("atk_flat", "小攻击", 19, "flat", "atk_flat"),
    RuleOption("atk_pct", "大攻击%", 3, "pct", "atk_pct"),
    RuleOption("def_flat", "小防御", 15, "flat", "def_flat"),
    RuleOption("def_pct", "大防御%", 4.8, "pct", "def_pct"),
    RuleOption("cr", "暴击率", 2.4, "pct", "cr"),
    RuleOption("cd", "暴击伤害", 4.8, "pct", "cd"),
    RuleOption("pen_val", "穿透值", 9, "flat", "pen_val"),
    RuleOption("am", "异常精通", 9, "flat", "am"),
)

SET_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("hp_pct_10", "生命 +10%", 10, "pct", "hp_pct"),
        ("atk_pct_10", "攻击力 +10%", 10, "pct", "atk_pct"),
        ("def_pct_10", "防御力 +10%", 10, "pct", "def_pct"),
        ("cr_8", "暴击率 +8%", 8, "pct", "cr"),
        ("cd_16", "暴击伤害 +16%", 16, "pct", "cd"),
        ("impact_pct_6", "冲击力 +6%", 6, "pct", "impact_pct"),
        ("ac_pct_8", "异常掌控 +8%", 8, "pct", "ac_pct"),
        ("er_pct_20", "能量回复 +20%", 20, "pct", "er_pct"),
        ("dmg_10", "增伤 +10%", 10, "pct", "dmg"),
        ("am_30", "异常精通 +30", 30, "flat", "am"),
    ),
    "set",
)


def find_option(options: tuple[RuleOption, ...], ident: str) -> Optional[RuleOption]:
    """按 id 查选项，未选中（空串）或未知 id 返回 ``None``。"""
    if not ident:
        return None
    for option in options:
        if option.id == ident:
            return option
    return None
