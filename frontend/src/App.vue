<script setup lang="ts">
import { computed } from 'vue';
import { NConfigProvider } from 'naive-ui';

import { naiveThemeOverrides } from '@/composables/useNaiveTheme';

/**
 * naive-ui 的浮层组件（音擎 cascader）需要 `n-config-provider` 才能拿到主题，
 * 放在根组件可让全站共用一份配置。
 *
 * 主题覆盖读自 `assets/styles/tokens.css`，避免 naive 自带的蓝色与项目靛蓝并存。
 * 其余页面样式仍走项目自己的 CSS，不受 naive 的 reset 影响——这里不开
 * `preflight`，否则 naive 的全局 reset 会改写 `body` 等既有排版。
 */
const themeOverrides = computed(() => naiveThemeOverrides());
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <router-view />
  </n-config-provider>
</template>