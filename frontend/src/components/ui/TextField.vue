<script setup lang="ts">
/**
 * 文本输入字段。对应 legacy 中 `type="text"` 的只读字段，
 * 例如音擎的「固定副词条属性」需要承载 `—` 这类非数值占位符，
 * 数字输入框无法表示，故与 NumberField 分开。
 *
 * 第 1 步只渲染结构，不做双向绑定。
 */
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
</script>

<template>
  <div class="field" :hidden="hidden">
    <label :for="name">{{ label }}</label>
    <!-- TODO(第 2 步)：改为 v-model，接入所选音擎的 subType -->
    <input :id="name" type="text" :value="modelValue" :readonly="readonly" />
  </div>
</template>