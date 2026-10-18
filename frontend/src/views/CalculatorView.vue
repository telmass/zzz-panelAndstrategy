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
 * 挂载时按 URL 的 `?mode=` 参数设定初始面板模式，
 * 并一次性校验预设数据完整性——任一条不通过即视为数据源损坏。
 */
const { initFromQueryParam } = useAgentPreset();

onMounted(() => {
  validateAgentPresetData();
  initFromQueryParam(new URLSearchParams(window.location.search).get('mode'));
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
