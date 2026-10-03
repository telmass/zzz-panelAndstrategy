# 音擎选择器完整对齐目标站（cascader + 搜索 + 清除 + 头像卡片）

## 背景

上一轮把音擎选择器从三级联动改成了「等级 + `<optgroup>` 分组」。功能到位，但用户手动验收后确认**与目标站 `https://zzzcaculator.top/` 的音擎选择 UI 不相似**——原生 `<select>` 交给系统渲染，无法还原目标站那套浮层交互。

本轮把交互与展示补齐到目标站形态。

## 目标站已核实事实（来自用户提供的 DOM）

| 维度 | 目标站 | 证据 |
| --- | --- | --- |
| 控件 | Naive UI **`n-cascader`**（非 select） | `class="n-cascader" aria-label="选择音擎"` |
| 外层类名 | `w-engine-select w-engine-select--rich workbench-entity-select` | — |
| 选中态文案 | `云霓孤光 / 强攻 / S级 / 角色推荐` | `.n-base-selection-overlay__wrapper` 的文本，同时进 `title` |
| 选中后富展示 | `.w-engine-select-display`：`aria-hidden="true"`，28px 头像 `<img src="/assets/w-engines/zzz_wiki_1751.png" loading="lazy">` + `.w-engine-select-name`（名称）+ `.w-engine-select-meta`（`强攻 / S级`） | — |
| 清除 | `n-base-clear`（× 按钮，与箭头同容器） | — |
| 无等级筛选 | 等级写进选项文案，不存在独立等级控件 | — |
| 同段另有字段 | `等级`（`n-input-number`，值 60）与 `精修`（`n-select`，`1 精`） | `data-layout-surface="w-engine-fields"` |

`云霓孤光` = 本项目 `data/weapon-presets.json` 的 **`ep-1751`**（S / 强攻），且 `frontend/public/images/weapons/ep-1751.png` 已存在，**头像不构成素材阻塞**。

## 已确认决策（用户逐项确认）

1. **范围**：完整对齐 —— cascader 浮层 + 下拉内搜索 + 清除按钮 + 选中后头像卡片 + 选项文案对齐。
2. **实现**：引入 **`naive-ui`**，不手写浮层。
3. **等级轴**：**去掉**「等级」下拉，等级写入选项文案。面板只剩一个控件。
4. **精修**：**本轮不做**，等拿到权威倍率表再单独立项。
5. **角色推荐**：由**另一份预设 JSON** 提供，本轮**只留出位置**。
6. **只读回填字段**：**保留**三个（基础攻击/防御力、固定副词条属性、固定副词条数值），另**加**头像卡片。

### 明确不做（范围外）

- **精修**及其倍率表 —— 无权威数据源，猜错会静默算错面板。
- **代理人等级字段**（目标站 `等级=60`）—— 本项目代理人预设全部按 60 级烘焙（`docs/requirements.md` F3），无此维度。
- **60 张代理人头像 PNG** 的接入 —— 本轮只接音擎头像；`public/images/agents/` 仍无引用，相关「已知冗余」文档条目改写时须**只对 weapons 目录销账**，不得整条删除。

## 已核实的现有代码事实

- `frontend/src/stores/panelStore.ts:115` `weaponGradeOptions`、`:163` `selectWeaponGrade`、`:124-129` `filteredWeaponPresets`（按 grade 过滤）—— 去等级轴后全部失去调用方。
- `frontend/src/composables/usePanelCalc.ts:113-117` 请求体只用 `weapon.baseKind/baseValue/substat`，**从不读 `weapon.grade`** → 去等级轴**不触碰后端与请求契约**。
- `frontend/public/images/weapons/` 100 张 `ep-*.png`，文件名 = `data/weapon-presets.json` 的 `id`；`public/` 原样拷贝到 `dist/` 根 → 运行时 URL 为 `/images/weapons/{id}.png`。
- `frontend/tools/dump_legacy_cases.mjs:129`、`frontend/tools/diff_breakdown.mjs:118` 引用 `weapon_grade`/`weapon_role`，但二者**只驱动 legacy 夹具**（读 `tests/fixtures/legacy-calculator/`），不碰 Vue 侧 → **无需改动**。
- `frontend/tests/support/setup.ts` 目前只有 `RouterLinkStub`，**无任何浏览器 API 桩**。
- `frontend/src/App.vue` 只有 `<router-view />`，无全局 provider。
- 音擎 PNG 冗余被记在三处：`docs/requirements.md:112`、`docs/directory-layout.md:25,67-69`、`frontend/src/README.md:51`。

## 有序任务清单

1. **【前置·阻断性】安装 naive-ui 并补测试环境桩**
   - `npm i naive-ui`（不引图标包：清除/箭头由 naive 自带 CSS 绘制）。
   - `frontend/tests/support/setup.ts` 增加 `window.matchMedia`、`ResizeObserver`、`IntersectionObserver`、`DOMRect` 桩。jsdom 不实现这些，naive 的浮层定位与自适应会直接抛错。**先做这步并跑一次 `npm test` 确认未破坏既有用例**，否则后续会追幻影失败。

2. **主题接入**：`frontend/src/App.vue` 用 `n-config-provider` 包住 `<router-view />`，`theme-overrides` 把 `common.primaryColor` / `primaryColorHover` / `primaryColorPressed` 映射到 `--color-accent`( `#6366f1` ) 系列，`borderRadius` → `--radius-md`，`fontFamily` → `--font-sans`。理由：不覆盖会出现靛蓝页面 + Naive 蓝控件的双色割裂。

3. **类型**（`frontend/src/types/panel.ts` / `weaponPresets.ts`）
   - 新增 cascader 选项类型：`{ label: string; value: string; children?: WeaponCascaderOption[] }`。
   - 删除 `SelectOptionGroup`（随 `GroupedSelectField` 一起下线）。

4. **`frontend/src/stores/panelStore.ts`**
   - 删 `weaponGradeOptions`、`selectWeaponGrade`、`filteredWeaponPresets`。
   - `weaponPresetGroups` 改为对**全量**音擎按 `WEAPON_ROLE_TAGS` 分组（组序仍固定，过滤空组），选项 `label` 走新的文案构造函数。
   - 新增文案构造函数与**推荐标记接缝**（这是用户要求的「留出位置」）：
     ```ts
     /** 音擎选项文案：`名称 / 职业 / 等级`。末尾预留「角色推荐」标记位。 */
     function weaponOptionLabel(weapon: WeaponPreset, badge?: string): string {
       return [weapon.name, weapon.roleTag, `${weapon.grade}级`, badge].filter(Boolean).join(' / ');
     }

     /**
      * 「角色推荐」标记的数据源。推荐关系由**另一份预设 JSON** 提供（尚未落地），
      * 当前恒为 undefined，故文案不追加该段。JSON 到位后只改这一个函数。
      */
     function recommendationBadge(_weaponId: string): string | undefined {
       return undefined;
     }
     ```
   - 新增 `selectedWeapon` getter（由 `weapon.preset` 查 `presetStore.weaponById`），供卡片渲染，避免组件里重复查表。
   - `selectWeaponPreset` **继续反向同步** `weapon.roleTag`，并**新增同步 `weapon.grade`**（卡片要显示 `强攻 / S级`）；未命中预设时两者一并清空。`resetWeaponSelection` 保持清空逻辑。

5. **`frontend/src/components/calculator/WeaponModule.vue` 重写**
   - 单个 `n-cascader`：`options="panel.weaponPresetGroups"`、`filterable`、`clearable`、`placeholder="选择音擎"`、`value`/`on-update:value` 走 `selectWeaponPreset`、`:render-label` 用 `weaponOptionLabel`。
   - 选中后渲染卡片：`<img :src="'/images/weapons/' + id + '.png'" loading="lazy" :alt="name">` + 名称 + `职业 / 等级`，带 `@error` 兜底（数据增长后缺图不显示破图）。**未选中时卡片不渲染**。
   - 保留三个只读回填字段。清除按钮（`clearable` 选中占位项）须走通「preset/roleTag/grade 清空 + 只读区复位」。

6. **下线 `GroupedSelectField`**
   - 删除 `frontend/src/components/common/GroupedSelectField.vue` 与 `components/common/index.ts` 中的导出。

7. **样式**
   - `base.css`：`.weapon-grid` 回到 3 轨；**移除** `.span-3` / `.span-2` 及其 560px 断点覆盖（唯一控件独占整行，卡片整行，三个只读字段一行三列）。
   - `components.css`：新增音擎卡片样式（头像 28px 圆形、`--radius-md`、名称/副信息两行），颜色一律走 token。
   - 为 cascader 触发框与浮层补少量覆盖，使其高度/圆角与项目其它输入框一致。

8. **测试**（`vue-tsc` + `npm test` 必须全绿）
   - `calculator-view.spec.ts`：删 `#weapon_grade` 相关断言与那条「单根 `.field` + `span-3` + `label[for]`」结构契约用例（naive 自带 DOM，该契约已不适用）；改为断言无 `#weapon_grade`/`#weapon_role`、cascader 存在、选中后才出现卡片。
   - `panel-interactions.spec.ts`：删全部 `selectWeaponGrade` 调用与「切等级清空下游」类用例（该轴已不存在）；改为「未选时禁用/空态」「100 条音擎按 7 组分组且组序固定」「选中回填 + 同步 roleTag/grade」「清除后全清」「锋御 `baseKind=def`」。
   - `legacy-parity.spec.ts`：`applyFullBuildVue` 去掉 `selectWeaponGrade('S')`，改为直接按 `grade==='S' && roleTag==='强攻'` 取第一条；**保留两侧音擎 id 相等的断言**（这是对拍等价性的唯一保证）。
   - 新增一条 cascader 交互用例：展开 → 7 个一级项 → 选中 → 卡片出现。依赖任务 1 的桩。
   - 任何「切等级」类断言若仍存在即视为漏改。

9. **文档**
   - `docs/changelog.md` 新增条目：去等级轴、引入 naive-ui、接头像、推荐位预留。
   - `docs/requirements.md:112`、`docs/directory-layout.md:25,67-69`、`frontend/src/README.md:51`：「160 张 PNG 无引用」**改为只对 `agents/` 保留**，`weapons/` 已接入。
   - `docs/directory-layout.md:37`、`frontend/src/README.md:13`：组件清单去掉 `GroupedSelectField`。
   - 依赖清单补 naive-ui（`docs/architecture.md` 与 `frontend/src/README.md` 的技术栈处）。
   - 四处测试计数（`README.md`、`docs/development.md`、`docs/testing.md` 两处、`frontend/tests/README.md` 两处）按重写后的真实数量更新。

## 关键风险

1. **jsdom 缺浏览器 API（最高风险）** —— naive 的浮层依赖 `matchMedia` / `ResizeObserver`。任务 1 未先落地就会看到大量与业务无关的报错，排查成本高。必须在动组件前先跑通一次既有测试。
2. **测试 DOM 契约失效** —— 现有 4 条用例依赖 `.field` 根节点与 `label[for]` 关联，naive 渲染自己的 DOM。必须逐条重写而非删了事，否则覆盖率静默下降。
3. **`noUnusedLocals`** —— `tsconfig` 开了该选项，删 getter/action 后若有残留引用会直接编译失败；反之删干净才不会留死代码。
4. **双色割裂** —— 不做任务 2 的主题映射，靛蓝页面里会出现蓝色控件。
5. **推荐接缝被判为死代码** —— `recommendationBadge()` 当前恒返回 `undefined`。这是用户明确要求的预留位，必须在函数注释里写明「JSON 落地后只改此处」，否则后续清理会把它当死代码删掉。

## 验证

- `npm run typecheck`（`vue-tsc --noEmit`）通过。
- `npm test` 全绿，重点 `panel-interactions.spec.ts`、`calculator-view.spec.ts`、`legacy-parity.spec.ts`。
- `npm run build` 成功，并确认 `dist/images/weapons/` 随产物落地（`public/` 原样拷贝）。
- **变异验证**：临时让 `weaponPresetGroups` 忽略 roleTag 分组，确认新分组用例会变红，再还原。
- 手工（dev 环境 `http://localhost:5173/calculator`）：
  1. 音擎模块只有一个控件，无等级/类别下拉
  2. 展开后左侧 7 个职业标签，选中后右侧二级列表，条目文案形如 `云霓孤光 / 强攻 / S级`
  3. 输入框可过滤
  4. 选中后卡片出现：头像 + 名称 + `强攻 / S级`
  5. 点 × 清除 → 卡片消失、三个只读字段复位、结果面板回到无音擎数值
  6. 窄屏（≤560px）下布局不溢出
- 后端与 API 无改动，`backend/` 87 项测试预期不受影响（仍需跑一次确认）。