<script setup lang="ts">
/** 指南里的属性卡片网格。对应 legacy guide.html 的 `.attr-grid` + `.attr-item`。 */
withDefaults(
  defineProps<{
    items: { label: string; value: string }[];
    /**
     * 固定列数。默认自适应；最终面板一览为 `repeat(4, 1fr)`，
     * 与 legacy 的行内 `grid-template-columns` 一致。
     */
    columns?: number;
    /** 深色卡片（最终面板一览压在渐变底上，用半透明白底）。 */
    onDark?: boolean;
  }>(),
  { columns: 0, onDark: false },
);
</script>

<template>
  <div
    class="guide-attrs"
    :class="{ 'guide-attrs--dark': onDark }"
    :style="columns ? { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` } : undefined"
  >
    <div v-for="item in items" :key="item.label" class="guide-attrs__item">
      <div class="guide-attrs__label">{{ item.label }}</div>
      <div class="guide-attrs__value">{{ item.value }}</div>
    </div>
  </div>
</template>
