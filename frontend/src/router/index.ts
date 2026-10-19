import { createRouter, createWebHistory } from 'vue-router';

import LauncherView from '@/views/LauncherView.vue';
import { strategyGuides } from '@/constants/strategyGuides';

// 路由级懒加载：启动页保持 eager（首屏），其余按需加载。
// GuideView（684 行）与 StrategyView（含 1260 行 renderStrategy）
// 是两个最大的 chunk，不必在首页就拉取。
const CalculatorView = () => import('@/views/CalculatorView.vue');
const GuideView = () => import('@/views/GuideView.vue');
const StrategyPickerView = () => import('@/views/StrategyPickerView.vue');
const StrategyView = () => import('@/views/StrategyView.vue');

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'launcher', component: LauncherView },
    { path: '/calculator', name: 'calculator', component: CalculatorView },
    { path: '/guide', name: 'guide', component: GuideView },
    { path: '/strategy', name: 'strategy-picker', component: StrategyPickerView },
    {
      path: '/strategy/:slug',
      name: 'strategy',
      component: StrategyView,
      // 必须显式开启：否则 Vue Router 不把 params 作为 props 传入组件，
      // StrategyView 的 slug 会是 undefined，数据请求会指向 /strategy/undefined/。
      props: true,
      // 攻略数据目录（strategy/<slug>/）与登记表（constants/strategyGuides）由生成器同步；
      // 未登记的 slug 直接回启动页，避免请求不存在的数据。
      beforeEnter: (to) => {
        const slug = to.params.slug;
        if (!strategyGuides.some((guide) => guide.slug === slug)) {
          return { name: 'launcher' };
        }
        return true;
      },
    },
    // 兜底路由：未知路径回启动页，不渲染空白页。
    // 必须放在最后；Vue Router 按 routes 数组顺序匹配。
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: '/',
    },
  ],
});

export default router;