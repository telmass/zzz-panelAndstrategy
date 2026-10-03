<script setup lang="ts">
/** 指南章节。对应 legacy guide.html 的 `<h2 id="...">标题</h2>` 加后续内容。 */
defineProps<{
  /** 章节序号与标题，如「一、整体结构概览」。 */
  title: string;
  /** 锚点 id，供目录跳转。原样落在 `<h2>` 上。 */
  anchor: string;
}>();
</script>

<template>
  <h2 :id="anchor">{{ title }}</h2>
  <slot />
</template>
