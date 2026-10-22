"""naive reference (ascii)."""
from __future__ import annotations
import math

def _clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value

def naive_normal_damage(attack, multiplier, damage_bonus, crit_rate, crit_damage, level_coefficient, target_defense, penetration_rate, penetration_value, resistance, resistance_reduce=0.0, ignore_resistance=0.0, defense_bonus=0.0, defense_reduce=0.0, ignore_defense=0.0, easy_damage=0.0, damage_reduction=0.0, stun_vulnerability=1.0, unstunned_vulnerability=1.0, stunned=False, distance_falloff=1.0):
    base = multiplier * attack
    bonus = _clamp(1.0 + damage_bonus, 0.0, 6.0)
    rate = _clamp(crit_rate, 0.0, 1.0)
    dmg = _clamp(crit_damage, 0.0, 5.0)
    crit = 1.0 + rate * dmg
    defense = max(0.0, target_defense * (1.0 + defense_bonus - defense_reduce - ignore_defense))
    effective = max(0.0, defense * (1.0 - penetration_rate) - penetration_value)
    defense_zone = 1.0 if effective <= 0 else level_coefficient / (effective + level_coefficient)
    resist_zone = _clamp(1.0 - resistance + resistance_reduce + ignore_resistance, 0.0, 2.0)
    vulnerability = _clamp(1.0 + easy_damage - damage_reduction, 0.2, 2.0)
    if stunned:
        stun_zone = _clamp(1.0 + stun_vulnerability, 0.2, 5.0)
    else:
        stun_zone = _clamp(1.0 + unstunned_vulnerability, 1.0, 3.0)
    return base * bonus * crit * defense_zone * resist_zone * vulnerability * stun_zone * distance_falloff

def naive_piercing_damage(attack, multiplier, damage_bonus, crit_rate, crit_damage, piercing_damage_bonus, resistance, resistance_reduce=0.0, ignore_resistance=0.0, easy_damage=0.0, damage_reduction=0.0, stun_vulnerability=1.0, unstunned_vulnerability=1.0, stunned=False, distance_falloff=1.0):
    base = multiplier * attack
    bonus = _clamp(1.0 + damage_bonus, 0.0, 6.0)
    rate = _clamp(crit_rate, 0.0, 1.0)
    dmg = _clamp(crit_damage, 0.0, 5.0)
    crit = 1.0 + rate * dmg
    piercing = _clamp(1.0 + piercing_damage_bonus, 0.2, 9.0)
    resist_zone = _clamp(1.0 - resistance + resistance_reduce + ignore_resistance, 0.0, 2.0)
    vulnerability = _clamp(1.0 + easy_damage - damage_reduction, 0.2, 2.0)
    if stunned:
        stun_zone = _clamp(1.0 + stun_vulnerability, 0.2, 5.0)
    else:
        stun_zone = _clamp(1.0 + unstunned_vulnerability, 1.0, 3.0)
    return base * bonus * crit * piercing * resist_zone * vulnerability * stun_zone * distance_falloff

def naive_anomaly_damage(attack, multiplier, anomaly_multiplier, damage_bonus, anomaly_mastery, level, anomaly_damage_bonus, anomaly_crit_rate, anomaly_crit_damage, level_coefficient, target_defense, penetration_rate, penetration_value, resistance, resistance_reduce=0.0, ignore_resistance=0.0, defense_bonus=0.0, defense_reduce=0.0, ignore_defense=0.0, easy_damage=0.0, damage_reduction=0.0, stun_vulnerability=1.0, unstunned_vulnerability=1.0, stunned=False, distance_falloff=1.0):
    base = multiplier * anomaly_multiplier * attack
    bonus = _clamp(1.0 + damage_bonus, 0.0, 6.0)
    mastery = _clamp(anomaly_mastery / 100.0, 0.0, 10.0)
    level_zone = math.trunc((1.0 + (level - 1) / 59.0) * 10000.0) / 10000.0
    anomaly_bonus = _clamp(1.0 + anomaly_damage_bonus, 0.0, 3.0)
    rate = _clamp(anomaly_crit_rate, 0.0, 1.0)
    dmg = _clamp(anomaly_crit_damage, 0.0, 5.0)
    anomaly_crit = 1.0 + rate * dmg
    defense = max(0.0, target_defense * (1.0 + defense_bonus - defense_reduce - ignore_defense))
    effective = max(0.0, defense * (1.0 - penetration_rate) - penetration_value)
    defense_zone = 1.0 if effective <= 0 else level_coefficient / (effective + level_coefficient)
    resist_zone = _clamp(1.0 - resistance + resistance_reduce + ignore_resistance, 0.0, 2.0)
    vulnerability = _clamp(1.0 + easy_damage - damage_reduction, 0.2, 2.0)
    if stunned:
        stun_zone = _clamp(1.0 + stun_vulnerability, 0.2, 5.0)
    else:
        stun_zone = _clamp(1.0 + unstunned_vulnerability, 1.0, 3.0)
    return base * bonus * mastery * defense_zone * resist_zone * vulnerability * stun_zone * level_zone * anomaly_bonus * anomaly_crit * distance_falloff

def naive_fengyu_damage(defense, multiplier, damage_bonus, sharpen_damage_bonus, crit_rate, blast_damage, level_coefficient, target_defense, penetration_rate, penetration_value, resistance, resistance_reduce=0.0, ignore_resistance=0.0, defense_bonus=0.0, defense_reduce=0.0, ignore_defense=0.0, easy_damage=0.0, damage_reduction=0.0, stun_vulnerability=1.0, unstunned_vulnerability=1.0, stunned=False, distance_falloff=1.0):
    base = multiplier * defense
    bonus = _clamp(1.0 + damage_bonus, 0.0, 6.0)
    sharpen = _clamp(1.0 + sharpen_damage_bonus, 0.0, 10.0)
    k = 1.0 + max(0.0, blast_damage)
    rate = max(0.0, crit_rate)
    if rate <= 1.0:
        crit = rate * k
    else:
        crit = k * (1.0 + (rate - 1.0) * k)
    enemy_defense = max(0.0, target_defense * (1.0 + defense_bonus - defense_reduce - ignore_defense))
    effective = max(0.0, enemy_defense * (1.0 - penetration_rate) - penetration_value)
    defense_zone = 1.0 if effective <= 0 else level_coefficient / (effective + level_coefficient)
    resist_zone = _clamp(1.0 - resistance + resistance_reduce + ignore_resistance, 0.0, 2.0)
    vulnerability = _clamp(1.0 + easy_damage - damage_reduction, 0.2, 2.0)
    if stunned:
        stun_zone = _clamp(1.0 + stun_vulnerability, 0.2, 5.0)
    else:
        stun_zone = _clamp(1.0 + unstunned_vulnerability, 1.0, 3.0)
    return base * bonus * sharpen * crit * defense_zone * resist_zone * vulnerability * stun_zone * distance_falloff

def naive_turbulence_damage(attack, multiplier, turbulence_base, remaining_seconds, damage_bonus, anomaly_mastery, level, anomaly_damage_bonus, anomaly_crit_rate, anomaly_crit_damage, level_coefficient, target_defense, penetration_rate, penetration_value, resistance, resistance_reduce=0.0, ignore_resistance=0.0, defense_bonus=0.0, defense_reduce=0.0, ignore_defense=0.0, easy_damage=0.0, damage_reduction=0.0, stun_vulnerability=1.0, unstunned_vulnerability=1.0, stunned=False, distance_falloff=1.0):
    _TURBULENCE_BASES = {"physical": (8.0, 0.075, 1.0), "ice": (13.0, 0.075, 1.0), "fire": (9.0, 0.50, 0.5), "electric": (6.5, 1.25, 1.0), "ether": (6.5, 0.625, 0.5), "frost": (0.0, 0.75, 1.0)}
    fixed, k, denom = _TURBULENCE_BASES.get(turbulence_base, _TURBULENCE_BASES["physical"])
    turb_mult = fixed + math.floor(remaining_seconds / denom) * k
    base = multiplier * turb_mult * attack
    bonus = _clamp(1.0 + damage_bonus, 0.0, 6.0)
    mastery = _clamp(anomaly_mastery / 100.0, 0.0, 10.0)
    level_zone = math.trunc((1.0 + (level - 1) / 59.0) * 10000.0) / 10000.0
    anomaly_bonus = _clamp(1.0 + anomaly_damage_bonus, 0.0, 3.0)
    rate = _clamp(anomaly_crit_rate, 0.0, 1.0)
    dmg = _clamp(anomaly_crit_damage, 0.0, 5.0)
    anomaly_crit = 1.0 + rate * dmg
    defense = max(0.0, target_defense * (1.0 + defense_bonus - defense_reduce - ignore_defense))
    effective = max(0.0, defense * (1.0 - penetration_rate) - penetration_value)
    defense_zone = 1.0 if effective <= 0 else level_coefficient / (effective + level_coefficient)
    resist_zone = _clamp(1.0 - resistance + resistance_reduce + ignore_resistance, 0.0, 2.0)
    vulnerability = _clamp(1.0 + easy_damage - damage_reduction, 0.2, 2.0)
    if stunned:
        stun_zone = _clamp(1.0 + stun_vulnerability, 0.2, 5.0)
    else:
        stun_zone = _clamp(1.0 + unstunned_vulnerability, 1.0, 3.0)
    return base * bonus * mastery * defense_zone * resist_zone * vulnerability * stun_zone * level_zone * anomaly_bonus * anomaly_crit * distance_falloff

__all__ = ["naive_normal_damage", "naive_piercing_damage", "naive_anomaly_damage", "naive_fengyu_damage", "naive_turbulence_damage"]
