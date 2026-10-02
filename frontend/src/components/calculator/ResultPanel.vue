<script setup lang="ts">
import { computed } from 'vue';

import { usePanelCalc } from '@/composables/usePanelCalc';
import { usePanelMode } from '@/composables/usePanelMode';
import type { ResultRow } from '@/types/panel';

/**
 * 最终面板。对应 legacy 的 `.result` + `.result-module`。
 *
 * 行顺序、标签与主属性标记对齐 legacy/calculator.html 的 15 行结果区，
 * 命破与锋御专属行通过 `ruptureOnly` / `fengyuOnly` 标注显隐条件。
 *
 * 数值与明细由 `usePanelCalc` 派生。沿用 legacy 的 innerHTML 写法，
 * 以保证第 3 步下沉 Python 前后与旧页面逐字符一致。
 */
interface ResultRowDef extends ResultRow {
  /** 标签随面板模式在「能量回复 / 锐能自动累积」之间切换。 */
  energyLabel?: boolean;
}

const ROWS: ResultRowDef[] = [
  { key: 'hp', label: '生命值', main: true },
  { key: 'atk', label: '攻击力', main: true },
  { key: 'penforce', label: '贯穿力', main: true, ruptureOnly: true },
  { key: 'actual_cr', label: '实际暴击率', main: true, fengyuOnly: true },
  { key: 'blast_dmg', label: '锐暴伤害', main: true, fengyuOnly: true },
  { key: 'def', label: '防御力', main: true },
  { key: 'cr', label: '暴击率' },
  { key: 'cd', label: '暴击伤害' },
  { key: 'dmg', label: '增伤' },
  { key: 'pr', label: '穿透率' },
  { key: 'pv', label: '穿透值' },
  { key: 'am', label: '异常精通' },
  { key: 'ac', label: '异常掌控' },
  { key: 'imp', label: '冲击力' },
  { key: 'er', label: '能量回复', energyLabel: true },
];

const { result } = usePanelCalc();
const { showRuptureResult, showFengyuResult, energyResultLabel } = usePanelMode();

/** 按当前面板模式筛选可见行，并替换随模式变化的标签。 */
const visibleRows = computed(() =>
  ROWS.filter((row) => {
    if (row.ruptureOnly) {
      return showRuptureResult.value;
    }
    if (row.fengyuOnly) {
      return showFengyuResult.value;
    }
    return true;
  }).map((row) => ({
    ...row,
    label: row.energyLabel ? energyResultLabel.value : row.label,
  })),
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
          <span class="r-value">{{ result[row.key]?.value ?? '—' }}</span>
          <span class="breakdown" v-html="result[row.key]?.breakdown ?? ''" />
        </div>
      </div>
    </div>
  </aside>
</template>