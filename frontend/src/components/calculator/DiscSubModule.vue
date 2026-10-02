<script setup lang="ts">
import { SUB_STAT_TOTAL_LIMIT } from '@/constants/calculatorOptions';
import { useSubStatLimit } from '@/composables/useSubStatLimit';
import { PanelModule, StepperInput } from '@/components/common';

/**
 * 五、驱动盘副词条。对应 legacy 的 `.module.sub`。
 *
 * legacy 由 JS 以模板字符串注入 `#sub_grid`，并直接操作 DOM 写合计读数、
 * 按钮 disabled 与输入框钳制；此处改为 `useSubStatLimit` 计算后经 props 下传，
 * 行为等价但副作用全部收敛到 composable。
 */
const { entries, totalCount, isTotalExceeded, step, setCount } = useSubStatLimit();
</script>

<template>
  <PanelModule title="五、驱动盘副词条" tag="每盘9条 · 6盘共54条" variant="sub">
    <p class="note note--lead">
      填写6盘合计副词条条数（每盘4初始+5强化=9条）。单条数值见标签，自动按条数折算。
    </p>

    <div class="grid-4">
      <StepperInput
        v-for="entry in entries"
        :key="entry.def.id"
        :label="entry.def.label"
        :unit-text="`+${entry.def.value}${entry.def.kind === 'pct' ? '%' : ''}/条`"
        :entry="entry"
        @step="step(entry.def, $event)"
        @input="setCount(entry.def.id, $event)"
      />
    </div>

    <p class="note">
      副词条总数：<span :style="isTotalExceeded ? 'color: #ef4444' : 'color: #111827'">{{ totalCount }}</span> /
      {{ SUB_STAT_TOTAL_LIMIT }}
      <span class="helper">（单项最多36条；主副不重复：若该属性是某盘主词条，则该属性副词条不计）</span>
    </p>
  </PanelModule>
</template>