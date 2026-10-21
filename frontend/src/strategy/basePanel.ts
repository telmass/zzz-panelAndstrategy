/**
 * 攻略页「基础面板」区块的数据来源。
 *
 * 基础面板的**唯一真实源是代理人预设**（`data/catalog/agents.json`）。
 * 攻略抓取产物里曾各存一份 ``basePanel``，61 份攻略 JSON 于是有了 61 份
 * 同样的数字——两份数据一旦漂移，攻略页显示的面板就会和计算器算出的对不上
 * （这件事已经发生过：三名代理人的属性名口径在两处不一致）。
 *
 * 现在攻略页的基础面板由这里从预设派生，攻略 JSON 不再携带 ``basePanel``。
 */

import { displayEnergyAttributeLabel } from '@/composables/usePanelMode';
import type { AgentPreset } from '@/types/agentPresets';

/** 基础面板的一行。 */
export interface BasePanelField {
  label: string;
  value: number;
  unit: string;
}

/**
 * 基础面板的规范字段顺序与展示文案。
 *
 * 顺序即展示顺序（生命 → 攻击 → 防御 → 冲击 → 暴击 → 异常 → 穿透 → 能量），
 * 与抓取脚本原先的 ``BASE_PANEL_FIELDS`` 一致。单位只有两种：百分比属性带
 * ``%``，其余不带。
 */
const BASE_FIELDS: ReadonlyArray<{
  key: keyof NonNullable<AgentPreset['base']>;
  label: string;
  unit: string;
}> = [
  { key: 'hp', label: '生命值', unit: '' },
  { key: 'atk', label: '攻击力', unit: '' },
  { key: 'def', label: '防御力', unit: '' },
  { key: 'impact', label: '冲击力', unit: '' },
  { key: 'cr', label: '暴击率', unit: '%' },
  { key: 'cd', label: '暴击伤害', unit: '%' },
  { key: 'ac', label: '异常掌控', unit: '' },
  { key: 'am', label: '异常精通', unit: '' },
  { key: 'pr', label: '穿透率', unit: '%' },
  { key: 'er', label: '能量自动回复', unit: '' },
];

/** 命破模式的额外基础属性（贯穿力 / 闪能自动累积）。 */
const EXTRA_FIELDS: ReadonlyArray<{
  key: keyof NonNullable<AgentPreset['baseExtra']>;
  label: string;
  unit: string;
}> = [
  { key: 'penforce', label: '贯穿力', unit: '' },
  { key: 'energyAccumulation', label: '闪能自动累积', unit: '' },
];

/**
 * 从代理人预设派生攻略页要展示的 60 级基础面板。
 *
 * 命破模式的「贯穿力 / 闪能自动累积」来自 ``baseExtra``，锋御模式的
 * 「能量自动回复」在页面上叫「锐能自动累积」——两者都由预设本身决定，
 * 不再各存一份。
 */
export function basePanelFromPreset(agent: AgentPreset): BasePanelField[] {
  const fields: BasePanelField[] = [];

  for (const field of BASE_FIELDS) {
    const value = agent.base?.[field.key];
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      continue;
    }
    fields.push({
      label: displayEnergyAttributeLabel(field.label, agent.panelMode),
      value,
      unit: field.unit,
    });
  }

  for (const field of EXTRA_FIELDS) {
    const value = agent.baseExtra?.[field.key];
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      continue;
    }
    fields.push({ label: field.label, value, unit: field.unit });
  }

  return fields;
}
