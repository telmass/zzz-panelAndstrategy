<script setup lang="ts">
import { onMounted, nextTick } from 'vue';
import { BackToLauncher } from '@/components/layout';
import { agentPortraitUrl, strategyGuides } from '@/constants/strategyGuides';

/**
 * 攻略板块的代理人选择页（/strategy）。
 *
 * 启动页只放「代理人攻略」入口卡（与计算器/指南并列的三张功能卡），
 * 本页再做头像卡网格，点卡进入具体代理人的攻略页
 * （`/strategy/<slug>`，Vue 共享渲染器读取 `strategy/<slug>/data/`）。
 *
 * 版式对齐米游社 WIKI 频道页：一行 5 个，所有卡片均走 tachie 背景 +
 * 左上角评级/属性/职业图标 + 底部名字胶囊，tachie 按
 * `frontend/public/images/agents/<agentId>.png` 既有约定取路径，
 * 未填 `tachie` 字段时沿用头像。
 */

// 进入详情前记录当前滚动位置，返回时恢复，避免回到顶部。
onMounted(() => {
  const saved = sessionStorage.getItem('strategyPickerScroll');
  if (saved) {
    const y = Number(saved);
    nextTick(() => window.scrollTo(0, y));
    sessionStorage.removeItem('strategyPickerScroll');
  }
});

function rememberScroll() {
  sessionStorage.setItem('strategyPickerScroll', String(window.scrollY));
}
</script>

<template>
  <BackToLauncher />

  <main class="container page-with-back strategy-picker">
    <h1>代理人攻略</h1>
    <p class="subtitle">选择要查看攻略的代理人。</p>

    <div class="agent-grid">
       <RouterLink
         v-for="guide in strategyGuides"
         :key="guide.slug"
         :class="{
           'strategy-card': true,
           'strategy-card--tachie': guide.tachie,
         }"
         :to="`/strategy/${guide.slug}`"
         @click="rememberScroll"
       >
        <div
          class="strategy-card__tachie"
          :style="{ backgroundImage: `url(${guide.tachie || agentPortraitUrl(guide.agentId)})` }"
        />
        <div v-if="guide.tachie || (guide.gradeIcon || guide.attributeIcon || guide.roleIcon)" class="strategy-card__badges">
          <img
            v-if="guide.gradeIcon"
            class="strategy-card__badge"
            :src="guide.gradeIcon"
            :alt="guide.gradeIcon"
            loading="lazy"
          />
          <img
            v-if="guide.attributeIcon"
            class="strategy-card__badge"
            :src="guide.attributeIcon"
            :alt="guide.attributeIcon"
            loading="lazy"
          />
          <img
            v-if="guide.roleIcon"
            class="strategy-card__badge"
            :src="guide.roleIcon"
            :alt="guide.roleIcon"
            loading="lazy"
          />
        </div>
        <div class="strategy-card__name-wrap">
          <span class="strategy-card__name">{{ guide.name }}</span>
        </div>
      </RouterLink>
    </div>
  </main>
</template>
