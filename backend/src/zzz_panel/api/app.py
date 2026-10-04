"""FastAPI 应用入口。

CORS 只放开本地前端 Vite dev server 的 5173（``http://localhost:5173`` 与
``http://127.0.0.1:5173``）。生产环境由 Cloudflare Worker 同源提供前端与
``/api/*``，浏览器不会跨源，因此无需放开任何公网来源。

同一个 ``app`` 有两个宿主：本地 ``uvicorn``，以及 Cloudflare Workers 上的
``backend/src/worker.py``（``Default = asgi.entrypoint(app)``）。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..schemas.panel import HealthResponse
from .routes.panel import router as panel_router
from .routes.presets import router as presets_router

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
app.include_router(presets_router)


@app.get("/api/health", response_model=HealthResponse, tags=["panel"], summary="健康检查")
def health() -> HealthResponse:
    return HealthResponse()


__all__ = ["app"]
