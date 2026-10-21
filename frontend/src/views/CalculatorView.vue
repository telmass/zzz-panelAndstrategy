<script setup lang="ts">
import { onMounted } from 'vue';

import {
  AgentBaseModule,
  CoreModule,
  DiscMainModule,
  DiscSubModule,
  ResultPanel,
  SetEffectModule,
  WeaponModule,
} from '@/components/calculator';
import { BackToLauncher, BackToTop } from '@/components/layout';
import { useAgentPreset, validateAgentPresetData } from '@/composables/useAgentPreset';
import { applyBuild } from '@/composables/useBuildPanel';
import { readBuildFromHash } from '@/composables/useBuildIO';
import { usePanelStore } from '@/stores/panelStore';

/**
 * 统一计算器页。DOM 结构对应 legacy/pages/calculator.html 的
 * `.container > .layout > (.left | .result)` 三层。
 *
 * 版面只留两列：左侧六大输入模块 + 右侧吸顶最终面板。这里**不放侧边目录**：
 * 计算器是「边填边看结果」的工具页，四个模块一屏内就能滚完，目录既帮不上忙
 * 又白占一列宽度；长文的指南页才需要它（见 GuideView）。
 *
 * 模块序号徽标（01–06）保留，与攻略页一级板块的编号方块同形，纯作视觉分区。
 *
 * 挂载时按 URL 的 `?mode=` 参数设定初始面板模式，按 `?agent=` 载入代理人预设
 * （slug 或预设 id 皆可），并一次性校验预设数据完整性——任一条不通过即视为
 * 数据源损坏。有了 `?agent=`，一条链接就能复现某位代理人的整套面板。
 */
const { initFromQueryParam } = useAgentPreset();
const panel = usePanelStore();

onMounted(() => {
  validateAgentPresetData();
  const params = new URLSearchParams(window.location.search);
  initFromQueryParam(params.get('mode'), params.get('agent'));

  // 分享链接：``#build=…`` 里是一套配装（本地编码，不落服务端）。
  // 读不到就当没有——访客点开一条失效的链接应该看到正常的页面。
  const shared = readBuildFromHash();
  if (shared) {
    const outcome = applyBuild(shared);
    if (!outcome.ok) {
      panel.setAgentNote({ text: outcome.message, tone: 'error' });
    }
  }
});
</script>

<template>
  <BackToLauncher />

  <div class="container page-with-back">
    <header class="page-hero">
      <p class="eyebrow">ZENLESS ZONE ZERO · PANEL CALCULATOR</p>
      <h1>绝区零代理人面板计算器</h1>
      <p class="subtitle">
        选择代理人预设即可自动应用对应计算规则：通用代理人使用标准面板，命破代理人计算贯穿力，锋御代理人计算实际暴击率。
      </p>
    </header>

    <div class="layout">
      <div class="left">
        <AgentBaseModule />
        <WeaponModule />
        <CoreModule />
        <DiscMainModule />
        <DiscSubModule />
        <SetEffectModule />
      </div>

      <ResultPanel />
    </div>
  </div>

  <BackToTop />
</template>
