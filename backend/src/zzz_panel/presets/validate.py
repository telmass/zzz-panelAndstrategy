"""预设数据的语义校验。

结构与类型由 ``schemas/presets.py`` 的 Pydantic 模型拦下；本模块管那些
需要查 ``core.options`` 或跨字段比较的规则。规则清单见
``docs/data-schema.md``「校验规则」，来源是 legacy 的
``calculator.js:47-58`` 与 ``applyAgentPreset``。

与 legacy 的差别只有一处，且是刻意的：legacy 逐条抛错、坏一条只废一条，
这里**启动时一次性全量校验，失败即整体拒绝服务**。理由是预设数据由抓取脚本
整体覆盖生成，出现坏条目几乎一定是源头或生成逻辑出了问题，此时「一半预设
可用」比「全部不可用」更难排查。
"""

from __future__ import annotations

from typing import NoReturn

from ..core.options import CORE_OPTIONS, find_option
from ..schemas.presets import AgentCoreBonus, AgentPreset, WeaponPreset
from .attributes import AGENT_ATTRIBUTES, AGENT_GRADES

#: 代理人标签全集，用于校验 ``roleTag``。与前端 ``AGENT_ROLE_TAGS`` 同源。
AGENT_ROLE_TAGS = frozenset({"强攻", "击破", "异常", "支援", "防护", "命破", "锋御"})

#: 基础面板的键序，同时用于「缺失的键必须在 unavailableBaseStats 中」这条检查。
BASE_KEYS = ("hp", "atk", "def", "impact", "cr", "cd", "ac", "am", "pr", "er")

#: 核心槽位数量。一名代理人的核心加成展开后必须恰好填满。
CORE_SLOTS = 2

#: 浮点比较容差，与 legacy 的 1e-7 一致。
EPSILON = 1e-7


class PresetValidationError(ValueError):
    """预设数据不满足校验规则。消息里带上是哪一条预设，便于定位。"""


def _fail(name: str, reason: str) -> NoReturn:
    raise PresetValidationError(f"{name}：{reason}")


def _check_core_bonus(name: str, bonus: AgentCoreBonus) -> int:
    """校验单条核心加成，返回它占用的核心槽位数。"""
    option = find_option(CORE_OPTIONS, bonus.option_id)
    if option is None:
        _fail(name, f"核心加成“{bonus.label}”引用了不存在的核心选项 {bonus.option_id}")

    count = bonus.count
    if count < 1:
        _fail(name, f"核心加成“{bonus.label}”的 optionCount={count}，至少为 1")

    if abs(option.value * count - bonus.total_value) > EPSILON:
        _fail(
            name,
            f"核心加成“{bonus.label}”合计 {bonus.total_value} 无法由选项 "
            f"{option.id}×{count}（{option.value * count}）准确表示",
        )

    if not bonus.ranks:
        _fail(name, f"核心加成“{bonus.label}”缺少核心技位次")
    if abs(bonus.per_rank_value * len(bonus.ranks) - bonus.total_value) > EPSILON:
        _fail(
            name,
            f"核心加成“{bonus.label}”每级 {bonus.per_rank_value}×{len(bonus.ranks)} 位次 "
            f"与合计 {bonus.total_value} 不一致",
        )

    return count


def _check_agent(agent: AgentPreset) -> None:
    name = agent.name or agent.id

    if not agent.name:
        _fail(agent.id, "缺少 name")
    if not agent.role_tag:
        _fail(name, "缺少 roleTag")
    if agent.role_tag not in AGENT_ROLE_TAGS:
        _fail(name, f"roleTag“{agent.role_tag}”不属于 {sorted(AGENT_ROLE_TAGS)}")

    # attribute / grade：只校验取值，特殊属性的判定是另一回事，见 presets.attributes。
    if not agent.attribute:
        _fail(name, "缺少 attribute")
    if agent.attribute not in AGENT_ATTRIBUTES:
        _fail(name, f"attribute“{agent.attribute}”不属于 {sorted(AGENT_ATTRIBUTES)}")
    if not agent.grade:
        _fail(name, "缺少 grade")
    if agent.grade not in AGENT_GRADES:
        _fail(name, f"grade“{agent.grade}”不属于 {sorted(AGENT_GRADES)}")

    # 基础面板：官方未提供的键必须显式列进 unavailableBaseStats，否则前端会
    # 把 None 当 0 写进面板，且用户看不到任何提示。
    unavailable = set(agent.unavailable_base_stats or ())
    if unavailable - set(BASE_KEYS):
        _fail(name, f"unavailableBaseStats 含非基础面板键 {sorted(unavailable - set(BASE_KEYS))}")
    provided = {
        key for key in BASE_KEYS
        if getattr(agent.base, key if key != "def" else "def_") is not None
    }
    missing = set(BASE_KEYS) - provided - unavailable
    if missing:
        _fail(name, f"基础面板缺少 {sorted(missing)}，且未列入 unavailableBaseStats")

    additional = agent.additional_base_stats
    if agent.panel_mode == "rupture":
        if additional is None:
            _fail(name, "命破模式缺少 additionalBaseStats")
        if additional.penforce is None or additional.energy_accumulation is None:
            _fail(name, "命破模式的 additionalBaseStats 缺少 penforce 或 energyAccumulation")

    if not agent.core_bonuses:
        _fail(name, "缺少 coreBonuses")
    slots = sum(_check_core_bonus(name, bonus) for bonus in agent.core_bonuses)
    if slots != CORE_SLOTS:
        _fail(name, f"核心加成展开后占 {slots} 个槽位，应恰好为 {CORE_SLOTS} 个")


def _check_weapon(weapon: WeaponPreset) -> None:
    name = weapon.name or weapon.id

    if not weapon.name:
        _fail(weapon.id, "缺少 name")
    if not weapon.role_tag:
        _fail(name, "缺少 roleTag")
    if weapon.role_tag not in AGENT_ROLE_TAGS:
        _fail(name, f"roleTag“{weapon.role_tag}”不属于 {sorted(AGENT_ROLE_TAGS)}")
    if weapon.base_kind == "atk" and weapon.base_attack == 0:
        _fail(name, "baseKind=atk 但 baseAttack 为 0")
    if weapon.base_kind == "def" and weapon.base_defense == 0:
        _fail(name, "baseKind=def 但 baseDefense 为 0")
    if not weapon.substat.to:
        _fail(name, "substat.to 为空，无法确定修正目标")


def _check_unique_ids(items: list, origin: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item.id in seen:
            duplicates.add(item.id)
        seen.add(item.id)
    if duplicates:
        raise PresetValidationError(f"{origin}：id 重复 {sorted(duplicates)}")


def validate_agents(agents: list[AgentPreset]) -> None:
    _check_unique_ids(agents, "代理人预设")
    for agent in agents:
        _check_agent(agent)


def validate_weapons(weapons: list[WeaponPreset]) -> None:
    _check_unique_ids(weapons, "音擎预设")
    for weapon in weapons:
        _check_weapon(weapon)


__all__ = [
    "AGENT_ROLE_TAGS",
    "PresetValidationError",
    "validate_agents",
    "validate_weapons",
]