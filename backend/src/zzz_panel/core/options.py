"""配装规则表。

这是词条、二件套与核心加成的**唯一权威来源**。取值逐条对齐
``frontend/tests/fixtures/legacy-calculator/scripts/calculator-config.js``，
唯一的例外是二件套的 ``pr_8``（穿透率 +8%）：参照实现没有这一条，
但游戏内的四件套效果确实存在，故在此补齐。

本模块**单向生成** ``data/rules/calculator-rules.json``，前端
``src/constants/calculatorOptions.ts`` 以
``import generated from '@data/rules/calculator-rules.json'`` 读取该派生产物，
**不再持有副本**。改了本模块必须跑
``python tools/sync_presets.py --options`` 重新生成，否则
``backend/tests/test_options_json.py`` 的防漂移测试会失败。

选项表**不经接口**：下拉框要瞬时可用，不能等一次 HTTP 往返，
所以走构建期生成而非运行时请求。

``name`` 与 ``label`` 的分工
--------------------------
``label`` 是**展示串**，形如「暴击伤害 +28.8%」「攻击力 30%」——含数值、
且各表的数值格式不统一（四种写法并存）。``name`` 是**规范名**，只含词条本身
（「暴击伤害」「攻击力」）。两者分开后：

- 展示文案可以自由调整格式而不用改规范名；
- 代理人预设里的核心加成 ``label``（Wiki 原始措辞）可以与 ``name`` 比对，
  不一致时给出告警——不必再从展示串里剥数字（``大生命%`` 这类名字带 %，
  剥不掉）。

``id`` 缺失的条目按出现顺序补齐，与 legacy 用数组下拉定位的行为等价。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import constants


@dataclass(frozen=True)
class RuleOption:
    """一条配装规则。"""

    id: str
    name: str
    label: str
    value: float
    kind: str
    to: str


def _with_ids(
    table: tuple[tuple[str, str, str, float, str, str], ...], prefix: str
) -> tuple[RuleOption, ...]:
    """legacy 用数组下标定位，迁移后需要稳定 id。"""
    return tuple(
        RuleOption(id=ident, name=name, label=label, value=value, kind=kind, to=target)
        for ident, name, label, value, kind, target in table
    )


CORE_OPTIONS: tuple[RuleOption, ...] = (
    RuleOption("er_base", "基础能量自动回复", "基础能量自动回复 +0.36", 0.36, "flat", "er_flat"),
    RuleOption("atk_base", "基础攻击力", "基础攻击力 +75", 75, "base", "atk_base"),
    RuleOption("impact_base", "基础冲击力", "基础冲击力 +18", 18, "flat", "impact_flat"),
    RuleOption("cd", "暴击伤害", "暴击伤害 +28.8%", 28.8, "pct", "cd"),
    RuleOption("cr", "暴击率", "暴击率 +14.4%", 14.4, "pct", "cr"),
    RuleOption("hp_pct", "生命值百分比", "生命值百分比 +18%", 18, "pct", "hp_pct"),
    RuleOption("hp_base", "基础生命值", "基础生命值 +420", 420, "base", "hp_base"),
    RuleOption("ac", "异常掌控", "异常掌控 +36", 36, "flat", "ac_flat"),
    RuleOption("am", "异常精通", "异常精通 +54", 54, "flat", "am"),
    RuleOption("pr", "穿透率", "穿透率 +14.4%", 14.4, "pct", "pr"),
    RuleOption("am_90", "异常精通", "异常精通 +90", 90, "flat", "am"),
    RuleOption("atk_pct_21", "攻击力", "攻击力 +21%", 21, "pct", "atk_pct"),
)

DISC4_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("atk_pct_30", "攻击力", "攻击力 30%", 30, "pct", "atk_pct"),
        ("hp_pct_30", "生命值", "生命值 30%", 30, "pct", "hp_pct"),
        ("def_pct_48", "防御力", "防御力 48%", 48, "pct", "def_pct"),
        ("cr_24", "暴击率", "暴击率 24%", 24, "pct", "cr"),
        ("cd_48", "暴击伤害", "暴击伤害 48%", 48, "pct", "cd"),
        ("am_92", "异常精通", "异常精通 92", 92, "flat", "am"),
    ),
    "d4",
)

DISC5_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("atk_pct_30", "攻击力", "攻击力 30%", 30, "pct", "atk_pct"),
        ("hp_pct_30", "生命值", "生命值 30%", 30, "pct", "hp_pct"),
        ("def_pct_48", "防御力", "防御力 48%", 48, "pct", "def_pct"),
        ("pr_24", "穿透率", "穿透率 24%", 24, "pct", "pr"),
        ("dmg_30", "增伤", "增伤 30%", 30, "pct", "dmg"),
    ),
    "d5",
)

DISC6_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("atk_pct_30", "攻击力", "攻击力 30%", 30, "pct", "atk_pct"),
        ("hp_pct_30", "生命值", "生命值 30%", 30, "pct", "hp_pct"),
        ("def_pct_48", "防御力", "防御力 48%", 48, "pct", "def_pct"),
        ("impact_pct_24", "冲击力", "冲击力 24%", 24, "pct", "impact_pct"),
        ("ac_pct_30", "异常掌控", "异常掌控 30%", 30, "pct", "ac_pct"),
        ("er_pct_60", "能量回复", "能量回复 60%", 60, "pct", "er_pct"),
    ),
    "d6",
)

SUB_STATS: tuple[RuleOption, ...] = (
    RuleOption("hp_flat", "小生命", "小生命", 112, "flat", "hp_flat"),
    RuleOption("hp_pct", "大生命%", "大生命%", 3, "pct", "hp_pct"),
    RuleOption("atk_flat", "小攻击", "小攻击", 19, "flat", "atk_flat"),
    RuleOption("atk_pct", "大攻击%", "大攻击%", 3, "pct", "atk_pct"),
    RuleOption("def_flat", "小防御", "小防御", 15, "flat", "def_flat"),
    RuleOption("def_pct", "大防御%", "大防御%", 4.8, "pct", "def_pct"),
    RuleOption("cr", "暴击率", "暴击率", 2.4, "pct", "cr"),
    RuleOption("cd", "暴击伤害", "暴击伤害", 4.8, "pct", "cd"),
    RuleOption("pen_val", "穿透值", "穿透值", 9, "flat", "pen_val"),
    RuleOption("am", "异常精通", "异常精通", 9, "flat", "am"),
)

SET_OPTIONS: tuple[RuleOption, ...] = _with_ids(
    (
        ("hp_pct_10", "生命", "生命 +10%", 10, "pct", "hp_pct"),
        ("atk_pct_10", "攻击力", "攻击力 +10%", 10, "pct", "atk_pct"),
        ("def_pct_10", "防御力", "防御力 +10%", 10, "pct", "def_pct"),
        # 荆棘玫瑰二件套（锋御毕业套）：没有这一条，锋御代理人的二件套根本无从选
        ("def_pct_16", "防御力", "防御力 +16%", 16, "pct", "def_pct"),
        ("cr_8", "暴击率", "暴击率 +8%", 8, "pct", "cr"),
        ("cd_16", "暴击伤害", "暴击伤害 +16%", 16, "pct", "cd"),
        ("impact_pct_6", "冲击力", "冲击力 +6%", 6, "pct", "impact_pct"),
        ("ac_pct_8", "异常掌控", "异常掌控 +8%", 8, "pct", "ac_pct"),
        ("er_pct_20", "能量回复", "能量回复 +20%", 20, "pct", "er_pct"),
        ("dmg_10", "增伤", "增伤 +10%", 10, "pct", "dmg"),
        ("pr_8", "穿透率", "穿透率 +8%", 8, "pct", "pr"),
        ("am_30", "异常精通", "异常精通 +30", 30, "flat", "am"),
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


#: 规则表里没有对应选项、但累加器里保留着的修正量。
#:
#: ``def_base``（核心「基础防御值」）在游戏里没有对应选项——核心加成里没有
#: 「基础防御值」这一条。但参照实现（``calculator.js`` 的累加器 ``S``）与后端
#: 面板公式（``panel.py`` 的 ``s("def_base")``）都保留着它，值恒为 0。留着是
#: 为了与参照实现的结构一致，也让将来官方真加出这条核心加成时不必改公式。
RESERVED_MODIFIER_KEYS = frozenset({"def_base"})


def modifier_keys() -> frozenset[str]:
    """全部可被配装修正的量。

    由各选项表的 ``to`` 与驱动盘固定主词条派生，**不另写一份清单**——
    写一份就多一个会与规则表漂移的地方。另有
    :data:`RESERVED_MODIFIER_KEYS` 这类「有累加器但无选项」的保留键。
    前端有一份等价的常量（``frontend/src/constants/calculatorOptions.ts`` 的
    ``MODIFIER_KEYS``），两侧是否一致由 ``frontend/tests/data-manifest.spec.ts``
    断言。
    """
    keys: set[str] = set(RESERVED_MODIFIER_KEYS)
    for table in (
        CORE_OPTIONS,
        DISC4_OPTIONS,
        DISC5_OPTIONS,
        DISC6_OPTIONS,
        SET_OPTIONS,
        SUB_STATS,
    ):
        for option in table:
            keys.add(option.to)
    for stat in constants.DISC_FIXED_STATS:
        keys.add(stat.to)
    return frozenset(keys)
