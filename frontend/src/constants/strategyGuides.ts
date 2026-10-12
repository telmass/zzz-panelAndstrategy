/**
 * 攻略板块登记表：每个条目对应 `strategy/<slug>/` 下的一个代理人攻略页，
 * 同时决定 `/strategy` 选择页的卡片与 `/strategy/<slug>` 路由是否可达。
 * 启动页只放静态的「代理人攻略」入口卡，与本表无关。
 *
 * 选择页卡片只展示**头像 + 名字**（版式对齐米游社 WIKI 频道页），因此登记表
 * 也只维护这两个展示元素所需的最小字段；职业、属性、评级等信息都在攻略页内，
 * 不在这里冗余一份。
 *
 * 新增代理人的流程（一次登记，两处生效）：
 * 1. 用 agent-strategy skill 产出 `strategy/<slug>/` 攻略页；
 * 2. 在下方 `strategyGuides` 追加一条——slug 必须与目录名一致，
 *    立绘按 `frontend/public/images/agents/<agentId>.png` 既有约定取路径。
 *
 * 攻略页本体不在这里维护：`strategy/` 下的静态页是唯一真实源，
 * 由 vite.config.ts 的 strategyPagesPlugin 挂载到 `/strategy/<slug>/`。
 */
export interface StrategyGuide {
  /** 攻略页目录名，同时是路由参数：`/strategy/<slug>`。 */
  slug: string;
  /** 代理人名称（卡片展示 + 攻略页标题）。 */
  name: string;
  /** 代理人预设 id，用于拼立绘路径 `/images/agents/<agentId>.png`。 */
  agentId: string;
}

/** 登记表顺序即选择页展示顺序。 */
export const strategyGuides: StrategyGuide[] = [
  {
    slug: 'ye-shun-guang',
    name: '叶瞬光',
    agentId: 'ep-1687',
  },
  {
    slug: 'ban-yue',
    name: '般岳',
    agentId: 'ep-1626',
  },
];

/** 立绘路径；`public/images/agents/` 缺图时由卡片自行兜底，不在这里判存在性。 */
export function agentPortraitUrl(agentId: string): string {
  return `/images/agents/${agentId}.png`;
}
