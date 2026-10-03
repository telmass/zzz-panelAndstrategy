/**
 * 面板计算 API 客户端。
 *
 * 这是前端访问后端的**唯一**网络出口。所有请求走 `VITE_API_BASE_URL`
 * （默认 `/api`，由 vite dev server 代理到 FastAPI）。
 *
 * 契约见 `backend/src/zzz_panel/schemas/panel.py`。请求只带**选择**
 * （下拉项 id、副词条条数）与角色基础面板，数值一律由后端解析——
 * 第 3 步之后前端不再持有任何计算口径。
 */

import type {
  PanelApiResponse,
  PanelCalcRequest,
} from '@/types/panel';
import { PanelApiError } from './errors';

export { PanelApiError };

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api';

function describe(status: number, body: unknown): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    return JSON.stringify((body as { detail: unknown }).detail);
  }
  return `HTTP ${status}`;
}

/** 计算最终面板。 */
export async function calcPanel(
  request: PanelCalcRequest,
  signal?: AbortSignal,
): Promise<PanelApiResponse> {
  const response = await fetch(`${BASE_URL}/panel/calc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new PanelApiError(describe(response.status, await safeJson(response)), response.status);
  }

  return (await response.json()) as PanelApiResponse;
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}
