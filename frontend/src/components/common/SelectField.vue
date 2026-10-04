<script setup lang="ts">
import type { SelectOption } from '@/types/panel';

/**
 * 下拉选择字段。对应 legacy 的 `.field` + `<select>`。
 *
 * 选项由父级传入，因此音擎三级联动、代理人标签联动等行为
 * 全部由各模块组件通过 store action 承担，此处只负责展示与上抛变更。
 */
withDefaults(
  defineProps<{
    name: string;
    label: string;
    labelUnit?: string;
    options?: SelectOption[];
    modelValue?: string;
    /** 首个空选项的文案。 */
    placeholder?: string;
  }>(),
  {
    labelUnit: '',
    options: () => [],
    modelValue: '',
    placeholder: '请选择',
  },
);

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

function onChange(event: Event): void {
  emit('update:modelValue', (event.target as HTMLSelectElement).value);
}
</script>

<template>
  <div class="field">
    <label :for="name">{{ label }}<span v-if="labelUnit" class="unit"> {{ labelUnit }}</span></label>
    <select :id="name" :value="modelValue" @change="onChange">
      <option value="">{{ placeholder }}</option>
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
  </div>
</template>