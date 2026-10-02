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