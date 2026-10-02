<script setup lang="ts">
import { computed } from 'vue';

import { usePanelStore } from '@/stores/panelStore';

/**
 * 最终面板。对应 legacy 的 `.result` + `.result-module`。
 *
 * 行顺序、标签与主属性标记完全对齐 legacy/calculator.html 的 15 行结果区，
 * 命破与锋御专属行通过 `ruptureOnly` / `fengyuOnly` 标注显隐条件。
 *
 * 第 1 步数值与明细均为占位：值恒为 `—`，明细为空。
 * 第 2 步接 `panelStore.result`（前端计算）；第 3 步改由后端响应填充。
 */
interface ResultRowDef {
  key: string;
  label: string;
  main?: boolean;
  ruptureOnly?: boolean;
  fengyuOnly?: boolean;
  unit?: string;
}

const ROWS: ResultRowDef[] = [
  { key: 'hp', label: '生命值', main: true },
  { key: 'atk', label: '攻击力', main: true },
  { key: 'penforce', label: '贯穿力', main: true, ruptureOnly: true },
  { key: 'actual_cr', label: '实际暴击率', main: true, fengyuOnly: true },
  { key: 'blast_dmg', label: '锐暴伤害', main: true, fengyuOnly: true, unit: '%' },
  { key: 'def', label: '防御力', main: true },
  { key: 'cr', label: '暴击率' },
  { key: 'cd', label: '暴击伤害' },
  { key: 'dmg', label: '增伤' },
  { key: 'pr', label: '穿透率' },
  { key: 'pv', label: '穿透值' },
  { key: 'am', label: '异常精通' },
  { key: 'ac', label: '异常掌控' },
  { key: 'imp', label: '冲击力' },
  { key: 'er', label: '能量回复' },
];

/**
 * 命破与锋御专属行的显隐。
 *
 * 第 1 步只读取 `panelStore.panelMode` 的声明式默认值 `standard`，
 * 因此渲染出 12 行通用结果；第 2 步由 `applyAgentPreset` 写入实际模式，
 * 无需改动本组件。第 3 步改由后端响应的 panelMode 驱动。
 */
const panel = usePanelStore();

const visibleRows = computed(() =>
  ROWS.filter((row) => {
    if (row.ruptureOnly) {
      return panel.panelMode === 'rupture';
    }
    if (row.fengyuOnly) {
      return panel.panelMode === 'fengyu';
    }
    return true;
  }),
);
</script>

<template>
  <aside class="result">
    <div class="result-module">
      <h2>最终面板</h2>

      <div
        v-for="row in visibleRows"
        :key="row.key"
        class="r-row"
        :class="{ 'r-row--main': row.main }"
      >
        <span class="r-label">{{ row.label }}</span>
        <div class="r-cell">
          <!-- TODO(第 2 步)：值改为 result[row.key] + row.unit，明细改为 result breakdown 的 v-html -->
          <span class="r-value">—</span>
          <span class="breakdown" />
        </div>
      </div>
    </div>
  </aside>
</template>