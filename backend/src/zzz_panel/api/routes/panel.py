"""面板计算路由。"""

from __future__ import annotations

from fastapi import APIRouter

from ...schemas.panel import PanelRequest, PanelResponse
from ...services import panel_service

router = APIRouter(prefix="/api", tags=["panel"])


@router.post("/panel/calc", response_model=PanelResponse, summary="计算最终面板")
def calc_panel(request: PanelRequest) -> PanelResponse:
    """由配装选择与基础面板算出最终面板与结构化明细。"""
    return panel_service.calculate(request)


__all__ = ["router"]
