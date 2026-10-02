import { defineStore } from 'pinia';

/**
 * 面板输入与计算结果的唯一真源。
 * 第 0 步仅建立骨架；字段在第 1 步按 legacy 的 DOM id 逐一补齐。
 */
export const usePanelStore = defineStore('panel', {
  state: () => ({}),
  getters: {},
  actions: {},
});