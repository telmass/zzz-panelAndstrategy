# 目录职责详解

## 1. 顶层

| 路径 | 职责 |
| --- | --- |
| `README.md` | 项目入口文档：简介、功能、技术栈、快速开始、目录结构 |
| `pyproject.toml` | 唯一 Python 依赖源（uv）。`name` 为 `zzz-panel-and-strategy`，`[project.scripts]` 暴露同名命令；`[tool.hatch.build.targets.wheel]` 指向 `backend/src/zzz_panel`；`[tool.pytest.ini_options]` 配置 `pythonpath` 与 `testpaths` |
| `uv.lock` | 锁文件，改依赖后必须 `uv lock` |
| `.python-version` | Python 版本锁定（>= 3.13） |
| `.gitignore` | 忽略 `__pycache__/`、`*.pyc`、`.venv/`、`node_modules/`、`dist/`、`.env` 等 |

根目录**没有 HTML 文件**。迁移期的 6 个中文书签兼容页已在第5 步删除，
记录见 [completeds/legacy-pages.md](completeds/legacy-pages.md)。

## 2. frontend/ — 前端工程（Vite root）

| 路径 | 职责与边界 |
| --- | --- |
| `index.html` | Vue3 应用入口。Vite 要求其位于 root 根 |
| `.env.example` | `VITE_API_BASE_URL` 的取值示例。**构建期变量**，运行时改无效 |
| `vite.config.ts` | dev 代理 `/api` → `http://127.0.0.1:8000`（避免 CORS）；别名 `@` → `src`、`@data` → `../data`；**Vitest 配置也在此文件的 `test` 块中**（无独立 `vitest.config.ts`） |
| `tsconfig.json` | `strict` + `noUnusedLocals` + `noUnusedParameters`；别名 `@/*`、`@data/*`；`exclude` 含 `tests/fixtures` |
| `package.json` | 6 个脚本：`dev` / `build` / `preview` / `typecheck` / `test` / `test:watch` |
| `public/` | **Vite 原样拷贝到 `dist/` 根，不做指纹化。** 不能被 `import`，只能按 URL 引用。当前 167 张 PNG：60 代理人 + 100 音擎 + 7 roletag 图标（见下方说明） |
| `tools/` | 两个独立 Node 诊断脚本，不参与构建，也不在任何 npm script 中 |
| `tests/` | Vitest 测试 + 夹具，见第 4 节 |

### 2.1 frontend/src/

| 目录 | 职责与边界 |
| --- | --- |
| `main.ts` | 引导：建 app + Pinia，**`mount` 之前 `await loadAll()`** 装载预设 |
| `App.vue` | `<n-config-provider>` 包 `<router-view />`；主题映射见 `composables/useNaiveTheme.ts` |
| `views/` | 路由级页面，3 个：`LauncherView`（`/`）、`CalculatorView`（`/calculator`）、`GuideView`（`/guide`） |
| `components/layout/` | `BackToLauncher.vue` —— 子页左上角的「返回主页」。**与业务无关** |
| `components/common/` | 表单与布局原语：`PanelModule`（模块卡片外壳）、`SelectField`、`NumberField`、`TextField`、`StepperInput`。代理人与音擎改用 naive-ui 的 `n-cascader`，故**无** `GroupedSelectField`；`SelectField` 仍被核心与驱动盘主词条使用 |
| `components/calculator/` | 6 个业务模块 + `ResultPanel`，对应计算器页的六块UI |
| `components/guide/` | 4 个纯展示组件：`GuideSection`、`GuideCallout`、`GuideTable`、`GuideAttrGrid` |
| `router/` | 3 条路由表。**无导航守卫** |
| `stores/` | Pinia 两个 store：`panelStore`（输入唯一真源）、`presetStore`（预设拉取）。**均不持久化** |
| `composables/` | `usePanelCalc`（防抖调用后端 + 明细渲染）、`useAgentPreset`（预设校验与套用）、`usePanelMode`（模式派生显隐与文案）、`useSubStatLimit`（副词条钳制）、`useCascaderIcons`（代理人与音擎共用的 cascader 选项图标与文案）、`useNaiveTheme`（CSS 变量 → `themeOverrides`） |
| `api/` | **唯一**网络出口。`panel.ts`（计算）、`presets.ts`（预设）、`errors.ts`（`ApiError` 及两个子类） |
| `types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 对齐 |
| `constants/` | **只有一个文件** `calculatorOptions.ts`：`@data/options.json` → 7 张 `RuleOption[]`，加枚举与常量，以及 `HIDE_STANDARD_MODE_LABEL` + `panelModeTagLabel()`（隐藏「通用」模式名的唯一开关） |
| `utils/` | `fmt.ts`（`fmt` + `escapeHtml`）、`clamp.ts`（`clamp` + `normalizeCount`） |
| `assets/styles/` | 4 个文件，**顺序由 `index.css` 固定**：tokens → base → components |
| `types/`、`README.md` | 见下|

各目录的具体文件清单：

| 路径 | 说明 |
| --- | --- |
| `assets/styles/index.css` | 仅用 `@import` 按序引入下列三个，**自身不写任何规则** |
| `assets/styles/tokens.css` | 75 个设计变量（颜色、间距、圆角、阴影、布局、模块强调色、结果区渐变）。**无字号令牌**，也**无暗色模式** |
| `assets/styles/base.css` | reset + 排版 + 页面骨架 + 各类栅格；3 个响应式断点（960 / 560 / 480px） |
| `assets/styles/components.css` | 10 个区块：模块卡片、表单字段、提示文字、固定词条徽标、副词条步进器、代理人与音擎选择器及头像卡片、结果区、按钮、指南页、启动界面 |
| `README.md` | 见 [requirements.md](requirements.md) 同级说明；实际内容为本目录的使用约定 |

### 2.2 资源放置规则（易错）

|放哪 | 规则 |
| --- | --- |
| `frontend/public/` | 运行时按 URL 取的资源。**不能被 `import`** |
| `frontend/src/assets/` | 会被 `import`、生成带 hash 的 URL、可被 CSS `url()` 引用。**未被 import 的文件不进构建产物** |

> ⚠️ `public/images/` 下 167 张 PNG **已全部接入**：
> **`weapons/`（100 张）**——音擎 `n-cascader` 的头像卡片与二级选项前缀按
> `/images/weapons/{id}.png` 取图（`WeaponModule.vue`）。
> **`agents/`（60 张）**——代理人 `n-cascader` 同构，按
> `/images/agents/{id}.png` 取图（`AgentBaseModule.vue`）。
> **`icons/`（7 张）**——两个 `n-cascader` 共用的一级选项前缀按
> `/images/icons/{slug}.png` 取图，roletag → slug 映射见
> `composables/useCascaderIcons.ts` 的 `ROLE_ICON`（slug 取自官方 Wiki profession key）。
>
> `icons/` 曾用中文文件名（`强攻.png`），已重命名为小写 ASCII slug。

## 3. backend/ — Python 计算服务

src-layout，包名 `zzz_panel`。

| 目录 | 职责与约束 |
| --- | --- |
| `core/` | **规则真源。** 零 IO、零 Web 框架依赖、不`print`。见下表 |
| `schemas/` | Pydantic 请求/响应模型。`base.py` 提供 `CamelModel`（camelCase 别名） |
| `services/` | 用例编排。**不含任何公式**，只做命名空间转换与结果打包 |
| `api/` | FastAPI 传输层。`app.py` 是应用与CORS；`routes/panel.py`、`routes/presets.py`。**不挂载静态文件** |
| `presets/` | `loader.py`（按 mtime 缓存的 JSON 加载）、`validate.py`（语义校验） |
| `cli.py` | 命令行入口。无子命令，固定跑一组示例并打印 12 行 |
| `tests/` | pytest，6 个文件 |

### 3.1 core/ 各模块

| 文件 | 职责 |
| --- | --- |
| `panel.py` | 两个入口：`calculate_panel`（CLI 契约，输出 12 键）与 `calculate_selection`（API 契约，输出 9 个结构化字段）。`_apply_totals` 是基础公式的实现处 |
| `modes.py` | 三种模式的专属公式 |
| `options.py` | 6 张选项表 + `find_option`。**规则表的权威源之一** |
| `constants.py` | `DISC_FIXED_STATS`（1/2/3 号固定词条）、`FENGYU_BLAST_DMG`。规则表权威源之二 |
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

> `api/__init__.py` 与 `api/routes/__init__.py` 的 docstring 仍提到未实现的
> `create_app`、`deps.py`、`health.py` 与路径 `/api/panel/calculate`
> （实际是 `/api/panel/calc`，且health 内联在 `app.py`）。**以
> [api-reference.md](api-reference.md) 为准。**

## 4. frontend/tests/

| 路径 | 说明 |
| --- | --- |
| `calculator-view.spec.ts` | 31 项渲染断言（计算器骨架、启动页、返回导航、指南页） |
| `panel-interactions.spec.ts` | 46 项交互与后端对接 |
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
| `legacy_cases.json` | 抽样用例夹具，由 `frontend/tools/dump_legacy_cases.mjs` 导出 |
| `_fmt_driver.cjs` | 从参照实现提取 `fmt` 函数体并执行 |
| `README.md` | 各文件覆盖内容 |

## 6. data/、docs/、tools/、.github/

| 目录 | 职责 |
| --- | --- |
| `data/` | **唯一真实数据源**，三个 JSON 全部是生成物。见 [data-schema.md](data-schema.md) |
| `docs/` | 长期技术文档。见 [docs/README.md](README.md) |
| `docs/completeds/` | 已完成事项的归档（迁移记录、旧页面删除记录）。**不是当前状态的描述** |
| `tools/` | 开发辅助脚本。**数据抓取脚本刻意不放这里**——它们是 Skill 契约的一部分，必须留在 `.github/skills/*/scripts/` |
| `tools/dev.ps1` | 一键启停前后端。**必须保留 UTF-8 BOM**，否则 Windows PowerShell 5.1 会因中文产生 ParserError |
| `.github/skills/` | Skill 定义与抓取脚本，位置固定 |

## 7. 相关文档

- [requirements.md](requirements.md) —— 项目定位与已知限制
- [architecture.md](architecture.md) —— 分层与依赖方向
- [development.md](development.md) —— 目录相关的开发流程与坑