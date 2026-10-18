<script setup lang="ts">
import { BackToTop } from '@/components/layout';

/**
 * 启动界面。版式沿用 legacy/pages/index.html 的卡片网格，配色改为
 * tokens.css 的浅色令牌，与计算器页共用同一套视觉（第 5 步）。
 *
 * 命破与锋御两张卡在 legacy 中已被统一计算器取代（`redirect-*.html`
 * 已改为跳转桩）。这里只放**板块入口**，每张点进去各自是一个子页面；
 * 三张卡片共用 `.card` 样式，不加区分色，保证视觉一致。
 *
 * 曾短暂存在过第四个入口「标准版示例」（/example，吸收自
 * legacy/pages/example-template.html），已按要求整体移除：
 * 路由、视图文件与本页卡片均不复存在。
 *
 * 与攻略页对齐的两处新增：顶部站点导航条（四个板块互通）与卡片序号
 * 徽标 + 特性列表；首页没有返回按钮，导航条同时承担「回首页」的职责。
 */

/** 首页卡片上的特性列表。与卡片正文解耦，增删条目不必碰排版。 */
const CARD_FEATURES: Record<string, string[]> = {
  calculator: ['60 名代理人预设', '100 项音擎预设', '逐项计算明细'],
  guide: ['六大模块口径', '命破 / 锋御差异', '公式与示例推演'],
  strategy: ['技能 / 影画数据', '音擎与驱动盘推荐', '满配毕业面板'],
};

/** 页眉信息片：一眼说明站点覆盖面。 */
const HERO_CHIPS = ['60 名代理人预设', '100 项音擎预设', '三类面板模式', '网页与命令行同源'];
</script>

<template>
  <!-- 顶部站点导航：跨板块互通。子页面改用左上角返回按钮，故只有首页挂它 -->
  <header class="site-nav">
    <div class="site-nav__inner">
      <span class="site-nav__brand">
        <span class="site-nav__badge">ZZZ</span>
        <span class="site-nav__brand-text">绝区零 · 面板工具</span>
      </span>
      <nav class="site-nav__links" aria-label="站点导航">
        <RouterLink class="site-nav__link" to="/">首页</RouterLink>
        <RouterLink class="site-nav__link" to="/calculator">计算器</RouterLink>
        <RouterLink class="site-nav__link" to="/guide">指南</RouterLink>
        <RouterLink class="site-nav__link" to="/strategy">攻略</RouterLink>
      </nav>
    </div>
  </header>

  <main class="container">
    <header class="launcher-header">
      <p class="eyebrow">ZENLESS ZONE ZERO · PANEL TOOLS</p>
      <h1>代理人面板计算器</h1>
      <p class="subtitle">
        选择代理人预设即可自动应用对应计算规则：通用代理人使用标准面板，命破代理人计算贯穿力，锋御代理人计算实际暴击率。
      </p>
      <ul class="hero-chips">
        <li v-for="chip in HERO_CHIPS" :key="chip" class="hero-chip">{{ chip }}</li>
      </ul>
    </header>

    <section class="cards" aria-label="选择功能">
      <RouterLink class="card" to="/calculator">
        <span class="card__no" aria-hidden="true">01</span>
        <span class="badge">统一计算器</span>
        <h2>代理人面板</h2>
        <p>在同一页面完成代理人预设、基础面板和配装计算，并根据所选代理人自动显示专属面板。</p>
        <span class="formula">
          命破：贯穿力 = 0.3 × 最终攻击力 + 0.1 × 最终生命值<br />
          锋御：实际暴击率 = 最终暴击伤害 × 35% + 原最终暴击率
        </span>
        <ul class="card__features">
          <li v-for="feature in CARD_FEATURES.calculator" :key="feature">{{ feature }}</li>
        </ul>
        <span class="launch">打开计算器 <span class="arrow" aria-hidden="true">→</span></span>
      </RouterLink>

      <RouterLink class="card" to="/guide">
        <span class="card__no" aria-hidden="true">02</span>
        <span class="badge">学习指南</span>
        <h2>面板计算方式学习指南</h2>
        <p>说明各字段的取值口径、计算顺序，以及命破与锋御专属面板的差异。</p>
        <ul class="card__features">
          <li v-for="feature in CARD_FEATURES.guide" :key="feature">{{ feature }}</li>
        </ul>
        <span class="launch">打开指南 <span class="arrow" aria-hidden="true">→</span></span>
      </RouterLink>

      <RouterLink class="card" to="/strategy">
        <span class="card__no" aria-hidden="true">03</span>
        <span class="badge">代理人攻略</span>
        <h2>代理人攻略</h2>
        <p>从官方 WIKI 数据整理的单页攻略：技能、影画、加点、音擎与驱动盘推荐、毕业面板与队伍推荐。先选择代理人。</p>
        <ul class="card__features">
          <li v-for="feature in CARD_FEATURES.strategy" :key="feature">{{ feature }}</li>
        </ul>
        <span class="launch">选择代理人 <span class="arrow" aria-hidden="true">→</span></span>
      </RouterLink>
    </section>

    <footer class="launcher-footer">
      <p>本地网页工具 · 通过代理人预设切换专属计算</p>
      <p class="launcher-footer__meta">数据来源：米游社绝区零 WIKI · 计算由后端完成，网页与命令行结果必然一致</p>
    </footer>
  </main>

  <BackToTop />
</template>
