# legacy 页面说明

`frontend/legacy/` 是重构前的原生 HTML 实现，在 Vue3 迁移完成前是**用户实际使用的版本**。

## 文件对照

| 现路径 | 原路径 |
| --- | --- |
| `pages/index.html` | `启动界面.html` |
| `pages/calculator.html` | `代理人面板计算器.html` |
| `pages/redirect-rupture.html` | `命破代理人面板计算器.html` |
| `pages/redirect-fengyu.html` | `锋御代理人面板计算器.html` |
| `pages/example-template.html` | `测试范例计算器模板.html` |
| `pages/guide.html` | `面板计算方式学习指南.html` |
| `styles/calculator.css` | `css/calculator.css` |
| `scripts/calculator.js` | `js/calculator.js` |
| `scripts/calculator-config.js` | `js/calculator-config.js` |
| `data/agent-presets.js` | `data/agent-presets.js` |
| `data/weapon-presets.js` | `data/weapon-presets.js` |
| `public/images/{agents,weapons}/*.png` | `images/{agents,weapons}/*.png` |

## 访问方式

- 直接 `file://` 打开 `frontend/legacy/pages/index.html`
- 或经 Vite dev server 访问 `/legacy/pages/index.html`

## 已知特性

- **不参与 `npm run build`**：`legacy/` 位于 Vite root 内但不是构建入口，
  不会被拷进 `dist/`。这是有意的设计——legacy 只是迁移期的对照实现。
- **`data/*.js` 是生成物**：由 `.github/skills/*/scripts/refresh_*_presets.py`
  整体覆盖写入，**不要手工编辑**。
- **`scripts/calculator-config.js` 是抓取脚本的正则解析源**：
  `refresh_agent_presets.py` 用正则 `const CORE_OPTIONS = \[(.*?)\];` 解析它。
  改动其格式（缩进、引号风格、数组写法）会导致抓取脚本静默失效。
- **加载顺序敏感**：`calculator.html` 中两个 `data/*.js` 必须先于
  `calculator.js` 执行，因为后者在顶层直接读取 `AGENT_PRESETS` / `CORE_OPTIONS`。

## 删除时机

在 [migration-vue3.md](migration-vue3.md) 第 5 步完成后，连同仓库根目录的 6 个
中文重定向页一并删除。删除前请确认：

- [ ] `npm run build` 产物可独立运行
- [ ] 新实现的计算结果与 legacy 抽样用例全等
- [ ] `?mode=rupture` / `?mode=fengyu` 直达链接在新实现中可用
- [ ] `guide.html` 与 `example-template.html` 的内容已被 `GuideView` / `ExampleView` 覆盖
