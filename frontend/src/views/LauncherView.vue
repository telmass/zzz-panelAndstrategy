<script setup lang="ts">
import { BackToTop } from '@/components/layout';
import { ENTRY_CARDS, NAV_LINKS } from '@/constants/navigation';

/**
 * 启动界面（产品主页）。导航链接与入口卡均从 `constants/navigation.ts`
 * 的 manifest 取值——新增功能板块只需在 manifest 登记，两侧自动同步。
 *
 * 首页没有返回按钮，导航条同时承担「回首页」的职责。
 */

/** 首页卡片上的特性列表。key 与 manifest 的 `id` 一一对应。 */
const CARD_FEATURES: Record<string, string[]> = {
  calculator: ['60 名代理人预设', '101 项音擎预设', '逐项计算明细'],
  guide: ['六大模块口径', '命破 / 锋御差异', '公式与示例推演'],
  strategy: ['技能 / 影画数据', '音擎与驱动盘推荐', '满配毕业面板'],
};

/** 每张卡的视觉文案（徽标 + 标题 + 描述 + 按钮文字）。 */
const CARD_COPY: Record<string, { badge: string; title: string; desc: string; launch: string }> = {
  calculator: {
    badge: '统一计算器',
    title: '代理人面板',
    desc: '在同一页面完成代理人预设、基础面板和配装计算，并根据所选代理人自动显示专属面板。',
    launch: '打开计算器',
  },
  guide: {
    badge: '学习指南',
    title: '面板计算方式学习指南',
    desc: '说明各字段的取值口径、计算顺序，以及命破与锋御专属面板的差异。',
    launch: '打开指南',
  },
  strategy: {
    badge: '代理人攻略',
    title: '代理人攻略',
    desc: '从官方 WIKI 数据整理的单页攻略：技能、影画、加点、音擎与驱动盘推荐、毕业面板与队伍推荐。先选择代理人。',
    launch: '选择代理人',
  },
};

/** 页眉信息片：一眼说明站点覆盖面。 */
const HERO_CHIPS = ['60 名代理人预设', '101 项音擎预设', '三类面板模式', '网页与命令行同源'];
</script>

<template>
  <!-- 顶部站点导航：跨板块互通，链接来自 navigation manifest -->
  <header class="site-nav">
    <div class="site-nav__inner">
      <span class="site-nav__brand">
        <span class="site-nav__badge">ZZZ</span>
        <span class="site-nav__brand-text">绝区零 · 面板工具</span>
      </span>
      <nav class="site-nav__links" aria-label="站点导航">
        <RouterLink
          v-for="area in NAV_LINKS"
          :key="area.id"
          class="site-nav__link"
          :to="area.path"
        >
          {{ area.label }}
        </RouterLink>
      </nav>
    </div>
  </header>

  <main class="container">
    <header class="launcher-header">
      <p class="eyebrow">ZENLESS ZONE ZERO · PANEL TOOLS</p>
      <h1>绝区零 · 面板计算与攻略</h1>
      <p class="subtitle">
        选择代理人预设即可自动应用对应计算规则：通用代理人使用标准面板，命破代理人计算贯穿力，锋御代理人计算实际暴击率。
      </p>
      <ul class="hero-chips">
        <li v-for="chip in HERO_CHIPS" :key="chip" class="hero-chip">{{ chip }}</li>
      </ul>
    </header>

    <section class="cards" aria-label="选择功能">
      <RouterLink
        v-for="(area, index) in ENTRY_CARDS"
        :key="area.id"
        class="card"
        :to="area.path"
      >
        <span class="card__no" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
        <span class="badge">{{ CARD_COPY[area.id]?.badge }}</span>
        <h2>{{ CARD_COPY[area.id]?.title }}</h2>
        <p>{{ CARD_COPY[area.id]?.desc }}</p>
        <span v-if="area.id === 'calculator'" class="formula">
          命破：贯穿力 = 0.3 × 最终攻击力 + 0.1 × 最终生命值<br />
          锋御：实际暴击率 = 最终暴击伤害 × 35% + 原最终暴击率
        </span>
        <ul v-if="CARD_FEATURES[area.id]" class="card__features">
          <li v-for="feature in CARD_FEATURES[area.id]" :key="feature">{{ feature }}</li>
        </ul>
        <span class="launch">
          {{ CARD_COPY[area.id]?.launch }}
          <span class="arrow" aria-hidden="true">→</span>
        </span>
      </RouterLink>
    </section>

    <footer class="launcher-footer">
      <p>本地网页工具 · 通过代理人预设切换专属计算</p>
      <p class="launcher-footer__meta">数据来源：米游社绝区零 WIKI · 计算由后端完成，网页与命令行结果必然一致</p>
    </footer>
  </main>

  <BackToTop />
</template>
