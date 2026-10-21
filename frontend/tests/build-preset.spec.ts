import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia, type Pinia } from 'pinia';

import {
  BUILD_SCHEMA_VERSION,
  fromCompact,
  isUsableBuild,
  toCompact,
  type BuildPreset,
} from '@/types/build';
import { useBuildStore } from '@/stores/buildStore';
import { applyBuild } from '@/composables/useBuildPanel';
import { usePanelStore } from '@/stores/panelStore';
import {
  buildShareUrl,
  importBuildFromFile,
  readBuildFromHash,
  writeBuildToHash,
} from '@/composables/useBuildIO';
import { loadPresets, mockApi } from './support/api';

/**
 * 配装方案的存取。
 *
 * 方案是**本地数据**：localStorage + 文件 + URL 片段，三条路都不落服务端
 * （站点公开、无鉴权，没有可写的服务端数据面）。
 */
const SAMPLE: BuildPreset = {
  schemaVersion: BUILD_SCHEMA_VERSION,
  name: '叶瞬光 方案',
  agentId: 'ep-1687',
  weaponId: 'ep-1751',
  core: { core1: 'cr', core2: 'atk_base' },
  discMain: { disc4: 'cd_48', disc5: 'atk_pct_30', disc6: 'atk_pct_30' },
  subStats: { cr: 13, cd: 16, atk_pct: 16, atk_flat: 5, pen_val: 4 },
  sets: { set0: 'dmg_10', set1: '', set2: 'cd_16' },
  setDiscs: { set0: 'ep-1754', set1: '', set2: 'ep-1000' },
  mode: 'standard',
  savedAt: '2026-10-20T00:00:00.000Z',
};

let pinia: Pinia;

describe('配装方案的本地存取', () => {
  beforeEach(() => {
    localStorage.clear();
    pinia = createPinia();
    setActivePinia(pinia);
  });

  it('存进 localStorage 后能取回来', () => {
    const store = useBuildStore();
    store.load();
    expect(store.builds).toHaveLength(0);

    store.save(SAMPLE);
    expect(store.builds).toHaveLength(1);
    expect(store.builds[0].name).toBe('叶瞬光 方案');

    // 换一个 store 实例（模拟刷新页面）后仍然在。
    const reloaded = useBuildStore();
    reloaded.load();
    expect(reloaded.builds).toHaveLength(1);
    expect(reloaded.builds[0].core).toEqual(SAMPLE.core);
    expect(reloaded.builds[0].subStats).toEqual(SAMPLE.subStats);
  });

  it('同名同代理人的方案会被覆盖而不是堆叠', () => {
    const store = useBuildStore();
    store.load();
    store.save(SAMPLE);
    store.save({ ...SAMPLE, sets: { set0: 'cr_8', set1: '', set2: '' } });
    expect(store.builds).toHaveLength(1);
    expect(store.builds[0].sets.set0).toBe('cr_8');
  });

  it('删掉方案后 localStorage 也不留', () => {
    const store = useBuildStore();
    store.load();
    store.save(SAMPLE);
    store.remove(SAMPLE.name, SAMPLE.agentId);
    expect(store.builds).toHaveLength(0);

    const reloaded = useBuildStore();
    reloaded.load();
    expect(reloaded.builds).toHaveLength(0);
  });

  it('存坏了的 localStorage 当作没有方案，不让计算器崩', () => {
    localStorage.setItem('zzz.builds.v1', '{ 这不是 JSON');
    const store = useBuildStore();
    store.load();
    expect(store.builds).toHaveLength(0);
  });
});

describe('配装方案的分享链接', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('编码 / 解码往返', () => {
    const compact = toCompact(SAMPLE);
    expect(compact.v).toBe(BUILD_SCHEMA_VERSION);
    expect(compact.a).toBe('ep-1687');

    const restored = fromCompact(compact);
    expect(restored.agentId).toBe(SAMPLE.agentId);
    expect(restored.weaponId).toBe(SAMPLE.weaponId);
    expect(restored.core).toEqual(SAMPLE.core);
    expect(restored.discMain).toEqual(SAMPLE.discMain);
    expect(restored.subStats).toEqual(SAMPLE.subStats);
    expect(restored.sets).toEqual(SAMPLE.sets);
    expect(restored.setDiscs).toEqual(SAMPLE.setDiscs);
    expect(restored.mode).toBe(SAMPLE.mode);
  });

  it('紧凑形状丢空值，链接更短', () => {
    const compact = toCompact({
      ...SAMPLE,
      core: { core1: '', core2: '' },
      sets: { set0: '', set1: '', set2: '' },
      setDiscs: { set0: '', set1: '', set2: '' },
    });
    expect(compact.c).toBeUndefined();
    expect(compact.t).toBeUndefined();
    expect(compact.g).toBeUndefined();
    expect(compact.d).toBeDefined();
  });

  it('链接里带的就是方案本身', () => {
    const url = buildShareUrl(SAMPLE, 'https://example.com/calculator');
    expect(url.startsWith('https://example.com/calculator#build=')).toBe(true);

    const restored = readBuildFromHash(url.slice(url.indexOf('#')));
    expect(restored?.agentId).toBe('ep-1687');
    expect(restored?.subStats.cr).toBe(13);
  });

  it('片段不对时返回 null（不抛错）——失效的链接不该让访客看到报错页', () => {
    expect(readBuildFromHash('')).toBeNull();
    expect(readBuildFromHash('#build=不是JSON')).toBeNull();
    expect(readBuildFromHash('#other=1')).toBeNull();
  });

  it('版本不符的链接被拒绝', () => {
    const encoded = encodeURIComponent(JSON.stringify({ ...toCompact(SAMPLE), v: 99 }));
    expect(readBuildFromHash(`#build=${encoded}`)).toBeNull();
  });
});

describe('配装方案的导入', () => {
  it('接受导出的完整文件', async () => {
    const file = new File(
      [JSON.stringify({ schemaVersion: 1, exportedAt: 'x', build: SAMPLE })],
      'build.json',
      { type: 'application/json' },
    );
    const restored = await importBuildFromFile(file);
    expect(restored.agentId).toBe('ep-1687');
  });

  it('也接受直接就是一份方案的文件', async () => {
    const file = new File([JSON.stringify(SAMPLE)], 'build.json', {
      type: 'application/json',
    });
    const restored = await importBuildFromFile(file);
    expect(restored.name).toBe('叶瞬光 方案');
  });

  it('非法内容被拒绝并说明原因', async () => {
    const notJson = new File(['{ 这不是 JSON'], 'build.json', { type: 'application/json' });
    await expect(importBuildFromFile(notJson)).rejects.toThrow(/不是合法的 JSON/);

    const wrongShape = new File([JSON.stringify({ hello: 'world' })], 'build.json', {
      type: 'application/json',
    });
    await expect(importBuildFromFile(wrongShape)).rejects.toThrow(/格式不对/);
  });
});

describe('配装方案的形状校验', () => {
  it('版本不符的方案不算可用', () => {
    expect(isUsableBuild(SAMPLE)).toBe(true);
    expect(isUsableBuild({ ...SAMPLE, schemaVersion: 99 })).toBe(false);
    expect(isUsableBuild({ ...SAMPLE, sets: undefined })).toBe(false);
    expect(isUsableBuild(null)).toBe(false);
  });
});

describe('写进地址栏', () => {
  it('把方案写进 hash，但不刷新页面', () => {
    const replaceState = vi.spyOn(window.history, 'replaceState');
    writeBuildToHash(SAMPLE);
    expect(replaceState).toHaveBeenCalled();
    expect(window.location.hash).toContain('build=');
  });
});

describe('方案套用到计算器', () => {
  beforeEach(async () => {
    localStorage.clear();
    mockApi();
    pinia = createPinia();
    setActivePinia(pinia);
    await loadPresets();
  });

  it('把配装写回面板：核心、主词条、副词条、二件套', () => {
    const panel = usePanelStore();
    const outcome = applyBuild(SAMPLE);

    expect(outcome.ok).toBe(true);
    expect(panel.agent.presetId).toBe('ep-1687');
    expect(panel.core).toEqual(SAMPLE.core);
    expect(panel.discMain).toEqual(SAMPLE.discMain);
    expect(panel.subStats).toEqual(SAMPLE.subStats);
    expect(panel.setEffects).toEqual(SAMPLE.sets);
    expect(panel.setDiscs).toEqual(SAMPLE.setDiscs);
    expect(panel.weapon.preset).toBe('ep-1751');
  });

  it('基础面板跟着代理人预设走（不靠方案里存的那份）', () => {
    const panel = usePanelStore();
    applyBuild(SAMPLE);
    // 叶瞬光的 60 级基础面板来自代理人预设，不是方案。
    expect(panel.base.hp).toBe(7673);
  });

  it('找不到的代理人给出提示，不抛错', () => {
    const outcome = applyBuild({ ...SAMPLE, agentId: 'ep-0000' });
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toContain('找不到');
  });
});
