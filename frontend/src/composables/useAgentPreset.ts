import {
  AGENT_ATTRIBUTES,
  AGENT_GRADES,
  CORE_OPTIONS,
  MODELED_BASE_STAT_LABELS,
  PANEL_MODE_LABELS,
  agentTagSegments,
} from '@/constants/calculatorOptions';
import { AGENT_ROLE_TAGS } from '@/constants/calculatorOptions';
import { strategyGuides } from '@/constants/strategyGuides';
import { displayEnergyAttributeLabel, isPanelMode } from '@/composables/usePanelMode';
import { usePanelStore, type AgentNote } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
import { fmt } from '@/utils/fmt';
import type { AgentPreset } from '@/types/agentPresets';
import type { PanelMode } from '@/types/panel';

/** 基础面板会从预设写入的键。对应 legacy 的 `baseFields`。 */
const BASE_KEYS = ['hp', 'atk', 'def', 'impact', 'cr', 'cd', 'ac', 'am', 'pr', 'er'] as const;

/**
 * 命破模式**允许缺失**的基础键：官方基础面板里本来就不列这两个
 * （它们被贯穿力 / 闪能自动累积取代）。其余模式十项必须齐全。
 *
 * 与后端 `zzz_panel.presets.validate.RUPTURE_OPTIONAL_BASE_KEYS` 同源。
 */
const RUPTURE_OPTIONAL_BASE_KEYS = ['pr', 'er'] as const;

/** 命破专属的基础面板键。对应 legacy 的 `extraBaseFields`。 */
const EXTRA_BASE_KEYS = ['penforce', 'energyAccumulation'] as const;

/** 浮点比较容差，与 legacy 的 1e-7 一致。 */
const EPSILON = 0.0000001;

/**
 * 特殊属性判定：**该属性当前只有一名代理人持有**（人数为 1）。
 *
 * 规则只有这一条，不再叠加「属性名不在常规五项内」之类的条件，也不写成
 * 「烈霜/玄墨/凛刃/流明」这样的硬编码名单——名单会随官方新代理人过时，
 * 而规则与具体是哪些属性无关。
 *
 * 结论随数据变化：某属性一旦被第二名代理人持有，它就不再是特殊属性。
 * 因此**不要缓存**返回值，每次按当前 `agents` 重算。
 *
 * 与后端 `zzz_panel.presets.attributes.special_agent_attributes` 同源。
 */
export function specialAgentAttributes(agents: AgentPreset[]): Set<string> {
  const counts = new Map<string, number>();
  for (const agent of agents) {
    counts.set(agent.attribute, (counts.get(agent.attribute) ?? 0) + 1);
  }
  return new Set([...counts].filter(([, count]) => count === 1).map(([key]) => key));
}

/** 单个属性是否为特殊属性。语义与 {@link specialAgentAttributes} 一致。 */
export function isSpecialAttribute(attribute: string, agents: AgentPreset[]): boolean {
  return agents.filter((agent) => agent.attribute === attribute).length === 1;
}

/**
 * 预设数据自身的完整性校验。对应 legacy 脚本顶部对
 * `invalidAgentPresets` 与 `duplicateAgentIds` 的两次检查。
 *
 * 在应用预设前一次性跑完，任何一条不通过都视为数据源损坏，
 * 此时所有预设均不可载入——比 legacy 逐项抛错更早暴露问题。
 *
 * 第 4 步起预设由 `GET /api/presets/agents` 下发，后端已在
 * `presets/validate.py` 做过同一套检查。这里保留是为了不把「数据可用性」
 * 完全托付给网络：即便后端换了数据源，前端也不会把坏数据写进面板。
 */
export function validateAgentPresetData(): void {
  const { agents } = usePresetStore();
  const invalid = agents.filter(
    (agent) =>
      !agent.id ||
      !agent.name ||
      !AGENT_ROLE_TAGS.includes(agent.roleTag as never) ||
      !AGENT_ATTRIBUTES.includes(agent.attribute as never) ||
      !AGENT_GRADES.includes(agent.grade as never),
  );
  if (invalid.length) {
    throw new Error(
      `代理人预设存在缺少专属标签或无效数据的条目：${invalid
        .map((agent) => agent.name || agent.id || '未知条目')
        .join('、')}`,
    );
  }

  const duplicateIds = agents.filter(
    (agent, index) => agents.findIndex((candidate) => candidate.id === agent.id) !== index,
  );
  if (duplicateIds.length) {
    throw new Error(
      `代理人预设存在重复ID：${[...new Set(duplicateIds.map((agent) => agent.id))].join('、')}`,
    );
  }
}

/**
 * 官方未提供的基础属性键。
 *
 * 「没写到的键」本身就是那份事实——数据里不再另存一个 `unavailableBaseStats`
 * 数组（同一件事存两份，就得靠校验器去证明它们没漂移）。
 */
function unavailableBaseKeys(agent: AgentPreset): string[] {
  return BASE_KEYS.filter((key) => !Number.isFinite(agent.base?.[key]));
}

/**
 * 单条预设的可载入性校验。逐条移植 legacy 的 `applyAgentPreset` 中的 try 块。
 *
 * 校验通过返回填入两个核心下拉的选项 id；不通过则抛出带代理人名称的错误，
 * 由调用方转成红色提示。这些校验属于「数据不可信」的防御层，
 * 第 4 步改为后端下发后需与 `backend/src/zzz_panel/presets/validate.py` 对齐。
 */
function resolveCoreIndexes(agent: AgentPreset): string[] {
  for (const key of BASE_KEYS) {
    if (Number.isFinite(agent.base?.[key])) {
      continue;
    }
    const legitimate =
      agent.panelMode === 'rupture' && RUPTURE_OPTIONAL_BASE_KEYS.includes(key as never);
    if (!legitimate) {
      throw new Error(`${agent.name}的基础面板缺少有效的${key}数值。`);
    }
  }

  const additional = agent.baseExtra ?? {};
  for (const [key, value] of Object.entries(additional)) {
    if (!(EXTRA_BASE_KEYS as readonly string[]).includes(key) || !Number.isFinite(value)) {
      throw new Error(`${agent.name}包含无法识别的额外基础属性“${key}”。`);
    }
  }
  if (
    agent.panelMode === 'rupture' &&
    EXTRA_BASE_KEYS.some((key) => !Number.isFinite(additional[key]))
  ) {
    throw new Error(`${agent.name}的命破基础面板缺少官方基础贯穿力或闪能自动累积数值。`);
  }

  if (!Array.isArray(agent.core) || agent.core.length === 0) {
    throw new Error(`${agent.name}缺少有效的核心加成数据。`);
  }
  if (!Object.hasOwn(PANEL_MODE_LABELS, agent.panelMode)) {
    throw new Error(`${agent.name}缺少有效的计算类型标签。`);
  }

  const coreIndexes: string[] = [];
  for (const bonus of agent.core) {
    const option = CORE_OPTIONS.find((candidate) => candidate.id === bonus.optionId);
    const optionCount = bonus.optionCount ?? 1;
    if (
      !option ||
      !Number.isInteger(optionCount) ||
      optionCount < 1 ||
      !Number.isFinite(bonus.totalValue) ||
      Math.abs(option.value * optionCount - bonus.totalValue) > EPSILON
    ) {
      throw new Error(`${agent.name}的核心加成“${bonus.label}”无法由当前核心选项准确表示。`);
    }
    if (
      !Array.isArray(bonus.ranks) ||
      bonus.ranks.length === 0 ||
      !Number.isFinite(bonus.perRank) ||
      Math.abs(bonus.perRank * bonus.ranks.length - bonus.totalValue) > EPSILON
    ) {
      throw new Error(`${agent.name}的核心加成“${bonus.label}”数据不一致。`);
    }
    for (let count = 0; count < optionCount; count += 1) {
      coreIndexes.push(option.id);
    }
  }
  if (coreIndexes.length !== 2) {
    throw new Error(`${agent.name}的核心加成无法准确填入两个计算器核心选项。`);
  }

  const rawUnmodeled = agent.baseUnmodeled ?? [];
  if (
    !Array.isArray(rawUnmodeled) ||
    rawUnmodeled.some(
      (stat) => typeof stat.label !== 'string' || !Number.isFinite(stat.value) || typeof stat.unit !== 'string',
    )
  ) {
    throw new Error(`${agent.name}包含无法识别的未建模基础属性。`);
  }

  return coreIndexes;
}

/**
 * 代理人的展示标签：`职业 / 属性 / 评级`，模式名按需插在职业之后。
 *
 * 分段由 `agentTagSegments` 单一定义，与 cascader 折叠框的选项文案同源，
 * 因此模式名隐去（通用）与同字去重（命破 / 锋御）的行为三处一致。
 */
export function agentTagLabel(agent: AgentPreset): string {
  return agentTagSegments(agent).join(' / ');
}

/** 载入预设后的提示文案。对应 legacy 的 `note.replaceChildren(...)` 部分。 */
function buildSuccessNote(agent: AgentPreset): AgentNote {
  // 结构校验覆盖全部条目；仅在生成提示文案时剔除已建模的同名属性。
  const unmodeled = (agent.baseUnmodeled ?? []).filter(
    (stat) => !MODELED_BASE_STAT_LABELS.has(stat.label),
  );

  // 命破模式缺 pr/er 是官方如此（这两个位置被贯穿力 / 闪能自动累积取代），
  // 不必在提示里说「官方未提供」。
  const unavailableVisible = unavailableBaseKeys(agent).filter(
    (key) =>
      agent.panelMode !== 'rupture' ||
      !RUPTURE_OPTIONAL_BASE_KEYS.includes(key as never),
  );
  const unavailableSummary = unavailableVisible.length
    ? `官方基础面板未提供${unavailableVisible
        .map(
          (key) =>
            ({
              pr: '穿透率',
              er: displayEnergyAttributeLabel('能量自动回复', agent.panelMode),
            })[key] ?? key,
        )
        .join('、')}。`
    : '';

  const coreSummary = agent.core
    .map(
      (bonus) =>
        `${bonus.ranks.join('/')}：${bonus.label}每级 +${fmt(bonus.perRank)}${bonus.unit}，合计 +${fmt(bonus.totalValue)}${bonus.unit}`,
    )
    .join('；');

  const unmodeledSummary = unmodeled.length
    ? `官方还列有当前计算器尚未建模的属性：${unmodeled
        .map((stat) => `${stat.label} ${fmt(stat.value)}${stat.unit}`)
        .join('、')}。`
    : '';

  return {
      // 词组内的不换行空格：「数据<nbsp>来源：<链接>」是一个整体，
      // 否则中文换行会把它折成「数据」+「来源：米游社官方WIKI」。
      text: `已载入${agent.name}（${agentTagLabel(agent)}）的60级基础面板（不含核心）及满级核心加成。${coreSummary}。${unavailableSummary}${unmodeledSummary}`,
    tone: 'neutral',
    source: agent.source,
  };
}

/**
 * 载入代理人预设。对应 legacy 的 `applyAgentPreset`。
 *
 * 副作用与 legacy 一致：先重置音擎，校验通过后写入基础面板、
 * 核心与面板模式，清空二件套；任何失败都只写红色提示而不改动已载入的字段。
 */
export function useAgentPreset() {
  const panel = usePanelStore();

  /**
   * 载入指定 id 的预设。传入空串表示取消选择，
   * 此时清空已载入字段并把面板模式回落到 URL 请求的模式。
   */
  function applyAgentPreset(agentId: string): AgentNote {
    panel.resetWeaponSelection();

    if (!agentId) {
      if (panel.appliedAgentPresetId) {
        panel.clearAgentPresetFields();
      }
      panel.panelMode = panel.requestedMode;
      const note: AgentNote = {
        text: panel.agent.roleTag
          ? `已筛选“${panel.agent.roleTag}”标签，请选择具体代理人载入基础面板和核心加成。`
          : '请选择代理人以载入基础面板和核心加成。',
        tone: 'neutral',
      };
      panel.setAgentNote(note);
      return note;
    }

    const agent = usePresetStore().agentById.get(agentId);
    if (!agent) {
      return fail(`代理人预设加载失败：找不到“${agentId}”的数据。`);
    }
    if (!panel.agent.roleTag || agent.roleTag !== panel.agent.roleTag) {
      panel.agent.presetId = '';
      return fail(
        `代理人预设加载失败：“${agent.name}”不属于当前选择的“${panel.agent.roleTag || '无'}”标签。请先选择正确标签。`,
      );
    }

    try {
      const coreIndexes = resolveCoreIndexes(agent);

      // 写入基础面板：缺失的键留空，与 legacy 的 `Number.isFinite(...) ? ... : ''` 一致。
      const nextBase = { ...panel.base };
      for (const key of BASE_KEYS) {
        const value = agent.base?.[key];
        nextBase[key] = Number.isFinite(value) ? (value as number) : 0;
      }
      panel.base = nextBase;

      for (const key of EXTRA_BASE_KEYS) {
        panel.base[key] = 0;
      }
      for (const [key, value] of Object.entries(agent.baseExtra ?? {})) {
        if ((EXTRA_BASE_KEYS as readonly string[]).includes(key) && Number.isFinite(value)) {
          panel.base[key as (typeof EXTRA_BASE_KEYS)[number]] = value as number;
        }
      }

      panel.core = { core1: coreIndexes[0], core2: coreIndexes[1] };
      panel.setEffects = { set0: '', set1: '', set2: '' };
      panel.panelMode = agent.panelMode;
      panel.agent.presetId = agent.id;
      panel.appliedAgentPresetId = agent.id;

      const note = buildSuccessNote(agent);
      panel.setAgentNote(note);
      return note;
    } catch (error) {
      return fail(`代理人预设加载失败：${(error as Error).message}`);
    }
  }

  /** 写入红色提示并记录到控制台，与 legacy 的 `console.error` 行为一致。 */
  function fail(text: string): AgentNote {
    console.error(text);
    const note: AgentNote = { text, tone: 'error' };
    panel.setAgentNote(note);
    return note;
  }

  /**
   * 初始化时按 URL 的 `?mode=` 参数确定初始面板模式，
   * 并可按 `?agent=` 直接载入某名代理人的预设。
   *
   * `?agent=` 接受两种写法：
   *
   * - **slug**（`ye-shunguang`）——与 `/strategy/<slug>` 一致，人写的链接；
   * - **预设 id**（`ep-1109`）——预设数据自身的稳定标识。
   *
   * 有了它，一条链接就能复现某位代理人的整套面板——既是**分享**需求，
   * 也是 UI 验收清单里「状态由 URL 决定」那条要求的前提。
   */
  function initFromQueryParam(raw: string | null, agentRef?: string | null): void {
    const mode: PanelMode = isPanelMode(raw) ? raw : 'standard';
    panel.requestedMode = mode;
    panel.panelMode = mode;

    const ref = (agentRef ?? '').trim();
    if (!ref) {
      return;
    }
    const agentId = ref.startsWith('ep-') ? ref : slugToAgentId(ref);
    if (!agentId) {
      fail(`代理人预设加载失败：找不到“${ref}”对应的代理人。`);
      return;
    }
    const agent = usePresetStore().agentById.get(agentId);
    if (!agent) {
      fail(`代理人预设加载失败：找不到“${ref}”的数据。`);
      return;
    }
    // 载入预设要求角色标签与代理人对得上；URL 直载时标签还没选过，
    // 按预设自身的标签补上，否则必然被判成「不属于当前标签」。
    panel.agent.roleTag = agent.roleTag;
    applyAgentPreset(agent.id);
  }

  /** slug → 预设 id。slug 表是攻略登记表，代理人 id 与之同一套。 */
  function slugToAgentId(slug: string): string {
    return strategyGuides.find((guide) => guide.slug === slug)?.agentId ?? '';
  }

  return { applyAgentPreset, initFromQueryParam };
}