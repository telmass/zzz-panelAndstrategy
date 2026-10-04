# 变更记录

记录影响使用方式或正确性的变更。纯内部重构不逐条记录，见
[git 历史](https://github.com)。

版本号见 `pyproject.toml` 与 `frontend/package.json`，当前均为 `0.1.0`。

## 2026-10-04 · Cloudflare Worker 部署形态 D（已上线）

### 背景

原先只有「自建服务器 + Nginx 反代」这一条公网部署路径（`docs/deployment.md`
形态 A）。GitHub Pages 托管不了本项目的后端——它是纯静态的，而计算全在
FastAPI 侧。Cloudflare 的 Python Workers 已 GA，可以让**一个 Worker 同时提供
API 与前端静态产物**，正好对上 `frontend/vite.config.ts` 里早已注明的设计意图。

### 线上地址

<https://zzz-panel-and-strategy.huangjiansheng0flipped.workers.dev>

### 变更

新增部署形态 D（`docs/deployment.md` 第 5 节），无新增运行时依赖：

| 文件 | 作用 |
| --- | --- |
| `wrangler.jsonc` | Worker 配置：入口、`python_workers` 标志、assets 路由 |
| `backend/src/worker.py` | Python Worker 入口，只有一行 `asgi.entrypoint(app)` |
| `tools/bundle_worker_data.py` | 把 `data/*.json` 编译进 `zzz_panel/_bundled_data.py` |
| `backend/tests/conftest.py` | autouse 夹具，切断编译产物回退路径，保证测试不依赖本机状态 |
| `backend/tests/test_worker_bundle.py` | 15 项 |

**前端零改动。** 页面与 API 同域，`VITE_API_BASE_URL=/api` 继续有效，
后端 CORS 白名单也不用放开。

### 四个实测踩出来的坑

**1. `pywrangler` 只上传 `.py`，`.json` 被静默丢弃。**
最初把 `data/*.json` 复制进包内 `_data/` 目录，部署不报错、`/api/panel/calc`
也是 200，但 `/api/presets/*` 一律 503。`wrangler deploy --dry-run --outdir`
dump 出来才看清：产物 `zzz_panel/` 里只有 27 个 `.py`，镜像的 JSON 不在其中。
因此数据必须编译成 Python 模块（每行一个相邻字符串字面量，仍与源逐字节一致）。

**2. loader 的编译产物模块名曾拼错。**
`__package__` 在 `presets/loader.py` 里是 `zzz_panel.presets` 而非包根，
拼成了 `zzz_panel.presets._bundled_data`。文件就在包里，线上却报「找不到编译
产物」。已加 `test_default_module_name_matches_generator_output` 钉住两侧名字。

**3. 生成物不进版本库，会让测试结论取决于本机状态。**
`test_missing_file_reports_how_to_generate` 在跑过生成脚本的机器上失败、在 CI
上通过。用 `conftest.py` 的 autouse 夹具统一切断，需要该路径的用例自己装。

**4. wrangler 不读 Windows 系统代理。**
直连 `api.cloudflare.com` 超时，而 PowerShell 走 `127.0.0.1:7892` 的系统代理
正常。wrangler 是 Node 程序，不走 WinINET；需显式给
`NODE_USE_ENV_PROXY=1` 与 `HTTPS_PROXY`。见 `docs/deployment.md` 第 5.7 节。

### 依赖分组按 Pyodide 能力重排

`pywrangler` 只解析 `[project.dependencies]`，其中任何带 C/Rust 扩展的包都会让
`sync` 失败：

| 包 | 原位置 | 现位置 | 原因 |
| --- | --- | --- | --- |
| `uvicorn[standard]` | `dependencies` | `dependency-groups.dev` | `uvicorn` 拉进的 uvloop / httptools 无 PyEmscripten wheel。本地开发仍可用（`uv sync` 默认装 dev 组） |
| `matplotlib` / `pandas` / `seaborn` | `dependencies` | `optional-dependencies.analysis` | 计算链路零引用，且 Pyodide 没有 matplotlib / seaborn |

### 线上自检结果

`/api/health`、`/api/presets/agents`（60 条）、`/api/presets/weapons`（100 条）、
`POST /api/panel/calc`（12 项 totals）、`/`、`/calculator`、`/guide`（SPA 回落）、
`/docs`、`/assets/*`、`/images/*` 全部 200。Worker 启动约 2.3 s。

本地：后端测试 94 → 109 项，前端 86 项不变，0 skip。

> ⚠️ 部署前必须先跑 `python tools/bundle_worker_data.py`。忘了这一步的症状是
> 页面能开但两个级联选择器为空、`/api/presets/*` 返回 503。

## 2026-10-04 · 仓库根新增 `index.html` 指引页

### 背景

仓库是 `backend/` + `frontend/` + `data/` 的 monorepo，从根目录打开看不到任何入口，
容易误以为「项目缺页面」或误把 `frontend/index.html` 搬到根目录。

### 变更

根目录新增 `index.html`：纯静态指引页，给出 dev server 入口按钮、三个入口的路径对照
（源码入口 / 开发服务 / 构建产物），以及根目录不能放应用的原因。内联样式，取值抄自
`frontend/src/assets/styles/tokens.css`。

**不移动 `frontend/index.html`。** Vite 的 `index.html`、`public/`、`dist/` 与 Vitest
用例发现全部以 root（即 `frontend/`）解析，入口上移会让 `/src/main.ts`、静态资源拷贝
路径、产物输出目录与测试发现同时失效。

**也不做 `meta refresh` 自动跳转。** 应用在 `http://localhost:5173`，未启动时跳转只会
得到浏览器连接错误并丢掉启动步骤，因此改为可点击入口加命令。

同步修订 `docs/directory-layout.md` 第 1 节——原文写着「根目录没有 HTML 文件」。

## 2026-10-04 · 修复选择器折叠框里职业标签重复两次

### 问题

`n-cascader` 的 `showPath` 默认为 `true`，此时折叠框显示的不是叶子文案，而是
**整条路径的 label 拼接**（`getPathLabel`，用 ` / ` 连接）。一级项正是职业标签，
叶子文案里又带着同一个职业标签，于是折叠框显示成：

```
强攻 / 伊芙琳·舒瓦利耶 / 强攻 / 火 / S级
```

职业标签出现两次，代理人名称也被挤到中间。该问题与文案长度无关——
补齐属性与评级之前就存在（`强攻 / 伊芙琳·舒瓦利耶 / 强攻`），此前未被注意到。

### 修复

两个选择器都显式加 `:show-path="false"`：

| 文件 | 修复后折叠框 |
| --- | --- |
| `AgentBaseModule.vue` | `伊芙琳·舒瓦利耶 / 强攻 / 火 / S级` |
| `WeaponModule.vue` | `防暴者Ⅵ型 / 强攻 / S级` |

音擎选择器是**同一处缺陷**（`强攻 / 防暴者Ⅵ型 / 强攻 / S级`），一并修掉：
它与 `changelog` 里记录的「选项与卡片文案为 `名称 / 职业 / 等级`」本就不符，
属偏差而非设计。

`showPath` 只影响折叠框文本，不改变选中值、分组、`filterable` 匹配与面板模式。
新增两条用例钉住 `showPath === false` 与「叶子文案自身不重复职业标签」。

> ⚠️ `filterable` 搜索结果浮层仍显示路径拼接文案（含重复的职业标签）。
> 这是 naive-ui 的 `createSelectOptions` 写死的行为，`n-cascader` 未把
> `renderLabel` 透传给该浮层，公开 API 无法改。

## 2026-10-04 · 代理人选择结果补上属性与评级

### 变更

| 变更 | 说明 |
| --- | --- |
| **折叠框选中文案改为 `名称 / 职业 / 属性 / 评级`** | 如「仪玄 / 命破 / 玄墨 / S级」。此前只有 `名称 / 职业`，看不到代理人的属性与稀有度 |
| **头像卡片副信息改为 `职业 / 属性 / 评级`** | 名称已单独一行，故副信息不含名称 |
| **载入提示的括号同步** | 「已载入仪玄（命破 / 玄墨 / S级）的…」 |
| **`filterable` 现在能按属性或评级搜到** | 匹配读的就是 `label`，输入「玄墨」「S级」皆可命中 |

三个展示面共用 `constants/calculatorOptions.ts` 新增的 `agentTagSegments()`，
段序、去重与「通用」隐去规则只定义一处，不会各自漂移。
评级沿用音擎的写法 `${grade}级`；`attribute` / `grade` 缺失时整段略去而非留空档。

段数恒为 4：命破/锋御因 `roleTag` 与模式名同字被去重、通用模式名被隐去，
两种情况都不改变段数。浏览菜单仍只显示名称（走 `renderLabel`），
补齐信息只出现在选中之后。

## 2026-10-04 · 代理人预设新增 `attribute` 与 `grade`

### 变更

| 变更 | 说明 |
| --- | --- |
| **`data/agent-presets.json` 每条新增 `attribute` 与 `grade`** | 取自官方 WIKI 页面 `role_base_info`，60 条全部补齐；记录顺序与原有字段一字未动 |
| **`grade` 由「可选」改为「必填」** | 此前模型上声明了 `grade` 却没有任何数据写入，响应里也从不出现；现在它有真实值，缺值会被校验拦下 |
| **两个字段都参与校验** | `attribute` 限 10 个合法值、`grade` 限 `S`/`A`，前端 `validateAgentPresetData` 同步同一份白名单 |
| **抓取脚本自动写入这两个字段** | `refresh_agent_presets.py` 新增 `ATTRIBUTE_LABELS`（slug → 页面中文），未知 slug 会跳过该代理人并在 `SKIPPED:` 里点名 |
| **「特殊属性」判定规则落地并有测试** | 人数 == 1 即为特殊属性，见下 |

键序上 `attribute` / `grade` 紧跟 `name`，与 `WEAPON_KEY_ORDER` 把 `grade`
放在 `name` 之后的既有约定一致；`roleTag` / `panelMode` 随后才是分组与计算维度。

### 特殊属性的判定规则

> **某个属性当前只有一名代理人持有（人数 == 1），即为特殊属性。仅此一条，无附加条件。**

按当前 60 名代理人，特殊属性为 `烈霜`、`玄墨`、`凛刃`、`流明`（各 1 人）；
`风` 有 2 人，**不是**特殊属性。

刻意不写成硬编码名单，也不附加「属性名不在常规五项内」这类条件：
名单会随官方新代理人过时，而规则与具体是哪些属性无关。结论随数据变化，
因此每次使用都按当前 `agents` 重算，不要缓存。

- 后端：`backend/src/zzz_panel/presets/attributes.py` 的 `special_agent_attributes()`
  与 `is_special_attribute()`
- 前端：`frontend/src/composables/useAgentPreset.ts` 的 `specialAgentAttributes()`
  与 `isSpecialAttribute()`

官方对 `electric` 的写法是**电**（社区口语常作「雷」），数据与白名单均照抄页面；
`凛刃` 也不并入 `物理`，尽管页面自称「更高阶的物理属性」。

## 2026-10-04 · 代理人文案不再显示「通用」

### 变更

| 变更 | 说明 |
| --- | --- |
| **代理人选项、头像卡片与载入提示中不再出现「通用」二字** | 通用代理人的文案由「名称 / 职业 / 通用」缩为「名称 / 职业」，与命破/锋御（角色与模式同字、本就只有两段）形状一致 |
| **命破、锋御的文案完全不变** | 仍显示角色名，两种模式名仍照常出现在文案里 |

实现为**可一键恢复的隐藏**而非删除：`constants/calculatorOptions.ts` 新增
`HIDE_STANDARD_MODE_LABEL`（当前 `true`）与 `panelModeTagLabel(mode)`，
后者在开关打开且 `mode === 'standard'` 时返回空串。所有调用点本就带
`filter(Boolean)`，空串会让这一段从拼接结果里消失，不会留下多余的 ` / `。
把该常量改回 `false` 即完全恢复原文案，**无需改动任何调用点**。

> ⚠️ **只影响显示，绝不影响计算。** `panel.panelMode` 仍照常写成 `'standard'`，
> 三种模式的公式、12 行结果与请求体一个都没变；`PANEL_MODE_LABELS` 本身也仍在，
> 因为 `useAgentPreset` 用它校验 `panelMode` 键是否合法。

> 未改动两处**不在代理人选择器内**的「通用」：`LauncherView.vue` 副标题的模式说明
> 与 `GuideView.vue` 的「攻防血通用计算」——后者是「通用公式」的意思，与面板模式无关。

## 2026-10-04 · 代理人选择改为与音擎同构的 `n-cascader`

### 变更

| 变更 | 说明 |
| --- | --- |
| **两个原生下拉合并为一个级联选择器** | 原「代理人标签 + 代理人名称」两个 `<select>`（`#agent_role` / `#agent_preset`）换成单个 `n-cascader`：一级为职业标签、二级为代理人。与音擎选择器同构，`panelMode` 写进选项文案而非单列筛选轴 |
| 浏览时二级只显示代理人名称 | 与音擎一致：前缀显示头像，标签只显示名字；完整文案留到选中后 |
| 选中后新增头像卡片 | 折叠框下方显示头像 + 名称 + 职业，与音擎卡片同构（副信息经 `agentTagLabel` 拼接，命破/锋御因角色与模式同字只有一段，通用模式名被隐去同样只有一段） |
| 60 张代理人 PNG 接入 | `public/images/agents/` 从「无代码引用」变为选项前缀与选中卡片均引用 |
| 删除两个 getter | `panelStore` 的 `agentRoleOptions`、`filteredAgentPresets` 随标签下拉一起失去调用方，已删除 |

### 实现

新增 `composables/useCascaderIcons.ts`，把音擎原先的 `ROLE_ICON` 映射与两个渲染器
（`render-prefix` / `render-label`）整体搬进去，两个模块改为调用同一个
`createCascaderRenderers({ leafIconDir, leafName })`——差异只有叶子图标目录与名称
解析函数，**渲染行为由构造保证一致，不再靠人工同步两份代码**。
`ROLE_ICON` 的键类型取 `AGENT_ROLE_TAGS` 与 `WEAPON_ROLE_TAGS` 的并集，
任一张表扩容而漏配图标时 `vue-tsc` 立即报错。
CSS 类名 `.weapon-option-icon` 相应改为中性的 `.cascader-option-icon`。

### 与音擎的差异

| 维度 | 音擎 | 代理人 |
| --- | --- | --- |
| 叶子第三段文案 | 等级（`S级`） | 面板模式（`通用`/`命破`/`锋御`）——**无等级字段**。故选项实为两段，见下一行 |
| 实际段数 | 恒 3 段 | 恒 2 段：命破/锋御因 `roleTag` 与模式名同字被去重，通用因模式名被 `HIDE_STANDARD_MODE_LABEL` 隐去（见本日上一条） |
| 文案去重 | 不需要 | **需要**：命破/锋御代理人的 `roleTag` 与模式名同字，不去重会得到「仪玄 / 命破 / 命破」 |
| 选中副作用 | `selectWeaponPreset` 一次写全 | `selectAgentRole` + `applyAgentPreset` **串联**，顺序不可反 |

### 兼容

`selectAgentRole`、`applyAgentPreset` 的语义与提示文案结构均未变
（仅删掉已被新交互取消的「音擎与套装会重置」半句），
`tests/legacy-parity.spec.ts` 的 Vue 侧走 store action，故三方对拍无需改动，仍全绿。

## 2026-10-03 · 音擎菜单项只显示名称，完整信息留到选中后

### 变更

| 变更 | 说明 |
| --- | --- |
| **浏览菜单时二级选项只显示武器名称** | 不再显示 roletag 与评级。选项前缀的武器头像照旧 |
| 一级选项不变 | 仍是职业标签分组名 |
| 选中后展示不变 | 折叠框仍显示「名称 / 职业 / 等级」，下方头像卡片仍显示图标、名称与「职业 / 等级」 |

实现方式：给 `n-cascader` 加 `render-label`，叶子项按 `value` 从 `presetStore.weaponById`
取 `name`。**完整文案仍留在选项的 `label` 字段上**——naive-ui 渲染折叠框时直接读
`rawNode.label` 构造 `selectedOption`（`Cascader.mjs:402`），不经过 `render-label`，
所以选中后的展示没有被这次改动波及。未改 `label` 字段，故 `filterable` 的搜索
结果列表文案也保持原样。

## 2026-10-03 · 音擎下拉选项新增前缀图标

### 变更

| 变更 | 说明 |
| --- | --- |
| **一级选项显示 roletag 图标** | 7 个职业标签各配一张类别图标，取自新增的 `public/images/icons/` |
| **二级选项显示音擎头像** | 与已选中的头像卡片同源，按 `/images/weapons/{id}.png` 取图 |
| **图标文件名改为小写英文** | 原为中文名（`强攻.png` 等），已重命名为 `strike` / `pierce` / `abnormal` / `support` / `guard` / `rupture` / `armero`。slug 取自官方 Wiki profession key，与 `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py` 同源 |
| 缺图不显示破图 | 职业标签未在映射表内、或图片加载失败时隐藏 `<img>`，不留破图方块 |

> 纯展示层改动：新增 `WeaponModule.vue` 的 `ROLE_ICON` 映射与 `render-prefix`，
> **未触碰** `panelStore`、选项数据结构、事件处理与请求体。
> 搜索结果列表仍为纯文本——naive-ui 的 `CascaderSelectMenu` 会把选项裁成
> `{value, label}` 且不提供任何渲染钩子，无法加图标；这与目标站行为一致。

## 2026-10-03 · 音擎选择器改为 naive-ui `n-cascader`（对齐 zzzcaculator.top）

### 变更

| 变更 | 说明 |
| --- | --- |
| **音擎模块只余一个控件** | 等级与类别两个下拉全部撤销，合并为一个可搜索（`filterable`）、可清除（`clearable`）的 `n-cascader`。占位文案「选择音擎」 |
| **引入 naive-ui 2** | 首个 UI 框架依赖。主题经 `App.vue` 的 `n-config-provider` 注入，`composables/useNaiveTheme.ts` 从 `tokens.css` 的 CSS 变量读主色/圆角/字体后转 `themeOverrides`，不另抄 hex |
| **等级不再是筛选轴，改写进文案** | 选项与卡片文案为 `名称 / 职业 / 等级`（如 `云霓孤光 / 强攻 / S级`）。一级分组即职业标签，组序固定为 `WEAPON_ROLE_TAGS` |
| **选中后展示头像卡片** | 头像按 `/images/weapons/{id}.png` 取自 `public/`，含名称与 `职业 / 等级`；缺图时隐藏图片而非显示破图 |
| **删除 `GroupedSelectField` 与相关 store API** | `components/common/GroupedSelectField.vue`、`types/panel.ts` 的 `SelectOptionGroup`、`panelStore` 的 `weaponGradeOptions` / `selectWeaponGrade` / `filteredWeaponPresets` / `GRADE_ORDER` 均移除，无替代 API |
| `selectWeaponPreset` 改为**双向同步** `roleTag` 与 `grade` | UI 不再单列这两个维度，但卡片要显示「职业 / 等级」，故保留；未命中预设（含点清除）时两者一并清空，不留 `roleTag` 有值而 `preset` 为空的矛盾态 |
| 预留「角色推荐」接缝 | `recommendationBadge(weaponId)` 恒返回 `undefined`；推荐关系数据来自另一份尚未落地的预设 JSON。落地后只改这一个函数 |

> ⚠️ 计算语义、请求体结构与后端**均未改动**。等级从不进入请求体
> （`usePanelCalc` 只发 `baseKind` / `baseValue` / `substat`），故去等级轴不触碰接口契约。

## 2026-10-03 · 音擎选择器改为「等级 + 职业标签分组」

### 变更

| 变更 | 说明 |
| --- | --- |
| **删除「类别」下拉** | 音擎模块由三个下拉减为两个。`panelStore` 的 `weaponRoleOptions` getter 与 `selectWeaponRole` action 一并移除，无替代 API |
| **音擎名称按职业标签分组** | 名称下拉内部改用 `<optgroup>`（新组件 `components/common/GroupedSelectField.vue`），组序固定为 `WEAPON_ROLE_TAGS`：强攻 / 击破 / 异常 / 支援 / 防护 / 命破 / 锋御。等级仍是唯一的筛选轴 |
| 分组不显示等级后缀 | 选项文案为纯音擎名称。等级已是外层筛选，组内选项同级，后缀是冗余 |
| `filteredWeaponPresets` 只按等级过滤 | 不再需要 `weapon.roleTag` 才有结果；未选等级时返回空数组 |
| `selectWeaponPreset` 反向同步 `weapon.roleTag` | 该字段无外部消费方，保留供展示与断言「切等级清空类别」 |

> ⚠️ 计算语义、请求体结构与后端**均未改动**。`frontend/tests/fixtures/legacy-calculator/`
> 保持冻结的三级参考实现不动，对拍改为按**音擎 id** 比对两侧输入等价性
> （legacy 走「S 级 + 强攻 → 首个选项」，Vue 侧按 `roleTag` 显式定位）。

## 2026-10-03 · Vue3 迁移收尾（第 5 步）

### 删除

| 变更 | 说明 |
| --- | --- |
| **删除「标准版示例」页** | 原 `/example` 路由与其视图整体移除。该页复制了一整套计算逻辑与预设值，与统一计算器完全重复。启动页入口卡片、路由、`ResultPanel` 中仅供它使用的插槽一并删除 |
| **删除 `frontend/legacy/`** | 迁移前的原生 HTML 实现。`index.html`、`guide.html`、`example-template.html`、`redirect-*.html` 均已分别被 Vue3 页面或路由 query 取代 |
| **删除仓库根目录 6 个中文重定向页** | 纯 `meta refresh` 兼容桩，现直接访问 `/` |

> ⚠️ **`data/agent-presets.js` 与 `data/weapon-presets.js` 仍然保留**，
> 但已移到 `frontend/tests/fixtures/legacy-calculator/data/`，
> 身份从「legacy 页面的数据」变为「只读对拍夹具」。删掉它三方对拍就跑不起来。

### 保留护栏

| 变更 | 说明 |
| --- | --- |
| 计算部分改为只读夹具 | 用 `git mv` 把对拍真正需要的 6 个文件移到 `frontend/tests/fixtures/legacy-calculator/`，保留 `pages/ data/ scripts/ styles/` 结构。新增该目录的 README 写明「禁止修改」 |
| 5 处消费者改路径 | `legacy-parity.spec.ts`、两个诊断脚本、`sync_presets.py`、`refresh_agent_presets.py` 的 `--config` 默认值 |
| **修掉一处假绿灯** | `test_fmt_parity.py` 原在 Node 退出码非 0 时 `pytest.skip`。基准文件缺失会命中这条路径——测试不报错但检查已失效。现改为只有 Node 不可用才 skip |

### 新增

- `/guide` 学习指南页（吸收旧 `guide.html` 全文），配套 4 个展示组件
- `docs/completeds/` 归档目录

### 文档

`docs/` 从 7 篇扩为 9 篇 + 2 篇归档。新增需求说明、接口文档、开发指南、
测试策略、部署指南、变更记录；修正 `data-schema.md` 中与实现不符的接口章节。

## 2026-10-03 · 预设数据改造为 JSON（第 4 步）

| 变更 | 说明 |
| --- | --- |
| 预设改走 `GET /api/presets/*` | 前端不再持有 160 条预设副本，构建产物从 182.90 kB 降到 128.97 kB |
| 新增 `data/agent-presets.json`（60 条）<br>`data/weapon-presets.json`（100 条） | 由 Skill 抓取脚本生成，是唯一真实源 |
| 配装规则表改为 `data/options.json` | 由 `core/options.py` 单向生成。前端经 `@data` 别名直接 import，下拉框无需等 HTTP |
| **选项从数组下标改为稳定 id** | 预存在后端、选项表在前端，两者不再需要共享同一份数组顺序 |
| 新增 `tools/sync_presets.py` | `--from-legacy` / `--to-legacy` / `--options` / `--check` 四模式，往返字节一致 |
| 后端新增 `presets/` | `loader.py` 按 mtime 缓存；`validate.py` 全量语义校验，失败整份拒绝 |
| 前端删除 `src/data/*.ts` | 数据不再有前端副本 |

> 预设走接口、规则表走本地是**故意不对称**：前者数据量大且需刷新，
> 后者要瞬时可用。理由与论证见 [architecture.md](architecture.md)。

## 2026-10-02 · 计算下沉到 Python（第 3 步）

**这是本项目唯一一次会改变数值正确性的变更。**

| 变更 | 说明 |
| --- | --- |
| 计算全部移到 `backend/src/zzz_panel/core/` | 前端不再做任何算术，只传「选了什么」 |
| 新增 `POST /api/panel/calc` | 请求只含选择项，响应含 12 行 `totals` 与结构化 `breakdown` |
| 明细改为结构化片段 | 后端不输出中文文案，格式化与换行留在前端 |
| 新增 `services/panel_service.py` | 网页与命令行共用同一份规则 |
| 新增三方对拍 | 旧 JS ≡ Vue3 页面 ≡ Python 后端，逐字符比对 |

## 2026-10-02 · 前端搭建（第 0～2 步）

- 第 0 步：Vite + Vue3 + TS 工程骨架，业务逻辑仍在前端计算
- 第 1 步：静态结构（无计算），`?mode=` 提升为路由 query，命破/锋御从独立页合为统一计算器
- 第 2 步：交互逻辑迁移到 Pinia store 与 composable

## 后续计划

见 [requirements.md](requirements.md) 第 7 节「已知限制」——
那里列出的死代码与不一致项都是可清理的重构候选。

## 相关文档

- [requirements.md](requirements.md) —— 项目范围与已知限制
- [architecture.md](architecture.md) —— 架构与设计决策
- [completeds/migration-vue3.md](completeds/migration-vue3.md) —— 迁移全过程记录