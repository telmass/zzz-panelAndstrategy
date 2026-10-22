"""基准目标（标准敌人）——配装比较的**可比对象**。

规格见 ``docs/design/damage-formulas.md`` §7。乘区公式是确定的，但「打谁」
决定数值——没有固定的目标，两套配装的伤害就没有可比性。

本模块给出**一个**标准目标（60 级以上首领）与各档敌人的基础防御区间，
全部来自《数据机制导论 2.0 版》的官方数值（见规格 §5 的出处）。

> **不是完整的敌人数据库**：法厄同图鉴里的逐属性弱点 / 抗性分布、失衡上限、
> 特殊机制（如秽盾减伤、庞培的电抗性 0.4）都**没有**收录。
> 需要更精细的比较时，先扩这里。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TargetPreset:
    """一个基准目标。

    ``base_defense`` 是**1 级**基础防御力：实际防御 = ``base_defense / 50 ×
    攻击方等级基数``（规格 §3.4）。60 级首领因此是 ``60 / 50 × 794 = 952.8``。

    ``attribute_resistance`` 是「被攻击的那个属性」的抗性值：弱点属性 ``-0.2``
    （抗性区 1.2）、抗性属性 ``+0.2``（抗性区 0.8）。**调用方决定打哪个属性**——
    标准目标默认按弱点算。
    """

    id: str
    name: str
    level: int = 60
    base_defense: float = 60.0
    attribute_resistance: float = -0.2
    stagger_resistance: float = 0.2
    stun_vulnerability: float = 1.0
    unstunned_stun_vulnerability: float = 1.0
    easy_damage: float = 0.0
    damage_reduction: float = 0.0
    notes: str = ""


#: 1 级基础防御力的官方区间（规格 §3.4）。
#:
#: 普通 36~46、精英 45~54、杜拉罕 58、首领 60。
ENEMY_BASE_DEFENSE = {
    "normal": (36.0, 46.0),
    "elite": (45.0, 54.0),
    "dulahn": (58.0, 58.0),
    "boss": (60.0, 60.0),
}

#: 标准目标：60 级以上首领。
#:
#: 官方算例的锚点——「60 级代理人攻击 60 级以上首领，默认情况防御区为
#: 794 / (952.8 + 794) = 0.4545」，伤害引擎的验收契约 C01 就钉在这个数上。
STANDARD_TARGET = TargetPreset(
    id="boss-60",
    name="60 级以上首领（标准目标）",
    level=60,
    base_defense=60.0,
    attribute_resistance=-0.2,
    stagger_resistance=0.2,
    stun_vulnerability=1.0,
    unstunned_stun_vulnerability=1.0,
    notes=(
        "默认按**弱点属性**算（抗性 −0.2 → 抗性区 1.2）；"
        "打抗性属性时把 attribute_resistance 改成 +0.2。"
        "失衡易伤倍率取 100%（大部分首领的默认值）。"
    ),
)

#: 普通敌人（官方区间 36~46，这里取**上界**；取下界会更软）。
#:
#: 失衡易伤倍率取 50%（官方：绝大部分敌人是 50% 或 100%）。
NORMAL_TARGET = TargetPreset(
    id="normal-60",
    name="60 级普通敌人",
    level=60,
    base_defense=46.0,
    attribute_resistance=-0.2,
    stagger_resistance=0.2,
    stun_vulnerability=0.5,
    unstunned_stun_vulnerability=1.0,
    notes=(
        "官方 1 级基础防御区间 36~46，本预设取**上界**；"
        "失衡易伤倍率取 50%（默认 25% 的敌人多带特殊机制）。"
    ),
)

#: 精英敌人（官方区间 45~54，取**上界**）。
ELITE_TARGET = TargetPreset(
    id="elite-60",
    name="60 级精英敌人",
    level=60,
    base_defense=54.0,
    attribute_resistance=-0.2,
    stagger_resistance=0.2,
    stun_vulnerability=0.5,
    unstunned_stun_vulnerability=1.0,
    notes="官方 1 级基础防御区间 45~54，本预设取**上界**。",
)

#: 杜拉罕（官方 1 级基础防御 **58**，唯一值）。
DULANH_TARGET = TargetPreset(
    id="dulahn-60",
    name="60 级杜拉罕",
    level=60,
    base_defense=58.0,
    attribute_resistance=-0.2,
    stagger_resistance=0.2,
    stun_vulnerability=0.5,
    unstunned_stun_vulnerability=1.0,
    notes="官方 1 级基础防御 58（唯一值）。",
)

#: 全部基准目标。
#:
#: 顺序即「推荐度」：首领是默认目标（官方算例的锚点）。
STANDARD_TARGETS: tuple[TargetPreset, ...] = (
    STANDARD_TARGET,
    ELITE_TARGET,
    NORMAL_TARGET,
    DULANH_TARGET,
)


def to_params(preset: TargetPreset):
    """基准目标 -> 引擎用的 :class:`~zzz_panel.core.damage.engine.TargetParams`。"""
    from .engine import TargetParams

    return TargetParams(
        level=preset.level,
        base_defense=preset.base_defense,
        stagger_resistance=preset.stagger_resistance,
        easy_damage=preset.easy_damage,
        damage_reduction=preset.damage_reduction,
        stun_vulnerability=preset.stun_vulnerability,
        unstunned_stun_vulnerability=preset.unstunned_stun_vulnerability,
    )


__all__ = [
    "DULANH_TARGET",
    "ELITE_TARGET",
    "ENEMY_BASE_DEFENSE",
    "NORMAL_TARGET",
    "STANDARD_TARGET",
    "STANDARD_TARGETS",
    "TargetPreset",
    "to_params",
]


#: 敌人逐属性抗性取值（白板，无 Buff）——与 ZZZ-HP 一致。
ENEMY_RESISTANCE_VALUE_MAP = {"weak": -0.2, "normal": 0.0, "res20": 0.2, "res40": 0.4}


def enemy_attribute_resistance(enemy_id: str, attribute: str) -> float:
    """按敌人 + 属性查白板抗性；查不到回落到弱点（-0.2）。"""
    try:
        import json
        from pathlib import Path

        path = Path("data/catalog/enemy-attributes.json")
        if not path.is_file():
            path = Path(__file__).resolve().parents[4] / "data" / "catalog" / "enemy-attributes.json"
        if not path.is_file():
            return 0.0
        for entry in json.loads(path.read_text(encoding="utf-8")):
            if entry.get("id") != enemy_id:
                continue
            er = (entry.get("elementResistance") or {}).get(attribute, "weak")
            return ENEMY_RESISTANCE_VALUE_MAP.get(er, -0.2)
    except Exception:
        pass
    return -0.2
