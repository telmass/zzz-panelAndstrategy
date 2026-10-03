"""面板计算核心。

本模块来自原仓库根目录 ``main.py``。硬约束：不 import fastapi/pydantic、
不读文件、不打印。

两条入口共用 :func:`_apply_totals` 这一套公式：

- :func:`calculate_panel` —— 旧 CLI 契约，输入 :class:`PanelInputs`（已是数值），
  输出键名为 ``impact`` / ``anomaly_ctrl`` / ``energy_regen`` / ``anomaly_mastery``
  / ``pen_value``。保持原样以免破坏既有回归测试。
- :func:`calculate_selection` —— 第 3 步的新契约，输入
  :class:`~zzz_panel.core.modifiers.PanelSelection`（只是选了哪些 id 与条数），
  键名与前端结果面板一致（``imp`` / ``ac`` / ``er`` / ``am`` / ``pv``），
  并额外返回结构化明细。
"""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional, Sequence

from .breakdown import Line, build_breakdown
from .modes import calculate_mode_stats
from .models import PanelInputs
from .modifiers import ModifierResult, PanelSelection, build_modifiers

_PCT_WEAPON_SUB_TYPES = frozenset({
    "hp_pct", "atk_pct", "def_pct", "impact_pct",
    "cr", "cd", "anomaly_ctrl_pct", "anomaly_mastery", "energy_pct",
    "dmg_bonus", "pen_rate", "pen_val",
})

_FLAT_WEAPON_SUB_TYPES = frozenset({
    "hp_flat", "atk_flat", "def_flat", "anomaly_mastery", "pen_val",
})


def _sum_values(values: Iterable[float]) -> float:
    return sum(float(v) for v in values)


def _resolve_weapon_bonus(inputs: PanelInputs) -> Dict[str, float]:
    weapon_type = inputs.weapon_sub_type
    if weapon_type in _PCT_WEAPON_SUB_TYPES:
        if weapon_type in _FLAT_WEAPON_SUB_TYPES:
            return {"flat": inputs.weapon_sub_value, "pct": 0.0}
        return {"flat": 0.0, "pct": inputs.weapon_sub_value}
    return {"flat": 0.0, "pct": 0.0}


def _apply_totals(
    base: Mapping[str, float],
    sums: Mapping[str, float],
    weapon_base: Mapping[str, float],
) -> Dict[str, float]:
    """由基础面板与修正量算出 12 行通用最终面板。

    键名与前端结果面板一致：``hp atk def cr cd dmg pr pv am ac imp er``。

    - 攻防血：``(基础 + 核心基础值 + 音擎基础值) × (1 + 百分比) + 固定值``
    - 异常掌控 / 冲击力 / 能量回复：``(基础 + 固定值) × (1 + 百分比)``
    - 其余：纯加法
    """

    def s(key: str) -> float:
        return float(sums.get(key, 0.0))

    def b(key: str) -> float:
        return float(base.get(key, 0.0))

    total_hp = (b("hp") + s("hp_base")) * (1 + s("hp_pct") / 100.0) + s("hp_flat")
    total_atk = (b("atk") + s("atk_base") + float(weapon_base.get("atk", 0.0))) * (
        1 + s("atk_pct") / 100.0
    ) + s("atk_flat")
    total_def = (b("def") + s("def_base") + float(weapon_base.get("def", 0.0))) * (
        1 + s("def_pct") / 100.0
    ) + s("def_flat")

    return {
        "hp": total_hp,
        "atk": total_atk,
        "def": total_def,
        "cr": b("cr") + s("cr"),
        "cd": b("cd") + s("cd"),
        "dmg": s("dmg"),
        "pr": b("pr") + s("pr"),
        "pv": b("pv") + s("pen_val"),
        "am": b("am") + s("am"),
        "ac": (b("ac") + s("ac_flat")) * (1 + s("ac_pct") / 100.0),
        "imp": (b("impact") + s("impact_flat")) * (1 + s("impact_pct") / 100.0),
        "er": (b("er") + s("er_flat")) * (1 + s("er_pct") / 100.0),
    }


# PanelInputs 的数值字段 → 修正量键名。仅用于旧 CLI 契约的适配层。
_SCALAR_FIELD_MAP = {
    "core_hp_pct": "hp_pct",
    "core_atk_pct": "atk_pct",
    "core_def_pct": "def_pct",
    "core_impact_pct": "impact_pct",
    "core_anomaly_ctrl_pct": "ac_pct",
    "core_energy_pct": "er_pct",
    "core_anomaly_mastery": "am",
    "core_pen_val": "pen_val",
    "set_hp_pct": "hp_pct",
    "set_atk_pct": "atk_pct",
    "set_def_pct": "def_pct",
    "set_cr": "cr",
    "set_cd": "cd",
    "set_dmg": "dmg",
    "set_pr": "pr",
    "set_impact_pct": "impact_pct",
    "set_anomaly_ctrl_pct": "ac_pct",
    "set_energy_pct": "er_pct",
    "set_anomaly_mastery": "am",
    "sub_hp_flat": "hp_flat",
    "sub_hp_pct": "hp_pct",
    "sub_atk_flat": "atk_flat",
    "sub_atk_pct": "atk_pct",
    "sub_def_flat": "def_flat",
    "sub_def_pct": "def_pct",
    "sub_cr": "cr",
    "sub_cd": "cd",
    "sub_dmg": "dmg",
    "sub_pr": "pr",
    "sub_impact_pct": "impact_pct",
    "sub_anomaly_ctrl_pct": "ac_pct",
    "sub_energy_pct": "er_pct",
    "sub_anomaly_mastery": "am",
    "sub_pen_val": "pen_val",
}

# PanelInputs.disc_main 的键名 → 修正量键名
_DISC_MAIN_MAP = {
    "anomaly_mastery": "am",
    "pen_val": "pen_val",
    "dmg_bonus": "dmg",
    "pen_rate": "pr",
    "cr": "cr",
    "cd": "cd",
    "hp_pct": "hp_pct",
    "atk_pct": "atk_pct",
    "def_pct": "def_pct",
    "impact_pct": "impact_pct",
    "anomaly_ctrl_pct": "ac_pct",
    "energy_pct": "er_pct",
    "hp_flat": "hp_flat",
    "atk_flat": "atk_flat",
    "def_flat": "def_flat",
}

# 内部键名 → 旧 CLI 契约键名
_TO_LEGACY_KEY = {
    "imp": "impact",
    "ac": "anomaly_ctrl",
    "er": "energy_regen",
    "am": "anomaly_mastery",
    "pv": "pen_value",
}


def _sums_from_inputs(inputs: PanelInputs) -> Dict[str, float]:
    """把 :class:`PanelInputs` 的数值字段摊平成修正量累加器。"""
    sums: Dict[str, float] = {}

    def add(key: str, value: float) -> None:
        if value:
            sums[key] = sums.get(key, 0.0) + float(value)

    for field_name, target in _SCALAR_FIELD_MAP.items():
        add(target, getattr(inputs, field_name))

    add("pv", inputs.base_pen_value)

    for disc_key, value in inputs.disc_main.items():
        target = _DISC_MAIN_MAP.get(disc_key)
        if target:
            add(target, value)

    bonus = _resolve_weapon_bonus(inputs)
    if bonus["pct"]:
        add(inputs.weapon_sub_type, bonus["pct"])
    if bonus["flat"]:
        add(
            {"hp_flat": "hp_flat", "atk_flat": "atk_flat", "def_flat": "def_flat",
             "anomaly_mastery": "am", "pen_val": "pen_val"}[inputs.weapon_sub_type],
            bonus["flat"],
        )

    return sums


def calculate_panel(inputs: PanelInputs) -> Dict[str, float]:
    """按《学习指南》规则计算最终面板（旧 CLI 契约，键名保持不变）。"""
    sums = _sums_from_inputs(inputs)
    base = {
        "hp": inputs.base_hp,
        "atk": inputs.base_atk,
        "def": inputs.base_def,
        "cr": inputs.base_cr,
        "cd": inputs.base_cd,
        "pr": inputs.base_pr,
        "am": inputs.base_anomaly_mastery,
        "ac": inputs.base_anomaly_ctrl,
        "impact": inputs.base_impact,
        "er": inputs.base_energy_regen,
    }
    weapon_base = {"atk": inputs.weapon_base_atk, "def": inputs.weapon_base_def}
    totals = _apply_totals(base, sums, weapon_base)

    result: Dict[str, float] = {}
    for key, value in totals.items():
        result[_TO_LEGACY_KEY.get(key, key)] = value

    result.update(
        calculate_mode_stats(
            inputs.mode,
            total_hp=totals["hp"],
            total_atk=totals["atk"],
            total_cr=totals["cr"],
            total_cd=totals["cd"],
        )
    )
    return result


def calculate_selection(
    selection: PanelSelection,
    base: Mapping[str, float],
    label_fn=lambda text: text,
) -> Dict[str, object]:
    """第 3 步的新入口：由「选了什么」算出最终面板与结构化明细。

    :param selection: 核心 / 4-6 号 / 副词条条数 / 二件套 / 音擎副词条的选择
    :param base: 角色基础面板，键为 ``hp/atk/def/cr/cd/pr/am/ac/impact/er``
    :param label_fn: 能量类文案的面板模式替换（锋御显示「锐能」）
    :return: ``{"mode", "totals", "mode_stats", "blast_dmg", "sums",
        "sources", "sub_fixed", "weapon_base", "breakdown"}``
    """
    modifiers: ModifierResult = build_modifiers(selection, label_fn)
    sums = modifiers.sums
    weapon_base = {"atk": selection.weapon_base_atk, "def": selection.weapon_base_def}

    totals = _apply_totals(base, sums, weapon_base)
    mode_stats = calculate_mode_stats(
        selection.mode,
        total_hp=totals["hp"],
        total_atk=totals["atk"],
        total_cr=totals["cr"],
        total_cd=totals["cd"],
    )

    breakdown: Dict[str, List[Line]] = build_breakdown(
        base=base,
        totals=totals,
        mode_stats=mode_stats,
        modifiers=modifiers,
        weapon_base=weapon_base,
    )

    return {
        "mode": selection.mode,
        "totals": totals,
        "mode_stats": mode_stats,
        "blast_dmg": mode_stats.get("fengyu_blast_dmg"),
        "sums": {key: value for key, value in sums.items()},
        "sources": {key: list(value) for key, value in modifiers.sources.items()},
        "sub_fixed": dict(modifiers.sub_fixed),
        "weapon_base": weapon_base,
        "breakdown": breakdown,
    }


__all__ = ["calculate_panel", "calculate_selection"]
