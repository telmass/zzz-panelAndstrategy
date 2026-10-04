import { defineStore } from 'pinia';

import { fetchAgentPresets, fetchWeaponPresets } from '@/api/presets';
import type { AgentPreset } from '@/types/agentPresets';
import type { WeaponPreset } from '@/types/weaponPresets';

/**
 * 代理人与音擎预设的唯一前端数据源。
 *
 * 预设数据的唯一真实源是仓库根 `data/*.json`，经后端 `presets/loader.py`
 * 校验后由 `GET /api/presets/*` 下发。前端**不再持有副本**。
 *
 * 两个下拉列表要求瞬时可用，因此 `main.ts` 在 `mount` 之前 `await loadAll()`——
 * 组件渲染时数据必已就位，不需要在每个使用点处理「还没加载完」的空态，
 * 所以本 store 不再保留加载状态：要么数组已填好，要么为空并已报错到控制台。
 */
export const usePresetStore = defineStore('presets', {
  state: () => ({
    agents: [] as AgentPreset[],
    weapons: [] as WeaponPreset[],
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
  },

  actions: {
    /**
     * 拉取全部预设。两个请求并发，任一失败即整体失败——
     * 只拿到一半预设会让代理人下拉有值、音擎下拉为空，比全空更难排查。
     */
    async loadAll(): Promise<void> {
      try {
        const [agents, weapons] = await Promise.all([fetchAgentPresets(), fetchWeaponPresets()]);
        this.agents = agents;
        this.weapons = weapons;
      } catch (cause) {
        this.agents = [];
        this.weapons = [];
        const reason = cause instanceof Error ? cause.message : '预设数据加载失败';
        console.error(`[presets] 加载失败，两个下拉将为空：${reason}`);
      }
    },
  },
});