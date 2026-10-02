<script setup lang="ts">
import {
  AgentBaseModule,
  CoreModule,
  DiscMainModule,
  DiscSubModule,
  ResultPanel,
  SetEffectModule,
  WeaponModule,
} from '@/components/calculator';

/**
 * 统一计算器页。DOM 结构对应 legacy/pages/calculator.html 的
 * `.container > .layout > (.left | .result)` 三层。
 *
 * 第 1 步仅静态骨架：不读 store、不绑定事件、不发请求。
 */
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