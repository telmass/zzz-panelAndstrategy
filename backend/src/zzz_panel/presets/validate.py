"""预设数据的语义校验。

结构合法性由 Pydantic 负责（``schemas/presets.py``），这里只查**结构查不
出来**的东西：id 重复、取值不在允许集合内、跨字段等式不成立。

设计原则
--------
1. **只允许有意义的失败。** 不去校验「值必须大于 0」这类规则——Wiki 上出现
   0 是数据事实，不是错误。真正的错误只有两类：id 重复，以及某条预设**在
   当前规则表下根本无法表达**（核心加成凑不满两个槽位、每级数值与选项值对
   不上、音擎基础值缺失）。
2. **一条错误只报一次。** 同一条预设的多个问题不重复刷屏。
3. **可推导的量要核对，但不必存储。** 例如「官方没给哪几项基础属性」由
   ``base`` 的缺键表达，不另存一个数组；「哪几项缺是合法的」由这里的规则
   判定——**命破模式**缺 ``pr`` 与 ``er``（这两个位置被贯穿力 / 闪能自动
   累积取代），其余模式十项必须齐全。

「与规则表不一致」是**告警**而非错误：代理人的核心加成在 Wiki 上的措辞
可能与规则表的规范名不同（例：``ep-1791`` 把「攻击力」写作「攻击力百分比」），
那是措辞差异，不是数据错误。
"""

from __future__ import annotations

from typing import Iterable, List, Sequence

from ..core.constants import DISC_FIXED_STATS
from ..core.options import (
    CORE_OPTIONS,
    RuleOption,
    find_option,
    modifier_keys,
)
from ..schemas.presets import AgentPreset, WeaponPreset
from .attributes import AGENT_ATTRIBUTES, AGENT_GRADES

#: 代理人 / 音擎职业标签全集，用于校验 ``roleTag``。与前端
#: ``AGENT_ROLE_TAGS`` 同源。
#:
#: 中英对照：强攻Attack、击破Stun、异常Anomaly、支援Support、防护Defense、
#: 命破Rupture、锋御Armorer。取值保持中文，英文仅用于图标文件名与展示转换。
AGENT_ROLE_TAGS = frozenset({"强攻", "击破", "异常", "支援", "防护", "命破", "锋御"})

#: 基础面板的全部键。缺哪些键表示官方未提供。
BASE_KEYS = ("hp", "atk", "def", "impact", "cr", "cd", "ac", "am", "pr", "er")

#: 命破模式**允许缺失**的基础键：这两个位置被贯穿力 / 闪能自动累积取代，
#: 官方基础面板里本来就不列。
RUPTURE_OPTIONAL_BASE_KEYS = ("pr", "er")

#: 命破模式**必须**存在的额外基础键。
EXTRA_BASE_KEYS = ("penforce", "energyAccumulation")

#: 浮点比较容差。与 legacy 的 1e-7 一致。
_EPS = 1e-7

#: 驱动盘 1/2/3 号固定主词条占用的修正量。音擎的固定副词条不能撞上它们。
_FIXED_MAIN_STAT_TARGETS = frozenset(stat.to for stat in DISC_FIXED_STATS)

#: 音擎基础值的两种取值。
WEAPON_BASE_KINDS = ("atk", "def")


class PresetValidationError(Exception):
    """预设数据违反语义规则。消息里带上是哪一条、哪个代理人。"""


def _fail(where: str, message: str) -> None:
    raise PresetValidationError(f"{where}：{message}")


def _duplicate_ids(items: Sequence[object], id_of) -> None:
    seen: set[str] = set()
    for item in items:
        ident = id_of(item)
        if ident in seen:
            _fail("预设数据", f"id 重复 {ident!r}")
        seen.add(ident)


def _check_core_bonus(agent: AgentPreset, bonus, options: Sequence[RuleOption]) -> None:
    where = f"代理人 {agent.id}（{agent.name}）"
    option = find_option(options, bonus.option_id)
    if option is None:
        _fail(where, f"核心加成引用了未登记的选项 {bonus.option_id!r}")

    count = bonus.option_count or 1
    if count < 1:
        _fail(where, f"核心加成 {bonus.option_id!r} 的槽位数必须至少为 1")

    if not bonus.ranks:
        _fail(where, f"核心加成 {bonus.option_id!r} 缺少生效位次")
    for rank in bonus.ranks:
        if rank not in "ABCDEF":
            _fail(where, f"核心加成 {bonus.option_id!r} 的位次 {rank!r} 非法")

    # 合计 = 选项值 × 槽位数：这条是「该代理人的核心加成能否由通用核心选项
    # 表达」的判据，对不上就意味着这条预设在当前规则表下无法载入。
    if abs(option.value * count - bonus.total_value) > _EPS:
        _fail(
            where,
            f"核心加成 {bonus.option_id!r} 的合计 {bonus.total_value} 与选项值 "
            f"{option.value} × {count} 槽对不上",
        )

    # 每级数值 × 位次数 = 合计：抓取脚本按 Wiki 的「每级 +X」抄的，
    # 这里核对它与位次数量自洽。
    if abs(bonus.per_rank * len(bonus.ranks) - bonus.total_value) > _EPS:
        _fail(
            where,
            f"核心加成 {bonus.option_id!r} 的每级数值 {bonus.per_rank} × "
            f"{len(bonus.ranks)} 位与合计 {bonus.total_value} 对不上",
        )


def validate_agents(agents: Sequence[AgentPreset]) -> None:
    """校验全部代理人预设。任何一条不合规则抛 :class:`PresetValidationError`。"""
    _duplicate_ids(agents, lambda a: a.id)
    for agent in agents:
        where = f"代理人 {agent.id}（{agent.name}）"
        if not agent.name:
            _fail(where, "缺少名称")
        if not agent.role_tag:
            _fail(where, "缺少 roleTag")
        if agent.role_tag not in AGENT_ROLE_TAGS:
            _fail(where, f"roleTag“{agent.role_tag}”不属于 {sorted(AGENT_ROLE_TAGS)}")
        if not agent.attribute:
            _fail(where, "缺少 attribute")
        if agent.attribute not in AGENT_ATTRIBUTES:
            _fail(where, f"attribute“{agent.attribute}”不属于 {sorted(AGENT_ATTRIBUTES)}")
        if not agent.grade:
            _fail(where, "缺少 grade")
        if agent.grade not in AGENT_GRADES:
            _fail(where, f"grade“{agent.grade}”不属于 {sorted(AGENT_GRADES)}")
        if agent.panel_mode not in ("standard", "rupture", "armorer"):
            _fail(where, f"未知的面板模式 {agent.panel_mode!r}")
        if not agent.source:
            _fail(where, "缺少数据来源链接")

        # 基础面板：命破模式缺 pr/er 合法（这两个位置被贯穿力 / 闪能自动
        # 累积取代），其余模式十项必须齐全。官方给出 0 是数据事实，不是错误，
        # 故只查「键在不在」，不查「值是不是正」。
        present = set(agent.base.model_dump(by_alias=True, exclude_none=True).keys())
        unknown = present - set(BASE_KEYS)
        if unknown:
            _fail(where, f"基础面板多出未知属性 {sorted(unknown)}")
        required = set(BASE_KEYS)
        if agent.panel_mode == "rupture":
            required -= set(RUPTURE_OPTIONAL_BASE_KEYS)
        missing = required - present
        if missing:
            _fail(where, f"基础面板缺少 {sorted(missing)}")

        # 命破专属的额外基础属性。
        extra_base = agent.base_extra or {}
        for key in extra_base:
            if key not in EXTRA_BASE_KEYS:
                _fail(where, f"未知的额外基础属性 {key!r}")
        if agent.panel_mode == "rupture":
            for key in EXTRA_BASE_KEYS:
                if key not in extra_base:
                    _fail(where, f"命破模式缺少额外基础属性 {key!r}")

        for stat in agent.base_unmodeled or []:
            if not stat.label:
                _fail(where, "未建模属性缺少名称")

        # 核心加成：展开后必须恰好填满两个核心槽位。
        if not agent.core:
            _fail(where, "缺少核心加成")
        slots = 0
        for bonus in agent.core:
            _check_core_bonus(agent, bonus, CORE_OPTIONS)
            slots += bonus.option_count or 1
        if slots != 2:
            _fail(where, f"核心加成展开后占 {slots} 个槽位，应为 2 个")


def validate_weapons(weapons: Sequence[WeaponPreset]) -> None:
    """校验全部音擎预设。"""
    _duplicate_ids(weapons, lambda w: w.id)
    keys = modifier_keys()
    for weapon in weapons:
        where = f"音擎 {weapon.id}（{weapon.name}）"
        if not weapon.name:
            _fail(where, "缺少名称")
        if not weapon.role_tag:
            _fail(where, "缺少 roleTag")
        if weapon.role_tag not in AGENT_ROLE_TAGS:
            _fail(where, f"roleTag“{weapon.role_tag}”不属于 {sorted(AGENT_ROLE_TAGS)}")
        if not weapon.source:
            _fail(where, "缺少数据来源链接")
        if weapon.base.kind not in WEAPON_BASE_KINDS:
            _fail(where, f"基础值类型 {weapon.base.kind!r} 非法")
        if weapon.base.value <= 0:
            _fail(where, "基础值必须为正")
        if weapon.substat.kind not in ("pct", "flat"):
            _fail(where, f"固定副词条的类型 {weapon.substat.kind!r} 非法")
        if weapon.substat.to not in keys:
            _fail(where, f"固定副词条指向了未知的修正量 {weapon.substat.to!r}")
        if weapon.substat.to in _FIXED_MAIN_STAT_TARGETS:
            _fail(where, f"固定副词条 {weapon.substat.to!r} 与驱动盘固定主词条重复")


def core_bonus_label_warnings(agents: Iterable[AgentPreset]) -> List[str]:
    """核心加成的 ``label`` 与规则表规范名不一致时给出告警。

    措辞差异不是数据错误（``ep-1791`` 把「攻击力」写作「攻击力百分比」），
    因此只告警不失败。返回的字符串可直接展示给维护者。
    """
    names = {option.id: option.name for option in CORE_OPTIONS}
    warnings: List[str] = []
    for agent in agents:
        for bonus in agent.core:
            expected = names.get(bonus.option_id)
            if expected and bonus.label != expected:
                warnings.append(
                    f"代理人 {agent.id}（{agent.name}）的核心加成 {bonus.option_id!r} "
                    f"写作「{bonus.label}」，规则表规范名为「{expected}」"
                )
    return warnings


__all__ = [
    "AGENT_ROLE_TAGS",
    "BASE_KEYS",
    "EXTRA_BASE_KEYS",
    "PresetValidationError",
    "RUPTURE_OPTIONAL_BASE_KEYS",
    "core_bonus_label_warnings",
    "validate_agents",
    "validate_weapons",
]
