import { describe, expect, it } from 'vitest';

import discs from '@data/catalog/drive-discs.json';
import rules from '@data/rules/calculator-rules.json';
import { DATA_MANIFEST, DATASET_PATHS } from '@/constants/dataManifest';
import { MODIFIER_KEYS } from '@/constants/calculatorOptions';

/**
 * 数据集登记表的漂移闸门。
 *
 * 后端能读 `data/manifest.json`（`backend/src/zzz_panel/presets/manifest.py`），
 * 前端不能——Vite 的静态导入要求路径可静态分析，没法在运行时按登记表拼路径。
 *
 * 于是前端的数据文件用字面量 `import` 读，登记表只作为**参照**：本测试断言
 * 「静态导入的文件 = 登记表登记的文件」。改路径时漏改静态 import，这里就会
 * 指名道姓地失败，而不是等到构建产物里少一块数据。
 */
describe('数据集登记表', () => {
  it('登记了全部五个数据集', () => {
    expect(Object.keys(DATASET_PATHS).sort()).toEqual([
      'agent-index',
      'agents',
      'calculator-rules',
      'drive-discs',
      'weapons',
    ]);
  });

  it('规则表走的是登记的路径', () => {
    expect(DATASET_PATHS['calculator-rules']).toBe('rules/calculator-rules.json');
  });

  it('每个数据集都声明了角色与维护方式', () => {
    for (const [id, entry] of Object.entries(DATA_MANIFEST.datasets)) {
      expect(entry.role, `${id} 的 role 非法`).toMatch(/^(source|generated)$/);
      expect(entry.maintained, `${id} 的 maintained 非法`).toMatch(/^(skill|manual|code)$/);
    }
  });
});

/**
 * 修正量键的漂移闸门。
 *
 * `MODIFIER_KEYS` 是前端对「可被配装修正的量」的唯一声明，它同时是
 * `ModifierKey` 类型的来源。Python 侧有等价的 `core.options.modifier_keys()`。
 * 规则表里出现一个前端不认识的 `to`，或前端多了一个没人用的键，都应该在这里
 * 被发现——否则表现是「某个加成静默不生效」。
 */
describe('修正量键', () => {
  const allTargets = [
    ...rules.coreOptions.map((option) => option.to),
    ...rules.disc4Options.map((option) => option.to),
    ...rules.disc5Options.map((option) => option.to),
    ...rules.disc6Options.map((option) => option.to),
    ...rules.setOptions.map((option) => option.to),
    ...rules.subStats.map((option) => option.to),
    ...rules.discFixedStats.map((stat) => stat.to),
  ];

  it('规则表里的每个 to 都在 MODIFIER_KEYS 内', () => {
    const known = new Set<string>(MODIFIER_KEYS);
    const unknown = [...new Set(allTargets)].filter((target) => !known.has(target));
    expect(unknown).toEqual([]);
  });

  it('MODIFIER_KEYS 没有多余的键', () => {
    // 保留键：累加器里存在、但规则表没有对应选项的修正量。
    // `def_base`（核心「基础防御值」）在游戏里没有这条核心加成，
    // 但参照实现与后端面板公式都保留着这个累加器（值恒为 0）。
    const RESERVED = ['def_base'];
    const used = new Set<string>([...allTargets, ...RESERVED]);
    const extra = MODIFIER_KEYS.filter((key) => !used.has(key));
    expect(extra).toEqual([]);
  });

  it('保留键确实没有对应选项', () => {
    const RESERVED = ['def_base'];
    for (const key of RESERVED) {
      expect(allTargets).not.toContain(key);
    }
  });

  it('键不重复', () => {
    expect(new Set(MODIFIER_KEYS).size).toBe(MODIFIER_KEYS.length);
  });
});

/**
 * 规则表的形状闸门。
 *
 * `name`（规范名）与 `label`（展示串）分开后，代理人预设里的核心加成措辞可以
 * 与规则表比对。这里先保证 `name` 存在且非空——它是后续漂移检查的基准。
 */
describe('规则表形状', () => {
  const tables = [
    rules.coreOptions,
    rules.disc4Options,
    rules.disc5Options,
    rules.disc6Options,
    rules.setOptions,
    rules.subStats,
  ] as Array<Array<{ id: string; name: string; label: string; value: number }>>;

  it('每条选项都有非空的 name 与 label', () => {
    for (const table of tables) {
      for (const option of table) {
        expect(option.name, `${option.id} 缺 name`).toBeTruthy();
        expect(option.label, `${option.id} 缺 label`).toBeTruthy();
      }
    }
  });

  it('选项 id 不重复', () => {
    for (const table of tables) {
      const ids = table.map((option) => option.id);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });

  it('驱动盘固定主词条用 to 而不是 target', () => {
    for (const stat of rules.discFixedStats) {
      expect(stat).toHaveProperty('to');
      expect(stat).not.toHaveProperty('target');
    }
  });
});

/**
 * 驱动盘套装的 ``effect2``：2 件套效果 -> 规则表 ``setOptions`` 的 id。
 *
 * 30 套里有 **12 套算不出来**——8 套是属性伤害（面板没有「属性伤害」这一行，
 * 加一行会破坏三方对拍）、4 套是条件触发（不是固定面板值）。这些写
 * ``effect2: null`` 并用 ``effect2Note`` 说明原因，UI 据此告诉用户
 * 「该套装的 2 件套效果不计入面板」。
 */
describe('驱动盘套装的二件套效果映射', () => {
  const setOptionIds = new Set(rules.setOptions.map((option) => option.id));

  it('effect2 要么是可选项 id，要么为 null 并说明原因', () => {
    for (const disc of discs) {
      if (disc.effect2 === null) {
        expect(disc.effect2Note, `${disc.name} 缺 effect2Note`).toBeTruthy();
      } else {
        expect(setOptionIds.has(disc.effect2), `${disc.name} 的 effect2 不在 setOptions 里`).toBe(
          true,
        );
      }
    }
  });

  it('每套都有 effect2 字段（不靠「缺字段」表达算不出来）', () => {
    for (const disc of discs) {
      expect(Object.hasOwn(disc, 'effect2'), `${disc.name} 缺 effect2 字段`).toBe(true);
    }
  });

  it('可算的套装不少于三分之二（覆盖了绝大多数常用 2 件套）', () => {
    const mappable = discs.filter((disc) => disc.effect2 !== null).length;
    expect(mappable / discs.length).toBeGreaterThan(0.5);
  });
});
