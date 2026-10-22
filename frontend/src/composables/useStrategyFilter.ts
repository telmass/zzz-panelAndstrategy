import { computed, ref, watch } from 'vue';

import { strategyGuides, type StrategyGuide } from '@/constants/strategyGuides';
import {
  EMPTY_STRATEGY_FILTER,
  isFilterEmpty,
  type StrategyFilter,
} from '@/types/strategy';

/**
 * 攻略选择页的筛选。
 *
 * 交互学的是米游社 WIKI 的代理人列表页（`zzz.gachabase.net/agents/beta`）：
 * 大标题 + 搜索框同一行，下面几排**图标方块**筛选（级别 / 属性 / 职业），
 * 末尾一个「重置」。
 *
 * 筛选状态写进 **URL 查询串**（`?q=&grade=&attr=&role=`），
 * 于是「只看 S 级异常」这种视图可以直接把链接发给别人——与计算器的
 * `?agent=`、配装方案的 `#build=` 是同一套思路。
 */

/** 维度之间「与」，同一维度内「或」。 */
function matches(guide: StrategyGuide, filter: StrategyFilter): boolean {
  const query = filter.query.trim().toLowerCase();
  if (query) {
    const haystack = `${guide.name} ${guide.shortName} ${guide.en}`.toLowerCase();
    if (!haystack.includes(query)) return false;
  }
  if (filter.grade && guide.grade !== filter.grade) return false;
  if (filter.attributes.length && !filter.attributes.includes(guide.attribute ?? '')) return false;
  if (filter.roles.length && !filter.roles.includes(guide.roleTag ?? '')) return false;
  return true;
}

function readFilterFromUrl(): StrategyFilter {
  if (typeof window === 'undefined') return { ...EMPTY_STRATEGY_FILTER };
  return parseFilterQuery(window.location.search);
}

/**
 * 把筛选条件编成 URL 查询串（`q=&grade=&attr=&role=`）。
 *
 * `base` 里的既有参数会保留（只覆盖这四个键），空值则删掉对应键。
 */
export function filterQuery(filter: StrategyFilter, base = ''): string {
  const params = new URLSearchParams(base);
  const set = (key: string, value: string) => {
    if (value) params.set(key, value);
    else params.delete(key);
  };
  set('q', filter.query.trim());
  set('grade', filter.grade);
  set('attr', filter.attributes.join(','));
  set('role', filter.roles.join(','));
  return params.toString();
}

/** 从 URL 查询串解出筛选条件。 */
export function parseFilterQuery(query: string): StrategyFilter {
  const params = new URLSearchParams(query);
  const list = (key: string) =>
    (params.get(key) ?? '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  return {
    query: params.get('q') ?? '',
    grade: params.get('grade') ?? '',
    attributes: list('attr'),
    roles: list('role'),
  };
}

function writeFilterToUrl(filter: StrategyFilter): void {
  if (typeof window === 'undefined') return;
  const query = filterQuery(filter, window.location.search);
  const url = `${window.location.pathname}${query ? `?${query}` : ''}`;
  window.history.replaceState(null, '', url);
}

/**
 * @param fallback URL 里没写筛选时用的兜底条件——「返回记忆」里存的那份。
 *   没有它，从详情页回到选择页会看到全量列表：列表内容变了，
 *   记下来的滚动位置也就对不上眼前的东西。
 */
export function useStrategyFilter(
  guides: StrategyGuide[] = strategyGuides,
  fallback?: StrategyFilter,
) {
  const fromUrl = readFilterFromUrl();
  const filter = ref<StrategyFilter>(
    isFilterEmpty(fromUrl) && fallback ? { ...fallback } : fromUrl,
  );

  /** 筛出来的代理人。 */
  const filtered = computed(() => guides.filter((guide) => matches(guide, filter.value)));

  /** 有没有任何筛选条件。 */
  const active = computed(() => !isFilterEmpty(filter.value));

  /** 选一个级别（单选；点已选的取消）。 */
  function toggleGrade(value: string): void {
    filter.value = { ...filter.value, grade: filter.value.grade === value ? '' : value };
  }

  /** 切一个属性 / 职业（多选）。 */
  function toggleIn(list: 'attributes' | 'roles', value: string): void {
    const current = filter.value[list];
    filter.value = {
      ...filter.value,
      [list]: current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    };
  }

  /** 清空全部筛选。 */
  function reset(): void {
    filter.value = { ...EMPTY_STRATEGY_FILTER };
  }

  // 筛选状态与 URL 保持同步：改筛选不刷新页面，但链接可分享。
  watch(filter, (value) => writeFilterToUrl(value), { deep: true });
  // 「返回记忆」还原出来的筛选也要立刻落到 URL 上——否则地址栏与页面不一致
  // （刷新一下就丢筛选了）。
  writeFilterToUrl(filter.value);

  return { filter, filtered, active, toggleGrade, toggleIn, reset };
}
