/**
 * 学习页（`/guide`）的**数值表**——从规则表派生，不手写。
 *
 * 为什么要派生
 * ------------
 * 这三张表（4/5/6 号位主词条、副词条单条数值、2 件套效果）此前是**手写**在
 * ``GuideView.vue`` 里的，于是它们会与规则表**漂移**——6 号位「冲击力」从 24%
 * 改成 18%、5 号位「增伤」正名为「属性伤害」时，这三张表都跟着错了，
 * 要靠人工记得同步。
 *
 * 现在数值一律来自 ``data/rules/calculator-rules.json``（其真源是
 * ``backend/src/zzz_panel/core/options.py``），**手写的地方只留解释性文案**。
 */

import rules from '@data/rules/calculator-rules.json';
import {
  MAIN_STAT_OPTION_ID_TO_EXCLUDED_SUB_STAT,
  SUB_STATS,
} from '@/constants/calculatorOptions';

/** 一行「数值 + 说明」表。 */
export interface GuideNumberRow {
  /** 规则表里的选项 id（副词条要靠它查互斥关系）。 */
  id?: string;
  /** 展示名（规则表的规范名）。 */
  name: string;
  /** 数值文本（带 % 或不带，由 kind 决定）。 */
  value: string;
  /** 百分比 / 固定值 / 数值型。 */
  kind: string;
}

function formatValue(value: number, kind: string): string {
  if (kind === 'pct') return `+${value}%`;
  return `+${value}`;
}

function kindLabel(kind: string): string {
  if (kind === 'pct') return '百分比';
  return '固定值';
}

/** 1/2/3 号固定主词条。 */
export const FIXED_MAIN_STATS: GuideNumberRow[] = rules.discFixedStats.map((stat) => ({
  name: stat.name,
  value: `+${stat.value}`,
  kind: '固定值',
}));

/** 4 / 5 / 6 号位的主词条选项。 */
export const MAIN_STAT_OPTIONS: Record<'disc4' | 'disc5' | 'disc6', GuideNumberRow[]> = {
  disc4: rules.disc4Options.map((o) => ({
    name: o.name,
    value: formatValue(o.value, o.kind),
    kind: kindLabel(o.kind),
  })),
  disc5: rules.disc5Options.map((o) => ({
    name: o.name,
    value: formatValue(o.value, o.kind),
    kind: kindLabel(o.kind),
  })),
  disc6: rules.disc6Options.map((o) => ({
    name: o.name,
    value: formatValue(o.value, o.kind),
    kind: kindLabel(o.kind),
  })),
};

/** 副词条的**单条数值**（10 种）。 */
export const SUB_STAT_ROWS: GuideNumberRow[] = rules.subStats.map((option) => ({
  id: option.id,
  name: option.name,
  value: formatValue(option.value, option.kind),
  kind: kindLabel(option.kind),
}));

/**
 * 副词条与「哪个主词条同名」的对应——由**主副互斥表**派生。
 *
 * 互斥表在规则表里（``mainStatExcludes``），不是手写的。
 */
export const SUB_STAT_SLOT_NOTE: Record<string, string> = (() => {
  const notes: Record<string, string> = {};
  for (const substat of SUB_STATS) {
    const fixed = rules.discFixedStats.find((stat) => stat.to === substat.id);
    if (fixed) {
      notes[substat.id] = `${fixed.slot}号主词条，主副不重复`;
      continue;
    }
    const slots: string[] = [];
    for (const [slot, options] of [
      ['4', rules.disc4Options],
      ['5', rules.disc5Options],
      ['6', rules.disc6Options],
    ] as const) {
      if (options.some((o) => MAIN_STAT_OPTION_ID_TO_EXCLUDED_SUB_STAT[o.id] === substat.id)) {
        slots.push(`${slot}号`);
      }
    }
    notes[substat.id] = slots.length
      ? `${slots.join('/')}可选`
      : '不在主词条（5号是穿透率）';
  }
  return notes;
})();

/** 某个主词条选项的数值文本（供示例正文引用，避免行内数字漂移）。 */
export function mainStatValue(slot: 'disc4' | 'disc5' | 'disc6', optionId: string): string {
  const found = MAIN_STAT_OPTIONS[slot].find((option) => option.name === optionId);
  return found ? found.value : optionId;
}

/** 2 件套效果。 */
export const SET_OPTION_ROWS: GuideNumberRow[] = rules.setOptions.map((option) => ({
  id: option.id,
  name: option.name,
  value: formatValue(option.value, option.kind),
  kind: kindLabel(option.kind),
}));
