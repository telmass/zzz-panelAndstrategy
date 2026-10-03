"""FastAPI 应用入口。

CORS 默认放开本地开发端口：前端 Vite dev server 在 5173，
生产环境由同源部署收敛，因此这里只做开发期放行。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..schemas.panel import HealthResponse
from .routes.panel import router as panel_router

app = FastAPI(
    title="ZZZ Panel API",
    version="0.1.0",
    description="绝区零代理人面板计算服务",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(panel_router)


@app.get("/api/health", response_model=HealthResponse, tags=["panel"], summary="健康检查")
def health() -> HealthResponse:
    return HealthResponse()


__all__ = ["app"]
