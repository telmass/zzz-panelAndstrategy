import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { buildStrategyCard } from '@/strategy/strategyCard';
import { strategyGuides } from '@/constants/strategyGuides';

const REPO_ROOT = resolve(__dirname, '../..');

function loadGuide(slug: string): Record<string, unknown> {
  const dataDir = resolve(REPO_ROOT, 'strategy', slug, 'data');
  const scraped = JSON.parse(readFileSync(resolve(dataDir, `${slug}.json`), 'utf-8'));
  scraped.strategy = JSON.parse(readFileSync(resolve(dataDir, `${slug}.strategy.json`), 'utf-8'));
  return scraped;
}

/**
 * 「保存攻略」导出图的内容必须由 strategy JSON 决定，而不是页面截图。
 * 这组用例锁住六个分支和关键数据映射，避免模板与数据字段脱节。
 */
describe('攻略缩略图卡片', () => {
  it('六个分支齐全，且技能/命座/武器/驱动盘/队伍/毕业面板都来自 JSON', () => {
    const card = buildStrategyCard(loadGuide('roxy'));

    expect(card.className).toBe('strategy-card strategy-card--export');
    expect(Array.from(card.querySelectorAll('.strategy-card__label')).map((node) => node.textContent)).toEqual([
      '技能加点',
      '命座推荐',
      '武器推荐',
      '驱动盘推荐',
      '队伍推荐',
      '毕业面板需求',
    ]);

    expect(card.querySelector('.strategy-card__tachie')?.getAttribute('src')).toBe(
      '/images/strategy/roxy/background.png',
    );

    expect(card.querySelectorAll('.strategy-card__skill')).toHaveLength(6);
    expect(card.textContent).toContain('Lv.12');
    expect(card.textContent).toContain('核心');

    expect(card.querySelectorAll('.strategy-card__cinema-slot')).toHaveLength(6);
    expect(card.querySelectorAll('.strategy-card__cinema-slot.is-key')).toHaveLength(3);
    expect(card.querySelector('.strategy-card__cinema-note')).toBeNull();

    expect(Array.from(card.querySelectorAll('.strategy-card__sub-item')).map((node) => node.textContent?.trim())).toEqual([
      '驱动盘属性',
      '4暴率',
      '5风伤',
      '6回能',
    ]);

    expect(card.textContent).toContain('绯月银棺');
    expect(card.textContent).toContain('福虓炉炉');
    expect(card.textContent).toContain('非锋御队');
    expect(card.textContent).toContain('锋御队');
    expect(card.textContent).toContain('山大王');
    expect(card.textContent).toContain('静听嘉音');
    expect(card.textContent).toContain('2 回能');

    expect(card.textContent).toContain('克洛丽');
    expect(card.textContent).toContain('佩洛耀');
    expect(card.textContent).toContain('满配毕业面板');
    expect(card.textContent).toContain('非满配毕业面板');
    expect(card.textContent).toContain('47+7 词条');
    expect(card.textContent).toContain('+7 小词条');
    expect(card.textContent).toContain('101%');
    expect(card.textContent).toContain('79.4%');
    expect(card.textContent).not.toContain('出招表');
  });

  it('缺少毕业生或攻略字段时降级为待拓展/占位，而不是报错', () => {
    const card = buildStrategyCard({});
    expect(card.querySelectorAll('.strategy-card__row')).toHaveLength(6);
    expect(card.textContent).toContain('待拓展');
    expect(card.querySelectorAll('.strategy-card__muted').length).toBeGreaterThan(0);
  });

  it('登记表里每个代理人都能生成卡片', () => {
    for (const guide of strategyGuides) {
      const card = buildStrategyCard(loadGuide(guide.slug));
      expect(card.querySelectorAll('.strategy-card__row'), `${guide.slug} 分支数不足`).toHaveLength(6);
      expect(card.querySelector('.strategy-card__portrait'), `${guide.slug} 缺少立绘容器`).not.toBeNull();
    }
  });
});
