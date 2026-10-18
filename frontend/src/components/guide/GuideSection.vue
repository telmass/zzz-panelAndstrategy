<script setup lang="ts">
/**
 * 指南章节。对应 legacy guide.html 的 `<h2 id="...">标题</h2>` 加后续内容。
 *
 * `index`（序号徽标）复刻攻略页一级板块的编号方块 `01`–`06`：
 * 文案本身不再写「一、二、三」，序号由徽标承载，与左侧目录的编号一致。
 *
 * 外层 `<section data-spy-region>` 是给侧边目录的滚动侦测用（见
 * `useScrollSpy`）：观察整章而不是几十像素高的 `<h2>`，否则长章节走到中段
 * 时目录高亮会整块消失。锚点 id 仍落在 `<h2>` 上，点击跳转的位置不变。
 */
defineProps<{
  /** 章节标题，如「整体结构概览」。 */
  title: string;
  /** 锚点 id，供目录跳转。原样落在 `<h2>` 上。 */
  anchor: string;
  /** 序号徽标文案，如「01」。 */
  index: string;
}>();
</script>

<template>
  <section class="guide-section" data-spy-region>
    <h2 class="section__title" :id="anchor">
      <span class="section__no" aria-hidden="true">{{ index }}</span>
      <span class="section__title-text">{{ title }}</span>
    </h2>
    <slot />
  </section>
</template>
