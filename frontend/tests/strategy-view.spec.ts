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
  const wrapper = mount(StrategyView, { props: { slug }, attachTo: document.body });
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
    expect(document.activeElement).toBe(wrapper.get('.hero__name').element);
  });

  it('提供 skip link、main landmark，并把返回按钮放进文档流', async () => {
    const wrapper = await mountStrategy('ye-shunguang');

    expect(wrapper.get('.skip-link').attributes('href')).toBe('#strategy-main');
    expect(wrapper.get('main#strategy-main').attributes('tabindex')).toBe('-1');
    expect(wrapper.get('#guide').attributes('aria-labelledby')).toBe('guide-title');
    expect(wrapper.get('.sidebar').attributes('aria-label')).toBe('攻略目录');
    expect(wrapper.find('.strategy-detail > .back-link').exists()).toBe(true);
    expect(wrapper.find('main footer').exists()).toBe(false);
    expect(wrapper.find('.content > footer').exists()).toBe(true);
  });

  it('技能 tab 有完整 ARIA 状态，并支持方向键切换', async () => {
    const wrapper = await mountStrategy('ye-shunguang');
    const tabbed = wrapper
      .findAll('.skill-cat--tabbed')
      .find((cat) => cat.findAll('.move-tab').length > 1);
    expect(tabbed).toBeTruthy();
    const tabs = tabbed!.findAll('.move-tab');

    expect(tabs[0].attributes('role')).toBe('tab');
    expect(tabs[0].attributes('aria-selected')).toBe('true');
    expect(tabs[0].attributes('tabindex')).toBe('0');
    expect(tabs[1].attributes('aria-selected')).toBe('false');
    expect(tabs[1].attributes('tabindex')).toBe('-1');
    expect(tabs[0].attributes('aria-controls')).toMatch(/-panel-0$/);

    await tabs[1].trigger('click');
    expect(tabs[1].attributes('aria-selected')).toBe('true');
    expect(tabs[0].attributes('aria-selected')).toBe('false');

    const firstTab = tabs[0].element as HTMLElement;
    firstTab.focus();
    await tabs[0].trigger('keydown', { key: 'ArrowRight' });
    expect(tabs[1].attributes('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(tabs[1].element);
  });

  it('加载态用 status 角色播报', () => {
    const wrapper = mount(StrategyView, { props: { slug: 'ye-shunguang' } });
    const loading = wrapper.get('.boot');
    expect(loading.attributes('role')).toBe('status');
    expect(loading.attributes('aria-live')).toBe('polite');
  });

  it('数据文件缺失进入错误态并给出路径提示', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ ok: false, status: 404, json: async () => ({}) }) as Response),
    );

    const wrapper = await mountStrategy('ye-shunguang');
    const error = wrapper.get('.boot--error');
    expect(error.attributes('role')).toBe('alert');
    expect(error.text()).toContain('strategy/ye-shunguang/data/ye-shunguang.json');
  });

  it('strategy JSON 的 background 字段渲染为右侧背景层', async () => {
    const wrapper = await mountStrategy('roxy');
    expect(wrapper.find('.page-bg').exists()).toBe(true);
    expect(wrapper.get('.strategy-detail .app').attributes('style')).toContain(
      '/images/strategy/roxy/background.png',
    );
    expect(wrapper.get('.sidebar__brand-name').text()).toBe('洛克茜');
    expect(wrapper.get('.hero__name').text()).toContain('洛克茜·');
  });

  it('音擎卡使用左侧列表 + 右侧说明的两列结构', async () => {
    const wrapper = await mountStrategy('ye-shunguang');
    const card = wrapper.get('#guide-weapons .weapon-card');
    expect(card.find('.weapon-card__head').exists()).toBe(true);
    expect(card.get('.weapon-card__count').text()).toMatch(/把/);
    expect(card.find('.weapon-card__row').exists()).toBe(true);
    expect(card.find('.weapon-card__note').exists()).toBe(true);
    expect(card.get('.weapon-card__note').element.parentElement).toBe(card.element);
  });

  it('驱动盘分为上中下三段：4/2 件套、主词条、副词条', async () => {
    const wrapper = await mountStrategy('ye-shunguang');
    const drives = wrapper.get('#guide-drives');
    expect(drives.find('.drive-spec__sets').exists()).toBe(true);
    expect(drives.find('.drive-spec__set4').exists()).toBe(true);
    expect(drives.find('.drive-spec__set2').exists()).toBe(true);
    expect(drives.find('.drive-spec__mains').exists()).toBe(true);
    expect(drives.find('.drive-spec__subs').exists()).toBe(true);
    expect(drives.find('.drive-set-row').exists()).toBe(true);
    expect(drives.find('.drive-set-row__slot').exists()).toBe(false);

    const table = drives.get('.drive-main');
    const headers = table.findAll('thead th');
    expect(headers).toHaveLength(4);
    expect(headers[3].text()).toBe('备注');
    const firstRow = table.findAll('tbody tr')[0];
    expect(firstRow.findAll('td, th')).toHaveLength(4);
    expect(firstRow.get('.drive-main__note').text()).toBe('—');
  });

  it('多驱动盘方案使用 tabs，并支持方向键切换', async () => {
    const multi = strategyGuides.find((guide) => {
      const dataDir = resolve(REPO_ROOT, 'strategy', guide.slug, 'data');
      const strategy = JSON.parse(
        readFileSync(resolve(dataDir, `${guide.slug}.strategy.json`), 'utf-8'),
      );
      return Array.isArray(strategy.driveBuilds) && strategy.driveBuilds.length > 1;
    });
    expect(multi).toBeTruthy();

    const wrapper = await mountStrategy(multi!.slug);
    const tabs = wrapper.findAll('.drive-tab');
    expect(tabs.length).toBeGreaterThan(1);
    expect(tabs[0].attributes('role')).toBe('tab');
    expect(tabs[0].attributes('aria-selected')).toBe('true');
    expect(tabs[0].attributes('aria-controls')).toBe('drive-panel-0');

    const panels = wrapper.findAll('.drive-panel');
    expect(panels[0].attributes('hidden')).toBeUndefined();
    expect(panels[1].attributes('hidden')).toBeDefined();

    await tabs[1].trigger('click');
    expect(tabs[1].attributes('aria-selected')).toBe('true');
    expect(panels[0].attributes('hidden')).toBeDefined();
    expect(panels[1].attributes('hidden')).toBeUndefined();

    const firstTab = tabs[0].element as HTMLElement;
    firstTab.focus();
    await tabs[0].trigger('keydown', { key: 'ArrowRight' });
    expect(tabs[1].attributes('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(tabs[1].element);
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
