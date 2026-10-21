# 架构

## 1. 全局视图

```
浏览器
  │
  │  ① 静态产物。线上由 Cloudflare Workers 的 Assets 层直接返回
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
backend/src/zzz_panel/cli.py             命令行入口（uv run zzz-panel-and-strategy）
```

三个入口（网页、API、命令行）共用 `core/`，因此不存在「网页算的和命令行算的不一样」。

### 两个宿主，一个 app

`backend/src/zzz_panel/api/app.py` 的 `app` 有两个宿主，**代码完全相同**：

|宿主 | 入口 | 用于 |
| --- | --- | --- |
| 本地 / 自建服务器 | `uvicorn zzz_panel.api.app:app` | 开发、形态 A/B/C |
| Cloudflare Workers | `backend/src/worker.py` 的 `Default = asgi.entrypoint(app)` | **线上生产** |

`wrangler.jsonc` 的 `run_worker_first: ["/api/*", "/docs", "/openapi.json"]`
决定哪些路径进 Worker，其余由 Assets 层直接返回（不进脚本、不计 CPU）。

**后端不托管前端静态文件**——`api/app.py` 中没有 `StaticFiles`，也没有 `mount()`。
详见 [deployment.md](../guides/deployment.md)。

### 迁移前的原生实现

Vue3 迁移已完成。旧的原生 HTML 实现已删除，其计算部分作为**只读参照基准**
保留在 `frontend/tests/fixtures/legacy-calculator/`，仅供[三方对拍](../guides/testing.md)，
不参与运行时与构建。删除记录见
[completeds/legacy-pages.md](../completeds/legacy-pages.md)。

### 攻略页：Vue 路由 + 共享渲染器

`strategy/<slug>/` 只保存该代理人的两份 JSON 数据；页面由主应用统一渲染：

- `views/StrategyView.vue`：按 slug 拉取 `/strategy/<slug>/data/*.json`，管理加载/错误态与卸载；
- `frontend/src/strategy/renderStrategy.ts`：从 legacy 静态模板迁移的唯一渲染器，负责生成 DOM 与交互；
- `frontend/src/strategy/strategyCard.ts`：`保存攻略` 的导出卡片构建器。完全由攻略 JSON 生成 1360px 白底 PNG（左侧 `background` 立绘 + 技能/命座/武器/驱动盘/队伍/毕业面板），不再截取页面；根类为 `strategy-card strategy-card--export`，用于覆盖启动页同名 `.strategy-card` / `.strategy-card__tachie` 规则。**导出卡片内部一律用 flex 布局**（html2canvas 不支持 grid，会被拍平成竖排），并显式重置启动页卡片继承来的 `flex-direction` / `align-items` / `justify-content`；立绘用 `max-width/max-height` 约束而非 `object-fit`。驱动盘主词条按 4/5/6 号位给三个小框，首选与备选同框且左对齐，只显示词条名，数值后缀（如 `+92` / `+30%`）仅详情页保留；主词条按方案分组（共用则一行、不同则各自成组）；驱动盘套装按**装备组**渲染——`set2` / `set2b` / `set2c` 三组 2 件套（并列，都要装）各出一栏，编号 ①②③；**没有 4 件套组时（2+2+2）整个「4 件套」栏不渲染**，留个空栏会让人以为漏了内容。单组时沿用旧口径（写效果名，一组候选常常同效果）；多组时组内效果可能相同，靠**套装名**才分得清；
- `frontend/src/strategy/substats.ts`：毕业面板词条展示口径。计算仍用完整 54 条，展示拆成「大词条 + 小词条」（如洛茜 54 → `47+7`），详情页与导出卡片共用；
- `frontend/src/strategy/strategy.css`：唯一一份攻略样式，页面样式收窄在 `.strategy-detail` 下；导出卡片样式使用 `.strategy-card--export` 作用域，避免与主应用冲突。左侧导航栏为紧凑版（主链接 32px / 子链接 26px / 操作按钮并排），设计目标是在 768px 视口高度内完整展示、不产生内部滚动。

`vite.config.ts` 的 `strategyDataPlugin` 只做两件事：开发期把 `/strategy/<slug>/data/*.json`
映射到仓库 `strategy/`，构建期只把两份 JSON 拷进 `dist/strategy/<slug>/data/`。
不再有 iframe、`index.html`、`app.js`、`styles.css` 的每页副本。

两个保存按钮的边界：**同一张图，两种交付方式**——`保存攻略` 走 `strategyCard.ts` 生成数据驱动卡片后**下载**；`复制攻略` 生成同一张卡片后**写进系统剪贴板**，可直接粘贴（剪贴板不可用时退回下载）。
卡片横向 1600px，驱动盘主词条单元按内容分配宽度（`flex: 1 1 auto`）——文案长的那个盒子更宽，不再三个等分硬挤。

新增代理人 = 补 `strategy/<slug>/data/` + 运行 `tools/gen_strategy_guides.py`；
渲染器、导出卡片与样式自动复用。`/strategy` 是选择页，`/strategy/:slug` 是同一个 `StrategyView`。

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

### 曾经的违反实例（留作警示）

| 曾经的错误 | 现状 |
| --- | --- |
| 第 2 步前端组件内自行计算面板 | 已下沉到 `core/`；`usePanelCalc.buildRequest` 只组装选择项 |
| 预设数据在前端持有副本 | 已改为 `GET /api/presets/*`；前端不再 import `data/catalog/*.json` |
| `SetEffectModule.vue` 直接用原生 `<select>`，未走 `SelectField` | **仍存在**。属样式层不一致，不违反上表任何一条铁律，故未修 |

## 3. 数据流

### 预设数据与规则表：故意不对称

| 数据 | 存放| 消费者 | 理由 |
| --- | --- | --- | --- |
| 代理人预设（61 条）<br>音擎预设（101 条） | `data/catalog/*.json` → `GET /api/presets/*` | 后端 `presets/loader.py`、前端经 HTTP | 数据量大、更新频率高（跟随游戏版本），走接口便于统一缓存与失效 |
| 同上，**Worker 上的形态** | `data/*.json` → 编译进 `zzz_panel/_bundled_data.py` | Worker 里的 `presets/loader.py` | Worker 没有仓库目录，`data/` 上不去（pywrangler 只传 `.py`）。磁盘上有 `data/` 时优先读磁盘，编译产物只作兜底 |
| 配装规则表（7 张表） | `data/rules/calculator-rules.json` → `@data` 别名直接 import | 前端 `constants/calculatorOptions.ts` | 下拉框要瞬时可用，不能等一次 HTTP 往返，也不能因接口不可用就瘫掉。**不编译进后端包** |
| 驱动盘套装效果（30 套） | `data/catalog/drive-discs.json` + `frontend/public/images/discs/` | Vue 路由攻略页（`StrategyView` + `renderStrategy.ts`）；计算器 UI 仍未接入（待做，见 [requirements.md](../overview/requirements.md) 第 7 节） | 与预设同为 Wiki 抓取物，但当前不进计算器：没有规则表条目、没有接口、不编译进 Worker。`image` 字段是 `/images/…` URL（唯一图片根约定，见 [directory-layout.md](../overview/directory-layout.md) 第 2.2 节），不是仓库相对路径 |
| 对拍夹具的 JS 包装 | `tests/fixtures/legacy-calculator/data/*.js` | 仅三方对拍 | 参照实现在顶层直接读 `window.AGENT_PRESETS`，删了它对拍就跑不起来 |

`data/` 下五个 JSON 中，四个是生成物，`catalog/agent-index.json` 是手工维护的规范 slug 表；
路径由 `data/manifest.json` 统一登记。改生成物必须重新生成，且有闸门守卫漂移：

| 生成物 | 源头 | 生成命令 | 漂移守卫 |
| --- | --- | --- | --- |
| `catalog/agents.json`<br>`catalog/weapons.json` | `.github/skills/*/scripts/refresh_*_presets.py`（联网抓官方 Wiki） | 抓取脚本直接写 | `test_presets.py` 断言数据规范化 |
| 夹具 `data/*.js` | **冻结的快照**（不再生成） | 无 | `backend/tests/test_legacy_fixture_snapshot.py`（语义等值） |
| `rules/calculator-rules.json` | `core/options.py` + `core/constants.py` | `sync_presets.py --options` | `backend/tests/test_options_json.py` |
| `catalog/drive-discs.json` | `.github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py`（联网抓官方 Wiki） | 抓取脚本直接写 | `sync_manifest.py --check`（**要**跑，它登记在册）；不进 Worker 产物，靠重跑幂等（JSON 字节不变）与人工核对 |
| `_bundled_data.py`（gitignored） | `data/catalog/agents.json`<br>`data/catalog/weapons.json` | `tools/bundle_worker_data.py` | `bundle_worker_data.py --check`<br>`backend/tests/test_worker_bundle.py` |
| `catalog/agent-index.json`（手写） | 维护者 / `fix-agent` Skill | 不经生成器；作为 slug 唯一来源 | 由 gen_strategy_guides.py --check 与 test_strategy_data.py 守卫（目录 ↔ 登记表 ↔ mapping 一致性） |

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
| 副词条上限 36/54 只在前端钳制 | 后端也限制 | 后端无上限契约，`core` 只做 `max(0, floor(x))`；详见 [requirements.md](../overview/requirements.md) 已知限制 |
| 生产部署用 Cloudflare Worker | 自建服务器 + Nginx 反代 | 一个 URL 同时提供页面与 API，不维护服务器、不做端口映射。代价是只能装纯 Python 包、只能上传 `.py`（预设因此要编译进包），见 [deployment.md](../guides/deployment.md) |
| 站点公开、无鉴权 | Cloudflare Access / Worker 内 Basic Auth | 全站无账号、无个人信息、无可写数据面。**这是刻意决定**，依据与残留风险见 [deployment.md](../guides/deployment.md) 5.9 |

## 5. 开发命令

```powershell
uv sync                                          # 安装 Python 依赖
uv run uvicorn zzz_panel.api.app:app --port 8000  # 后端 :8000
uv run pytest                                    # 后端测试
uv run zzz-panel-and-strategy                 # CLI 计算示例

pwsh tools/dev.ps1                # 一条命令拉起前后端（推荐）

cd frontend
npm install
npm run dev                       # 前端 :5173，/api 代理到 8000
npm run typecheck                 # vue-tsc --noEmit
npm run test                      # Vitest，含三方对拍
npm run build                     # 产物到 frontend/dist/
```

开发期 Vite 代理 `/api`，因此**不涉及 CORS**；CORS 白名单只是跨域部署时的兜底。
详见 [deployment.md](../guides/deployment.md)。

## 6. 相关文档

- [requirements.md](../overview/requirements.md) —— 项目定位、功能范围、约束与已知限制
- [api-reference.md](../reference/api-reference.md) —— HTTP 接口与数据结构
- [data-schema.md](data-schema.md) —— 预设与选项表字段定义
- [calculation-rules.md](calculation-rules.md) —— 计算公式
- [directory-layout.md](../overview/directory-layout.md) —— 目录职责详解
- [development.md](../guides/development.md) —— 开发流程、数据管线、常见坑
- [testing.md](../guides/testing.md) —— 测试策略与三方对拍
- [deployment.md](../guides/deployment.md) —— 构建与部署形态
- [changelog.md](../changelog.md) —— 变更记录