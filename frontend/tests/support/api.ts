import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { vi } from 'vitest';

import { usePresetStore } from '@/stores/presetStore';
import type { AgentPreset } from '@/types/agentPresets';
import type { PanelApiResponse, PanelCalcRequest } from '@/types/panel';
import type { WeaponPreset } from '@/types/weaponPresets';

/**
 * 前端测试用的假后端。
 *
 * 第 3 步起 `usePanelCalc` 不再本地计算，所有数值都来自 `POST /api/panel/calc`；
 * 第 4 步起代理人与音擎预设也来自 `GET /api/presets/*` 而非打包进产物的常量。
 * 组件与交互测试不应该依赖真实 FastAPI 服务，因此这里用**一个** fetch stub
 * 按路径分发，生产代码无需为测试做任何让步。
 *
 * 预设刻意用仓库根 `data/*.json` 的**真实内容**，而不是手写几条假数据：
 * 这样下拉项数量、标签分组、音擎等级联动等断言同样能发现数据漂移。
 * 数值正确性由 `tests/legacy-parity.spec.ts` 与后端 `tests/test_legacy_parity.py`
 * 负责，这里只保证渲染路径可跑通。
 */

const REPO_ROOT = resolve(__dirname, '../../..');

function readPreset<T>(name: string): T[] {
  return JSON.parse(readFileSync(resolve(REPO_ROOT, 'data', name), 'utf-8')) as T[];
}

const AGENT_PRESETS = readPreset<AgentPreset>('agent-presets.json');
const WEAPON_PRESETS = readPreset<WeaponPreset>('weapon-presets.json');

const EMPTY_TOTALS: Record<string, number> = {
  hp: 10200,
  atk: 1316,
  def: 784,
  cr: 5,
  cd: 50,
  dmg: 0,
  pr: 0,
  pv: 0,
  am: 100,
  ac: 100,
  imp: 90,
  er: 1.2,
};

export function makeResponse(overrides: Partial<PanelApiResponse> = {}): PanelApiResponse {
  return {
    mode: 'standard',
    totals: { ...EMPTY_TOTALS },
    modeStats: {},
    blastDmg: null,
    sums: { hp_flat: 2200, atk_flat: 316, def_flat: 184 },
    sources: {
      hp_flat: ['1号固定固定生命+2,200'],
      atk_flat: ['2号固定固定攻击+316'],
      def_flat: ['3号固定固定防御+184'],
    },
    subFixed: { hp_flat: 0, atk_flat: 0, def_flat: 0 },
    weaponBase: { atk: 0, def: 0 },
    breakdown: {
      hp: [
        {
          type: 'line',
          wrapped: true,
          parts: [
            { type: 'text', text: '(' },
            { type: 'num', value: 8000, bold: false, unit: '' },
            { type: 'text', text: ')×(1+' },
            { type: 'kw', text: '0%' },
            { type: 'text', text: ')' },
          ],
        },
        {
          type: 'line',
          wrapped: true,
          parts: [
            { type: 'text', text: '+' },
            { type: 'num', value: 2200, bold: false, unit: '' },
            { type: 'text', text: '（1号主词条）' },
            { type: 'text', text: '+' },
            { type: 'num', value: 0, bold: false, unit: '' },
            { type: 'text', text: '（副词条）' },
            { type: 'text', text: ' = ' },
            { type: 'num', value: 10200, bold: true, unit: '' },
          ],
        },
      ],
    },
    ...overrides,
  };
}

/** 记录每次面板计算请求体，供断言「前端确实把选择发给了后端」。 */
export const requests: PanelCalcRequest[] = [];

interface Failure {
  path: string;
  message: string;
  status: number;
}

let panelResponse: PanelApiResponse = makeResponse();
let failure: Failure | null = null;

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}

function errorResponse(status: number, message: string): Response {
  return { ok: false, status, json: async () => ({ detail: message }) } as Response;
}

/**
 * 安装 fetch stub。预设端点恒返回真实数据；面板计算返回 `response`。
 * 重复调用会重置记录并恢复成功状态。
 */
export function mockApi(response: PanelApiResponse = makeResponse()): void {
  requests.length = 0;
  panelResponse = response;
  failure = null;
  vi.stubGlobal('fetch', vi.fn(handle));
}

/** 让面板计算失败，预设仍正常——用于验证结果区的错误提示。 */
export function mockPanelApiFailure(message = 'boom', status = 500): void {
  failure = { path: '/panel/calc', message, status };
}

/** 让预设拉取失败——后端在数据非法时返回 503。 */
export function mockPresetsFailure(message = '预设数据损坏', status = 503): void {
  failure = { path: '/presets/', message, status };
}

/**
 * 把预设灌进 store。生产的 `main.ts` 在 `mount` 前 `await loadAll()`，
 * 测试同样必须先装载，否则下拉是空的。
 * 必须在 `setActivePinia` 之后调用。
 */
export async function loadPresets(): Promise<void> {
  await usePresetStore().loadAll();
}

async function handle(url: string, init?: RequestInit): Promise<Response> {
  const path = String(url).replace(/^https?:\/\/[^/]+/, '').replace(/^\/api/, '');

  if (init?.body) {
    requests.push(JSON.parse(String(init.body)) as PanelCalcRequest);
  }

  if (failure && path.startsWith(failure.path)) {
    return errorResponse(failure.status, failure.message);
  }

  if (path === '/presets/agents') {
    return jsonResponse({ items: AGENT_PRESETS });
  }
  if (path === '/presets/weapons') {
    return jsonResponse({ items: WEAPON_PRESETS });
  }
  return jsonResponse(panelResponse);
}