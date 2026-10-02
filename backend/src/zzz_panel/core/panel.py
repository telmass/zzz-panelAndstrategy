"""面板计算核心。

本模块来自原仓库根目录 ``main.py``。硬约束：不 import fastapi/pydantic、
不读文件、不打印。输入 :class:`~zzz_panel.core.models.PanelInputs`，
输出面板数值字典。
"""

from __future__ import annotations

from typing import Dict, Iterable

from .modes import calculate_mode_stats
from .models import PanelInputs

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


def calculate_panel(inputs: PanelInputs) -> Dict[str, float]:
    """按《学习指南》规则计算最终面板。"""
    weapon_bonus = _resolve_weapon_bonus(inputs)

    hp_pct = _sum_values([
        inputs.core_hp_pct,
        inputs.set_hp_pct,
        inputs.disc_main.get("hp_pct", 0.0),
        inputs.sub_hp_pct,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "hp_pct" else 0.0,
    ])
    atk_pct = _sum_values([
        inputs.core_atk_pct,
        inputs.set_atk_pct,
        inputs.disc_main.get("atk_pct", 0.0),
        inputs.sub_atk_pct,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "atk_pct" else 0.0,
    ])
    def_pct = _sum_values([
        inputs.core_def_pct,
        inputs.set_def_pct,
        inputs.disc_main.get("def_pct", 0.0),
        inputs.sub_def_pct,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "def_pct" else 0.0,
    ])
    impact_pct = _sum_values([
        inputs.core_impact_pct,
        inputs.set_impact_pct,
        inputs.disc_main.get("impact_pct", 0.0),
        inputs.sub_impact_pct,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "impact_pct" else 0.0,
    ])
    anomaly_ctrl_pct = _sum_values([
        inputs.core_anomaly_ctrl_pct,
        inputs.set_anomaly_ctrl_pct,
        inputs.disc_main.get("anomaly_ctrl_pct", 0.0),
        inputs.sub_anomaly_ctrl_pct,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "anomaly_ctrl_pct" else 0.0,
    ])
    energy_pct = _sum_values([
        inputs.core_energy_pct,
        inputs.set_energy_pct,
        inputs.disc_main.get("energy_pct", 0.0),
        inputs.sub_energy_pct,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "energy_pct" else 0.0,
    ])

    hp_flat = _sum_values([
        inputs.disc_main.get("hp_flat", 0.0),
        inputs.sub_hp_flat,
        weapon_bonus["flat"] if inputs.weapon_sub_type == "hp_flat" else 0.0,
    ])
    atk_flat = _sum_values([
        inputs.disc_main.get("atk_flat", 0.0),
        inputs.sub_atk_flat,
        weapon_bonus["flat"] if inputs.weapon_sub_type == "atk_flat" else 0.0,
    ])
    def_flat = _sum_values([
        inputs.disc_main.get("def_flat", 0.0),
        inputs.sub_def_flat,
        weapon_bonus["flat"] if inputs.weapon_sub_type == "def_flat" else 0.0,
    ])

    total_hp = (inputs.base_hp * (1 + hp_pct / 100.0)) + hp_flat
    total_atk = ((inputs.base_atk + inputs.weapon_base_atk) * (1 + atk_pct / 100.0)) + atk_flat
    total_def = ((inputs.base_def + inputs.weapon_base_def) * (1 + def_pct / 100.0)) + def_flat

    total_cr = _sum_values([
        inputs.base_cr,
        inputs.set_cr,
        inputs.disc_main.get("cr", 0.0),
        inputs.sub_cr,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "cr" else 0.0,
    ])
    total_cd = _sum_values([
        inputs.base_cd,
        inputs.set_cd,
        inputs.disc_main.get("cd", 0.0),
        inputs.sub_cd,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "cd" else 0.0,
    ])
    total_dmg = _sum_values([
        inputs.set_dmg,
        inputs.disc_main.get("dmg_bonus", 0.0),
        inputs.sub_dmg,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "dmg_bonus" else 0.0,
    ])
    total_pr = _sum_values([
        inputs.base_pr,
        inputs.set_pr,
        inputs.disc_main.get("pen_rate", 0.0),
        inputs.sub_pr,
        weapon_bonus["pct"] if inputs.weapon_sub_type == "pen_rate" else 0.0,
    ])

    total_impact = inputs.base_impact * (1 + impact_pct / 100.0)
    total_anomaly_ctrl = inputs.base_anomaly_ctrl * (1 + anomaly_ctrl_pct / 100.0)
    total_energy_regen = inputs.base_energy_regen * (1 + energy_pct / 100.0)

    total_anomaly_mastery = _sum_values([
        inputs.base_anomaly_mastery,
        inputs.core_anomaly_mastery,
        inputs.set_anomaly_mastery,
        inputs.disc_main.get("anomaly_mastery", 0.0),
        inputs.sub_anomaly_mastery,
        weapon_bonus["flat"] if inputs.weapon_sub_type == "anomaly_mastery" else 0.0,
    ])
    total_pen_value = _sum_values([
        inputs.base_pen_value,
        inputs.core_pen_val,
        inputs.disc_main.get("pen_val", 0.0),
        inputs.sub_pen_val,
        weapon_bonus["flat"] if inputs.weapon_sub_type == "pen_val" else 0.0,
    ])

    result = {
        "hp": total_hp,
        "atk": total_atk,
        "def": total_def,
        "cr": total_cr,
        "cd": total_cd,
        "dmg": total_dmg,
        "pr": total_pr,
        "impact": total_impact,
        "anomaly_ctrl": total_anomaly_ctrl,
        "energy_regen": total_energy_regen,
        "anomaly_mastery": total_anomaly_mastery,
        "pen_value": total_pen_value,
    }
    result.update(calculate_mode_stats(
        inputs.mode,
        total_hp=total_hp,
        total_atk=total_atk,
        total_cr=total_cr,
        total_cd=total_cd,
    ))
    return result
