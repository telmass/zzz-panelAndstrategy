/**
 * 音擎预设数据的类型契约。
 *
 * 与 `backend/src/zzz_panel/schemas/` 的预设响应模型一一对应，
 * 第 4 步改由 `GET /api/presets/weapons` 下发后仍复用本文件。
 */

import type { ModifierKey, ModifierKind } from '@/constants/calculatorOptions';

/** 音擎等级。 */
export type WeaponGrade = 'S' | 'A' | 'B';

/**
 * 音擎提供的基础值种类。
 *
 * `atk` 为基础攻击力，`def` 为基础防御力——锋御音擎提供后者，
 * 对应 `usePanelCalc` 中攻防血基础值的不同来源。
 */
export type WeaponBaseKind = 'atk' | 'def';

/** 音擎的固定副词条。 */
export interface WeaponSubstat {
  label: string;
  value: number;
  kind: ModifierKind;
  to: ModifierKey;
}

/** 一条音擎预设。 */
export interface WeaponPreset {
  id: string;
  name: string;
  grade: WeaponGrade;
  roleTag: string;
  /** 米游社官方 WIKI 出处。 */
  source: string;
  /** 缺省视为 `atk`。 */
  baseKind?: WeaponBaseKind;
  baseAttack: number;
  baseDefense: number;
  substat: WeaponSubstat;
}

/**
 * 音擎 cascader 的一个选项。
 *
 * 结构与 naive-ui 的 `CascaderOption` 对齐：一级项是职业标签（带 `children`），
 * 二级项是具体音擎（叶子）。`label` 已经是拼好的完整文案
 * 「名称 / 职业 / 等级」，因为 `filterable` 的过滤就是拿 `label` 匹配的，
 * 这样用户输入「S」也能命中 S 级音擎。
 */
export interface WeaponCascaderOption {
  label: string;
  /** 一级为职业标签，二级为音擎 id。 */
  value: string;
  children?: WeaponCascaderOption[];
  /**
   * naive-ui 的 `CascaderOption` 带字符串索引签名，去掉它就无法直接
   * 传给 `n-cascader` 的 `options`。保留签名以确保结构兼容。
   */
  [key: string]: unknown;
}