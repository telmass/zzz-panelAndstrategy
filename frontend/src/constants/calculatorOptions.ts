/**
 * 配装规则的类型与纯枚举。
 *
 * **规则表本身不在这里。** 七张表（CORE / DISC4 / DISC5 / DISC6 / SET / SUB_STATS
 * 与驱动盘固定值）由 `backend/src/zzz_panel/core/options.py` 与
 * `core/constants.py` 单向生成到 `data/options.json`，本文件只做类型标注与读取。
 *
 * 规则表**不走接口**：下拉框要瞬时可用，不能等一次 HTTP 往返，
 * 也不能因为后端不可用就让整个计算器瘫掉。`data/options.json` 是派生产物而非
 * 副本，改了 Python 侧规则表要跑 `python tools/sync_presets.py --options` 重新生成。
 *
 * `id` 为选项标识，`value` 为加成数值，`kind` 决定明细中的单位后缀，
 * `to` 指明该加成累加到哪个修正量。
 */

import generated from '@data/options.json';

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

/** 驱动盘 1/2/3 号固定主词条。 */
export interface DiscFixedStat {
  slot: number;
  label: string;
  value: number;
  to: ModifierKey;
}

/**
 * JSON 里的 `kind` / `to` 是 string，TS 侧需要收窄到联合类型。
 * 直接断言而非逐条校验：这份 JSON 由上面的脚本从 Python 规则表生成，
 * 类型漂移只可能来自手改，而手改会先被后端的漂移测试拦下。
 */
function table<K extends string>(key: K): RuleOption[] {
  return (generated as Record<K, RuleOption[]>)[key];
}

/** 核心加成 9 项（可重复选取，实际出现 12 个条目）。 */
export const CORE_OPTIONS: RuleOption[] = table('coreOptions');

/** 4 号主词条，6 选 1。 */
export const DISC4_OPTIONS: RuleOption[] = table('disc4Options');

/** 5 号主词条，5 选 1。 */
export const DISC5_OPTIONS: RuleOption[] = table('disc5Options');

/** 6 号主词条，6 选 1。 */
export const DISC6_OPTIONS: RuleOption[] = table('disc6Options');

/** 二件套效果 10 种。 */
export const SET_OPTIONS: RuleOption[] = table('setOptions');

/** 副词条 10 种。`value` 为单条数值，按条数折算。 */
export const SUB_STATS: RuleOption[] = table('subStats');

/**
 * 驱动盘 1/2/3 号固定主词条。
 *
 * Python 侧字段名是 `target`（`DiscFixedStat.target`），这里转成前端统一的 `to`，
 * 免得同一概念在两个层里叫不同名字。
 */
export const DISC_FIXED_STATS: DiscFixedStat[] = (
  generated as { discFixedStats: { slot: number; label: string; value: number; target: ModifierKey }[] }
).discFixedStats.map((stat) => ({
  slot: stat.slot,
  label: stat.label,
  value: stat.value,
  to: stat.target,
}));

/** 副词条上限：单项 36 条，6 盘合计 54 条。后端只做向下取整，不设上限，故无对应表。 */
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

/**
 * 音擎职业标签全集，用于音擎下拉的分组顺序。
 *
 * 与 `AGENT_ROLE_TAGS` 当前取值一致，但语义独立（一个是代理人阵营，
 * 一个是音擎适配定位），故不复用——改名或合并会波及代理人数据校验。
 *
 * 分组顺序必须固定为此表，不能用首次出现顺序：按等级过滤后首次出现
 * 顺序会随等级变化（S 级 强攻→异常→支援→…、A 级 击破→防护→异常→…），
 * 会导致切换等级时分组跳序。
 */
export const WEAPON_ROLE_TAGS = ['强攻', '击破', '异常', '支援', '防护', '命破', '锋御'] as const;

/** 面板模式的中文名，用于代理人预设下拉的标签拼接。 */
export const PANEL_MODE_LABELS: Record<string, string> = {
  standard: '通用',
  rupture: '命破',
  fengyu: '锋御',
};