<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

/**
 * 回到顶部按钮。复刻攻略页右下角的圆形悬浮按钮：滚动超过一屏后淡入，
 * 点击平滑回顶。计算器页、指南页与启动页共用。
 */
const visible = ref(false);

/** 超过约一屏才出现，避免页首附近按钮闪烁。 */
const SHOW_OFFSET = 400;

function onScroll(): void {
  visible.value = window.scrollY > SHOW_OFFSET;
}

function toTop(): void {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll);
});
</script>

<template>
  <button
    class="to-top"
    :class="{ 'is-visible': visible }"
    type="button"
    aria-label="回到顶部"
    @click="toTop"
  >
    <span aria-hidden="true">↑</span>
  </button>
</template>
