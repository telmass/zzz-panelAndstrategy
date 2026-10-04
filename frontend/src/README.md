# frontend/src — Vue3 源码

计算器前端的全部源码。**没有任何预设或规则表副本**：`data/options.json`
在**构建期**经 Vite 别名 `@data` → 仓库根 `data/` 直接 import，代理人与音擎预设
则由后端经 HTTP 提供。迁移前的 `src/data/agentPresets.ts` 与
`weaponPresets.ts` 静态兜底已删除。

完整目录职责见 [docs/directory-layout.md](../../docs/directory-layout.md) 第 2 节。

## 目录一览

| 目录 | 内容 |
| --- | --- |
| `views/` | 3 个路由页：`LauncherView`（`/`）、`CalculatorView`（`/calculator`）、`GuideView`（`/guide`） |
| `components/layout/` | `BackToLauncher.vue` —— 子页返回主页，与业务无关 |
| `components/common/` | 表单原语：`PanelModule`、`SelectField`、`NumberField`、`TextField`、`StepperInput`。代理人与音擎都用 naive-ui 的 `n-cascader`，不走这里；`SelectField` 仍被核心与驱动盘主词条使用 |
| `components/calculator/` | 6 个业务模块 + `ResultPanel`，对应计算器页六块 UI |
| `components/guide/` | 4 个纯展示组件：`GuideSection`、`GuideCallout`、`GuideTable`、`GuideAttrGrid` |
| `router/` | 3 条路由，**无导航守卫** |
| `stores/` | Pinia：`panelStore`（输入唯一真源）、`presetStore`。均不持久化 |
| `composables/` | `usePanelCalc`、`useAgentPreset`、`usePanelMode`、`useSubStatLimit`、`useCascaderIcons`（两个 cascader 共用的选项图标与文案）、`useNaiveTheme` |
| `api/` | **唯一**网络出口：`panel.ts`、`presets.ts`、`errors.ts` |
| `types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 对齐 |
| `constants/` | 仅 `calculatorOptions.ts`：`@data/options.json`（构建期从仓库根 `data/` 读）→ 7 张 `RuleOption[]` |
| `utils/` | `fmt.ts`（`fmt` + `escapeHtml`）、`clamp.ts`（仅导出 `normalizeCount`，`clamp` 为模块私有） |
| `assets/styles/` | 4 个文件，顺序由 `index.css` 固定：tokens → base → components |

## 约定

### 网络访问

组件内**禁止直接 `fetch`**，一律经 `src/api/`。基址在 `api/*.ts` 中统一解析：

```ts
(import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api'
```

开发期 Vite 把 `/api` 代理到 `http://127.0.0.1:8000`，因此**不涉及 CORS**。

### 组件不计算

前端不做任何算术。`usePanelCalc.buildRequest()` 只把「选了什么」组装成请求体，
数值全部由后端算完返回。这是第 3 步起的硬约定——否则会出现两套实现漂移。

需要新增公式时，改 `backend/src/zzz_panel/core/`，不是改这里。

### 资源放置

| 放哪 | 规则 |
| --- | --- |
| `frontend/public/` | 运行时按 URL 取。**不能被 `import`** |
| `frontend/src/assets/` | 会被 `import`、生成带 hash URL、可被 CSS `url()` 引用。**未被 import 的文件不进构建产物** |

> `public/images/` 下的 167 张 PNG **全部已接入**：`weapons/`（100 张）由音擎
> `n-cascader`、`agents/`（60 张）由代理人 `n-cascader`，各自的选中卡片按
> `/images/{weapons,agents}/{id}.png` 引用，选项前缀同理；
> `icons/`（7 张）为两个选择器共用的一级 roletag 图标。

### 样式

- 颜色一律走 `assets/styles/tokens.css` 的 CSS 变量，**不写死 hex**。
  唯一的例外是 `CoreModule.vue` 未选择核心时的红色提示（内联样式）。
- 新增样式按区块加进 `components.css`，不要另起文件。
- 无字号令牌、无暗色模式。
- naive-ui 组件的配色经 `App.vue` 的 `n-config-provider` 注入，
  `composables/useNaiveTheme.ts` **从 `tokens.css` 的 CSS 变量读值**再转成
  `themeOverrides`，不另抄一份 hex —— 改令牌两边同时生效。

### 路由与直达链接

`?mode=standard|rupture|fengyu` 由 `CalculatorView.vue` 手动读取
（`new URLSearchParams(...)`），经 `useAgentPreset.initFromQueryParam` 校验，
非法值回落 `standard`。**没有路由守卫**，也没做重定向。

## 相关文档

- [docs/requirements.md](../../docs/requirements.md) —— 功能范围与已知限制
- [docs/architecture.md](../../docs/architecture.md) —— 分层与依赖方向
- [docs/api-reference.md](../../docs/api-reference.md) —— 接口契约
- [docs/development.md](../../docs/development.md) —— 开发流程与常见坑
- [docs/testing.md](../../docs/testing.md) —— 测试策略
- [docs/completeds/migration-vue3.md](../../docs/completeds/migration-vue3.md) —— 迁移记录（已归档）