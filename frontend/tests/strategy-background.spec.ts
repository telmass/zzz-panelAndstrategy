import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia, type Pinia } from 'pinia';

import StrategyView from '@/views/StrategyView.vue';
import { strategyGuides } from '@/constants/strategyGuides';
import { loadPresets, mockApi } from './support/api';

const REPO_ROOT = resolve(__dirname, '../..');

enableAutoUnmount(afterEach);

let pinia: Pinia;

beforeEach(async () => {
  mockApi();
  pinia = createPinia();
  setActivePinia(pinia);
  await loadPresets();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function mountStrategy(slug: string) {
  const wrapper = mount(StrategyView, {
    props: { slug },
    attachTo: document.body,
    global: { plugins: [pinia] },
  });
  await flushPromises();
  await new Promise((resolve) => setTimeout(resolve, 0));
  await flushPromises();
  return wrapper;
}

/**
 * 立绘背景（`strategy/<slug>/data/<slug>.strategy.json` 顶层 `background` +
 * `frontend/public/images/strategy/<slug>/background.webp`）由
 * `tools/fetch_agent_backgrounds.py` 从 Gachabase 抓取补齐，共享渲染器据此
 * 输出 `.page-bg` 背景层。这里守住「登记表里每位代理人都有背景」这条不变量。
 */
describe('代理人立绘背景', () => {
  it('每位代理人的攻略数据都带 background 字段且背景图存在', () => {
    const slugs = strategyGuides.map((guide) => guide.slug);
    expect(slugs.length).toBeGreaterThan(0);

    for (const slug of slugs) {
      const data = JSON.parse(
        readFileSync(resolve(REPO_ROOT, 'strategy', slug, 'data', `${slug}.strategy.json`), 'utf-8'),
      ) as { background?: string };
      expect(data.background, `${slug} 缺少 background 字段`).toBe(
        `/images/strategy/${slug}/background.webp`,
      );

      const image = resolve(REPO_ROOT, 'frontend/public/images/strategy', slug, 'background.webp');
      expect(existsSync(image), `${slug} 缺少背景图`).toBe(true);
      expect(readFileSync(image).length, `${slug} 背景图为空`).toBeGreaterThan(0);
    }
  });

  it('每位代理人都有一张角色框头像 film.webp', () => {
    for (const guide of strategyGuides) {
      const image = resolve(REPO_ROOT, 'frontend/public/images/strategy', guide.slug, 'film.webp');
      expect(existsSync(image), `${guide.slug} 缺少角色框头像`).toBe(true);
      expect(readFileSync(image).length, `${guide.slug} 角色框头像为空`).toBeGreaterThan(0);
    }
  });

  it('攻略页渲染 .page-bg 背景层', async () => {
    const wrapper = await mountStrategy('miyabi');
    expect(wrapper.find('.page-bg').exists()).toBe(true);
  });
});
