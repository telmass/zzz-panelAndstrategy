# legacy 页面说明（已归档）

> ⚠️ **归档文档 · 记录已删除的内容。**
> `frontend/legacy/` 与仓库根目录 6 个中文重定向页已于 2026-10-03 全部删除。
>
> 想了解夹具现在的样子，请看
> [directory-layout.md](../directory-layout.md) 第 4 节。
>
> **本文仍有价值的部分**：「迁移期已知特性」一节至今生效——
> `scripts/calculator-config.js` 是数据抓取脚本的正则解析源，
> 改它的格式会让抓取脚本**静默失效**。

`frontend/legacy/` 是重构前的原生 HTML 实现，Vue3 迁移期间是**用户实际使用的版本**。
第 5 步已把它连同仓库根目录的 6 个中文重定向页一并删除。

**但计算部分没有删干净，也不是遗漏** —— 三方对拍需要一份独立的参照实现。
需要用到的那几个文件被原样`git mv` 到了
`frontend/tests/fixtures/legacy-calculator/`（保留 `pages/ data/ scripts/ styles/`
子目录结构，因为 `calculator.html` 用相对路径引用它们）。

| 原路径 | 现在 |
| --- | --- |
| `pages/calculator.html` | `tests/fixtures/legacy-calculator/pages/calculator.html`（只读夹具） |
| `scripts/calculator.js` | `tests/fixtures/legacy-calculator/scripts/calculator.js`（只读夹具） |
| `scripts/calculator-config.js` | `tests/fixtures/legacy-calculator/scripts/calculator-config.js`（抓取脚本仍读它） |
| `styles/calculator.css` | `tests/fixtures/legacy-calculator/styles/calculator.css`（只读夹具） |
| `data/agent-presets.js` | `tests/fixtures/legacy-calculator/data/agent-presets.js`（生成物，见下） |
| `data/weapon-presets.js` | `tests/fixtures/legacy-calculator/data/weapon-presets.js`（生成物，见下） |
| `pages/index.html` | 已删除 → `src/views/LauncherView.vue` |
| `pages/guide.html` | 已删除 → `src/views/GuideView.vue` |
| `pages/example-template.html` | 已删除 → **不吸收**，计算逻辑与统一计算器重复 |
| `pages/redirect-rupture.html` | 已删除 → 路由 query `?mode=rupture` |
| `pages/redirect-fengyu.html` | 已删除 → 路由 query `?mode=fengyu` |
| 根目录 6 个中文页 | 已删除（纯 `meta refresh` 桩，无内容损失） |
| `public/images/{agents,weapons}/*.png` | 保留（现由 Vue3 页面使用） |

## 夹具的维护约束

见 [../../frontend/tests/fixtures/legacy-calculator/README.md](../../frontend/tests/fixtures/legacy-calculator/README.md)。
最重要的一条：**禁止修改夹具内任何文件**。改了参照基准，三方对拍就退化成
「自己和自己比」，永远不会失败。

## 仍然依赖夹具的五处

| 消费者 | 用途 |
| --- | --- |
| `frontend/tests/legacy-parity.spec.ts` | legacy 原生JS ≡ Vue3 ≡ Python，三方对拍 |
| `backend/tests/test_fmt_parity.py` | Python `core.fmt.fmt` ≡ legacy `fmt` |
| `frontend/tools/dump_legacy_cases.mjs` | 导出抽样用例为 `backend/tests/legacy_cases.json` |
| `frontend/tools/diff_breakdown.mjs` | 对拍差异逐行 diff |
| `tools/sync_presets.py --to-legacy` | 由 `data/*.json` 反向生成夹具的 `data/*.js` |

## 迁移期已知特性（历史记录）

- **不参与 `npm run build`**：夹具位于 Vite root 内但不是构建入口，不会进 `dist/`；
  `tsconfig.json` 以 `tests/fixtures` 为 exclude。
- **`data/*.js` 是生成物**：由 `tools/sync_presets.py --to-legacy` 写入，
  **不要手工编辑**。改动预设后跑 `--to-legacy --check`，退出码非 0 即漂移。
- **`scripts/calculator-config.js` 是抓取脚本的正则解析源**：
  `refresh_agent_presets.py` 用正则 `const CORE_OPTIONS = \[(.*?)\];` 解析它，
  `--config` 默认值即指向夹具中的该文件。改动其格式（缩进、引号风格、数组写法）
  会导致抓取脚本静默失效。
- **加载顺序敏感**：`calculator.html` 中两个 `data/*.js` 必须先于
  `calculator.js` 执行，因为后者在顶层直接读取 `AGENT_PRESETS` / `CORE_OPTIONS`。

## 迁移完成时的验收

- [x] `npm run build` 产物可独立运行
- [x] 新实现的计算结果与 legacy 抽样用例全等（`test_legacy_parity.py` 逐条比对）
- [x] `?mode=rupture` / `?mode=fengyu` 直达链接在新实现中可用
- [x] `guide.html` 的内容已被 `GuideView` 覆盖
- [x] `example-template.html` 不再需要保留：其计算逻辑与统一计算器重复，迁移计划决定不吸收，删除无信息损失
- [x] 三方对拍与格式化对拍的基准已迁移到 `tests/fixtures/legacy-calculator/`，两道护栏仍然有效