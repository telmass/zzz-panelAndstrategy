<script setup lang="ts">
import { computed, ref } from 'vue';
import { NCascader } from 'naive-ui';

import { createCascaderRenderers } from '@/composables/useCascaderIcons';
import { agentTagLabel, useAgentPreset } from '@/composables/useAgentPreset';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
import { NumberField, PanelModule } from '@/components/common';

/**
 * 一、基础面板。对应 legacy 的 `.module.base`。
 *
 * 面板模式相关的显隐与锋御文案替换由 `usePanelMode` 驱动；
 * 代理人的载入由 `useAgentPreset` 承担。
 *
 * `show-path` 关掉：naive-ui 默认会把**整条路径**的 label 用 ` / ` 拼起来显示在
 * 折叠框里，而一级项正是职业标签、叶子文案里又带着同一个职业标签，于是折叠框
 * 会显示成「强攻 / 伊芙琳·舒瓦利耶 / 强攻 / 火 / S级」——职业标签重复两次。
 * 关掉后折叠框只显示叶子文案，即 `名称 / 职业 / 属性 / 评级`。
 */
const panel = usePanelStore();
const presets = usePresetStore();
const { applyAgentPreset } = useAgentPreset();
const {
  showPenetrationInput,
  showEnergyReplyInput,
  showPenforceInput,
  showEnergyAccumulationInput,
  energyInputLabel,
} = usePanelMode();

const cascaderValue = computed<string | null>(() => panel.agent.presetId || null);

/** 头像路径。`public/` 原样拷贝到 `dist/` 根，故按 URL 取而非 import。 */
const avatarSrc = computed(() =>
  panel.selectedAgent ? `/images/agents/${panel.selectedAgent.id}.png` : '',
);

/**
 * 卡片副信息：`职业 / 模式`，复用 `agentTagLabel` 与载入提示同一份拼接逻辑。
 *
 * 通用模式的中文名被 `panelModeTagLabel` 隐去，故此处只有一段；
 * 命破/锋御因角色与模式同字同样只剩一段。
 */
const metaText = computed(() => {
  const agent = panel.selectedAgent;
  return agent ? agentTagLabel(agent) : '';
});

/**
 * 头像缺失时的兜底。
 *
 * 数据增长后可能出现有预设无 PNG 的代理人，此时不能显示破图——
 * 隐藏图片会让卡片只剩文字，布局不至于塌。
 */
const avatarBroken = ref(false);

function onAvatarError(): void {
  avatarBroken.value = true;
}

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

/* ====== 选项前缀图标与文案（与音擎选择器共用，见 useCascaderIcons） ====== */

const { renderOptionPrefix, renderOptionLabel } = createCascaderRenderers({
  leafIconDir: '/images/agents',
  leafName: (id) => presets.agentById.get(id)?.name,
});

/** 基础面板的数值字段，与 legacy 的 baseFields 顺序一致。 */
const NUMERIC_FIELDS = [
  { key: 'hp', label: '生命值', unit: '' },
  { key: 'atk', label: '攻击力', unit: '' },
  { key: 'def', label: '防御力', unit: '' },
  { key: 'impact', label: '冲击力', unit: '' },
  { key: 'cr', label: '暴击率', unit: '%' },
  { key: 'cd', label: '暴击伤害', unit: '%' },
  { key: 'ac', label: '异常掌控', unit: '' },
  { key: 'am', label: '异常精通', unit: '' },
] as const;

/** 数值字段的读写桥接，保持模板中不出现下标签名。 */
function numberModel(key: (typeof NUMERIC_FIELDS)[number]['key']) {
  return computed({
    get: () => panel.base[key],
    set: (value: number | string) => {
      const parsed = Number.parseFloat(String(value));
      panel.base[key] = Number.isFinite(parsed) ? parsed : 0;
    },
  });
}
</script>

<template>
  <PanelModule title="一、基础面板" tag="角色本体" variant="base">
    <p class="note note--lead">
      填写角色纯基础面板（不含核心）。若游戏内显示已含核心基础值，请先减去再填。
    </p>

    <div class="agent-selector-grid" style="margin-bottom: 8px">
      <div class="field agent-picker">
        <span class="agent-picker-label">代理人</span>
        <n-cascader
          class="agent-picker-input"
          :options="panel.agentPresetGroups"
          :value="cascaderValue"
          :render-prefix="renderOptionPrefix"
          :render-label="renderOptionLabel"
          :show-path="false"
          filterable
          clearable
          placeholder="选择代理人"
          @update:value="onSelect"
        />
      </div>

      <!-- 选中后展示：头像 + 名称 + 职业/模式。与音擎卡片同构 -->
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

    <p class="note note--lead" :style="panel.agentNote.tone === 'error' ? 'color: #dc2626' : ''">
      {{ panel.agentNote.text }}<a
        v-if="panel.agentNote.source"
        :href="panel.agentNote.source"
        target="_blank"
        rel="noopener noreferrer"
        >米游社官方WIKI</a
      >
    </p>

    <div class="base-grid">
      <NumberField
        v-for="field in NUMERIC_FIELDS"
        :key="field.key"
        :name="`base_${field.key}`"
        :label="field.label"
        :unit="field.unit"
        :model-value="numberModel(field.key).value"
        @update:model-value="numberModel(field.key).value = $event"
      />

      <!-- 穿透率：命破模式改用贯穿力，故隐藏 -->
      <NumberField
        name="base_pr"
        label="穿透率"
        unit="%"
        :model-value="panel.base.pr"
        :hidden="!showPenetrationInput"
        @update:model-value="panel.base.pr = Number($event) || 0"
      />
      <!-- 基础贯穿力：仅命破模式显示 -->
      <NumberField
        name="base_penforce"
        label="基础贯穿力"
        :model-value="panel.base.penforce"
        :hidden="!showPenforceInput"
        @update:model-value="panel.base.penforce = Number($event) || 0"
      />
      <!-- 能量回复：命破模式隐藏，锋御模式文案改为锐能自动累积 -->
      <NumberField
        name="base_er"
        :label="energyInputLabel"
        :model-value="panel.base.er"
        :hidden="!showEnergyReplyInput"
        @update:model-value="panel.base.er = Number($event) || 0"
      />
      <!-- 闪能自动累积：仅命破模式显示 -->
      <NumberField
        name="base_energy_accumulation"
        label="闪能自动累积"
        :model-value="panel.base.energyAccumulation"
        :hidden="!showEnergyAccumulationInput"
        @update:model-value="panel.base.energyAccumulation = Number($event) || 0"
      />
    </div>
  </PanelModule>
</template>