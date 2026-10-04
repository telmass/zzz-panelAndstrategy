import { fileURLToPath, URL } from 'node:url';
// 从 vitest/config 而非 vite 导入 defineConfig：只有它带 test 字段的类型定义，
// 否则下方 test 块会被 TypeScript 判为未知属性。
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';

// 前端工程配置。
// docs/architecture.md 的分层约束：
// - 组件内禁止直接 fetch，一律经 src/api/
// - tests/fixtures/legacy-calculator/ 是只读的参照实现，不参与 npm run build
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // 仓库根 data/ 是预设与规则表的唯一真实源，由 tools/sync_presets.py 生成。
      // 前端直接读同一份文件而非复制一份，构建产物因此不含规则表副本。
      '@data': fileURLToPath(new URL('../data', import.meta.url)),
    },
  },

  server: {
    port: 5173,
    strictPort: true,
    // @data 指到 frontend/ 之外，默认的 fs.allow 不放行，需显式加上仓库根。
    fs: { allow: [fileURLToPath(new URL('..', import.meta.url))] },
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
    // 产物由 Cloudflare Workers 的 Assets 上传并直接分发（wrangler.jsonc 的
    // assets.directory），FastAPI 不挂载本目录，因此这里只管产出干净的 dist/。
    emptyOutDir: true,
  },

  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.ts'],
    setupFiles: ['./tests/support/setup.ts'],
  },
});