import { createRouter, createWebHistory } from 'vue-router';

import CalculatorView from '@/views/CalculatorView.vue';
import GuideView from '@/views/GuideView.vue';
import LauncherView from '@/views/LauncherView.vue';
import StrategyPickerView from '@/views/StrategyPickerView.vue';
import StrategyView from '@/views/StrategyView.vue';
import { strategyGuides } from '@/constants/strategyGuides';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
      // StrategyView 的 slug 会是 undefined，iframe 指向 /strategy/undefined/。
      props: true,
      // 攻略目录（strategy/<slug>/）与登记表（constants/strategyGuides）由维护者同步新增；
      // 未登记的 slug 直接回启动页，避免 iframe 加载到不存在的静态页。
      beforeEnter: (to) => {
        const slug = to.params.slug;
        if (!strategyGuides.some((guide) => guide.slug === slug)) {
          return { name: 'launcher' };
        }
        return true;
      },
    },
  ],
});

export default router;