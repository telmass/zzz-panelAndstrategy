import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createPinia, setActivePinia, type Pinia } from 'pinia';

import StrategyView from '@/views/StrategyView.vue';
import { strategyGuides } from '@/constants/strategyGuides';
import { renderStrategy } from '@/strategy/renderStrategy';
import { loadPresets, mockApi } from './support/api';

const REPO_ROOT = resolve(__dirname, '../..');

/**
 * 攻略详情页改为 Vue 内共享渲染器后，至少锁住：
 * - 数据从 `/strategy/<slug>/data/` 拉取并渲染出完整区块；
 * - 不再出现 iframe；
 * - 数据缺失时显示错误态而不是白屏。
 *
 * 攻略页的基础面板**从代理人预设派生**（不再由攻略 JSON 自带），因此本页
 * 依赖 ``presetStore``——测试须像生产一样先装载预设。
 */
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

  it('毕业面板把 54 条词条拆成 47+7 展示', async () => {
    const wrapper = await mountStrategy('roxy');
    const graduation = wrapper.get('#guide-graduation');

    expect(graduation.text()).toContain('47+7 词条');
    expect(graduation.text()).toContain('+7 小词条');
    expect(graduation.text()).toContain('暴击率 ×24');
    expect(graduation.text()).not.toContain('攻击力 ×5');
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
      '/images/strategy/roxy/background.webp',
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

/**
 * 驱动盘不一定只有「4+2」。
 *
 * 6 个槽位也可以是 **2+2+2**（三组 2 件套）——比如 4 件套的效果对某角色没有
 * 增益，或需要三套不同属性的 2 件套。现有 61 个攻略页都是 4+2，但契约要能
 * 表达 2+2+2，否则下一个遇到这种配装的代理人只能把信息塞进备注里。
 *
 * 契约（`strategy/README.md`）分两条轴，**不能混**：
 *
 * - **组**（并列，都要装）：`set2` / `set2b` / `set2c`——第 1/2/3 组 2 件套；
 * - **候选**（二选一）：组内的 `main` / `alt`，各自还可以是「多套同效果的候选」。
 *
 * 另外 `set4` 是 4 件套的**候选**列表（三选一），不是「同时生效多个」——
 * 一个代理人最多生效一个 4 件套，4+4 也装不下（8 片 > 6 槽）。
 */
describe('驱动盘的 2+2+2 结构', () => {
  /** 用一份真实攻略数据当底，只替换 driveBuilds——渲染器要读 profile 等字段。 */
  function renderBuild(build: Record<string, unknown>, graduation?: Record<string, unknown>) {
    const host = document.createElement('div');
    document.body.append(host);
    const dataDir = resolve(REPO_ROOT, 'strategy', 'ye-shunguang', 'data');
    const scraped = JSON.parse(readFileSync(resolve(dataDir, 'ye-shunguang.json'), 'utf-8'));
    scraped.strategy = JSON.parse(
      readFileSync(resolve(dataDir, 'ye-shunguang.strategy.json'), 'utf-8'),
    );
    scraped.strategy.driveBuilds = [build];
    if (graduation) {
      scraped.strategy.graduationPanel = {
        ...scraped.strategy.graduationPanel,
        ...graduation,
      };
      // 非满配面板也带一份 build 块；这里一并换掉，否则它仍写着 4 件套。
      scraped.strategy.graduationPanelAlt = {
        ...scraped.strategy.graduationPanelAlt,
        ...graduation,
      };
    }

    const cleanup = renderStrategy({
      root: host,
      guide: scraped,
      slug: 'ye-shunguang',
    });
    return { host, cleanup };
  }

  const group1 = { main: { name: '混沌重金属', label: '以太伤害 +10%', icon: '/images/discs/a.webp' } };
  const group2 = { main: { name: '流光咏叹', label: '以太伤害 +10%', icon: '/images/discs/b.webp' } };
  const group3 = { main: { name: '拂晓行纪', label: '以太伤害 +10%', icon: '/images/discs/c.webp' } };

  it('2+2+2：没有 4 件套栏，三组 2 件套各占一栏', () => {
    const { host, cleanup } = renderBuild({
      name: '属性伤害三件套',
      set4: null,
      set2: group1,
      set2b: group2,
      set2c: group3,
      mainStats: [],
      subPriority: [],
    });

    expect(host.querySelector('.drive-spec__set4')).toBeNull();
    const groups = host.querySelectorAll('.drive-spec__set2');
    expect(groups.length).toBe(3);
    expect(groups[0].textContent).toContain('2 件套 ①');
    expect(groups[1].textContent).toContain('2 件套 ②');
    expect(groups[2].textContent).toContain('2 件套 ③');
    expect(host.textContent).toContain('混沌重金属');
    expect(host.textContent).toContain('拂晓行纪');

    cleanup();
    host.remove();
  });

  it('2+2+2：方案名缺省时按三组套装自动生成', () => {
    const { host, cleanup } = renderBuild({
      set4: null,
      set2: group1,
      set2b: group2,
      set2c: group3,
      mainStats: [],
      subPriority: [],
    });

    const title = host.querySelector('.drive-group__title');
    expect(title?.textContent).toContain('混沌重金属');
    expect(title?.textContent).toContain('2 件套');
    expect(title?.textContent).not.toContain('4 件套');

    cleanup();
    host.remove();
  });

  it('单组 2 件套（对象写法）仍按现状渲染，标题不带编号', () => {
    const { host, cleanup } = renderBuild({
      name: '沧浪行歌 4 件套 + 折枝剑歌 2 件套',
      set4: { name: '沧浪行歌', label: '物理伤害 +10%', effect4: '…', icon: '/images/discs/d.webp' },
      set2: { main: { name: '折枝剑歌', label: '暴击伤害 +16%', icon: '/images/discs/e.webp' } },
      mainStats: [],
      subPriority: [],
    });

    expect(host.querySelector('.drive-spec__set4')).not.toBeNull();
    const groups = host.querySelectorAll('.drive-spec__set2');
    expect(groups.length).toBe(1);
    expect(groups[0].textContent).toContain('2 件套');
    expect(groups[0].textContent).not.toContain('①');

    cleanup();
    host.remove();
  });

  it('毕业面板的套装名支持多组（2+2+2 时 set2 是数组）', () => {
    const { host, cleanup } = renderBuild(
      {
        name: '属性伤害三件套',
        set4: null,
        set2: group1,
        set2b: group2,
        set2c: group3,
        mainStats: [],
        subPriority: [],
      },
      {
        build: {
          agent: '叶瞬光',
          weapon: '云霓孤光',
          core: '暴击率 +14.4%、基础攻击力 +75',
          set4: null,
          set2: ['混沌重金属', '流光咏叹', '拂晓行纪'],
          mainStats: '4 号位暴击伤害 +48%',
          subStats: '54 条满配：暴击率 ×13、暴击伤害 ×16、攻击力% ×16、攻击力 ×5、穿透值 ×4',
        },
      },
    );

    const rows = Array.from(host.querySelectorAll('#guide-graduation .build-row'));
    const set2Row = rows.find((row) => row.textContent?.includes('2 件套'));
    expect(set2Row?.textContent).toContain('混沌重金属');
    expect(set2Row?.textContent).toContain('流光咏叹');
    expect(set2Row?.textContent).toContain('拂晓行纪');
    // 没有 4 件套组时不应出现「4 件套」这一行（set4 为 null 也不渲染空行）
    expect(rows.some((row) => row.textContent?.includes('4 件套'))).toBe(false);

    cleanup();
    host.remove();
  });

  it('真实数据：洛克茜的第三种配装是 2+2+2，渲染出三组且无 4 件套栏', () => {
    // 洛克茜（roxy）实测有第三种配装「2 月光 + 2 摇摆 + 2 啄木鸟」——
    // 没有 4 件套组，三组 2 件套，其中两组效果相同（能量自动回复 +20%）。
    // 这是契约的真实用例，不该只靠 mock 守着。
    const host = document.createElement('div');
    document.body.append(host);
    const dataDir = resolve(REPO_ROOT, 'strategy', 'roxy', 'data');
    const scraped = JSON.parse(readFileSync(resolve(dataDir, 'roxy.json'), 'utf-8'));
    scraped.strategy = JSON.parse(readFileSync(resolve(dataDir, 'roxy.strategy.json'), 'utf-8'));

    const cleanup = renderStrategy({ root: host, guide: scraped, slug: 'roxy' });

    // 三个方案 tab
    const tabs = host.querySelectorAll('.drive-tab');
    expect(tabs.length).toBe(3);
    expect(tabs[2].textContent).toContain('2 月光');

    // 点开第三种。
    // 注意：所有面板都留在 DOM 里（只有激活的那个可见），所以断言必须**限定在
    // 激活面板内**——否则会数到另外两个方案的面板。
    tabs[2].dispatchEvent(new MouseEvent('click', { bubbles: true }));
    const active = host.querySelector('.drive-panel.is-active') as HTMLElement;
    expect(active).not.toBeNull();
    expect(active.id).toBe('drive-panel-2');

    const groups = active.querySelectorAll('.drive-spec__set2');
    expect(groups.length).toBe(3);
    expect(groups[0].textContent).toContain('2 件套 ①');
    expect(groups[1].textContent).toContain('2 件套 ②');
    expect(groups[2].textContent).toContain('2 件套 ③');
    // 没有 4 件套组
    expect(active.querySelector('.drive-spec__set4')).toBeNull();
    // 三组各是一套
    expect(active.textContent).toContain('月光骑士颂');
    expect(active.textContent).toContain('摇摆爵士');
    expect(active.textContent).toContain('啄木鸟电音');

    cleanup();
    host.remove();
  });
});
