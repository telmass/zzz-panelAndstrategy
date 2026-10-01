# 架构

## 当前状态（迁移中）

```
浏览器（file:// 直接打开）
  └── frontend/legacy/pages/*.html
        ├── ../styles/calculator.css
        ├── ../scripts/calculator-config.js   选项常量
        ├── ../data/*.js                      window.AGENT_PRESETS / WEAPON_PRESETS
        └── ../scripts/calculator.js          交互 + 全部计算逻辑（纯前端）

命令行
  └── backend/src/zzz_panel/cli.py → core/panel.py
```

前端与后端目前**各自独立、互不调用**。legacy 页面的计算完全在浏览器内完成；
Python 侧只是一个可复用的计算库与 CLI。

## 目标状态

```
Vue 组件 (frontend/src/components/**)
   │  只依赖 src/api/*.ts 暴露的类型，不感知 HTTP 细节
   ▼
src/api/client.ts  ──HTTP/JSON──►  backend/src/zzz_panel/api/routes
                                          │  仅协议转换
                                          ▼
                                   services/panel_service
                                          │  编排
                                          ▼
                              core/  ◄──── cli.py 也调用这一层
                        （纯函数、零 IO、零框架依赖）
```

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
| 现在 | `frontend/legacy/data/*.js`（Skill 抓取生成） | 浏览器（`calculator.js`） |
| 迁移第 0–2 步 | 同上 | 浏览器（Vue 组件内，先不调后端） |
| 迁移第 3 步起 | `data/*.json`（`GET /api/presets/*`） | FastAPI（`core/`） |

`data/*.json` 将成为唯一真实源。`frontend/legacy/data/*.js` 是它的过渡期产物，
由 `tools/sync_presets.py` 生成，仅供 legacy 页面使用。

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
