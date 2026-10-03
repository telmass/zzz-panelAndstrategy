# 架构

## 1. 全局视图

```
浏览器
  │
  │  ① 静态产物（任意静态服务器）
  ▼
frontend/dist/index.html
  │
  │  ② SPA history 路由，直连 /calculator 与 /guide
  ▼
frontend/src/views/*.vue                Vue3 SPA，Vite 构建
  │
  │  组件只依赖 src/api/*.ts，不感知 HTTP
  ▼
src/api/panel.ts · src/api/presets.ts
  │
  │  ③ POST /api/panel/calc  GET /api/presets/*
  ▼
backend/src/zzz_panel/api/routes/       FastAPI，只做协议转换
  │
  ▼
backend/src/zzz_panel/services/          用例编排，无公式
  │
  ▼
backend/src/zzz_panel/core/              规则真源：纯函数、零 IO、零框架
  ▲
  │  ④ 同一条链路
  │
backend/src/zzz_panel/cli.py             命令行入口（uv run zzz-panel）
```

三个入口（网页、API、命令行）共用 `core/`，因此不存在「网页算的和命令行算的不一样」。

### 部署形态的补充说明

② 与 ③ 在生产环境通常由**同一个反向代理**接入（同域），这样前端用相对路径
`/api` 即可，开发期与生产期的 URL 策略一致。

**后端不托管前端静态文件**——`api/app.py` 中没有 `StaticFiles`，也没有 `mount()`。
前端由 Vite dev server 或任意静态服务器提供。详见 [deployment.md](deployment.md)。

### 迁移前的原生实现

Vue3 迁移已完成。旧的原生 HTML 实现已删除，其计算部分作为**只读参照基准**
保留在 `frontend/tests/fixtures/legacy-calculator/`，仅供[三方对拍](testing.md)，
不参与运行时与构建。删除记录见
[completeds/legacy-pages.md](completeds/legacy-pages.md)。

## 2. 分层与依赖方向铁律

| # | 铁律 | 理由 |
| --- | --- | --- |
| 1 | `core/` 不得 `import fastapi` / `import pydantic`，不得读文件，不得 `print` | 同一份规则可被 API、CLI、批量计算三方复用，也能脱离 Web 环境单测 |
| 2 | `api/routes/` 只做协议转换：请求 → `schemas` → `services` → 响应，不写业务逻辑 | 业务逻辑散在路由里就没法复用 |
| 3 | `api/` 与 `cli.py` 都不得重复实现公式，必须走 `services/` | 保证「网页算的」与「命令行算的」永远一致 |
| 4 | `schemas/` 与 `core/` 的模型分离 | core 保持框架无关，schemas 承担入参校验与 OpenAPI 文档 |
| 5 | 前端组件内禁止直接 `fetch`，一切网络访问经 `src/api/` | 单一网络出口，错误处理与基址策略只在一处实现 |
| 6 | 前端**不做任何算术**，只传「选了什么」 | 计算下沉后前端就只是渲染层，避免两套实现漂移 |
| 7 | 参照夹具 `tests/fixtures/` 只读 | 它是对拍基准，改了对拍就变成自己跟自己比 |

### 违反铁律的实例（都已修正，留作警示）

|曾经的错误 | 现状 |
| --- | --- |
| 第 2 步前端组件内自行计算面板 | 已下沉到 `core/`；`usePanelCalc.buildRequest` 只组装选择项 |
| 预设数据在前端持有副本 | 已改为 `GET /api/presets/*`；前端不再 import `data/*.json` |
| `SetEffectModule.vue` 直接用原生 `<select>` | 仍存在，但属样式层不一致，不违反第 5 条铁律 |

## 3. 数据流

### 预设数据与规则表：故意不对称

| 数据 | 存放| 消费者 | 理由 |
| --- | --- | --- | --- |
| 代理人预设（60 条）<br>音擎预设（100 条） | `data/*.json` → `GET /api/presets/*` | 后端 `presets/loader.py`、前端经 HTTP | 数据量大、更新频率高（跟随游戏版本），走接口便于统一缓存与失效 |
| 配装规则表（7 张表） | `data/options.json` → `@data` 别名直接 import | 前端 `constants/calculatorOptions.ts` | 下拉框要瞬时可用，不能等一次 HTTP 往返，也不能因接口不可用就瘫掉 |
| 对拍夹具的 JS 包装 | `tests/fixtures/legacy-calculator/data/*.js` | 仅三方对拍 | 参照实现在顶层直接读 `window.AGENT_PRESETS`，删了它对拍就跑不起来 |

`data/` 下三个 JSON **全部是生成物**，改源头必须重新生成，且有测试守卫漂移：

| 生成物 | 源头 | 生成命令 | 漂移守卫 |
| --- | --- | --- | --- |
| `agent-presets.json`<br>`weapon-presets.json` | `.github/skills/*/scripts/refresh_*_presets.py`（联网抓官方 Wiki） | 抓取脚本直接写 | `test_presets.py` 断言数据规范化 |
| 夹具 `data/*.js` | `data/*.json` | `sync_presets.py --to-legacy` | `sync_presets.py --to-legacy --check` |
| `options.json` | `core/options.py` + `core/constants.py` | `sync_presets.py --options` | `backend/tests/test_options_json.py` |

### 面板计算的往返

```
用户在组件里改一个下拉框
  ↓
panelStore（输入唯一真源）状态变更
  ↓
usePanelCalc 的 watch 触发（防抖 200ms）
  ↓  buildRequest()：只组装选择项，不做算术
POST /api/panel/calc
  ↓
schemas/panel.py 校验 → services/panel_service.py 转换命名
  ↓
core/modifiers.py   选择 → 加成累加 + 来源记录
core/panel.py       加成 + 基础值 → 12 行 totals
core/modes.py       模式专属公式 → modeStats
core/breakdown.py   逐行明细（结构化片段）
  ↓
PanelResponse（9 个顶层字段）
  ↓
usePanelCalc.renderBreakdown 把片段渲染成 HTML
  ↓
ResultPanel 展示
```

明细以**结构化数组**而非 HTML 字符串返回，后端因此不必输出中文文案，
换行与格式化规则留在前端 `usePanelCalc.renderBreakdown` 与 `utils/fmt.ts`。
代价是前端要维护渲染逻辑；收益是改文案样式不必同步改后端。

## 4. 关键设计决策

| 决策 | 替代方案 | 选择理由 |
| --- | --- | --- |
| 选项用稳定字符串 id | 数组下标（迁移前的做法） | 预存在后端、选项表在前端，两侧独立演进；下标会因选项增删而错位 |
| 预设走接口、规则表走本地JSON | 全部走接口 / 全部本地打包 | 见第 3 节，取决于「数据大且需刷新」还是「要瞬时可用」 |
| 明细返回结构化片段 | 返回 HTML 字符串 | 后端不掺入展示逻辑 |
| 响应字段 camelCase、`totals` 键用短名、`breakdown` 键用长名 | 全部统一一种风格 | 有意的不统一，且有测试锁住。前端 `types/panel.ts` 与之逐字对齐 |
| 保留旧实现作只读夹具 | 直接删除 | 三方对拍是唯一的端到端正确性保证；删掉后 `test_fmt_parity.py` 还会静默 skip 成假绿灯 |
| 副词条上限 36/54 只在前端钳制 | 后端也限制 | 后端无上限契约，`core` 只做 `max(0, floor(x))`；详见 [requirements.md](requirements.md) 已知限制 |

## 5. 开发命令

```powershell
uv sync                                          # 安装 Python 依赖
uv run uvicorn zzz_panel.api.app:app --port 8000  # 后端 :8000
uv run pytest                                    # 后端测试
uv run zzz-panel                                 # CLI 计算示例

pwsh tools/dev.ps1                # 一条命令拉起前后端（推荐）

cd frontend
npm install
npm run dev                       # 前端 :5173，/api 代理到 8000
npm run typecheck                 # vue-tsc --noEmit
npm run test                      # Vitest，含三方对拍
npm run build                     # 产物到 frontend/dist/
```

开发期 Vite 代理 `/api`，因此**不涉及 CORS**；CORS 白名单只是跨域部署时的兜底。
详见 [deployment.md](deployment.md)。

## 6. 相关文档

- [requirements.md](requirements.md) —— 项目定位、功能范围、约束与已知限制
- [api-reference.md](api-reference.md) —— HTTP 接口与数据结构
- [data-schema.md](data-schema.md) —— 预设与选项表字段定义
- [calculation-rules.md](calculation-rules.md) —— 计算公式
- [directory-layout.md](directory-layout.md) —— 目录职责详解
- [development.md](development.md) —— 开发流程、数据管线、常见坑
- [testing.md](testing.md) —— 测试策略与三方对拍
- [deployment.md](deployment.md) —— 构建与部署形态
- [changelog.md](changelog.md) —— 变更记录