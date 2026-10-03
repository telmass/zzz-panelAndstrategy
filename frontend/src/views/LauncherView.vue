<script setup lang="ts">
/**
 * 启动界面。版式沿用 legacy/pages/index.html 的卡片网格，配色改为
 * tokens.css 的浅色令牌，与计算器页共用同一套视觉（第 5 步）。
 *
 * 命破与锋御两张卡在 legacy 中已被统一计算器取代（`redirect-*.html`
 * 已改为跳转桩），因此这里只保留「统一计算器」与「学习指南」两个入口。
 * 两张卡片共用 `.card` 样式，不加区分色，保证视觉一致。
 *
 * 曾短暂存在过第三个入口「标准版示例」（/example，吸收自
 * legacy/pages/example-template.html），已按要求整体移除：
 * 路由、视图文件与本页卡片均不复存在。
 */
</script>

<template>
  <main class="container">
    <header class="launcher-header">
      <p class="eyebrow">ZENLESS ZONE ZERO · PANEL TOOLS</p>
      <h1>代理人面板计算器</h1>
      <p class="subtitle">
        选择代理人预设即可自动应用对应计算规则：通用代理人使用标准面板，命破代理人计算贯穿力，锋御代理人计算实际暴击率。
      </p>
    </header>

    <section class="cards" aria-label="选择功能">
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

      <RouterLink class="card" to="/guide">
        <span class="badge">学习指南</span>
        <h2>面板计算方式学习指南</h2>
        <p>说明各字段的取值口径、计算顺序，以及命破与锋御专属面板的差异。</p>
        <span class="launch">打开指南 <span class="arrow" aria-hidden="true">→</span></span>
      </RouterLink>
    </section>

    <footer class="launcher-footer">本地网页工具 · 通过代理人预设切换专属计算</footer>
  </main>
</template>
