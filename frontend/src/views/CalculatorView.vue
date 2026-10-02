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
import { useAgentPreset, validateAgentPresetData } from '@/composables/useAgentPreset';

/**
 * 统一计算器页。DOM 结构对应 legacy/pages/calculator.html 的
 * `.container > .layout > (.left | .result)` 三层。
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
  <div class="container">
    <h1>绝区零代理人面板计算器</h1>

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
</template>