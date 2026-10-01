from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable

sys.stdout.reconfigure(encoding="utf-8")


def _sum_values(values: Iterable[float]) -> float:
    return sum(float(v) for v in values)


@dataclass
class PanelInputs:
    """面板计算输入。

    参考《面板计算方式学习指南》中的规则：
    - 攻防血：基础值 × (1 + 百分比) + 固定值
    - 冲击力 / 异常掌控 / 能量回复：基础值 × (1 + 百分比)
    - 暴击率 / 暴击伤害 / 增伤 / 穿透率 / 异常精通 / 穿透值：纯加法
    """

    base_hp: float = 8000.0
    base_atk: float = 1000.0
    base_def: float = 600.0
    base_cr: float = 20.0
    base_cd: float = 50.0
    base_pr: float = 0.0
    base_impact: float = 0.0
    base_anomaly_ctrl: float = 0.0
    base_energy_regen: float = 1.2
    base_anomaly_mastery: float = 0.0
    base_pen_value: float = 0.0

    weapon_base_atk: float = 0.0
    weapon_base_def: float = 0.0
    weapon_sub_type: str = "cd"
    weapon_sub_value: float = 0.0

    core_hp_pct: float = 0.0
    core_atk_pct: float = 0.0
    core_def_pct: float = 0.0
    core_impact_pct: float = 0.0
    core_anomaly_ctrl_pct: float = 0.0
    core_energy_pct: float = 0.0
    core_anomaly_mastery: float = 0.0
    core_pen_val: float = 0.0

    set_hp_pct: float = 0.0
    set_atk_pct: float = 0.0
    set_def_pct: float = 0.0
    set_cr: float = 0.0
    set_cd: float = 0.0
    set_dmg: float = 0.0
    set_pr: float = 0.0
    set_impact_pct: float = 0.0
    set_anomaly_ctrl_pct: float = 0.0
    set_energy_pct: float = 0.0
    set_anomaly_mastery: float = 0.0

    disc_main: Dict[str, float] = field(default_factory=lambda: {
        "hp_flat": 0.0,
        "atk_flat": 0.0,
        "def_flat": 0.0,
        "hp_pct": 0.0,
        "atk_pct": 0.0,
        "def_pct": 0.0,
        "cr": 0.0,
        "cd": 0.0,
        "impact_pct": 0.0,
        "anomaly_ctrl_pct": 0.0,
        "energy_pct": 0.0,
        "dmg_bonus": 0.0,
        "pen_rate": 0.0,
        "anomaly_mastery": 0.0,
        "pen_val": 0.0,
    })

    sub_hp_flat: float = 0.0
    sub_hp_pct: float = 0.0
    sub_atk_flat: float = 0.0
    sub_atk_pct: float = 0.0
    sub_def_flat: float = 0.0
    sub_def_pct: float = 0.0
    sub_cr: float = 0.0
    sub_cd: float = 0.0
    sub_dmg: float = 0.0
    sub_pr: float = 0.0
    sub_impact_pct: float = 0.0
    sub_anomaly_ctrl_pct: float = 0.0
    sub_energy_pct: float = 0.0
    sub_anomaly_mastery: float = 0.0
    sub_pen_val: float = 0.0


def _resolve_weapon_bonus(inputs: PanelInputs) -> Dict[str, float]:
    weapon_type = inputs.weapon_sub_type
    if weapon_type in {"hp_flat", "hp_pct", "atk_flat", "atk_pct", "def_flat", "def_pct", "impact_pct",
                       "cr", "cd", "anomaly_ctrl_pct", "anomaly_mastery", "energy_pct",
                       "dmg_bonus", "pen_rate", "pen_val"}:
        if weapon_type in {"hp_flat", "atk_flat", "def_flat", "anomaly_mastery", "pen_val"}:
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

    return {
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


def _fmt(value: float, as_percent: bool = False) -> str:
    if as_percent:
        return f"{value:.2f}%"
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}"


EXAMPLE = PanelInputs(
    base_hp=7673.0,
    base_atk=888.0,
    base_def=612.0,
    base_cr=19.4,
    base_cd=50.0,
    base_pr=0.0,
    base_impact=93.0,
    base_anomaly_ctrl=94.0,
    base_energy_regen=1.2,
    base_anomaly_mastery=93.0,
    weapon_base_atk=713.0,
    weapon_sub_type="cd",
    weapon_sub_value=0.0,
    set_dmg=10.0,
    set_anomaly_ctrl_pct=8.0,
    disc_main={
        "hp_flat": 0.0,
        "atk_flat": 0.0,
        "def_flat": 0.0,
        "hp_pct": 0.0,
        "atk_pct": 0.0,
        "def_pct": 0.0,
        "cr": 0.0,
        "cd": 48.0,
        "impact_pct": 0.0,
        "anomaly_ctrl_pct": 0.0,
        "energy_pct": 0.0,
        "dmg_bonus": 0.0,
        "pen_rate": 0.0,
        "anomaly_mastery": 0.0,
        "pen_val": 0.0,
    },
    sub_cr=28.8,
    sub_cd=57.6,
)


if __name__ == "__main__":
    result = calculate_panel(EXAMPLE)
    print("面板计算结果（参考学习指南示例）")
    print(f"生命值：{_fmt(result['hp'])}")
    print(f"攻击力：{_fmt(result['atk'])}")
    print(f"防御力：{_fmt(result['def'])}")
    print(f"暴击率：{_fmt(result['cr'], as_percent=True)}")
    print(f"暴击伤害：{_fmt(result['cd'], as_percent=True)}")
    print(f"增伤：{_fmt(result['dmg'], as_percent=True)}")
    print(f"穿透率：{_fmt(result['pr'], as_percent=True)}")
    print(f"冲击力：{_fmt(result['impact'])}")
    print(f"异常掌控：{_fmt(result['anomaly_ctrl'])}")
    print(f"能量回复：{_fmt(result['energy_regen'])}")
    print(f"异常精通：{_fmt(result['anomaly_mastery'])}")
    print(f"穿透值：{_fmt(result['pen_value'])}")