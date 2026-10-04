# 代理人选择复现音擎的 cascader 选择器

## 目标

把代理人选择的两个原生 `<select>`（`agent_role` + `agent_preset`）换成与音擎**完全同构**的
单个 `n-cascader`：同样的交互方式、筛选条件、排序规则与界面表现，并尽量复用音擎已有的代码结构。

## 已核实的事实（勿重复调查）

| 事实 | 依据 |
| --- | --- |
| 参考实现 | `WeaponModule.vue`（186 行），单 `n-cascader` + `render-prefix` + `render-label` + 头像卡片 |
| 代理人现状 | `AgentBaseModule.vue:64-82`，`.agent-selector-grid` 内两个 `SelectField` |
| **数据没有属性/特性/阵营/稀有度字段** | `data/agent-presets.json` 每条仅 `id/name/roleTag/panelMode/source/base/coreBonuses`(+3 可选)。grep `grade\|rarity\|attribute\|faction\|element` **零命中** |
| `grade` 是残留字段 | `backend/src/zzz_panel/schemas/presets.py:90` 有 `grade: Optional[str]`，但**无任何数据填它** |
| 60 个代理人，7 类 roleTag 全覆盖 | `data/agent-presets.json` |
| `命破↔rupture`、`锋御↔fengyu` 一一对应，其余恒 `standard` | 同上 |
| `锋御` 只有 1 个代理人 | 同上 → 故不做三级，避免只有 1 个子项的退化分组 |
| 改选项文案**不破坏**三方对拍 | `legacy-parity.spec.ts:172` 的 `vueVisibleLabels` 只读 `.r-row` 结果行；`selectLegacyByLabel` 只操作 legacy DOM |
| `LauncherView` 无代理人选择 | 全文无 agent 相关代码 |
| `SelectField` 不能删 | 仍被 `CoreModule.vue` 与 `DiscMainModule.vue` 使用 |
| `agent_role`/`agent_preset` 的 Vue 侧只被 2 条用例引用 | `panel-interactions.spec.ts:360,370`；`legacy-parity` 引用的是 legacy DOM 的同名 id |
| 两条过时提示文案无测试断言 | `请先选择代理人标签…` / `已筛选"X"标签…` 仅见于 `panelStore.ts:251`、`useAgentPreset.ts:205` 与 legacy 夹具 |
| naive-ui 渲染契约 | 折叠框读 `rawNode.label`（`Cascader.mjs:402`），**不经过** `render-label`；`filterable` 搜索结果由 `CascaderSelectMenu` 渲染，也不经过 `render-label` |

## 已锁定决策

1. **仅 roleTag 两级**：`roleTag → 代理人`。`panelMode` 不单独成轴，写进叶子文案——
   与音擎把「等级」写进文案的做法一致。
2. **保留 `selectAgentRole` 与 `applyAgentPreset` 不动**，cascader 只做展示层接线。
   这样 `legacy-parity.spec.ts` 与既有用例无需改写。
3. **保留 `render-label` 的完整文案契约**：浏览时只显示名称，选中后折叠框仍是完整文案。
4. **复用方式**：抽出 `useCascaderIcons.ts` 承载两个渲染器，音擎改为调用它，
   代理人也调用它——两者渲染逻辑由构造保证一致，而非靠人工同步。

## 与音擎逻辑的差异（实现后需在说明中点出）

| 维度 | 音擎 | 代理人 | 原因 |
| --- | --- | --- | --- |
| 叶子第三段文案 | `S级`（`grade`） | `通用`/`命破`/`锋御`（`panelMode`） | 代理人无等级字段 |
| 去重 | 不需要 | **需要** | 命破/锋御代理人的 `roleTag` 与模式名同字，不去重会得到「仪玄 / 命破 / 命破」 |
| 选中副作用 | `selectWeaponPreset` 一次写全 | `selectAgentRole` + `applyAgentPreset` **串联** | 代理人的载入逻辑（校验、核心加成、二件套清空）在 composable 里，不在 store |
| 文案格式 | `名称 / 职业 / 等级` | `名称 / 职业 / 模式` | 原为 `名称（职业 / 模式）`，为对齐音擎改为 ` / ` 分隔 |

---

## 步骤

### 步骤 1 · 新建 `frontend/src/composables/useCascaderIcons.ts`

承载两个模块共用的 roletag 图标映射与 `render-prefix` / `render-label`。
**音擎现有的 90 行图标代码整体搬到这里**，函数签名不变。

```ts
import { h, type VNodeChild } from 'vue';
import type { CascaderOption } from 'naive-ui';

import { AGENT_ROLE_TAGS, WEAPON_ROLE_TAGS } from '@/constants/calculatorOptions';

export type RoleTag =
  | (typeof AGENT_ROLE_TAGS)[number]
  | (typeof WEAPON_ROLE_TAGS)[number];

const ROLE_ICON: Record<RoleTag, string> = {
  强攻: 'strike',
  击破: 'pierce',
  异常: 'abnormal',
  支援: 'support',
  防护: 'guard',
  命破: 'rupture',
  锋御: 'armero',
};

function optionValue(option: CascaderOption): string {
  return typeof option.value === 'string' ? option.value : '';
}

export interface CascaderRendererOptions {
  /** 二级（叶子）图标目录，如 `/images/weapons`。 */
  leafIconDir: string;
  /** 二级选项名称解析，用于浏览时只显示名称；返回 undefined 时退回 label。 */
  leafName: (id: string) => string | undefined;
}

function optionIconSrc(option: CascaderOption, leafIconDir: string): string {
  const value = optionValue(option);
  if (!value) {
    return '';
  }
  if (option.children?.length) {
    const slug = ROLE_ICON[value as RoleTag];
    return slug ? `/images/icons/${slug}.png` : '';
  }
  return `${leafIconDir}/${value}.png`;
}

export function createCascaderRenderers(options: CascaderRendererOptions): {
  renderOptionPrefix: (props: { option: CascaderOption }) => VNodeChild;
  renderOptionLabel: (option: CascaderOption) => string | undefined;
} {
  function renderOptionPrefix({ option }: { option: CascaderOption }): VNodeChild {
    const src = optionIconSrc(option, options.leafIconDir);
    if (!src) {
      return null;
    }
    return h('img', {
      class: 'cascader-option-icon',
      src,
      alt: '',
      loading: 'lazy',
      onError: (event: Event) => {
        (event.target as HTMLImageElement).style.display = 'none';
      },
    });
  }

  function renderOptionLabel(option: CascaderOption): string | undefined {
    if (option.children?.length) {
      return option.label;
    }
    return options.leafName(optionValue(option)) ?? option.label;
  }

  return { renderOptionPrefix, renderOptionLabel };
}
```

要点：
- 键类型取 `AGENT_ROLE_TAGS` 与 `WEAPON_ROLE_TAGS` 的**并集**。两张表当前取值相同
  但语义独立；取并集后任一张扩容而漏配图标，`vue-tsc` 立即报错。
- 类名从 `weapon-option-icon` 改为中性的 `cascader-option-icon`——它已不再是音擎专用。

**验证**：`npm run typecheck` 通过；删掉 `ROLE_ICON` 任一键后必须报
`TS2741: Property '…' is missing`，随后还原。

### 步骤 2 · `WeaponModule.vue` 改为调用共享 composable

删除 `ROLE_ICON`、`optionIconSrc`、`renderOptionPrefix`、`renderOptionLabel`
（约 90 行）与 `h` / `CascaderOption` / `WEAPON_ROLE_TAGS` 导入，改为：

```ts
import { computed, ref } from 'vue';
import { NCascader } from 'naive-ui';

import { createCascaderRenderers } from '@/composables/useCascaderIcons';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
import { NumberField, PanelModule, TextField } from '@/components/common';

const panel = usePanelStore();
const presets = usePresetStore();
const { localize } = usePanelMode();

const { renderOptionPrefix, renderOptionLabel } = createCascaderRenderers({
  leafIconDir: '/images/weapons',
  leafName: (id) => presets.weaponById.get(id)?.name,
});
```

**模板一字不改**（`renderOptionPrefix` / `renderOptionLabel` 变量名保持一致）。

**验证**：`npm run typecheck`；`npm test` 应仍全绿——这一步是纯重构，
任何一条用例变红都说明抽取改变了行为。

### 步骤 3 · `panelStore.ts` 新增代理人的分组与选中 getter

新增模块私有函数（与既有 `weaponOptionLabel` 同处、同风格）：

```ts
/**
 * 代理人选项文案：`名称 / 职业 / 模式`。
 *
 * 与 `weaponOptionLabel` 同构（` / ` 分隔）。去重是必须的：
 * 命破与锋御代理人的 `roleTag` 与模式名同字，
 * 不去重会得到「仪玄 / 命破 / 命破」。
 */
function agentOptionLabel(agent: AgentPreset): string {
  const tags = [...new Set([agent.roleTag, PANEL_MODE_LABELS[agent.panelMode]].filter(Boolean))];
  return [agent.name, ...tags].join(' / ');
}
```

在 `getters` 中，紧邻 `weaponPresetGroups` 新增：

```ts
/**
 * 全部代理人预设，按职业标签分组成 cascader 的两级选项。
 *
 * `panelMode` **不作为筛选轴**（与音擎的等级同理），写进叶子文案。
 * 组序取自 `AGENT_ROLE_TAGS` 而非首次出现顺序：后者随数据变化会跳序。
 * 组内保持 `data/agent-presets.json` 原序。
 */
agentPresetGroups(): AgentCascaderOption[] {
  const { agents } = usePresetStore();
  return AGENT_ROLE_TAGS.map((roleTag) => ({
    label: roleTag,
    value: roleTag,
    children: agents
      .filter((agent) => agent.roleTag === roleTag)
      .map((agent) => ({ label: agentOptionLabel(agent), value: agent.id })),
  })).filter((group) => group.children && group.children.length > 0);
},

/** 当前选中的代理人预设，供选中后的头像卡片渲染。 */
selectedAgent(): AgentPreset | null {
  return usePresetStore().agentById.get(this.agent.presetId) ?? null;
},
```

`frontend/src/types/agentPresets.ts` 追加（与 `WeaponCascaderOption` 结构一致，
各自放在本域文件内，与仓库现有约定一致）：

```ts
/**
 * 代理人 cascader 的一个选项。
 *
 * 结构与 `WeaponCascaderOption` 相同：一级项是职业标签（带 `children`），
 * 二级项是具体代理人（叶子）。`label` 是完整文案「名称 / 职业 / 模式」，
 * 因为 `filterable` 匹配的是 `label`，而折叠框显示的也是它。
 * 索引签名是 naive-ui 的 `CascaderOption` 所必需，去掉就无法传给 `n-cascader`。
 */
export interface AgentCascaderOption {
  label: string;
  /** 一级为职业标签，二级为代理人 id。 */
  value: string;
  children?: AgentCascaderOption[];
  [key: string]: unknown;
}
```

**验证**：`npm run typecheck`。另做一次穷尽性变异：把
`children: agents.filter(...)` 改成 `children: []`，确认 `filter` 后的空组被剔除
（`.filter(group => group.children.length > 0)`）。

### 步骤 4 · `AgentBaseModule.vue` 换成 cascader

- 删除 `SelectField` 导入与 `agentPresetOptions` computed。
- 新增 `cascaderValue` / `avatarSrc` / `metaText` / `avatarBroken` / `onSelect`，
  与 `WeaponModule.vue` 逐行同构，只有 `onSelect` 不同：

```ts
/**
 * 选中即确定 roletag —— 不再单独提供标签下拉。
 *
 * 与音擎的差别：音擎的 `selectWeaponPreset` 一次写全 roleTag/grade/preset，
 * 而代理人的载入逻辑（结构校验、核心加成、二件套清空、面板模式写入）
 * 在 `useAgentPreset` 里，不在 store。故这里串联两个既有 action，
 * 顺序必须是先 role 后 preset——`selectAgentRole` 会把面板模式回落到
 * `requestedMode`，`applyAgentPreset` 再写入代理人的真实模式。
 *
 * 清除（`null`）时只走 `selectAgentRole('')`：它已经清空 presetId、
 * 还原基础面板/核心/二件套、回落面板模式并重置音擎，与
 * `applyAgentPreset('')` 的效果完全一致，后者是冗余的。
 */
function onSelect(value: string | null): void {
  avatarBroken.value = false;
  const agentId = value ?? '';
  if (!agentId) {
    panel.selectAgentRole('');
    return;
  }
  const agent = presets.agentById.get(agentId);
  if (!agent) {
    // 交给既有校验给出红色提示，不静默失败
    applyAgentPreset(agentId);
    return;
  }
  panel.selectAgentRole(agent.roleTag);
  applyAgentPreset(agentId);
}
```

模板把 `:64-82` 的两个 `SelectField` 换成：

```html
<div class="agent-selector-grid" style="margin-bottom: 8px">
  <div class="field agent-picker">
    <span class="agent-picker-label">代理人</span>
    <n-cascader
      class="agent-picker-input"
      :options="panel.agentPresetGroups"
      :value="cascaderValue"
      :render-prefix="renderOptionPrefix"
      :render-label="renderOptionLabel"
      filterable
      clearable
      placeholder="选择代理人"
      @update:value="onSelect"
    />
  </div>

  <!-- 选中后展示：头像 + 名称 + 职业/模式，与音擎卡片同构 -->
  <div v-if="panel.selectedAgent" class="agent-card">
    <img
      v-if="!avatarBroken"
      class="agent-card-avatar"
      :src="avatarSrc"
      :alt="panel.selectedAgent.name"
      loading="lazy"
      @error="onAvatarError"
    />
    <span class="agent-card-copy">
      <span class="agent-card-name">{{ panel.selectedAgent.name }}</span>
      <span class="agent-card-meta">{{ metaText }}</span>
    </span>
  </div>
</div>
```

`.base-grid` 的 8 个数值字段与其余显隐逻辑**一字不动**。

### 步骤 5 · 更新两条已过时的提示文案

标签下拉没了，原文案会误导用户。**两处**都要改（`panelStore.selectAgentRole`
与 `useAgentPreset.applyAgentPreset('')`），保持一致：

- 有 roleTag 无预设：`已筛选“X”标签，请选择具体代理人载入基础面板和核心加成。`
  （删掉「确认代理人后音擎与套装选择会重置」——新交互下该状态不可达）
- 无 roleTag：`请选择代理人以载入基础面板和核心加成。`

已确认两条文案**均无测试断言**，改安全。

### 步骤 6 · 样式

`frontend/src/assets/styles/components.css`：

1. `.weapon-option-icon` 改名为 `.cascader-option-icon`（它已通用）。
2. 新增 `.agent-picker` / `.agent-card` 各占满整行：
   `.agent-picker, .agent-card { grid-column: 1 / -1; }`
3. 选择器高度与内边距对齐音擎（`height: 32px`、`padding-left: var(--space-2)`、
   `padding-right: 26px`），否则同一行的原生输入框会显得参差。
4. 卡片样式**用并列选择器复用**，不复制一份：
   把 `.weapon-card` / `-avatar` / `-copy` / `-name` / `-meta` 五条规则
   各自扩成 `.weapon-card, .agent-card` 形式。
5. ⚠️ 选项图标类名必须是**全局**的：浮层 Teleport 到 `body`，
   写成 `.weapon-picker .cascader-option-icon` 不会命中。

### 步骤 7 · 测试

`frontend/tests/panel-interactions.spec.ts`：

**重写 2 条失效用例**（`#agent_role` / `#agent_preset` 已不存在）：
- `未选标签时代理人下拉禁用` → 删除，替换为「初始无值且 cascader 不锁定」
- `选标签后解锁并按标签过滤` → 替换为「分组覆盖全部代理人、组序取自 `AGENT_ROLE_TAGS`、组内保持数据原序」

**新增用例**：
1. `agentPresetGroups` 展开后条目数 === 代理人总数（守护分组不丢数据）
2. `renderPrefix`：一级 `/images/icons/strike.png`、二级 `/images/agents/ep-xxx.png`、
   未知 roletag 与空 value 返回 `null`、`alt` 为空
3. `renderLabel`：一级得 roleTag；二级**只有名称**，不含 roleTag 与模式名；
   `option.label` 仍是完整三段（守护选中后展示）
4. 接线：cascader `$emit('update:value', id)` → `panel.agent.roleTag` 同步、
   `panel.agent.presetId` 写入、`panel.panelMode` 为该代理人的模式
5. 清除：`$emit('update:value', null)` → `roleTag`/`presetId` 清空、面板模式回落

⚠️ 断言只能走 `props('renderPrefix')` / `props('renderLabel')`，
**不能断 `.n-cascader-option` DOM**——jsdom 无布局，虚拟列表一项都不渲染。

**变异验证**（逐条确认会红）：
- `agentOptionLabel` 去掉去重 → 命破用例红（出现「命破 / 命破」）
- `renderOptionLabel` 直接 `return option.label` → 用例 3 红
- `onSelect` 漏掉 `selectAgentRole` → 用例 4 红
- `onSelect` 清除时不调 `selectAgentRole('')` → 用例 5 红

### 步骤 8 · 文档

`agents/` 的 60 张 PNG 从「无任何代码引用」变为**已接入**，
以下 4 处关于 PNG 冗余的记述必须同步，否则文档即失实：

- `frontend/public/README.md` —— `images/agents/` 行去掉「尚无代码引用」
- `docs/directory-layout.md:25` 与 `:67-73` —— 接入状态由「分两块」改为「三块全接入」
- `frontend/src/README.md:51` —— 同上
- `docs/requirements.md:112` —— 「60 张代理人 PNG 无引用」是**已知限制表**的一行，
  接入后应删除该行

另需更新：测试计数（`README.md`、`docs/development.md`、`docs/testing.md` ×3、
`frontend/tests/README.md`、`docs/directory-layout.md:118-120`）、
`docs/changelog.md` 新增条目。

### 步骤 9 · 验收

```powershell
cd frontend; npm run typecheck
cd frontend; npm test
npm run build
cd ..\backend; uv run pytest -q
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\dev.ps1 start
```

浏览器打开 `http://localhost:5173/calculator`，目视确认：
1. 代理人选择器与音擎选择器**外观一致**（同高度、同占满整行）
2. 展开后一级 7 组带 roletag 图标；点开某组，二级只显示「头像 + 名称」
3. 选中某代理人后：折叠框显示完整「名称 / 职业 / 模式」，下方卡片显示头像 + 名称 + 职业/模式
4. 基础面板 8 项数值与两个核心槽位被正确写入；命破代理人额外出现贯穿力与闪能自动累积
5. DevTools Network 过滤 `agents` 应见 200、无 404；Console 无报错
6. 点清除按钮：折叠框回到占位、卡片消失、基础面板回落默认值

## 风险

| 风险 | 处置 |
| --- | --- |
| 抽取共享 composable 时改变音擎行为 | 步骤 2 是纯重构，`npm test` 必须仍全绿，否则立即回退排查 |
| `onSelect` 里两个 action 的顺序写反 | 面板模式会停在 `requestedMode`；用例 4 断言 `panelMode` 守护 |
| 重复计算：同 roleTag 内切换也走一遍 `clearAgentPresetFields` | 结果与直接载入一致（先清后写），无可见闪烁；不做优化以保持与 legacy 同构 |
| `ROLE_ICON` 成为第三份 roletag 相关表 | 键类型取两张常量的并集 + `Record` 编译期穷尽，新增即报错 |
| 改选项文案影响三方对拍 | 已核实 `vueVisibleLabels` 只读 `.r-row`，不受影响 |

## 明确不做

- 不给代理人加 `panelMode` 第三级（`锋御` 只有 1 人，退化分组）
- 不新增稀有度/属性/阵营字段（涉及后端契约与校验规则，属另一件事）
- 不删除 `SelectField`（`CoreModule`、`DiscMainModule` 仍在用）
- 不改 `selectAgentRole` / `applyAgentPreset` 的副作用语义
- 不改 `legacy-parity.spec.ts`（其 Vue 侧走 store action，不受 UI 变更影响）
