# 目录职责详解

## 1. 顶层

| 路径 | 职责 |
| --- | --- |
| `README.md` | 项目入口文档：简介、功能、技术栈、快速开始、目录结构 |
| `pyproject.toml` | 唯一 Python 依赖源（uv）。`name` 为 `zzz-panel-and-strategy`，`[project.scripts]` 暴露同名命令；`[tool.hatch.build.targets.wheel]` 指向 `backend/src/zzz_panel`；`[tool.pytest.ini_options]` 配置 `pythonpath` 与 `testpaths` |
| `uv.lock` | 锁文件，改依赖后必须 `uv lock` |
| `pylock.toml` | **Worker 的**锁文件（PEP 751），由 `pywrangler sync` 生成。**要提交**：它固定 Pyodide 环境里每个依赖的版本，否则同一份代码在不同机器上部署出不同的 Worker |
| `.python-version` | Python 版本锁定（>= 3.13） |
| `.gitignore` | 忽略 `__pycache__/`、`*.pyc`、`.pytest_cache/`、`.venv/`、`node_modules/`、`dist/`、`.env`，以及 Worker 生成物 `backend/src/zzz_panel/_bundled_data.py`、`python_modules/`、`.venv-workers/`、`.wrangler/`、`.wrangler-dry/` |
| `index.html` | 仓库根的**指引页**，不是应用本体。内联样式，取值抄自 `frontend/src/assets/styles/tokens.css`。给出 dev server 入口、三个入口的路径对照，以及「为什么根目录不能放应用」的说明。**不参与任何构建**（Vite root 在 `frontend/`），也因此不会被拷进 `dist/` |
| `wrangler.jsonc` | Cloudflare Worker 配置：`main` 指向 `backend/src/worker.py`，`compatibility_flags` 含 `python_workers`，`assets` 指向 `frontend/dist/` 并开 `not_found_handling: single-page-application`。见 [deployment.md](deployment.md) 第 5 节 |

根目录的 `index.html` 刻意**不做 `meta refresh` 自动跳转**：应用在
`http://localhost:5173`，未启动时跳转只会得到浏览器连接错误，反而丢掉启动步骤，
故改为可点击的入口加命令。

迁移期的 6 个中文书签兼容页已在第5 步删除，记录见
[completeds/legacy-pages.md](completeds/legacy-pages.md)。

## 2. frontend/ — 前端工程（Vite root）

| 路径 | 职责与边界 |
| --- | --- |
| `index.html` | Vue3 应用入口。Vite 要求其位于 root 根 |
| `.env.example` | `VITE_API_BASE_URL` 的取值示例。**构建期变量**，运行时改无效 |
| `vite.config.ts` | dev 代理 `/api` → `http://127.0.0.1:8000`（避免 CORS）；别名 `@` → `src`、`@data` → `../data`；**Vitest 配置也在此文件的 `test` 块中**（无独立 `vitest.config.ts`） |
| `tsconfig.json` | `strict` + `noUnusedLocals` + `noUnusedParameters`；别名 `@/*`、`@data/*`；`exclude` 含 `tests/fixtures` |
| `package.json` | 6 个脚本：`dev` / `build` / `preview` / `typecheck` / `test` / `test:watch` |
| `public/` | **Vite 原样拷贝到 `dist/` 根，不做指纹化。** 不能被 `import`，只能按 URL 引用。当前 209 张 PNG：60 代理人 + 100 音擎 + 7 roletag 图标 + 30 驱动盘套装图标 + 6 技能 + 1 属性（凛刃）+ 1 等级（S）+ 4 攻略独有（叶瞬光），完整清单见第 2.2 节 |
| `tools/` | 两个独立 Node 诊断脚本，不参与构建，也不在任何 npm script 中 |
| `tests/` | Vitest 测试 + 夹具，见第 4 节 |

### 2.1 frontend/src/

| 目录 | 职责与边界 |
| --- | --- |
| `main.ts` | 引导：建 app + Pinia，**`mount` 之前 `await loadAll()`** 装载预设 |
| `App.vue` | `<n-config-provider>` 包 `<router-view />`；主题映射见 `composables/useNaiveTheme.ts` |
| `views/` | 路由级页面，5 个：`LauncherView`（`/`）、`CalculatorView`（`/calculator`）、`GuideView`（`/guide`）、`StrategyPickerView`（`/strategy`）、`StrategyView`（`/strategy/:slug`） |
| `components/layout/` | `BackToLauncher.vue` —— 子页左上角的「返回主页」。**与业务无关** |
| `components/common/` | 表单与布局原语：`PanelModule`（模块卡片外壳）、`SelectField`、`NumberField`、`TextField`、`StepperInput`。代理人与音擎改用 naive-ui 的 `n-cascader`，故**无** `GroupedSelectField`；`SelectField` 仍被核心与驱动盘主词条使用 |
| `components/calculator/` | 6 个业务模块 + `ResultPanel`，对应计算器页的六块UI |
| `components/guide/` | 4 个纯展示组件：`GuideSection`、`GuideCallout`、`GuideTable`、`GuideAttrGrid` |
| `router/` | 5 条路由表：`/`、`/calculator`、`/guide`、`/strategy`、`/strategy/:slug`。唯一的导航守卫在 `/strategy/:slug`：slug 不在 `constants/strategyGuides.ts` 登记表里就重定向回 `/`（避免 iframe 加载不存在的静态页） |
| `stores/` | Pinia 两个 store：`panelStore`（输入唯一真源）、`presetStore`（预设拉取）。**均不持久化** |
| `composables/` | `usePanelCalc`（防抖调用后端 + 明细渲染）、`useAgentPreset`（预设校验与套用）、`usePanelMode`（模式派生显隐与文案）、`useSubStatLimit`（副词条钳制）、`useCascaderIcons`（代理人与音擎共用的 cascader 选项图标与文案）、`useNaiveTheme`（CSS 变量 → `themeOverrides`） |
| `api/` | **唯一**网络出口。`panel.ts`（计算）、`presets.ts`（预设）、`errors.ts`（`ApiError` 及两个子类） |
| `types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 对齐 |
| `constants/` | 两个文件：`calculatorOptions.ts`（`@data/options.json` → 7 张 `RuleOption[]`，加枚举与常量，以及 `HIDE_STANDARD_MODE_LABEL` + `panelModeTagLabel()`——隐藏「通用」模式名的唯一开关，两者都是**模块私有**，只在本文件内生效）与 `strategyGuides.ts`（攻略板块登记表：一条 = `strategy/<slug>/` 一页，决定 `/strategy` 选择页卡片与 `/strategy/<slug>` 可达性） |
| `utils/` | `fmt.ts`（`fmt` + `escapeHtml`）、`clamp.ts`（只导出 `normalizeCount`；`clamp` 为模块私有） |
| `assets/styles/` | 4 个文件，**顺序由 `index.css` 固定**：tokens → base → components |
| `README.md` | 本目录的使用约定，见 [frontend/src/README.md](../frontend/src/README.md) |

各目录的具体文件清单：

| 路径 | 说明 |
| --- | --- |
| `assets/styles/index.css` | 仅用 `@import` 按序引入下列三个，**自身不写任何规则** |
| `assets/styles/tokens.css` | 75 个设计变量（颜色、间距、圆角、阴影、布局、模块强调色、结果区渐变）。**无字号令牌**，也**无暗色模式** |
| `assets/styles/base.css` | reset + 排版 + 页面骨架 + 各类栅格；3 个响应式断点（960 / 560 / 480px） |
| `assets/styles/components.css` | 12 个区块：模块卡片、表单字段、音擎与代理人选择器及头像卡片、提示文字、固定词条徽标、副词条步进器、结果区、按钮、指南页、启动界面、攻略板块选择页（`/strategy`）、攻略页舞台（`/strategy/:slug`） |
| `../README.md` | 本目录的使用约定，见 [frontend/src/README.md](../frontend/src/README.md) |

### 2.2 资源放置规则（易错）

|放哪 | 规则 |
| --- | --- |
| `frontend/public/` | 运行时按 URL 取的资源。**不能被 `import`** |
| `frontend/src/assets/` | 会被 `import`、生成带 hash 的 URL、可被 CSS `url()` 引用。**未被 import 的文件不进构建产物** |

> 📌 **唯一图片根 = `frontend/public/images/`。** 所有引用——应用代码、`data/*.json`、
> `strategy/` 攻略 JSON、文档命令——一律写 **`/images/…` URL**。
> **禁止**再出现页相对 `assets/…` 与仓库相对 `frontend/public/images/…` 两种形态；
> 攻略目录（`strategy/<slug>/`）本身不放任何图片。

```
frontend/public/images/
├── agents/<agentId>.png        # 60，计算器 cascader、攻略立绘/队伍头像、选择页封面
├── weapons/<engineId>.png      # 100，计算器、攻略音擎卡
├── discs/<setId>.png           # 30，攻略驱动盘卡（计算器 UI 接入待做）
├── icons/<profession>.png      # 7，计算器一级选项、攻略/选择页职业标签
├── skills/<key>.png            # 6，全代理人共享：basic/dodge/assist/special/chain/core
├── attributes/<slug>.png       # 1，属性图标（仅 honed_edge，其余属性待补）
├── grades/<grade>.png          # 1，等级图标（s/a/b，当前仅 s）
└── strategy/<slug>/            # 每代理人独有：title/tachie/cinema-2/cinema-3（当前仅叶瞬光 4 张）
```

已接入的取图位置：

> **`weapons/`（100 张）**——音擎 `n-cascader` 的头像卡片与二级选项前缀按
> `/images/weapons/{id}.png` 取图（`WeaponModule.vue`）。
> **`agents/`（60 张）**——代理人 `n-cascader` 同构，按
> `/images/agents/{id}.png` 取图（`AgentBaseModule.vue`）；`/strategy` 选择页封面与
> 攻略页 hero/队伍卡同样按此路径。
> **`icons/`（7 张）**——两个 `n-cascader` 共用的一级选项前缀按
> `/images/icons/{slug}.png` 取图，roletag → slug 映射见
> `composables/useCascaderIcons.ts` 的 `ROLE_ICON`（slug 取自官方 Wiki profession key）。
> `icons/` 曾用中文文件名（`强攻.png`），已重命名为小写 ASCII slug。
>
> **`skills/`（6 张）/ `grades/` / `attributes/` / `strategy/<slug>/`**——只被攻略页
> （`strategy/<slug>/` 静态页，见第 6.1 节）按 `/images/…` URL 消费，不参与计算器。
>
> `discs/`（30 张驱动盘套装图标）由抓取脚本写入、`data/drive-disc-presets.json` 的
> `image` 字段（URL 形态）与攻略页驱动盘卡引用；**计算器 UI 仍未接入**（待做，
> 见 [requirements.md](requirements.md) 第 7 节）。

## 3. backend/ — Python 计算服务

src-layout，包名 `zzz_panel`。

| 目录 | 职责与约束 |
| --- | --- |
| `core/` | **规则真源。** 零 IO、零 Web 框架依赖、不`print`。见下表 |
| `schemas/` | Pydantic 请求/响应模型。`base.py` 提供 `CamelModel`（camelCase 别名） |
| `services/` | 用例编排。**不含任何公式**，只做命名空间转换与结果打包 |
| `api/` | FastAPI 传输层。`app.py` 是应用与CORS；`routes/panel.py`、`routes/presets.py`。**不挂载静态文件** |
| `presets/` | `loader.py`（按 mtime 缓存的 JSON 加载）、`validate.py`（语义校验） |
| `zzz_panel/_bundled_data.py` | **生成物，不提交**。`tools/bundle_worker_data.py` 把 `data/*.json` 的原文编译成两个字符串常量，供 Cloudflare Worker 读取——`pywrangler` 只上传 `.py`，包里的 `.json` 会被静默丢弃。见 [deployment.md](deployment.md) 第 5.3 节 |
| `cli.py` | 命令行入口。无子命令，固定跑一组示例并打印 12 行 |
| `tests/` | pytest，7 个文件 |

### 3.0 backend/src/ 的顶层两个文件

`backend/src/` 既是包目录，也是 Cloudflare Worker 的入口目录——`pywrangler`
会把**入口文件所在目录的整棵子树**附加到 Worker 里，但**只上传 `.py` 文件**。
因此 `worker.py` 必须与 `zzz_panel/` 同级（入口才能以 `zzz_panel.xxx` 正常导入），
而任何非 `.py` 资源（`.json` / `.html`）都到不了线上。预设数据的编译产物因此
也必须是 `.py`。

> 同目录下的 `.json` / `.html` 会被**静默**丢弃：部署不报错，线上却读不到。

| 文件 | 说明 |
| --- | --- |
| `zzz_panel/` | Python 包本体 |
| `worker.py` | Cloudflare Python Worker 入口，只有 `Default = asgi.entrypoint(app)` 一行生效。**本地 uvicorn 开发不经过它** |

### 3.1 core/ 各模块

| 文件 | 职责 |
| --- | --- |
| `panel.py` | 两个入口：`calculate_panel`（CLI 契约，输出 12 键）与 `calculate_selection`（API 契约，输出 9 个结构化字段）。`_apply_totals` 是基础公式的实现处 |
| `modes.py` | 三种模式的专属公式 |
| `options.py` | 6 张选项表 + `find_option`。**规则表的权威源之一** |
| `constants.py` | `DISC_FIXED_STATS`（1/2/3 号固定词条）。规则表权威源之二。锋御的 `FENGYU_BLAST_DMG` 属模式公式，在 `modes.py` |
| `modifiers.py` | 选择项 → 加成累加 + 来源记录。含累加器与副词条钳制 |
| `breakdown.py` | 逐行计算明细，输出结构化片段而非 HTML |
| `models.py` | `PanelInputs` dataclass（CLI 用的输入模型，约 50 个标量字段） |
| `fmt.py` | `fmt` —— 取整、千分位、小数位。**跨语言对拍的基准之一** |

### 3.2 api/ 的实际形状

| 项 | 值 |
| --- | --- |
| 路由前缀 | `/api`（两个 router 都带此前缀） |
| CORS 白名单 | 仅 `http://localhost:5173` 与 `http://127.0.0.1:5173`，`allow_credentials=False` |
| 静态文件 | **无** |
| 异常处理 | 无自定义 handler；仅预设路由捕获 `PresetLoadError` → 503 |

> 各 `__init__.py` 只保留职责说明，**不做再导出**。调用方一律直接 import 子模块
> （`from .panel import calculate_panel`），不从包根取。`/api/health` 定义在 `app.py`，
> 不在 `routes/` 里——路径以 [api-reference.md](api-reference.md) 为准。

## 4. frontend/tests/

| 路径 | 说明 |
| --- | --- |
| `calculator-view.spec.ts` | 34 项渲染断言（计算器骨架、启动页、返回导航、指南页、攻略选择页与 `/strategy/:slug` 路由守卫/iframe 指向） |
| `panel-interactions.spec.ts` | 51 项交互与后端对接 |
| `legacy-parity.spec.ts` | 4 项三方对拍 |
| `support/` | 夹具层：`setup.ts`、`router.ts`、`api.ts`（假后端）、`backend.ts`（拉起真实 uvicorn）、`flush.ts` |
| `fixtures/legacy-calculator/` | **只读参照实现**，见第 5 节 |

### frontend/tests/fixtures/legacy-calculator/

迁移前的原生实现，原样保留作为对拍基准。**禁止修改。**

| 路径 | 说明 |
| --- | --- |
| `pages/calculator.html` | 原「代理人面板计算器.html」，唯一引用外部资源的页面 |
| `scripts/calculator.js` | 全部交互与计算逻辑，当前实现的**行为基准** |
| `scripts/calculator-config.js` | 选项常量。**是数据抓取脚本的正则解析源，格式不可随意改动** |
| `styles/calculator.css` | 旧样式表，规则已拆进 `src/assets/styles/` |
| `data/agent-presets.js`<br>`data/weapon-presets.js` | `sync_presets.py --to-legacy` 生成物，勿手改 |
| `README.md` | 维护约束与「已删除页面去向」对照表 |

**子目录结构必须保持**：`calculator.html` 用 `../styles`、`../data`、`../scripts`
相对引用，改位置会静默失效。

不参与 `npm run build`，`tsconfig.json` 已 exclude。可经 dev server 以
`/tests/fixtures/legacy-calculator/pages/calculator.html` 打开人工核对。

## 5. backend/tests/

| 文件 | 覆盖 |
| --- | --- |
| `test_presets.py` | 加载、结构与语义校验、响应与 JSON 等价、503 行为 |
| `test_panel.py` | 加成链路、武器并入顺序、模式公式、取整 |
| `test_options_json.py` | `options.json` 与 Python 规则表一致 |
| `test_legacy_parity.py` | Python 侧对 `legacy_cases.json` 逐条比对 |
| `test_fmt_parity.py` | 跨语言格式化对拍（用 Node 驱动参照实现） |
| `test_api.py` | 路由形状、CORS、422 触发条件、响应键名 |
| `test_worker_bundle.py` | Worker 部署形态：编译产物与真源逐字节一致、幂等、两侧模块名对得上，以及 `loader.py` 的编译产物回退分支 |
| `conftest.py` | autouse 夹具：默认切断「包内编译产物」这条回退路径。生成物不进版本库，不切断的话测试结论会取决于本机是否跑过生成脚本 |
| `legacy_cases.json` | 抽样用例夹具，由 `frontend/tools/dump_legacy_cases.mjs` 导出 |
| `_fmt_driver.cjs` | 从参照实现提取 `fmt` 函数体并执行 |
| `README.md` | 各文件覆盖内容 |

## 6. data/、docs/、tools/、.github/

| 目录 | 职责 |
| --- | --- |
| `data/` | **唯一真实数据源**，四个 JSON 全部是生成物。见 [data-schema.md](data-schema.md) |
| `docs/` | 长期技术文档。见 [docs/README.md](README.md) |
| `docs/completeds/` | 已完成事项的归档（迁移记录、旧页面删除记录）。**不是当前状态的描述** |
| `tools/` | 开发辅助脚本。**数据抓取脚本刻意不放这里**——它们是 Skill 契约的一部分，必须留在 `.github/skills/*/scripts/` |
| `tools/dev.ps1` | 一键启停前后端。**必须保留 UTF-8 BOM**，否则 Windows PowerShell 5.1 会因中文产生 ParserError |
| `tools/sync_presets.py` | 生成 `data/*.json`（从 legacy 夹具或 `core/options.py`），并校验往返无损 |
| `tools/bundle_worker_data.py` | 把 `data/*.json` 编译进 `backend/src/zzz_panel/_bundled_data.py`，供 Worker 使用。`--check` 只比对不写 |
| `.github/skills/` | Skill 定义与抓取脚本，位置固定 |

### 6.1 strategy/ — 攻略板块

| 路径 | 职责 |
| --- | --- |
| `strategy/<slug>/` | 一名代理人的攻略静态页，**一个目录一个代理人**（当前仅 `ye-shun-guang/`）。目录名即主应用路由 slug |
| `strategy/<slug>/index.html` · `styles.css` · `app.js` | 零依赖静态页模板（从参考实例复制，改数据不改前端） |
| `strategy/<slug>/data/<slug>.json` | 抓取产物（基础信息 / 基础面板 / 技能 / 影画 / 背景图），由 `.github/skills/agent-strategy/scripts/scrape_agent_guide.py` 生成 |
| `strategy/<slug>/data/<slug>.strategy.json` | 攻略编辑内容（加点链 / 武器 / 驱动盘 / 队伍 / 文字攻略，手写；`graduationPanel` 由 `calc_graduation_panel.py` 写入） |

挂载与路由：`frontend/vite.config.ts` 的 `strategyPagesPlugin` 把每个含 `index.html` 的
`strategy/<slug>/` 映射到 `/strategy/<slug>/`（开发期中间件直读、构建期拷入
`dist/strategy/<slug>/`，只收 `.html/.css/.js/.json`）；视图侧是
`/strategy`（`StrategyPickerView`，卡片来自 `frontend/src/constants/strategyGuides.ts`
登记表）与 `/strategy/:slug`（`StrategyView`，iframe 嵌入）。新增代理人 =
`strategy/<slug>/` 目录 + 登记表追加一条，前端无其他改动。

**图片不放在这里**：攻略 JSON 一律写 `/images/…` URL，文件本体落在
`frontend/public/images/`（共享图标进 `skills/ icons/ grades/ attributes/`，
每代理人独有的立绘 / 称号 / 影画背景进 `strategy/<slug>/`）——见第 2.2 节。
抓取脚本的位置约束：「抓取脚本必须留在 `.github/skills/*/scripts/`」，
`strategy/` 根下不放脚本。

## 7. 相关文档

- [requirements.md](requirements.md) —— 项目定位与已知限制
- [architecture.md](architecture.md) —— 分层与依赖方向
- [development.md](development.md) —— 目录相关的开发流程与坑