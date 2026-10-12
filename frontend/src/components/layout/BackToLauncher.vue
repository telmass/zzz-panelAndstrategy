<script setup lang="ts">
/**
 * 子页面左上角的返回按钮。计算器页、指南页与攻略选择页共用，默认回启动页 `/`。
 *
 * 样式复用 `.btn`——与副词条步进器按钮（`.sub-count-btn`）同一套 accent 视觉，
 * 不另写一套配色；定位与让位分别由 `.back-link` 和 `.page-with-back` 负责。
 * 目标写成路径而非路由名，与 `LauncherView` 里的入口写法保持一致。
 *
 * 攻略详情页（/strategy/:slug）的上一层是代理人选择页而非启动页，故该页传
 * `to="/strategy" label="返回代理人选择"`。
 */
withDefaults(defineProps<{ to?: string; label?: string }>(), {
  to: '/',
  label: '返回主页',
});
</script>

<template>
  <RouterLink class="btn back-link" :to="to">
    <span class="back-link__arrow" aria-hidden="true">←</span>
    <span>{{ label }}</span>
  </RouterLink>
</template>
