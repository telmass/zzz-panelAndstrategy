<script setup lang="ts">
import { computed } from 'vue';

import { DISC4_OPTIONS, DISC5_OPTIONS, DISC6_OPTIONS, DISC_FIXED_STATS } from '@/constants/calculatorOptions';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { PanelModule, SelectField } from '@/components/common';

/**
 * 四、驱动盘主词条。对应 legacy 的 `.module.disc`。
 *
 * 1/2/3 号固定主词条为常量，第 3 步下沉到 `core/constants.py` 后改为后端下发。
 */
const panel = usePanelStore();
const { localize } = usePanelMode();

/** 4/5/6 号沿用 legacy 的四格不换行空格缩进，使其与上方徽标对齐。 */
const INDENT = '\u00a0\u00a0\u00a0\u00a0';

/** 6 号主词条含「能量回复 60%」，锋御模式需替换为锐能文案，故单独派生。 */
const SLOTS = computed(() => [
  { key: 'disc4' as const, label: `${INDENT}4号`, unit: '6选1', options: DISC4_OPTIONS },
  { key: 'disc5' as const, label: `${INDENT}5号`, unit: '5选1', options: DISC5_OPTIONS },
  { key: 'disc6' as const, label: `${INDENT}6号`, unit: '6选1', options: DISC6_OPTIONS },
]);

const slotOptions = computed(() =>
  SLOTS.value.map((slot) => ({
    key: slot.key,
    label: slot.label,
    unit: slot.unit,
    options: slot.options.map((option) => ({ value: option.id, label: localize(option.label) })),
  })),
);
</script>

<template>
  <PanelModule title="四、驱动盘主词条" tag="1~3固定 · 4/5/6可选" variant="disc">
    <div class="disc-main-grid" style="margin-bottom: 10px">
      <div v-for="stat in DISC_FIXED_STATS" :key="stat.slot" class="fixed-stat">
        {{ stat.slot }}号 {{ stat.label }} <span class="v">+{{ stat.value }}</span>
      </div>
    </div>

    <div class="disc-main-grid">
      <SelectField
        v-for="slot in slotOptions"
        :key="slot.key"
        :name="slot.key"
        :label="slot.label"
        :label-unit="slot.unit"
        :model-value="panel.discMain[slot.key]"
        :options="slot.options"
        @update:model-value="panel.discMain[slot.key] = $event"
      />
    </div>
  </PanelModule>
</template>