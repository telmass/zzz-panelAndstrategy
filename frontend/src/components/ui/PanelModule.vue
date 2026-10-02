<script setup lang="ts">
/**
 * 模块卡片外壳。对应 legacy 的 `.module` + `.module-title`。
 * `variant` 决定左侧色条与标题标签配色，需与组件同名修饰符一一对应。
 */
withDefaults(
  defineProps<{
    /** 模块序号标题，如「一、基础面板」。 */
    title: string;
    /** 标题右侧的浅色标签文案。 */
    tag?: string;
    /** 配色变体：base / weapon / core / disc / sub / set。 */
    variant: 'base' | 'weapon' | 'core' | 'disc' | 'sub' | 'set';
  }>(),
  { tag: '' },
);
</script>

<template>
  <section class="module" :class="`module--${variant}`">
    <header class="module-title">
      <span>{{ title }}</span>
      <span v-if="tag" class="tag">{{ tag }}</span>
    </header>
    <slot />
  </section>
</template>