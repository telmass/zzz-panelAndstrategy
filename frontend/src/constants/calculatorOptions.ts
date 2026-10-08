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
import type { AgentPreset } from '@/types/agentPresets';

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
interface DiscFixedStat {
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

/** 主词条 to 值 → 对应被排除的副词条 id（主副不重复规则） */
export const MAIN_STAT_TO_EXCLUDED_SUB_STAT: Record<ModifierKey, string | null> = {
  // 固定主词条
  hp_flat: 'hp_flat',     // 1号固定生命 → 排除小生命
  atk_flat: 'atk_flat',   // 2号固定攻击 → 排除小攻击
  def_flat: 'def_flat',   // 3号固定防御 → 排除小防御
  // 4/5/6号可选主词条
  atk_pct: 'atk_pct',     // 攻击% → 排除大攻击%
  hp_pct: 'hp_pct',       // 生命% → 排除大生命%
  def_pct: 'def_pct',     // 防御% → 排除大防御%
  cr: 'cr',               // 暴击率 → 排除暴击率
  cd: 'cd',               // 暴击伤害 → 排除暴击伤害
  am: 'am',               // 异常精通 → 排除异常精通
  pr: null,               // 穿透率 → 无对应副词条（穿透值不同属性）
  dmg: null,              // 增伤 → 无对应副词条
  impact_pct: null,       // 冲击力% → 无对应副词条
  ac_pct: null,           // 异常掌控% → 无对应副词条
  er_pct: null,           // 能量回复% → 无对应副词条
  // 其余 ModifierKey 不作为主词条
  hp_base: null,
  atk_base: null,
  def_base: null,
  pen_val: null,
  ac_flat: null,
  impact_flat: null,
  er_flat: null,
};

/** 固定主词条排除的副词条（1/2/3号位恒定生效） */
export const FIXED_MAIN_STAT_EXCLUDED_SUB_STATS = new Set<string>([
  'hp_flat',  // 1号固定生命
  'atk_flat', // 2号固定攻击
  'def_flat', // 3号固定防御
]);

/** 每盘理论词条数（1基础 + 5强化），用于折算理论上限 */
const SUB_STAT_PER_SLOT_THEORETICAL = 6;

/** 计算单个副词条的动态上限
 * 公式：(6 - 被排除盘位数) × 6
 * - 固定排除：1/2/3号位对应的副词条各被排除1个盘位
 * - 可选排除：4/5/6号位选中的主词条对应的副词条各被排除1个盘位
 */
export function calculateSubStatLimit(
  subStatId: string,
  disc4MainStat: string,
  disc5MainStat: string,
  disc6MainStat: string,
): number {
  let excludedSlots = 0;

  // 固定排除（1/2/3号位）
  if (FIXED_MAIN_STAT_EXCLUDED_SUB_STATS.has(subStatId)) {
    excludedSlots += 1;
  }

  // 可选排除（4/5/6号位）
  const disc4Excluded = MAIN_STAT_TO_EXCLUDED_SUB_STAT[disc4MainStat as ModifierKey];
  const disc5Excluded = MAIN_STAT_TO_EXCLUDED_SUB_STAT[disc5MainStat as ModifierKey];
  const disc6Excluded = MAIN_STAT_TO_EXCLUDED_SUB_STAT[disc6MainStat as ModifierKey];

  if (disc4Excluded === subStatId) excludedSlots += 1;
  if (disc5Excluded === subStatId) excludedSlots += 1;
  if (disc6Excluded === subStatId) excludedSlots += 1;

  const availableSlots = 6 - excludedSlots;
  return availableSlots * SUB_STAT_PER_SLOT_THEORETICAL;
}

/** 计算所有副词条的动态上限映射 */
export function calculateAllSubStatLimits(
  disc4MainStat: string,
  disc5MainStat: string,
  disc6MainStat: string,
): Record<string, number> {
  const limits: Record<string, number> = {};
  for (const stat of SUB_STATS) {
    limits[stat.id] = calculateSubStatLimit(stat.id, disc4MainStat, disc5MainStat, disc6MainStat);
  }
  return limits;
}

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

/**
 * 代理人标签全集，用于校验预设数据的 roleTag。
 */
export const AGENT_ROLE_TAGS = ['强攻', '击破', '异常', '支援', '防护', '命破', '锋御'] as const;

/**
 * 代理人属性类型全集，用于校验预设数据的 attribute。
 *
 * 与后端 `AGENT_ATTRIBUTES` 同源，取值由抓取脚本从官方 WIKI 页面抄来。
 * 官方对 `electric` 的写法是**电**（社区口语常作「雷」），此处照抄页面。
 */
export const AGENT_ATTRIBUTES = [
  '火',
  '冰',
  '电',
  '以太',
  '物理',
  '烈霜',
  '玄墨',
  '凛刃',
  '风',
  '流明',
] as const;

/**
 * 官方评级全集，用于校验预设数据的 grade。代理人口前只有 S / A。
 */
export const AGENT_GRADES = ['S', 'A'] as const;

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

/**
 * 是否隐藏「通用」模式的名称。
 *
 * 置 `true` 后 `panelModeTagLabel('standard')` 返回空串，代理人选择器的
 * 选项文案、头像卡片副信息与载入提示里都不再出现「通用」二字——
 * 通用代理人的文案因此缩成「名称 / 职业 / 属性 / 评级」，与命破/锋御的
 * 「名称 / 职业 / 属性 / 评级」（角色与模式同字、本就同形）一致。
 *
 * ⚠️ **只影响显示，绝不影响计算。** `panel.panelMode` 仍照常写成
 * `'standard'`，三种模式的公式、结果行与请求体一个都没变。
 *
 * 改回 `false` 即完全恢复，无需动任何调用点。
 */
const HIDE_STANDARD_MODE_LABEL = true;

/**
 * 面板模式的展示标签；`HIDE_STANDARD_MODE_LABEL` 为真且传入 `standard` 时返回空串。
 *
 * 刻意返回空串而不是别的占位：所有调用点都用 `filter(Boolean)` 过滤空段，
 * 于是这一段会自动从拼接结果里消失，不会留下多余的 ` / ` 分隔符。
 * 校验路径（`useAgentPreset` 判断 `panelMode` 是否合法）应继续用
 * `PANEL_MODE_LABELS` ——它判的是**键是否存在**，与显示无关。
 */
function panelModeTagLabel(mode: string): string {
  if (HIDE_STANDARD_MODE_LABEL && mode === 'standard') {
    return '';
  }
  return PANEL_MODE_LABELS[mode] ?? '';
}

/**
 * 代理人的标签分段：`职业 / 属性 / 评级`，面板模式名按需插在职业之后。
 *
 * 三个展示面共用这一份分段，顺序与去重规则因此不可能各自漂移：
 *
 * - 代理人 cascader 折叠框：`名称` + 本函数的分段
 * - 选中后的头像卡片副信息：只有本函数的分段（名称已单独一行）
 * - 载入提示的括号：同样只有本函数的分段
 *
 * 职业与面板模式同字（命破 / 锋御）时由 `Set` 收成一段；通用模式名被
 * `panelModeTagLabel` 隐去，故通用代理人少一段。属性与评级恒有两段，
 * 且取值全集（`AGENT_ATTRIBUTES` / `AGENT_GRADES`）与职业、模式名没有交集，
 * 不需要参与去重。
 *
 * 评级沿用音擎的写法 `${grade}级`。`attribute` / `grade` 缺失时整段略去，
 * 而不是留下空档或 `undefined`——数据结构坏了由 `validateAgentPresetData`
 * 报错，这里只保证不把 `undefined` 渲染到界面上。
 */
export function agentTagSegments(agent: AgentPreset): string[] {
  const tags = [...new Set([agent.roleTag, panelModeTagLabel(agent.panelMode)].filter(Boolean))];
  return [...tags, agent.attribute, `${agent.grade}级`].filter(Boolean);
}