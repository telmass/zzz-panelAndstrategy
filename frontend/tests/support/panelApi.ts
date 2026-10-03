import { vi } from 'vitest';

import type { PanelApiResponse, PanelCalcRequest } from '@/types/panel';

/**
 * 前端测试用的假后端。
 *
 * 第 3 步起 `usePanelCalc` 不再本地计算，所有数值都来自 `POST /api/panel/calc`。
 * 组件与交互测试不应该依赖真实 FastAPI 服务，因此这里用 `fetch` mock 返回一份
 * 结构合法的响应，**数值本身由 `tests/legacy-parity.spec.ts` 与后端
 * `tests/test_legacy_parity.py` 负责校验**，此处只保证渲染路径可跑通。
 */

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

/** 记录每次请求体，供断言「前端确实把选择发给了后端」。 */
export const requests: PanelCalcRequest[] = [];

export function mockPanelApi(response: PanelApiResponse = makeResponse()): void {
  requests.length = 0;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.body) {
        requests.push(JSON.parse(String(init.body)));
      }
      return {
        ok: true,
        status: 200,
        json: async () => response,
      } as Response;
    }),
  );
}

/** 让请求失败，用于验证错误提示。 */
export function mockPanelApiFailure(message = 'boom', status = 500): void {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: false,
      status,
      json: async () => ({ detail: message }),
    })),
  );
}
