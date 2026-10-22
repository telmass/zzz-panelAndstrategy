/**
 * 攻略选择页的「返回记忆」：滚动位置 + 筛选条件。
 *
 * 需求：从代理人详情页返回选择页时，页面要回到离开时的样子——
 * 滚动位置（回到原来那一屏）与筛选条件（列表内容不变，位置才有意义）。
 *
 * 为什么不用路由自带的 `savedPosition`：那只覆盖浏览器的「后退」；
 * 站内「返回代理人选择」是 push 导航，路由拿不到历史位置，得自己记。
 *
 * 存 `sessionStorage`：按标签页隔离，刷新页面也还在（纯内存刷新即失）。
 */

/** 存储键。与旧实现的 `strategyPickerScroll` 不同名——那份只存了位置，且位置根本没还回去。 */
const STORAGE_KEY = 'strategyPickerMemory';

export interface PickerMemory {
  /** 离开选择页时的滚动位置（`window.scrollY`）。 */
  scrollTop: number;
  /** 离开时的筛选查询串（`q=&grade=&attr=&role=`），回来时按它还原列表。 */
  query: string;
}

/** 读记忆；没有或读坏了都返回 null（当作「没有记忆」，回到顶部）。 */
export function readPickerMemory(): PickerMemory | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<PickerMemory>;
    if (typeof parsed.scrollTop !== 'number' || !Number.isFinite(parsed.scrollTop)) return null;
    return {
      scrollTop: Math.max(0, parsed.scrollTop),
      query: typeof parsed.query === 'string' ? parsed.query : '',
    };
  } catch {
    return null;
  }
}

/** 写记忆。写不进去（隐私模式等）就算了——少一次记忆而已，不该因此报错。 */
export function writePickerMemory(memory: PickerMemory): void {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(memory));
  } catch {
    /* 同上 */
  }
}
