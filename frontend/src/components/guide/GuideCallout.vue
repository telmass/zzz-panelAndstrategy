<script setup lang="ts">
/**
 * 指南里的提示框。对应 legacy guide.html 的 `.highlight` 及其四个配色变体
 * （默认 / blue / green / purple / yellow）。
 *
 * legacy 把配色写在行内 `style` 上，这里收进 `tone` 修饰符，样式集中在本组件上。
 */
withDefaults(
  defineProps<{
    /** 标题，如「📌 一句话理解」。留空则不渲染标题行。 */
    title?: string;
    tone?: 'plain' | 'blue' | 'green' | 'purple' | 'yellow';
  }>(),
  { title: '', tone: 'plain' },
);
</script>

<template>
  <div class="guide-callout" :class="`guide-callout--${tone}`">
    <p v-if="title" class="guide-callout__title">{{ title }}</p>
    <slot />
  </div>
</template>
