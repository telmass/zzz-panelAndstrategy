import agents from '@data/catalog/agents.json';

import type { AgentAdditionalBaseStats, AgentBaseStats } from '@/types/agentPresets';

/**
 * 代理人预设的**构建期静态副本**。
 *
 * 攻略详情页要在**不依赖网络**的前提下显示基础面板。那份数据过去只从
 * `GET /api/presets/agents` 拿——接口一挂（本地没起后端、线上偶发失败），
 * 页面就只剩一句「暂无基础面板数据」，看着像没做。
 *
 * 这里直接读仓库根 `data/catalog/agents.json`：与接口下发的是**同一份文件**
 * （后端不改写、不丢字段，见 `backend/src/zzz_panel/schemas/presets.py`
 * 的「线格式与源数据逐条等价」），因此不存在两份数据漂移的问题。
 * 驱动盘套装与规则表是同一做法（`@data/catalog/drive-discs.json`、
 * `@data/rules/calculator-rules.json`）。
 *
 * 代价是这 57 KB 会进产物——但它只进**攻略详情页**的路由 chunk：
 * 只有这个页面 import 本模块，别的路由不付这份体积。
 */

/** 本地副本里我们真正用到的字段（其余字段与基础面板无关）。 */
export interface LocalAgentPreset {
  /** `ep-<entry_page_id>`，与 Wiki 详情页一一对应。 */
  id: string;
  /** 面板模式（standard / rupture / armorer）。 */
  panelMode?: string;
  /** 60 级基础面板。 */
  base?: AgentBaseStats;
  /** 命破模式专属的额外基础属性。 */
  baseExtra?: AgentAdditionalBaseStats;
}

/** 全部代理人预设（构建期内联）。 */
export const LOCAL_AGENT_PRESETS = agents as LocalAgentPreset[];

const BY_ID = new Map(LOCAL_AGENT_PRESETS.map((agent) => [agent.id, agent]));

/**
 * 按 id 查代理人预设。
 *
 * 查不到返回 `undefined`——官方还没公开的代理人（只有 mapping 条目、
 * 没有预设）属于正常情况。
 */
export function localAgentPreset(agentId: string): LocalAgentPreset | undefined {
  return BY_ID.get(agentId);
}
