"""伤害引擎（规格见 ``docs/design/damage-formulas.md``）。

分层：

- :mod:`zones` —— 纯乘区函数（零 I/O），每个乘区对应规格里的一节；
- :mod:`engine` —— 把乘区按三条伤害路径装配成结果。
"""

from __future__ import annotations

from .engine import (
    CritMode,
    DamageInput,
    DamagePath,
    DamageResult,
    RealtimeReadings,
    SnapshotReadings,
    TargetParams,
    compute_damage,
)
from .zones import (
    ATTACK_LEVEL_COEFFICIENT,
    anomaly_accumulation_zone,
    anomaly_control_zone,
    anomaly_crit_zone,
    anomaly_damage_bonus_zone,
    anomaly_mastery_zone,
    attack_level_coefficient,
    crit_zone,
    damage_bonus_zone,
    damage_level_zone,
    defense_zone,
    fengyu_crit_zone,
    disorder_stagger_level_zone,
    effective_defense,
    penetrating_damage_bonus_zone,
    resistance_zone,
    sharpen_damage_bonus_zone,
    stun_value_zone,
    stun_vulnerability_zone,
    target_defense,
    vulnerability_zone,
)

__all__ = [
    "ATTACK_LEVEL_COEFFICIENT",
    "CritMode",
    "DamageInput",
    "DamagePath",
    "DamageResult",
    "RealtimeReadings",
    "SnapshotReadings",
    "TargetParams",
    "anomaly_accumulation_zone",
    "anomaly_control_zone",
    "anomaly_crit_zone",
    "anomaly_damage_bonus_zone",
    "anomaly_mastery_zone",
    "attack_level_coefficient",
    "compute_damage",
    "crit_zone",
    "damage_bonus_zone",
    "damage_level_zone",
    "defense_zone",
    "fengyu_crit_zone",
    "disorder_stagger_level_zone",
    "effective_defense",
    "penetrating_damage_bonus_zone",
    "resistance_zone",
    "sharpen_damage_bonus_zone",
    "stun_value_zone",
    "stun_vulnerability_zone",
    "target_defense",
    "vulnerability_zone",
]
