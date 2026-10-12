<script setup lang="ts">
import { BackToLauncher } from '@/components/layout';
import { agentPortraitUrl, strategyGuides } from '@/constants/strategyGuides';

/**
 * 攻略板块的代理人选择页（/strategy）。
 *
 * 启动页只放「代理人攻略」入口卡（与计算器/指南并列的三张功能卡），
 * 本页再做头像卡网格，点卡进入具体代理人的攻略页
 * （`/strategy/<slug>`，iframe 挂载 `strategy/<slug>/`）。
 *
 * 版式对齐米游社 WIKI 频道页：一行 5 个，每卡只放**头像 + 名字**，
 * 多余信息都在攻略页内。卡片数据来自 `constants/strategyGuides.ts`
 * 登记表：一条 = 一个代理人。
 */
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
        class="strategy-card"
        :to="`/strategy/${guide.slug}`"
      >
        <img
          class="strategy-card__avatar"
          :src="agentPortraitUrl(guide.agentId)"
          :alt="guide.name"
          loading="lazy"
        />
        <span class="strategy-card__name">{{ guide.name }}</span>
      </RouterLink>
    </div>
  </main>
</template>
