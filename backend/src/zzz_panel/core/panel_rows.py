"""面板结果行与展示名的唯一权威来源。

之前展示名散在四处，各改各的：

- ``.github/skills/agent-strategy/scripts/calc_graduation_panel.py`` 的
  ``TOTAL_LABELS`` / ``PCT_ROWS`` / ``SUB_STAT_LABELS``
- ``frontend/src/components/calculator/ResultPanel.vue`` 的 ``ROWS``
- ``frontend/src/strategy/substats.ts`` 的大 / 小词条分类集合
- ``backend/tests/test_strategy_data.py`` 的 ``MODIFIER_TO_LABEL``

改一个词条名要同时动四个地方，漏一处就错——而前端「47+7」那一档是从
``"54 条满配：暴击率 ×12、…"`` 这样的**中文串反解**出来的，文案一改就崩。

本模块把这些展示名收成一份，随 :mod:`zzz_panel.core.options` 一起由
``tools/sync_presets.py --options`` 生成到
``data/rules/calculator-rules.json``（``panelRows`` / ``modifierToRow`` /
``subStatDisplayLabels`` 三张表），前端与脚本都从那份派生产物读取，
**不再持有副本**。

两套命名的分工
--------------
- **规范名**：只含词条本身（「暴击伤害」「攻击力%」），见 ``options.py`` 的
  ``RuleOption.name``。规则表与计算用这一套。
- **展示名**：面板行与攻略配装说明用这一套（本模块）。攻略页历来写
  「攻击力% / 攻击力 / 穿透值」而不是规则表的「大攻击% / 小攻击」，
  改动会让已发布的毕业面板与实算结果对不上，所以**两套并存、各司其职**，
  但每一套内部**只有一处真源**。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PanelRow:
    """面板结果的一行。

    ``percent`` 决定展示时是否带 % 后缀；``main`` 决定它是不是「主属性行」
    （计算器主界面与毕业面板的主区块）；``rupture_only`` / ``armorer_only``
    决定该行只在命破 / 锋御面板模式下出现；``energy_label`` 标记能量行
    （标签随模式切换成「能量回复」或「闪能」）。
    """

    key: str
    label: str
    percent: bool = False
    main: bool = False
    rupture_only: bool = False
    armorer_only: bool = False
    energy_label: bool = False


#: 面板结果的全部行，顺序即展示顺序。
#:
#: 与计算器主界面 ``ResultPanel.vue`` 的 ``ROWS`` 一一对应；
#: 毕业面板的 ``--rows`` 取其中若干。
PANEL_ROWS: tuple[PanelRow, ...] = (
    PanelRow("hp", "生命值", main=True),
    PanelRow("atk", "攻击力", main=True),
    PanelRow("penforce", "贯穿力", main=True, rupture_only=True),
    PanelRow("actual_cr", "实际暴击率", percent=True, main=True, armorer_only=True),
    PanelRow("blast_dmg", "锐暴伤害", percent=True, main=True, armorer_only=True),
    PanelRow("def", "防御力", main=True),
    PanelRow("cr", "暴击率", percent=True),
    PanelRow("cd", "暴击伤害", percent=True),
    PanelRow("dmg", "属性伤害", percent=True),
    PanelRow("pr", "穿透率", percent=True),
    PanelRow("pv", "穿透值"),
    PanelRow("am", "异常精通"),
    PanelRow("ac", "异常掌控"),
    PanelRow("imp", "冲击力"),
    PanelRow("er", "能量回复", energy_label=True),
)

#: 修正量（累加器键）→ 面板行 key。
#:
#: 「某个 2 件套效果被多算一次时，会不会落到展示行上」这类判断要用它
#: （见 ``backend/tests/test_strategy_data.py``）。没有对应展示行的修正量
#: （如保留键 ``def_base``）不出现在这里。
MODIFIER_TO_ROW: dict[str, str] = {
    "hp_pct": "hp",
    "hp_flat": "hp",
    "hp_base": "hp",
    "atk_pct": "atk",
    "atk_flat": "atk",
    "atk_base": "atk",
    "def_pct": "def",
    "def_flat": "def",
    "cr": "cr",
    "cd": "cd",
    "dmg": "dmg",
    "pr": "pr",
    "pen_val": "pv",
    "am": "am",
    "ac_flat": "ac",
    "ac_pct": "ac",
    "impact_flat": "imp",
    "impact_pct": "imp",
    "er_flat": "er",
    "er_pct": "er",
}

#: 副词条 id → 攻略配装说明里的展示名。
#:
#: 攻略页历来写「攻击力% / 攻击力 / 穿透值」，不是规则表的「大攻击% / 小攻击」——
#: 改了会让已发布的毕业面板文案与实算结果对不上。**口径不同，但各自只有一处真源。**
SUB_STAT_DISPLAY_LABELS: dict[str, str] = {
    "hp_flat": "生命值",
    "hp_pct": "生命值%",
    "atk_flat": "攻击力",
    "atk_pct": "攻击力%",
    "def_flat": "防御力",
    "def_pct": "防御力%",
    "cr": "暴击率",
    "cd": "暴击伤害",
    "pen_val": "穿透值",
    "am": "异常精通",
}

#: 副词条展示名里属于「小词条」的那些（前端 47+7 口径的少数派）。
SUB_STAT_MINOR_LABELS: tuple[str, ...] = (
    "生命值",
    "防御力",
    "攻击力",
    "小生命",
    "小防御",
    "小攻击",
    "穿透值",
    "穿透",
)

#: 占位用的填充词条名（前端把未列出的剩余条数归到这一档）。
SUB_STAT_FILLER_LABELS: tuple[str, ...] = ("无效词条", "填充", "其余词条")


def row_labels() -> dict[str, str]:
    """面板行 key → 展示名。"""
    return {row.key: row.label for row in PANEL_ROWS}


def percent_row_keys() -> frozenset[str]:
    """带 % 后缀的面板行 key。"""
    return frozenset(row.key for row in PANEL_ROWS if row.percent)


def modifier_labels() -> dict[str, str]:
    """修正量 → 展示名（经面板行中转）。"""
    labels = row_labels()
    return {
        modifier: labels[row_key]
        for modifier, row_key in MODIFIER_TO_ROW.items()
        if row_key in labels
    }
