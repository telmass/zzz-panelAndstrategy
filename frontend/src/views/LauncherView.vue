<script setup lang="ts">
/**
 * 启动界面。复刻 legacy/pages/index.html 的卡片布局。
 *
 * 命破与锋御两张卡在 legacy 中已被统一计算器取代（`redirect-*.html`
 * 已改为跳转桩），因此这里只保留「统一计算器」入口，与 legacy 一致。
 */
</script>

<template>
  <main class="launcher-shell">
    <header class="launcher-header">
      <p class="eyebrow">ZENLESS ZONE ZERO · PANEL TOOLS</p>
      <h1>代理人面板计算器</h1>
      <p class="intro">
        选择代理人预设即可自动应用对应计算规则：通用代理人使用标准面板，命破代理人计算贯穿力，锋御代理人计算实际暴击率。
      </p>
    </header>

    <section class="cards" aria-label="选择计算器">
      <RouterLink class="card" to="/calculator">
        <span class="badge">统一计算器</span>
        <h2>代理人面板</h2>
        <p>在同一页面完成代理人预设、基础面板和配装计算，并根据所选代理人自动显示专属面板。</p>
        <span class="formula">
          命破：贯穿力 = 0.3 × 最终攻击力 + 0.1 × 最终生命值<br />
          锋御：实际暴击率 = 最终暴击伤害 × 35% + 原最终暴击率
        </span>
        <span class="launch">打开计算器 <span class="arrow" aria-hidden="true">→</span></span>
      </RouterLink>
    </section>

    <footer class="launcher-footer">本地网页工具 · 通过代理人预设切换专属计算</footer>
  </main>
</template>