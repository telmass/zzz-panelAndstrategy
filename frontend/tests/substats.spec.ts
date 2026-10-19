import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { formatPanelTitle, formatSubStats } from '@/strategy/substats';
import { strategyGuides } from '@/constants/strategyGuides';

const REPO_ROOT = resolve(__dirname, '../..');

function panelList(slug: string): Array<Record<string, any>> {
  const dataDir = resolve(REPO_ROOT, 'strategy', slug, 'data');
  const strategy = JSON.parse(readFileSync(resolve(dataDir, `${slug}.strategy.json`), 'utf-8'));
  return [strategy.graduationPanel, strategy.graduationPanelAlt].filter(
    (panel) => panel && panel.build && panel.build.subStats,
  );
}

function mainPanel(slug: string): Record<string, any> {
  const dataDir = resolve(REPO_ROOT, 'strategy', slug, 'data');
  const strategy = JSON.parse(readFileSync(resolve(dataDir, `${slug}.strategy.json`), 'utf-8'));
  return strategy.graduationPanel;
}

describe('副词条展示口径', () => {
  it('洛茜 54 条拆成 47+7，并隐藏小攻击与穿透值', () => {
    const panel = mainPanel('roxy');
    const sub = formatSubStats(panel.build.subStats);

    expect(sub).not.toBeNull();
    expect(sub?.summary).toBe('47+7');
    expect(sub?.breakdown).toBe('暴击率 ×24、攻击力% ×12、暴击伤害 ×11');
    expect(sub?.minorEntries).toEqual([
      { label: '攻击力', count: 5 },
      { label: '穿透值', count: 2 },
    ]);
    expect(formatPanelTitle(panel.title, sub)).toBe('满配毕业面板（47+7 词条，100%暴率档）');
  });

  it('莱特 47+7、克拉蕾 37+17、叶瞬光 45+9', () => {
    expect(formatSubStats(mainPanel('lighter').build.subStats)?.summary).toBe('47+7');

    const claret = formatSubStats(mainPanel('claret').build.subStats);
    expect(claret?.summary).toBe('37+17');
    expect(claret?.breakdown).toBe('暴击率 ×19、防御力% ×15、暴击伤害 ×3');

    const ye = formatSubStats(mainPanel('ye-shunguang').build.subStats);
    expect(ye?.summary).toBe('45+9');
    expect(ye?.breakdown).toBe('暴击率 ×13、暴击伤害 ×16、攻击力% ×16');
  });

  it('非满配面板沿用同一口径：克拉蕾 31 条 → 29+2', () => {
    const alt = panelList('claret')[1];
    const sub = formatSubStats(alt.build.subStats);
    expect(sub?.summary).toBe('29+2');
    expect(formatPanelTitle(alt.title, sub)).toBe('非满配毕业面板（29+2 词条）');
  });

  it('登记表内所有毕业面板都能解析，且标题中的条数被替换', () => {
    for (const guide of strategyGuides) {
      for (const panel of panelList(guide.slug)) {
        const sub = formatSubStats(panel.build.subStats);
        expect(sub, guide.slug).not.toBeNull();
        if (panel.title && /\d+\s*(词条|条)/.test(panel.title)) {
          expect(formatPanelTitle(panel.title, sub), guide.slug).toContain(sub!.summary);
        }
      }
    }
  });
});
