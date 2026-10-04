"""Cloudflare Python Worker 入口。

部署形态：**一个 Worker 同时提供 API 与前端静态产物**，对应
``docs/deployment.md`` 里 Nginx 那套「同域反代 + SPA history 回落」，
只是把反代换成了 Wrangler 的 assets 路由。

为什么入口放在 ``backend/src/`` 而不是包内
------------------------------------------
``pywrangler`` 会把**入口文件所在目录的整棵树**附加到 Worker 的虚拟文件系统，
且不做任何排除。这里选 ``backend/src/``，于是 ``zzz_panel`` 作为一个完整包被附加，
``presets/loader.py`` 里的相对导入照常工作——若把入口放进
``backend/src/zzz_panel/``，包会被摊平，``from ..schemas.panel import ...``
这类相对导入会直接失败。

仓库根的 ``data/`` 不在这棵树里，因此部署前要先生成包内镜像：

    python tools/bundle_worker_data.py

路由分工（见 ``wrangler.jsonc``）：

===============================  ==================================
路径                             由谁处理
===============================  ==================================
``/api/*``                       本 Worker（FastAPI）
``/docs`` / ``/openapi.json``    本 Worker（FastAPI 自带接口文档）
``/``、``/assets/*``             Workers 静态资源层，不进本 Worker
``/calculator``、``/guide``      静态资源层未命中 → 回落 ``index.html``
===============================  ==================================

最后一行等价于 Nginx 的 ``try_files $uri $uri/ /index.html``；前端用 history
模式路由，少了这个回落，直连子页会 404。

因为页面与 API 同域，前端的相对路径 ``/api`` 继续有效，**无需设置
``VITE_API_BASE_URL``，也无需放开后端 CORS**。

本地预览：``uv run --group worker pywrangler dev``
"""

from workers import asgi

from zzz_panel.api.app import app

#: Cloudflare 以这个名字查找 Worker 的 fetch 入口。
Default = asgi.entrypoint(app)
