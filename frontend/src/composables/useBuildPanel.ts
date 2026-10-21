import { useAgentPreset } from '@/composables/useAgentPreset';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
import type { BuildPreset } from '@/types/build';

/**
 * 配装方案与计算器面板之间的搬运。
 *
 * **基础面板不进方案。** 它是代理人的事实数据（来自代理人预设），
 * 存进方案只会多一份可能过期的副本。载入方案时重新载入代理人预设，
 * 基础面板自然跟着代理人对。
 */

/** 当前面板 -> 一套配装方案。 */
export function currentBuild(name: string): BuildPreset {
  const panel = usePanelStore();
  return {
    schemaVersion: 1,
    name,
    agentId: panel.agent.presetId,
    weaponId: panel.weapon.preset,
    core: { ...panel.core },
    discMain: { ...panel.discMain },
    subStats: { ...panel.subStats },
    sets: { ...panel.setEffects },
    setDiscs: { ...panel.setDiscs },
    mode: panel.panelMode,
    savedAt: new Date().toISOString(),
  };
}

/**
 * 套用一套配装方案。
 *
 * 顺序有讲究：先载入代理人预设（它会重置基础面板、核心、音擎与二件套），
 * 再把方案里记录的配装盖回去。
 */
export function applyBuild(preset: BuildPreset): { ok: boolean; message: string } {
  const panel = usePanelStore();
  const presets = usePresetStore();
  const { applyAgentPreset } = useAgentPreset();
  const { localize } = usePanelMode();

  if (preset.agentId) {
    const agent = presets.agentById.get(preset.agentId);
    if (!agent) {
      return { ok: false, message: `找不到代理人“${preset.agentId}”的预设数据。` };
    }
    // applyAgentPreset 要求角色标签与代理人对得上，标签按预设补上。
    panel.agent.roleTag = agent.roleTag;
    const note = applyAgentPreset(agent.id);
    if (note.tone === 'error') {
      return { ok: false, message: note.text };
    }
  }

  panel.core = { ...preset.core };
  panel.discMain = { ...preset.discMain };
  panel.subStats = { ...preset.subStats };
  panel.setEffects = { ...preset.sets };
  panel.setDiscs = { ...preset.setDiscs };
  if (preset.mode) {
    panel.panelMode = preset.mode;
  }

  if (preset.weaponId) {
    const weapon = presets.weaponById.get(preset.weaponId);
    if (!weapon) {
      return { ok: false, message: `找不到音擎“${preset.weaponId}”的预设数据。` };
    }
    panel.selectWeaponPreset(weapon.id, localize);
  }

  return { ok: true, message: `已载入方案“${preset.name}”。` };
}
