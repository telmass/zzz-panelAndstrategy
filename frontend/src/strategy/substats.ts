/**
 * 毕业面板「词条」展示口径。
 *
 * 计算始终使用完整的 54 条副词条（含小词条），本文件只负责**展示**：
 * - 大词条：暴击率 / 暴击伤害 / 大攻击% / 大防御% / 异常精通 / 异常掌控等；
 * - 小词条：小攻击、小防御、小生命、穿透值、无效词条等。
 *
 * 例如 Roxy 的 54 条 = 暴击率×24 + 攻击力%×12 + 暴击伤害×11（47）
 * + 攻击力×5 + 穿透值×2（7），展示为 47+7，而不是 54。
 */

export interface SubStatEntry {
  label: string;
  count: number;
}

export interface SubStatDisplay {
  total: number;
  major: number;
  minor: number;
  /** `47+7`；没有小词条时只显示 `47`。 */
  summary: string;
  /** 只列大词条，如 `暴击率 ×24、攻击力% ×12、暴击伤害 ×11`。 */
  breakdown: string;
  /** 页面/卡片上直接可用的完整文案。 */
  display: string;
  majorEntries: SubStatEntry[];
  minorEntries: SubStatEntry[];
}

const FLAT_LABELS = new Set(['小攻击', '小防御', '小生命', '攻击力', '防御力', '生命值']);
const PEN_LABELS = new Set(['穿透值', '穿透']);
const FILLER_LABELS = new Set(['无效词条', '填充', '其余词条']);

function sum(entries: SubStatEntry[]): number {
  return entries.reduce((total, entry) => total + entry.count, 0);
}

function parseEntries(value: string): Map<string, number> {
  const counts = new Map<string, number>();
  const listText = value.replace(/^[^：:=]*[：:=]/, '');
  for (const segment of listText.split(/[、,，；;]/)) {
    const match = /([^\d×xX+]+?)\s*[×xX]\s*(\d+)/.exec(segment);
    if (!match) continue;
    const label = match[1].replace(/\s+/g, '').trim();
    const count = Number(match[2]);
    if (!label || !Number.isFinite(count) || count <= 0) continue;
    counts.set(label, (counts.get(label) || 0) + count);
  }
  return counts;
}

/**
 * 把 `54 条满配：暴击率 ×24、攻击力% ×12、暴击伤害 ×11、攻击力 ×5、穿透值 ×2`
 * 解析成「大词条 + 小词条」的展示口径。
 */
export function formatSubStats(value: unknown): SubStatDisplay | null {
  const raw = String(value ?? '').trim();
  if (!raw) return null;
  const counts = parseEntries(raw);
  if (!counts.size) return null;

  const totalMatch = /(\d+)\s*条/.exec(raw);
  const declaredTotal = totalMatch ? Number(totalMatch[1]) : 0;

  const majorEntries: SubStatEntry[] = [];
  const minorEntries: SubStatEntry[] = [];

  for (const [label, count] of counts) {
    if (PEN_LABELS.has(label) || FLAT_LABELS.has(label) || FILLER_LABELS.has(label)) {
      minorEntries.push({ label, count });
    } else {
      majorEntries.push({ label, count });
    }
  }

  let major = sum(majorEntries);
  let minor = sum(minorEntries);
  const total = declaredTotal || major + minor;

  // 有些文案只列出影响阈值的词条，剩余条数按填充词条计入小词条。
  if (total > major + minor) {
    const rest = total - major - minor;
    minorEntries.push({ label: '其余词条', count: rest });
    minor = total - major;
  }

  const summary = minor > 0 ? `${major}+${minor}` : `${major}`;
  const breakdown = majorEntries.map((entry) => `${entry.label} ×${entry.count}`).join('、');
  const display = `${summary} 词条${breakdown ? `：${breakdown}` : ''}${minor > 0 ? `（+${minor} 小词条）` : ''}`;

  return {
    total,
    major,
    minor,
    summary,
    breakdown,
    display,
    majorEntries,
    minorEntries,
  };
}

/** 把标题里的 `54 词条` 换成 `47+7 词条`；标题没有数字时原样返回。 */
export function formatPanelTitle(title: unknown, sub: SubStatDisplay | null): string {
  const text = String(title ?? '').trim();
  if (!sub || !text) return text;
  if (/\d+\s*(词条|条)/.test(text)) {
    return text.replace(/\d+\s*(词条|条)/, `${sub.summary} 词条`);
  }
  return text;
}
