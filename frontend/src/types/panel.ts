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
  roleTag: string;
  preset: string;
  /** 「基础攻击力」或「基础防御力」，随音擎 baseKind 变化。 */
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

/** 副词条条数，键为副词条 id（取自 `SUB_STATS`）。对应 legacy 的 `#sub_${id}`。 */
export type SubStatCounts = Record<string, number>;

/** 三组二件套选中项。对应 legacy 的 `#sets_container` 内 `#set${i}`。 */
export interface SetEffects {
  set0: string;
  set1: string;
  set2: string;
}

/** 代理人预设选择。对应 legacy 的 `#agent_role` / `#agent_preset`。 */
export interface AgentSelection {
  roleTag: string;
  presetId: string;
}

/**
 * 累加器：各配装对修正量的累加结果。
 *
 * `_flat` / `_base` 结尾的是纯加法或基础值修正，`_pct` 结尾的带 % 参与乘法。
 */
export type ModifierSum = Record<string, number>;

/**
 * 来源记录：每个修正量由哪些配装贡献，用于生成明细文案。
 * 键与累加器一致，值为贡献来源的说明数组。
 */
export type ModifierSources = Record<string, string[]>;

/** 结果面板的一行。 */
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

/**
 * 单行结果。`value` 为格式化后的数值，`breakdown` 为已转义的明细 HTML 片段。
 *
 * 第 3 步起数值与明细片段均来自后端（`PanelApiResponse`），这里只保留
 * 「已渲染好、可直接 `v-html`」的形态，以便与 legacy 的 innerHTML 逐字符一致。
 * `tests/legacy-parity.spec.ts` 守住这一等价性。
 */
export interface ResultValue {
  value: string;
  breakdown: string;
}

/** 全部结果的映射，键为 `ResultRow.key`。 */
export type PanelResult = Record<string, ResultValue>;

/* ====== 第 3 步：与后端的 HTTP 契约 ======
 * 与 backend/src/zzz_panel/schemas/panel.py 一一对应。
 */

/** 请求里的角色基础面板。键名与本文件的 `BaseStats` 一致。 */
export type PanelCalcBase = {
  hp: number;
  atk: number;
  /** 防御力。JSON 键为 `def`，Python 侧是 `def_` 关键字规避。 */
  def: number;
  impact: number;
  cr: number;
  cd: number;
  ac: number;
  am: number;
  pr: number;
  er: number;
};

/** 音擎固定副词条。已从音擎预设解析出目标修正量与数值。 */
export interface PanelCalcWeaponSubstat {
  /** 目标修正量键名，取自 `ModifierKey`。 */
  target: string;
  value: number;
  kind: 'pct' | 'flat';
  label: string;
}

export interface PanelCalcWeapon {
  baseKind: 'atk' | 'def';
  baseValue: number;
  substat: PanelCalcWeaponSubstat | null;
}

export interface PanelCalcCore {
  core1: string;
  core2: string;
}

export interface PanelCalcDiscMain {
  disc4: string;
  disc5: string;
  disc6: string;
}

export interface PanelCalcSets {
  set0: string;
  set1: string;
  set2: string;
}

/** 发起计算所需的全部信息。只带选择，不带数值。 */
export interface PanelCalcRequest {
  mode: PanelMode;
  base: PanelCalcBase;
  weapon: PanelCalcWeapon;
  core: PanelCalcCore;
  discMain: PanelCalcDiscMain;
  /** 副词条条数。键为**规则表 id**（snake_case，如 `hp_flat`），非 camelCase。 */
  subStats: Record<string, number>;
  sets: PanelCalcSets;
}

/** 明细片段：与后端 `core/breakdown.py` 的 dataclass 一一对应。 */
export type BreakdownSegment =
  | { type: 'text'; text: string }
  /** 关键百分比，`text` 已含 `%`。 */
  | { type: 'kw'; text: string }
  /** 裸数值，渲染时套 `fmt`；`bold` 对应 legacy 明细末值的 `<b>`，`unit` 渲染进 `<b>` 内。 */
  | { type: 'num'; value: number; bold: boolean; unit: string }
  /** 来源数组，渲染时以 ` + ` 连接。 */
  | { type: 'sources'; items: string[] };

export interface BreakdownLine {
  type: 'line';
  parts: BreakdownSegment[];
  /** false 时不套 `breakdown-line`，对应 legacy 的纯加法裸行。 */
  wrapped: boolean;
}

/** 后端返回的最终面板。 */
export interface PanelApiResponse {
  mode: PanelMode;
  /** 12 行通用结果，键为 `hp/atk/def/cr/cd/dmg/pr/pv/am/ac/imp/er`。 */
  totals: Record<string, number>;
  /** 命破 `penforce` 或锋御 `actual_cr` / `fengyu_blast_dmg`。 */
  modeStats: Record<string, number>;
  /** 锋御固有属性「锐暴伤害」，非锋御模式为 null。 */
  blastDmg: number | null;
  /** 修正量累加器，中间量，供明细渲染。 */
  sums: Record<string, number>;
  /** 每个修正量的来源说明。 */
  sources: Record<string, string[]>;
  /** 副词条中固定值三类的小计。 */
  subFixed: Record<string, number>;
  /** 音擎基础值归属。 */
  weaponBase: Record<string, number>;
  /** 结构化明细，渲染交由前端。键为结果行键（snake_case，与 `totals` 一致）。 */
  breakdown: Record<string, BreakdownLine[]>;
}


/** 下拉框的一项。 */
export interface SelectOption {
  value: string;
  label: string;
}