<script setup lang="ts">
import type { SelectOption } from '@/types/panel';

/**
 * 下拉选择字段。对应 legacy 的 `.field` + `<select>`。
 *
 * 第 1 步只渲染结构，不做双向绑定与联动；
 * 第 2 步接入 `v-model` 与级联逻辑（音擎三级联动、代理人标签联动）。
 */
withDefaults(
  defineProps<{
    name: string;
    label: string;
    labelUnit?: string;
    options?: SelectOption[];
    modelValue?: string;
    /** 未就绪时的占位文案，如「请先选择标签」。 */
    placeholder?: string;
    disabled?: boolean;
    hidden?: boolean;
  }>(),
  { labelUnit: '', options: () => [], modelValue: '', placeholder: '请选择', disabled: false, hidden: false },
);
</script>

<template>
  <div class="field" :hidden="hidden">
    <label :for="name">{{ label }}<span v-if="labelUnit" class="unit"> {{ labelUnit }}</span></label>
    <!-- TODO(第 2 步)：改为 v-model，并将 options 换成 store 派生值 -->
    <select :id="name" :value="modelValue" :disabled="disabled">
      <option value="">{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
  </div>
</template>