/**
 * UI 验收截图：用 CDP 驱动本机 Chrome 拍图。
 *
 *     node frontend/tools/screenshot.mjs --out <目录> [--base http://127.0.0.1:5173]
 *                                         [--only <子串>] [--width <n>]
 *
 * 为什么不用 `chrome --headless --screenshot`
 * ------------------------------------------
 * Chrome 在 Windows 上把 `--window-size` 的**宽度钳到最小 500px**
 * （实测请求 375 → 实际视口 500，请求 560 → 实际 544，1280 → 1264）。
 * 截出来的图按请求宽度**裁切**，但页面是按 500px 渲染的——图在骗人：
 * 看上去是「窄屏没折叠」，其实是根本没截到窄屏。
 *
 * CDP 的 `Emulation.setDeviceMetricsOverride` 能设**任意**宽度，
 * `Page.captureScreenshot` 还能整页截（`captureBeyondViewport`）。
 *
 * **不新增任何依赖**：Node 22 自带全局 `WebSocket`，直接说 DevTools 协议即可。
 *
 * 产物用途见 `docs/design/ui-review-checklist.md`：B 档与 C 档要人看图，
 * 本脚本负责把图拍出来，且每次都是同一批节点、同一批视口——不同评审员看的
 * 是可比的东西。
 */

import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

/** 候选浏览器。优先 Chrome——评审时用哪个浏览器，截图就用哪个。 */
const BROWSER_CANDIDATES = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
];

/** 视口宽度。清单 §2 规定的四档。 */
const WIDTHS = [1280, 960, 560, 375];

/** 视口高度固定 800：只关心宽度带来的布局变化。 */
const HEIGHT = 800;

/** 页面加载后额外等待的毫秒数。Vue 挂载 + 拉预设 + 首次计算都要时间。 */
const SETTLE_MS = 1500;

/**
 * 截图节点。`name` 即文件名的一部分。
 *
 * `state` 只是命名上的约定——真正决定页面状态的是 URL。
 * 计算器目前**不读** query 参数（见下方 TODO），因此 S1/S2/S3 三个状态
 * 需要先在应用里支持 `?agent=<slug>` 才能自动复现。
 */
const NODES = [
  { name: 'launcher', url: '/', widths: WIDTHS },
  { name: 'calculator-empty', url: '/calculator', widths: WIDTHS },
  { name: 'calculator-agent', url: '/calculator?agent=ye-shunguang', widths: WIDTHS },
  { name: 'calculator-rupture', url: '/calculator?agent=yixuan', widths: [1280, 560, 375] },
  { name: 'calculator-armorer', url: '/calculator?agent=claret', widths: [1280, 560, 375] },
  { name: 'guide', url: '/guide', widths: WIDTHS },
  { name: 'strategy-picker', url: '/strategy', widths: WIDTHS },
  { name: 'strategy-detail', url: '/strategy/ye-shunguang', widths: WIDTHS },
];

function parseArgs(argv) {
  const options = {
    out: null,
    base: null,
    only: null,
    width: null,
    viewportOnly: false,
    scroll: null,
    click: null,
    url: null,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === '--out') {
      options.out = value;
      index += 1;
    } else if (flag === '--base') {
      options.base = value;
      index += 1;
    } else if (flag === '--only') {
      options.only = value;
      index += 1;
    } else if (flag === '--width') {
      options.width = Number(value);
      index += 1;
    } else if (flag === '--viewport-only') {
      options.viewportOnly = true;
    } else if (flag === '--scroll') {
      options.scroll = value;
      index += 1;
    } else if (flag === '--click') {
      options.click = value;
      index += 1;
    } else if (flag === '--url') {
      options.url = value;
      index += 1;
    }
  }
  return options;
}

function findBrowser() {
  for (const candidate of BROWSER_CANDIDATES) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  throw new Error('找不到 Chrome / Edge');
}

/** 端口是否有人监听。 */
function probePort(port) {
  return new Promise((done) => {
    const socket = connect(`127.0.0.1:${port}`);
    socket.on('connect', () => {
      socket.destroy();
      done(true);
    });
    socket.on('error', () => done(false));
  });
}

import { connect } from 'node:net';

async function findFrontend(ports) {
  for (const port of ports) {
    if (await probePort(port)) {
      return port;
    }
  }
  return null;
}

/** 极简 CDP 客户端：一条 WebSocket，按 id 配对响应。 */
class Cdp {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) {
          reject(new Error(`${message.error.message}（${message.error.code}）`));
        } else {
          resolve(message.result);
        }
        return;
      }
      if (message.method) {
        const handlers = this.listeners.get(message.method);
        if (handlers) {
          for (const handler of handlers) {
            handler(message.params, message.sessionId);
          }
        }
      }
    });
  }

  send(method, params = {}, sessionId) {
    const id = this.nextId;
    this.nextId += 1;
    const payload = { id, method, params };
    if (sessionId) {
      payload.sessionId = sessionId;
    }
    return new Promise((res, rej) => {
      this.pending.set(id, { resolve: res, reject: rej });
      this.socket.send(JSON.stringify(payload));
    });
  }

  on(method, handler) {
    if (!this.listeners.has(method)) {
      this.listeners.set(method, []);
    }
    this.listeners.get(method).push(handler);
  }
}

/** 启动 Chrome 并等它吐出 DevTools WebSocket 地址。 */
async function launchBrowser(browserPath) {
  const userDataDir = join(tmpdir(), `ui-shot-${Date.now()}`);
  const child = spawn(
    browserPath,
    [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-extensions',
      '--force-device-scale-factor=1',
      '--remote-debugging-port=0',
      `--user-data-dir=${userDataDir}`,
      'about:blank',
    ],
    { stdio: ['ignore', 'pipe', 'pipe'] },
  );

  const endpoint = await new Promise((done, fail) => {
    let buffer = '';
    const timer = setTimeout(() => fail(new Error('等待 DevTools 端点超时')), 30000);
    child.stderr.on('data', (chunk) => {
      buffer += chunk.toString();
      const match = buffer.match(/DevTools listening on (ws:\/\/\S+)/);
      if (match) {
        clearTimeout(timer);
        done(match[1]);
      }
    });
    child.on('exit', (code) => {
      clearTimeout(timer);
      fail(new Error(`Chrome 提前退出（${code}）`));
    });
  });

  return { child, endpoint, userDataDir };
}

function sleep(ms) {
  return new Promise((done) => setTimeout(done, ms));
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (!options.out) {
    throw new Error('需要 --out <目录>');
  }
  const outDir = resolve(options.out);
  await mkdir(outDir, { recursive: true });

  let base = options.base;
  if (!base) {
    const port = await findFrontend([5173, 5174, 5175]);
    if (!port) {
      throw new Error('找不到前端 dev server，先跑 `pwsh tools/dev.ps1`，或用 --base 指定');
    }
    base = `http://127.0.0.1:${port}`;
  }

  const browserPath = findBrowser();
  console.log(`浏览器：${browserPath}`);
  console.log(`地址：${base}`);

  const { child, endpoint, userDataDir } = await launchBrowser(browserPath);
  const socket = new WebSocket(endpoint);
  await new Promise((done, fail) => {
    socket.addEventListener('open', done, { once: true });
    socket.addEventListener('error', fail, { once: true });
  });
  const cdp = new Cdp(socket);

  let taken = 0;
  const failed = [];
  try {
    const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await cdp.send('Target.attachToTarget', {
      targetId,
      flatten: true,
    });

    await cdp.send('Page.enable', {}, sessionId);

    for (const node of options.url
      ? [{ name: 'custom', url: options.url, widths: options.width ? [options.width] : WIDTHS }]
      : NODES) {
      if (options.only && !node.name.includes(options.only)) {
        continue;
      }
      const widths = options.width ? [options.width] : node.widths;
      for (const width of widths) {
        await cdp.send(
          'Emulation.setDeviceMetricsOverride',
          {
            width,
            height: HEIGHT,
            deviceScaleFactor: 1,
            mobile: false,
          },
          sessionId,
        );
        const loaded = new Promise((done) => {
          const handler = (_params, session) => {
            if (session === sessionId) {
              done();
            }
          };
          cdp.on('Page.loadEventFired', handler);
        });
        await cdp.send('Page.navigate', { url: base + node.url }, sessionId);
        await Promise.race([loaded, sleep(15000)]);
        // 留出挂载、接口与首次计算的时间。
        await sleep(SETTLE_MS);

        // 逐段滚到底再回顶：攻略页的区块靠 IntersectionObserver 淡入
        // （``.reveal`` → ``.reveal.is-visible``，480ms 过渡）。不滚一遍的话，
        // 视口外的区块在整页截图里是**全透明**的——图会骗人。
        await cdp.send(
          'Runtime.evaluate',
          {
            awaitPromise: true,
            expression: `(async () => {
              const step = window.innerHeight;
              for (let y = 0; y < document.body.scrollHeight; y += step) {
                window.scrollTo(0, y);
                await new Promise((r) => setTimeout(r, 120));
              }
              window.scrollTo(0, 0);
              await new Promise((r) => setTimeout(r, 200));
              return true;
            })()`,
          },
          sessionId,
        );
        // 过渡动画留够时间。
        await sleep(700);

        if (options.scroll) {
          // 滚到指定元素：SPA 渲染完才有目标，故在 settle 之后执行。
          await cdp.send(
            'Runtime.evaluate',
            {
              expression: `(() => {
                const el = document.querySelector(${JSON.stringify(options.scroll)});
                if (el) el.scrollIntoView({ block: 'start' });
                return Boolean(el);
              })()`,
            },
            sessionId,
          );
          await sleep(700);
        }

        if (options.click) {
          // 点开一个浮层（cascader 下拉等）。清单 B12 要看浮层里的图标。
          await cdp.send(
            'Runtime.evaluate',
            {
              expression: `(() => {
                const el = document.querySelector(${JSON.stringify(options.click)});
                if (!el) return false;
                el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                el.click();
                return true;
              })()`,
            },
            sessionId,
          );
          await sleep(900);
        }

        const shot = await cdp.send(
          'Page.captureScreenshot',
          {
            format: 'png',
            captureBeyondViewport: !options.viewportOnly,
            fromSurface: true,
          },
          sessionId,
        );
        const suffix = options.viewportOnly ? '-vp' : '';
        const file = join(outDir, `${node.name}-${width}${suffix}.png`);
        await writeFile(file, Buffer.from(shot.data, 'base64'));
        console.log(`  ok       ${node.name}-${width}.png`);
        taken += 1;
      }
    }
  } finally {
    socket.close();
    child.kill();
  }

  console.log(`\n共 ${taken} 张，失败 ${failed.length} 张`);
  if (failed.length) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
