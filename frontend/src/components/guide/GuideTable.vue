<script setup lang="ts">
/**
 * 指南里的表格。对应 legacy guide.html 的 `table` + `.calc-table`。
 *
 * 表头由 `head` 给出；表体走默认插槽，因为单元格里有 `<strong>`、`<br>`
 * 与百分比/数值两种着色，逐格拆成 props 反而更难读。
 * 行级修饰类写在 `<tr>` 上：`guide-table__section`（分组标题行）、
 * `guide-table__total`（小计行）。
 */
withDefaults(
  defineProps<{
    head: string[];
    /** 12px 紧凑字号，列多的表用它。 */
    compact?: boolean;
    /** 末列右对齐并用等宽字体，`.calc-table` 的做法。 */
    numeric?: boolean;
  }>(),
  { compact: false, numeric: false },
);
</script>

<template>
  <table
    class="guide-table"
    :class="{ 'guide-table--compact': compact, 'guide-table--numeric': numeric }"
  >
    <thead>
      <tr>
        <th v-for="cell in head" :key="cell">{{ cell }}</th>
      </tr>
    </thead>
    <tbody>
      <slot />
    </tbody>
  </table>
</template>
