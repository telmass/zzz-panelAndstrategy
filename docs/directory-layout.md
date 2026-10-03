# 目录职责详解

## 顶层

| 路径 | 职责 |
| --- | --- |
| `pyproject.toml` | 唯一 Python 依赖源（uv）。`[project.scripts]` 暴露 `zzz-panel` 命令；`[tool.hatch.build.targets.wheel]` 指向 `backend/src/zzz_panel`；`[tool.pytest.ini_options]` 配置 `pythonpath` |
| `uv.lock` | 锁文件，改依赖后必须 `uv lock` |
| `.python-version` | Python 版本锁定（>= 3.13） |
| `.gitignore` | 忽略 `__pycache__/`、`*.pyc`、`.venv/`、`node_modules/`、`dist/`、`.env` 等 |
| `*.html`（根目录 6 个） | **临时**重定向页，兼容旧书签。Vue3 迁移完成后删除 |

## frontend/ — 前端工程（Vite root）

| 目录 | 职责与边界 |
| --- | --- |
| `index.html` | Vue3 应用入口，Vite 要求其位于 root 根 |
| `vite.config.ts` | dev 代理 `/api` → `http://127.0.0.1:8000`（避免 CORS）、别名 `@` → `src` |
| `public/` | **Vite 原样拷贝到 `dist/` 根，不做指纹化。** 放「运行时按 URL 取」的资源。注意：`public/` 下的文件**不能被 `import`**，只能按路径引用。当前存放 160 张代理人/音擎 PNG |
| `src/assets/` | **经 Vite 处理**：`import` 后生成带 hash 的 URL，可被 CSS `url()` 引用。放页面内联插图、自定义字体、全局样式 |
| `src/assets/styles/` | `tokens.css`（设计变量，替代散落的 `#dc2626` 硬编码）、`base.css`（reset）、`components.css`（`.field` / `.module` / `.breakdown-item` 等复用类）。`legacy/styles/calculator.css` 的最终归宿 |
| `src/views/` | 路由级页面，一一对应现有 6 个 HTML |
| `src/components/layout/` | 页面骨架（AppHeader / AppShell / AppFooter），与业务无关 |
| `src/components/common/` | 通用件：BaseSelect / NumberField / StatRow |
| `src/components/calculator/` | 业务组件，按 legacy 页面的 `.module` 切分 |
| `src/router/` | 路由表 + 守卫。需把 legacy 的 `?mode=standard\|rupture\|fengyu` 提升为路由 query |
| `src/stores/` | Pinia。`panelStore` 为输入唯一真源；`presetStore` 管预设联动；`uiStore` 放纯 UI 态 |
| `src/composables/` | 跨组件复用的行为：`usePanelCalc`、`useSubStatLimit`（≤54 钳制）、`usePanelMode`（锋御文案替换） |
| `src/api/` | **唯一**网络出口。组件内禁止直接 `fetch` |
| `src/types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 一一对应 |
| `src/constants/` | 枚举：面板模式、职业标签、属性键名。第 4 步第 20 条后选项表迁走，只留纯枚举 |
| `src/utils/` | 纯函数：`fmt`（须对齐 `calculator.js` 的取整与千分位规则）、`clamp` |
| `tests/` | Vitest 单测 |

### frontend/legacy/ — 过渡期原生实现

Vue3 迁移完成后**整个目录删除**。

| 路径 | 说明 |
| --- | --- |
| `pages/index.html` | 原「启动界面.html」 |
| `pages/calculator.html` | 原「代理人面板计算器.html」，唯一引用外部资源的页面 |
| `pages/redirect-rupture.html` | 原「命破代理人面板计算器.html」，`meta refresh` 到 `calculator.html?mode=rupture` |
| `pages/redirect-fengyu.html` | 原「锋御…」，同上，`?mode=fengyu` |
| `pages/example-template.html` | 原「测试范例计算器模板.html」 |
| `pages/guide.html` | 原「面板计算方式学习指南.html」 |
| `styles/calculator.css` | 现有唯一样式表 |
| `scripts/calculator-config.js` | 选项常量。**是数据抓取脚本的正则解析源，格式不可随意改动** |
| `scripts/calculator.js` | 全部交互与计算逻辑。计算部分未来由 `core/` 接管，DOM 部分迁到 Vue 组件/composable |
| `data/agent-presets.js`<br>`data/weapon-presets.js` | **Skill 脚本生成物，勿手改**（每次运行整体覆盖） |

> `legacy/` 位于 Vite root 内，dev server 可通过 `/legacy/pages/calculator.html` 访问；
> 但它**不参与 `npm run build`**，不会被拷进 `dist/`。这是有意的。

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
| `data/*.json` | **未来唯一的真实数据源。** 与 `frontend/legacy/data/*.js` 的区别：后者是由这里生成的过渡产物 |
| `docs/` | 长期文档 |
| `tools/` | 开发辅助脚本。**数据抓取脚本刻意不放这里**——它们是 Skill 契约的一部分，必须留在 `.github/skills/*/scripts/` |
| `.github/skills/` | Skill 定义与抓取脚本，位置固定 |
