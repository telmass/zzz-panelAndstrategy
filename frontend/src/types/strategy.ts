/**
 * 攻略选择页的筛选状态。
 *
 * 三个维度取自官方 WIKI 的同一套分类：**级别**（S / A）、**属性**（火 / 冰 /
 * 电 / 以太 …）、**职业**（强攻 / 击破 / 异常 …）。阵营（Faction）不做——
 * 官方页面有，本项目的数据里没有。
 *
 * 维度之间是「与」，同一维度内多个取值是「或」。
 */
export interface StrategyFilter {
  /** 名称关键词（中 / 短名 / 英文名子串，不区分大小写）。 */
  query: string;
  /** 级别；空串 = 不限。**单选**。 */
  grade: string;
  /** 属性；空数组 = 不限。**多选**。 */
  attributes: string[];
  /** 职业；空数组 = 不限。**多选**。 */
  roles: string[];
}

/** 空筛选：全放行。 */
export const EMPTY_STRATEGY_FILTER: StrategyFilter = {
  query: '',
  grade: '',
  attributes: [],
  roles: [],
};

/** 筛选是否处于「什么都没选」的状态。 */
export function isFilterEmpty(filter: StrategyFilter): boolean {
  return (
    filter.query.trim() === '' &&
    filter.grade === '' &&
    filter.attributes.length === 0 &&
    filter.roles.length === 0
  );
}
