/**
 * naive-ui 主题映射。
 *
 * naive-ui 自带一套蓝色主色（`#2080f0`），直接用会让靛蓝页面里出现蓝色控件。
 * 这里把它的 `common` 令牌**读自** `assets/styles/tokens.css` 的 CSS 变量，
 * 而不是把 hex 再抄一遍——项目约定是颜色一律走令牌、不得写死，
 * 抄一份就等于多一个会漂移的副本。
 *
 * 必须在组件 setup 期间调用（而非模块顶层）：顶层求值时样式表未必已注入，
 * `getComputedStyle` 会全部读到空串，静默退回 fallback。
 */

import type { GlobalThemeOverrides } from 'naive-ui';

/**
 * 读取一个 CSS 自定义属性的值。
 *
 * `getPropertyValue` 返回的串带前导空格（`var()` 的代入会保留），必须 trim，
 * 否则拼进 `font-family` 会因前导空格而失效。
 */
function token(name: string, fallback: string): string {
  if (typeof window === 'undefined') {
    return fallback;
  }
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

/**
 * 构造 naive-ui 的主题覆盖。
 *
 * 只覆盖主色、圆角、字体三类；其余（字号、间距、禁用态…）沿用 naive 默认值，
 * 避免把项目令牌表整个复制一份过来。
 */
export function naiveThemeOverrides(): GlobalThemeOverrides {
  return {
    common: {
      primaryColor: token('--color-accent', '#6366f1'),
      primaryColorHover: token('--color-accent-border-strong', '#818cf8'),
      primaryColorPressed: token('--color-accent-text', '#4338ca'),
      primaryColorSuppl: token('--color-accent-border-strong', '#818cf8'),
      borderRadius: token('--radius-md', '6px'),
      fontFamily: token('--font-sans', 'sans-serif'),
    },
  };
}