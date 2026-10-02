<script setup lang="ts">
/**
 * 数值输入字段。对应 legacy 的 `.field` + `<input type="number">`。
 *
 * `modelValue` 允许数字或字符串：数字字段传 number，
 * 留空状态传空字符串以复现 legacy 中 `input.value = ''` 的表现。
 */
withDefaults(
  defineProps<{
    /** 字段标识，同时作为 label 的 for。 */
    name: string;
    label: string;
    /** 标签右侧的单位后缀，如 '%'。 */
    unit?: string;
    modelValue?: number | string;
    readonly?: boolean;
    hidden?: boolean;
  }>(),
  { unit: '', modelValue: 0, readonly: false, hidden: false },
);

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

/** 原样上抛输入框的字符串，由 store 侧负责数值转换。 */
function onInput(event: Event): void {
  emit('update:modelValue', (event.target as HTMLInputElement).value);
}
</script>

<template>
  <div class="field" :hidden="hidden">
    <label :for="name">{{ label }}<span v-if="unit" class="unit"> {{ unit }}</span></label>
    <input
      :id="name"
      type="number"
      step="any"
      :value="modelValue"
      :readonly="readonly"
      @input="onInput"
    />
  </div>
</template>