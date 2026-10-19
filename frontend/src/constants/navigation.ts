/**
 * 顶层功能板块导航清单——唯一真实源。
 *
 * `LauncherView` 的入口卡与站点导航条、`router/index.ts` 的路由守卫、
 * 以及前端测试的 manifest↔router 覆盖检查都从本文件取值。
 *
 * 新增功能板块时：先在此登记（`showAsCard` 或 `showInNav` 至少一项为 true），
 * 再在 `router/` 里注册路由；测试会强制两侧一致。
 *
 * 注意：`/strategy/:slug` 是详情子路由，不在此登记。
 */

export interface NavigationArea {
  /** 稳定标识（用于 CARD_FEATURES 等关联数据的 key） */
  id: string;
  /** 导航条与卡片上显示的中文名 */
  label: string;
  /** 路由路径（与 router/index.ts 的 path 完全一致） */
  path: string;
  /** 是否出现在顶部站点导航条 */
  showInNav: boolean;
  /** 是否在启动页以大卡片形式展示 */
  showAsCard: boolean;
}

/** 顶层功能板块（含首页），顺序即展示顺序。 */
export const NAVIGATION_AREAS: readonly NavigationArea[] = [
  { id: 'launcher', label: '首页', path: '/', showInNav: true, showAsCard: false },
  { id: 'calculator', label: '计算器', path: '/calculator', showInNav: true, showAsCard: true },
  { id: 'guide', label: '指南', path: '/guide', showInNav: true, showAsCard: true },
  { id: 'strategy', label: '攻略', path: '/strategy', showInNav: true, showAsCard: true },
] as const;

/** 站点导航链接（`showInNav: true` 的板块）。 */
export const NAV_LINKS: readonly NavigationArea[] = NAVIGATION_AREAS.filter((a) => a.showInNav);

/** 启动页入口卡（`showAsCard: true` 的板块）。 */
export const ENTRY_CARDS: readonly NavigationArea[] = NAVIGATION_AREAS.filter((a) => a.showAsCard);
