"""预设数据的 HTTP 契约。

字段与仓库根 ``data/*.json`` 一一对应（该目录是唯一真实源），
因此这里的模型同时承担两个职责：

1. **结构校验**：类型、必填项、枚举在 Pydantic 层拦下，报错带字段路径；
2. **线格式**：响应按 camelCase 序列化，前端直接复用同一套类型定义。

跨字段的语义校验（id 唯一、核心加成能否由选项表示、能否填满两个核心槽位）
不在本层，由 ``zzz_panel.presets.validate`` 负责——那些规则需要查
``core.options``，与传输层无关。
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base import CamelModel
from .panel import PanelMode


class AgentBaseStats(CamelModel):
    """60 级基础面板（不含核心）。

    全部键可选：``unavailableBaseStats`` 列出的项在官方面板中本就缺失，
    例如部分命破代理人不提供穿透率与能量自动回复。
    """

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


class AgentAdditionalBaseStats(CamelModel):
    """命破模式专属的基础面板字段。"""

    penforce: Optional[float] = None
    energy_accumulation: Optional[float] = None


class UnmodeledBaseStat(CamelModel):
    """官方 WIKI 列出、但当前计算器尚未建模的基础属性。"""

    label: str
    value: float
    unit: str


class AgentCoreBonus(CamelModel):
    """单条核心加成。

    ``ranks`` 为核心技位次；``option_count`` 表示该条被计入几个核心选项，
    等于 1 时在 JSON 里省略。
    """

    option_id: str
    ranks: List[str]
    label: str
    per_rank_value: float
    total_value: float
    unit: str = ""
    option_count: Optional[int] = None

    @property
    def count(self) -> int:
        return self.option_count or 1


class AgentPreset(CamelModel):
    id: str
    name: str
    role_tag: str
    panel_mode: PanelMode
    source: str
    base: AgentBaseStats
    core_bonuses: List[AgentCoreBonus]
    additional_base_stats: Optional[AgentAdditionalBaseStats] = None
    unavailable_base_stats: Optional[List[str]] = None
    unmodeled_base_stats: Optional[List[UnmodeledBaseStat]] = None
    grade: Optional[str] = None


class WeaponSubstat(CamelModel):
    """音擎固定副词条。``to`` 对应累加器键名。"""

    label: str
    value: float
    kind: Literal["pct", "flat"]
    to: str


class WeaponPreset(CamelModel):
    id: str
    name: str
    grade: str
    role_tag: str
    source: str
    base_kind: Literal["atk", "def"]
    base_attack: float = 0.0
    base_defense: float = 0.0
    substat: WeaponSubstat


class AgentPresetList(BaseModel):
    items: List[AgentPreset]


class WeaponPresetList(BaseModel):
    items: List[WeaponPreset]


__all__ = [
    "AgentAdditionalBaseStats",
    "AgentBaseStats",
    "AgentCoreBonus",
    "AgentPreset",
    "AgentPresetList",
    "UnmodeledBaseStat",
    "WeaponPreset",
    "WeaponPresetList",
    "WeaponSubstat",
]