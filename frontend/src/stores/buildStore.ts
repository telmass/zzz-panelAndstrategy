import { defineStore } from 'pinia';

import { BUILD_SCHEMA_VERSION, type BuildLibrary, type BuildPreset } from '@/types/build';

/**
 * 本机保存的配装方案。
 *
 * **只存 localStorage**——方案是「某个用户自己的一套配装」，不是游戏事实，
 * 不该进仓库的 `data/`。导出 / 导入 / URL 分享走文件与链接，不落服务端
 * （站点公开、无鉴权，没有可写的服务端数据面）。
 */

/** localStorage 的键。带版本号，将来换形状时换键而不是迁移数据。 */
export const BUILD_STORAGE_KEY = 'zzz.builds.v1';

function readLibrary(): BuildLibrary {
  if (typeof localStorage === 'undefined') {
    return { schemaVersion: BUILD_SCHEMA_VERSION, builds: [] };
  }
  try {
    const raw = localStorage.getItem(BUILD_STORAGE_KEY);
    if (!raw) {
      return { schemaVersion: BUILD_SCHEMA_VERSION, builds: [] };
    }
    const parsed = JSON.parse(raw) as BuildLibrary;
    if (parsed?.schemaVersion !== BUILD_SCHEMA_VERSION || !Array.isArray(parsed.builds)) {
      return { schemaVersion: BUILD_SCHEMA_VERSION, builds: [] };
    }
    return parsed;
  } catch {
    // 存坏了就当没有——别让一个坏存档挡住整个计算器。
    return { schemaVersion: BUILD_SCHEMA_VERSION, builds: [] };
  }
}

function writeLibrary(library: BuildLibrary): void {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.setItem(BUILD_STORAGE_KEY, JSON.stringify(library));
  } catch {
    // 配额满 / 隐私模式禁写：方案存不下不该让计算器崩。
  }
}

export const useBuildStore = defineStore('builds', {
  state: () => ({
    /** 已保存的方案，最新的在前。 */
    builds: [] as BuildPreset[],
  }),

  getters: {
    /** 方案名列表（给下拉用）。 */
    buildNames(state): string[] {
      return state.builds.map((build) => build.name);
    },
  },

  actions: {
    /** 从 localStorage 载入方案列表。应用启动时调一次。 */
    load(): void {
      this.builds = readLibrary().builds;
    },

    /** 保存（或覆盖同名）一套方案。返回它在列表里的下标。 */
    save(preset: BuildPreset): number {
      const next = { ...preset, savedAt: preset.savedAt || new Date().toISOString() };
      const existing = this.builds.findIndex(
        (build) => build.name === next.name && build.agentId === next.agentId,
      );
      if (existing >= 0) {
        this.builds.splice(existing, 1, next);
      } else {
        this.builds.unshift(next);
      }
      writeLibrary({ schemaVersion: BUILD_SCHEMA_VERSION, builds: this.builds });
      return existing >= 0 ? existing : 0;
    },

    /** 删掉一个方案。 */
    remove(name: string, agentId: string): void {
      this.builds = this.builds.filter(
        (build) => !(build.name === name && build.agentId === agentId),
      );
      writeLibrary({ schemaVersion: BUILD_SCHEMA_VERSION, builds: this.builds });
    },

    /** 清空全部方案。 */
    clear(): void {
      this.builds = [];
      writeLibrary({ schemaVersion: BUILD_SCHEMA_VERSION, builds: this.builds });
    },
  },
});
