<script setup lang="ts">
import { SUB_STAT_LIMIT_PER_KEY } from '@/constants/calculatorOptions';
import type { SubStatEntry } from '@/composables/useSubStatLimit';

/**
 * 副词条条数步进器。对应 legacy 的 `.sub-count`。
 *
 * 按钮可用性由 `useSubStatLimit` 计算后经 props 下传：
 * 单项已达 36 条或合计已达 54 条时禁用加号，为 0 时禁用减号。
 */
withDefaults(
  defineProps<{
    label: string;
    /** 单条数值说明，如「+112/条」。 */
    unitText?: string;
    entry: SubStatEntry;
  }>(),
  { unitText: '' },
);

const emit = defineEmits<{
  step: [delta: number];
  input: [value: string];
}>();

function onInput(event: Event): void {
  emit('input', (event.target as HTMLInputElement).value);
}
</script>

<template>
  <div class="field">
    <label :for="`sub_${entry.def.id}`">
      {{ label }}
      <span class="unit">{{ unitText }}</span>
    </label>
    <div class="sub-count">
      <button
        type="button"
        class="sub-count-btn"
        :disabled="!entry.canDecrease"
        :aria-label="`减少${label}副词条数量`"
        @click="emit('step', -1)"
      >
        −
      </button>
      <input
        :id="`sub_${entry.def.id}`"
        type="number"
        min="0"
        :max="SUB_STAT_LIMIT_PER_KEY"
        step="1"
        :value="entry.count"
        :aria-label="`${label}副词条数量`"
        @input="onInput"
      />
      <button
        type="button"
        class="sub-count-btn"
        :disabled="!entry.canIncrease"
        :aria-label="`增加${label}副词条数量`"
        @click="emit('step', 1)"
      >
        +
      </button>
      <span class="total">{{ entry.total }}</span>
    </div>
  </div>
</template>