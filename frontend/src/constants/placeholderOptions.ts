/**
 * 占位选项常量 —— 仅用于第 1 步渲染静态骨架。
 *
 * 取值与 legacy/scripts/calculator-config.js 保持一致，使骨架与 legacy 外观对齐。
 * 第 4 步预设数据改造后，本文件整体删除，改为从 `GET /api/presets/*` 拉取；
 * 届时 `value` / `kind` / `to` 等计算用字段随数据一同下发。
 */

import type { SelectOption, SubStatDef } from '@/types/panel';

/** 核心加成 9 项。 */
export const CORE_OPTIONS: SelectOption[] = [
  { value: 'er_base', label: '基础能量自动回复 +0.36' },
  { value: 'atk_base', label: '基础攻击力 +75' },
  { value: 'impact_base', label: '基础冲击力 +18' },
  { value: 'cd', label: '暴击伤害 +28.8%' },
  { value: 'cr', label: '暴击率 +14.4%' },
  { value: 'hp_pct', label: '生命值百分比 +18%' },
  { value: 'hp_base', label: '基础生命值 +420' },
  { value: 'ac', label: '异常掌控 +36' },
  { value: 'am', label: '异常精通 +54' },
  { value: 'pr', label: '穿透率 +14.4%' },
  { value: 'am_90', label: '异常精通 +90' },
  { value: 'atk_pct_21', label: '攻击力 +21%' },
];

/** 4 号主词条，6 选 1。 */
export const DISC4_OPTIONS: SelectOption[] = [
  { value: 'atk_pct_30', label: '攻击力 30%' },
  { value: 'hp_pct_30', label: '生命值 30%' },
  { value: 'def_pct_48', label: '防御力 48%' },
  { value: 'cr_24', label: '暴击率 24%' },
  { value: 'cd_48', label: '暴击伤害 48%' },
  { value: 'am_92', label: '异常精通 92' },
];

/** 5 号主词条，5 选 1。 */
export const DISC5_OPTIONS: SelectOption[] = [
  { value: 'atk_pct_30', label: '攻击力 30%' },
  { value: 'hp_pct_30', label: '生命值 30%' },
  { value: 'def_pct_48', label: '防御力 48%' },
  { value: 'pr_24', label: '穿透率 24%' },
  { value: 'dmg_30', label: '增伤 30%' },
];

/** 6 号主词条，6 选 1。 */
export const DISC6_OPTIONS: SelectOption[] = [
  { value: 'atk_pct_30', label: '攻击力 30%' },
  { value: 'hp_pct_30', label: '生命值 30%' },
  { value: 'def_pct_48', label: '防御力 48%' },
  { value: 'impact_pct_24', label: '冲击力 24%' },
  { value: 'ac_pct_30', label: '异常掌控 30%' },
  { value: 'er_pct_60', label: '能量回复 60%' },
];

/** 二件套效果 10 种。 */
export const SET_OPTIONS: SelectOption[] = [
  { value: 'hp_pct_10', label: '生命 +10%' },
  { value: 'atk_pct_10', label: '攻击力 +10%' },
  { value: 'def_pct_10', label: '防御力 +10%' },
  { value: 'cr_8', label: '暴击率 +8%' },
  { value: 'cd_16', label: '暴击伤害 +16%' },
  { value: 'impact_pct_6', label: '冲击力 +6%' },
  { value: 'ac_pct_8', label: '异常掌控 +8%' },
  { value: 'er_pct_20', label: '能量回复 +20%' },
  { value: 'dmg_10', label: '增伤 +10%' },
  { value: 'am_30', label: '异常精通 +30' },
];

/** 副词条 10 种，含单条数值。第 2 步按条数折算时使用。 */
export const SUB_STATS: SubStatDef[] = [
  { id: 'hp_flat', label: '小生命', value: 112, kind: 'flat' },
  { id: 'hp_pct', label: '大生命%', value: 3, kind: 'pct' },
  { id: 'atk_flat', label: '小攻击', value: 19, kind: 'flat' },
  { id: 'atk_pct', label: '大攻击%', value: 3, kind: 'pct' },
  { id: 'def_flat', label: '小防御', value: 15, kind: 'flat' },
  { id: 'def_pct', label: '大防御%', value: 4.8, kind: 'pct' },
  { id: 'cr', label: '暴击率', value: 2.4, kind: 'pct' },
  { id: 'cd', label: '暴击伤害', value: 4.8, kind: 'pct' },
  { id: 'pen_val', label: '穿透值', value: 9, kind: 'flat' },
  { id: 'am', label: '异常精通', value: 9, kind: 'flat' },
];

/** 驱动盘 1/2/3 号固定主词条，第 3 步下沉到 `core/constants.py` 后改为后端下发。 */
export const DISC_FIXED_STATS = [
  { slot: 1, label: '固定生命', value: 2200 },
  { slot: 2, label: '固定攻击', value: 316 },
  { slot: 3, label: '固定防御', value: 184 },
] as const;

/** 副词条上限：单项 36 条，6 盘合计 54 条。 */
export const SUB_STAT_LIMIT_PER_KEY = 36;
export const SUB_STAT_TOTAL_LIMIT = 54;