<script setup lang="ts">
/**
 * 数值输入字段。对应 legacy 的 `.field` + `<input type="number">`。
 *
 * 第 1 步只渲染结构，不做双向绑定；第 2 步在此接入 `v-model`
 * （配合 `panelStore` 的对应字段）与输入校验。
 */
withDefaults(
  defineProps<{
    /** 字段标识，同时作为 label 的 for 与后续 store 映射的键。 */
    name: string;
    label: string;
    /** 标签右侧的单位后缀，如 '%'。 */
    unit?: string;
    modelValue?: number | string;
    /** 只读字段用于展示音擎固定属性。 */
    readonly?: boolean;
    /** 隐藏字段由父级按面板模式控制显隐。 */
    hidden?: boolean;
  }>(),
  { unit: '', modelValue: 0, readonly: false, hidden: false },
);
</script>

<template>
  <div class="field" :hidden="hidden">
    <label :for="name">{{ label }}<span v-if="unit" class="unit"> {{ unit }}</span></label>
    <!-- TODO(第 2 步)：改为 v-model="panel.base.${name}" -->
    <input :id="name" type="number" :value="modelValue" step="any" :readonly="readonly" />
  </div>
</template>