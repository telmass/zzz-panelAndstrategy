<script setup lang="ts">
import { SUB_STATS, SUB_STAT_TOTAL_LIMIT } from '@/constants/placeholderOptions';
import { PanelModule, StepperInput } from '@/components/ui';

/**
 * 五、驱动盘副词条。对应 legacy 的 `.module.sub`。
 *
 * legacy 由 JS 以模板字符串注入 `#sub_grid`；此处改为按 `SUB_STATS`
 * 静态渲染 10 项，视觉与 DOM 结构一致。
 * 总数钳制（单项 ≤36、合计 ≤54）与主副不重复规则在第 2 步实现。
 */
</script>

<template>
  <PanelModule title="五、驱动盘副词条" tag="每盘9条 · 6盘共54条" variant="sub">
    <p class="note note--lead">
      填写6盘合计副词条条数（每盘4初始+5强化=9条）。单条数值见标签，自动按条数折算。
    </p>

    <!-- TODO(第 2 步)：:model-value 改为 panel.subStats[stat.id]，
         并由 useSubStatLimit 控制按钮 disabled 与合计读数 -->
    <div class="grid-4">
      <StepperInput
        v-for="stat in SUB_STATS"
        :key="stat.id"
        :label="stat.label"
        :unit-text="`+${stat.value}${stat.kind === 'pct' ? '%' : ''}/条`"
        :model-value="0"
      />
    </div>

    <p class="note">
      副词条总数：<span>0</span> / {{ SUB_STAT_TOTAL_LIMIT }}
      <span class="helper">（单项最多36条；主副不重复：若该属性是某盘主词条，则该属性副词条不计）</span>
    </p>
  </PanelModule>
</template>