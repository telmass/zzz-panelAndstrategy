import { computed } from 'vue';

import { SUB_STATS, SUB_STAT_TOTAL_LIMIT, calculateAllSubStatLimits } from '@/constants/calculatorOptions';
import { normalizeCount } from '@/utils/clamp';
import { fmt } from '@/utils/fmt';
import { usePanelStore } from '@/stores/panelStore';
import type { RuleOption } from '@/constants/calculatorOptions';

/** 单项副词条的当前条数与该步进器按钮是否可用。 */
export interface SubStatEntry {
  def: RuleOption;
  count: number;
  /** 折算后的总值，按 `kind` 带 % 后缀。对应 legacy 的 `#sub_v_${id}`。 */
  total: string;
  canDecrease: boolean;
  canIncrease: boolean;
  /** 该副词条的动态上限 */
  limit: number;
}

/**
 * 副词条条数钳制。对应 legacy 的 `handleSubInput` 与 `adjustSubInput`。
 *
 * 规则有两层：
 * - 单项动态上限：基于主词条出现频率计算 (6 - 被排除盘位数) × 6
 * - 合计上限 54 条（6 盘 × 9 条）。
 *
 * legacy 的做法是「先改当前项，再看总数是否超标，超标就从当前项里扣掉超出量」，
 * 这里保持同样的语义：以最后被修改的那一项为回填对象。
 */
export function useSubStatLimit() {
  const panel = usePanelStore();

  /** 6 盘副词条合计条数。 */
  const totalCount = computed(() =>
    SUB_STATS.reduce((sum, stat) => sum + (panel.subStats[stat.id] ?? 0), 0),
  );

  /** 合计是否已达上限，用于把合计读数标红。 */
  const isTotalExceeded = computed(() => totalCount.value > SUB_STAT_TOTAL_LIMIT);

  /** 基于当前主词条选择计算的单项动态上限映射 */
  const subStatLimits = computed(() =>
    calculateAllSubStatLimits(panel.discMain.disc4, panel.discMain.disc5, panel.discMain.disc6),
  );

  /** 每项副词条的展示状态，按 `SUB_STATS` 顺序。 */
  const entries = computed<SubStatEntry[]>(() => {
    const total = totalCount.value;
    const limits = subStatLimits.value;
    return SUB_STATS.map((def) => {
      const count = panel.subStats[def.id] ?? 0;
      const limit = limits[def.id] ?? SUB_STAT_TOTAL_LIMIT;
      // 单条值里的 4.8 / 2.4 在二进制浮点下不精确，4.8*3 === 14.399999999999999，
      // 直接 String() 会把误差原样显示。走 fmt 与 legacy calculator.js:524 一致。
      const value = fmt(count * def.value);
      return {
        def,
        count,
        limit,
        total: count === 0 ? '0' : def.kind === 'pct' ? `${value}%` : value,
        canDecrease: count > 0,
        canIncrease: count < limit && total < SUB_STAT_TOTAL_LIMIT,
      };
    });
  });

  /**
   * 由步进按钮调整某项条数。对应 legacy 的 `adjustSubInput`。
   * 复用 `setCount` 的钳制逻辑，因此合计超限时回填的仍是本项。
   */
  function step(def: RuleOption, delta: number): void {
    setCount(def.id, (panel.subStats[def.id] ?? 0) + delta);
  }

  /**
   * 直接设置某项条数。对应 legacy 的 `handleSubInput`，
   * 用于数字输入框的 input 事件与预设重置。
   */
  function setCount(id: string, raw: unknown): void {
    const limits = subStatLimits.value;
    const limit = limits[id] ?? SUB_STAT_TOTAL_LIMIT;
    const next = normalizeCount(raw, limit);
    const others = totalCount.value - (panel.subStats[id] ?? 0);
    // 合计超限时从本项回填，宁可减少也不允许总数越界。
    const room = Math.max(0, SUB_STAT_TOTAL_LIMIT - others);
    panel.subStats[id] = Math.min(next, room);
  }

  return { entries, totalCount, isTotalExceeded, step, setCount };
}