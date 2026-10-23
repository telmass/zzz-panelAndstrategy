# frontend/src — Vue3 源码

计算器前端的全部源码。**没有任何预设或规则表副本**：`data/rules/calculator-rules.json`
在**构建期**经 Vite 别名 `@data` → 仓库根 `data/` 直接 import，代理人与音擎预设
则由后端经 HTTP 提供。迁移前的 `src/data/agentPresets.ts` 与
`weaponPresets.ts` 静态兜底已删除。

完整目录职责见 [docs/overview/directory-layout.md](../../docs/overview/directory-layout.md) 第 2 节。

## 目录一览

| 目录 | 内容 |
| --- | --- |
| `views/` | 5 个路由页：`LauncherView`（`/`）、`CalculatorView`（`/calculator`）、`GuideView`（`/guide`）、`StrategyPickerView`（`/strategy`，代理人选择）、`StrategyView`（`/strategy/:slug`，Vue 共享渲染器） |
| `components/layout/` | 跨页面布局组件：`BackToLauncher.vue`（子页返回主页）、`BackToTop.vue`（右下角回到顶部） |
| `components/common/` | 表单原语：`PanelModule`、`SelectField`、`NumberField`、`TextField`、`StepperInput`；另有 `SideNav.vue` —— 左侧编号目录（一级编号链接 + 二级子链接 + 窄屏折叠为顶部目录条），版式复刻攻略页 `.sidebar`，**目前只有指南页在用**（计算器是边填边看结果的工具页，一屏内滚完，不放目录）。代理人与音擎都用 naive-ui 的 `n-cascader`，不走这里；`SelectField` 仍被核心与驱动盘主词条使用 |
| `components/calculator/` | 6 个业务模块 + `ResultPanel`，对应计算器页六块 UI |
| `components/guide/` | 4 个纯展示组件：`GuideSection`、`GuideCallout`、`GuideTable`、`GuideAttrGrid` |
| `router/` | 6 条路由（含兜底 `/:pathMatch(.*)*` → 启动页）；`/strategy/:slug` 带 `beforeEnter` 守卫（未登记 slug 回启动页） |
| `stores/` | Pinia 三个：`panelStore`（输入唯一真源）、`presetStore`（预设）、`buildStore`（配装方案，**持久化**到 `localStorage` 键 `zzz.builds.v1`）。前两个不持久化 |
| `composables/` | `usePanelCalc`、`useAgentPreset`、`usePanelMode`、`useSubStatLimit`、`useCascaderIcons`（两个 cascader 共用的选项图标与文案）、`useScrollSpy`（侧边目录滚动高亮：观察 `data-spy-region` 区域容器而非锚点小标题，空窗保留上一个高亮，触底兜底最后一个目标）、`useNaiveTheme`、`useCoreSummary`（核心加成汇总文案）、`useBuildIO`（配装方案的导入 / 导出 / 分享链接）、`useBuildPanel`（配装方案与面板互转） |
| `api/` | **唯一**网络出口：`panel.ts`、`presets.ts`、`errors.ts` |
| `types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 对齐：`panel.ts` · `agentPresets.ts` · `weaponPresets.ts` · `build.ts`（配装方案） |
| `constants/` | `calculatorOptions.ts`（`@data/rules/calculator-rules.json` → 7 张 `RuleOption[]`）、`discPresets.ts`（`@data/catalog/drive-discs.json` → 驱动盘套装，**构建期静态读**，不走后端接口）、`dataManifest.ts`（数据集登记表在前端的视图）、`strategyGuides.ts`（攻略登记表，**由 `tools/gen_strategy_guides.py` 生成**，决定 `/strategy` 卡片与详情可达性）、`navigation.ts`、`guideContent.ts` |
| `strategy/` | 攻略共享层：`renderStrategy.ts`（页面渲染器，从 legacy 静态模板迁移）、`strategyCard.ts`（`保存攻略` 的 JSON 驱动导出卡片）、`substats.ts`（毕业面板 47+7 展示口径）、`basePanel.ts`（基础面板**由代理人预设派生**，攻略 JSON 不再自带副本）+ `strategy.css`（页面与导出卡片样式）。`strategy/<slug>/` 只放数据 |
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

> `public/images/` 是**唯一图片根**，所有引用一律写 `/images/…` URL（禁止页相对
> `assets/…` 与仓库相对 `frontend/public/images/…`）。当前 522 张 webp（统一 webp）：
> `weapons/`（101 张）由音擎 `n-cascader`、`agents/`（61 张）由代理人 `n-cascader`，
> 各自的选中卡片按 `/images/{weapons,agents}/{id}.webp` 引用，选项前缀同理；
> `icons/`（7 张）为两个选择器共用的一级 roletag 图标；`discs/`（30 张驱动盘套装图标）
> 由 `data/catalog/drive-discs.json` 的 `image` 字段与攻略页引用；计算器的「按套装」选择器
> 也用它（`constants/discPresets.ts` 构建期静态读）；
> `skills/`（6 张，全代理人共享）、`attributes/`（10 张）、`grades/`（2 张）与
> `strategy/<slug>/`（305 张，每代理人独有的立绘 / 称号 / 影画背景 / 背景图 / 角色框头像）只被攻略页与导出卡片消费。
> 完整目录树见 [docs/overview/directory-layout.md](../../docs/overview/directory-layout.md) 第 2.2 节。

### 样式

- 颜色一律走 `assets/styles/tokens.css` 的 CSS 变量，**不写死 hex**。
  唯一的例外是 `CoreModule.vue` 未选择核心时的红色提示（内联样式）。
- 新增样式按区块加进 `components.css`，不要另起文件。
- **有**字号令牌：`tokens.css` 的 8 档 `--text-*` + 3 档 `--weight-*`，由
  `python tools/check_ui_scale.py --check` 守住（越界即失败）。无暗色模式（项目明确决策）。
- naive-ui 组件的配色经 `App.vue` 的 `n-config-provider` 注入，
  `composables/useNaiveTheme.ts` **从 `tokens.css` 的 CSS 变量读值**再转成
  `themeOverrides`，不另抄一份 hex —— 改令牌两边同时生效。

### 路由与直达链接

`?mode=standard|rupture|armorer` 由 `CalculatorView.vue` 手动读取
（`new URLSearchParams(...)`），经 `useAgentPreset.initFromQueryParam` 校验，
非法值回落 `standard`。目前唯一的路由守卫在 `/strategy/:slug`：
`strategyGuides.ts` 未登记的 slug 会被重定向回 `/`，避免请求不存在的攻略数据。

攻略数据 `/strategy/<slug>/data/*.json` 由 `vite.config.ts` 的 `strategyDataPlugin` 提供
（开发期中间件直读仓库 `strategy/<slug>/data/`，构建期只把两份 JSON 拷入
`dist/strategy/<slug>/data/`）。页面本体由 `frontend/src/strategy/renderStrategy.ts` 渲染，`保存攻略` 由 `strategyCard.ts` 按同一份 JSON 生成导出卡片，不再有
iframe 或每页 `index.html/app.js/styles.css`。

## 相关文档

- [docs/overview/requirements.md](../../docs/overview/requirements.md) —— 功能范围与已知限制
- [docs/design/architecture.md](../../docs/design/architecture.md) —— 分层与依赖方向
- [docs/reference/api-reference.md](../../docs/reference/api-reference.md) —— 接口契约
- [docs/guides/development.md](../../docs/guides/development.md) —— 开发流程与常见坑
- [docs/guides/testing.md](../../docs/guides/testing.md) —— 测试策略
- [docs/completeds/migration-vue3.md](../../docs/completeds/migration-vue3.md) —— 迁移记录（已归档）