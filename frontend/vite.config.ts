import { readdir, readFile, stat } from 'node:fs/promises';
import { extname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath, URL } from 'node:url';
// 从 vitest/config 而非 vite 导入 defineConfig：只有它带 test 字段的类型定义，
// 否则下方 test 块会被 TypeScript 判为未知属性。
import { defineConfig } from 'vitest/config';
import type { Plugin } from 'vite';
import vue from '@vitejs/plugin-vue';

/**
 * 攻略静态页挂载点：strategy/<slug>/ 是每个代理人的攻略页目录（唯一真实源），
 * 统一挂到 /strategy/<slug>/ 下由前端 iframe 引用。页面与数据只有 strategy/
 * 一份，图片统一走 public/（JSON 里一律写 /images/… URL）。
 *
 * 开发期走中间件直读文件系统，构建期由 generateBundle 拷进 dist/，因此：
 * - 新增代理人攻略只需在 strategy/ 建目录，前端无需改代码；
 * - 攻略页不会在前端仓库里出现第二份副本；
 * - 构建产物（Cloudflare Assets 分发）同样带上攻略页。
 */
const STRATEGY_ROOT = resolve(fileURLToPath(new URL('../strategy', import.meta.url)));
const STRATEGY_PREFIX = '/strategy/';

/** 攻略页可能出现的静态资源类型（扩展名 -> Content-Type）。 */
const STRATEGY_MIME: Record<string, string> = {
  '.css': 'text/css; charset=utf-8',
  '.gif': 'image/gif',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ttf': 'font/ttf',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

/**
 * 只把前端运行时拷进 dist：页面与数据只有 strategy/ 一份，图片统一走 public/。
 * .py 脚本与 .md 文档留在仓库里即可，不进产物。
 */
const STRATEGY_ASSET_EXTENSIONS = new Set(['.css', '.html', '.js', '.json']);

/** 目录名即 URL 片段，限制为小写字母/数字/连字符，避免穿越与大小写歧义。 */
const STRATEGY_SLUG_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

/** 攻略页内的相对路径片段：字母 / 数字 / 点 / 连字符 / 下划线（反斜杠与 .. 均不匹配）。 */
const FILE_SEGMENT_PATTERN = /^[A-Za-z0-9._-]+$/;

interface StrategyPage {
  slug: string;
  root: string;
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

/** strategy/ 下每个含 index.html 的子目录即一个攻略页。 */
async function listStrategyPages(): Promise<StrategyPage[]> {
  const entries = await readdir(STRATEGY_ROOT, { withFileTypes: true });
  const pages: StrategyPage[] = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) {
      continue;
    }
    const root = join(STRATEGY_ROOT, entry.name);
    if (await isFile(join(root, 'index.html'))) {
      pages.push({ slug: entry.name, root });
    }
  }
  return pages;
}

/** 递归遍历目录下所有文件（不依赖 Node 新版 readdir 的 recursive 选项）。 */
async function* walkFiles(dir: string): AsyncGenerator<string> {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walkFiles(full);
    } else {
      yield full;
    }
  }
}

function strategyPagesPlugin(): Plugin {
  return {
    name: 'zzz-strategy-pages',
    // configureServer 里注册的中间件默认早于 Vite 内部中间件，
    // 因此 /strategy/ 请求先经这里，未命中再交回 SPA 历史回退。
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
        // 不带子路径的 /strategy/<slug> 交给 Vue 路由（iframe 舞台页）；
        // /strategy/<slug>/ 由下方 relPath 兜底成 index.html。
        const rest = pathname.slice(STRATEGY_PREFIX.length);
        const slash = rest.indexOf('/');
        if (slash <= 0) {
          next();
          return;
        }
        const slug = rest.slice(0, slash);
        if (!STRATEGY_SLUG_PATTERN.test(slug)) {
          next();
          return;
        }
        // /strategy/<slug>/ 与 /strategy/<slug> 都解析到 index.html
        //（前者 relPath 为空串，后者没有斜杠，见上面的 slash 判断）。
        const relPath = rest.slice(slash + 1) || 'index.html';
        // 路径片段只允许常见文件名字符，并显式排除 . / ..（点号本身在字符类里，
        // 不排除就会放行 ../../ 穿越）。同时挡住 Windows 反斜杠写法。
        // 攻略页文件名不含其他字符，正常请求不会命中这条 404。
        const segments = relPath.split('/');
        if (
          segments.some(
            (segment) =>
              segment === '.' ||
              segment === '..' ||
              !FILE_SEGMENT_PATTERN.test(segment),
          )
        ) {
          res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
          res.end('Not Found');
          return;
        }
        // resolve 已归一化 .. 等片段，再用边界检查兜底目录穿越。
        const file = resolve(STRATEGY_ROOT, slug, relPath);
        if (!file.startsWith(STRATEGY_ROOT + sep)) {
          next();
          return;
        }
        const target = (await isDirectory(file)) ? join(file, 'index.html') : file;
        if (!(await isFile(target))) {
          next();
          return;
        }
        const source = await readFile(target);
        res.setHeader('Content-Type', STRATEGY_MIME[extname(target).toLowerCase()] ?? 'application/octet-stream');
        res.setHeader('Cache-Control', 'no-store');
        res.end(req.method === 'HEAD' ? undefined : source);
      });
    },
    // 仅构建期执行：把各攻略页的运行时拷进 dist/strategy/<slug>/。
    async generateBundle() {
      for (const page of await listStrategyPages()) {
        for await (const absolute of walkFiles(page.root)) {
          if (!STRATEGY_ASSET_EXTENSIONS.has(extname(absolute).toLowerCase())) {
            continue;
          }
          const rel = relative(page.root, absolute).split(sep).join('/');
          this.emitFile({
            type: 'asset',
            fileName: `${STRATEGY_PREFIX.slice(1)}${page.slug}/${rel}`,
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
  plugins: [vue(), strategyPagesPlugin()],

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