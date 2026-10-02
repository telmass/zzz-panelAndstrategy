import { defineStore } from 'pinia';

import { SUB_STATS } from '@/constants/placeholderOptions';
import type {
  AgentSelection,
  BaseStats,
  CoreSelection,
  DiscMainStats,
  PanelMode,
  SetEffects,
  SubStatCounts,
  WeaponSelection,
} from '@/types/panel';

/** 空副词条计数表，键取自 `SUB_STATS` 的 id。 */
function emptySubStats(): SubStatCounts {
  return Object.fromEntries(SUB_STATS.map((stat) => [stat.id, 0]));
}

/**
 * 面板输入与计算结果的唯一真源。
 *
 * 第 1 步只声明字段与默认值，不含任何 action / getter；
 * 第 2 步在此接入计算逻辑与联动 action，第 3 步改为转发后端响应。
 *
 * 字段名与 legacy/scripts/calculator.js 的 `baseFields`、`extraBaseFields`
 * 键名及面板行 id 保持一致，便于逐步对照迁移。
 */
export const usePanelStore = defineStore('panel', {
  state: () => ({
    /** 面板模式，由所选代理人预设决定；standard 下不显示命破与锋御专属行。 */
    panelMode: 'standard' as PanelMode,

    agent: {
      role: '',
      preset: '',
    } as AgentSelection,

    base: {
      hp: 8000,
      atk: 1000,
      def: 600,
      impact: 90,
      cr: 5,
      cd: 50,
      ac: 100,
      am: 100,
      pr: 0,
      er: 1.2,
      penforce: 0,
      energyAccumulation: 0,
    } as BaseStats,

    weapon: {
      grade: '',
      role: '',
      preset: '',
      baseLabel: '基础攻击力',
      baseValue: 0,
      subType: '—',
      subValue: 0,
    } as WeaponSelection,

    core: {
      core1: '',
      core2: '',
    } as CoreSelection,

    discMain: {
      disc4: '',
      disc5: '',
      disc6: '',
    } as DiscMainStats,

    subStats: emptySubStats() as SubStatCounts,

    setEffects: {
      set0: '',
      set1: '',
      set2: '',
    } as SetEffects,

    /**
     * 计算结果，按 `ResultRow.key` 索引。
     * 第 2 步写入前端计算结果，第 3 步改由后端响应填充。
     */
    result: {} as Record<string, string>,
  }),

  getters: {},

  actions: {},
});