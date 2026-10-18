import { onBeforeUnmount, onMounted, ref } from 'vue';

import type { Ref } from 'vue';

/**
 * 页面内锚点滚动侦测：返回当前处在可见带内的区块 id。
 *
 * 逻辑移植自攻略页渲染器（`strategy/renderStrategy.ts`）的 `bindScrollSpy`，并修掉它
 * 在指南页暴露出的两个问题：
 *
 * 1. **观察对象取「区域」而非锚点元素本身**。攻略页的目录指向整个板块容器
 *    （`.section`，高数百像素），观察它时命中带内几乎一直有目标在。
 *    指南页的锚点落在 `<h2>` 上，标题只有几十像素高，长章节（动辄上千像素）
 *    走到中段时**谁都不在命中带**，高亮会整块消失、滚动时反复闪现。
 *    故锚点元素若在带 `data-spy-region` 的包裹元素内，就观察那个包裹元素；
 *    没有包裹时才退回锚点自身（单元测试里就是这样）。
 *
 * 2. **空窗保留上一个高亮**。即使有了区域容器，两个区域之间仍有几十像素的
 *    缝；命中为空时沿用上一次的 activeId，而不是清空。
 *
 * 命中优先级与触底兜底同攻略页：深层目标（被另一目标包含，如模块小节之于
 * 所属章节）优先；页面滚到最底时高亮 DOM 顺序最后一个目标。
 *
 * jsdom（测试环境）里 `IntersectionObserver` 由 tests/support/setup.ts 打桩，
 * observe 为空操作，因此侦测不会报错，只是 activeId 恒为空字符串——
 * 组件测试断言的是结构与初始态，不依赖滚动高亮。
 */
export function useScrollSpy(collectIds: () => string[]): Ref<string> {
  const activeId = ref('');

  /** 可见带：视口顶部 15% 至 70% 之间算「正在阅读」。 */
  const ROOT_MARGIN = '-15% 0px -70% 0px';

  /** 一个侦测目标：id 是目录链接的锚点名，el 是真正被观察的元素。 */
  interface SpyTarget {
    id: string;
    el: HTMLElement;
  }

  let observer: IntersectionObserver | null = null;
  let ticking = false;

  /** 按目录锚点名解析观察对象，保持目录里的出现顺序、去重。 */
  function resolve(): SpyTarget[] {
    const targets: SpyTarget[] = [];
    for (const id of collectIds()) {
      const el = document.getElementById(id);
      if (!el) {
        continue;
      }
      if (targets.some((item) => item.id === id)) {
        continue;
      }
      const region = (el.closest('[data-spy-region]') as HTMLElement | null) ?? el;
      targets.push({ id, el: region });
    }
    return targets;
  }

  /** 深层目标优先：被别的目标包含时排在前面。 */
  function deepFirst(nodes: SpyTarget[]): string[] {
    return nodes
      .slice()
      .sort((a, b) => (b.el.contains(a.el) ? -1 : a.el.contains(b.el) ? 1 : 0))
      .map((node) => node.id);
  }

  /** 观察对象 → 锚点 id：IntersectionObserver 回调只给元素，查表才知道是谁。 */
  const idByElement = new WeakMap<Element, string>();

  function onScroll(): void {
    if (ticking) {
      return;
    }
    ticking = true;
    requestAnimationFrame(() => {
      ticking = false;
      paint();
    });
  }

  const visible = new Set<string>();

  function paint(): void {
    const nodes = resolve();
    if (nodes.length === 0) {
      return;
    }
    const order = deepFirst(nodes);
    const lastId = nodes[nodes.length - 1].id;
    const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
    const hit = order.find((id) => visible.has(id));
    // 触底兜底最后一个目标；空窗（两个区域之间的缝）沿用上一个高亮而不是清空
    activeId.value = atBottom ? lastId : (hit ?? activeId.value);
  }

  onMounted(() => {
    const nodes = resolve();
    if (nodes.length === 0 || !('IntersectionObserver' in window)) {
      return;
    }
    nodes.forEach((node) => idByElement.set(node.el, node.id));
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = idByElement.get(entry.target);
          if (!id) {
            continue;
          }
          if (entry.isIntersecting) {
            visible.add(id);
          } else {
            visible.delete(id);
          }
        }
        paint();
      },
      { rootMargin: ROOT_MARGIN, threshold: 0 },
    );
    nodes.forEach((node) => observer?.observe(node.el));
    window.addEventListener('scroll', onScroll, { passive: true });
  });

  onBeforeUnmount(() => {
    observer?.disconnect();
    observer = null;
    window.removeEventListener('scroll', onScroll);
    visible.clear();
  });

  return activeId;
}
