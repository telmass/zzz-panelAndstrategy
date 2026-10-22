import { describe, expect, it } from 'vitest';

import {
  FIXED_MAIN_STATS,
  MAIN_STAT_OPTIONS,
  SET_OPTION_ROWS,
  SUB_STAT_ROWS,
  mainStatValue,
} from '@/constants/guideRules';

/**
 * 学习页（`/guide`）的**数值必须来自规则表**。
 *
 * 这些表此前是**手写**在模板里的，于是它们与规则表**漂移**了两次：
 * 6 号位「冲击力」从 24% 改成 18%、5 号位「增伤」正名为「属性伤害」，
 * 学习页都跟着错了。现在它们由 `constants/guideRules.ts` 从
 * `data/rules/calculator-rules.json` 派生——这个测试就是那道保险。
 */
describe('学习页数值从规则表派生', () => {
  it('6 号位冲击力是 18%（不是 24%）', () => {
    expect(mainStatValue('disc6', '冲击力')).toBe('+18%');
    const impact = MAIN_STAT_OPTIONS.disc6.find((option) => option.name === '冲击力');
    expect(impact?.value).toBe('+18%');
  });

  it('5 号位是属性伤害 30%（不是通用增伤）', () => {
    const damage = MAIN_STAT_OPTIONS.disc5.find((option) => option.name === '属性伤害');
    expect(damage?.value).toBe('+30%');
    expect(MAIN_STAT_OPTIONS.disc5.some((option) => option.name === '增伤')).toBe(false);
  });

  it('4 号位六项齐全，数值与规则表一致', () => {
    expect(MAIN_STAT_OPTIONS.disc4).toHaveLength(6);
    const names = MAIN_STAT_OPTIONS.disc4.map((option) => option.name);
    expect(names).toEqual(['攻击力', '生命值', '防御力', '暴击率', '暴击伤害', '异常精通']);
    expect(MAIN_STAT_OPTIONS.disc4.find((o) => o.name === '暴击率')?.value).toBe('+24%');
    expect(MAIN_STAT_OPTIONS.disc4.find((o) => o.name === '异常精通')?.value).toBe('+92');
  });

  it('固定主词条是 2200 / 316 / 184', () => {
    expect(FIXED_MAIN_STATS.map((row) => row.value)).toEqual(['+2200', '+316', '+184']);
  });

  it('副词条 10 项，每档数值取自规则表', () => {
    expect(SUB_STAT_ROWS).toHaveLength(10);
    const byName = Object.fromEntries(SUB_STAT_ROWS.map((row) => [row.name, row.value]));
    expect(byName['暴击率']).toBe('+2.4%');
    expect(byName['暴击伤害']).toBe('+4.8%');
    expect(byName['穿透值']).toBe('+9');
    expect(byName['异常精通']).toBe('+9');
  });

  it('2 件套效果取自规则表（含属性伤害 +10%）', () => {
    const byName = Object.fromEntries(SET_OPTION_ROWS.map((row) => [row.name, row.value]));
    expect(byName['属性伤害']).toBe('+10%');
    expect(byName['暴击伤害']).toBe('+16%');
    expect(byName['异常精通']).toBe('+30');
  });
});
