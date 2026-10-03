"""预设数据路由。

``GET /api/presets/agents`` 与 ``GET /api/presets/weapons`` 直接下发
``data/*.json`` 的内容。响应体是 ``{"items": [...] }`` 而不是裸数组，
留出后续加分页/版本号的余地而不破坏前端解析。

预设数据非法时返回 **503** 而不是 500：这不是「代码坏了」，而是数据源坏了，
调用方（前端 presetStore）据此展示「预设数据不可用」而不是「服务器错误」。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...presets import loader
from ...schemas.presets import AgentPresetList, WeaponPresetList

router = APIRouter(prefix="/api/presets", tags=["presets"])


@router.get(
    "/agents",
    response_model=AgentPresetList,
    response_model_exclude_none=True,
    summary="代理人预设列表",
)
def list_agents() -> AgentPresetList:
    try:
        return AgentPresetList(items=loader.load_agents())
    except loader.PresetLoadError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get(
    "/weapons",
    response_model=WeaponPresetList,
    response_model_exclude_none=True,
    summary="音擎预设列表",
)
def list_weapons() -> WeaponPresetList:
    try:
        return WeaponPresetList(items=loader.load_weapons())
    except loader.PresetLoadError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


__all__ = ["router"]