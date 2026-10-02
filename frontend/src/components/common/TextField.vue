<script setup lang="ts">
/** 文本输入字段，用于承载 `—` 等非数值占位符（音擎的固定副词条属性）。 */
withDefaults(
  defineProps<{
    name: string;
    label: string;
    modelValue?: string;
    readonly?: boolean;
    hidden?: boolean;
  }>(),
  { modelValue: '', readonly: false, hidden: false },
);

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

function onInput(event: Event): void {
  emit('update:modelValue', (event.target as HTMLInputElement).value);
}
</script>

<template>
  <div class="field" :hidden="hidden">
    <label :for="name">{{ label }}</label>
    <input
      :id="name"
      type="text"
      :value="modelValue"
      :readonly="readonly"
      @input="onInput"
    />
  </div>
</template>