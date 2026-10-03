/**
 * 预设数据 API 客户端。
 *
 * 与 `api/panel.ts` 共用 `VITE_API_BASE_URL`（默认 `/api`），
 * `frontend/src/api/` 是前端访问后端的唯一出口。
 *
 * 契约见 `backend/src/zzz_panel/schemas/presets.py`；数据本体来自仓库根
 * `data/*.json`，由后端 `presets/loader.py` 校验后下发。前端不再持有副本。
 */

import type { AgentPreset } from '@/types/agentPresets';
import type { WeaponPreset } from '@/types/weaponPresets';
import { PresetApiError } from './errors';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api';

async function getItems<T>(path: string, signal?: AbortSignal): Promise<T[]> {
  const response = await fetch(`${BASE_URL}${path}`, { signal });

  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = (await response.json()) as { detail?: unknown };
    } catch {
      detail = null;
    }
    const message =
      detail && typeof detail === 'object' && 'detail' in detail && typeof detail.detail === 'string'
        ? detail.detail
        : `HTTP ${response.status}`;
    throw new PresetApiError(message, response.status);
  }

  const body = (await response.json()) as { items: T[] };
  return body.items;
}

/** 全部代理人预设。 */
export function fetchAgentPresets(signal?: AbortSignal): Promise<AgentPreset[]> {
  return getItems<AgentPreset>('/presets/agents', signal);
}

/** 全部音擎预设。 */
export function fetchWeaponPresets(signal?: AbortSignal): Promise<WeaponPreset[]> {
  return getItems<WeaponPreset>('/presets/weapons', signal);
}