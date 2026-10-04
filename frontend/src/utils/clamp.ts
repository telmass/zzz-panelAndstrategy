/** 把数值钳制到 [min, max] 区间。 */
function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/**
 * 归一化副词条输入：丢弃非数值、按整数向下取整并钳制到 [0, limit]。
 * 对应 legacy 的 `handleSubInput` 中对单个输入框的处理。
 */
export function normalizeCount(raw: unknown, limit: number): number {
  const parsed = Number.parseFloat(String(raw));
  const floored = Math.floor(Number.isFinite(parsed) ? parsed : 0);
  return clamp(floored, 0, limit);
}