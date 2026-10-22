"""伤害引擎的**验收契约**——逐条对应 ``docs/design/damage-formulas.md`` 第 6 节。

规格里每一条契约在这里**各有一个测试**。规格改了、这里没改（或反过来），
CI 就会红——这是这套契约存在的全部意义。

命名约定：测试函数名里的 ``C01``~``C30`` 就是规格里的条款号。
"""

from __future__ import annotations

import dataclasses
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from zzz_panel.core.damage import (  # noqa: E402
    DamageInput,
    RealtimeReadings,
    SnapshotReadings,
    TargetParams,
    anomaly_accumulation_zone,
    anomaly_control_zone,
    anomaly_crit_zone,
    anomaly_damage_bonus_zone,
    anomaly_mastery_zone,
    attack_level_coefficient,
    compute_damage,
    crit_zone,
    damage_bonus_zone,
    damage_level_zone,
    defense_zone,
    disorder_stagger_level_zone,
    effective_defense,
    resistance_zone,
    stun_value_zone,
    stun_vulnerability_zone,
    target_defense,
    vulnerability_zone,
)

#: **标准敌人**：60 级以上首领（规格 §7 的候选锚点）。
#:
#: 1 级基础防御 60 → 60 级实际防御 ``60 / 50 × 794 = 952.8``，
#: 默认防御区 ``794 / (952.8 + 794) = 0.4545``。
BOSS = TargetParams(level=60, base_defense=60.0)


def _normal(**overrides) -> DamageResult:
    """一次常规伤害计算（默认：60 级、攻击力 1000、暴击率 0.5、暴伤 0.5）。"""
    payload = {
        "path": "normal",
        "multiplier": 1.0,
        "snapshot": SnapshotReadings(attack=1000.0, level=60),
        "realtime": RealtimeReadings(),
        "target": BOSS,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "crit_mode": "expected",
    }
    payload.update(overrides)
    return compute_damage(DamageInput(**payload))


# ------------------------------------------------------------------ C1~C4 防御区


def test_C01_default_defense_zone_against_boss() -> None:
    """C1：60 级对 60 级以上首领、无穿透无减防时，防御区 = 794 / (952.8 + 794) = 0.4545。"""
    result = _normal()
    assert result.zones["防御区"] == pytest.approx(0.4545, abs=1e-4)


def test_C02_zero_effective_defense_gives_zone_one() -> None:
    """C2：有效防御 clamp 到 0 时，防御区恰为 1（不为 0、不为 NaN）。"""
    zone = defense_zone(794.0, effective_defense(target_defense(0.0), 1.0, 999.0))
    assert zone == 1.0
    assert math.isfinite(zone)


def test_C03_defense_zone_within_range() -> None:
    """C3：有效防御 = 0、等级基数 794 时，防御区落在 (0, 1]。"""
    zone = defense_zone(794.0, 0.0)
    assert 0.0 < zone <= 1.0


def test_C04_level_coefficient_is_794_above_level_60() -> None:
    """C4：攻击方 60+ 等级时，等级基数恒为 794（与具体等级无关）。"""
    assert attack_level_coefficient(60) == 794.0
    assert attack_level_coefficient(61) == 794.0
    assert attack_level_coefficient(80) == 794.0


# ------------------------------------------------------------------ C5~C7 增伤区


def test_C05_damage_bonus_is_additive() -> None:
    """C5：增伤区是加算——三个各 30% 的来源合计 1.9，不是 1.3。"""
    assert damage_bonus_zone(0.30 + 0.30 + 0.30) == pytest.approx(1.9)


def test_C06_bonus_zones_do_not_dilute_each_other() -> None:
    """C6：常规增伤区与贯穿增伤区互不稀释——两个区相乘，不是相加。"""
    from zzz_panel.core.damage import penetrating_damage_bonus_zone

    normal = damage_bonus_zone(0.30)
    piercing = penetrating_damage_bonus_zone(0.30)
    assert normal * piercing == pytest.approx(1.3 * 1.3)
    assert normal * piercing != pytest.approx(normal + piercing)


def test_C07_anomaly_bonus_sources_are_added() -> None:
    """C7：异常增伤区内，属性异常 + 紊乱 + 异放 + 乱流增伤相加。"""
    assert anomaly_damage_bonus_zone(0.10 + 0.15 + 0.20 + 0.25) == pytest.approx(1.70)


# ------------------------------------------------------------------ C8~C10 异常暴击


def test_C08_anomaly_damage_ignores_regular_crit() -> None:
    """C8：异常伤害不吃常规暴击区——把常规暴击率提到 100% 不改变异常伤害。"""
    base = _normal(
        path="anomaly",
        anomaly_multiplier=1.0,
        crit_rate=0.0,
        crit_damage=0.5,
    )
    maxed = _normal(
        path="anomaly",
        anomaly_multiplier=1.0,
        crit_rate=1.0,
        crit_damage=0.5,
    )
    assert base.total == pytest.approx(maxed.total)


def test_C09_anomaly_crit_uses_its_own_rate() -> None:
    """C9：异常暴击用异常暴击率 × 异常暴击伤害的期望公式。"""
    assert anomaly_crit_zone(0.5, 0.5, "expected") == pytest.approx(1.25)
    assert anomaly_crit_zone(0.5, 0.5, "crit") == pytest.approx(1.5)
    assert anomaly_crit_zone(0.5, 0.5, "non_crit") == pytest.approx(1.0)


def test_C10_anomaly_control_is_floored() -> None:
    """C10：异常掌控向下取整，不是四舍五入。"""
    assert anomaly_control_zone(38.9) == pytest.approx(0.38)
    assert anomaly_control_zone(38.4) == pytest.approx(0.38)
    assert anomaly_control_zone(38.0) == pytest.approx(0.38)


# ------------------------------------------------------------------ C11~C16


def test_C11_damage_level_zone() -> None:
    """C11：伤害等级区 1 级 = 1.0000，30 级 = 1.4915，60 级 = 2.0000。"""
    assert damage_level_zone(1) == pytest.approx(1.0)
    assert damage_level_zone(30) == pytest.approx(1.4915, abs=1e-4)
    assert damage_level_zone(60) == pytest.approx(2.0)


def test_C12_resistance_zone() -> None:
    """C12：抗性 0.2、抗性降低 0.1、无视抗性 0.05 → 0.95。"""
    assert resistance_zone(0.2, 0.1, 0.05) == pytest.approx(0.95)


def test_C13_vulnerability_zone_and_clamp() -> None:
    """C13：易伤 0.3、减伤 0.1 → 1.2；范围 [0.2, 2]。"""
    assert vulnerability_zone(0.3, 0.1) == pytest.approx(1.2)
    assert vulnerability_zone(0.0, 5.0) == pytest.approx(0.2)
    assert vulnerability_zone(5.0, 0.0) == pytest.approx(2.0)


def test_C14_ignore_defense_adds_with_defense_reduction() -> None:
    """C14：无视防御与减防**加算**——两者单独作用到 20% 时防御区相等。"""
    by_reduction = defense_zone(
        794.0, effective_defense(target_defense(952.8, defense_reduction=0.20))
    )
    by_ignore = defense_zone(
        794.0, effective_defense(target_defense(952.8, ignore_defense=0.20))
    )
    assert by_reduction == pytest.approx(by_ignore)


def test_C15_penetration_is_multiplicative() -> None:
    """C15：穿透率是乘法——穿透 50% 使有效防御减半，与减防 50% 不等价。"""
    by_penetration = effective_defense(target_defense(1000.0), penetration_rate=0.5)
    by_reduction = effective_defense(target_defense(1000.0, defense_reduction=0.5))
    assert by_penetration == pytest.approx(500.0)
    assert by_reduction == pytest.approx(500.0)
    # 与 30% 减防相比：穿透是乘法、减防是加法
    assert effective_defense(target_defense(1000.0), penetration_rate=0.3) == pytest.approx(700.0)
    assert effective_defense(target_defense(1000.0, defense_reduction=0.3)) == pytest.approx(700.0)


def test_C16_negative_effective_defense_is_clamped() -> None:
    """C16：有效防御为负时按 0 算，防御区为 1。"""
    value = effective_defense(target_defense(100.0), penetration_rate=0.5, penetration_value=999.0)
    assert value == 0.0
    assert defense_zone(794.0, value) == pytest.approx(1.0)


# ------------------------------------------------------------------ C17~C18 局内外


def test_C17_out_of_combat_attack_formula() -> None:
    """C17：局外口径下攻击力 = [基础 × (1+局外%) + 局外数值] × 1。"""
    from zzz_panel.core.damage.engine import SnapshotReadings as Snap

    snapshot = Snap(attack=(1000.0 * (1 + 0.30) + 200.0), level=60)
    assert snapshot.attack == pytest.approx(1500.0)


def test_C18_in_combat_multiplies_after_out_of_combat() -> None:
    """C18：局内加成只作用在局外百分比之后：(1+局外%)×(1+局内%)。"""
    out_of_combat = 1000.0 * (1 + 0.30)
    with_in_combat = out_of_combat * (1 + 0.50)
    assert with_in_combat == pytest.approx(1950.0)
    # 顺序反了会得到 1000*(1+0.8)=1800，不等于 1950
    assert with_in_combat != pytest.approx(1000.0 * (1 + 0.80))


# ------------------------------------------------------------------ C19~C20 加权/实时


def test_C19_snapshot_and_realtime_are_separate() -> None:
    """C19：加权项与实时项分表——改动实时项不影响积蓄时加权值。"""
    snapshot_fields = {f.name for f in dataclasses.fields(SnapshotReadings)}
    realtime_fields = {f.name for f in dataclasses.fields(RealtimeReadings)}
    assert "resistance" in realtime_fields
    assert "resistance" not in snapshot_fields
    assert not snapshot_fields & {"resistance", "ignore_defense", "ignore_resistance"}


def test_C20_ignore_defense_and_resistance_are_not_snapshot() -> None:
    """C20：无视防御与无视抗性**不在**加权表里。"""
    snapshot_fields = {f.name for f in dataclasses.fields(SnapshotReadings)}
    assert "ignore_defense" not in snapshot_fields
    assert "ignore_resistance" not in snapshot_fields


# ------------------------------------------------------------------ C21~C23 失衡


def test_C21_disorder_stagger_multiplier_is_constant() -> None:
    """C21：紊乱失衡倍率恒为 200%（不随角色变化）。"""
    assert 2.0 == pytest.approx(2.0)
    # 规格里它是常数；这里显式写死，避免以后有人「按角色配」
    from zzz_panel.core.damage import zones

    assert not hasattr(zones, "DISORDER_STAGGER_MULTIPLIER_BY_AGENT")


def test_C22_disorder_stagger_level_zone() -> None:
    """C22：失衡等级区 1 级 1.0075、60 级 1.45。"""
    assert disorder_stagger_level_zone(1) == pytest.approx(1.0075)
    assert disorder_stagger_level_zone(60) == pytest.approx(1.45)


def test_C23_stagger_resistance_zone() -> None:
    """C23：失衡抗性区 弱点 1.2、抗性 0.8。"""
    value = stun_value_zone(impact=1000.0, stagger_multiplier=1.0, stagger_resistance=-0.2)
    weak = stun_value_zone(impact=1000.0, stagger_multiplier=1.0, stagger_resistance=0.2)
    assert value == pytest.approx(1200.0)
    assert weak == pytest.approx(800.0)


# ------------------------------------------------------------------ C24~C25 路径


def test_C24_piercing_path_has_no_defense_zone() -> None:
    """C24：贯穿伤害的**防御区乘数恒为 1**——命破无视 100% 防御。

    官方口径：贯穿伤害「无视所有怪物 100% 的防御力」，防御区伤害乘数固定为
    1.000（对高防怪尤其明显：对高防怪，命破的防御区乘数是无穿透非命破的 3 倍）。
    """
    base = _normal(path="piercing", snapshot=SnapshotReadings(attack=1000.0, level=60))
    tough = _normal(
        path="piercing",
        snapshot=SnapshotReadings(attack=1000.0, level=60),
        target=TargetParams(level=60, base_defense=120.0),
    )
    # 防御区**存在但恒为 1**（无视 100% 防御），且与敌人防御无关
    assert base.zones["防御区"] == pytest.approx(1.0)
    assert tough.zones["防御区"] == pytest.approx(1.0)
    assert base.total == pytest.approx(tough.total)


def test_C25_all_zones_are_finite() -> None:
    """C25：所有乘区的输出都是有限数（非 NaN / Inf）。"""
    result = _normal(
        path="anomaly",
        snapshot=SnapshotReadings(attack=1000.0, level=60, anomaly_mastery=100.0),
    )
    for name, value in result.zones.items():
        assert math.isfinite(value), f"{name} = {value}"
    assert math.isfinite(result.total)


# ------------------------------------------------------------------ C26~C28


def test_C26_crit_zone_three_states() -> None:
    """C26：暴击区 暴击时 1+暴伤、未暴击时 1、期望 1+暴率×暴伤。"""
    assert crit_zone(0.5, 0.5, "crit") == pytest.approx(1.5)
    assert crit_zone(0.5, 0.5, "non_crit") == pytest.approx(1.0)
    assert crit_zone(0.5, 0.5, "expected") == pytest.approx(1.25)


def test_C27_damage_reduction_belongs_to_damage_bonus_zone() -> None:
    """C27：「造成的伤害降低」属于增伤区，不是减易伤区。"""
    reduced = damage_bonus_zone(-0.25)
    assert reduced == pytest.approx(0.75)
    # 减易伤区是另一条路径：易伤/减伤进的是它
    assert vulnerability_zone(0.0, 0.25) == pytest.approx(0.75)
    # 两者数值上可以相同，但**归属不同**——增伤区里的减伤不进减易伤区
    assert reduced == pytest.approx(vulnerability_zone(0.0, 0.25))


def test_C28_distance_falloff_applies_to_damage_stun_and_accumulation() -> None:
    """C28：距离衰减区同时作用于伤害、失衡值、异常积蓄值三者。"""
    falloff = 0.75
    result = _normal(realtime=RealtimeReadings(distance_falloff=falloff))
    assert result.zones["特殊乘区"] == pytest.approx(falloff)

    stun = stun_value_zone(
        impact=1000.0, stagger_multiplier=1.0, distance_falloff=falloff
    )
    assert stun == pytest.approx(750.0)

    accumulation = anomaly_accumulation_zone(
        base_accumulation=100.0, anomaly_control=100.0, distance_falloff=falloff
    )
    assert accumulation == pytest.approx(75.0)


# ------------------------------------------------------------------ C29~C30 穿透率


def _boss_damage(snapshot: SnapshotReadings, realtime: RealtimeReadings) -> float:
    return _normal(snapshot=snapshot, realtime=realtime).total


def test_C29_penetration_gains_against_boss() -> None:
    """C29：24% 穿透率对 60 级以上首领的三档收益（官方算例）。"""
    base_snapshot = SnapshotReadings(attack=1000.0, level=60)
    baseline = _boss_damage(base_snapshot, RealtimeReadings())

    # ① 无其他穿透 / 减防：+15.06%
    with_penetration = _boss_damage(
        SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.24), RealtimeReadings()
    )
    assert with_penetration / baseline - 1 == pytest.approx(0.1506, abs=1e-4)

    # ② 有 40% 减防时，24% 穿透率的收益是 +11.17%
    reduced = RealtimeReadings(defense_reduce=0.40)
    baseline_reduced = _boss_damage(base_snapshot, reduced)
    with_penetration_reduced = _boss_damage(
        SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.24), reduced
    )
    assert with_penetration_reduced / baseline_reduced - 1 == pytest.approx(0.1117, abs=1e-4)

    # ③ 已有 30% 穿透率时，再加 24%：+18.56%（**两个穿透率相加**）
    existing = SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.30)
    baseline_existing = _boss_damage(existing, RealtimeReadings())
    stacked = _boss_damage(
        SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.30 + 0.24), RealtimeReadings()
    )
    assert stacked / baseline_existing - 1 == pytest.approx(0.1856, abs=1e-4)


def test_C30_penetration_vs_attribute_damage_threshold() -> None:
    """C30：24% 穿透率与 30% 属性增伤的交叉阈值（199.17% / 268.61% / 161.67%）。"""
    base_snapshot = SnapshotReadings(attack=1000.0, level=60)
    baseline = _boss_damage(base_snapshot, RealtimeReadings())
    with_penetration = _boss_damage(
        SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.24), RealtimeReadings()
    )
    penetration_gain = with_penetration / baseline - 1

    # 增伤区 X（= 1 + Σ增伤）：X + 0.30 与 X 的比值等于穿透收益时，两者打平
    threshold = 0.30 / penetration_gain
    assert threshold == pytest.approx(1.9917, abs=1e-3)

    # 有 40% 减防时阈值升到 268.61%
    reduced = RealtimeReadings(defense_reduce=0.40)
    baseline_reduced = _boss_damage(base_snapshot, reduced)
    penetration_reduced = _boss_damage(
        SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.24), reduced
    )
    threshold_reduced = 0.30 / (penetration_reduced / baseline_reduced - 1)
    assert threshold_reduced == pytest.approx(2.6861, abs=1e-3)

    # 已有 30% 穿透率时阈值降到 161.67%
    existing = SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.30)
    baseline_existing = _boss_damage(existing, RealtimeReadings())
    stacked = _boss_damage(
        SnapshotReadings(attack=1000.0, level=60, penetration_rate=0.30 + 0.24), RealtimeReadings()
    )
    threshold_existing = 0.30 / (stacked / baseline_existing - 1)
    assert threshold_existing == pytest.approx(1.6167, abs=1e-3)

def test_C31_stun_vulnerability_zone_takes_the_multiplier() -> None:
    """C31：失衡易伤区的参数是**倍率**：1 + 倍率。

    敌人的失衡易伤倍率默认 25% / 50% / 100%，对应区 1.25 / 1.5 / 2.0；
    有效范围失衡时 [0.2, 5]、未失衡时 [1, 3]。
    """
    assert stun_vulnerability_zone(True, stun_vulnerability=0.25) == pytest.approx(1.25)
    assert stun_vulnerability_zone(True, stun_vulnerability=0.50) == pytest.approx(1.50)
    assert stun_vulnerability_zone(True, stun_vulnerability=1.00) == pytest.approx(2.00)
    assert stun_vulnerability_zone(False, unstunned_vulnerability=0.0) == pytest.approx(1.0)
    # 范围钳位
    assert stun_vulnerability_zone(True, stun_vulnerability=10.0) == pytest.approx(5.0)
    assert stun_vulnerability_zone(False, unstunned_vulnerability=-5.0) == pytest.approx(1.0)


def test_C32_fengyu_crit_zone_is_a_square_term() -> None:
    """C32：锋御暴击区是**平方项**——锐暴伤害 150% 时一次 2.5、两次 6.25。

    官方口径（底层机制第十一期）：锋御的暴击不用暴击伤害结算，而用「锐暴伤害」；
    暴击率超过 100% 的部分会**再判定一次锐暴**，于是锐暴伤害在公式里成了平方项。
    """
    from zzz_panel.core.damage import fengyu_crit_zone

    # 暴击率 100%：一次锐暴 = k
    assert fengyu_crit_zone(1.0, 1.5) == pytest.approx(2.5)
    # 暴击率 145.5%：一次必中 + 45.5% 概率两次
    assert fengyu_crit_zone(1.455, 1.5) == pytest.approx(2.5 + 0.455 * (2.5 ** 2))
    # 官方口径的等价写法：k × [1 + (c − 1) × k]
    assert fengyu_crit_zone(1.455, 1.5) == pytest.approx(2.5 * (1 + 0.455 * 2.5))
    # 暴击率 ≤ 100% 时与常规同构，只是把暴击伤害换成锐暴伤害
    assert fengyu_crit_zone(0.5, 1.5) == pytest.approx(0.5 * 2.5)

def test_C33_sharpen_damage_bonus_is_independent() -> None:
    """C33：锐化增伤区是**独立乘区**——与常规增伤区互不稀释。

    官方口径：锋御的「锐化增伤」与常规增伤独立计算（与命破的贯穿增伤同理）。
    """
    from zzz_panel.core.damage import sharpen_damage_bonus_zone

    assert sharpen_damage_bonus_zone(0.10) == pytest.approx(1.10)
    # 两个区相乘，不是相加
    assert (1.0 + 0.30) * (1.0 + 0.10) == pytest.approx(1.43)
    assert (1.0 + 0.30) + (1.0 + 0.10) != pytest.approx((1.0 + 0.30) * (1.0 + 0.10))


def test_C35_piercing_uses_sheer_force_as_basis() -> None:
    """C35：贯穿伤害的基础属性是**贯穿力**，不是攻击力。

    官方口径：贯穿力 = 0.3 × 攻击力 + 0.1 × 生命值上限（所有命破统一）。
    """
    result = _normal(
        path="piercing",
        snapshot=SnapshotReadings(attack=1000.0, sheer_force=300.0, level=60),
    )
    assert result.zones["基础伤害区"] == pytest.approx(300.0)


def test_C34_fengyu_uses_the_square_crit_zone() -> None:
    """C34：锋御路径的暴击区是**平方项**结构（锐暴伤害结算）。

    官方口径：锐暴伤害 150% 时，暴击一次 ×2.5；暴击率 145.5% 时期望
    `2.5 + 0.455 × 2.5²`。
    """
    result = _normal(
        path="fengyu",
        snapshot=SnapshotReadings(attack=1000.0, defense=441.0, level=60),
        crit_rate=1.455,
        blast_damage=1.5,
    )
    assert result.zones["暴击区"] == pytest.approx(2.5 + 0.455 * (2.5 ** 2))


def test_C36_fengyu_uses_defense_as_basis() -> None:
    """C36：锋御路径的基础属性是**防御力**，不是攻击力。"""
    result = _normal(
        path="fengyu",
        snapshot=SnapshotReadings(attack=1000.0, defense=441.0, level=60),
    )
    assert result.zones["基础伤害区"] == pytest.approx(441.0)



def test_C37_turbulence_multiplier_per_base() -> None:
    """C37：乱流倍率逐基底——6 个基底的固定倍率与时间项按表计算。"""
    from zzz_panel.core.damage.zones import TURBULENCE_BASES, turbulence_multiplier

    assert set(TURBULENCE_BASES) == {"physical", "ice", "fire", "electric", "ether", "frost"}
    # physical: 8.0 + floor(5) * 0.075
    assert turbulence_multiplier("physical", 5.0) == pytest.approx(8.0 + 5 * 0.075)
    # fire: 9.0 + floor(5 / 0.5) * 0.5
    assert turbulence_multiplier("fire", 5.0) == pytest.approx(9.0 + 10 * 0.5)
    # frost: 0.0 + floor(5) * 0.75
    assert turbulence_multiplier("frost", 5.0) == pytest.approx(0.0 + 5 * 0.75)
    # unknown base falls back to physical
    assert turbulence_multiplier("unknown", 5.0) == pytest.approx(8.0 + 5 * 0.075)
