<script setup lang="ts">
import { computed, ref } from 'vue';

import { useScrollSpy } from '@/composables/useScrollSpy';

/**
 * 侧边目录导航。版式复刻代理人攻略页（`strategy/<slug>/`）的 `.sidebar`：
 * 品牌块 + 编号一级链接 + 二级子链接，滚到哪里亮哪一格；窄屏折叠成
 * 顶部目录条，由「目录」开关展开。
 *
 * 只给长文页用（目前是 `/guide`）。计算器是「边填边看结果」的工具页，
 * 模块一屏内滚完，放目录只会白占一列宽度，故它不用本组件。
 *
 * 与攻略页的差异只有配色真源：攻略页按代理人属性色动态取色，这里固定用
 * `--color-accent` 一族的靛蓝，与正文的强调色同源。
 *
 * 链接一律写成原生 `<a href="#id">`：平滑滚动交给 CSS 的
 * `scroll-behavior: smooth` + `scroll-padding-top`，不需要 JS 拦截点击，
 * 禁用 JS 时目录依然可用。
 */

/** 一级导航项。`sub` 为该章节下的二级锚点。 */
export interface SideNavGroup {
  /** 章节锚点 id。 */
  id: string;
  /** 一级链接文案。 */
  label: string;
  /** 二级链接。 */
  sub?: { id: string; label: string }[];
}

const props = defineProps<{
  /** 导航分组。序号徽标按出现顺序从 01 起自动编号。 */
  groups: SideNavGroup[];
  /** 品牌块主文案（页名）。 */
  brandName: string;
  /** 品牌块副文案。 */
  brandSub: string;
}>();

/** 一级链接带上编号，与攻略页 `01`–`04` 的呈现一致。 */
const entries = computed(() =>
  props.groups.map((group, index) => ({
    ...group,
    index: String(index + 1).padStart(2, '0'),
  })),
);

const open = ref(false);
const activeId = useScrollSpy(() => {
  const ids = props.groups.map((group) => group.id);
  for (const group of props.groups) {
    ids.push(...(group.sub ?? []).map((item) => item.id));
  }
  return ids;
});

/** 一级链接高亮：自身命中，或其子链接命中（父级保持浅色高亮）。 */
function isActive(group: SideNavGroup): boolean {
  return group.id === activeId.value;
}

function isParent(group: SideNavGroup): boolean {
  return (group.sub ?? []).some((item) => item.id === activeId.value);
}

function toggle(): void {
  open.value = !open.value;
}
</script>

<template>
  <aside class="sidebar" :class="{ 'is-open': open }" id="page-sidebar">
    <div class="sidebar__brand">
      <span class="sidebar__brand-badge">ZZZ</span>
      <div class="sidebar__brand-text">
        <p class="sidebar__brand-name">{{ brandName }}</p>
        <p class="sidebar__brand-sub">{{ brandSub }}</p>
      </div>
      <button
        class="sidebar__toggle"
        type="button"
        :aria-expanded="open ? 'true' : 'false'"
        aria-controls="page-sidebar-nav"
        @click="toggle"
      >
        {{ open ? '收起' : '目录' }}
      </button>
    </div>

    <nav class="sidebar__nav" id="page-sidebar-nav" aria-label="页面导航">
      <div v-for="group in entries" :key="group.id" class="sidebar__group">
        <a
          class="sidebar__link"
          :class="{ 'is-active': isActive(group), 'is-parent': isParent(group) }"
          :href="`#${group.id}`"
        >
          <span class="sidebar__index">{{ group.index }}</span>
          <span class="sidebar__label">{{ group.label }}</span>
        </a>
        <div v-if="group.sub?.length" class="sidebar__sublinks">
          <a
            v-for="item in group.sub"
            :key="item.id"
            class="sidebar__sublink"
            :class="{ 'is-active': activeId === item.id }"
            :href="`#${item.id}`"
            >{{ item.label }}</a
          >
        </div>
      </div>
    </nav>

    <div class="sidebar__foot">
      <p>页面导航</p>
      <p class="sidebar__foot-source">点击条目跳转对应区块</p>
    </div>
  </aside>
</template>
