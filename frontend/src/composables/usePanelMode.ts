import { computed } from 'vue';

import { PANEL_MODE_LABELS } from '@/constants/calculatorOptions';
import { usePanelStore } from '@/stores/panelStore';
import type { PanelMode } from '@/types/panel';

/** 判断字符串是否为合法面板模式。 */
export function isPanelMode(value: string | null | undefined): value is PanelMode {
  return value !== null && value !== undefined && value !== '' && Object.hasOwn(PANEL_MODE_LABELS, value);
}

/**
 * 锋御模式文案替换。对应 legacy 的 `displayEnergyAttributeLabel`。
 *
 * 锋御代理人的能量类属性在面板上统一称为「锐能自动累积」，
 * 核心加成、驱动盘主词条与二件套的选项文案都需同步替换，
 * 否则会出现「锋御选了锐能，公式里却写能量」的不一致。
 *
 * 替换顺序不可调整：必须先替换更长的「基础能量自动回复」，
 * 否则会被「能量自动回复」的规则先吃掉。
 */
export function displayEnergyAttributeLabel(label: string, mode: PanelMode = 'standard'): string {
  if (mode !== 'fengyu') {
    return label;
  }
  return label
    .replaceAll('基础能量自动回复', '基础锐能自动累积')
    .replaceAll('能量自动回复', '锐能自动累积')
    .replaceAll('能量回复', '锐能自动累积');
}

/**
 * 面板模式相关的派生状态。对应 legacy 的 `updatePanelMode`、
 * `updateEnergyAttributeLabels` 与结果区的 `hidden` 控制。
 */
export function usePanelMode() {
  const panel = usePanelStore();
  const mode = computed(() => panel.panelMode);

  /** 结果区命破专属行（贯穿力）的显隐。 */
  const showRuptureResult = computed(() => mode.value === 'rupture');
  /** 结果区锋御专属行（实际暴击率、锐暴伤害）的显隐。 */
  const showFengyuResult = computed(() => mode.value === 'fengyu');

  /** 基础面板中穿透率字段的显隐：命破模式改用贯穿力，故隐藏。 */
  const showPenetrationInput = computed(() => mode.value !== 'rupture');
  /** 基础面板中能量回复字段的显隐：命破模式改用闪能自动累积，故隐藏。 */
  const showEnergyReplyInput = computed(() => mode.value !== 'rupture');
  /** 基础面板中基础贯穿力字段的显隐。 */
  const showPenforceInput = computed(() => mode.value === 'rupture');
  /** 基础面板中闪能自动累积字段的显隐。 */
  const showEnergyAccumulationInput = computed(() => mode.value === 'rupture');

  /**
   * 基础面板能量字段的标签。锋御模式显示「锐能自动累积」，
   * 其余显示 legacy 原有的「能量自动回复」。
   * 对应 legacy 的 `updateEnergyAttributeLabels`。
   */
  const energyInputLabel = computed(() =>
    mode.value === 'fengyu' ? '锐能自动累积' : '能量自动回复',
  );

  /** 结果区能量行的标签。对应 legacy 中 `能量回复` / `锐能自动累积` 的切换。 */
  const energyResultLabel = computed(() => (mode.value === 'fengyu' ? '锐能自动累积' : '能量回复'));

  /** 按当前模式替换文案，用于核心、驱动盘与二件套的选项标签。 */
  function localize(label: string): string {
    return displayEnergyAttributeLabel(label, mode.value);
  }

  return {
    showRuptureResult,
    showFengyuResult,
    showPenetrationInput,
    showEnergyReplyInput,
    showPenforceInput,
    showEnergyAccumulationInput,
    energyInputLabel,
    energyResultLabel,
    localize,
  };
}