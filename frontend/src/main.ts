import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from '@/App.vue';
import router from '@/router';
import { usePresetStore } from '@/stores/presetStore';

import '@/assets/styles/index.css';

/**
 * 先拉预设再挂载。
 *
 * 代理人与音擎下拉依赖 `presetStore`，而两者的 getter 是同步派生的。
 * 在 `mount` 之前 `await` 一次加载，组件渲染时数据必已就位，
 * 避免每个使用点都处理「尚未加载」的空态。
 * 失败不阻断挂载：`presetStore.status` 会是 `error`，
 * 由界面展示原因，总比白屏好。
 *
 * 用 async 函数而非顶层 await：构建目标（es2020）不支持顶层 await。
 */
async function bootstrap(): Promise<void> {
  const app = createApp(App);
  const pinia = createPinia();
  app.use(pinia).use(router);

  await usePresetStore(pinia).loadAll();

  app.mount('#app');
}

void bootstrap();