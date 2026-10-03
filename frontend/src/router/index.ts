import { createRouter, createWebHistory } from 'vue-router';

import CalculatorView from '@/views/CalculatorView.vue';
import ExampleView from '@/views/ExampleView.vue';
import GuideView from '@/views/GuideView.vue';
import LauncherView from '@/views/LauncherView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'launcher', component: LauncherView },
    { path: '/calculator', name: 'calculator', component: CalculatorView },
    { path: '/guide', name: 'guide', component: GuideView },
    // 标准版示例页，吸收自 legacy/pages/example-template.html
    { path: '/example', name: 'example', component: ExampleView },
  ],
});

export default router;