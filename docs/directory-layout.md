# 目录职责详解

## 顶层

| 路径 | 职责 |
| --- | --- |
| `pyproject.toml` | 唯一 Python 依赖源（uv）。`[project.scripts]` 暴露 `zzz-panel` 命令；`[tool.hatch.build.targets.wheel]` 指向 `backend/src/zzz_panel`；`[tool.pytest.ini_options]` 配置 `pythonpath` |
| `uv.lock` | 锁文件，改依赖后必须 `uv lock` |
| `.python-version` | Python 版本锁定（>= 3.13） |
| `.gitignore` | 忽略 `__pycache__/`、`*.pyc`、`.venv/`、`node_modules/`、`dist/`、`.env` 等 |

## frontend/ — 前端工程（Vite root）

| 目录 | 职责与边界 |
| --- | --- |
| `index.html` | Vue3 应用入口，Vite 要求其位于 root 根 |
| `vite.config.ts` | dev 代理 `/api` → `http://127.0.0.1:8000`（避免 CORS）、别名 `@` → `src` |
| `public/` | **Vite 原样拷贝到 `dist/` 根，不做指纹化。** 放「运行时按 URL 取」的资源。注意：`public/` 下的文件**不能被 `import`**，只能按路径引用。当前存放 160 张代理人/音擎 PNG |
| `src/assets/` | **经 Vite 处理**：`import` 后生成带 hash 的 URL，可被 CSS `url()` 引用。放页面内联插图、自定义字体、全局样式 |
| `src/assets/styles/` | `tokens.css`（设计变量，替代散落的 `#dc2626` 硬编码）、`base.css`（reset）、`components.css`（`.field` / `.module` / `.breakdown-item` 等复用类）。原 `legacy/styles/calculator.css` 的最终归宿 |
| `src/views/` | 路由级页面：`LauncherView`（`/`）、`CalculatorView`（`/calculator`）、`GuideView`（`/guide`） |
| `src/components/layout/` | 页面骨架（AppHeader / AppShell / AppFooter），与业务无关 |
| `src/components/common/` | 通用件：BaseSelect / NumberField / StatRow |
| `src/components/calculator/` | 业务组件，按原页面的 `.module` 切分 |
| `src/router/` | 路由表 + 守卫。原 legacy 的 `?mode=standard\|rupture\|fengyu` 已提升为路由 query |
| `src/stores/` | Pinia。`panelStore` 为输入唯一真源；`presetStore` 管预设联动；`uiStore` 放纯 UI 态 |
| `src/composables/` | 跨组件复用的行为：`usePanelCalc`、`useSubStatLimit`（≤54 钳制）、`usePanelMode`（锋御文案替换） |
| `src/api/` | **唯一**网络出口。组件内禁止直接 `fetch` |
| `src/types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 一一对应 |
| `src/constants/` | 枚举：面板模式、职业标签、属性键名。第 4 步第 20 条后选项表迁走，只留纯枚举 |
| `src/utils/` | 纯函数：`fmt`（须对齐 `calculator.js` 的取整与千分位规则）、`clamp` |
| `tests/` | Vitest 单测 |

### frontend/tests/fixtures/legacy-calculator/ — 只读参照实现

Vue3 迁移完成后 `frontend/legacy/` 整体删除，但其中计算部分作为**对拍基准**
被原样保留在这里。**禁止修改**——改了基准，三方对拍就变成自己跟自己比。

| 路径 | 说明 |
| --- | --- |
| `pages/calculator.html` | 原「代理人面板计算器.html」，唯一引用外部资源的页面 |
| `scripts/calculator.js` | 全部交互与计算逻辑，当前实现的**行为基准** |
| `scripts/calculator-config.js` | 选项常量。**是数据抓取脚本的正则解析源，格式不可随意改动** |
| `styles/calculator.css` | 旧样式表，其规则已拆进 `src/assets/styles/` |
| `data/agent-presets.js`<br>`data/weapon-presets.js` | `sync_presets.py --to-legacy` 生成物，勿手改 |

已删除、不再保留的页面：`index.html`、`guide.html`、`example-template.html`、
`redirect-rupture.html`、`redirect-fengyu.html`。逐页去向见
[legacy-pages.md](legacy-pages.md)。

> 夹具位于 Vite root 内，dev server 可通过
> `/tests/fixtures/legacy-calculator/pages/calculator.html` 打开人工核对，
> 但它**不参与 `npm run build`**，不会被拷进 `dist/`；`tsconfig.json` 已 exclude。

## backend/ — Python 计算服务

| 目录 | 职责与约束 |
| --- | --- |
| `src/zzz_panel/core/` | **唯一规则真源。** 零 IO、零 Web 框架依赖。`models.py`（输入模型）、`panel.py`（`calculate_panel`）、`modes.py`（模式专属计算）；`constants.py` / `modifiers.py` / `breakdown.py` 为预留待实现 |
| `src/zzz_panel/api/` | FastAPI 传输层（预留）。只做协议转换 |
| `src/zzz_panel/schemas/` | Pydantic 请求/响应模型（预留） |
| `src/zzz_panel/services/` | 用例编排（预留），被 API 与 CLI 共同调用 |
| `src/zzz_panel/presets/` | 预设加载与结构校验（预留） |
| `src/zzz_panel/cli.py` | 命令行入口，承自原 `main.py` 的打印块 |
| `tests/` | pytest 回归测试 |

## data/、docs/、tools/

| 目录 | 职责 |
| --- | --- |
| `data/*.json` | **唯一的真实数据源。** `frontend/tests/fixtures/legacy-calculator/data/*.js` 是由这里生成的对拍夹具产物 |
| `docs/` | 长期文档 |
| `tools/` | 开发辅助脚本。**数据抓取脚本刻意不放这里**——它们是 Skill 契约的一部分，必须留在 `.github/skills/*/scripts/` |
| `.github/skills/` | Skill 定义与抓取脚本，位置固定 |
