"""FastAPI 传输层。

只做 HTTP 协议转换（请求 → schemas → services → 响应），不写业务逻辑。
四个端点挂在 ``app.py`` 的 ``app`` 上：``/api/health``、``/api/panel/calc``、
``/api/presets/agents``、``/api/presets/weapons``。

同一份 ``app`` 既由 ``uvicorn`` 本地起服务，也由 ``backend/src/worker.py``
（``Default = asgi.entrypoint(app)``）交给 Cloudflare Workers 承载。
"""
