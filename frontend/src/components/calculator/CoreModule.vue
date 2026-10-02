<script setup lang="ts">
import { computed } from 'vue';

import { CORE_OPTIONS } from '@/constants/calculatorOptions';
import { usePanelCalc } from '@/composables/usePanelCalc';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { PanelModule, SelectField } from '@/components/common';

/**
 * 三、核心加成。对应 legacy 的 `.module.core`。
 *
 * 选项文案需按面板模式替换：锋御模式下「基础能量自动回复」显示为
 * 「基础锐能自动累积」，与 legacy 的 `updateEnergyAttributeLabels` 一致。
 * legacy 用 `option.dataset.standardLabel` 缓存原文案再覆盖，
 * 这里因为文案由 computed 派生，无需缓存，直接从常量还原。
 */
const panel = usePanelStore();
const { localize } = usePanelMode();
const { coreSummary } = usePanelCalc();

const coreOptions = computed(() =>
  CORE_OPTIONS.map((option) => ({ value: option.id, label: localize(option.label) })),
);
</script>

<template>
  <PanelModule title="三、核心加成" tag="9选2 · 可重复选" variant="core">
    <p class="note note--lead">
      从8项中选2项，可重复（如两次暴击率=28.8%）。<br />核心互斥：同一属性不会同时给基础值与百分比。
    </p>

    <div class="grid-2">
      <SelectField
        name="core1"
        label="核心选择 ①"
        :model-value="panel.core.core1"
        :options="coreOptions"
        @update:model-value="panel.core.core1 = $event"
      />
      <SelectField
        name="core2"
        label="核心选择 ②"
        :model-value="panel.core.core2"
        :options="coreOptions"
        @update:model-value="panel.core.core2 = $event"
      />
    </div>

    <!-- 与 legacy 一致：摘要以 innerHTML 写入，未选择时为红色警示 -->
    <p class="note" v-html="coreSummary" />
  </PanelModule>
</template>