import { createRouter, createWebHistory } from 'vue-router';

import CalculatorView from '@/views/CalculatorView.vue';
import GuideView from '@/views/GuideView.vue';
import LauncherView from '@/views/LauncherView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'launcher', component: LauncherView },
    { path: '/calculator', name: 'calculator', component: CalculatorView },
    { path: '/guide', name: 'guide', component: GuideView },
  ],
});

export default router;