# 项目目录结构重构方案（前端 Vue3 预留 + Python 计算服务化）

## 0. 现状盘点（已核实）

| 现状 | 事实 |
| --- | --- |
| 页面 | 6 个 HTML 在仓库根目录，全部为原生单文件（内联 `<style>`） |
| 唯一外部依赖页 | `代理人面板计算器.html`：1 个 CSS + 4 个 JS（`data/agent-presets.js`、`data/weapon-presets.js`、`js/calculator-config.js`、`js/calculator.js`） |
| 页面间链接 | 仅 3 处：`启动界面.html:180` 锚点；`命破…html:7`、`锋御…html:7` 的 `meta refresh`（带 `?mode=`） |
| 样式 | `css/calculator.css`，无 `url()` / `@import`，不引用字体或图片 |
| 静态资源 | `images/agents` 60 张 + `images/weapons` 100 张 PNG，**当前无任何代码引用**（文件名 `ep-{id}.png` 与预设 `id` 一一对应，属预留素材） |
| Python | 根 `main.py` 独立计算原型（含示例数据与打印入口）；根 `pyproject.toml`（name=`test`）+ `uv.lock` + `.python-version` + `.venv` |
| 数据生成脚本 | `.github/skills/*/scripts/refresh_*.py`，**硬编码默认路径** `js/calculator-config.js`、`data/agent-presets.js`、`data/weapon-presets.js` |
| 文档 | `README.md` 为空文件 |
| 卫生问题 | `__pycache__/main.cpython-313.pyc` 被 Git 跟踪；无 `.gitignore` |

**已确认的四项决策**：① Python 走 FastAPI + 纯函数计算库；② 前端走 Vite + Vue3 + TS；③ legacy 目录拆分 + 中文文件名改英文；④ 旧路径保留重定向页；⑤ Python 依赖用单一根 `pyproject.toml` + src 布局。

---

## 一、重构后的完整目录树

```
test/
├── README.md                       # 项目总览 / 快速开始 / 目录导航（重写，当前为空）
├── .gitignore                      # 新增
├── .python-version                 # 保留
├── pyproject.toml                  # 唯一 Python 依赖源（uv），声明 backend 包
├── uv.lock                         # 随 pyproject 重新生成
│
├── frontend/                       # = 前端工程根（Vite root）
│   ├── index.html                  # Vue3 应用入口（Vite 要求位于 root 根）
│   ├── package.json                # 预留（本次不落地，见风险说明）
│   ├── tsconfig.json               # 预留
│   ├── vite.config.ts              # 预留：dev 代理 /api → http://127.0.0.1:8000
│   ├── .env.example                # 预留：VITE_API_BASE_URL
│   │
│   ├── public/                     # Vite 原样拷贝到 dist 根，不参与指纹化
│   │   └── images/
│   │       ├── agents/              # 60 张 ep-*.png（原 images/agents）
│   │       └── weapons/             # 100 张 ep-*.png（原 images/weapons）
│   │
│   ├── src/                        # Vue3 源码（本次仅建目录 + 占位说明）
│   │   ├── main.ts                 # 应用入口：createApp + router + pinia
│   │   ├── App.vue                 # 根组件，router-view + 全局布局
│   │   │
│   │   ├── assets/                 # 经 Vite 处理（可被 import、生成 hash）
│   │   │   ├── images/             # 页面内联引用的插图、图标
│   │   │   ├── fonts/              # 自定义字体（当前项目无字体文件）
│   │   │   └── styles/             # 全局样式
│   │   │       ├── tokens.css      # 设计变量（颜色/间距/圆角），替代散落的硬编码
│   │   │       ├── base.css        # reset + 元素级基础样式
│   │   │       └── components.css  # 复用组件类（field / module / breakdown 等）
│   │   │
│   │   ├── views/                  # 路由级页面（对应现在的 6 个 HTML）
│   │   │   ├── LauncherView.vue    # 启动界面（现 启动界面.html）
│   │   │   ├── CalculatorView.vue  # 统一计算器（现 代理人面板计算器.html）
│   │   │   ├── GuideView.vue       # 学习指南（现 面板计算方式学习指南.html）
│   │   │   └── ExampleView.vue     # 测试范例模板（现 测试范例计算器模板.html）
│   │   │
│   │   ├── components/             # 可复用 UI 组件
│   │   │   ├── layout/             # 页面骨架：AppHeader / AppShell / AppFooter
│   │   │   ├── common/             # 通用件：BaseSelect / NumberField / StatRow
│   │   │   └── calculator/         # 业务件，逐块对应 legacy 的 .module
│   │   │       ├── BasePanel.vue           # 一、基础面板 + 代理人预设选择
│   │   │       ├── WeaponPanel.vue          # 二、音擎（等级/标签/预设/副词条）
│   │   │       ├── CoreSkillPanel.vue       # 三、核心技（core1 / core2）
│   │   │       ├── DriveDiscPanel.vue       # 四、驱动盘主词条 4/5/6
│   │   │       ├── SubStatPanel.vue         # 副词条网格 + 54 条上限约束
│   │   │       ├── SetBonusPanel.vue        # 二件套 0~3 组
│   │   │       ├── ResultPanel.vue          # 右侧结果数值
│   │   │       ├── BreakdownPanel.vue       # 计算明细（来源追溯）
│   │   │       └── ModeBadge.vue            # 通用/命破/锋御 模式标识
│   │   │
│   │   ├── router/
│   │   │   └── index.ts            # 路由表 + history 模式 + ?mode= 查询参数同步
│   │   │
│   │   ├── stores/                 # Pinia 状态
│   │   │   ├── panelStore.ts       # 全部输入项 + 计算结果 + 来源明细
│   │   │   ├── presetStore.ts      # 代理人/音擎预设列表与筛选
│   │   │   └── uiStore.ts          # 当前计算模式、折叠状态等纯 UI 态
│   │   │
│   │   ├── composables/            # 组合式逻辑（跨组件复用的行为）
│   │   │   ├── usePanelCalc.ts     # 调用后端计算、防抖、错误态
│   │   │   ├── useSubStatLimit.ts  # 副词条总条数 ≤54 的钳制逻辑
│   │   │   └── usePanelMode.ts     # standard/rupture/fengyu 模式切换与文案替换
│   │   │
│   │   ├── api/                    # 与 FastAPI 的唯一通信层
│   │   │   ├── client.ts           # fetch 封装、baseURL、错误规范化
│   │   │   ├── panel.ts            # POST /api/panel/calculate
│   │   │   └── presets.ts          # GET  /api/presets/{agents,weapons}
│   │   │
│   │   ├── types/                  # TS 类型定义，与后端 schemas 一一对应
│   │   │   ├── panel.ts
│   │   │   └── preset.ts
│   │   ├── constants/              # 枚举与常量：面板模式、职业标签、属性键名
│   │   ├── utils/                  # 纯函数：格式化 fmt、百分比、钳制
│   │   └── data/                   # 前端静态兜底数据（后端不可用时的降级预设）
│   │
│   ├── tests/                      # Vitest 单元测试
│   │
│   └── legacy/                     # 过渡期：现有原生页面，Vue3 完成后整体删除
│       ├── pages/
│       │   ├── index.html                  # 原 启动界面.html
│       │   ├── calculator.html             # 原 代理人面板计算器.html
│       │   ├── redirect-rupture.html       # 原 命破代理人面板计算器.html
│       │   ├── redirect-fengyu.html        # 原 锋御代理人面板计算器.html
│       │   ├── example-template.html       # 原 测试范例计算器模板.html
│       │   └── guide.html                  # 原 面板计算方式学习指南.html
│       ├── styles/calculator.css           # 原 css/calculator.css
│       ├── scripts/calculator.js           # 原 js/calculator.js
│       ├── scripts/calculator-config.js    # 原 js/calculator-config.js
│       ├── data/agent-presets.js           # 原 data/agent-presets.js
│       └── data/weapon-presets.js          # 原 data/weapon-presets.js
│
├── backend/                        # Python 计算服务
│   ├── src/zzz_panel/              # 可安装包（src 布局，避免污染仓库根）
│   │   ├── __init__.py             # 版本号
│   │   ├── __main__.py             # python -m zzz_panel
│   │   ├── cli.py                  # 命令行入口（原 main.py 的打印逻辑迁到这里）
│   │   │
│   │   ├── core/                   # 纯计算层：零 IO、零 Web 框架依赖，可单测
│   │   │   ├── __init__.py
│   │   │   ├── models.py           # PanelInputs / PanelResult 数据类
│   │   │   ├── panel.py            # calculate_panel 主体（承自 main.py）
│   │   │   ├── modifiers.py        # 词条/套装/音擎修正量的合成与分类
│   │   │   ├── modes.py            # 命破贯穿力、锋御实际暴击率等模式专属公式
│   │   │   ├── breakdown.py        # 来源明细生成（对齐 legacy 的 src/b_* 追溯）
│   │   │   └── constants.py        # 1/2/3 号固定主词条等硬编码常量
│   │   │
│   │   ├── api/                    # FastAPI 传输层，只做协议转换
│   │   │   ├── __init__.py
│   │   │   ├── app.py              # create_app()：装配路由、CORS、异常处理
│   │   │   ├── deps.py             # 依赖注入（预设缓存、客户端标识）
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── panel.py        # POST /api/panel/calculate
│   │   │       ├── presets.py      # GET  /api/presets/agents|weapons
│   │   │       └── health.py       # GET  /api/health
│   │   │
│   │   ├── schemas/                # Pydantic 请求/响应模型（与 core 数据类解耦）
│   │   │   ├── panel.py            # PanelRequest / PanelResponse
│   │   │   └── preset.py
│   │   │
│   │   ├── services/               # 用例编排：core 的调用方，供 API 与 CLI 复用
│   │   │   ├── panel_service.py    # 编排：请求 → core → 明细 → 响应
│   │   │   └── preset_service.py   # 预设读取、筛选、校验
│   │   │
│   │   └── presets/               # 预设数据加载
│   │       ├── __init__.py
│   │       ├── loader.py           # 读取根 data/*.json，带 mtime 缓存
│   │       └── validate.py         # 预设结构校验（对齐 calculator.js 的防御性校验）
│   │
│   └── tests/
│       ├── test_panel.py           # core 纯函数单测（含 main.py 现有示例作为回归用例）
│       ├── test_modes.py           # 命破/锋御公式
│       ├── test_breakdown.py       # 明细来源与 legacy 输出一致
│       ├── test_presets.py         # 预设加载与校验
│       └── test_api.py            # FastAPI 路由测试
│
├── data/                           # 唯一真实数据源（本次仅建目录说明，内容后续生成）
│   ├── README.md                   # 说明：此处 JSON 为权威数据
│   ├── agent-presets.json          # 预留：由 tools/ 脚本从 Wiki 生成
│   └── weapon-presets.json         # 预留
│
├── docs/                           # 项目文档
│   ├── README.md                   # 文档索引
│   ├── architecture.md             # 整体架构、分层与数据流
│   ├── directory-layout.md         # 本方案的目录说明（长期维护依据）
│   ├── calculation-rules.md        # 面板计算规则（现学习指南的可维护文本版）
│   ├── data-schema.md              # 预设 JSON 与 API 契约
│   ├── migration-vue3.md           # Vue3 迁移分步指南
│   └── legacy-pages.md             # legacy 页面说明与删除时机
│
├── tools/                          # 开发辅助脚本（不含数据抓取，数据抓取仍在 skills 内）
│   ├── README.md
│   ├── dev.ps1                     # 一键起后端 + 前端 dev
│   └── sync_presets.py             # 预留：JSON → legacy JS 包装 / 前端 public 同步
│
├── 启动界面.html                    # 临时重定向页 → frontend/legacy/pages/index.html
├── 代理人面板计算器.html             # 临时重定向页 → frontend/legacy/pages/calculator.html
├── 命破代理人面板计算器.html         # 临时重定向页 → frontend/legacy/pages/redirect-rupture.html
├── 锋御代理人面板计算器.html         # 临时重定向页 → frontend/legacy/pages/redirect-fengyu.html
├── 测试范例计算器模板.html           # 临时重定向页 → frontend/legacy/pages/example-template.html
├── 面板计算方式学习指南.html         # 临时重定向页 → frontend/legacy/pages/guide.html
│
├── .github/skills/                 # 位置不变（Skill 契约依赖相对路径 scripts/）
└── .kilo/                          # 不动
```

---

## 二、目录与关键文件用途说明

### 顶层

| 路径 | 用途 |
| --- | --- |
| `README.md` | 项目总览：技术栈、快速开始（两条命令）、目录导航、legacy 状态说明、迁移路线。当前为空，本次重写 |
| `.gitignore` | 忽略 `__pycache__/`、`*.pyc`、`.venv/`、`node_modules/`、`dist/`、`.env`、`.pytest_cache/`、`.ipynb_checkpoints/` |
| `pyproject.toml` | 唯一 Python 依赖源。`name` 改为 `zzz-panel`；新增 `[build-system]`（hatchling，`packages = ["backend/src/zzz_panel"]`）、`[project.scripts] zzz-panel = "zzz_panel.cli:main"`、FastAPI 相关依赖、pytest 配置 |
| `uv.lock` | 随 `pyproject.toml` 用 `uv lock` 重新生成 |

### frontend/（Vue3 主战场）

| 目录 | 用途与边界 |
| --- | --- |
| `index.html` | Vite 强制要求的入口模板，含 `<script type="module" src="/src/main.ts">` |
| `vite.config.ts` | 插件、`server.proxy`（`/api` → `http://127.0.0.1:8000`，避免 CORS）、路径别名 `@` → `src`、构建输出 |
| `public/` | **原样拷贝**到 `dist/` 根，不做指纹化。放"运行时按 URL 取"的资源。当前 160 张 PNG 放这里——因为它们尚无任何代码引用，若放 `src/assets` 则不会被 Vite 打进产物 |
| `src/assets/` | 会被 Vite 处理：`import` 后生成带 hash 的 URL，可被 CSS 引用。页面内联插图、自定义字体、全局样式放这里 |
| `src/assets/styles/` | `tokens.css`（颜色/间距变量，替代现在散落的 `#dc2626`、`#f0f2f5` 硬编码）、`base.css`（reset）、`components.css`（`.field`/`.module`/`.breakdown-item` 等复用类）。承自 `css/calculator.css` 的样式最终归宿 |
| `src/views/` | 路由级页面，一一对应现有 6 个 HTML。`redirect-rupture/fengyu` 不需要视图，改由 `CalculatorView` 读 `?mode=` 渲染 |
| `src/components/layout/` | 页面骨架，与业务无关 |
| `src/components/common/` | 通用件：`BaseSelect`、`NumberField`、`StatRow` 等，对应 `fillSelect()`、`num()` 的复用形态 |
| `src/components/calculator/` | 业务组件，按 legacy 页面的 `.module` 切分。保持与现有 DOM id 语义对应（`base_hp`、`core1`、`sub_grid`…），便于对照迁移 |
| `src/router/` | 路由表 + `beforeEnter` 守卫。需把 legacy 的 `?mode=standard\|rupture\|fengyu` 提升为路由 query，刷新后保持 |
| `src/stores/` | Pinia。`panelStore` 是唯一输入真源；`presetStore` 管代理人/音擎预设与联动筛选；`uiStore` 放纯 UI 态（模式、折叠），避免污染计算状态 |
| `src/composables/` | 跨组件复用的行为。`useSubStatLimit` 封装 legacy 中"总条数 >54 自动回退"的隐式约束；`usePanelMode` 封装锋御模式的文案替换（`能量自动回复` → `锐能自动累积`） |
| `src/api/` | **唯一**网络出口。禁止组件内直接 `fetch`。`client.ts` 统一 baseURL、超时、错误结构 |
| `src/types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 一一对应，改一处同步另一处 |
| `src/constants/` | 枚举：面板模式、职业标签、属性键名（`hp/atk/def/impact/cr/cd/ac/am/pr/er/pen_val/penforce`） |
| `src/utils/` | 纯函数：`fmt`（对齐 `calculator.js:388` 的 10 位小数取整 + 千分位规则）、`clamp`、百分比格式化 |
| `src/data/` | 前端静态兜底数据。仅在后端不可用时降级使用，正常路径走 API |
| `tests/` | Vitest 单测，优先覆盖 `utils/fmt`、`composables/useSubStatLimit` |

### frontend/legacy/（过渡保留，Vue3 完成后整体删除）

| 路径 | 说明 |
| --- | --- |
| `pages/calculator.html` | 统一计算器。唯一引用外部资源的页面，5 处引用全部改为 `../` 前缀 |
| `pages/index.html` | 启动界面，锚点改为 `calculator.html` |
| `pages/redirect-rupture.html` / `redirect-fengyu.html` | 跳转壳，`meta refresh` 目标改为 `calculator.html?mode=…`。**Vue3 完成后这两个文件应删除**，因为 `CalculatorView` 已能直接读 query 参数 |
| `pages/example-template.html` / `guide.html` | 独立单文件，无外部引用，只需移动 |
| `styles/calculator.css` | 现有唯一样式表。未来迁移到 `src/assets/styles/` |
| `scripts/calculator-config.js` | 选项常量（`CORE_OPTIONS` 等）。**是数据抓取脚本的正则解析源**，不可随意改动格式 |
| `scripts/calculator.js` | 全部交互与计算逻辑。计算部分（`calc()`）未来由后端 `core/` 接管；DOM 操作部分（`fillSelect`、联动下拉、模式文案替换）迁到 Vue 组件/composable |
| `data/agent-presets.js`、`data/weapon-presets.js` | `window.AGENT_PRESETS` / `window.WEAPON_PRESETS`。**由 skill 脚本生成，不要手改**。未来改为从根 `data/*.json` 读取 |

> 重要：`frontend/legacy/` 位于 Vite root 内，dev server 可通过 `/legacy/pages/calculator.html` 访问；但它**不参与 `npm run build`**，不会被拷进 `dist/`。这是有意的——legacy 只是迁移期的对照实现。

### backend/（Python 计算服务）

| 目录 | 职责与约束 |
| --- | --- |
| `core/` | **唯一规则真源**。硬约束：不 import fastapi/pydantic、不读文件、不打印。输入 `PanelInputs` → 输出 `PanelResult`。这样同一份规则可被 API、CLI、未来的批量计算三方复用，也能脱离 Web 环境单测 |
| `core/models.py` | 承自 `main.py` 的 `PanelInputs` dataclass。补齐 JS 侧已有而 Python 侧缺失的字段：`penforce`、`energy_accumulation`、`d4/d5/d6` 主词条、3 组二件套、`mode` |
| `core/panel.py` | `calculate_panel()`，承自 `main.py:108`。**注意差异**：JS 版（`calculator.js:517-536`）把"核心基础值"并入基础值再乘百分比，且含 `0.3×atk+0.1×hp` 贯穿力、`cd×0.35+cr` 实际暴击率；Python 版（`main.py:171-173`）没有贯穿力/实际暴击率。迁移时以 JS 版为行为基准，Python 版为公式参考 |
| `core/modes.py` | 模式专属公式：standard / rupture（贯穿力）/ fengyu（实际暴击率） |
| `core/breakdown.py` | 生成来源明细。**必须对齐** `calculator.js:567-583` 的 `b_*` 文案结构，否则 Vue 迁移后右侧"计算明细"面板会变样 |
| `api/app.py` | `create_app()`。装配 CORS（`http://localhost:5173`）、全局异常处理、路由注册 |
| `api/routes/` | 只做 HTTP 协议转换：请求 → `schemas` → `services` → 响应。不写业务逻辑 |
| `schemas/` | Pydantic 模型。与 `core` 的 dataclass 分离：core 保持框架无关，schemas 承担校验与 OpenAPI 文档 |
| `services/` | 用例编排。`panel_service` 被 API 和 CLI 共同调用，保证"网页算的"和"命令行算的"结果一致 |
| `presets/loader.py` | 读取根 `data/*.json`，按 mtime 缓存，避免每次请求读盘 |
| `presets/validate.py` | 结构校验。**迁移 `calculator.js:47-58` 的防御性校验**（缺 `roleTag`、重复 id、核心加成无法由选项表示等）到这里，并改成启动时一次性校验 + 失败即报错 |
| `backend/tests/` | `main.py` 现有的 `EXAMPLE` 输入作为回归用例固化进 `test_panel.py`，确保迁移前后数值一致 |

### data/、docs/、tools/

| 目录 | 用途 |
| --- | --- |
| `data/*.json` | **未来唯一的真实数据源**。注意与 `frontend/legacy/data/*.js` 的区别：后者是由这里生成的过渡产物（JS 全局变量格式），仅供 legacy 页面使用 |
| `docs/` | 长期文档。`calculation-rules.md` 是 `面板计算方式学习指南.html` 的可维护文本版；`data-schema.md` 记录预设 JSON 与 API 契约；`migration-vue3.md` 记录迁移进度 |
| `tools/` | 开发辅助。`dev.ps1` 一键起后端+前端。**数据抓取脚本刻意不放这里**——它们是 Skill 契约的一部分，必须留在 `.github/skills/*/scripts/` |

---

## 三、文件移动清单与需同步修改的引用

### 3.1 移动清单（原路径 → 新路径）

> 建议用 `git mv` 执行，以便 Git 识别为重命名。

| # | 原路径 | 新路径 |
| --- | --- | --- |
| 1 | `启动界面.html` | `frontend/legacy/pages/index.html` |
| 2 | `代理人面板计算器.html` | `frontend/legacy/pages/calculator.html` |
| 3 | `命破代理人面板计算器.html` | `frontend/legacy/pages/redirect-rupture.html` |
| 4 | `锋御代理人面板计算器.html` | `frontend/legacy/pages/redirect-fengyu.html` |
| 5 | `测试范例计算器模板.html` | `frontend/legacy/pages/example-template.html` |
| 6 | `面板计算方式学习指南.html` | `frontend/legacy/pages/guide.html` |
| 7 | `css/calculator.css` | `frontend/legacy/styles/calculator.css` |
| 8 | `js/calculator.js` | `frontend/legacy/scripts/calculator.js` |
| 9 | `js/calculator-config.js` | `frontend/legacy/scripts/calculator-config.js` |
| 10 | `data/agent-presets.js` | `frontend/legacy/data/agent-presets.js` |
| 11 | `data/weapon-presets.js` | `frontend/legacy/data/weapon-presets.js` |
| 12 | `images/agents/*.png`（60） | `frontend/public/images/agents/*.png` |
| 13 | `images/weapons/*.png`（100） | `frontend/public/images/weapons/*.png` |
| 14 | `main.py` | 拆分至 `backend/src/zzz_panel/core/panel.py` + `models.py` + `cli.py`（见 3.3） |
| 15 | `__pycache__/main.cpython-313.pyc` | **删除**（`git rm --cached` + 删目录），并由 `.gitignore` 覆盖 |

移动完成后 `css/`、`js/`、`data/`、`images/` 四个旧目录应为空并被删除。

### 3.2 需同步修改的引用（共 8 处代码 + 4 处文档/脚本）

**A. `frontend/legacy/pages/calculator.html`（5 处，head 区）**

| 行 | 改前 | 改后 |
| --- | --- | --- |
| 8 | `<link rel="stylesheet" href="css/calculator.css">` | `href="../styles/calculator.css"` |
| 187 | `<script src="data/agent-presets.js">` | `src="../data/agent-presets.js"` |
| 188 | `<script src="data/weapon-presets.js">` | `src="../data/weapon-presets.js"` |
| 189 | `<script src="js/calculator-config.js">` | `src="../scripts/calculator-config.js"` |
| 190 | `<script src="js/calculator.js">` | `src="../scripts/calculator.js"` |

> `<script>` 的**加载顺序不可调整**：`data/*` 必须先于 `scripts/calculator.js` 执行（后者在顶层直接读 `AGENT_PRESETS`、`CORE_OPTIONS`）。

**B. `frontend/legacy/pages/index.html`（1 处）**

- L180：`<a class="card standard" href="代理人面板计算器.html">` → `href="calculator.html"`

**C. `frontend/legacy/pages/redirect-rupture.html`（1 处）**

- L7：`content="0; url=代理人面板计算器.html?mode=rupture"` → `url=calculator.html?mode=rupture`

**D. `frontend/legacy/pages/redirect-fengyu.html`（1 处）**

- L7：`content="0; url=代理人面板计算器.html?mode=fengyu"` → `url=calculator.html?mode=fengyu`

**E. Skill 脚本默认路径（3 处，脚本位置不变）**

| 文件 | 位置 | 改后 |
| --- | --- | --- |
| `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py` | L317 `--config` 默认值 | `frontend/legacy/scripts/calculator-config.js` |
| 同上 | L318 `--out` 默认值 | `frontend/legacy/data/agent-presets.js` |
| `.github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py` | L26 `OUTPUT` | `frontend/legacy/data/weapon-presets.js` |

> 这两个脚本的路径是**相对仓库根**的，SKILL.md 里的调用方式不变，但需在 SKILL.md 中补一句"必须在仓库根目录执行"。

**F. Skill 文档中的路径文字（4 处）**

| 文件 | 行 | 原文 → 改后 |
| --- | --- | --- |
| `.github/skills/do_calculatorModel/SKILL.md` | 25 | `代理人面板计算器.html`、`js/calculator.js`、`js/calculator-config.js`、`data/agent-presets.js` → 各自新路径 |
| `.github/skills/read-zzz-agent-stats/SKILL.md` | 61 | `` `data/agent-presets.js` `` → `` `frontend/legacy/data/agent-presets.js` `` |
| `.github/skills/read-zzz-engine-stats/SKILL.md` | 138、163 | `` `data/weapon-presets.js` `` → `` `frontend/legacy/data/weapon-presets.js` `` |

**G. `README.md`**（重写时引用新路径）

**H. 无需改引用的项（已核实）**

- `css/calculator.css`：无 `url()`、无 `@import`、无外部字体 → 移动后样式零影响
- `images/**`：全仓库无任何 HTML/JS/CSS 引用 → 移动零影响（这也是可以安全放进 `public/` 的前提）
- `example-template.html`、`guide.html`：单文件内联，无外部引用 → 仅移动
- `js/calculator.js`、`data/*.js` 内部：无相对路径引用（已 grep 确认）→ 移动零影响

### 3.3 `main.py` 的拆分

不整体搬迁，按职责拆三处：

| 源 | 目标 |
| --- | --- |
| `main.py:14-94` `PanelInputs` | `backend/src/zzz_panel/core/models.py` |
| `main.py:97-236` `_resolve_weapon_bonus` / `calculate_panel` | `backend/src/zzz_panel/core/panel.py` |
| `main.py:239-299` `_fmt` / `EXAMPLE` / `__main__` 打印块 | `backend/src/zzz_panel/cli.py`；`EXAMPLE` 改放到 `backend/tests/` 作为回归 fixture |

同时**不搬运**的部分（本次不做，属后续任务）：贯穿力、实际暴击率、驱动盘 1~6 号词条、二件套、面板模式——这些 JS 侧已有而 Python 侧缺失，属于"补齐"而非"搬迁"，在 Vue3 迁移阶段一并做（见第五节）。

### 3.4 新增的重定向页（6 个，根目录）

统一内容（以 `启动界面.html` 为例）：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=frontend/legacy/pages/index.html">
  <title>已移动</title>
</head>
<body>
  <p>本页面已移动至 <a href="frontend/legacy/pages/index.html">frontend/legacy/pages/index.html</a>。</p>
</body>
</html>
```

> 注意：这类跳转依赖**相对路径**，因此仅在以 `file://` 方式直接打开仓库根目录时有效。经 HTTP 服务访问时也成立（同一目录层级）。Vue3 迁移完成后，连同这 6 个文件一并删除。

---

## 四、迁移到 Vue3 的分步建议

每步都保持 `legacy` 可用，随时可回退。

**第 0 步 · 搭壳（不迁移任何业务）**
1. 在 `frontend/` 初始化 Vite + Vue3 + TS：`npm create vite@latest . -- --template vue-ts`（在 `frontend/` 内，注意 `legacy/` 已存在，需选择"忽略现有文件"或手工合并）
2. 配置 `vite.config.ts`：`server.proxy = { '/api': 'http://127.0.0.1:8000' }`、别名 `@` → `src`
3. 建 `router/index.ts`（3 条路由：Launcher / Calculator / Guide）、`stores/panelStore.ts`（先空）、`App.vue` 只放 `<router-view/>`
4. 验收：`npm run dev` 能打开，`/legacy/pages/calculator.html` 仍可访问，两者互不影响

**第 1 步 · 静态结构（无计算）**
5. 把 `legacy/styles/calculator.css` 拆进 `src/assets/styles/`：`tokens.css`（提取颜色/间距变量）+ `base.css` + `components.css`
6. 按 `.module` 边界把 `calculator.html` 的 DOM 拆成 `components/calculator/*`，全部用 `v-model` 双向绑定到 `panelStore`，**计算结果先写死**
7. `views/LauncherView.vue` 复刻启动界面卡片
8. 验收：新页面渲染与 legacy 像素级一致，切换所有下拉无报错

**第 2 步 · 交互逻辑（仍在前端算）**
9. `useSubStatLimit`（≤54 钳制）、`usePanelMode`（锋御文案替换）、`calculator.js:80-136` 的音擎三级联动、`:183-222` 的代理人标签联动，全部从 JS 翻译为 composable/store action
10. `applyAgentPreset`（`calculator.js:224-365`）的**防御性校验**在前端先保留一份（用于即时反馈），后续与后端 `presets/validate.py` 对齐
11. 验收：同一组输入，新旧页面显示完全相同的 12 项数值与明细文案

**第 3 步 · 计算下沉到 Python**
12. 后端按第五节落地 `core/` + `api/`
13. `src/api/panel.ts` + `usePanelCalc`（防抖 150~300ms）替换前端 `calc()`
14. `src/utils/fmt` 与后端格式化规则保持一致（或统一由后端返回已格式化字符串）
15. 验收：`backend/tests/test_panel.py` 中 legacy 抽样用例数值全等

**第 4 步 · 预设数据改造**
16. 用 `tools/sync_presets.py` 把 `legacy/data/*.js` 转成根 `data/*.json`（脚本需可重复执行且字节幂等）
17. `presetStore` 改从 `GET /api/presets/*` 拉取
18. 抓取脚本（`refresh_*_presets.py`）输出目标改为 `data/*.json`；此时 legacy 页面需要 `data/*.json` 的 JS 包装，由同步脚本反向生成

**第 5 步 · 收尾**
19. 吸收 `guide.html`、`example-template.html` 为 `GuideView` / `ExampleView`
20. `npm run build` 验证产物；删除 `frontend/legacy/`、根目录 6 个重定向页
21. 在 `docs/migration-vue3.md` 记录每步完成状态与回退方式

---

## 五、计算部分迁移到 Python 的实现与目录集成

### 5.1 分层与依赖方向

```
Vue 组件 (frontend/src/components)
   │  只依赖 src/api/*.ts 的类型签名，不感知 HTTP 细节
   ▼
src/api/client.ts  ──HTTP/JSON──►  backend/src/zzz_panel/api/routes
                                          │ 仅协议转换
                                          ▼
                                   services/panel_service
                                          │ 编排
                                          ▼
                              core/  ◄── cli.py 也调用这一层
                              （纯函数、零 IO、零框架）
```

铁律：
- `core/` 不得 `import fastapi` / `import pydantic`、不得读文件、不得 `print`
- `api/` 与 `cli.py` 都不得重复实现公式，必须走 `services/`
- 这样"网页显示的"与"命令行打印的"永远一致

### 5.2 API 契约

```
GET  /api/health
     → { "status": "ok", "version": "0.1.0" }

GET  /api/presets/agents
     → { "items": [ { id, name, roleTag, panelMode, base{}, coreBonuses[], ... } ] }
GET  /api/presets/weapons
     → { "items": [ { id, name, grade, roleTag, baseKind, baseAttack, baseDefense, substat{} } ] }

POST /api/panel/calculate
  body  { mode, base{}, weapon{}, core[2], drives{fixed, d4, d5, d6},
          substats{ hp_flat: n, ... }, sets[3] }
  resp  { totals{ hp, atk, def, cr, cd, dmg, pr, penforce, actualCr,
                  impact, ac, er, am, penVal },
          breakdown{ hp: [ {label, value} ], ... } }
```

`breakdown` 采用结构化数组而非 HTML 字符串，前端自行渲染——这样 Python 不必输出中文文案，格式化与换行规则留在前端 `utils/fmt`。

### 5.3 与现有 Python 原型的差异（迁移时必须处理）

| 项 | `main.py` 现状 | `calculator.js` 现状 | 处理方式 |
| --- | --- | --- | --- |
| 贯穿力 | 无 | `0.3×最终ATK + 0.1×最终HP`（`:524`） | 以 JS 为准，移入 `core/modes.py` |
| 实际暴击率 | 无 | `CD×0.35 + CR`（`:529`） | 以 JS 为准，移入 `core/modes.py` |
| 核心基础值 | 并入百分比计算基数（`:171-173`） | 显式 `+S.atk_base` 后再乘百分比（`:517-523`） | **数值等价，但需逐条验证**；以 JS 写法为准 |
| 驱动盘 1/2/3 固定词条 | 无 | 2200 HP / 316 ATK / 184 DEF（`:473-475`） | 移入 `core/constants.py` |
| 驱动盘 4/5/6 | 有 `disc_main` 字段但示例全 0 | 6选1 / 5选1 / 6选1 | `core/modifiers.py` |
| 二件套 | 有 `set_*` 字段 | 3 组独立选择 | `core/modifiers.py` |
| 面板模式 | 无 | standard / rupture / fengyu | `core/modes.py` |
| 锋御武器基础防御力 | `weapon_base_def` 字段存在 | 按 `baseKind` 切换 | 两版一致，需单测锁定 |
| `penforce` / `energy_accumulation` | 缺 | 有（`calculator.js:192-193`） | 补入 `core/models.py` |

**回归策略**：先把 `main.py:247-282` 的 `EXAMPLE` 原样搬进 `backend/tests/test_panel.py`，作为迁移前后数值不变的锚点；再逐项补齐上表缺失能力，每补一项加一条断言。

### 5.4 开发与运行

```powershell
# 后端（热重载）
uv run uvicorn zzz_panel.api.app:app --reload --port 8000

# 后端 CLI（保留原 main.py 的演示输出）
uv run zzz-panel

# 前端
cd frontend; npm run dev          # /api 自动代理到 8000

# 一键（tools/dev.ps1）
.\tools\dev.ps1

# 测试
uv run pytest backend/tests
cd frontend; npm run test
```

生产部署时用 FastAPI 挂载 `frontend/dist` 静态文件，单进程同时提供 API 与页面，无需 CORS。

### 5.5 配置与数据文件位置

| 项 | 位置 | 说明 |
| --- | --- | --- |
| 预设 JSON | `data/*.json`（仓库根） | 唯一真实源。前端不直接读，经 API；CLI 直读 |
| 同步脚本 | `tools/sync_presets.py` | 双向：`data/*.json` → `frontend/legacy/data/*.js`（迁移期）；`data/*.json` → 前端本地兜底 |
| 抓取脚本 | `.github/skills/*/scripts/refresh_*.py` | 保持原位（Skill 契约），输出目标改指 `data/*.json` |
| 环境变量 | `frontend/.env.example` → `VITE_API_BASE_URL` | 默认 `/api`（走 dev 代理） |

---

## 六、执行步骤清单（供实施 agent 逐条执行）

1. `git status` 确认工作区干净；新建 `.gitignore`；`git rm --cached __pycache__/main.cpython-313.pyc` 并删除该目录
2. `mkdir -p` 全部目标目录骨架；空目录用 `README.md` 占位（Git 不跟踪空目录）
3. 按 3.1 表格依次 `git mv`（#1–#13），确认旧目录 `css/ js/ data/ images/` 已空并删除
4. 按 3.2 A–D 修改 4 个 legacy HTML 的 8 处引用；逐页用浏览器打开验证（含 `?mode=rupture` / `?mode=fengyu` 直达）
5. 新建 6 个根目录重定向页
6. 拆分 `main.py` → `backend/src/zzz_panel/`（`core/models.py`、`core/panel.py`、`cli.py`、各级 `__init__.py`、`__main__.py`）
7. 更新 `pyproject.toml`（name、`[build-system]`、`[project.scripts]`、fastapi/uvicorn/pydantic 依赖、pytest 配置），`uv lock` 重新生成 lock
8. `uv run zzz-panel` 验证输出与重构前 `python main.py` 完全一致
9. 按 3.2 E–F 更新两个 skill 脚本的默认路径与 3 处 SKILL.md 文字
10. 新建 `backend/tests/test_panel.py`，以 `EXAMPLE` 为回归用例跑通
11. 编写 `README.md` 与 `docs/`（至少 `architecture.md`、`directory-layout.md`、`migration-vue3.md`）
12. 本次不落地 `package.json` / `vite.config.ts` / `src/**` 的实际代码（Vue3 阶段再做），仅保留目录骨架与占位说明

## 七、风险与注意事项

| 风险 | 缓解 |
| --- | --- |
| Vite 脚手架初始化时把 `legacy/` 当冲突文件 | 在 `frontend/` 内初始化并明确选择"忽略现有文件"，或手工创建 `package.json` |
| `<script>` 加载顺序被误改导致 `AGENT_PRESETS` undefined | 修改 3.2 A 时保持行序不变；验收时打开控制台确认无报错 |
| `data/*.js` 被误手改 | 文件顶部不加注释（会被覆盖写入），靠 `docs/` 与 SKILL.md 说明"生成物，勿手改" |
| `images/` 移入 `public/` 后被误 import | `public/` 下的资源只能按 URL 引用，Vite 不支持 `import`；需在 `docs/directory-layout.md` 写明 |
| `pyproject.toml` 改名导致 `uv.lock` 失效 | 改完立即 `uv lock`；`.venv` 若失效则 `uv sync` |
| 根目录 6 个中文重定向页长期残留 | 在 `docs/migration-vue3.md` 标注"第 5 步删除"，并列入收尾 checklist |
| 拆分 `main.py` 时数值漂移 | 先原样搬运 + 回归测试通过，再做任何补齐 |

## 八、明确不在本次范围内

- 不改写任何现有 HTML 为 Vue 组件
- 不实现 `core/modes.py`、`core/modifiers.py` 的缺失能力（仅在 5.3 表格中记录差异）
- 不把 `data/*.js` 转换为 JSON（仅建目录与说明）
- 不落地 `package.json` / `vite.config.ts` / `src/**` 实际代码
- 不引入 pandas / matplotlib / seaborn 到计算链路（现有依赖保持不动，是否移入 optional 依赖组另行决定）
