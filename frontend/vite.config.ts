import { readdir, readFile, stat } from 'node:fs/promises';
import { join, resolve, sep } from 'node:path';
import { fileURLToPath, URL } from 'node:url';
// 从 vitest/config 而非 vite 导入 defineConfig：只有它带 test 字段的类型定义，
// 否则下方 test 块会被 TypeScript 判为未知属性。
import { defineConfig } from 'vitest/config';
import type { Plugin } from 'vite';
import vue from '@vitejs/plugin-vue';

/**
 * 攻略数据挂载点：`strategy/<slug>/data/` 是攻略页唯一真实源。
 *
 * 页面本身已迁入 Vue（`views/StrategyView.vue` + `strategy/renderStrategy.ts`），
 * 因此这里只负责两件事：
 * - 开发期把 `/strategy/<slug>/data/*.json` 映射到仓库 `strategy/` 目录；
 * - 构建期只把两份 JSON 拷进 `dist/strategy/<slug>/data/`。
 *
 * 不再复制 `index.html / app.js / styles.css`，也不再把整页静态资源打进产物。
 */
const STRATEGY_ROOT = resolve(fileURLToPath(new URL('../strategy', import.meta.url)));
const STRATEGY_PREFIX = '/strategy/';

/**
 * 数据集登记表。路径只在这里声明一次（`data/manifest.json`），
 * 本文件按 id 取用，不再自己记文件名。
 */
const DATA_DIR = fileURLToPath(new URL('../data', import.meta.url));
const MANIFEST_PATH = join(DATA_DIR, 'manifest.json');

interface ManifestEntry {
  path: string;
}

interface Manifest {
  datasets: Record<string, ManifestEntry>;
}

/** 目录名即 URL 片段，限制为小写字母/数字/连字符，避免穿越与大小写歧义。 */
const STRATEGY_SLUG_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

/** 只允许规范命名的两份数据文件，防止把脚本、Markdown 等带进产物。 */
const STRATEGY_DATA_PATTERN = /^([a-z0-9][a-z0-9-]*)\.(json|strategy\.json)$/;

interface StrategyDataDir {
  slug: string;
  dir: string;
}

async function isDirectory(path: string): Promise<boolean> {
  try {
    return (await stat(path)).isDirectory();
  } catch {
    return false;
  }
}

async function isFile(path: string): Promise<boolean> {
  try {
    return (await stat(path)).isFile();
  } catch {
    return false;
  }
}

/** 读取登记表并返回某个数据集的绝对路径。 */
async function datasetPath(id: string): Promise<string> {
  const manifest = JSON.parse(await readFile(MANIFEST_PATH, 'utf-8')) as Manifest;
  const entry = manifest.datasets[id];
  if (!entry) {
    throw new Error(`数据集 ${id} 未在 data/manifest.json 中登记`);
  }
  return join(DATA_DIR, entry.path);
}

/** strategy/ 下每个含 data/ 的子目录即一个攻略数据目录。 */
async function listStrategyDataDirs(): Promise<StrategyDataDir[]> {
  const entries = await readdir(STRATEGY_ROOT, { withFileTypes: true });
  // 只打包已发布的 slug（在 agent-presets 中有对应预设的），
  // 防止未发布/不完整的目录被意外带进 dist。
  const presetsText = await readFile(await datasetPath('agents'), 'utf-8');
  const presets: Array<{ id: string }> = JSON.parse(presetsText);
  const agentsText = await readFile(await datasetPath('agent-index'), 'utf-8');
  const mapping: Array<{ slug: string }> = JSON.parse(agentsText);
  const mappingSlugs = new Set(mapping.map((m) => m.slug));
  const dirs: StrategyDataDir[] = [];
  for (const entry of entries) {
    if (!entry.isDirectory() || !STRATEGY_SLUG_PATTERN.test(entry.name)) {
      continue;
    }
    if (!mappingSlugs.has(entry.name)) {
      continue; // 未在 mapping 中登记的目录不打包
    }
    const dir = join(STRATEGY_ROOT, entry.name);
    if (await isDirectory(join(dir, 'data'))) {
      dirs.push({ slug: entry.name, dir });
    }
  }
  return dirs;
}

function strategyDataPlugin(): Plugin {
  return {
    name: 'zzz-strategy-data',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (req.method !== 'GET' && req.method !== 'HEAD') {
          next();
          return;
        }
        const [pathname] = (req.url ?? '').split('?');
        if (!pathname?.startsWith(STRATEGY_PREFIX)) {
          next();
          return;
        }
        const rest = pathname.slice(STRATEGY_PREFIX.length);
        const match = /^([a-z0-9][a-z0-9-]*)\/data\/([a-z0-9][a-z0-9.-]*)$/.exec(rest);
        if (!match) {
          // /strategy/<slug> 交给 Vue Router；其他路径也交回 Vite。
          next();
          return;
        }
        const [, slug, file] = match;
        const dataMatch = STRATEGY_DATA_PATTERN.exec(file);
        if (!dataMatch || dataMatch[1] !== slug) {
          res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
          res.end('Not Found');
          return;
        }
        const target = resolve(STRATEGY_ROOT, slug, 'data', file);
        if (!target.startsWith(join(STRATEGY_ROOT, slug, 'data') + sep) || !(await isFile(target))) {
          next();
          return;
        }
        try {
          const source = await readFile(target);
          res.setHeader('Content-Type', 'application/json; charset=utf-8');
          res.setHeader('Cache-Control', 'no-store');
          res.end(req.method === 'HEAD' ? undefined : source);
        } catch {
          next();
        }
      });
    },
    async generateBundle() {
      for (const { slug, dir } of await listStrategyDataDirs()) {
        for (const name of [`${slug}.json`, `${slug}.strategy.json`]) {
          const absolute = join(dir, 'data', name);
          if (!(await isFile(absolute))) {
            continue;
          }
          this.emitFile({
            type: 'asset',
            fileName: `strategy/${slug}/data/${name}`,
            source: await readFile(absolute),
          });
        }
      }
    },
  };
}

// 前端工程配置。
// docs/architecture.md 的分层约束：
// - 组件内禁止直接 fetch，一律经 src/api/
// - tests/fixtures/legacy-calculator/ 是只读的参照实现，不参与 npm run build
export default defineConfig({
  plugins: [vue(), strategyDataPlugin()],

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
