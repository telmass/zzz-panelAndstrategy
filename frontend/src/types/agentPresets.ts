/**
 * 代理人预设数据的类型契约。
 *
 * 与 `backend/src/zzz_panel/schemas/` 的预设响应模型一一对应，
 * 第 4 步改由 `GET /api/presets/agents` 下发后仍复用本文件。
 */

import type { PanelMode } from './panel';

export type { PanelMode };

/**
 * 60 级基础面板（不含核心）。
 *
 * 全部键均为可选：`unavailableBaseStats` 列出的项在官方面板中本就缺失，
 * 例如部分命破代理人不提供穿透率与能量自动回复。
 */
export type AgentBaseStats = Partial<{
  hp: number;
  atk: number;
  def: number;
  impact: number;
  cr: number;
  cd: number;
  ac: number;
  am: number;
  /** 穿透率 %，命破模式下不显示。 */
  pr: number;
  /** 能量自动回复 %；锋御模式下面板文案替换为「锐能自动累积」。 */
  er: number;
}>;

/** 命破模式专属的基础面板字段。 */
export interface AgentAdditionalBaseStats {
  penforce?: number;
  energyAccumulation?: number;
}

/** 官方 WIKI 列出、但当前计算器尚未建模的基础属性。 */
export interface UnmodeledBaseStat {
  label: string;
  value: number;
  unit: string;
}

/** 单条核心加成。`ranks` 为核心技位次，`optionCount` 表示该条被计入几个核心选项。 */
export interface AgentCoreBonus {
  optionId: string;
  ranks: string[];
  label: string;
  perRankValue: number;
  totalValue: number;
  unit: string;
  optionCount?: number;
}

/** 一条代理人预设。 */
export interface AgentPreset {
  id: string;
  name: string;
  /** 官方属性类型，如「火」「烈霜」。取值白名单见 `AGENT_ATTRIBUTES`。 */
  attribute: string;
  /** 官方评级，代理人口前只有 `S` / `A`。 */
  grade: string;
  roleTag: string;
  panelMode: PanelMode;
  /** 米游社官方 WIKI 出处，载入预设时以链接形式展示。 */
  source: string;
  base: AgentBaseStats;
  additionalBaseStats?: AgentAdditionalBaseStats;
  /** `base` 中官方未提供、需要留空的键。 */
  unavailableBaseStats?: string[];
  unmodeledBaseStats?: UnmodeledBaseStat[];
  coreBonuses: AgentCoreBonus[];
}

/**
 * 代理人 cascader 的一个选项。
 *
 * 结构与 `WeaponCascaderOption` 相同：一级项是职业标签（带 `children`），
 * 二级项是具体代理人（叶子）。`label` 是浏览态看不到、但选中后可见的文案——
 * naive-ui 渲染折叠框与 `filterable` 匹配用的都是它，`renderLabel` 只管浏览菜单。
 *
 * 实际段数恒为 4（「名称 / 职业 / 属性 / 评级」）：`panelMode` 不作独立筛选轴，
 * 只写进文案，且命破/锋御因 `roleTag` 与模式名同字被去重、通用模式名被
 * `HIDE_STANDARD_MODE_LABEL` 隐去，两种情况都不改变段数。
 * 分段由 `constants/calculatorOptions` 的 `agentTagSegments` 单一定义，
 * `panelStore` 的 `agentOptionLabel` 只在其前面拼上名称。
 *
 * 索引签名是 naive-ui 的 `CascaderOption` 所必需，去掉就无法传给 `n-cascader`。
 */
export interface AgentCascaderOption {
  label: string;
  /** 一级为职业标签，二级为代理人 id。 */
  value: string;
  children?: AgentCascaderOption[];
  [key: string]: unknown;
}