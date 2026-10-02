<script setup lang="ts">
import { computed } from 'vue';

import { SET_OPTIONS } from '@/constants/calculatorOptions';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { PanelModule } from '@/components/common';

/**
 * 六、二件套效果。对应 legacy 的 `.module.set`。
 *
 * 组数语义（2+2+2=3 组、4+2=2 组、2+散件=1 组、全散件=0 组）
 * 由三组下拉的留空数量隐含表达——留空即未组成一组。
 */
const panel = usePanelStore();
const { localize } = usePanelMode();

/** 二件套选项含「能量回复 +20%」，锋御模式需替换为锐能文案。 */
const options = computed(() =>
  SET_OPTIONS.map((option) => ({ value: option.id, label: localize(option.label) })),
);

const SLOTS = [
  { key: 'set0' as const, index: 1 },
  { key: 'set1' as const, index: 2 },
  { key: 'set2' as const, index: 3 },
];

function onChange(key: 'set0' | 'set1' | 'set2', event: Event): void {
  panel.setEffects[key] = (event.target as HTMLSelectElement).value;
}
</script>

<template>
  <PanelModule title="六、二件套效果" tag="0~3组" variant="set">
    <p class="note note--lead">
      2+2+2=3组 · 4+2=2组 · 2+散件=1组 · 全散件=0组。每组选一种属性。
    </p>

    <div class="set-grid">
      <div v-for="slot in SLOTS" :key="slot.key" class="set-item">
        <label class="helper" :for="`set${slot.index - 1}`">第{{ slot.index }}组</label>
        <select
          :id="`set${slot.index - 1}`"
          :value="panel.setEffects[slot.key]"
          @change="onChange(slot.key, $event)"
        >
          <option value="">请选择</option>
          <option v-for="option in options" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>
  </PanelModule>
</template>