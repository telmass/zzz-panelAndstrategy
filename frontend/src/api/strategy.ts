/**
 * 攻略数据的网络访问层——StrategyView 不再直接 `fetch`。
 *
 * 攻略 JSON 是 Vite 构建时通过 `strategyDataPlugin` 复制到
 * `dist/strategy/<slug>/data/` 的静态资源，不经过 `/api`；
 * 但仍收口到 `src/api/` 以保持「组件内禁止直接 fetch」的架构约束。
 */

export interface StrategyDataResponse {
  [key: string]: unknown;
}

/**
 * 按slug获取攻略数据。
 * 攻略数据是静态资源，路径为 `/strategy/<slug>/data/<slug>.json`。
 */
export async function fetchStrategyData(slug: string): Promise<StrategyDataResponse> {
  const response = await fetch(`/strategy/${slug}/data/${slug}.json`, {
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`策略数据请求失败 (${response.status}): ${slug}`);
  }
  return response.json() as Promise<StrategyDataResponse>;
}

/**
 * 按slug获取攻略编辑内容。
 */
export async function fetchStrategyContent(slug: string): Promise<StrategyDataResponse> {
  const response = await fetch(`/strategy/${slug}/data/${slug}.strategy.json`, {
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`策略内容请求失败 (${response.status}): ${slug}`);
  }
  return response.json() as Promise<StrategyDataResponse>;
}
