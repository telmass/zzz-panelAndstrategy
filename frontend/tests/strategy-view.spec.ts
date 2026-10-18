import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import StrategyView from '@/views/StrategyView.vue';
import { strategyGuides } from '@/constants/strategyGuides';
import { renderStrategy } from '@/strategy/renderStrategy';
import { mockApi } from './support/api';

const REPO_ROOT = resolve(__dirname, '../..');

/**
 * 攻略详情页改为 Vue 内共享渲染器后，至少锁住：
 * - 数据从 `/strategy/<slug>/data/` 拉取并渲染出完整区块；
 * - 不再出现 iframe；
 * - 数据缺失时显示错误态而不是白屏。
 */
enableAutoUnmount(afterEach);

beforeEach(() => {
  mockApi();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function mountStrategy(slug: string) {
  const wrapper = mount(StrategyView, { props: { slug } });
  await flushPromises();
  await new Promise((resolve) => setTimeout(resolve, 0));
  await flushPromises();
  return wrapper;
}

describe('StrategyView', () => {
  it('用共享渲染器渲染叶瞬光攻略，且没有 iframe', async () => {
    const wrapper = await mountStrategy('ye-shunguang');

    expect(wrapper.find('iframe').exists()).toBe(false);
    expect(wrapper.find('.strategy-detail .hero').exists()).toBe(true);
    expect(wrapper.get('.hero__name').text()).toContain('叶瞬光');
    expect(wrapper.find('#guide').exists()).toBe(true);
    expect(wrapper.find('#base').exists()).toBe(true);
    expect(wrapper.find('#skills').exists()).toBe(true);
    expect(wrapper.find('#cinema').exists()).toBe(true);
    expect(wrapper.find('#guide-graduation').exists()).toBe(true);
    expect(wrapper.find('#guide-team').exists()).toBe(true);
    expect(wrapper.find('#guide-text').exists()).toBe(true);
    expect(wrapper.find('.sidebar').exists()).toBe(true);
    expect(wrapper.find('.to-top').exists()).toBe(true);
  });

  it('数据文件缺失进入错误态并给出路径提示', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ ok: false, status: 404, json: async () => ({}) }) as Response),
    );

    const wrapper = await mountStrategy('ye-shunguang');
    expect(wrapper.find('.boot--error').exists()).toBe(true);
    expect(wrapper.text()).toContain('strategy/ye-shunguang/data/ye-shunguang.json');
  });

  it('strategy JSON 的 background 字段渲染为右侧背景层', async () => {
    const wrapper = await mountStrategy('roxy');
    expect(wrapper.find('.page-bg').exists()).toBe(true);
    expect(wrapper.get('.strategy-detail .app').attributes('style')).toContain(
      '/images/strategy/roxy/background.png',
    );
  });

  it('登记表里每个代理人的数据都能被共享渲染器渲染', () => {
    for (const guide of strategyGuides) {
      const host = document.createElement('div');
      document.body.append(host);
      const dataDir = resolve(REPO_ROOT, 'strategy', guide.slug, 'data');
      const scraped = JSON.parse(readFileSync(resolve(dataDir, `${guide.slug}.json`), 'utf-8'));
      scraped.strategy = JSON.parse(
        readFileSync(resolve(dataDir, `${guide.slug}.strategy.json`), 'utf-8'),
      );

      const cleanup = renderStrategy({
        root: host,
        guide: scraped,
        slug: guide.slug,
      });

      expect(host.querySelector('.hero'), `${guide.slug} 缺 hero`).not.toBeNull();
      expect(host.querySelector('#guide'), `${guide.slug} 缺攻略区块`).not.toBeNull();
      expect(host.querySelector('.sidebar'), `${guide.slug} 缺侧边目录`).not.toBeNull();

      cleanup();
      host.remove();
    }
  });
});
