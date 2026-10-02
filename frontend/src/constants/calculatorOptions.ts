/**
 * 配装规则常量。取值逐条对齐 `legacy/scripts/calculator-config.js`，
 * 是第 2 步前端计算的口径来源；第 3 步下沉到 `backend/core/constants.py`
 * 与 `core/modifiers.py` 后改为由后端下发。
 *
 * `id` 为选项标识，`value` 为加成数值，`kind` 决定明细中的单位后缀，
 * `to` 指明该加成累加到哪个修正量。
 */

/** 可被配装修正的量。与 `usePanelCalc` 的累加器一一对应。 */
export type ModifierKey =
  | 'hp_pct'
  | 'atk_pct'
  | 'def_pct'
  | 'hp_flat'
  | 'atk_flat'
  | 'def_flat'
  | 'hp_base'
  | 'atk_base'
  | 'def_base'
  | 'cr'
  | 'cd'
  | 'dmg'
  | 'pr'
  | 'pen_val'
  | 'am'
  | 'ac_flat'
  | 'ac_pct'
  | 'impact_flat'
  | 'impact_pct'
  | 'er_flat'
  | 'er_pct';

/** 加成种类。`base` 进入基础面板参与乘法，`pct` 带 % 参与乘法，其余为纯加法。 */
export type ModifierKind = 'base' | 'pct' | 'flat';

/** 一条配装规则。 */
export interface RuleOption {
  id: string;
  label: string;
  value: number;
  kind: ModifierKind;
  to: ModifierKey;
}

/** 核心加成 9 项（可重复选取，实际出现 12 个条目）。 */
export const CORE_OPTIONS: RuleOption[] = [
  { id: 'er_base', label: '基础能量自动回复 +0.36', value: 0.36, kind: 'flat', to: 'er_flat' },
  { id: 'atk_base', label: '基础攻击力 +75', value: 75, kind: 'base', to: 'atk_base' },
  { id: 'impact_base', label: '基础冲击力 +18', value: 18, kind: 'flat', to: 'impact_flat' },
  { id: 'cd', label: '暴击伤害 +28.8%', value: 28.8, kind: 'pct', to: 'cd' },
  { id: 'cr', label: '暴击率 +14.4%', value: 14.4, kind: 'pct', to: 'cr' },
  { id: 'hp_pct', label: '生命值百分比 +18%', value: 18, kind: 'pct', to: 'hp_pct' },
  { id: 'hp_base', label: '基础生命值 +420', value: 420, kind: 'base', to: 'hp_base' },
  { id: 'ac', label: '异常掌控 +36', value: 36, kind: 'flat', to: 'ac_flat' },
  { id: 'am', label: '异常精通 +54', value: 54, kind: 'flat', to: 'am' },
  { id: 'pr', label: '穿透率 +14.4%', value: 14.4, kind: 'pct', to: 'pr' },
  { id: 'am_90', label: '异常精通 +90', value: 90, kind: 'flat', to: 'am' },
  { id: 'atk_pct_21', label: '攻击力 +21%', value: 21, kind: 'pct', to: 'atk_pct' },
];

/** 4 号主词条，6 选 1。 */
export const DISC4_OPTIONS: RuleOption[] = [
  { id: 'atk_pct_30', label: '攻击力 30%', value: 30, kind: 'pct', to: 'atk_pct' },
  { id: 'hp_pct_30', label: '生命值 30%', value: 30, kind: 'pct', to: 'hp_pct' },
  { id: 'def_pct_48', label: '防御力 48%', value: 48, kind: 'pct', to: 'def_pct' },
  { id: 'cr_24', label: '暴击率 24%', value: 24, kind: 'pct', to: 'cr' },
  { id: 'cd_48', label: '暴击伤害 48%', value: 48, kind: 'pct', to: 'cd' },
  { id: 'am_92', label: '异常精通 92', value: 92, kind: 'flat', to: 'am' },
];

/** 5 号主词条，5 选 1。 */
export const DISC5_OPTIONS: RuleOption[] = [
  { id: 'atk_pct_30', label: '攻击力 30%', value: 30, kind: 'pct', to: 'atk_pct' },
  { id: 'hp_pct_30', label: '生命值 30%', value: 30, kind: 'pct', to: 'hp_pct' },
  { id: 'def_pct_48', label: '防御力 48%', value: 48, kind: 'pct', to: 'def_pct' },
  { id: 'pr_24', label: '穿透率 24%', value: 24, kind: 'pct', to: 'pr' },
  { id: 'dmg_30', label: '增伤 30%', value: 30, kind: 'pct', to: 'dmg' },
];

/** 6 号主词条，6 选 1。 */
export const DISC6_OPTIONS: RuleOption[] = [
  { id: 'atk_pct_30', label: '攻击力 30%', value: 30, kind: 'pct', to: 'atk_pct' },
  { id: 'hp_pct_30', label: '生命值 30%', value: 30, kind: 'pct', to: 'hp_pct' },
  { id: 'def_pct_48', label: '防御力 48%', value: 48, kind: 'pct', to: 'def_pct' },
  { id: 'impact_pct_24', label: '冲击力 24%', value: 24, kind: 'pct', to: 'impact_pct' },
  { id: 'ac_pct_30', label: '异常掌控 30%', value: 30, kind: 'pct', to: 'ac_pct' },
  { id: 'er_pct_60', label: '能量回复 60%', value: 60, kind: 'pct', to: 'er_pct' },
];

/** 二件套效果 10 种。 */
export const SET_OPTIONS: RuleOption[] = [
  { id: 'hp_pct_10', label: '生命 +10%', value: 10, kind: 'pct', to: 'hp_pct' },
  { id: 'atk_pct_10', label: '攻击力 +10%', value: 10, kind: 'pct', to: 'atk_pct' },
  { id: 'def_pct_10', label: '防御力 +10%', value: 10, kind: 'pct', to: 'def_pct' },
  { id: 'cr_8', label: '暴击率 +8%', value: 8, kind: 'pct', to: 'cr' },
  { id: 'cd_16', label: '暴击伤害 +16%', value: 16, kind: 'pct', to: 'cd' },
  { id: 'impact_pct_6', label: '冲击力 +6%', value: 6, kind: 'pct', to: 'impact_pct' },
  { id: 'ac_pct_8', label: '异常掌控 +8%', value: 8, kind: 'pct', to: 'ac_pct' },
  { id: 'er_pct_20', label: '能量回复 +20%', value: 20, kind: 'pct', to: 'er_pct' },
  { id: 'dmg_10', label: '增伤 +10%', value: 10, kind: 'pct', to: 'dmg' },
  { id: 'am_30', label: '异常精通 +30', value: 30, kind: 'flat', to: 'am' },
];

/** 副词条 10 种。`value` 为单条数值，第 2 步按条数折算。 */
export const SUB_STATS: RuleOption[] = [
  { id: 'hp_flat', label: '小生命', value: 112, kind: 'flat', to: 'hp_flat' },
  { id: 'hp_pct', label: '大生命%', value: 3, kind: 'pct', to: 'hp_pct' },
  { id: 'atk_flat', label: '小攻击', value: 19, kind: 'flat', to: 'atk_flat' },
  { id: 'atk_pct', label: '大攻击%', value: 3, kind: 'pct', to: 'atk_pct' },
  { id: 'def_flat', label: '小防御', value: 15, kind: 'flat', to: 'def_flat' },
  { id: 'def_pct', label: '大防御%', value: 4.8, kind: 'pct', to: 'def_pct' },
  { id: 'cr', label: '暴击率', value: 2.4, kind: 'pct', to: 'cr' },
  { id: 'cd', label: '暴击伤害', value: 4.8, kind: 'pct', to: 'cd' },
  { id: 'pen_val', label: '穿透值', value: 9, kind: 'flat', to: 'pen_val' },
  { id: 'am', label: '异常精通', value: 9, kind: 'flat', to: 'am' },
];

/** 驱动盘 1/2/3 号固定主词条。 */
export const DISC_FIXED_STATS = [
  { slot: 1, label: '固定生命', value: 2200, to: 'hp_flat' },
  { slot: 2, label: '固定攻击', value: 316, to: 'atk_flat' },
  { slot: 3, label: '固定防御', value: 184, to: 'def_flat' },
] as const satisfies readonly {
  slot: number;
  label: string;
  value: number;
  to: 'hp_flat' | 'atk_flat' | 'def_flat';
}[];

/** 副词条上限：单项 36 条，6 盘合计 54 条。 */
export const SUB_STAT_LIMIT_PER_KEY = 36;
export const SUB_STAT_TOTAL_LIMIT = 54;

/**
 * 官方 WIKI 基础面板中已建模的同名条目。
 * 锋御代理人的「锐暴伤害」是固有属性，已在最终面板固定展示，
 * 因此不再计入「尚未建模的属性」提示。
 * 预设数据重新生成并将其移入建模字段后，可从本集合移除。
 */
export const MODELED_BASE_STAT_LABELS: ReadonlySet<string> = new Set(['锐暴伤害']);

/** 锋御固有属性「锐暴伤害」，恒定 150%，不参与任何加成与修正计算。 */
export const FENGYU_BLAST_DMG = 150;

/** 代理人标签全集，用于校验预设数据的 roleTag。 */
export const AGENT_ROLE_TAGS = ['强攻', '击破', '异常', '支援', '防护', '命破', '锋御'] as const;

/** 面板模式的中文名，用于代理人预设下拉的标签拼接。 */
export const PANEL_MODE_LABELS: Record<string, string> = {
  standard: '通用',
  rupture: '命破',
  fengyu: '锋御',
};