import { h, type VNodeChild } from 'vue';
import type { CascaderOption } from 'naive-ui';

import { AGENT_ROLE_TAGS, WEAPON_ROLE_TAGS } from '@/constants/calculatorOptions';

/**
 * 职业标签全集。
 *
 * 取 `AGENT_ROLE_TAGS` 与 `WEAPON_ROLE_TAGS` 的**并集**：两张表当前取值一致
 * 但语义独立（一个是代理人阵营，一个是音擎适配定位），任一张将来扩容时
 * 下面的 `ROLE_ICON` 若漏配新键，`vue-tsc` 会直接报错，而不是运行时静默缺图。
 */
export type RoleTag = (typeof AGENT_ROLE_TAGS)[number] | (typeof WEAPON_ROLE_TAGS)[number];

/**
 * 职业标签 → roletag 图标文件名（不含扩展名）。
 *
 * 取值是官方 Wiki 的 profession key，与既有抓取脚本
 * `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py:39-47`
 * 同源，不另造一套拼音或意译——`armero`（锋御）看着费解，但改了就与脚本脱节。
 */
const ROLE_ICON: Record<RoleTag, string> = {
  强攻: 'strike',
  击破: 'pierce',
  异常: 'abnormal',
  支援: 'support',
  防护: 'guard',
  命破: 'rupture',
  锋御: 'armero',
};

/** cascader 的 `value` 可能是 `string | number`，取不到字符串时按空处理。 */
function optionValue(option: CascaderOption): string {
  return typeof option.value === 'string' ? option.value : '';
}

/** 调用方需要按领域差异化的两处参数。 */
export interface CascaderRendererOptions {
  /** 二级（叶子）图标目录，如 `/images/weapons`。 */
  leafIconDir: string;
  /** 二级选项名称解析，用于浏览时只显示名称；返回 undefined 时退回 label。 */
  leafName: (id: string) => string | undefined;
}

/**
 * 选项前缀图片路径；无法确定时返回空串。
 *
 * 以 `children` 判层级而非查表：一级项带 `children`（职业标签组），
 * 二级项是叶子（`value` 即音擎或代理人 id）。查表只用于一级项取 slug。
 *
 * 返回空串而不是拼一个可能不存在的路径：破图在浏览器里会显示成小方块图标，
 * 正是这里要避免的观感。`public/` 原样拷贝到 `dist/` 根，故按 URL 取而非 import。
 */
function optionIconSrc(option: CascaderOption, leafIconDir: string): string {
  const value = optionValue(option);
  if (!value) {
    return '';
  }
  if (option.children?.length) {
    const slug = ROLE_ICON[value as RoleTag];
    return slug ? `/images/icons/${slug}.png` : '';
  }
  return `${leafIconDir}/${value}.png`;
}

/**
 * 代理人与音擎选择器共用的两个 cascader 渲染器。
 *
 * 两者的层级结构、图标规则与文案策略完全一致，差别只在「叶子 id 指向哪个目录」
 * 与「叶子的名称去哪张表里取」。把这些差异收敛成构造参数，
 * 两个模块的渲染行为便由构造保证一致，而不是靠人工同步两份近乎相同的代码。
 */
export function createCascaderRenderers(options: CascaderRendererOptions): {
  renderOptionPrefix: (props: { option: CascaderOption }) => VNodeChild;
  renderOptionLabel: (option: CascaderOption) => string | undefined;
} {
  /**
   * naive-ui 的 `render-prefix`：给每个选项渲染前缀节点。
   *
   * `option` 是 `tmNode.rawNode`，即 store 交给 cascader 的原始选项对象，
   * 故这里只读 `value` / `children` 判断层级，不新增任何字段——
   * 数据结构与 store 均不受影响。
   */
  function renderOptionPrefix({ option }: { option: CascaderOption }): VNodeChild {
    const src = optionIconSrc(option, options.leafIconDir);
    if (!src) {
      return null;
    }
    return h('img', {
      class: 'cascader-option-icon',
      src,
      // 装饰性图标，标签文字已表达含义，避免读屏重复朗读
      alt: '',
      loading: 'lazy',
      // 资源真缺时隐藏，而不是留一个破图方块
      onError: (event: Event) => {
        (event.target as HTMLImageElement).style.display = 'none';
      },
    });
  }

  /**
   * 菜单选项文案：浏览过程中二级项只显示名称。
   *
   * 完整文案「名称 / 职业 / …」仍留在选项的 `label` 字段上，因此
   * **选中后折叠框显示的仍是完整文案**——前提是调用方显式关掉了
   * `show-path`。naive-ui 的 `Cascader.mjs` 里 `selectedOption` 是
   * `showPath ? getPathLabel(node, separator, labelField) : rawNode[labelField]`：
   * `showPath` 默认为 `true`，会把一级分组与叶子两段的 label 一起拼起来，
   * 而一级正是职业标签、叶子文案里又有同一个职业标签，于是折叠框里
   * 职业标签会出现两次。`renderLabel` 只管浏览菜单，不影响折叠框。
   *
   * 一级项是职业标签分组，按 `children` 判定后原样返回 `label`。
   * 二级项按 `value`（条目 id）由调用方解析出 `name`，
   * 而不切分 `label` 字符串——名称里若出现分隔符，切分会取错。
   */
  function renderOptionLabel(option: CascaderOption): string | undefined {
    if (option.children?.length) {
      return option.label;
    }
    return options.leafName(optionValue(option)) ?? option.label;
  }

  return { renderOptionPrefix, renderOptionLabel };
}