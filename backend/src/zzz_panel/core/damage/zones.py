"""伤害乘区——纯函数，零 I/O。

规格真源是 ``docs/design/damage-formulas.md``；本模块**只实现**那份规格，
不得自行发明公式。每条函数的 docstring 指向规格里的对应条款编号。

两条全局约定：

- **增伤区分四类**（常规 / 贯穿 / 异常 / 直接攻击），跨区相乘、同区加算——
  见规格 §2。
- 所有乘区都有**有效范围**，越界即 clamp；clamp 之后的结果仍参与后续乘算。
"""

from __future__ import annotations

import math
from typing import Literal

# ---------------------------------------------------------------- 等级基数

#: 60 级及以上的攻击方等级基数（规格 §3.4）。
#:
#: 60 级以下官方是查表（18 / 30 / 52 级有 ±1 误差），本表尚未取得，
#: 所以低等级**显式报错**而不是给个近似值——近似值会静默地算错。
ATTACK_LEVEL_COEFFICIENT_MAX_LEVEL = 60
ATTACK_LEVEL_COEFFICIENT = 794.0


def attack_level_coefficient(level: int) -> float:
    """攻击方等级基数（规格 §3.4，契约 C4）。

    满级口径：一律按 60 级（794）计算，不考虑更低等级。
    """
    return ATTACK_LEVEL_COEFFICIENT


# ---------------------------------------------------------------- 增伤区


def damage_bonus_zone(total: float) -> float:
    """增伤区 = 1 + Σ增伤（规格 §3.2，契约 C5 / C27）。

    同一区内的来源**相加**；「造成的伤害降低」也是这一区（减伤）。
    有效范围 ``[0, 6]``。
    """
    return _clamp(1.0 + total, 0.0, 6.0)


def penetrating_damage_bonus_zone(total: float) -> float:
    """贯穿增伤区 = 1 + Σ贯穿增伤（规格 §3.8）。有效范围 ``[0.2, 9]``。"""
    return _clamp(1.0 + total, 0.2, 9.0)


def sharpen_damage_bonus_zone(total: float) -> float:
    """锐化增伤区 = 1 + Σ锐化增伤（锋御专有，规格 §3.12，契约 C33）。

    官方口径：**独立乘区**，与常规增伤区**独立计算、互不稀释**——与命破的
    贯穿增伤区同理。量级约 **10%**。

    ⚠️ 官方**没有公布**这个乘区的有效范围（只给了量级），这里取一个宽松的
    ``[0, 10]`` 作钳制；有官方数值后应收紧。
    """
    return _clamp(1.0 + total, 0.0, 10.0)


def anomaly_damage_bonus_zone(total: float) -> float:
    """异常增伤区 = 1 + Σ异常增伤（规格 §3.6，契约 C7）。

    属性异常 / 紊乱 / 异放 / 乱流增伤**同属这一区**，相加。
    有效范围 ``[0, 3]``。
    """
    return _clamp(1.0 + total, 0.0, 3.0)


# ---------------------------------------------------------------- 暴击区

CritMode = Literal["crit", "non_crit", "expected"]


def crit_zone(crit_rate: float, crit_damage: float, mode: CritMode = "expected") -> float:
    """暴击区（规格 §3.3，契约 C26）。

    - 暴击时 ``1 + 暴击伤害``；未暴击时 ``1``；
    - 期望 ``1 + 暴击率 × 暴击伤害``。

    暴击率 clamp 到 ``[0, 1]``、暴击伤害 clamp 到 ``[0, 5]``，
    因此暴击区落在 ``[1, 6]``。
    """
    rate = _clamp(crit_rate, 0.0, 1.0)
    damage = _clamp(crit_damage, 0.0, 5.0)
    if mode == "crit":
        return 1.0 + damage
    if mode == "non_crit":
        return 1.0
    return 1.0 + rate * damage


def anomaly_crit_zone(anomaly_crit_rate: float, anomaly_crit_damage: float, mode: CritMode = "expected") -> float:
    """异常暴击区（规格 §3.3，契约 C9）。

    异常伤害**不吃**常规暴击区（契约 C8），它有自己的暴击率与暴击伤害。
    有效范围 ``[1, 3]``。
    """
    rate = _clamp(anomaly_crit_rate, 0.0, 1.0)
    damage = _clamp(anomaly_crit_damage, 0.0, 5.0)
    if mode == "crit":
        return 1.0 + damage
    if mode == "non_crit":
        return 1.0
    return 1.0 + rate * damage


def fengyu_crit_zone(crit_rate: float, blast_damage: float) -> float:
    """锋御（锐化伤害）的暴击区——**平方项**结构（规格 §3.12，契约 C32）。

    锋御的暴击**不用暴击伤害结算，而用「锐暴伤害」**；并且暴击率**可以超过
    100%**——超出的部分会**再判定一次锐暴**。于是：

    - 暴击一次 → ``k = 1 + 锐暴伤害``
    - 暴击两次 → ``k²``（锐暴伤害在公式里是**平方项**）

    期望（按官方口径）：

    - 暴击率 ≤ 100%：``c × k``（公式与常规一样，只是把暴击伤害换成锐暴伤害）
    - 暴击率 > 100%：``k × [1 + (c − 1) × k]``
      —— 官方原话是「暴击率多个 -1，然后外层再乘一次 (1 + 锐暴伤害)」。

    默认锐暴伤害 150% 时，暴击一次的乘区是 2.5、两次是 6.25。
    """
    rate = max(0.0, crit_rate)
    k = 1.0 + max(0.0, blast_damage)
    if rate <= 1.0:
        return rate * k
    return k * (1.0 + (rate - 1.0) * k)


# ---------------------------------------------------------------- 防御区


def target_defense(
    base_defense: float,
    defense_bonus: float = 0.0,
    defense_reduction: float = 0.0,
    ignore_defense: float = 0.0,
) -> float:
    """受击方防御（规格 §3.4）。

    ```
    (基础防御 × (1 + 初始防御%) + 初始固定防御) × (1 + 防御加成% − 防御降低% − 无视防御%)
    ```

    **无视防御与减防加算**（契约 C14）；穿透率不在这一步，它在 :func:`defense_zone` 里乘。
    """
    percent = 1.0 + defense_bonus - defense_reduction - ignore_defense
    return max(0.0, base_defense * percent)


def effective_defense(
    defense: float,
    penetration_rate: float = 0.0,
    penetration_value: float = 0.0,
) -> float:
    """受击方有效防御 = 防御 × (1 − 穿透率%) − 穿透值，下限 0（规格 §3.4）。

    **穿透率是乘法**，与减防不等价（契约 C15）。
    """
    return max(0.0, defense * (1.0 - penetration_rate) - penetration_value)


def defense_zone(
    level_coefficient: float,
    effective_def: float,
) -> float:
    """防御区 = 等级基数 / (有效防御 + 等级基数)（规格 §3.4，契约 C1 / C2 / C3）。

    有效防御已由 :func:`effective_defense` clamp 到 ≥ 0，所以防御区 ≤ 1。
    """
    if effective_def <= 0:
        return 1.0
    return level_coefficient / (effective_def + level_coefficient)


# ---------------------------------------------------------------- 抗性区


def resistance_zone(
    resistance: float,
    resistance_reduce: float = 0.0,
    ignore_resistance: float = 0.0,
) -> float:
    """抗性区 = 1 − 受击方抗性 + 抗性降低 + 无视抗性（规格 §3.5，契约 C12）。

    弱点属性抗性 −0.2 → 1.2；抗性属性抗性 +0.2 → 0.8。
    有效范围 ``[0, 2]``。
    """
    return _clamp(1.0 - resistance + resistance_reduce + ignore_resistance, 0.0, 2.0)


# ---------------------------------------------------------------- 减易伤 / 失衡易伤


def vulnerability_zone(easy_damage: float = 0.0, damage_reduction: float = 0.0) -> float:
    """减易伤区 = 1 + 受击方易伤 − 受击方减伤（规格 §3.7，契约 C13）。

    有效范围 ``[0.2, 2]``——叠减伤**到不了**无伤。
    """
    return _clamp(1.0 + easy_damage - damage_reduction, 0.2, 2.0)


def stun_vulnerability_zone(
    stunned: bool,
    stun_vulnerability: float = 0.0,
    unstunned_vulnerability: float = 0.0,
) -> float:
    """失衡易伤区（规格 §3.7，契约 C31）。

    **参数是「倍率」不是「区」**：失衡时 ``1 + 失衡易伤倍率``、未失衡时
    ``1 + 未失衡倍率``。敌人的失衡易伤倍率默认有 25% / 50% / 100% 三种，
    对应区 1.25 / 1.5 / 2.0。

    有效范围：失衡时 ``[0.2, 5]``、未失衡时 ``[1, 3]``。
    """
    if stunned:
        return _clamp(1.0 + stun_vulnerability, 0.2, 5.0)
    return _clamp(1.0 + unstunned_vulnerability, 1.0, 3.0)


# ---------------------------------------------------------------- 异常侧


def anomaly_mastery_zone(anomaly_mastery: float) -> float:
    """异常精通区 = 异常精通 / 100（规格 §3.6）。

    有效范围 ``[0, 10]``（1.4 版本之前是 ``[0, 6]``）。
    """
    return _clamp(anomaly_mastery / 100.0, 0.0, 10.0)


def damage_level_zone(level: int) -> float:
    """伤害等级区 = trunc(1 + (等级 − 1) / 59, 4)（规格 §3.6，契约 C11）。

    1 级 = 1.0000，30 级 = 1.4915，60 级 = 2.0000。
    """
    return math.trunc((1.0 + (level - 1) / 59.0) * 10000.0) / 10000.0


def anomaly_control_zone(anomaly_control: float) -> float:
    """异常掌控区 = 异常掌控 / 100，**向下取整**（规格 §3.6，契约 C10）。

    积蓄公式读它，带小数会算出 ``38.332`` 这种不可能的暴击率，
    所以是 floor 而不是 round。有效范围 ``[0, 3]``。
    """
    return _clamp(math.floor(anomaly_control) / 100.0, 0.0, 3.0)


def anomaly_accumulation_zone(
    base_accumulation: float,
    anomaly_control: float,
    accumulation_efficiency: float = 1.0,
    accumulation_resistance: float = 0.0,
    accumulation_resistance_reduce: float = 0.0,
    distance_falloff: float = 1.0,
) -> float:
    """异常积蓄值（规格 §3.6）。

    ```
    基础异常积蓄值 × 异常掌控区 × 异常积蓄效率区 × 异常积蓄抗性区 × 距离衰减区
    ```

    异常积蓄抗性区 = 1 − 抗性 + 抗性降低（弱点 −0.2 → 1.2）。
    """
    control = anomaly_control_zone(anomaly_control)
    resistance = _clamp(1.0 - accumulation_resistance + accumulation_resistance_reduce, 0.0, 2.0)
    return base_accumulation * control * accumulation_efficiency * resistance * distance_falloff


# ---------------------------------------------------------------- 失衡


def stun_value_zone(
    impact: float,
    stagger_multiplier: float,
    stagger_resistance: float = 0.0,
    stagger_value_bonus: float = 0.0,
    stagger_value_reduction: float = 0.0,
    received_stagger_value_bonus: float = 0.0,
    received_stagger_value_reduction: float = 0.0,
    distance_falloff: float = 1.0,
) -> float:
    """失衡值累积（规格 §3.10，契约 C21~C23）。

    ```
    Σ(基础失衡区) × 失衡抗性区 × 失衡值提升区 × 受到失衡值提升区 × 距离衰减区
    基础失衡区 = 冲击力 × 失衡倍率
    失衡抗性区 = 1 − 受击方失衡抗性        # 弱点 −0.2 → 1.2；抗性 +0.2 → 0.8
    失衡值提升区 = 1 + 造成失衡值提升 − 造成失衡值降低
    受到失衡值提升区 = 1 + 受到失衡值提升 − 受到失衡值降低
    ```

    冲击力有效范围 ``[0, 1000]``；各区有效范围见规格。
    """
    base = _clamp(impact, 0.0, 1000.0) * stagger_multiplier
    resistance = _clamp(1.0 - stagger_resistance, 0.0, 2.0)
    bonus = _clamp(1.0 + stagger_value_bonus - stagger_value_reduction, 0.0, 4.0)
    received = _clamp(
        1.0 + received_stagger_value_bonus - received_stagger_value_reduction, 0.0, 4.0
    )
    return base * resistance * bonus * received * distance_falloff


def disorder_stagger_level_zone(level: int) -> float:
    """紊乱失衡等级区 = 1 + 0.0075 × 等级（规格 §3.10，契约 C22）。

    1 级 1.0075，60 级 1.45。
    """
    return 1.0 + 0.0075 * level


# ---------------------------------------------------------------- 乱流（风属性）

#: 乱流按基底异常分的固定倍率 + 时间项（规格 §3.13）。
#:
#: 键为基底异常的属性/名称；值为 (固定倍率, 时间项系数 k, 时间归一化分母)。
#: 时间项 = floor(T / 分母) × k。
TURBULENCE_BASES = {
    "physical": (8.0, 0.075, 1.0),
    "ice": (13.0, 0.075, 1.0),
    "fire": (9.0, 0.50, 0.5),
    "electric": (6.5, 1.25, 1.0),
    "ether": (6.5, 0.625, 0.5),
    "frost": (0.0, 0.75, 1.0),
}


def laceration_crit_zone(crit_rate, laceration_value, mode="expected"):
    L = max(0.0, laceration_value)
    cr = max(0.0, crit_rate)
    p1 = min(1.0, max(0.0, cr))
    p2 = min(1.0, max(0.0, cr - 1.0))
    if mode in ("nonCrit", "non_crit"):
        return 1.0
    if mode in ("sharpCrit", "sharp_crit"):
        return 1.0 + L
    if mode in ("lacerationCrit", "laceration_crit"):
        return (1.0 + L) ** 2
    return (1.0 + p1 * L) * (1.0 + p2 * L)


def turbulence_multiplier(base: str, remaining_seconds: float) -> float:
    """乱流倍率 = 固定倍率 + 时间项（规格 §3.13）。

    ``base`` 为基底异常的属性/名称（physical/ice/fire/electric/ether/frost）；
    ``remaining_seconds`` 为非风基底异常的剩余时间 ``T``。
    """
    fixed, k, denom = TURBULENCE_BASES.get(base, TURBULENCE_BASES["physical"])
    import math as _math

    time_term = _math.floor(remaining_seconds / denom) * k
    return fixed + time_term


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


__all__ = [
    "ATTACK_LEVEL_COEFFICIENT",
    "anomaly_accumulation_zone",
    "anomaly_control_zone",
    "anomaly_crit_zone",
    "anomaly_damage_bonus_zone",
    "anomaly_mastery_zone",
    "attack_level_coefficient",
    "crit_zone",
    "fengyu_crit_zone",
    "damage_bonus_zone",
    "damage_level_zone",
    "defense_zone",
    "disorder_stagger_level_zone",
    "effective_defense",
    "penetrating_damage_bonus_zone",
    "resistance_zone",
    "sharpen_damage_bonus_zone",
    "stun_value_zone",
    "stun_vulnerability_zone",
    "TURBULENCE_BASES",
    "turbulence_multiplier",
    "laceration_crit_zone",
    "target_defense",
    "vulnerability_zone",
]
