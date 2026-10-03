import { defineStore } from 'pinia';

import {
  AGENT_ROLE_TAGS,
  PANEL_MODE_LABELS,
  SUB_STATS,
} from '@/constants/calculatorOptions';
import { usePresetStore } from '@/stores/presetStore';
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
import type { AgentPreset } from '@/types/agentPresets';
import type { WeaponPreset } from '@/types/weaponPresets';

/** 音擎等级的展示顺序，对应 legacy 的排序依据。 */
const GRADE_ORDER = ['S', 'A', 'B'];

/** 默认基础面板，取自 legacy calculator.html 上各 input 的默认值。 */
function defaultBase(): BaseStats {
  return {
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
  };
}

/** 空副词条计数表，键取自 `SUB_STATS` 的 id。 */
function emptySubStats(): SubStatCounts {
  return Object.fromEntries(SUB_STATS.map((stat) => [stat.id, 0]));
}

/** 代理人提示信息。对应 legacy 的 `#agent_preset_note`。 */
export interface AgentNote {
  text: string;
  /** neutral 为常规提示，error 为载入失败。 */
  tone: 'neutral' | 'error';
  /** 载入成功时的数据来源链接。 */
  source?: string;
}

const NEUTRAL_NOTE: AgentNote = { text: '', tone: 'neutral' };

/**
 * 面板输入的唯一真源。
 *
 * 只保存用户直接编辑的字段，不保存派生结果——最终面板由
 * `composables/usePanelCalc.ts` 以 computed 派生，避免状态与派生值双写。
 */
export const usePanelStore = defineStore('panel', {
  state: () => ({
    /** 当前面板模式，由载入的代理人预设决定。 */
    panelMode: 'standard' as PanelMode,

    /** URL 的 `?mode=` 参数，切换标签时回落到它。对应 legacy 的 activePanelMode。 */
    requestedMode: 'standard' as PanelMode,

    agent: { roleTag: '', presetId: '' } as AgentSelection,
    agentNote: { ...NEUTRAL_NOTE } as AgentNote,

    base: defaultBase(),

    weapon: {
      grade: '',
      roleTag: '',
      preset: '',
      baseLabel: '基础攻击力',
      baseValue: 0,
      subType: '—',
      subValue: 0,
    } as WeaponSelection,

    core: { core1: '', core2: '' } as CoreSelection,
    discMain: { disc4: '', disc5: '', disc6: '' } as DiscMainStats,
    subStats: emptySubStats(),
    setEffects: { set0: '', set1: '', set2: '' } as SetEffects,

    /** 已成功载入的代理人预设 id，用于判断切换标签时是否需要清空。 */
    appliedAgentPresetId: '',
  }),

  getters: {
    /** 代理人标签下拉选项。顺序取自 `AGENT_ROLE_TAGS`，与 legacy 一致。 */
    agentRoleOptions: (): string[] => {
      const { agents } = usePresetStore();
      return AGENT_ROLE_TAGS.filter((role) => agents.some((agent) => agent.roleTag === role));
    },

    /** 当前标签下的代理人预设。 */
    filteredAgentPresets(): AgentPreset[] {
      const { agents } = usePresetStore();
      return this.agent.roleTag
        ? agents.filter((agent) => agent.roleTag === this.agent.roleTag)
        : [];
    },

    /** 音擎等级下拉选项，按 S / A / B 排列。 */
    weaponGradeOptions(): string[] {
      const { weapons } = usePresetStore();
      return [...new Set(weapons.map((weapon) => weapon.grade))].sort(
        (a, b) => GRADE_ORDER.indexOf(a) - GRADE_ORDER.indexOf(b),
      );
    },

    /** 当前等级下的音擎类别选项。 */
    weaponRoleOptions(): string[] {
      const { weapons } = usePresetStore();
      if (!this.weapon.grade) {
        return [];
      }
      return [
        ...new Set(
          weapons.filter((weapon) => weapon.grade === this.weapon.grade).map(
            (weapon) => weapon.roleTag,
          ),
        ),
      ];
    },

    /** 当前等级与类别下的音擎预设。 */
    filteredWeaponPresets(): WeaponPreset[] {
      const { weapons } = usePresetStore();
      const { grade, roleTag } = this.weapon;
      if (!grade || !roleTag) {
        return [];
      }
      return weapons.filter(
        (weapon) => weapon.grade === grade && weapon.roleTag === roleTag,
      );
    },
  },

  actions: {
    /* ====== 面板模式 ====== */

    setPanelMode(mode: PanelMode): void {
      this.panelMode = mode;
    },

    /* ====== 音擎三级联动 ====== */

    /**
     * 选择音擎等级。对应 legacy 的 `updateWeaponGrade`：
     * 清空下游的类别与预设，并重置只读回填区。
     */
    selectWeaponGrade(grade: string): void {
      this.weapon.grade = grade;
      this.weapon.roleTag = '';
      this.weapon.preset = '';
      this.clearWeaponStats();
    },

    /** 选择音擎类别。对应 legacy 的 `updateWeaponRole`。 */
    selectWeaponRole(roleTag: string): void {
      this.weapon.roleTag = roleTag;
      this.weapon.preset = '';
      this.clearWeaponStats();
    },

    /** 清空音擎只读回填区。对应 legacy 的 `clearWeaponStats`。 */
    clearWeaponStats(): void {
      this.weapon.baseLabel = '基础攻击力';
      this.weapon.baseValue = 0;
      this.weapon.subType = '—';
      this.weapon.subValue = 0;
    },

    /**
     * 选择音擎预设并回填固定属性。对应 legacy 的 `updateWeaponSelection`。
     *
     * 基础值标签随 baseKind 变化：锋御音擎提供基础防御力。
     * `localize` 传入当前面板模式下的文案替换函数，
     * 使锋御模式显示「锐能自动累积」而非「能量自动回复」。
     */
    selectWeaponPreset(presetId: string, localize: (text: string) => string): void {
      const weapon = usePresetStore().weaponById.get(presetId);
      if (!weapon) {
        this.weapon.preset = '';
        this.clearWeaponStats();
        return;
      }
      const baseKind = weapon.baseKind ?? 'atk';
      this.weapon.preset = weapon.id;
      this.weapon.baseLabel = baseKind === 'def' ? '基础防御力' : '基础攻击力';
      this.weapon.baseValue = baseKind === 'def' ? weapon.baseDefense : weapon.baseAttack;
      this.weapon.subType = localize(weapon.substat.label);
      this.weapon.subValue = weapon.substat.value;
    },

    /** 重置整个音擎选择。对应 legacy 的 `resetWeaponSelection`。 */
    resetWeaponSelection(): void {
      this.weapon.grade = '';
      this.weapon.roleTag = '';
      this.weapon.preset = '';
      this.clearWeaponStats();
    },

    /* ====== 代理人标签联动 ====== */

    /**
     * 清空预设写入的字段。对应 legacy 的 `clearAgentPresetFields`。
     *
     * 注意只还原基础面板、核心与二件套，**不触碰副词条与音擎**——
     * 这与 legacy 完全一致：切换代理人标签不清副词条，
     * 但音擎在 `selectAgentRole` 中单独重置。
     */
    clearAgentPresetFields(): void {
      this.base = defaultBase();
      this.core = { core1: '', core2: '' };
      this.setEffects = { set0: '', set1: '', set2: '' };
      this.appliedAgentPresetId = '';
    },

    /**
     * 选择代理人标签。对应 legacy 的 `updateAgentRole`。
     *
     * 副作用顺序照搬 legacy：清空已载入预设的字段 → 面板模式回落到
     * URL 请求的模式 → 重置音擎 → 更新提示文案。
     */
    selectAgentRole(roleTag: string): void {
      this.agent.roleTag = roleTag;
      this.agent.presetId = '';

      if (this.appliedAgentPresetId) {
        this.clearAgentPresetFields();
      }
      this.panelMode = this.requestedMode;
      this.resetWeaponSelection();
      this.agentNote = {
        text: roleTag
          ? `已筛选“${roleTag}”标签，请选择具体代理人载入基础面板和核心加成；确认代理人后音擎与套装选择会重置。`
          : '请先选择代理人标签，再选择具体代理人。',
        tone: 'neutral',
      };
    },

    setAgentNote(note: AgentNote): void {
      this.agentNote = note;
    },
  },
});

export { PANEL_MODE_LABELS };