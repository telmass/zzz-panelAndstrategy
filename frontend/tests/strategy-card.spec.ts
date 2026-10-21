import { describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { buildStrategyCard, copyStrategyCard } from '@/strategy/strategyCard';
import { strategyGuides } from '@/constants/strategyGuides';

const REPO_ROOT = resolve(__dirname, '../..');

function loadGuide(slug: string): Record<string, unknown> {
  const dataDir = resolve(REPO_ROOT, 'strategy', slug, 'data');
  const scraped = JSON.parse(readFileSync(resolve(dataDir, `${slug}.json`), 'utf-8'));
  scraped.strategy = JSON.parse(readFileSync(resolve(dataDir, `${slug}.strategy.json`), 'utf-8'));
  return scraped;
}

const MAIN_A = [
  { slot: '4 号位', main: '暴击率 +24%', alt: '无', note: '' },
  { slot: '5 号位', main: '风属性伤害 +30%', alt: '穿透率 +24%', note: '' },
];

const MAIN_B = [
  { slot: '4 号位', main: '暴击伤害 +48%', alt: '无', note: '' },
  { slot: '5 号位', main: '暴击率 +24%', alt: '无', note: '' },
];

function driveBuild(name: string, mainStats: Array<Record<string, unknown>>) {
  return {
    name,
    set4: { name: '山大王', label: '攻击力 +12%', icon: '/images/discs/ep-1346.webp' },
    set2: {
      main: [{ name: '静听嘉音', label: '能量自动回复 +20%', icon: '/images/discs/ep-1551.webp' }],
    },
    mainStats,
  };
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
      '面板参考',
    ]);

    expect(card.querySelector('.strategy-card__tachie')?.getAttribute('src')).toBe(
      '/images/strategy/roxy/background.webp',
    );

    expect(card.querySelectorAll('.strategy-card__skill')).toHaveLength(6);
    expect(card.textContent).toContain('Lv.12');
    expect(card.textContent).toContain('核心');

    expect(card.querySelectorAll('.strategy-card__cinema-slot')).toHaveLength(6);
    expect(card.querySelectorAll('.strategy-card__cinema-slot.is-key')).toHaveLength(3);
    expect(card.querySelector('.strategy-card__cinema-note')).toBeNull();

    expect(card.querySelectorAll('.strategy-card__main')).toHaveLength(3);
    expect(Array.from(card.querySelectorAll('.strategy-card__main-slot')).map((node) => node.textContent?.trim())).toEqual([
      '4 号位',
      '5 号位',
      '6 号位',
    ]);
    const mains = Array.from(card.querySelectorAll('.strategy-card__main')).map(
      (node) => node.textContent?.trim() || '',
    );
    expect(mains[0]).toContain('暴击率');
    expect(mains[0]).not.toContain('+24%');
    expect(mains[1]).toContain('风属性伤害');
    expect(card.querySelector('.strategy-card__main-alt')?.textContent).toContain('穿透率 / 攻击力');
    expect(mains[2]).toContain('能量回复');
    expect(mains[2]).not.toContain('+60%');
    expect(card.querySelectorAll('.strategy-card__main-alt')).toHaveLength(1);

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

  it('主词条卡片展示首选与备选、隐藏数值，并按方案分组', () => {
    const card = buildStrategyCard(loadGuide('lighter'));
    const groups = Array.from(card.querySelectorAll('.strategy-card__main')).map(
      (node) => node.textContent?.trim() || '',
    );
    expect(groups).toHaveLength(3);
    expect(groups[0]).toContain('暴击率');
    expect(groups[0]).toContain('暴击伤害');
    expect(groups[1]).toContain('火属性伤害');
    expect(groups[1]).toContain('攻击力');
    expect(groups[2]).toContain('冲击力');
    expect(groups.join('')).not.toMatch(/\+\d/);

    // 用户示例：异常精通 +92 在导出卡片里只保留「异常精通」。
    const synthetic = buildStrategyCard({
      strategy: {
        driveBuilds: [
          {
            mainStats: [
              { slot: '4 号位', main: '异常精通 +92', alt: '攻击力 +30% / 暴击率 +24%' },
            ],
          },
        ],
      },
    });
    const syntheticMain = synthetic.querySelector('.strategy-card__main');
    expect(syntheticMain?.textContent).toContain('异常精通');
    expect(syntheticMain?.textContent).toContain('攻击力 / 暴击率');
    expect(syntheticMain?.textContent).not.toContain('+92');
    expect(syntheticMain?.textContent).not.toContain('+30%');

    // 两套方案主词条相同 → 仍然只渲染一行主词条。
    const shared = buildStrategyCard({
      strategy: {
        driveBuilds: [
          driveBuild('非锋御队：4 山大王', MAIN_A),
          driveBuild('锋御队：4 静听嘉音', MAIN_A),
        ],
      },
    });
    expect(shared.querySelectorAll('.strategy-card__mains-row')).toHaveLength(1);
    expect(shared.querySelector('.strategy-card__mains-label')?.textContent).toBe('主词条');

    // 两套方案主词条不同 → 各自成组，主词条紧跟对应方案。
    const split = buildStrategyCard({
      strategy: {
        driveBuilds: [
          driveBuild('非锋御队：4 山大王', MAIN_A),
          driveBuild('锋御队：4 静听嘉音', MAIN_B),
        ],
      },
    });
    const rows = split.querySelectorAll('.strategy-card__mains-row');
    expect(split.querySelectorAll('.strategy-card__build-group')).toHaveLength(2);
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain('非锋御队');
    expect(rows[0].textContent).toContain('风属性伤害');
    expect(rows[1].textContent).toContain('锋御队');
    expect(rows[1].textContent).toContain('暴击伤害');
  });

  it('缺少毕业生或攻略字段时降级为待拓展/占位，而不是报错', () => {
    const card = buildStrategyCard({});
    expect(card.querySelectorAll('.strategy-card__row')).toHaveLength(6);
    expect(card.textContent).toContain('待拓展');
    expect(card.querySelectorAll('.strategy-card__muted').length).toBeGreaterThan(0);
  });

  it('导出卡片布局只用 flex，并显式重置启动页卡片继承的 column 方向', () => {
    const css = readFileSync(resolve(REPO_ROOT, 'frontend/src/strategy/strategy.css'), 'utf-8');
    const cardBlocks = css.match(/\.strategy-card[^{]*\{[^}]*\}/g) ?? [];

    // html2canvas 不支持 grid，导出卡片里出现 grid 会被拍平成竖排。
    expect(cardBlocks.filter((block) => /display:\s*grid/.test(block))).toEqual([]);

    // components.css 的启动页 `.strategy-card` 是 column + align-items:center，
    // 导出卡片必须显式重置，否则立绘与内容会上下堆叠。
    const rootBlock = cardBlocks.find((block) => block.startsWith('.strategy-card.strategy-card--export'));
    expect(rootBlock).toBeDefined();
    expect(rootBlock).toMatch(/flex-direction:\s*row/);
    expect(rootBlock).toMatch(/align-items:\s*stretch/);
    expect(rootBlock).toMatch(/justify-content:\s*flex-start/);
  });

  it('登记表里每个代理人都能生成卡片', () => {
    for (const guide of strategyGuides) {
      const card = buildStrategyCard(loadGuide(guide.slug));
      expect(card.querySelectorAll('.strategy-card__row'), `${guide.slug} 分支数不足`).toHaveLength(6);
      expect(card.querySelector('.strategy-card__portrait'), `${guide.slug} 缺少立绘容器`).not.toBeNull();
    }
  });
});

/**
 * 驱动盘**装备组**在导出卡片上的排版。
 *
 * **组**（并列，都要装）：`set2` / `set2b` / `set2c`——第 1/2/3 组 2 件套；
 * **候选**（组内二选一）：组内的 `main` / `alt`。
 *
 * 2+2+2 的配装**没有 4 件套组**，所以「4 件套」那一栏整个不渲染——
 * 留个空栏会让人以为漏了内容。
 */
describe('导出卡片上的驱动盘装备组', () => {
  function buildFor(build: Record<string, unknown>) {
    const guide = loadGuide('roxy');
    (guide.strategy as { driveBuilds: unknown[] }).driveBuilds = [build];
    return buildStrategyCard(guide);
  }

  function chipsOf(card: HTMLElement) {
    return Array.from(card.querySelectorAll('.strategy-card__set')).map((chip) => ({
      text: chip.querySelector('b')?.textContent?.trim() ?? '',
      icons: chip.querySelectorAll('.strategy-card__set-icon').length,
    }));
  }

  it('4+2：仍是「4 件套 + 2 件套」两栏', () => {
    const card = buildFor({
      name: '非锋御队',
      set4: [{ name: '山大王', label: '攻击力 +12%', icon: '/images/discs/ep-1346.webp' }],
      set2: { main: [{ name: '摇摆爵士', label: '能量自动回复 +20%', icon: '/images/discs/ep-231.webp' }] },
      mainStats: [],
    });
    const chips = chipsOf(card);
    expect(chips.length).toBe(2);
    expect(chips[0].text).toBe('4 山大王');
    expect(chips[1].text).toBe('2 回能');
  });

  it('2+2+2：渲染三组 2 件套，且不渲染「4 件套」栏', () => {
    const card = buildFor({
      name: '自身循环',
      set4: null,
      set2: { main: [{ name: '月光骑士颂', label: '能量自动回复 +20%', icon: '/images/discs/ep-1551.webp' }] },
      set2b: { main: [{ name: '摇摆爵士', label: '能量自动回复 +20%', icon: '/images/discs/ep-231.webp' }] },
      set2c: { main: [{ name: '啄木鸟电音', label: '暴击率 +8%', icon: '/images/discs/ep-232.webp' }] },
      mainStats: [],
    });
    const chips = chipsOf(card);
    expect(chips.length).toBe(3);
    // 没有 4 件套组，就不该出现「4 件套」这一栏
    expect(chips.some((chip) => chip.text.startsWith('4 '))).toBe(false);
    // 三组各自编号 + 名字（组内的效果可能相同，靠名字区分）
    expect(chips[0].text).toBe('2 件套 ① 月光骑士颂');
    expect(chips[1].text).toBe('2 件套 ② 摇摆爵士');
    expect(chips[2].text).toBe('2 件套 ③ 啄木鸟电音');
    // 每组一个图标
    expect(chips.map((chip) => chip.icons)).toEqual([1, 1, 1]);
  });

  it('真实数据：洛克茜的第三种配装（2+2+2）在卡片上是三组', () => {
    const card = buildStrategyCard(loadGuide('roxy'));
    const rows = Array.from(card.querySelectorAll('.strategy-card__build'));
    const twoPlusTwoPlusTwo = rows.find((row) =>
      row.querySelector('.strategy-card__build-label')?.textContent?.includes('自身循环'),
    );
    expect(twoPlusTwoPlusTwo, '卡片上找不到 2+2+2 的方案行').toBeTruthy();
    const chips = Array.from(twoPlusTwoPlusTwo!.querySelectorAll('.strategy-card__set')).map(
      (chip) => chip.querySelector('b')?.textContent?.trim() ?? '',
    );
    expect(chips.length).toBe(3);
    expect(chips[0]).toContain('月光骑士颂');
    expect(chips[1]).toContain('摇摆爵士');
    expect(chips[2]).toContain('啄木鸟电音');
  });
});

/**
 * 导出卡片的**尺寸契约**与**交付方式**。
 *
 * - 卡片横向 1600px：1360px 时「主词条」表的「备选」列（"穿透率 +24% / 攻击力 +30%"）
 *   会折行。
 * - 主词条单元按内容分配宽度（``flex: 1 1 auto``）：文案长的那个盒子更宽，
 *   不再三个等分硬挤。
 * - 「保存攻略」下载、「复制攻略」进剪贴板，**同一张图**。
 */
describe('导出卡片的尺寸与交付', () => {
  const css = readFileSync(resolve(REPO_ROOT, 'frontend/src/strategy/strategy.css'), 'utf-8');

  it('卡片横向宽度是 1600px', () => {
    const block = (css.match(/\.strategy-card\.strategy-card--export\s*\{[^}]*\}/) ?? [''])[0];
    expect(block).toMatch(/width:\s*1600px/);
  });

  it('主词条单元按内容分配宽度，不是三个等分', () => {
    const block = (css.match(/\.strategy-card__main\s*\{[^}]*\}/) ?? [''])[0];
    expect(block).toMatch(/flex:\s*1 1 auto/);
  });

  it('主词条标签列收窄，把横向空间让给单元', () => {
    const block = (css.match(/\.strategy-card__mains-label\s*\{[^}]*\}/) ?? [''])[0];
    expect(block).toMatch(/flex:\s*0 0 76px/);
  });
});

describe('复制攻略：写进系统剪贴板', () => {
  it('剪贴板可用时把 PNG 写进剪贴板，不触发下载', async () => {
    const written: Blob[] = [];
    const write = vi.fn(async (items: Blob[]) => {
      written.push(...items);
    });
    vi.stubGlobal('ClipboardItem', class {
      constructor(public parts: Record<string, Blob>) {}
    });
    vi.stubGlobal('navigator', { clipboard: { write } });

    // jsdom 里图片既不加载也不报错，``loadImage`` 会一直等到 6 秒超时。
    // 把 ``complete`` 桩成 true，图片这一步立刻过去。
    const complete = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'complete');
    Object.defineProperty(HTMLImageElement.prototype, 'complete', {
      get: () => true,
      configurable: true,
    });
    // html2canvas 在 jsdom 里画不出东西，用桩替掉整条渲染链。
    const original = (window as unknown as { html2canvas?: unknown }).html2canvas;
    (window as unknown as { html2canvas?: unknown }).html2canvas = async () => ({
      toBlob: (callback: (blob: Blob | null) => void) =>
        callback(new Blob(['png'], { type: 'image/png' })),
    });

    try {
      const copied = await copyStrategyCard(loadGuide('roxy') as never, '洛克茜-攻略.png');
      expect(copied).toBe(true);
      expect(write).toHaveBeenCalledTimes(1);
      // 写进剪贴板的是一个 ClipboardItem，图在它的 image/png 部件里。
      const item = written[0] as unknown as { parts: Record<string, Blob> };
      expect(item.parts['image/png']).toBeInstanceOf(Blob);
      expect(item.parts['image/png'].type).toBe('image/png');
    } finally {
      (window as unknown as { html2canvas?: unknown }).html2canvas = original;
      if (complete) {
        Object.defineProperty(HTMLImageElement.prototype, 'complete', complete);
      }
      vi.unstubAllGlobals();
    }
  });
});
