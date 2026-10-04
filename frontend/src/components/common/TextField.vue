<script setup lang="ts">
/**
 * 只读文本字段，用于承载 `—` 等非数值占位符（音擎的固定副词条属性）。
 *
 * 唯一使用处（音擎模块的「固定副词条属性」）恒为 `readonly` 且不监听变更，
 * 因此本组件**不抛事件**，也不接受输入。
 */
withDefaults(
  defineProps<{
    name: string;
    label: string;
    modelValue?: string;
    readonly?: boolean;
  }>(),
  { modelValue: '', readonly: false },
);
</script>

<template>
  <div class="field">
    <label :for="name">{{ label }}</label>
    <input :id="name" type="text" :value="modelValue" :readonly="readonly" />
  </div>
</template>