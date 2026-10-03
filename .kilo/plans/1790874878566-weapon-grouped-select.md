# 音擎选择器改为「等级 + 职业标签分组单选」

## 背景与已核实事实

目标交互来自 `https://zzzcaculator.top/`：单个音擎控件，选项按职业标签二级分组，等级不再作为筛选轴。

对方站点已验证（`https://zzzcaculator.top/static/app/catalog-BffhORPx.js`）：

- 音擎字段：`id`、`name.zhCN`、`rarity`(S/A/B)、`specialty`(职业标签)、`attribute`、`baseATK`/`baseDefense`
- 标签构造函数 `Ar(r) = "<specialty> / <rarity>"`，即对方把等级写进文字而非作为筛选轴
- WorkbenchView 该选择器为 `placeholder:"选择音擎"` + `filterable` + `clearable` + `renderLabel`，并出现 `children:` —— 与单控件二级分组一致

本项目现状（已读源码确认）：

- `frontend/src/components/calculator/WeaponModule.vue:36-58` 三个 `SelectField`：`weapon_grade` / `weapon_role` / `weapon_preset`
- `frontend/src/components/common/SelectField.vue:42` 是原生 `<select>` + 扁平 `SelectOption[]`，第 43 行渲染空白占位 `<option>`
- `frontend/src/stores/panelStore.ts:113-145` 三级联动 getters；`:161-173` `selectWeaponGrade` / `selectWeaponRole`
- `weapon.grade` 与 `weapon.roleTag` **无外部消费方**：只有 `frontend/src/composables/usePanelCalc.ts:88` 读 `weapon.preset`；`frontend/src/composables/useAgentPreset.ts:196` 调 `resetWeaponSelection()`
- `frontend/src/assets/styles/base.css:93-99` `.weapon-grid` 为 `repeat(3, minmax(0,1fr))`

`data/weapon-presets.json` 实测（100 条）：等级 S 47 / A 37 / B 16；roleTag 强攻 25、异常 19、击破 19、支援 13、防护 11、命破 9、锋御 4。7 个 roleTag 在三个等级下**均存在**，交叉覆盖完整。

**已确认决策：保留等级筛选**，删除「类别」下拉，音擎名称改为原生 `<select>` + `<optgroup>` 按 roleTag 分组。控件从 3 个变 2 个。

## 有序任务清单

1. **`frontend/src/types/panel.ts`**（在 `SelectOption`（第 217 行）旁）新增：
   ```ts
   /** 分组下拉的一组。 */
   export interface SelectOptionGroup {
     label: string;
     options: SelectOption[];
   }
   ```

2. **`frontend/src/constants/calculatorOptions.ts`**：在 `AGENT_ROLE_TAGS`（第 120 行）旁新增 `WEAPON_ROLE_TAGS`，同 7 值 `['强攻','击破','异常','支援','防护','命破','锋御'] as const`。注释写明「与 `AGENT_ROLE_TAGS` 当前取值一致，但语义独立，故不复用」。

3. **新建 `frontend/src/components/common/GroupedSelectField.vue`**：原生 `<select>` + `<optgroup>`。
   - 契约对齐 `SelectField.vue`：props `name` / `label` / `labelUnit` / `modelValue` / `placeholder`(默认 `请选择`) / `disabled` / `hidden`；emit `update:modelValue: [value: string]`
   - 首个 `<option value="">{{ placeholder }}</option>`，随后 `v-for` 渲染 `<optgroup :label="group.label">` 包裹 `v-for` 的 `<option>`
   - 根节点 `<div class="field" :hidden="hidden">`，`<label :for="name">` 结构照抄 `SelectField.vue:40-41`
   - 复用 `SelectField.vue:34-36` 的 `onChange` 实现

4. **`frontend/src/components/common/index.ts`**：追加 `export { default as GroupedSelectField } from './GroupedSelectField.vue';`

5. **`frontend/src/stores/panelStore.ts`**：
   - 删除 `weaponRoleOptions` getter（`:120-133`）——无调用方
   - 删除 `selectWeaponRole` action（`:169-173`）——UI 不再暴露该步骤
   - `filteredWeaponPresets`（`:136-145`）改为**只按 `grade` 过滤**（去掉 `roleTag` 条件与提前返回）
   - 新增 `weaponPresetGroups` getter：按 `WEAPON_ROLE_TAGS` 顺序分组，**组内保持 `data/weapon-presets.json` 原序**，选项 `label` 用 `weapon.name`；`grade` 为空时返回 `[]`
   - `selectWeaponPreset`（`:190-203`）内补 `this.weapon.roleTag = weapon.roleTag;`
   - `selectWeaponGrade`（`:161-166`）、`resetWeaponSelection`（`:206-211`）保持现有清空逻辑不动
   - 更新文件顶部与各处的「三级联动」注释为两级

6. **`frontend/src/components/calculator/WeaponModule.vue`**：
   - 保留等级 `SelectField`（`id="weapon_grade"`，文案 `${grade}级` 逻辑不变）
   - 删除类别 `SelectField`（`id="weapon_role"`）与 `roleOptions` computed（`:24-26`）
   - 音擎名称换成 `GroupedSelectField`（`id="weapon_preset"`），`:groups="panel.weaponPresetGroups"`，`:disabled="!panel.weapon.grade"`，仍走 `@update:model-value="panel.selectWeaponPreset($event, localize)"`
   - 两个 select 各加 `class="span-3"`，三个只读回填字段各加 `class="span-2"`
   - 改写文件头注释

7. **`frontend/src/assets/styles/base.css`**：
   - `.weapon-grid`（`:93-99`）从 3 轨改为 6 轨：`grid-template-columns: repeat(6, minmax(0, 1fr))`，并新增 `.weapon-grid .span-3 { grid-column: span 3 }`、`.weapon-grid .span-2 { grid-column: span 2 }`
   - `@media (width <= 560px)` 内（`:115-120`）`.weapon-grid` 改回 `repeat(2, minmax(0, 1fr))`，两个 span 类改 `grid-column: span 1`
   - 依赖 Vue 3 class fallthrough；已核对 4 个 common 组件根节点均为单个 `.field`（`NumberField.vue:31`、`TextField.vue:22`、`SelectField.vue:40`、`StepperInput.vue:32`）

8. **测试与文档更新**：
   - `frontend/tests/panel-interactions.spec.ts:53-124` — `describe('音擎三级联动')` 重写为 `音擎等级与分组联动`：未选等级时名称禁用；选等级后名称解锁且 `optgroup` 数量为 7；切换等级清空 `preset`/`roleTag` 与只读回填区；选中后回填基础值与固定副词条；锋御 `baseKind=def` 回填基础防御力。移除全部 `selectWeaponRole` / `weapon_role` 断言
   - `frontend/tests/calculator-view.spec.ts:107-111` — 去掉 `#weapon_role`，改为断言「等级 + 音擎名称」两个下拉（名称初始 disabled）+ 三个只读字段齐备；可加 `#weapon_preset optgroup` 数量断言
   - `frontend/tests/legacy-parity.spec.ts:245-247` — 删除 `panel.selectWeaponRole('强攻')`。依赖「`data/weapon-presets.json` 第一条即 S + 强攻」，使 `filteredWeaponPresets[0]` 与 legacy 侧 `weapon_grade=S级` + `weapon_role=强攻` 的首个选项指向同一条；**实现时必须显式断言这一等价性**，否则改为按 roleTag 显式查找
   - `frontend/tests/README.md:20` 与 `docs/testing.md:104` — 「音擎三级联动」改为「音擎等级 + 职业标签分组」；同行用例计数按重写后实际数量更新
   - `docs/completeds/migration-vue3.md:107` 是已归档的历史记录，**不修改**

9. **`frontend/tests/fixtures/legacy-calculator/` 保持不动** —— 冻结的三级参考实现，仅用于数值对拍，不随 UI 改造同步。

## 关键决策与取舍

- **选项 label 用纯 `weapon.name`，不加等级后缀。** 等级已是外层筛选，组内选项同级，后缀是纯冗余（对方站点需要它，是因为对方没有等级筛选）。若要完全对齐对方视觉，只需改 `weaponPresetGroups` 一行。
- **分组顺序必须固定为 `WEAPON_ROLE_TAGS`，不能用首次出现顺序。** 按 grade 过滤后首次出现顺序会变：S 级为 强攻/异常/支援/击破/防护/命破/锋御，A 级为 击破/防护/异常/强攻/支援/命破/锋御，B 级为 支援/强攻/击破/防护/异常/命破/锋御 —— 会导致切换等级时分组跳序。
- **保留 `weapon.roleTag` 状态，由 `selectWeaponPreset` 反向同步。** 它无外部消费方，保留可让「切等级清空类别」等断言继续成立，也便于后续在 UI 显示。
- **用原生 `<select>`/`<optgroup>` 而非自绘二级菜单**：零新依赖、键盘与移动端原生可用；对方站点的 `filterable` 需要自研搜索，本次不做。
- **`<optgroup>` 不支持组级 `disabled`**（部分浏览器），本方案不需要组级禁用，不受影响。

## 风险

- `frontend/tests/legacy-parity.spec.ts` 的音擎等价性依赖数据顺序，是本次最脆弱的一处；必须写成断言而非注释。
- `frontend/tests/README.md:20` 与 `docs/testing.md:104` 的用例计数需与重写后实际数量一致。

## 验证

- 仓库既有 lint / typecheck 命令（`frontend/package.json` scripts）
- `npm test`（`frontend/`），重点 `panel-interactions.spec.ts`、`calculator-view.spec.ts`、`legacy-parity.spec.ts`
- 后端与 API 无改动，`backend/` 测试预期不受影响
- 手工：dev 环境 `http://localhost:5173/calculator` → 选 `S级` → 名称下拉出现 7 个 `optgroup` 且顺序为 强攻/击破/异常/支援/防护/命破/锋御 → 选任一项 → 三个只读字段回填 → 切到 `A级` → 名称清空、只读区复位、仍是 7 组
