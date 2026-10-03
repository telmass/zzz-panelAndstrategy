import { defineStore } from 'pinia';

import { fetchAgentPresets, fetchWeaponPresets } from '@/api/presets';
import type { AgentPreset } from '@/types/agentPresets';
import type { WeaponPreset } from '@/types/weaponPresets';

/** 预设数据的加载状态。 */
export type PresetStatus = 'idle' | 'loading' | 'ready' | 'error';

/**
 * 代理人与音擎预设的唯一前端数据源。
 *
 * 第 4 步第 17 条起，预设数据的唯一真实源是仓库根 `data/*.json`，经后端
 * `presets/loader.py` 校验后由 `GET /api/presets/*` 下发。前端**不再持有副本**：
 * `src/data/agentPresets.ts` 与 `weaponPresets.ts` 已删除。
 *
 * 两个下拉列表要求瞬时可用，因此 `main.ts` 在 `mount` 之前 `await loadAll()`——
 * 组件渲染时 `status` 必为 `ready`，各处 getter 可以保持同步派生，
 * 不用在每个使用点处理「还没加载完」的空态。
 */
export const usePresetStore = defineStore('presets', {
  state: () => ({
    agents: [] as AgentPreset[],
    weapons: [] as WeaponPreset[],
    status: 'idle' as PresetStatus,
    /** 加载失败时的原因，用于向用户解释下拉为何为空。 */
    error: '',
  }),

  getters: {
    /** 按 id 索引的代理人预设，供载入时 O(1) 查找。 */
    agentById: (state) => {
      const index = new Map<string, AgentPreset>();
      for (const agent of state.agents) {
        index.set(agent.id, agent);
      }
      return index;
    },

    /** 按 id 索引的音擎预设。 */
    weaponById: (state) => {
      const index = new Map<string, WeaponPreset>();
      for (const weapon of state.weapons) {
        index.set(weapon.id, weapon);
      }
      return index;
    },

    /** 下拉可用。为 false 时界面应展示加载中或错误提示，而非空列表。 */
    ready: (state) => state.status === 'ready',
  },

  actions: {
    /**
     * 拉取全部预设。两个请求并发，任一失败即整体失败——
     * 只拿到一半预设会让代理人下拉有值、音擎下拉为空，比全空更难排查。
     */
    async loadAll(): Promise<void> {
      this.status = 'loading';
      this.error = '';
      try {
        const [agents, weapons] = await Promise.all([fetchAgentPresets(), fetchWeaponPresets()]);
        this.agents = agents;
        this.weapons = weapons;
        this.status = 'ready';
      } catch (cause) {
        this.agents = [];
        this.weapons = [];
        this.status = 'error';
        this.error = cause instanceof Error ? cause.message : '预设数据加载失败';
      }
    },
  },
});