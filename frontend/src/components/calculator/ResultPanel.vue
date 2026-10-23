<script setup lang="ts">
import { computed, ref } from 'vue';
import { NPopconfirm } from 'naive-ui';

import { usePanelCalc } from '@/composables/usePanelCalc';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { useBuildStore } from '@/stores/buildStore';
import { applyBuild, currentBuild } from '@/composables/useBuildPanel';
import {
  buildShareUrl,
  exportBuildToFile,
  importBuildFromFile,
  writeBuildToHash,
} from '@/composables/useBuildIO';
import { usePresetStore } from '@/stores/presetStore';
import type { ResultRow } from '@/types/panel';

/**
 * 最终面板。对应 legacy 的 `.result` + `.result-module`。
 *
 * 行顺序、标签与主属性标记对齐 legacy/calculator.html 的 15 行结果区，
 * 命破与锋御专属行通过 `ruptureOnly` / `armorerOnly` 标注显隐条件。
 *
 * 数值来自后端（`usePanelCalc` 经 `src/api/panel.ts` 拉取，200ms 防抖），
 * 明细由后端给的结构化片段在 `usePanelCalc` 内渲染成 HTML——仍用 `v-html`，
 * 以保证下沉前后与旧页面逐字符一致。
 *
 * 头部两个按钮是攻略页同款排版的一部分（板块标题右侧放操作）：
 *   - 复制结果：把当前可见行拼成纯文本写入剪贴板，便于贴到群里问配装；
 *   - 重置：一键清空全部输入（`panelStore.resetAll`）。**破坏性操作**，
 *     因此与「复制」样式区分，并加二次确认——一次误点会丢掉整套配装。
 *
 * 状态行说明「下面这列数字是谁的」：没载入代理人时显示的是通用默认值，
 * 容易被误读成某位代理人的真实面板。
 */
interface ResultRowDef extends ResultRow {
  /** 标签随面板模式在「能量回复 / 锐能自动累积」之间切换。 */
  energyLabel?: boolean;
}

const ROWS: ResultRowDef[] = [
  { key: 'hp', label: '生命值', main: true },
  { key: 'atk', label: '攻击力', main: true },
  { key: 'penforce', label: '贯穿力', main: true, ruptureOnly: true },
  { key: 'actual_cr', label: '实际暴击率', main: true, armorerOnly: true },
  { key: 'blast_dmg', label: '锐暴伤害', main: true, armorerOnly: true },
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
const { showRuptureResult, showarmorerResult, energyResultLabel } = usePanelMode();

/* ====== 配装方案的存取 ====== */

const buildStore = useBuildStore();
const presetStore = usePresetStore();

/** 已保存的方案（本地 localStorage）。 */
const savedBuilds = computed(() => buildStore.builds);

/** 选中的方案下标。 */
const selectedBuild = ref('');

/** 操作提示（成功 / 失败）。 */
const buildHint = ref('');

/** 隐藏的文件输入框——「导入」按钮点它。 */
const fileInput = ref<HTMLInputElement | null>(null);

buildStore.load();

/** 方案的默认名字：代理人名 + 「方案」。 */
function defaultBuildName(): string {
  const agent = presetStore.agentById.get(panel.agent.presetId);
  return agent ? `${agent.name} 方案` : '我的配装';
}

/** 保存当前配装为本机方案。 */
function saveCurrentBuild(): void {
  const name = defaultBuildName();
  buildStore.save(currentBuild(name));
  buildHint.value = `已保存方案“${name}”。`;
  selectedBuild.value = '0';
}

/** 导出当前配装为文件。 */
function exportCurrentBuild(): void {
  exportBuildToFile(currentBuild(defaultBuildName()));
  buildHint.value = '已导出配装文件。';
}

/** 导入配装文件。 */
async function onFilePicked(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (!file) return;
  try {
    const preset = await importBuildFromFile(file);
    const result = applyBuild(preset);
    buildHint.value = result.message;
  } catch (error) {
    buildHint.value = error instanceof Error ? error.message : '导入失败。';
  }
}

/** 载入选中的方案。 */
function loadSelectedBuild(): void {
  const index = Number(selectedBuild.value);
  const preset = savedBuilds.value[index];
  if (!preset) return;
  const result = applyBuild(preset);
  buildHint.value = result.message;
}

/** 删掉选中的方案。 */
function removeSelectedBuild(): void {
  const index = Number(selectedBuild.value);
  const preset = savedBuilds.value[index];
  if (!preset) return;
  buildStore.remove(preset.name, preset.agentId);
  selectedBuild.value = '';
  buildHint.value = `已删除方案“${preset.name}”。`;
}

/** 复制一条能复现当前配装的链接。 */
async function copyBuildLink(): Promise<void> {
  const url = buildShareUrl(currentBuild(defaultBuildName()));
  writeBuildToHash(currentBuild(defaultBuildName()));
  try {
    await navigator.clipboard.writeText(url);
    buildHint.value = '已复制配装链接。';
  } catch {
    buildHint.value = '配装链接已写进地址栏，可以直接复制。';
  }
}

/** 按当前面板模式筛选可见行，并替换随模式变化的标签。 */
const visibleRows = computed(() =>
  ROWS.filter((row) => {
    if (row.ruptureOnly) {
      return showRuptureResult.value;
    }
    if (row.armorerOnly) {
      return showarmorerResult.value;
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

/**
 * 状态行：说明下面这列数字是谁的。
 *
 * 未载入代理人时，面板里那 12 行是**通用默认值**（生命 8000 / 攻击 1000 …），
 * 不是任何代理人的真实面板——不说清楚很容易被当成结果读走。
 */
const statusText = computed(() => {
  const agent = panel.selectedAgent?.name;
  if (!agent) {
    return '未载入代理人 · 下列为通用默认值';
  }
  return `已载入 ${agent}`;
});

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
          <n-popconfirm
            positive-text="重置"
            negative-text="取消"
            @positive-click="resetPanel"
          >
            <template #trigger>
              <button class="result-action result-action--danger" type="button">重置</button>
            </template>
            会清空代理人、音擎与全部词条选择，确定重置？
          </n-popconfirm>
        </div>
      </div>
      <p class="result-status">{{ statusText }}</p>
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

      <!-- 配装方案的存取。方案是**本地数据**（localStorage / 文件 / 链接），
           不落服务端——站点公开、无鉴权，没有可写的服务端数据面。 -->
      <div class="result-builds">
        <div class="result-builds__row">
          <button class="result-build-action" type="button" @click="saveCurrentBuild">保存方案</button>
          <button class="result-build-action" type="button" @click="exportCurrentBuild">导出</button>
          <button class="result-build-action" type="button" @click="fileInput?.click()">导入</button>
          <button class="result-build-action" type="button" @click="copyBuildLink">复制链接</button>
          <input
            ref="fileInput"
            class="result-builds__file"
            type="file"
            accept="application/json,.json"
            @change="onFilePicked"
          />
        </div>
        <div v-if="savedBuilds.length" class="result-builds__row">
          <select v-model="selectedBuild" class="result-builds__select">
            <option value="">选择一个已存方案</option>
            <option v-for="(build, index) in savedBuilds" :key="index" :value="String(index)">
              {{ build.name }}
            </option>
          </select>
          <button
            class="result-build-action"
            type="button"
            :disabled="selectedBuild === ''"
            @click="loadSelectedBuild"
          >
            载入
          </button>
          <button
            class="result-build-action result-build-action--danger"
            type="button"
            :disabled="selectedBuild === ''"
            @click="removeSelectedBuild"
          >
            删除
          </button>
        </div>
        <p v-if="buildHint" class="result-hint" role="status">{{ buildHint }}</p>
      </div>
    </div>
  </aside>
</template>
