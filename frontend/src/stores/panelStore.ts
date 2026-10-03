import { defineStore } from 'pinia';

import {
  AGENT_ROLE_TAGS,
  PANEL_MODE_LABELS,
  SUB_STATS,
  WEAPON_ROLE_TAGS,
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
import type { WeaponCascaderOption, WeaponPreset } from '@/types/weaponPresets';

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
 * 「角色推荐」标记的数据源。
 *
 * 推荐关系（哪个代理人与哪条音擎适配）由**另一份预设 JSON** 提供，
 * 该文件尚未落地，故此处恒返回 `undefined`，选项文案不追加该段。
 *
 * ⚠️ 这是一个刻意留出的接缝，**不是死代码**：JSON 到位后只改这一个函数，
 * `weaponOptionLabel` 无需改动。清理时勿当作未使用代码删除。
 *
 * @param weaponId 音擎预设 id。
 */
function recommendationBadge(_weaponId: string): string | undefined {
  return undefined;
}

/**
 * 音擎选项文案：`名称 / 职业 / 等级`，末尾可选追加「角色推荐」标记。
 *
 * 等级不再作为筛选轴（与目标站一致），故写进文案，让用户仍能分辨 S/A/B。
 * 段序与目标站 `zzzcaculator.top` 的音擎选择器一致。
 */
function weaponOptionLabel(weapon: WeaponPreset): string {
  const badge = recommendationBadge(weapon.id);
  return [weapon.name, weapon.roleTag, `${weapon.grade}级`, badge].filter(Boolean).join(' / ');
}

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

    /**
     * 全部音擎预设，按职业标签分组成 cascader 的两级选项。
     *
     * 等级**不再是筛选轴**（与目标站一致，写进选项文案），故这里不按等级过滤。
     *
     * 组序取自 `WEAPON_ROLE_TAGS` 而非首次出现顺序：后者随数据变化，
     * 会导致分组跳序。组内保持 `data/weapon-presets.json` 原序。
     */
    weaponPresetGroups(): WeaponCascaderOption[] {
      const { weapons } = usePresetStore();
      return WEAPON_ROLE_TAGS.map((roleTag) => ({
        label: roleTag,
        value: roleTag,
        children: weapons
          .filter((weapon) => weapon.roleTag === roleTag)
          .map((weapon) => ({ label: weaponOptionLabel(weapon), value: weapon.id })),
      })).filter((group) => group.children && group.children.length > 0);
    },

    /** 当前选中的音擎预设，供选中后的头像卡片渲染。 */
    selectedWeapon(): WeaponPreset | null {
      return usePresetStore().weaponById.get(this.weapon.preset) ?? null;
    },
  },

  actions: {
    /* ====== 面板模式 ====== */

    setPanelMode(mode: PanelMode): void {
      this.panelMode = mode;
    },

    /* ====== 音擎选择 ====== */

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
     * 职业标签与等级都由预设反向同步回 `weapon.roleTag` / `weapon.grade`：
     * UI 已不再单列这两个维度（等级写进选项文案、职业标签作为一级分组），
     * 但选中后的头像卡片要显示「职业 / 等级」，故仍需保留。
     * 未命中预设（含用户点清除按钮）时两者一并清空，
     * 否则会出现 `roleTag` 有值而 `preset` 为空的矛盾状态。
     *
     * 基础值标签随 baseKind 变化：锋御音擎提供基础防御力。
     * `localize` 传入当前面板模式下的文案替换函数，
     * 使锋御模式显示「锐能自动累积」而非「能量自动回复」。
     */
    selectWeaponPreset(presetId: string, localize: (text: string) => string): void {
      const weapon = usePresetStore().weaponById.get(presetId);
      if (!weapon) {
        this.weapon.preset = '';
        this.weapon.roleTag = '';
        this.weapon.grade = '';
        this.clearWeaponStats();
        return;
      }
      const baseKind = weapon.baseKind ?? 'atk';
      this.weapon.preset = weapon.id;
      this.weapon.roleTag = weapon.roleTag;
      this.weapon.grade = weapon.grade;
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