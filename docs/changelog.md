# 变更记录

记录影响使用方式或正确性的变更。纯内部重构不逐条记录，见
[git 历史](https://github.com)。

版本号见 `pyproject.toml` 与 `frontend/package.json`，当前均为 `0.1.0`。

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