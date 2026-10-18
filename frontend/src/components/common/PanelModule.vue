<script setup lang="ts">
/**
 * 模块卡片外壳。对应 legacy 的 `.module` + `.module-title`。
 * `variant` 决定左侧色条与标题标签配色，需与组件同名修饰符一一对应。
 *
 * `index`（序号徽标）复刻攻略页一级板块的编号方块：序号由徽标承载，
 * 标题文本不再写「一、二、三」。计算器页不放侧边目录，故这里**没有**锚点
 * 参数——需要锚点的是 GuideSection（指南章）那类长文板块。
 */
withDefaults(
  defineProps<{
    /** 模块标题，如「基础面板」。 */
    title: string;
    /** 标题右侧的浅色标签文案。 */
    tag?: string;
    /** 配色变体：base / weapon / core / disc / sub / set。 */
    variant: 'base' | 'weapon' | 'core' | 'disc' | 'sub' | 'set';
    /** 序号徽标文案，如「01」；为空时不渲染徽标。 */
    index?: string;
  }>(),
  { tag: '', index: '' },
);
</script>

<template>
  <section class="module" :class="`module--${variant}`">
    <header class="module-title">
      <span v-if="index" class="module-no" aria-hidden="true">{{ index }}</span>
      <span class="module-title__text">{{ title }}</span>
      <span v-if="tag" class="tag">{{ tag }}</span>
    </header>
    <slot />
  </section>
</template>
