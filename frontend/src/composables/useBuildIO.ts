import {
  BUILD_SCHEMA_VERSION,
  fromCompact,
  isUsableBuild,
  toCompact,
  type BuildPreset,
  type CompactBuild,
} from '@/types/build';

/**
 * 配装方案的导入 / 导出 / 分享链接。
 *
 * 三条路都**不落服务端**：
 *
 * - **导出**：下载一个 `.json` 文件，发给队友；
 * - **导入**：读队友发来的 `.json`；
 * - **分享链接**：把方案编码进 URL 片段（`#build=…`），对方打开就是这套配装。
 *
 * URL 片段是**本地编码**的内容（紧凑 JSON + URI 编码），不含任何服务端引用。
 */

/** URL 片段的参数名。 */
export const BUILD_HASH_KEY = 'build';

/** 当前页面的完整地址（分享链接的基底）。 */
function currentBase(): string {
  if (typeof window === 'undefined') return '';
  const { origin, pathname } = window.location;
  return `${origin}${pathname}`;
}

/** 方案 -> 分享链接。 */
export function buildShareUrl(preset: BuildPreset, base = currentBase()): string {
  const encoded = encodeURIComponent(JSON.stringify(toCompact(preset)));
  return `${base}#${BUILD_HASH_KEY}=${encoded}`;
}

/**
 * 从当前 URL 片段里读出一套方案。
 *
 * 片段格式不对时返回 null（**不抛错**）——访客点开一条失效的链接应该看到
 * 正常的页面，而不是一个报错页。
 */
export function readBuildFromHash(hash = typeof window === 'undefined' ? '' : window.location.hash): BuildPreset | null {
  if (!hash) return null;
  const match = hash.match(/[#&]build=([^&]+)/);
  if (!match) return null;
  try {
    const compact = JSON.parse(decodeURIComponent(match[1])) as CompactBuild;
    return fromCompact(compact);
  } catch {
    return null;
  }
}

/** 把分享链接里的方案写进地址栏（不刷新页面）。 */
export function writeBuildToHash(preset: BuildPreset): void {
  if (typeof window === 'undefined') return;
  const encoded = encodeURIComponent(JSON.stringify(toCompact(preset)));
  window.history.replaceState(
    null,
    '',
    `${window.location.pathname}${window.location.search}#${BUILD_HASH_KEY}=${encoded}`,
  );
}

/** 导出：下载一个 `.json` 文件。 */
export function exportBuildToFile(preset: BuildPreset): void {
  if (typeof document === 'undefined') return;
  const payload = {
    schemaVersion: BUILD_SCHEMA_VERSION,
    exportedAt: new Date().toISOString(),
    build: preset,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: 'application/json;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${preset.name || '配装方案'}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/**
 * 读文件内容。
 *
 * ``File.text()`` 在现代浏览器都有，但旧 Safari 与部分 jsdom 版本没有——
 * 退回 ``FileReader``，免得导入功能在那些环境里直接不可用。
 */
async function readFileText(file: File): Promise<string> {
  if (typeof file.text === 'function') {
    return file.text();
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ''));
    reader.onerror = () => reject(new Error('文件读取失败'));
    reader.readAsText(file, 'utf-8');
  });
}

/**
 * 导入：读一个 `.json` 文件。
 *
 * 接受两种内容——导出的完整文件，或直接就是一份方案。非法内容抛错，
 * 由调用方转成提示文案。
 */
export async function importBuildFromFile(file: File): Promise<BuildPreset> {
  const text = await readFileText(file);
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error('这个文件不是合法的 JSON');
  }
  if (parsed && typeof parsed === 'object' && 'build' in parsed) {
    const inner = (parsed as { build: unknown }).build;
    if (!isUsableBuild(inner)) {
      throw new Error('文件里的配装方案格式不对');
    }
    return inner;
  }
  if (!isUsableBuild(parsed)) {
    throw new Error('文件里的配装方案格式不对');
  }
  return parsed;
}
