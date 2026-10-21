"""代理人 / 音擎预设的 HTTP 契约。

线格式与 ``data/catalog/`` 下的数据文件**逐条等价**——后端不改写、不丢字段，
也不加运行时派生字段。响应因此就是源数据，前端不必再留一份副本。

形状的来龙去脉见 ``docs/design/data-schema.md``。相对早期版本的两处变化：

1. **``unavailableBaseStats`` 已删除**。「官方没给哪几项基础属性」原本存了两
   份：``base`` 里缺键 + 一个数组。数组是多余的——缺键本身就是那份事实。
   「缺哪些键是合法的」由 ``presets/validate.py`` 按规则判定：**命破模式**
   的代理人缺 ``pr`` 与 ``er``（这两个位置被贯穿力 / 闪能自动累积取代），
   其余模式十项必须齐全。
2. **音擎的基础攻击 / 基础防御合并为 ``base: {kind, value}``**。原先是三个
   字段（``baseKind`` + ``baseAttack`` + ``baseDefense``），其中恒有一个是 0，
   消歧要靠 ``baseKind``；二元组没有冗余。
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import ConfigDict, Field

from .base import CamelModel


class PresetModel(CamelModel):
    """预设模型的公共配置。

    ``exclude_none``：源数据里**没写的键就是没有**，响应里也不该冒出来一个
    ``null``。开着它，接口响应与源 JSON 才逐条等价——``base`` 缺 ``pr`` 的
    命破代理人不会被补出 ``"pr": null``，``optionCount`` 同理。
    """

    model_config = ConfigDict(
        alias_generator=CamelModel.model_config["alias_generator"],
        populate_by_name=True,
        exclude_none=True,
    )


class AgentBaseStats(PresetModel):
    """60 级基础面板。缺失的键表示官方未提供该属性。"""

    hp: Optional[float] = None
    atk: Optional[float] = None
    def_: Optional[float] = Field(default=None, alias="def")
    impact: Optional[float] = None
    cr: Optional[float] = None
    cd: Optional[float] = None
    ac: Optional[float] = None
    am: Optional[float] = None
    pr: Optional[float] = None
    er: Optional[float] = None


class UnmodeledBaseStat(PresetModel):
    """官方列了、但当前计算器未建模的基础属性。"""

    label: str
    value: float
    unit: str


class AgentCoreBonus(PresetModel):
    """一条核心加成。

    ``optionCount`` 缺省为 1（占用一个核心槽位）；``totalValue`` 与 ``unit``
    是规则表可推出的量，保留在数据里是为了让接口响应与源数据逐条等价，
    其一致性由 ``presets/validate.py`` 逐条核对。
    """

    option_id: str
    option_count: Optional[int] = None
    ranks: List[str]
    label: str
    per_rank: float
    total_value: float
    unit: str = ""

    @property
    def count(self) -> int:
        """该条占用的核心槽位数。"""
        return self.option_count or 1


class AgentPreset(PresetModel):
    """一名代理人的完整预设。"""

    id: str
    name: str
    attribute: str
    grade: str
    role_tag: str
    panel_mode: str
    source: str
    base: AgentBaseStats
    base_extra: Optional[Dict[str, float]] = None
    base_unmodeled: Optional[List[UnmodeledBaseStat]] = None
    core: List[AgentCoreBonus]


class WeaponBase(PresetModel):
    """音擎的基础攻击或基础防御。"""

    kind: Literal["atk", "def"]
    value: float


class WeaponSubstat(PresetModel):
    """音擎自带的固定副词条。"""

    label: str
    value: float
    kind: Literal["pct", "flat"]
    to: str


class WeaponPreset(PresetModel):
    """一件音擎的完整预设。"""

    id: str
    name: str
    grade: str
    role_tag: str
    source: str
    base: WeaponBase
    substat: WeaponSubstat


class AgentPresetList(CamelModel):
    items: List[AgentPreset]


class WeaponPresetList(CamelModel):
    items: List[WeaponPreset]


__all__ = [
    "AgentBaseStats",
    "AgentCoreBonus",
    "AgentPreset",
    "AgentPresetList",
    "UnmodeledBaseStat",
    "WeaponBase",
    "WeaponPreset",
    "WeaponPresetList",
    "WeaponSubstat",
]
