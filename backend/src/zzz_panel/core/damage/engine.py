"""伤害引擎——按规格装配乘区。

规格真源：``docs/design/damage-formulas.md``。乘区的算式都在
:mod:`zzz_panel.core.damage.zones`，本模块只负责**装配**。

两条结构性的东西在这里落地：

- **积蓄时加权 / 结算时实时分成两个 dataclass**（:class:`SnapshotReadings` /
  :class:`RealtimeReadings`）。它们不是「约定」，是**结构**——无视防御与无视抗性
  物理上不在加权那一侧（规格 §4.2，契约 C19 / C20）。
- **三条伤害路径**走不同的乘区组合（规格 §2）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .zones import (
    anomaly_control_zone,
    anomaly_crit_zone,
    anomaly_damage_bonus_zone,
    anomaly_mastery_zone,
    attack_level_coefficient,
    crit_zone,
    damage_bonus_zone,
    damage_level_zone,
    defense_zone,
    effective_defense,
    armorer_crit_zone,
    penetrating_damage_bonus_zone,
    resistance_zone,
    sharpen_damage_bonus_zone,
    stun_vulnerability_zone,
    target_defense,
    turbulence_multiplier,
    vulnerability_zone,
)

DamagePath = Literal["normal", "piercing", "anomaly", "armorer", "turbulence"]
CritMode = Literal["crit", "non_crit", "expected"]


@dataclass(frozen=True)
class SnapshotReadings:
    """**积蓄时加权**的读数——一次算定，异常伤害用它的加权和。

    规格 §4.2 列的加权项：攻击力、增伤、等级、穿透率、穿透值、异常精通、失衡值提升。
    **无视防御与无视抗性不在这里**（契约 C20）。
    """

    #: 攻击力——常规直伤与**异常伤害**的基础属性。
    #: ⚠️ 命破与锋御的异常伤害**仍用攻击力**（只有直伤换口径）。
    attack: float
    damage_bonus: float = 0.0
    level: int = 60
    penetration_rate: float = 0.0
    penetration_value: float = 0.0
    anomaly_mastery: float = 0.0
    stagger_value_bonus: float = 0.0
    #: 贯穿力——**贯穿伤害（命破）**的基础属性。
    #: 官方口径：贯穿力 = 0.3 × 攻击力 + 0.1 × 生命值上限（所有命破统一）。
    sheer_force: float = 0.0
    #: 防御力——**锐化伤害（锋御）**的基础属性。
    defense: float = 0.0


@dataclass(frozen=True)
class RealtimeReadings:
    """**结算时实时**的读数——打到的瞬间才读。

    规格 §4.2：抗性、抗性降低、防御降低、无视防御、无视抗性、失衡易伤、异常增伤、
    异常暴击。**这一侧不进加权**（契约 C19 / C20）。
    """

    resistance: float = 0.0
    resistance_reduce: float = 0.0
    defense_reduce: float = 0.0
    ignore_defense: float = 0.0
    ignore_resistance: float = 0.0
    stun_vulnerability: float = 1.0
    unstunned_stun_vulnerability: float = 1.0
    anomaly_damage_bonus: float = 0.0
    anomaly_crit_rate: float = 0.0
    anomaly_crit_damage: float = 0.0
    distance_falloff: float = 1.0


@dataclass(frozen=True)
class TargetParams:
    """受击方（敌人）参数。

    ``base_defense`` 是**1 级**基础防御力（普通 36~46、精英 45~54、杜拉罕 58、
    首领 60），实际防御 = ``base_defense / 50 × 攻击方等级基数``（规格 §3.4）。
    """

    level: int = 60
    base_defense: float = 60.0
    stagger_resistance: float = 0.0
    easy_damage: float = 0.0
    damage_reduction: float = 0.0
    defense_bonus: float = 0.0
    #: 敌人的失衡易伤**倍率**（失衡易伤区 = 1 + 倍率）
    stun_vulnerability: float = 1.0
    unstunned_stun_vulnerability: float = 1.0
    fixed_defense: float = 0.0


@dataclass(frozen=True)
class DamageInput:
    """一次伤害计算的输入。"""

    path: DamagePath = "normal"
    #: 技能倍率（常规伤害 / 贯穿伤害的倍率）。
    multiplier: float = 1.0
    snapshot: SnapshotReadings = field(default_factory=lambda: SnapshotReadings(attack=0.0))
    realtime: RealtimeReadings = field(default_factory=RealtimeReadings)
    target: TargetParams = field(default_factory=TargetParams)
    crit_rate: float = 0.0
    crit_damage: float = 0.0
    crit_mode: CritMode = "expected"
    #: 锐暴伤害（锋御专有，规格 §3.12）。官方基础值 150%，
    #: 还会被额外能力 / 影画 / 套装 / Boss 加成抬升（那些来源尚未建模）。
    blast_damage: float = 150.0
    #: 锐化增伤（锋御专有的独立乘区，规格 §3.12）。量级约 10%；
    #: 来源数据集尚未建，先恒为 0。
    sharpen_damage_bonus: float = 0.0
    #: 异常伤害的额外倍率（异常伤害的基础伤害区与常规不同，见规格 §3.1）。
    anomaly_multiplier: float = 1.0
    stunned: bool = False
    #: 乱流的时间输入：非风基底异常的剩余时间 T（规格 §3.13，B3）。
    remaining_seconds: float = 0.0
    #: 乱流的基底异常（physical/ice/fire/electric/ether/frost），决定倍率表行。
    base_anomaly: str = "physical"


@dataclass(frozen=True)
class DamageResult:
    """伤害结果：总值 + 逐乘区明细。

    ``zones`` 的键就是乘区名，与规格 §2 的总纲一一对应——UI 可以直接拿它做白盒。
    """

    total: float
    base: float
    zones: dict[str, float]

    def zone_product(self) -> float:
        """把各乘区连乘——应当等于 ``total``（自检用）。"""
        product = 1.0
        for value in self.zones.values():
            product *= value
        return product


def compute_damage(request: DamageInput) -> DamageResult:
    """按规格装配乘区，算出一个伤害值。

    乘区组合（规格 §2）：

    - 常规：基础伤害区 × 增伤区 × 暴击区 × 防御区 × 抗性区 × 减易伤区 × 失衡易伤区 × 特殊乘区
    - 贯穿：基础伤害区 × 增伤区 × 暴击区 × **贯穿增伤区** × 抗性区 × 减易伤区 × 失衡易伤区 × 特殊乘区
    - 异常：基础伤害区 × 增伤区 × **异常精通区** × 防御区 × 抗性区 × 减易伤区 × 失衡易伤区
      × **伤害等级区** × **异常增伤区** × **异常暴击区**
    """
    snapshot = request.snapshot
    realtime = request.realtime
    target = request.target

    coefficient = attack_level_coefficient(snapshot.level)
    level_coefficient = attack_level_coefficient(target.level)

    zones: dict[str, float] = {}

    # 基础伤害区（规格 §3.1）——**基础属性按路径取**：
    #   常规直伤 → 攻击力；贯穿伤害（命破）→ **贯穿力**；
    #   锐化伤害（锋御）→ **防御力**；异常伤害 → 攻击力（命破/锋御的异常伤害仍用攻击力）。
    if request.path == "anomaly":
        base = request.multiplier * request.anomaly_multiplier * snapshot.attack
    elif request.path == "piercing":
        base = request.multiplier * snapshot.sheer_force
    elif request.path == "armorer":
        base = request.multiplier * snapshot.defense
    elif request.path == "turbulence":
        base = request.multiplier * snapshot.attack
    else:
        base = request.multiplier * snapshot.attack
    zones["基础伤害区"] = base

    # 增伤区（所有路径都有；异常伤害吃的是它的**加权和**）
    zones["增伤区"] = damage_bonus_zone(snapshot.damage_bonus)

    if request.path in ("anomaly", "turbulence"):
        zones["异常精通区"] = anomaly_mastery_zone(snapshot.anomaly_mastery)
        zones["伤害等级区"] = damage_level_zone(snapshot.level)
        zones["异常增伤区"] = anomaly_damage_bonus_zone(realtime.anomaly_damage_bonus)
        zones["异常暴击区"] = anomaly_crit_zone(
            realtime.anomaly_crit_rate, realtime.anomaly_crit_damage, request.crit_mode
        )
        if request.path == "turbulence":
            zones["乱流倍率区"] = turbulence_multiplier(
                request.base_anomaly, request.remaining_seconds
            )
        # 异常伤害**有**防御区（规格 §2 / §3.4）——它不吃常规暴击区，不是不吃防御区。
        zones["防御区"] = defense_zone(
            level_coefficient,
            effective_defense(
                target_defense(
                    _scaled_base_defense(target, level_coefficient),
                    defense_bonus=target.defense_bonus,
                    defense_reduction=realtime.defense_reduce,
                    ignore_defense=realtime.ignore_defense,
                ),
                penetration_rate=snapshot.penetration_rate,
                penetration_value=snapshot.penetration_value,
            ),
        )
    elif request.path == "armorer":
        # 锋御的直伤统称「**锐化伤害**」：基础属性换成**防御力**（规格 §3.12）。
        # 暴击不用暴击伤害结算，而用**锐暴伤害**；暴击率可超 100%，超出部分
        # 再判一次锐暴——于是锐暴伤害在公式里是**平方项**（armorer_crit_zone）。
        zones["暴击区"] = armorer_crit_zone(request.crit_rate, request.blast_damage)
        zones["锐化增伤区"] = sharpen_damage_bonus_zone(request.sharpen_damage_bonus)
        defense = target_defense(
            _scaled_base_defense(target, level_coefficient),
            defense_bonus=target.defense_bonus,
            defense_reduction=realtime.defense_reduce,
            ignore_defense=realtime.ignore_defense,
        )
        zones["防御区"] = defense_zone(
            level_coefficient,
            effective_defense(
                defense,
                penetration_rate=snapshot.penetration_rate,
                penetration_value=snapshot.penetration_value,
            ),
        )
    elif request.path == "piercing":
        # 贯穿伤害跳过防御区，改吃贯穿增伤区（规格 §2 / §3.4）。
        # 官方口径：贯穿伤害**无视 100% 防御**——防御区乘数恒为 1，
        # 这里显式记 1，白盒里能看见（而不是「没有这一项」）。
        zones["防御区"] = 1.0
        zones["贯穿增伤区"] = penetrating_damage_bonus_zone(0.0)
        zones["暴击区"] = crit_zone(request.crit_rate, request.crit_damage, request.crit_mode)
    else:
        zones["暴击区"] = crit_zone(request.crit_rate, request.crit_damage, request.crit_mode)
        defense = target_defense(
            _scaled_base_defense(target, level_coefficient),
            defense_bonus=target.defense_bonus,
            defense_reduction=realtime.defense_reduce,
            ignore_defense=realtime.ignore_defense,
        )
        zones["防御区"] = defense_zone(
            level_coefficient,
            effective_defense(
                defense,
                penetration_rate=snapshot.penetration_rate,
                penetration_value=snapshot.penetration_value,
            ),
        )

    zones["抗性区"] = resistance_zone(
        realtime.resistance,
        resistance_reduce=realtime.resistance_reduce,
        ignore_resistance=realtime.ignore_resistance,
    )
    zones["减易伤区"] = vulnerability_zone(target.easy_damage, target.damage_reduction)
    zones["失衡易伤区"] = stun_vulnerability_zone(
        request.stunned,
        stun_vulnerability=realtime.stun_vulnerability,
        unstunned_vulnerability=realtime.unstunned_stun_vulnerability,
    )
    zones["特殊乘区"] = realtime.distance_falloff

    product = 1.0
    for value in zones.values():
        product *= value
    return DamageResult(total=product, base=base, zones=zones)


def _scaled_base_defense(target: TargetParams, level_coefficient: float) -> float:
    """敌人的实际防御 = 1 级基础防御 / 50 × 攻击方等级基数（规格 §3.4）。"""
    return target.base_defense / 50.0 * level_coefficient


__all__ = [
    "CritMode",
    "DamageInput",
    "DamagePath",
    "DamageResult",
    "RealtimeReadings",
    "SnapshotReadings",
    "TargetParams",
    "compute_damage",
]
