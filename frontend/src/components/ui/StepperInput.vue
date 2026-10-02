<script setup lang="ts">
/**
 * 副词条条数步进器。对应 legacy 的 `.sub-count` 与 `.sub-count-btn`。
 *
 * 第 1 步按钮固定为禁用态，仅保留外观；
 * 第 2 步由 `useSubStatLimit` 依据单项 36 条与总计 54 条上限控制 disabled，
 * 并在点击时以 `step` 更新 `panelStore.subStats`。
 */
withDefaults(
  defineProps<{
    label: string;
    /** 单条数值的说明文案，如「+112/条」。 */
    unitText?: string;
    modelValue?: number;
  }>(),
  { unitText: '', modelValue: 0 },
);
</script>

<template>
  <div class="field">
    <label>
      {{ label }}
      <span v-if="unitText" class="unit">{{ unitText }}</span>
    </label>
    <div class="sub-count">
      <!-- TODO(第 2 步)：绑定 adjustSubCounts(id, -1) / adjustSubCounts(id, 1) -->
      <button type="button" class="sub-count-btn" disabled aria-label="减少副词条数量">−</button>
      <input type="number" min="0" :max="36" step="1" :value="modelValue" readonly />
      <button type="button" class="sub-count-btn" disabled aria-label="增加副词条数量">+</button>
      <span class="total">0</span>
    </div>
  </div>
</template>