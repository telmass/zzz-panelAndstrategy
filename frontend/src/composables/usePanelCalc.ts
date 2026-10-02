import { computed } from 'vue';

import {
  CORE_OPTIONS,
  DISC4_OPTIONS,
  DISC5_OPTIONS,
  DISC6_OPTIONS,
  DISC_FIXED_STATS,
  FENGYU_BLAST_DMG,
  SET_OPTIONS,
  SUB_STATS,
} from '@/constants/calculatorOptions';
import { WEAPON_PRESETS } from '@/data/weaponPresets';
import { displayEnergyAttributeLabel } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import type {
  ModifierSources,
  ModifierSum,
  PanelResult,
  ResultValue,
} from '@/types/panel';
import type { RuleOption } from '@/constants/calculatorOptions';
import { escapeHtml, fmt } from '@/utils/fmt';

/**
 * 面板计算。逐条移植 legacy/scripts/calculator.js 的 `calc()`，
 * 输出值与明细文案与旧页面逐字符一致——第 3 步下沉 Python 后，
 * `tests/legacy-parity.spec.ts` 负责守住这一等价性。
 *
 * 本步只做计算，不含任何 DOM 操作或事件绑定。
 */

/** 按 id 查选项，未选中返回 undefined。 */
function optionById(options: RuleOption[], id: string): RuleOption | undefined {
  if (!id) {
    return undefined;
  }
  return options.find((option) => option.id === id);
}

/**
 * 累加一个修正量并记录来源。
 *
 * 对应 legacy 的 `add`：值为 undefined 或 0 时直接跳过，
 * 避免明细中出现无意义的「+0」来源。
 */
function createAccumulator() {
  const sum: ModifierSum = {};
  const sources: ModifierSources = {};

  function add(key: string, value: number | undefined, label: string): void {
    if (value === undefined || value === 0) {
      return;
    }
    sum[key] = (sum[key] ?? 0) + value;
    if (label) {
      sources[key] = (sources[key] ?? []).concat(label);
    }
  }

  return { sum, sources, add };
}

/** 来源数组拼成明细文本，空数组显示「无」。对应 legacy 的 `j`。 */
function joinSources(items: string[] | undefined): string {
  if (!items || items.length === 0) {
    return '无';
  }
  return items
    .map((value) => `<span class="breakdown-item">${escapeHtml(value.replace(/ ([0-9])/g, '\u00a0$1'))}</span>`)
    .join(' + ');
}

/** 固定主词条的明细文案。对应 legacy 的 `fixedBreakdown`。 */
function fixedBreakdown(main: number, sub: number, mainLabel: string): string {
  return `${fmt(main)}（${mainLabel}）+${fmt(sub)}（副词条）`;
}

/** 结果行构造器。 */
function row(value: string, breakdown: string): ResultValue {
  return { value, breakdown };
}

export function usePanelCalc() {
  const panel = usePanelStore();

  /**
   * 完整面板计算。返回的结果同时包含 12~15 行，
   * 由 `ResultPanel` 按当前面板模式决定展示哪些。
   */
  const result = computed<PanelResult>(() => {
    const mode = panel.panelMode;
    /** 按当前模式替换能量类文案，与 legacy 的 displayEnergyAttributeLabel 默认参数一致。 */
    const label = (text: string) => displayEnergyAttributeLabel(text, mode);

    // 1. 基础面板
    const { base, weapon, core, discMain, subStats, setEffects } = panel;

    // 2. 音擎：锋御音擎提供基础防御力，其余提供基础攻击力
    const weaponPreset = WEAPON_PRESETS.find((item) => item.id === weapon.preset);
    const weaponBaseKind = weaponPreset ? (weaponPreset.baseKind ?? 'atk') : 'atk';
    const wAtk = weaponPreset && weaponBaseKind === 'atk' ? weapon.baseValue : 0;
    const wDef = weaponPreset && weaponBaseKind === 'def' ? weapon.baseValue : 0;
    const wSubVal = weapon.subValue;

    const { sum: S, sources: src, add } = createAccumulator();

    // 3. 核心（2 选）
    const corePicks = [
      optionById(CORE_OPTIONS, core.core1),
      optionById(CORE_OPTIONS, core.core2),
    ];

    const coreLabels: string[] = [];
    corePicks.forEach((option, index) => {
      if (!option) {
        return;
      }
      const text = `核心${index + 1}(${label(option.label)})`;
      coreLabels.push(text);
      add(option.to, option.value, text);
    });

    // 音擎固定副词条
    if (weaponPreset && wSubVal) {
      add(
        weaponPreset.substat.to,
        wSubVal,
        `音擎固定副词条(${label(weaponPreset.substat.label)} ${wSubVal}${weaponPreset.substat.kind === 'pct' ? '%' : ''})`,
      );
    }

    // 驱动盘 1/2/3 号固定
    DISC_FIXED_STATS.forEach((stat) => {
      add(stat.to, stat.value, `${stat.slot}号固定${stat.label}+${stat.value}`);
    });

    // 4/5/6 号主词条
    const d4 = optionById(DISC4_OPTIONS, discMain.disc4);
    const d5 = optionById(DISC5_OPTIONS, discMain.disc5);
    const d6 = optionById(DISC6_OPTIONS, discMain.disc6);
    if (d4) add(d4.to, d4.value, `4号(${d4.label})`);
    if (d5) add(d5.to, d5.value, `5号(${d5.label})`);
    if (d6) add(d6.to, d6.value, `6号(${label(d6.label)})`);

    // 副词条：按条数 × 单条数值
    const subFixed = { hp_flat: 0, atk_flat: 0, def_flat: 0 };
    for (const stat of SUB_STATS) {
      const count = Math.max(0, Math.floor(subStats[stat.id] ?? 0));
      const value = count * stat.value;
      if (count > 0) {
        add(stat.to, value, `副词条·${stat.label}×${count}=${fmt(value)}${stat.kind === 'pct' ? '%' : ''}`);
        if (stat.to in subFixed) {
          subFixed[stat.to as keyof typeof subFixed] += value;
        }
      }
    }

    // 二件套（0~3 组）
    ([setEffects.set0, setEffects.set1, setEffects.set2] as const).forEach((id) => {
      const option = optionById(SET_OPTIONS, id);
      if (option) {
        add(option.to, option.value, `2件套·${label(option.label)}`);
      }
    });

    // ====== 最终面板 ======
    // 攻防血：(基础 + 核心基础值 + 音擎基础值) × (1 + 百分比) + 固定值
    const atkBase = base.atk + (S.atk_base ?? 0) + wAtk;
    const defBase = base.def + (S.def_base ?? 0) + wDef;
    const hpBase = base.hp + (S.hp_base ?? 0);

    const totalHp = hpBase * (1 + (S.hp_pct ?? 0) / 100) + (S.hp_flat ?? 0);
    const totalAtk = atkBase * (1 + (S.atk_pct ?? 0) / 100) + (S.atk_flat ?? 0);
    const totalDef = defBase * (1 + (S.def_pct ?? 0) / 100) + (S.def_flat ?? 0);
    const totalPenForce = 0.3 * totalAtk + 0.1 * totalHp;

    // 纯加法与乘法
    const totalCr = base.cr + (S.cr ?? 0);
    const totalCd = base.cd + (S.cd ?? 0);
    const actualCr = totalCd * 0.35 + totalCr;
    /** 锋御固有属性，非锋御模式不参与计算也不展示。 */
    const blastDmg = mode === 'fengyu' ? FENGYU_BLAST_DMG : null;
    const totalDmg = S.dmg ?? 0;
    const totalPr = base.pr + (S.pr ?? 0);
    const totalPv = S.pen_val ?? 0;
    const totalAm = base.am + (S.am ?? 0);
    const totalAc = (base.ac + (S.ac_flat ?? 0)) * (1 + (S.ac_pct ?? 0) / 100);
    const totalImp = (base.impact + (S.impact_flat ?? 0)) * (1 + (S.impact_pct ?? 0) / 100);
    const totalEr = (base.er + (S.er_flat ?? 0)) * (1 + (S.er_pct ?? 0) / 100);

    // 明细片段
    const hpPctText = `<span class="kw">${fmt(S.hp_pct ?? 0)}%</span>`;
    const atkPctText = `<span class="kw">${fmt(S.atk_pct ?? 0)}%</span>`;
    const defPctText = `<span class="kw">${fmt(S.def_pct ?? 0)}%</span>`;
    const acPctText = `<span class="kw">${fmt(S.ac_pct ?? 0)}%</span>`;
    const impactPctText = `<span class="kw">${fmt(S.impact_pct ?? 0)}%</span>`;
    const erPctText = `<span class="kw">${fmt(S.er_pct ?? 0)}%</span>`;

    const output: PanelResult = {
      hp: row(
        fmt(totalHp),
        `<span class="breakdown-line">(${fmt(base.hp)}${S.hp_base ? `+核心${fmt(S.hp_base)}` : ''})×(1+${hpPctText})</span>` +
          `<span class="breakdown-line">+${fixedBreakdown(DISC_FIXED_STATS[0].value, subFixed.hp_flat, '1号主词条')} = <b>${fmt(totalHp)}</b></span>`,
      ),
      atk: row(
        fmt(totalAtk),
        `<span class="breakdown-line">(${fmt(base.atk)}${S.atk_base ? `+核心${fmt(S.atk_base)}` : ''}+音擎${fmt(wAtk)})</span>` +
          `<span class="breakdown-line">×(1+${atkPctText})+${fixedBreakdown(DISC_FIXED_STATS[1].value, subFixed.atk_flat, '2号主词条')} = <b>${fmt(totalAtk)}</b></span>`,
      ),
      penforce: row(
        fmt(totalPenForce),
        `<span class="breakdown-line">0.3×${fmt(totalAtk)} + 0.1×${fmt(totalHp)}</span>` +
          `<span class="breakdown-line">= <b>${fmt(totalPenForce)}</b></span>`,
      ),
      actual_cr: row(
        `${fmt(actualCr)}%`,
        `<span class="breakdown-line">${fmt(totalCd)}%×35% + ${fmt(totalCr)}%</span>` +
          `<span class="breakdown-line">= <b>${fmt(actualCr)}%</b></span>`,
      ),
      blast_dmg: row(
        blastDmg === null ? '—' : `${fmt(blastDmg)}%`,
        blastDmg === null
          ? ''
          : '<span class="breakdown-line">固有属性，不受词条、音擎与套装影响</span>' +
            `<span class="breakdown-line">= <b>${fmt(blastDmg)}%</b></span>`,
      ),
      def: row(
        fmt(totalDef),
        `<span class="breakdown-line">(${fmt(base.def)}${S.def_base ? `+核心${fmt(S.def_base)}` : ''}+音擎${fmt(wDef)})</span>` +
          `<span class="breakdown-line">×(1+${defPctText})+${fixedBreakdown(DISC_FIXED_STATS[2].value, subFixed.def_flat, '3号主词条')} = <b>${fmt(totalDef)}</b></span>`,
      ),
      cr: row(`${fmt(totalCr)}%`, `${fmt(base.cr)}% + ${joinSources(src.cr)} = ${fmt(totalCr)}%`),
      cd: row(`${fmt(totalCd)}%`, `${fmt(base.cd)}% + ${joinSources(src.cd)} = ${fmt(totalCd)}%`),
      dmg: row(`${fmt(totalDmg)}%`, `${joinSources(src.dmg)} = ${fmt(totalDmg)}%`),
      pr: row(`${fmt(totalPr)}%`, `${fmt(base.pr)}% + ${joinSources(src.pr)} = ${fmt(totalPr)}%`),
      pv: row(fmt(totalPv), `${joinSources(src.pen_val)} = ${fmt(totalPv)}`),
      am: row(
        fmt(totalAm),
        `${base.am ? `基础${fmt(base.am)} + ` : ''}${joinSources(src.am)} = ${fmt(totalAm)}`,
      ),
      ac: row(
        fmt(totalAc),
        `<span class="breakdown-line">(${joinSources([`基础${fmt(base.ac)}`, ...(src.ac_flat ?? [])])})×(1+${acPctText})</span>` +
          `<span class="breakdown-line">${joinSources(src.ac_pct)} = <b>${fmt(totalAc)}</b></span>`,
      ),
      imp: row(
        fmt(totalImp),
        `<span class="breakdown-line">(${joinSources([`基础${fmt(base.impact)}`, ...(src.impact_flat ?? [])])})×(1+${impactPctText})</span>` +
          `<span class="breakdown-line">${joinSources(src.impact_pct)} = <b>${fmt(totalImp)}</b></span>`,
      ),
      er: row(
        fmt(totalEr),
        `<span class="breakdown-line">(${joinSources([`基础${fmt(base.er)}`, ...(src.er_flat ?? [])])})×(1+${erPctText})</span>` +
          `<span class="breakdown-line">${joinSources(src.er_pct)} = <b>${fmt(totalEr)}</b></span>`,
      ),
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

  return { result, coreSummary };
}