import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { enableAutoUnmount, mount } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';

import type { VueWrapper } from '@vue/test-utils';

import CalculatorView from '@/views/CalculatorView.vue';
import GuideView from '@/views/GuideView.vue';
import LauncherView from '@/views/LauncherView.vue';
import { useScrollSpy } from '@/composables/useScrollSpy';
import { usePanelStore } from '@/stores/panelStore';
import { loadPresets, mockApi } from './support/api';

/**
 * 攻略同款排版的回归护栏：侧边目录（仅指南页）、序号徽标、结果区操作按钮
 * 与启动页导航。计算与口径的正确性不在本文件范围内（见 legacy-parity.spec）。
 */

let pinia: Pinia;

beforeEach(async () => {
  pinia = createPinia();
  setActivePinia(pinia);
  mockApi();
  await loadPresets();
});

enableAutoUnmount(afterEach);

afterEach(() => {
  vi.unstubAllGlobals();
});

function mountCalculator(): VueWrapper {
  return mount(CalculatorView, { global: { plugins: [pinia] } });
}

describe('侧边目录（SideNav）', () => {
  it('计算器页不渲染侧边目录，只留页眉与结果列', () => {
    const wrapper = mountCalculator();
    expect(wrapper.find('.sidebar').exists()).toBe(false);
    // 布局回到 base.css 的两列：输入列 + 吸顶结果
    expect(wrapper.find('.layout').classes()).not.toContain('layout--calc');
    expect(wrapper.findAll('.layout > *')).toHaveLength(2);
  });

  it('指南页目录六章齐全，第二章带五个模块子链接', () => {
    const wrapper = mount(GuideView);
    expect(wrapper.findAll('.sidebar__link').map((node) => node.find('.sidebar__label').text())).toEqual([
      '整体结构概览',
      '六大模块详解',
      '攻防血通用计算',
      '双爆与其他属性',
      '驱动盘进阶知识',
      '规律与概念总结',
    ]);
    expect(wrapper.findAll('.sidebar__sublink').map((node) => node.text())).toEqual([
      '基础面板',
      '核心加成',
      '音擎加成',
      '驱动盘',
      '2件套效果',
    ]);
  });

  it('初始态没有任何高亮；jsdom 的观察器桩不会误亮', () => {
    const wrapper = mount(GuideView);
    expect(wrapper.findAll('.sidebar__link.is-active, .sidebar__sublink.is-active')).toHaveLength(0);
    // 目录默认收起由 CSS 类控制，桌面上没有 is-open
    expect(wrapper.find('.sidebar').classes()).not.toContain('is-open');
  });

  it('「目录」开关切换展开态并同步 aria-expanded', async () => {
    const wrapper = mount(GuideView);
    const toggle = wrapper.get('.sidebar__toggle');
    expect(toggle.attributes('aria-expanded')).toBe('false');

    await toggle.trigger('click');
    expect(wrapper.find('.sidebar').classes()).toContain('is-open');
    expect(toggle.text()).toBe('收起');

    await toggle.trigger('click');
    expect(wrapper.find('.sidebar').classes()).not.toContain('is-open');
    expect(toggle.text()).toBe('目录');
  });

  it('章节与模块小节都套了侦测区域', () => {
    const wrapper = mount(GuideView);
    // data-spy-region 是滚动侦测的观察对象：少一个，该章/该小节的高亮就会闪没。
    // 6 个 GuideSection + 「六大模块详解」下 5 个模块小节
    expect(wrapper.findAll('[data-spy-region]')).toHaveLength(11);
    expect(wrapper.findAll('.guide-section')).toHaveLength(6);
    expect(wrapper.findAll('.guide-module')).toHaveLength(5);
  });

  it('模块小节进入可见带时，二级链接与父级同时高亮', async () => {
    // 这是二级链接的整条链路回归：区域容器 → 锚点名 → is-active/is-parent。
    // 必须 attachTo document.body： VTU 默认挂到游离节点，document.getElementById
    // 取不到锚点，侦测根本不会启动（jsdom 无滚动，只能手动喂 entries）。
    let observerCallback: IntersectionObserverCallback | undefined;
    vi.stubGlobal(
      'IntersectionObserver',
      class SpyObserver {
        constructor(callback: IntersectionObserverCallback) {
          observerCallback = callback;
        }
        observe(): void {}
        unobserve(): void {}
        disconnect(): void {}
        takeRecords(): IntersectionObserverEntry[] {
          return [];
        }
      },
    );
    // jsdom 无布局：scrollHeight 恒 0 会让「触底」判断恒真、永远兜底到最后一项
    Object.defineProperty(document.documentElement, 'scrollHeight', {
      value: 5000,
      configurable: true,
    });
    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true, writable: true });

    const wrapper = mount(GuideView, { attachTo: document.body });
    const region = wrapper.get('#mod-drive').element.closest('[data-spy-region]');
    expect(region).not.toBeNull();

    observerCallback?.(
      [{ target: region, isIntersecting: true } as unknown as IntersectionObserverEntry],
      {} as IntersectionObserver,
    );
    await wrapper.vm.$nextTick();

    // 二级链接亮自己，父级亮「浅色高亮」，两者缺一不可
    expect(wrapper.get('a[href="#mod-drive"]').classes()).toContain('is-active');
    expect(wrapper.get('a[href="#modules"]').classes()).toContain('is-parent');
  });

  it('计算器与指南的页眉不放跳转按钮', () => {
    // 只删两页**顶部**的跳转按钮；指南结尾的 CTA 是学完即用的转化位，保留
    for (const wrapper of [mountCalculator(), mount(GuideView)]) {
      expect(wrapper.find('.page-hero__actions').exists()).toBe(false);
      // 页眉里一个链接都没有：返回按钮在页外固定层，锚点/CTA 都在正文里
      expect(wrapper.find('.page-hero').findAll('a')).toHaveLength(0);
    }
    // 计算器整页除左上角返回外无任何链接
    expect(mountCalculator().findAll('a').map((node) => node.attributes('href'))).toEqual(['/']);
    // 指南的其余链接只能是页内锚点 + 结尾一个指向计算器的 CTA
    const guideLinks = mount(GuideView)
      .findAll('a')
      .map((node) => node.attributes('href'));
    expect(guideLinks[0]).toBe('/');
    expect(guideLinks.slice(1).filter((href) => !href?.startsWith('#'))).toEqual(['/calculator']);
  });
});

describe('useScrollSpy', () => {
  /** 捕获构造时传入的回调，手动喂「可见性变化」。 */
  let observerCallback: IntersectionObserverCallback | undefined;

  beforeEach(() => {
    observerCallback = undefined;
    vi.stubGlobal(
      'IntersectionObserver',
      class SpyObserver {
        constructor(callback: IntersectionObserverCallback) {
          observerCallback = callback;
        }
        observe(): void {}
        unobserve(): void {}
        disconnect(): void {}
        takeRecords(): IntersectionObserverEntry[] {
          return [];
        }
      },
    );
    // jsdom 无布局：scrollHeight 恒 0 会让「触底」判断恒真，必须撑高页面
    Object.defineProperty(document.documentElement, 'scrollHeight', {
      value: 5000,
      configurable: true,
    });
    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true, writable: true });
  });

  it('区块进入可见带时高亮该区块；空窗时保留上一个高亮', async () => {
    const first = document.createElement('div');
    first.id = 'spy-first';
    const second = document.createElement('div');
    second.id = 'spy-second';
    document.body.append(first, second);

    const Host = defineComponent({
      setup() {
        const active = useScrollSpy(() => ['spy-first', 'spy-second']);
        return { active };
      },
      template: '<p class="spy">{{ active }}</p>',
    });

    const wrapper = mount(Host);
    expect(wrapper.find('.spy').text()).toBe('');

    observerCallback?.(
      [{ target: first, isIntersecting: true } as unknown as IntersectionObserverEntry],
      {} as IntersectionObserver,
    );
    await nextTick();
    expect(wrapper.find('.spy').text()).toBe('spy-first');

    // 离开可见带：两个都不在命中带时不算「回到页首」，沿用上一个高亮
    observerCallback?.(
      [{ target: first, isIntersecting: false } as unknown as IntersectionObserverEntry],
      {} as IntersectionObserver,
    );
    await nextTick();
    expect(wrapper.find('.spy').text()).toBe('spy-first');
  });

  it('锚点裹在侦测区域里时，观察对象是区域容器', async () => {
    // 指南页的真实结构：目录指向 <h2>，但观察的是整章 <section data-spy-region>
    const regionA = document.createElement('section');
    regionA.setAttribute('data-spy-region', '');
    const headA = document.createElement('h2');
    headA.id = 'spy-region-a';
    regionA.append(headA);
    const headB = document.createElement('h2');
    headB.id = 'spy-region-b';
    document.body.append(regionA, headB);

    const Host = defineComponent({
      setup() {
        const active = useScrollSpy(() => ['spy-region-a', 'spy-region-b']);
        return { active };
      },
      template: '<p class="spy">{{ active }}</p>',
    });

    const wrapper = mount(Host);

    // 回调报的是区域容器（不是 h2），也要能映射回目录锚点名
    observerCallback?.(
      [{ target: regionA, isIntersecting: true } as unknown as IntersectionObserverEntry],
      {} as IntersectionObserver,
    );
    await nextTick();
    expect(wrapper.find('.spy').text()).toBe('spy-region-a');
  });

  it('滚动触底时兜底高亮最后一个目标', async () => {
    const first = document.createElement('div');
    first.id = 'spy-tail-a';
    const second = document.createElement('div');
    second.id = 'spy-tail-b';
    document.body.append(first, second);

    const Host = defineComponent({
      setup() {
        const active = useScrollSpy(() => ['spy-tail-a', 'spy-tail-b']);
        return { active };
      },
      template: '<p class="spy">{{ active }}</p>',
    });

    const wrapper = mount(Host);
    window.scrollY = 5000;
    window.dispatchEvent(new Event('scroll'));
    // 滚动回调走 requestAnimationFrame，等一帧
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(observerCallback).toBeDefined();
    expect(wrapper.find('.spy').text()).toBe('spy-tail-b');
  });
});

describe('结果区操作按钮', () => {
  it('复制结果把可见行拼成文本写入剪贴板，并给出「已复制」反馈', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });

    const wrapper = mountCalculator();
    await wrapper.get('.result-action').trigger('click');
    // 等待 clipboard 的 Promise 链走完
    await nextTick();
    await nextTick();

    expect(writeText).toHaveBeenCalledTimes(1);
    const text = writeText.mock.calls[0][0] as string;
    expect(text).toContain('最终面板');
    expect(text).toContain('生命值：');
    expect(wrapper.find('.result-hint').text()).toBe('已复制');
  });

  it('重置一键还原全部输入', async () => {
    const wrapper = mountCalculator();
    const panel = usePanelStore();

    panel.base.hp = 12345;
    panel.core.core1 = 'atk_flat';
    panel.setEffects.set0 = 'atk_pct_10';
    panel.discMain.disc4 = 'atk_pct_30';
    await nextTick();

    await wrapper.findAll('.result-action')[1].trigger('click');

    expect(panel.base.hp).toBe(8000);
    expect(panel.core.core1).toBe('');
    expect(panel.setEffects.set0).toBe('');
    expect(panel.discMain.disc4).toBe('');
    expect(panel.agent.presetId).toBe('');
  });
});

describe('启动页顶部导航与卡片', () => {
  function mountLauncher(): VueWrapper {
    return mount(LauncherView);
  }

  it('顶部站点导航覆盖四个板块', () => {
    const links = mountLauncher().findAll('.site-nav__link');
    expect(links.map((node) => node.text())).toEqual(['首页', '计算器', '指南', '攻略']);
    expect(links.map((node) => node.attributes('href'))).toEqual(['/', '/calculator', '/guide', '/strategy']);
  });

  it('页眉信息片与卡片序号、特性列表齐备', () => {
    const wrapper = mountLauncher();
    expect(wrapper.findAll('.hero-chip')).toHaveLength(4);
    expect(wrapper.findAll('.card__no').map((node) => node.text())).toEqual(['01', '02', '03']);
    // 每张卡三条特性；第三张卡的「满配毕业面板」是攻略板块独有信息
    expect(wrapper.findAll('.card__features li').map((node) => node.text())).toContain('满配毕业面板');
    expect(wrapper.findAll('.card__features')).toHaveLength(3);
  });

  it('卡片徽标与页脚信息保持原文案', () => {
    const wrapper = mountLauncher();
    expect(wrapper.findAll('.badge').map((node) => node.text())).toEqual([
      '统一计算器',
      '学习指南',
      '代理人攻略',
    ]);
    expect(wrapper.find('.launcher-footer__meta').text()).toContain('网页与命令行结果必然一致');
  });
});

describe('指南章节序号与结尾 CTA', () => {
  it('六章各带 01–06 序号徽标', () => {
    const badges = mount(GuideView).findAll('.section__title .section__no');
    expect(badges.map((node) => node.text())).toEqual(['01', '02', '03', '04', '05', '06']);
  });

  it('结尾 CTA 指向计算器', () => {
    const cta = mount(GuideView).find('.guide-cta');
    expect(cta.find('.guide-cta__title').text()).toContain('亲手算一遍');
    expect(cta.find('a').attributes('href')).toBe('/calculator');
  });
});
