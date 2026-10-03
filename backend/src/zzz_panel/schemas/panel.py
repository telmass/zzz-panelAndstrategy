"""面板计算的 HTTP 契约。

线格式统一为 **camelCase**（Pydantic 的 ``alias_generator=to_camel``），
与前端 TypeScript 类型直接对应，避免在客户端再写一层 snake→camel 映射。

请求只带**选择**（下拉项 id、副词条条数）与角色基础面板，数值一律由后端查表
解析——这是第 3 步「计算下沉」的关键：前端不再持有任何计算口径。

响应分两部分：

- ``totals`` / ``modeStats`` / ``blastDmg`` —— 纯数值，前端直接展示
- ``sums`` / ``sources`` / ``subFixed`` / ``weaponBase`` —— 中间量
- ``breakdown`` —— 结构化明细片段，HTML 拼接留给前端

明细只给结构化片段（``text`` / ``kw`` / ``num`` / ``sources``），
后端因此不掺入展示层。
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

PanelMode = Literal["standard", "rupture", "fengyu"]


class _CamelModel(BaseModel):
    """按 camelCase 收发；仍允许用字段名传入，便于测试与 Python 侧调用。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BaseStatsIn(_CamelModel):
    """角色基础面板。对应前端 ``BaseStats``。

    默认值取自 legacy ``calculator.html`` 上各 input 的默认值，与前端
    ``stores/panelStore.ts`` 的 ``defaultBase()`` 一致。任何字段漏传都必须
    得到与旧页面相同的面板，否则「字段缺失」会静默变成「算错」。
    """

    hp: float = 8000.0
    atk: float = 1000.0
    # `def` 是 Python 关键字，用 def_ 承载；alias_generator 会把 def_ 转成 def。
    def_: float = Field(default=600.0, alias="def")
    impact: float = 90.0
    cr: float = 5.0
    cd: float = 50.0
    ac: float = 100.0
    am: float = 100.0
    pr: float = 0.0
    er: float = 1.2
    penforce: float = 0.0
    energy_accumulation: float = 0.0


class WeaponSubIn(_CamelModel):
    """音擎固定副词条。已从音擎预设解析出目标修正量与数值。"""

    target: str
    value: float
    kind: Literal["pct", "flat"] = "pct"
    label: str = ""


class WeaponIn(_CamelModel):
    base_kind: Literal["atk", "def"] = "atk"
    base_value: float = 0.0
    substat: Optional[WeaponSubIn] = None


class CoreIn(_CamelModel):
    core1: str = ""
    core2: str = ""


class DiscMainIn(_CamelModel):
    disc4: str = ""
    disc5: str = ""
    disc6: str = ""


class SetsIn(_CamelModel):
    set0: str = ""
    set1: str = ""
    set2: str = ""


class PanelRequest(_CamelModel):
    mode: PanelMode = "standard"
    base: BaseStatsIn = Field(default_factory=BaseStatsIn)
    weapon: WeaponIn = Field(default_factory=WeaponIn)
    core: CoreIn = Field(default_factory=CoreIn)
    disc_main: DiscMainIn = Field(default_factory=DiscMainIn)
    sub_stats: Dict[str, int] = Field(default_factory=dict)
    sets: SetsIn = Field(default_factory=SetsIn)


# ---------------------------------------------------------------- 响应


class TextSegment(BaseModel):
    type: Literal["text"] = "text"
    text: str


class KwSegment(BaseModel):
    type: Literal["kw"] = "kw"
    text: str


class NumSegment(BaseModel):
    type: Literal["num"] = "num"
    value: float
    bold: bool = False
    unit: str = ""


class SourcesSegment(BaseModel):
    type: Literal["sources"] = "sources"
    items: List[str]


class LineSegment(BaseModel):
    type: Literal["line"] = "line"
    parts: List[Union[TextSegment, KwSegment, NumSegment, SourcesSegment]]
    wrapped: bool = True


class PanelResponse(_CamelModel):
    mode: PanelMode
    totals: Dict[str, float]
    mode_stats: Dict[str, float] = Field(default_factory=dict)
    blast_dmg: Optional[float] = None
    sums: Dict[str, float] = Field(default_factory=dict)
    sources: Dict[str, List[str]] = Field(default_factory=dict)
    sub_fixed: Dict[str, float] = Field(default_factory=dict)
    weapon_base: Dict[str, float] = Field(default_factory=dict)
    breakdown: Dict[str, List[LineSegment]] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


__all__ = [
    "BaseStatsIn",
    "CoreIn",
    "DiscMainIn",
    "HealthResponse",
    "KwSegment",
    "LineSegment",
    "NumSegment",
    "PanelRequest",
    "PanelResponse",
    "SetsIn",
    "SourcesSegment",
    "TextSegment",
    "WeaponIn",
    "WeaponSubIn",
]
