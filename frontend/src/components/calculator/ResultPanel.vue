<script setup lang="ts">
import { computed, ref } from 'vue';

import { usePanelCalc } from '@/composables/usePanelCalc';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import type { ResultRow } from '@/types/panel';

/**
 * 最终面板。对应 legacy 的 `.result` + `.result-module`。
 *
 * 行顺序、标签与主属性标记对齐 legacy/calculator.html 的 15 行结果区，
 * 命破与锋御专属行通过 `ruptureOnly` / `fengyuOnly` 标注显隐条件。
 *
 * 数值来自后端（`usePanelCalc` 经 `src/api/panel.ts` 拉取，200ms 防抖），
 * 明细由后端给的结构化片段在 `usePanelCalc` 内渲染成 HTML——仍用 `v-html`，
 * 以保证下沉前后与旧页面逐字符一致。
 *
 * 头部两个按钮是攻略页同款排版的一部分（板块标题右侧放操作）：
 *   - 复制结果：把当前可见行拼成纯文本写入剪贴板，便于贴到群里问配装；
 *   - 重置：一键清空全部输入（`panelStore.resetAll`）。
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

const panel = usePanelStore();
const { result, pending, error } = usePanelCalc();
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

/** 复制按钮的瞬时反馈文案。空字符串表示不显示。 */
const copyHint = ref('');
let copyTimer: ReturnType<typeof setTimeout> | undefined;

/** 当前可见结果拼成纯文本，一行一项。 */
function resultText(): string {
  const agent = panel.selectedAgent?.name;
  const header = agent ? `【${agent}】最终面板` : '最终面板';
  const lines = visibleRows.value.map(
    (row) => `${row.label}：${result.value[row.key]?.value ?? '—'}`,
  );
  return [header, ...lines].join('\n');
}

async function copyResult(): Promise<void> {
  const text = resultText();
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      // 非安全上下文（http 局域网访问等）没有 clipboard API，退回选中复制
      const area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.opacity = '0';
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
    copyHint.value = '已复制';
  } catch {
    copyHint.value = '复制失败';
  }
  if (copyTimer !== undefined) {
    clearTimeout(copyTimer);
  }
  copyTimer = setTimeout(() => {
    copyHint.value = '';
    copyTimer = undefined;
  }, 1600);
}

function resetPanel(): void {
  panel.resetAll();
}
</script>

<template>
  <aside class="result">
    <div class="result-module">
      <div class="result-module__head">
        <h2>最终面板</h2>
        <div class="result-actions">
          <button class="result-action" type="button" @click="copyResult">复制结果</button>
          <button class="result-action" type="button" @click="resetPanel">重置</button>
        </div>
      </div>
      <p v-if="copyHint" class="result-hint" role="status">{{ copyHint }}</p>

      <!-- 第 3 步起结果来自后端，需要显式的计算中 / 失败反馈，
            否则服务不可用时只会静默显示一列「—」。 -->
      <p v-if="error" class="calc-error" role="alert">面板计算失败：{{ error }}</p>
      <p v-else-if="pending" class="calc-pending">计算中…</p>

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
