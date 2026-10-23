"""伤害引擎的**独立验证**：朴素实现对照（D1）+ 属性随机 fuzz（D2）。

- **D1 对照**：把引擎的结果与 ``naive_reference.py``（照规格原文写的独立重写）
  逐值比对。两份独立实现算出同一个数，才说明引擎符合规格。
- **D2 fuzz**：随机属性/base/词条，断言不抛异常、输出有限、乘区不越界，
  并且与朴素实现在**同一输入**上一致。

引擎与规格可能**一起错**——如果引擎写错了，而它的测试又照着引擎写，两边都会绿。
这组测试就是那层「第二意见」。
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "backend" / "tests"))

from naive_reference import (  # noqa: E402
    naive_anomaly_damage,
    naive_armorer_damage,
    naive_normal_damage,
    naive_piercing_damage,
    naive_turbulence_damage,
)
from zzz_panel.core.damage.engine import (  # noqa: E402
    DamageInput,
    RealtimeReadings,
    SnapshotReadings,
    TargetParams,
    compute_damage,
)

#: 标准目标的敌人参数（与规格 §7 的锚点一致）。
BOSS = TargetParams(level=60, base_defense=60.0)


def _engine(**overrides) -> float:
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
    return compute_damage(DamageInput(**payload)).total


def _target_defense() -> float:
    """敌人的实际防御 = 1 级基础防御 / 50 × 攻击方等级基数（规格 §3.4）。"""
    return 60.0 / 50.0 * 794.0


# ------------------------------------------------------------------ D1 对照


def test_D1_normal_path_matches_naive() -> None:
    """常规路径：引擎与朴素重写一致。"""
    naive = naive_normal_damage(
        attack=1000.0,
        multiplier=1.0,
        damage_bonus=0.30,
        crit_rate=0.5,
        crit_damage=0.5,
        level_coefficient=794.0,
        target_defense=_target_defense(),
        penetration_rate=0.24,
        penetration_value=9.0,
        resistance=-0.2,
    )
    engine = _engine(
        snapshot=SnapshotReadings(
            attack=1000.0, level=60, damage_bonus=0.30, penetration_rate=0.24, penetration_value=9.0
        ),
        realtime=RealtimeReadings(resistance=-0.2),
    )
    assert engine == pytest.approx(naive, rel=1e-12)


def test_D1_piercing_path_matches_naive() -> None:
    """贯穿路径：引擎与朴素重写一致。"""
    naive = naive_piercing_damage(
        attack=1000.0,
        multiplier=1.0,
        damage_bonus=0.30,
        crit_rate=0.5,
        crit_damage=0.5,
        piercing_damage_bonus=0.0,
        resistance=-0.2,
    )
    engine = _engine(
        path="piercing",
        snapshot=SnapshotReadings(
            attack=1000.0, sheer_force=1000.0, level=60, damage_bonus=0.30
        ),
        realtime=RealtimeReadings(resistance=-0.2),
    )
    assert engine == pytest.approx(naive, rel=1e-12)


def test_D1_anomaly_path_matches_naive() -> None:
    """异常路径：引擎与朴素重写一致。"""
    naive = naive_anomaly_damage(
        attack=1000.0,
        multiplier=1.0,
        anomaly_multiplier=1.0,
        damage_bonus=0.30,
        anomaly_mastery=100.0,
        level=60,
        anomaly_damage_bonus=0.20,
        anomaly_crit_rate=0.3,
        anomaly_crit_damage=0.4,
        level_coefficient=794.0,
        target_defense=_target_defense(),
        penetration_rate=0.0,
        penetration_value=0.0,
        resistance=-0.2,
    )
    engine = _engine(
        path="anomaly",
        snapshot=SnapshotReadings(attack=1000.0, level=60, damage_bonus=0.30, anomaly_mastery=100.0),
        realtime=RealtimeReadings(
            resistance=-0.2,
            anomaly_damage_bonus=0.20,
            anomaly_crit_rate=0.3,
            anomaly_crit_damage=0.4,
        ),
    )
    assert engine == pytest.approx(naive, rel=1e-12)


# ------------------------------------------------------------------ D2 fuzz


def _random_case(rng: random.Random) -> dict:
    """随机一组属性。范围刻意越过有效范围边界——钳制正是要测的。"""
    return {
        "attack": rng.uniform(0.0, 5000.0),
        "defense": rng.uniform(0.0, 5000.0),
        "multiplier": rng.uniform(0.0, 10.0),
        "blast_damage": rng.uniform(0.0, 3.0),
        "sharpen_damage_bonus": rng.uniform(0.0, 1.0),
        "damage_bonus": rng.uniform(-0.5, 2.0),
        "crit_rate": rng.uniform(-0.2, 1.5),
        "crit_damage": rng.uniform(-0.2, 2.0),
        "penetration_rate": rng.uniform(-0.2, 1.2),
        "penetration_value": rng.uniform(-50.0, 2000.0),
        "resistance": rng.uniform(-1.0, 1.0),
        "anomaly_mastery": rng.uniform(-50.0, 1500.0),
        "anomaly_damage_bonus": rng.uniform(-0.5, 1.0),
        "anomaly_crit_rate": rng.uniform(-0.2, 1.2),
        "anomaly_crit_damage": rng.uniform(-0.2, 2.0),
        # 引擎只支持 60 级及以上（更低等级的等级基数是官方查表值，尚未收录——
        # 引擎**故意报错**而不是给近似值，见 test_low_level_is_refused）。
        "level": rng.choice([60, 60, 60, 61]),
        "easy_damage": rng.uniform(-0.5, 1.0),
        "damage_reduction": rng.uniform(-0.2, 1.0),
        "stun_vulnerability": rng.uniform(-0.5, 2.0),
        "unstunned_vulnerability": rng.uniform(-0.5, 1.0),
        "stunned": rng.random() < 0.5,
        "defense_bonus": rng.uniform(-0.5, 1.0),
        "defense_reduce": rng.uniform(-0.2, 1.0),
        "ignore_defense": rng.uniform(-0.2, 1.0),
    }


def test_low_level_uses_max_level() -> None:
    """低于 60 级时一律按满级（794）计算，不报错。"""
    from zzz_panel.core.damage.zones import attack_level_coefficient

    assert attack_level_coefficient(30) == 794.0
    assert attack_level_coefficient(18) == 794.0


def test_D2_fuzz_matches_naive_and_stays_finite() -> None:
    """D2：200 组随机属性，引擎与朴素实现一致，且输出有限。"""
    rng = random.Random(20261022)
    for index in range(200):
        case = _random_case(rng)
        level_coefficient = 794.0
        target_defense = _target_defense()

        normal_engine = _engine(
            multiplier=case["multiplier"],
            snapshot=SnapshotReadings(
                attack=case["attack"],
                level=case["level"],
                damage_bonus=case["damage_bonus"],
                penetration_rate=case["penetration_rate"],
                penetration_value=case["penetration_value"],
                anomaly_mastery=case["anomaly_mastery"],
            ),
            realtime=RealtimeReadings(
                resistance=case["resistance"],
                defense_reduce=case["defense_reduce"],
                ignore_defense=case["ignore_defense"],
                stun_vulnerability=case["stun_vulnerability"],
                unstunned_stun_vulnerability=case["unstunned_vulnerability"],
                anomaly_damage_bonus=case["anomaly_damage_bonus"],
                anomaly_crit_rate=case["anomaly_crit_rate"],
                anomaly_crit_damage=case["anomaly_crit_damage"],
            ),
            target=TargetParams(
                level=60,
                base_defense=60.0,
                easy_damage=case["easy_damage"],
                damage_reduction=case["damage_reduction"],
                defense_bonus=case["defense_bonus"],
            ),
            crit_rate=case["crit_rate"],
            crit_damage=case["crit_damage"],
            stunned=case["stunned"],
        )
        normal_naive = naive_normal_damage(
            attack=case["attack"],
            multiplier=case["multiplier"],
            damage_bonus=case["damage_bonus"],
            crit_rate=case["crit_rate"],
            crit_damage=case["crit_damage"],
            level_coefficient=level_coefficient,
            target_defense=target_defense,
            penetration_rate=case["penetration_rate"],
            penetration_value=case["penetration_value"],
            resistance=case["resistance"],
            defense_bonus=case["defense_bonus"],
            defense_reduce=case["defense_reduce"],
            ignore_defense=case["ignore_defense"],
            easy_damage=case["easy_damage"],
            damage_reduction=case["damage_reduction"],
            stun_vulnerability=case["stun_vulnerability"],
            unstunned_vulnerability=case["unstunned_vulnerability"],
            stunned=case["stunned"],
        )
        assert math.isfinite(normal_engine), f"#{index} 常规路径输出非有限数"
        assert normal_engine == pytest.approx(normal_naive, rel=1e-12), f"#{index} 常规路径不一致"

        anomaly_engine = _engine(
            path="anomaly",
            multiplier=case["multiplier"],
            snapshot=SnapshotReadings(
                attack=case["attack"],
                level=case["level"],
                damage_bonus=case["damage_bonus"],
                penetration_rate=case["penetration_rate"],
                penetration_value=case["penetration_value"],
                anomaly_mastery=case["anomaly_mastery"],
            ),
            realtime=RealtimeReadings(
                resistance=case["resistance"],
                defense_reduce=case["defense_reduce"],
                ignore_defense=case["ignore_defense"],
                stun_vulnerability=case["stun_vulnerability"],
                unstunned_stun_vulnerability=case["unstunned_vulnerability"],
                anomaly_damage_bonus=case["anomaly_damage_bonus"],
                anomaly_crit_rate=case["anomaly_crit_rate"],
                anomaly_crit_damage=case["anomaly_crit_damage"],
            ),
            target=TargetParams(
                level=60,
                base_defense=60.0,
                easy_damage=case["easy_damage"],
                damage_reduction=case["damage_reduction"],
                defense_bonus=case["defense_bonus"],
            ),
            crit_rate=case["crit_rate"],
            crit_damage=case["crit_damage"],
            stunned=case["stunned"],
        )
        anomaly_naive = naive_anomaly_damage(
            attack=case["attack"],
            multiplier=case["multiplier"],
            anomaly_multiplier=1.0,
            damage_bonus=case["damage_bonus"],
            anomaly_mastery=case["anomaly_mastery"],
            level=case["level"],
            anomaly_damage_bonus=case["anomaly_damage_bonus"],
            anomaly_crit_rate=case["anomaly_crit_rate"],
            anomaly_crit_damage=case["anomaly_crit_damage"],
            level_coefficient=level_coefficient,
            target_defense=target_defense,
            penetration_rate=case["penetration_rate"],
            penetration_value=case["penetration_value"],
            resistance=case["resistance"],
            defense_bonus=case["defense_bonus"],
            defense_reduce=case["defense_reduce"],
            ignore_defense=case["ignore_defense"],
            easy_damage=case["easy_damage"],
            damage_reduction=case["damage_reduction"],
            stun_vulnerability=case["stun_vulnerability"],
            unstunned_vulnerability=case["unstunned_vulnerability"],
            stunned=case["stunned"],
        )
        assert math.isfinite(anomaly_engine), f"#{index} 异常路径输出非有限数"
        assert anomaly_engine == pytest.approx(anomaly_naive, rel=1e-12), f"#{index} 异常路径不一致"


def test_D2_fuzz_piercing_matches_naive() -> None:
    """D2：贯穿路径同样对照（它跳过防御区，最容易与常规路径串味）。"""
    rng = random.Random(20261023)
    for index in range(120):
        case = _random_case(rng)
        engine = _engine(
            path="piercing",
            multiplier=case["multiplier"],
            snapshot=SnapshotReadings(
                attack=case["attack"],
                sheer_force=case["attack"],
                level=case["level"],
                damage_bonus=case["damage_bonus"],
            ),
            realtime=RealtimeReadings(
                resistance=case["resistance"],
                stun_vulnerability=case["stun_vulnerability"],
                unstunned_stun_vulnerability=case["unstunned_vulnerability"],
            ),
            target=TargetParams(
                level=60,
                base_defense=60.0,
                easy_damage=case["easy_damage"],
                damage_reduction=case["damage_reduction"],
                defense_bonus=case["defense_bonus"],
            ),
            crit_rate=case["crit_rate"],
            crit_damage=case["crit_damage"],
            stunned=case["stunned"],
        )
        naive = naive_piercing_damage(
            attack=case["attack"],
            multiplier=case["multiplier"],
            damage_bonus=case["damage_bonus"],
            crit_rate=case["crit_rate"],
            crit_damage=case["crit_damage"],
            piercing_damage_bonus=0.0,
            resistance=case["resistance"],
            easy_damage=case["easy_damage"],
            damage_reduction=case["damage_reduction"],
            stun_vulnerability=case["stun_vulnerability"],
            unstunned_vulnerability=case["unstunned_vulnerability"],
            stunned=case["stunned"],
        )
        assert math.isfinite(engine), f"#{index} 贯穿路径输出非有限数"
        assert engine == pytest.approx(naive, rel=1e-12), f"#{index} 贯穿路径不一致"

def test_D1_armorer_path_matches_naive() -> None:
    """D1：锋御路径——引擎与朴素重写逐值相等。

    锋御的三处不同都在这里：基础属性是**防御力**、暴击区是**平方项**（锐暴伤害
    结算）、多一个**锐化增伤区**。
    """
    naive = naive_armorer_damage(
        defense=441.0,
        multiplier=1.0,
        damage_bonus=0.30,
        sharpen_damage_bonus=0.10,
        crit_rate=1.455,
        blast_damage=1.5,
        level_coefficient=794.0,
        target_defense=952.8,
        penetration_rate=0.0,
        penetration_value=0.0,
        resistance=-0.2,
    )
    engine = _engine(
        path="armorer",
        snapshot=SnapshotReadings(
            attack=1000.0, defense=441.0, level=60, damage_bonus=0.30
        ),
        realtime=RealtimeReadings(resistance=-0.2),
        crit_rate=1.455,
        blast_damage=1.5,
        sharpen_damage_bonus=0.10,
    )
    assert engine == pytest.approx(naive, rel=1e-12)


def test_D2_fuzz_armorer_matches_naive() -> None:
    """D2：锋御路径的随机用例——输出有限、乘区不越界、与朴素实现一致。"""
    rng = random.Random(20261024)
    for index in range(120):
        case = _random_case(rng)
        engine = _engine(
            path="armorer",
            multiplier=case["multiplier"],
            snapshot=SnapshotReadings(
                attack=case["attack"],
                defense=case["defense"],
                level=case["level"],
                damage_bonus=case["damage_bonus"],
                penetration_rate=case["penetration_rate"],
                penetration_value=case["penetration_value"],
            ),
            realtime=RealtimeReadings(
                resistance=case["resistance"],
                defense_reduce=case["defense_reduce"],
                ignore_defense=case["ignore_defense"],
                stun_vulnerability=case["stun_vulnerability"],
                unstunned_stun_vulnerability=case["unstunned_vulnerability"],
            ),
            target=TargetParams(
                level=60,
                base_defense=60.0,
                easy_damage=case["easy_damage"],
                damage_reduction=case["damage_reduction"],
                defense_bonus=case["defense_bonus"],
            ),
            crit_rate=case["crit_rate"],
            crit_damage=case["crit_damage"],
            blast_damage=case["blast_damage"],
            sharpen_damage_bonus=case["sharpen_damage_bonus"],
            stunned=case["stunned"],
        )
        naive = naive_armorer_damage(
            defense=case["defense"],
            multiplier=case["multiplier"],
            damage_bonus=case["damage_bonus"],
            sharpen_damage_bonus=case["sharpen_damage_bonus"],
            crit_rate=case["crit_rate"],
            blast_damage=case["blast_damage"],
            level_coefficient=794.0,
            target_defense=60.0 / 50.0 * 794.0,
            penetration_rate=case["penetration_rate"],
            penetration_value=case["penetration_value"],
            resistance=case["resistance"],
            defense_bonus=case["defense_bonus"],
            defense_reduce=case["defense_reduce"],
            ignore_defense=case["ignore_defense"],
            easy_damage=case["easy_damage"],
            damage_reduction=case["damage_reduction"],
            stun_vulnerability=case["stun_vulnerability"],
            unstunned_vulnerability=case["unstunned_vulnerability"],
            stunned=case["stunned"],
        )
        assert math.isfinite(engine), f"#{index} 锋御路径输出非有限数"
        assert engine == pytest.approx(naive, rel=1e-12), f"#{index} 锋御路径不一致"



def test_D2_fuzz_turbulence_matches_naive() -> None:
    """D2：乱流路径随机对照。"""
    rng = random.Random(20261025)
    for index in range(80):
        case = _random_case(rng)
        level_coefficient = 794.0
        base_anomaly = rng.choice(["physical", "ice", "fire", "electric", "ether", "frost"])
        remaining = rng.uniform(0.0, 8.0)
        naive = naive_turbulence_damage(
            attack=1000.0,
            multiplier=1.0,
            turbulence_base=base_anomaly,
            remaining_seconds=remaining,
            damage_bonus=case["damage_bonus"],
            anomaly_mastery=case["anomaly_mastery"],
            level=60,
            anomaly_damage_bonus=case["anomaly_damage_bonus"],
            anomaly_crit_rate=case["anomaly_crit_rate"],
            anomaly_crit_damage=case["anomaly_crit_damage"],
            level_coefficient=level_coefficient,
            target_defense=_target_defense(),
            penetration_rate=case["penetration_rate"],
            penetration_value=case["penetration_value"],
            resistance=case["resistance"],
            resistance_reduce=0.0,
            ignore_resistance=0.0,
            defense_bonus=case["defense_bonus"],
            defense_reduce=case["defense_reduce"],
            ignore_defense=case["ignore_defense"],
            easy_damage=case["easy_damage"],
            damage_reduction=case["damage_reduction"],
            stun_vulnerability=case["stun_vulnerability"],
            unstunned_vulnerability=case["unstunned_vulnerability"],
            stunned=case["stunned"],
            distance_falloff=1.0,
        )
        engine = _engine(
            path="turbulence",
            multiplier=1.0,
            snapshot=SnapshotReadings(
                attack=1000.0,
                level=60,
                damage_bonus=case["damage_bonus"],
                penetration_rate=case["penetration_rate"],
                penetration_value=case["penetration_value"],
                anomaly_mastery=case["anomaly_mastery"],
            ),
            realtime=RealtimeReadings(
                resistance=case["resistance"],
                resistance_reduce=0.0,
                ignore_resistance=0.0,
                defense_reduce=case["defense_reduce"],
                ignore_defense=case["ignore_defense"],
                anomaly_damage_bonus=case["anomaly_damage_bonus"],
                anomaly_crit_rate=case["anomaly_crit_rate"],
                anomaly_crit_damage=case["anomaly_crit_damage"],
                stun_vulnerability=case["stun_vulnerability"],
                unstunned_stun_vulnerability=case["unstunned_vulnerability"],
                distance_falloff=1.0,
            ),
            target=TargetParams(
                level=60,
                base_defense=60.0,
                defense_bonus=case["defense_bonus"],
                easy_damage=case["easy_damage"],
                damage_reduction=case["damage_reduction"],
                stun_vulnerability=case["stun_vulnerability"],
                unstunned_stun_vulnerability=case["unstunned_vulnerability"],
            ),
            stunned=case["stunned"],
            remaining_seconds=remaining,
            base_anomaly=base_anomaly,
        )
        assert engine == pytest.approx(naive, rel=1e-9, abs=1e-6), (index, engine, naive)
