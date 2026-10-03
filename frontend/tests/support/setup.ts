import { config } from '@vue/test-utils';

import { RouterLinkStub } from './router';

/**
 * 全局测试装置。
 *
 * 单元测试不安装真实 router，`RouterLink` 拿不到注入的实例会报
 * “Failed to resolve component”。这里用 VTU 的全局 `config` 挂一个
 * 只渲染 `to` 的 `<a>` 桩，各 spec 无需各自声明 `stubs`。
 */
config.global.stubs = { ...config.global.stubs, RouterLink: RouterLinkStub };

/*
 * ====== 浏览器 API 桩 ======
 *
 * jsdom 不实现下面这些 API，而 naive-ui 的浮层（cascader / select / popover）
 * 在挂载时就会读取它们：`n-cascader` 用 `matchMedia` 判断折叠断点、用
 * `ResizeObserver` 观察触发框尺寸、用 `getBoundingClientRect` 算浮层位置。
 * 缺任何一个都会在**挂载阶段**抛错，报错信息与业务无关，极易被误判成
 * 组件写错。故必须在引入 naive-ui 之前补齐。
 *
 * 桩只求「不抛错且返回合理的默认值」——布局计算在 jsdom 里本就不真实，
 * 组件测试断言的是结构与状态流转，不是像素位置。
 */

if (!window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

// 用宽松视图改写全局对象：`'ResizeObserver' in window` 会让 TS 把 window
// 收窄成 `never`（DOM lib 里没有这两个声明），导致赋值处直接报错。
const globals = globalThis as Record<string, unknown>;

if (typeof globals.ResizeObserver !== 'function') {
  globals.ResizeObserver = class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  };
}

if (typeof globals.IntersectionObserver !== 'function') {
  globals.IntersectionObserver = class IntersectionObserverStub {
    readonly root = null;
    readonly rootMargin = '';
    readonly thresholds: readonly number[] = [];
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
    takeRecords(): [] {
      return [];
    }
  };
}

/**
 * ⚠️ `getBoundingClientRect` 刻意**不**打桩。
 *
 * jsdom 已实现它（`jsdom/lib/jsdom/living/generated/Element.js`）且恒返回全 0。
 * naive-ui 的 `n-cascader` 默认 `virtualScroll`，会拿这个 0 高度决定渲染多少
 * 选项 —— 结果是浮层确实打开，但选项一项都不渲染（实测 `menuModel[0].length`
 * 为 7 而 `.n-cascader-option` 计数为 0）。
 *
 * 因此测试**不得断言浮层内的选项 DOM**：「7 个一级项」在 store 层断言，
 * DOM 层只验证浮层已打开。若将来必须断言选项 DOM，才需要在这里返回
 * 非零 `width` / `height`。
 */