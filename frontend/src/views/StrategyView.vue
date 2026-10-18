<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';

import { BackToLauncher } from '@/components/layout';
import { renderStrategy } from '@/strategy/renderStrategy';
import '@/strategy/strategy.css';

/**
 * 代理人攻略详情页。
 *
 * 攻略数据仍以 `strategy/<slug>/data/<slug>.json` 与 `.strategy.json` 为唯一真实源，
 * 但页面不再由 59 份静态 `index.html/app.js/styles.css` 渲染：
 * 主应用直接挂载共享渲染器 `@/strategy/renderStrategy`，样式收窄在
 * `.strategy-detail` 下，因此没有 iframe、也没有每页模板副本。
 *
 * 新增代理人只需放数据；渲染器与样式自动复用。
 */
const props = defineProps<{ slug: string }>();

const host = ref<HTMLElement | null>(null);
const state = ref<'loading' | 'ready' | 'error'>('loading');
const errorMessage = ref('');

let cleanup: (() => void) | undefined;
let requestId = 0;

async function load(slug: string): Promise<void> {
  const current = ++requestId;
  cleanup?.();
  cleanup = undefined;
  state.value = 'loading';
  errorMessage.value = '';

  try {
    const base = `/strategy/${slug}/data/${slug}`;
    const [guideResponse, strategyResponse] = await Promise.all([
      fetch(`${base}.json`, { cache: 'no-store' }),
      fetch(`${base}.strategy.json`, { cache: 'no-store' }),
    ]);
    if (!guideResponse.ok) {
      throw new Error(`HTTP ${guideResponse.status}`);
    }
    const guide: Record<string, unknown> = await guideResponse.json();
    guide.strategy = strategyResponse.ok ? await strategyResponse.json() : null;

    if (current !== requestId || !host.value) {
      return;
    }
    cleanup = renderStrategy({
      root: host.value,
      guide,
      slug,
      onTitle: (title) => {
        document.title = title;
      },
    });
    state.value = 'ready';
  } catch (error) {
    if (current !== requestId) {
      return;
    }
    errorMessage.value = error instanceof Error ? error.message : String(error);
    state.value = 'error';
  }
}

watch(
  () => props.slug,
  (slug) => {
    void load(slug);
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  requestId += 1;
  cleanup?.();
  cleanup = undefined;
  document.title = '代理人面板计算器';
});
</script>

<template>
  <BackToLauncher to="/strategy" label="返回代理人选择" />

  <div class="strategy-detail">
    <div v-if="state === 'loading'" class="boot">
      <div class="boot__spinner" aria-hidden="true"></div>
      <p class="boot__text">正在加载攻略数据…</p>
    </div>

    <div v-else-if="state === 'error'" class="boot boot--error">
      <p class="boot__title">无法加载攻略数据</p>
      <p class="boot__text">{{ errorMessage }}</p>
      <p class="boot__text">
        请确认 <code>strategy/{{ slug }}/data/{{ slug }}.json</code> 存在，并重新启动前端。
      </p>
    </div>

    <div v-show="state === 'ready'" ref="host" class="app" data-state="loading"></div>
  </div>
</template>
