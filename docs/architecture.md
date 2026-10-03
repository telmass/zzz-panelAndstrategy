# 架构

## 当前状态

Vue3 迁移已完成，下面这张图即当前形态：

```
浏览器
  └── frontend/src/views/*.vue（Vite dev server :5173 / 静态产物 dist/）
        │  只依赖 src/api/*.ts，不感知 HTTP 细节
        ▼
    src/api/panel.ts  ──HTTP/JSON──►  backend/src/zzz_panel/api/routes
                                          │  仅协议转换
                                          ▼
                                   services/panel_service
                                          │  编排
                                          ▼
                              core/  ◄──── cli.py 也调用这一层
                        （纯函数、零 IO、零框架依赖）

命令行
  └── backend/src/zzz_panel/cli.py → core/panel.py
```

网页与命令行走的是同一份 `core/`，因此「网页算的」与「命令行算的」永远一致。

迁移前的原生实现已删除；其计算部分作为**只读参照基准**留在
`frontend/tests/fixtures/legacy-calculator/`，仅供三方对拍，不参与运行时与构建。
见 [legacy-pages.md](legacy-pages.md)。

### 依赖方向铁律

1. `core/` 不得 `import fastapi` / `import pydantic`，不得读文件，不得 `print`。
   这样同一份规则可被 API、CLI、未来的批量计算三方复用，也能脱离 Web 环境单测。
2. `api/routes/` 只做 HTTP 协议转换：请求 → `schemas` → `services` → 响应，不写业务逻辑。
3. `api/` 与 `cli.py` 都不得重复实现公式，必须走 `services/`，保证「网页算的」与
   「命令行算的」永远一致。
4. `schemas/` 与 `core/` 的模型分离：core 保持框架无关，schemas 承担入参校验与
   OpenAPI 文档。
5. 前端组件内禁止直接 `fetch`，一切网络访问经 `src/api/`。

## 数据流

| 阶段 | 预设数据来源 | 计算执行位置 |
| --- | --- | --- |
| 迁移前（legacy） | `frontend/legacy/data/*.js`（Skill 抓取生成） | 浏览器（`calculator.js`） |
| 迁移第 0–2 步 | 同上 | 浏览器（Vue 组件内，先不调后端） |
| 迁移第 3 步起（**现在**） | `data/*.json`（`GET /api/presets/*`） | FastAPI（`core/`） |

`data/*.json` 是唯一真实源。
`frontend/tests/fixtures/legacy-calculator/data/*.js` 是它的派生产物，
由 `tools/sync_presets.py --to-legacy` 生成，仅供对拍夹具读取。

## 开发命令

```powershell
uv sync                                   # 安装 Python 依赖
uv run zzz-panel                          # CLI 计算示例
uv run pytest                             # Python 测试
uv run uvicorn zzz_panel.api.app:app --reload --port 8000   # 后端（待实现）

cd frontend
npm install
npm run dev                               # /api 代理到 8000
npm run test                              # Vitest
```

生产部署时由 FastAPI 挂载 `frontend/dist` 静态文件，单进程同时提供 API 与页面，无需 CORS。
