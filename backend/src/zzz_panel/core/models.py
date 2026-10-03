"""面板计算输入模型。

本模块来自原仓库根目录 ``main.py``，在重构中拆分为包内模块。
规则参考《面板计算方式学习指南》：
- 攻防血：基础值 × (1 + 百分比) + 固定值
- 冲击力 / 异常掌控 / 能量回复：基础值 × (1 + 百分比)
- 暴击率 / 暴击伤害 / 增伤 / 穿透率 / 异常精通 / 穿透值：纯加法
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PanelInputs:
    """面板计算输入。

    默认值对齐 legacy ``calculator.html`` 表单的默认值（与前端
    ``stores/panelStore.ts`` 的 ``defaultBase()`` 一致），这样 CLI 示例与
    空表单场景都得到与旧页面相同的面板。
    """

    base_hp: float = 8000.0
    base_atk: float = 1000.0
    base_def: float = 600.0
    base_cr: float = 5.0
    base_cd: float = 50.0
    base_pr: float = 0.0
    base_impact: float = 90.0
    base_anomaly_ctrl: float = 100.0
    base_energy_regen: float = 1.2
    base_anomaly_mastery: float = 100.0
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

    mode: str = "standard"
