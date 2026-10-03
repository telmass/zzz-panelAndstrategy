"""面板计算编排层。

职责是**转换**，不含公式：把 HTTP 请求的 camelCase 字段转成 core 层的
Python 命名，把 core 的 dataclass 结果转成可 JSON 序列化的响应。
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..core import breakdown as bd
from ..core.modifiers import PanelSelection
from ..core.panel import calculate_selection
from ..schemas.panel import PanelRequest, PanelResponse

# core 的基础面板键名 ← 请求里的键名
_BASE_KEY_MAP = {
    "hp": "hp",
    "atk": "atk",
    "def": "def",
    "cr": "cr",
    "cd": "cd",
    "pr": "pr",
    "am": "am",
    "ac": "ac",
    "impact": "impact",
    "er": "er",
}


def _to_selection(request: PanelRequest) -> PanelSelection:
    weapon = request.weapon
    substat = weapon.substat
    return PanelSelection(
        mode=request.mode,
        core=(request.core.core1, request.core.core2),
        disc_main={
            "disc4": request.disc_main.disc4,
            "disc5": request.disc_main.disc5,
            "disc6": request.disc_main.disc6,
        },
        sub_stats=dict(request.sub_stats),
        sets=(request.sets.set0, request.sets.set1, request.sets.set2),
        weapon_sub_target=substat.target if substat else "",
        weapon_sub_value=substat.value if substat else 0.0,
        weapon_sub_kind=substat.kind if substat else "pct",
        weapon_sub_label=substat.label if substat else "",
        weapon_base_atk=weapon.base_value if weapon.base_kind == "atk" else 0.0,
        weapon_base_def=weapon.base_value if weapon.base_kind == "def" else 0.0,
    )


def _to_base(request: PanelRequest) -> Dict[str, float]:
    base = request.base
    values = base.model_dump(by_alias=True)
    return {key: float(values.get(source, 0.0)) for key, source in _BASE_KEY_MAP.items()}


def _segment_to_dict(segment: object) -> Dict[str, Any]:
    if isinstance(segment, bd.Text):
        return {"type": "text", "text": segment.text}
    if isinstance(segment, bd.Kw):
        return {"type": "kw", "text": segment.text}
    if isinstance(segment, bd.Num):
        return {"type": "num", "value": segment.value, "bold": segment.bold, "unit": segment.unit}
    if isinstance(segment, bd.Sources):
        return {"type": "sources", "items": list(segment.items)}
    raise TypeError(f"Unsupported segment: {segment!r}")


def _breakdown_to_dict(breakdown: Dict[str, List[bd.Line]]) -> Dict[str, List[Dict[str, Any]]]:
    return {
        row: [
            {
                "type": "line",
                "parts": [_segment_to_dict(part) for part in line.parts],
                "wrapped": line.wrapped,
            }
            for line in lines
        ]
        for row, lines in breakdown.items()
    }


def calculate(request: PanelRequest) -> PanelResponse:
    """执行一次面板计算并返回响应。"""
    result = calculate_selection(_to_selection(request), _to_base(request))

    return PanelResponse(
        mode=result["mode"],
        totals=result["totals"],
        mode_stats=result["mode_stats"],
        blast_dmg=result["blast_dmg"],
        sums=result["sums"],
        sources=result["sources"],
        sub_fixed=result["sub_fixed"],
        weapon_base=result["weapon_base"],
        breakdown=_breakdown_to_dict(result["breakdown"]),
    )


__all__ = ["calculate"]
