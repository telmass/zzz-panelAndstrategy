/**
 * 面板计算器的类型契约。
 *
 * 字段与命名沿用 legacy/scripts/calculator.js 的 `baseFields` / `extraBaseFields`
 * 键名与面板行 id，保证第 2 步迁移计算逻辑时无需二次改名。
 */

/** 面板模式：standard 通用 / rupture 命破 / fengyu 锋御。 */
export type PanelMode = 'standard' | 'rupture' | 'fengyu';

/** 角色纯基础面板（不含核心）。对应 legacy 的 `#base_*`。 */
export interface BaseStats {
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
  /** 角色基础贯穿力，仅命破模式显示。 */
  penforce: number;
  /** 闪能自动累积，仅命破模式显示。 */
  energyAccumulation: number;
}

/** 音擎选择与只读回填字段。对应 legacy 的 `#weapon_*`。 */
export interface WeaponSelection {
  grade: string;
  role: string;
  preset: string;
  baseLabel: string;
  baseValue: number;
  subType: string;
  subValue: number;
}

/** 核心加成两个下拉的选中项 id。对应 legacy 的 `#core1` / `#core2`。 */
export interface CoreSelection {
  core1: string;
  core2: string;
}

/** 4/5/6 号主词条选中项。对应 legacy 的 `#disc4` / `#disc5` / `#disc6`。 */
export interface DiscMainStats {
  disc4: string;
  disc5: string;
  disc6: string;
}

/** 副词条条数，键为副词条 id。对应 legacy 的 `#sub_${id}`。 */
export type SubStatCounts = Record<string, number>;

/** 三组二件套选中项。对应 legacy 的 `#sets_container` 内 `#set${i}`。 */
export interface SetEffects {
  set0: string;
  set1: string;
  set2: string;
}

/** 代理人预设选择。对应 legacy 的 `#agent_role` / `#agent_preset`。 */
export interface AgentSelection {
  role: string;
  preset: string;
}

/**
 * 结果面板的一行。
 *
 * `key` 对应 legacy 的 `#r_${key}`，`breakdownKey` 对应 `#b_${key}`，
 * 第 2 步填充 `value` 与 `breakdown` 两个 HTML 片段。
 */
export interface ResultRow {
  key: string;
  label: string;
  /** 主属性行使用更大字号与强调色。 */
  main?: boolean;
  /** 命破专属行，对应 `#rupture_result`。 */
  ruptureOnly?: boolean;
  /** 锋御专属行，对应 `#fengyu_result` / `#fengyu_blast_result`。 */
  fengyuOnly?: boolean;
  /** 数值后缀，如 '%'。 */
  unit?: string;
}

/** 下拉框的一项。 */
export interface SelectOption {
  value: string;
  label: string;
}

/**
 * 副词条定义，对应 legacy 的 `SUB_STATS`。
 *
 * `id` 为标识键（用于 store 与 DOM id），`value` 为单条数值，
 * 与 legacy 中 `{ id, label, value, kind, to }` 的字段划分一致。
 */
export interface SubStatDef {
  id: string;
  label: string;
  /** 单条数值，第 2 步按条数折算时使用。 */
  value: number;
  kind: 'flat' | 'pct';
}