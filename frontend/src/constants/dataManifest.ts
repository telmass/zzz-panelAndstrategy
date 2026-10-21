import manifest from '@data/manifest.json';

/**
 * 数据集登记表（`data/manifest.json`）在前端的视图。
 *
 * 前端的**数据文件本身**仍用字面量 `import` 读（Vite 的静态导入要求路径可静态
 * 分析，不能在运行时按 manifest 拼路径）。本模块只提供登记信息本身，供：
 *
 * - `tests/data-manifest.spec.ts` 断言「静态导入的文件 = manifest 登记的文件」，
 *   路径改名漏改时测试会指名道姓地失败；
 * - 调试与文档：想知道某个数据集的角色 / 维护方式时读这里，不必翻 JSON。
 *
 * 权威副本在仓库根 `data/manifest.json`，由 `tools/sync_manifest.py` 校验。
 */
export const DATA_MANIFEST = manifest;

/** 数据集 id -> 相对 `data/` 的路径。 */
export const DATASET_PATHS = Object.fromEntries(
  Object.entries(manifest.datasets).map(([id, entry]) => [id, entry.path]),
) as Record<string, string>;
