"""计算明细（来源追溯）。

必须与 ``frontend/tests/fixtures/legacy-calculator/scripts/calculator.js`` 的明细文案逐段等价，
否则 Vue3 迁移后右侧「计算明细」面板会变样。

按 ``constants.py`` 的建议输出**结构化片段**而非 HTML 字符串：每个片段是
一个 dataclass，前端 ``usePanelCalc`` 负责拼成 ``v-html`` 所需的 HTML。
后端因此不掺入展示层，``tests/legacy-parity.spec.ts`` 仍能守住等价性。

片段类型：

- ``Text``    纯文本
- ``Kw``      关键百分比，渲染时套 ``<span class="kw">``，``text`` 已含 ``%``
- ``Num``     裸数值，渲染时套 ``fmt``（千分位 + 取整）
- ``Sources`` 来源数组，渲染时以 `` + `` 连接并套 ``breakdown-item``
- ``Line``    明细的一行，行内是片段序列
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

from .constants import DISC_FIXED_STATS
from .fmt import fmt
from .modifiers import ModifierResult

# ---------------------------------------------------------------- 片段类型


@dataclass(frozen=True)
class Text:
    text: str


@dataclass(frozen=True)
class Kw:
    """关键百分比，``text`` 已带 ``%``。"""

    text: str


@dataclass(frozen=True)
class Num:
    """裸数值，由前端 ``fmt`` 决定千分位与小数位。

    ``bold`` 对应 legacy 明细里最终值的 ``<b>`` 加粗——只出现在多行明细的末行，
    单行明细（暴击率等）不加粗。``unit`` 会被渲染进 ``<b>`` 内部
    （legacy 是 ``= <b>68.8%</b>`` 而不是 ``= <b>68.8</b>%``）。
    """

    value: float
    bold: bool = False
    unit: str = ""


@dataclass(frozen=True)
class Sources:
    """来源数组，渲染时以 `` + `` 连接。"""

    items: Sequence[str]


@dataclass(frozen=True)
class Line:
    """明细的一行。

    ``wrapped`` 为 False 时前端不套 ``<span class="breakdown-line">``。
    legacy 的纯加法行（暴击率/暴击伤害/增伤/穿透率/穿透值/异常精通）就是这种裸行。
    """

    parts: Sequence[object]
    wrapped: bool = True


# 需要「(基础 + 固定) × (1 + 百分比)」形态的三项
_SCALED_ROWS = (
    # (结果键, 基础键, 固定来源后缀, 百分比修正键)
    ("ac", "ac", "ac_flat", "ac_pct"),
    ("imp", "impact", "impact_flat", "impact_pct"),
    ("er", "er", "er_flat", "er_pct"),
)


def _pct_text(value: float) -> str:
    """百分比数字转文本（不含 ``%``）。

    必须复用 :func:`core.fmt.fmt`：前端 ``usePanelCalc`` 用的是同一个 ``fmt``，
    各自实现会出现 ``4.80%`` 与 ``4.8%`` 的差异。
    """
    return fmt(value)


def _src(key: str, sources: Mapping[str, Sequence[str]]) -> Sources:
    return Sources(sources.get(key, []))


def _flat_disc_line(slot: int, sub_flat: float, *, leading: str) -> List[object]:
    """``+2200（1号主词条）+336（副词条）`` 的片段序列。"""
    fixed = DISC_FIXED_STATS[slot - 1]
    return [
        Text(leading),
        Num(fixed.value),
        Text(f"（{fixed.slot}号主词条）"),
        Text("+"),
        Num(sub_flat),
        Text("（副词条）"),
    ]


def build_breakdown(
    *,
    base: Mapping[str, float],
    totals: Mapping[str, float],
    mode_stats: Mapping[str, float],
    modifiers: ModifierResult,
    weapon_base: Mapping[str, float],
) -> Dict[str, List[Line]]:
    """返回 ``{row_key: [Line, ...]}``。

    :param base: 角色基础面板，键为 ``hp/atk/def/cr/cd/pr/am/ac/impact/er``
    :param totals: 12 行通用最终面板数值
    :param mode_stats: 命破 ``penforce`` 或锋御 ``actual_cr`` / ``fengyu_blast_dmg``
    :param modifiers: :class:`~zzz_panel.core.modifiers.ModifierResult`
    :param weapon_base: ``{"atk": ..., "def": ...}``，音擎基础值归属
    """
    acc = modifiers.accumulator
    sums = acc.sum
    sources = acc.sources
    sub_fixed = modifiers.sub_fixed
    out: Dict[str, List[Line]] = {}

    def total(key: str) -> float:
        return sums.get(key, 0.0)

    def b(key: str) -> float:
        return float(base.get(key, 0.0))

    # ---------- 生命 / 攻击 / 防御：两行 ----------
    # legacy 的三行结构并不一致，迁移时必须逐行照搬，否则明细逐字符比对会失败：
    #   生命  第一行 `(基础[+核心])×(1+百分比)`，第二行 `+固定主词条… = 总值`
    #   攻防  第一行 `(基础[+核心][+音擎])`，    第二行 `×(1+百分比)+固定主词条… = 总值`
    for row, slot, with_weapon, multiply_on_first_line in (
        ("hp", 1, False, True),
        ("atk", 2, True, False),
        ("def", 3, True, False),
    ):
        core_base = total(f"{row}_base")
        head: List[object] = [Text("("), Num(b(row))]
        if core_base:
            head += [Text("+核心"), Num(core_base)]
        if with_weapon:
            head += [Text("+音擎"), Num(float(weapon_base.get(row, 0.0)))]
        # 头部括号在三种行里都是闭合的
        head += [Text(")")]

        multiply: List[object] = [
            Text("×(1+"),
            Kw(f"{_pct_text(total(f'{row}_pct'))}%"),
            Text(")"),
        ]

        if multiply_on_first_line:
            line1 = [*head, *multiply]
            line2: List[object] = _flat_disc_line(
                slot, sub_fixed.get(f"{row}_flat", 0.0), leading="+"
            )
        else:
            line1 = head
            line2 = [*multiply, *_flat_disc_line(slot, sub_fixed.get(f"{row}_flat", 0.0), leading="+")]

        line2 += [Text(" = "), Num(totals[row], bold=True)]
        out[row] = [Line(line1), Line(line2)]

    # ---------- 命破：贯穿力 ----------
    if "penforce" in mode_stats:
        penforce = mode_stats["penforce"]
        out["penforce"] = [
            Line([Text("0.3×"), Num(totals["atk"]), Text(" + 0.1×"), Num(totals["hp"])]),
            Line([Text("= "), Num(penforce, bold=True)]),
        ]

    # ---------- 锋御：实际暴击率与锐暴伤害 ----------
    if "actual_cr" in mode_stats:
        out["actual_cr"] = [
            Line([Num(totals["cd"]), Text("%×35% + "), Num(totals["cr"]), Text("%")]),
            Line([Text("= "), Num(mode_stats["actual_cr"], bold=True, unit="%")]),
        ]

    if "fengyu_blast_dmg" in mode_stats:
        blast = mode_stats["fengyu_blast_dmg"]
        out["blast_dmg"] = [
            Line([Text("固有属性，不受词条、音擎与套装影响")]),
            Line([Text("= "), Num(blast, bold=True, unit="%")]),
        ]

    # ---------- 纯加法行：基础% + 来源 = 总值（裸行，不套 breakdown-line）----------
    for row in ("cr", "cd", "pr"):
        out[row] = [
            Line(
                [
                    Num(b(row)),
                    Text("% + "),
                    _src(row, sources),
                    Text(" = "),
                    Num(totals[row]),
                    Text("%"),
                ],
                wrapped=False,
            )
        ]

    out["dmg"] = [
        Line([_src("dmg", sources), Text(" = "), Num(totals["dmg"]), Text("%")], wrapped=False)
    ]
    out["pv"] = [Line([_src("pen_val", sources), Text(" = "), Num(totals["pv"])], wrapped=False)]

    # ---------- 异常精通：基础为 0 时省略「基础0 + 」（裸行）----------
    am_prefix: List[object] = [Text("基础"), Num(b("am")), Text(" + ")] if b("am") else []
    out["am"] = [
        Line([*am_prefix, _src("am", sources), Text(" = "), Num(totals["am"])], wrapped=False)
    ]

    # ---------- 异常掌控 / 冲击力 / 能量回复：(基础 + 固定) × (1 + 百分比) ----------
    for row, base_key, flat_key, pct_key in _SCALED_ROWS:
        line1: List[object] = [
            Text("("),
            Sources([f"基础{_pct_text(b(base_key))}", *sources.get(flat_key, [])]),
            Text(")×(1+"),
            Kw(f"{_pct_text(total(pct_key))}%"),
            Text(")"),
        ]
        line2: List[object] = [_src(pct_key, sources), Text(" = "), Num(totals[row], bold=True)]
        out[row] = [Line(line1), Line(line2)]

    return out


__all__ = ["build_breakdown", "Kw", "Line", "Num", "Sources", "Text"]
