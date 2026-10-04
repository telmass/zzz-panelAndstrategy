import { computed, onScopeDispose, ref, shallowRef, watch } from 'vue';

import { calcPanel, PanelApiError } from '@/api/panel';
import { CORE_OPTIONS } from '@/constants/calculatorOptions';
import { displayEnergyAttributeLabel } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
import type {
  BreakdownLine,
  BreakdownSegment,
  PanelApiResponse,
  PanelCalcRequest,
  PanelResult,
  ResultValue,
} from '@/types/panel';
import { escapeHtml, fmt } from '@/utils/fmt';

/**
 * 面板计算。第 3 步起**不再本地计算**：把配装选择发给后端，
 * 拿回最终数值与结构化明细，再在本文件渲染成与 legacy 逐字符一致的 HTML。
 *
 * 明细只由后端决定「有哪些行、每行有哪些片段、哪个值加粗」，
 * 本文件只负责把片段变成 HTML 字符串，因此展示层仍留在前端，
 * `tests/legacy-parity.spec.ts` 得以继续守住与旧页面的等价性。
 */

/** 防抖间隔。文档要求 150~300ms，取 200ms。 */
const CALC_DEBOUNCE_MS = 200;

/** 来源数组渲染成明细片段，对应 legacy 的 `joinSources`。 */
function renderSources(items: string[]): string {
  if (items.length === 0) {
    return '无';
  }
  return items
    .map(
      (value) =>
        `<span class="breakdown-item">${escapeHtml(value.replace(/ ([0-9])/g, '\u00a0$1'))}</span>`,
    )
    .join(' + ');
}

/** 单个片段渲染成 HTML。 */
function renderSegment(segment: BreakdownSegment): string {
  switch (segment.type) {
    case 'text':
      return escapeHtml(segment.text);
    case 'kw':
      return `<span class="kw">${escapeHtml(segment.text)}</span>`;
    case 'num': {
      // unit 必须渲染进 <b> 内部：legacy 是 `= <b>68.8%</b>`
      const text = `${fmt(segment.value)}${segment.unit}`;
      return segment.bold ? `<b>${text}</b>` : text;
    }
    case 'sources':
      return renderSources(segment.items);
    default:
      return '';
  }
}

/** 明细行渲染成 HTML。`wrapped` 决定是否套 `breakdown-line`。 */
function renderLine(line: BreakdownLine): string {
  const inner = line.parts.map(renderSegment).join('');
  return line.wrapped ? `<span class="breakdown-line">${inner}</span>` : inner;
}

/** 整个明细渲染成 HTML。 */
function renderBreakdown(lines: BreakdownLine[] | undefined): string {
  return (lines ?? []).map(renderLine).join('');
}

/** 按 id 查选项，未选中返回 undefined。 */
function optionById(options: typeof CORE_OPTIONS, id: string) {
  if (!id) {
    return undefined;
  }
  return options.find((option) => option.id === id);
}

/** 由 store 组装请求。只带选择，不带任何计算口径。 */
function buildRequest(): PanelCalcRequest {
  const panel = usePanelStore();
  const { base, weapon, core, discMain, subStats, setEffects } = panel;

  // 音擎的固定副词条已由预设解析出目标与数值，直接透传给后端。
  // ModifierKind 还有 'base'（核心专用），音擎副词条只有百分比与固定值两种。
  const preset = usePresetStore().weaponById.get(weapon.preset);
  const substat =
    preset && weapon.subValue
      ? {
          target: preset.substat.to,
          value: weapon.subValue,
          kind: preset.substat.kind === 'pct' ? ('pct' as const) : ('flat' as const),
          label: preset.substat.label,
        }
      : null;

  return {
    mode: panel.panelMode,
    base: {
      hp: base.hp,
      atk: base.atk,
      def: base.def,
      impact: base.impact,
      cr: base.cr,
      cd: base.cd,
      ac: base.ac,
      am: base.am,
      pr: base.pr,
      er: base.er,
    },
    weapon: {
      baseKind: preset ? (preset.baseKind ?? 'atk') : 'atk',
      baseValue: preset ? weapon.baseValue : 0,
      substat,
    },
    core: { core1: core.core1, core2: core.core2 },
    discMain: { disc4: discMain.disc4, disc5: discMain.disc5, disc6: discMain.disc6 },
    subStats: { ...subStats },
    sets: { set0: setEffects.set0, set1: setEffects.set1, set2: setEffects.set2 },
  };
}

export function usePanelCalc() {
  const panel = usePanelStore();

  /** 后端原始响应。`null` 表示尚未拿到首个结果。 */
  const response = shallowRef<PanelApiResponse | null>(null);
  /** 计算中标记，避免结果面板闪回旧值。 */
  const pending = ref(false);
  const error = ref<string | null>(null);

  let timer: ReturnType<typeof setTimeout> | undefined;
  /** 递增序号，丢弃过期响应，避免快速改动时旧结果覆盖新结果。 */
  let requestSeq = 0;

  function cancel(): void {
    if (timer !== undefined) {
      clearTimeout(timer);
      timer = undefined;
    }
  }

  async function run(request: PanelCalcRequest): Promise<void> {
    const seq = ++requestSeq;
    pending.value = true;
    try {
      const data = await calcPanel(request);
      if (seq !== requestSeq) {
        return;
      }
      response.value = data;
      error.value = null;
    } catch (cause) {
      if (seq !== requestSeq) {
        return;
      }
      error.value = cause instanceof PanelApiError ? cause.message : '面板计算服务不可用';
    } finally {
      if (seq === requestSeq) {
        pending.value = false;
      }
    }
  }

  /**
   * 任何影响计算的输入变化都触发一次防抖重算。
   * 监听整个 store 的深比较结果即可覆盖所有字段，避免逐个字段列举。
   */
  watch(
    () => JSON.stringify(buildRequest()),
    () => {
      cancel();
      // 一旦排上新的重算就立刻标记 pending：否则防抖窗口内（200ms）
      // 结果区毫无反馈，用户会以为输入没生效。
      pending.value = true;
      timer = setTimeout(() => {
        timer = undefined;
        void run(buildRequest());
      }, CALC_DEBOUNCE_MS);
    },
    { immediate: true },
  );

  onScopeDispose(cancel);

  /**
   * 最终面板结果。数值来自后端，明细由结构化片段渲染而成。
   * 键与 `ResultRow.key` 对齐，缺失的行回落到 `—` 占位。
   */
  const result = computed<PanelResult>(() => {
    const data = response.value;
    if (!data) {
      return {};
    }

    const { totals, modeStats, blastDmg } = data;
    const lines = data.breakdown;

    function row(key: string, text: string, unit = ''): ResultValue {
      return { value: `${text}${unit}`, breakdown: renderBreakdown(lines[key]) };
    }

    const output: PanelResult = {
      hp: row('hp', fmt(totals.hp)),
      atk: row('atk', fmt(totals.atk)),
      def: row('def', fmt(totals.def)),
      cr: row('cr', fmt(totals.cr), '%'),
      cd: row('cd', fmt(totals.cd), '%'),
      dmg: row('dmg', fmt(totals.dmg), '%'),
      pr: row('pr', fmt(totals.pr), '%'),
      pv: row('pv', fmt(totals.pv)),
      am: row('am', fmt(totals.am)),
      ac: row('ac', fmt(totals.ac)),
      imp: row('imp', fmt(totals.imp)),
      er: row('er', fmt(totals.er)),
    };

    if (modeStats.penforce !== undefined) {
      output.penforce = row('penforce', fmt(modeStats.penforce));
    }
    if (modeStats.actual_cr !== undefined) {
      output.actual_cr = row('actual_cr', fmt(modeStats.actual_cr), '%');
    }
    // 锐暴伤害是锋御固有属性：非锋御模式显示「—」且无明细
    output.blast_dmg = {
      value: blastDmg === null ? '—' : `${fmt(blastDmg)}%`,
      breakdown: blastDmg === null ? '' : renderBreakdown(lines.blast_dmg),
    };

    return output;
  });

  /**
   * 核心选择摘要。对应 legacy 的 `core_summary`。
   * 未选择时给出与 legacy 同色的警示文案。
   */
  const coreSummary = computed(() => {
    const mode = panel.panelMode;
    const picks = [optionById(CORE_OPTIONS, panel.core.core1), optionById(CORE_OPTIONS, panel.core.core2)];
    const labels = picks
      .map((option, index) =>
        option ? `核心${index + 1}(${displayEnergyAttributeLabel(option.label, mode)})` : '',
      )
      .filter(Boolean);
    return labels.length ? `已选：${labels.join('，')}` : '<span style="color:#dc2626">未选择核心</span>';
  });

  return { result, coreSummary, pending, error };
}
