import { fileURLToPath, URL } from 'node:url';
// 从 vitest/config 而非 vite 导入 defineConfig：只有它带 test 字段的类型定义，
// 否则下方 test 块会被 TypeScript 判为未知属性。
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';

// 前端工程配置。
// docs/architecture.md 的分层约束：
// - 组件内禁止直接 fetch，一律经 src/api/（第 3 步已创建 src/api/panel.ts）
// - legacy/ 是过渡期原生实现，不参与 npm run build
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    port: 5173,
    strictPort: true,
    // 开发期由 Vite 代理转发到 FastAPI，前端代码里统一用相对路径 /api，
    // 因此本地开发不需要处理 CORS。
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    // 生产部署时由 FastAPI 挂载本目录的静态产物，单进程同时提供 API 与页面。
    emptyOutDir: true,
  },

  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.ts', 'src/**/*.spec.ts'],
  },
});