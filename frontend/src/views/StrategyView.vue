<script setup lang="ts">
import { computed } from 'vue';

import { BackToLauncher } from '@/components/layout';
import { strategyGuides } from '@/constants/strategyGuides';

/**
 * 代理人攻略页舞台。攻略本体是 strategy/<slug>/ 下的零依赖静态页，
 * 由 vite.config.ts 的 strategyPagesPlugin 挂载到 /strategy/<slug>/，
 * 这里用整屏 iframe 嵌入，使应用外壳（返回、路由）保持可用。
 *
 * 返回按钮回代理人选择页（/strategy）而不是启动页：本页的入口是选择页卡片，
 * 「返回」应回到上一层。slug 有效性在路由 beforeEnter 处已校验，见 router/index.ts。
 */
const props = defineProps<{ slug: string }>();

const guide = computed(() => strategyGuides.find((item) => item.slug === props.slug));
const src = computed(() => `/strategy/${props.slug}/index.html`);
</script>

<template>
  <BackToLauncher to="/strategy" label="返回代理人选择" />

  <iframe
    class="strategy-frame"
    :src="src"
    :title="guide ? `代理人攻略 · ${guide.name}` : '代理人攻略'"
    allowfullscreen
  />
</template>
