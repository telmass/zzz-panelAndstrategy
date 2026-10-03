<script setup lang="ts">
/**
 * 子页面左上角的「返回主页」按钮。计算器页与指南页共用。
 *
 * 样式复用 `.btn`——与副词条步进器按钮（`.sub-count-btn`）同一套 accent 视觉，
 * 不另写一套配色；定位与让位分别由 `.back-link` 和 `.page-with-back` 负责。
 * 目标写成路径而非路由名，与 `LauncherView` 里的入口写法保持一致。
 */
</script>

<template>
  <RouterLink class="btn back-link" to="/">
    <span class="back-link__arrow" aria-hidden="true">←</span>
    <span>返回主页</span>
  </RouterLink>
</template>
