<script setup lang="ts">
import { computed } from 'vue';

import { PANEL_MODE_LABELS } from '@/constants/calculatorOptions';
import { useAgentPreset } from '@/composables/useAgentPreset';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { NumberField, PanelModule, SelectField } from '@/components/common';

/**
 * 一、基础面板。对应 legacy 的 `.module.base`。
 *
 * 面板模式相关的显隐与锋御文案替换由 `usePanelMode` 驱动；
 * 代理人下拉的联动与预设载入由 store action 与 `useAgentPreset` 承担。
 */
const panel = usePanelStore();
const { applyAgentPreset } = useAgentPreset();
const {
  showPenetrationInput,
  showEnergyReplyInput,
  showPenforceInput,
  showEnergyAccumulationInput,
  energyInputLabel,
} = usePanelMode();

/** 代理人预设选项文案为「名字（标签 / 模式）」，与 legacy 一致。 */
const agentPresetOptions = computed(() =>
  panel.filteredAgentPresets.map((agent) => {
    const tags = [...new Set([agent.roleTag, PANEL_MODE_LABELS[agent.panelMode]].filter(Boolean))];
    return { value: agent.id, label: `${agent.name}（${tags.join(' / ')}）` };
  }),
);

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
      <SelectField
        name="agent_role"
        label="代理人标签"
        placeholder="请选择"
        :model-value="panel.agent.roleTag"
        :options="panel.agentRoleOptions.map((role) => ({ value: role, label: role }))"
        @update:model-value="panel.selectAgentRole($event)"
      />
      <SelectField
        name="agent_preset"
        label="代理人名称"
        placeholder="请先选择标签"
        :model-value="panel.agent.presetId"
        :options="agentPresetOptions"
        :disabled="!panel.agent.roleTag"
        @update:model-value="applyAgentPreset($event)"
      />
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