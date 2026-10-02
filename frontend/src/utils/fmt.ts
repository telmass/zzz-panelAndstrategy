/**
 * 数值格式化。规则逐条对齐 legacy/scripts/calculator.js 的 `fmt`：
 *
 * 1. 先用 `toFixed(10)` 消化浮点误差，再转回数字；
 * 2. 与四舍五入后的整数差小于 1e-7 时，按千分位整数输出；
 * 3. 否则保留两位小数。
 *
 * 第 3 步下沉 Python 后，这里的规则需与后端格式化函数保持一致，
 * `tests/legacy-parity.spec.ts` 是两侧的共同基准。
 */
export function fmt(n: number): string {
  const fixed = Number(n.toFixed(10));
  if (Math.abs(fixed - Math.round(fixed)) < 0.0000001) {
    return Math.round(fixed).toLocaleString();
  }
  return Number(fixed.toFixed(2)).toString();
}

/** HTML 转义，用于明细文案。对应 legacy 的 `escapeHtml`。 */
export function escapeHtml(value: string): string {
  return value.replace(
    /[&<>"']/g,
    (char) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      })[char] as string,
  );
}