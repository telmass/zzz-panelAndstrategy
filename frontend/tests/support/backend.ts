import { execFileSync, spawn, type ChildProcessByStdio } from 'node:child_process';
import { resolve } from 'node:path';
import { vi } from 'vitest';
import type { Readable } from 'node:stream';

/**
 * 在 vitest 中拉起真实 FastAPI 后端。
 *
 * `legacy-parity.spec.ts` 要做的是三方对拍：legacy 原生 JS ≡ Vue 页面 ≡ Python 后端。
 * 只有真的把后端跑起来，这条链路才被验证；用 mock 的话 Vue 侧就成了自证。
 */

const REPO_ROOT = resolve(__dirname, '../..');
const HOST = '127.0.0.1';
/** 用 0 端口让系统分配空闲端口，避免与开发中的 8000 冲突。 */
const STARTUP_TIMEOUT_MS = 20_000;
const PROBE_INTERVAL_MS = 200;
/** 健康检查最长等待。启动超时后仍留一点余量，避免误杀慢机器。 */
const HEALTH_TIMEOUT_MS = 15_000;

let child: ChildProcessByStdio<null, Readable, Readable> | null = null;
let baseUrl = '';

/**
 * 从 uvicorn 的日志行里取实际绑定端口。
 *
 * 两个容易踩的点：
 * 1. uvicorn 的日志走 **stderr**，stdout 是空的；
 * 2. `--log-level warning` 会把 `Uvicorn running on ...` 这行 INFO 抑制掉，
 *    因此必须用 info 级别才能拿到端口。
 */
function portFrom(chunk: string): number | null {
  const match = chunk.match(/Uvicorn running on https?:\/\/[^:]+:(\d+)/);
  return match ? Number(match[1]) : null;
}

async function waitForHealth(url: string): Promise<boolean> {
  try {
    const response = await fetch(`${url}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export interface BackendHandle {
  baseUrl: string;
  stop: () => Promise<void>;
}

/** 启动后端并等待健康检查通过。失败时抛出带 stderr 的错误，由调用方 skip。 */
export async function startBackend(): Promise<BackendHandle> {
  if (child) {
    return { baseUrl, stop: stopBackend };
  }

  // 注意 log-level 必须是 info：warning 会抑制掉报端口的那行。
  child = spawn(
    'uv',
    ['run', 'uvicorn', 'zzz_panel.api.app:app', '--host', HOST, '--port', '0', '--log-level', 'info'],
    { cwd: REPO_ROOT, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, PYTHONIOENCODING: 'utf-8' } },
  );

  let output = '';
  const capture = (chunk: Buffer) => {
    output += chunk.toString();
  };
  // uvicorn 的日志全部走 stderr；stdout 保留监听只为保险。
  child.stderr.on('data', capture);
  child.stdout.on('data', capture);

  const port = await new Promise<number | null>((resolvePort) => {
    const timer = setTimeout(() => resolvePort(null), STARTUP_TIMEOUT_MS);
    const onData = (chunk: Buffer) => {
      const found = portFrom(chunk.toString());
      if (found !== null) {
        clearTimeout(timer);
        child!.stderr.off('data', onData);
        child!.stdout.off('data', onData);
        resolvePort(found);
      }
    };
    child!.stderr.on('data', onData);
    child!.stdout.on('data', onData);
    child!.on('exit', () => {
      clearTimeout(timer);
      resolvePort(null);
    });
  });

  if (port === null) {
    const failed = child;
    child = null;
    failed.kill();
    killOrphanUvicorn();
    throw new Error(
      `后端启动失败（${STARTUP_TIMEOUT_MS / 1000}s 内未报出端口）。uvicorn 输出：\n${output.trim() || '（无输出）'}`,
    );
  }

  baseUrl = `http://${HOST}:${port}`;

  const deadline = Date.now() + HEALTH_TIMEOUT_MS;
  while (Date.now() < deadline) {
    if (await waitForHealth(baseUrl)) {
      return { baseUrl, stop: stopBackend };
    }
    await new Promise((r) => setTimeout(r, PROBE_INTERVAL_MS));
  }

  await stopBackend();
  throw new Error(`后端健康检查超时（${HEALTH_TIMEOUT_MS / 1000}s）。uvicorn 输出：\n${output.trim() || '（无输出）'}`);
}

export async function stopBackend(): Promise<void> {
  if (!child) {
    return;
  }
  const current = child;
  child = null;
  baseUrl = '';

  // Windows 上 `uv run uvicorn` 是两层进程：杀掉 uv 不会连带杀掉 python
  // 孙子进程，孤儿会继续持有端口与句柄，导致 vitest 事件循环永不退出
  //（表现为「测试跑完了但命令不返回」）。
  await new Promise<void>((done) => {
    const finish = setTimeout(done, 3000);
    current.once('exit', () => {
      clearTimeout(finish);
      done();
    });
    current.kill();
  });

  killOrphanUvicorn();
}

/**
 * 清理本项目遗留的 uvicorn 进程。
 *
 * 不走「按父 pid 找子孙」的思路：`uv run` 的父子关系在 Windows 上不稳定，
 * 且 `wmic` 已废弃。直接按命令行匹配本项目的 uvicorn，简单且实测可靠。
 * 只匹配 `python.exe` + `zzz_panel` + `uvicorn`，不会误杀其它进程。
 */
function killOrphanUvicorn(): void {
  try {
    execFileSync(
      'powershell',
      [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" " +
          '| Where-Object { $_.CommandLine -like "*zzz_panel*" -and $_.CommandLine -like "*uvicorn*" } ' +
          '| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }',
      ],
      { stdio: 'ignore', timeout: 15_000 },
    );
  } catch {
    /* 无残留或权限不足；不影响测试结论 */
  }
}

/**
 * 让 `api/panel.ts` 发出的 `/api/...` 请求真正打到测试后端。
 *
 * 不改 `VITE_API_BASE_URL`：`import.meta.env` 在 Vite 构建时就被内联，
 * 运行时改 `process.env` 无效。这里用 fetch stub 重写 URL，
 * Node 18+ 自带 fetch，因此生产代码无需为测试做任何让步。
 */
export function routeFetchToBackend(backendUrl: string): void {
  // 必须在 stub 之前抓住原始 fetch：stub 之后再引用全局 fetch 会指回 stub 自身，
  // 造成二次拼接出 `http://host:PORThttp://host:PORT/...` 的非法 URL。
  const realFetch = globalThis.fetch?.bind(globalThis);
  if (!realFetch) {
    throw new Error('当前运行环境没有 fetch，无法做三方对拍');
  }

  vi.stubGlobal('fetch', (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.toString();
    return realFetch(`${backendUrl}${url}`, init);
  });
}
