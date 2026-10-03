import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { JSDOM } from 'jsdom';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { mount, type VueWrapper } from '@vue/test-utils';

import CalculatorView from '@/views/CalculatorView.vue';
import { useAgentPreset } from '@/composables/useAgentPreset';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { routeFetchToBackend, startBackend, stopBackend } from './support/backend';
import { loadPresets } from './support/api';
import { flushCalc } from './support/flush';

/**
 * 三方对拍：legacy 原生 JS ≡ Vue3 页面 ≡ Python 后端。
 *
 * legacy 侧在独立 JSDOM 窗口里加载未经改动的原始 HTML 与四个脚本，
 * 按 calculator.html 中的顺序求值，跑的是旧实现本身。
 *
 * Vue 侧自第 3 步起不再本地计算，结果来自真实拉起的 FastAPI 后端
 * （`tests/support/backend.ts`）。因此这里断言的是完整链路：
 * 旧页面算出来的每一个数值与每一段明细，新页面经 HTTP 取回后必须逐字符相同。
 *
 * 后端拉不起来时整体 skip，而不是让 CI 变红。
 */

const LEGACY_ROOT = resolve(__dirname, '../legacy');
const LEGACY_SCRIPTS = [
  'data/agent-presets.js',
  'data/weapon-presets.js',
  'scripts/calculator-config.js',
  'scripts/calculator.js',
];

let legacyWindow: Window & typeof globalThis;

/**
 * 新建一个干净的 legacy 页面实例。
 *
 * 每个用例都重建，避免用例之间互相污染：legacy 的 `clearAgentPresetFields`
 * 只重置基础面板、核心与二件套，**不触碰 4/5/6 号主词条与副词条**，
 * 因此上一个用例遗留的驱动盘配置会直接影响下一个用例的数值。
 */
function createLegacyWindow(): Window & typeof globalThis {
  const dom = new JSDOM(readFileSync(resolve(LEGACY_ROOT, 'pages/calculator.html'), 'utf8'), {
    // 必须是 dangerously：jsdom 只在该模式下编译 HTML 内联的 onchange 属性，
    // 否则 legacy 的 updateWeaponGrade / applyAgentPreset 等联动不会执行。
    // 外部 <script src> 不会被真正请求（未开启 resources: 'usable'），
    // 脚本由下方以内联形式注入。
    runScripts: 'dangerously',
    url: 'http://localhost/legacy/pages/calculator.html',
  });

  // 必须合并为一段内联脚本：真实浏览器中多个 <script> 共享全局词法作用域，
  // 而独立的 eval() 各自成域，const 声明的 CORE_OPTIONS 等将不可见。
  const source = LEGACY_SCRIPTS.map((path) => readFileSync(resolve(LEGACY_ROOT, path), 'utf8')).join(
    '\n;\n',
  );
  const scriptElement = dom.window.document.createElement('script');
  scriptElement.textContent = source;
  dom.window.document.body.appendChild(scriptElement);

  return dom.window as unknown as Window & typeof globalThis;
}

let pinia: Pinia;
/** 后端不可用时为 null，整套对拍 skip。 */
let backendUrl: string | null = null;
let backendError: string | null = null;

beforeAll(async () => {
  try {
    const backend = await startBackend();
    backendUrl = backend?.baseUrl ?? null;
    if (backendUrl) {
      routeFetchToBackend(backendUrl);
    }
  } catch (cause) {
    backendError = cause instanceof Error ? cause.message : String(cause);
  }
}, 90_000);
afterAll(async () => {
  await stopBackend();
});

beforeEach(async () => {
  legacyWindow = createLegacyWindow();
  pinia = createPinia();
  setActivePinia(pinia);
  // 预设现在也来自后端，这条链路同样要被三方对拍覆盖：
  // legacy 页面读打包进 HTML 的 window.AGENT_PRESETS，Vue 页面读 HTTP 接口，
  // 两者必须拿到同一份数据。
  if (backendUrl) {
    await loadPresets();
  }
});

/* ====== legacy 侧 ====== */

function legacyDoc(): Document {
  return legacyWindow.document;
}

function legacyEvent(type: string): Event {
  return new legacyWindow.Event(type, { bubbles: true });
}

/** 触发 legacy 的 calc()。calculator.js 在 document 上监听 input/change。 */
function recalcLegacy(): void {
  legacyDoc().dispatchEvent(legacyEvent('input'));
}

function setLegacyNumber(id: string, value: number): void {
  (legacyDoc().getElementById(id) as HTMLInputElement).value = String(value);
  recalcLegacy();
}

/**
 * 按选项文案选中 legacy 的下拉框。
 * legacy 的 option value 是数组下标，这里通过文案定位再取其 value，
 * 避免在测试里重复硬编码下标。
 */
function selectLegacyByLabel(id: string, label: string): void {
  const select = legacyDoc().getElementById(id) as HTMLSelectElement;
  const option = [...select.options].find((item) => item.textContent === label);
  if (!option) {
    throw new Error(`legacy #${id} 中找不到文案为「${label}」的选项`);
  }
  select.value = option.value;
  select.dispatchEvent(legacyEvent('change'));
}

/** 在 legacy 中载入代理人预设：先选标签触发联动，再选具体代理人。 */
function applyLegacyAgent(roleTag: string, presetId: string): void {
  selectLegacyByLabel('agent_role', roleTag);
  const select = legacyDoc().getElementById('agent_preset') as HTMLSelectElement;
  select.value = presetId;
  select.dispatchEvent(legacyEvent('change'));
}

/** legacy 结果区当前可见的行标签。 */
function legacyVisibleLabels(): string[] {
  return [...legacyDoc().querySelectorAll('.result .r-row')]
    .filter((row) => !(row as HTMLElement).hidden)
    .map((row) => row.querySelector('.r-label')?.textContent ?? '');
}

/* ====== Vue 侧 ====== */

function mountVue(): VueWrapper {
  return mount(CalculatorView, { global: { plugins: [pinia] } });
}

/**
 * Vue 结果区每行的原始文案，以行标签为键。
 * 键名与 legacy 侧不同（legacy 用 id，Vue 用可见标签），
 * 故改为按行序对齐后再断言，避免标签随模式变化导致键不匹配。
 */
function readVueRows(wrapper: VueWrapper): { label: string; value: string; breakdown: string }[] {
  return wrapper.findAll('.r-row').map((row) => ({
    label: row.get('.r-label').text(),
    value: row.get('.r-value').text(),
    breakdown: row.get('.breakdown').element.innerHTML,
  }));
}

function vueVisibleLabels(wrapper: VueWrapper): string[] {
  return readVueRows(wrapper).map((row) => row.label);
}

/** legacy 侧按 DOM 顺序产出的行快照，与 Vue 侧结构一致。 */
function legacyRows(): { label: string; value: string; breakdown: string }[] {
  return [...legacyDoc().querySelectorAll('.result .r-row')]
    .filter((row) => !(row as HTMLElement).hidden)
    .map((row) => ({
      label: row.querySelector('.r-label')?.textContent ?? '',
      value: row.querySelector('.r-value')?.textContent ?? '',
      breakdown: (row.querySelector('.breakdown') as HTMLElement).innerHTML,
    }));
}

/* ====== 场景：两侧各一份，取值相同 ====== */

/** 满配场景：legacy 侧。 */
function applyFullBuildLegacy(): void {
  setLegacyNumber('base_hp', 8000);
  setLegacyNumber('base_atk', 1000);
  setLegacyNumber('base_def', 600);
  setLegacyNumber('base_impact', 90);
  setLegacyNumber('base_cr', 5);
  setLegacyNumber('base_cd', 50);
  setLegacyNumber('base_ac', 100);
  setLegacyNumber('base_am', 100);
  setLegacyNumber('base_pr', 0);
  setLegacyNumber('base_er', 1.2);

  selectLegacyByLabel('weapon_grade', 'S级');
  selectLegacyByLabel('weapon_role', '强攻');
  // 取该等级+类别下的第一个音擎
  const weaponSelect = legacyDoc().getElementById('weapon_preset') as HTMLSelectElement;
  const firstWeapon = weaponSelect.options[1];
  weaponSelect.value = firstWeapon.value;
  weaponSelect.dispatchEvent(legacyEvent('change'));

  selectLegacyByLabel('core1', '暴击率 +14.4%');
  selectLegacyByLabel('core2', '暴击伤害 +28.8%');
  selectLegacyByLabel('disc4', '攻击力 30%');
  // DISC5 为 5 选 1，不含暴击伤害
  selectLegacyByLabel('disc5', '增伤 30%');
  selectLegacyByLabel('disc6', '冲击力 24%');

  setLegacyNumber('sub_hp_flat', 12);
  setLegacyNumber('sub_atk_pct', 7);
  setLegacyNumber('sub_def_flat', 5);
  setLegacyNumber('sub_cr', 9);
  setLegacyNumber('sub_cd', 4);
  setLegacyNumber('sub_pen_val', 6);
  setLegacyNumber('sub_am', 11);

  selectLegacyByLabel('set0', '攻击力 +10%');
  selectLegacyByLabel('set1', '暴击伤害 +16%');
  selectLegacyByLabel('set2', '能量回复 +20%');
}

/** 满配场景：Vue 侧。音擎取同样的「第一个」。 */
function applyFullBuildVue(): void {
  const panel = usePanelStore();
  const { localize } = usePanelMode();

  panel.base.hp = 8000;
  panel.base.atk = 1000;
  panel.base.def = 600;
  panel.base.impact = 90;
  panel.base.cr = 5;
  panel.base.cd = 50;
  panel.base.ac = 100;
  panel.base.am = 100;
  panel.base.pr = 0;
  panel.base.er = 1.2;

  panel.selectWeaponGrade('S');
  panel.selectWeaponRole('强攻');
  panel.selectWeaponPreset(panel.filteredWeaponPresets[0].id, localize);

  panel.core.core1 = 'cr';
  panel.core.core2 = 'cd';
  panel.discMain.disc4 = 'atk_pct_30';
  // DISC5 为 5 选 1，不含暴击伤害
  panel.discMain.disc5 = 'dmg_30';
  panel.discMain.disc6 = 'impact_pct_24';

  panel.subStats.hp_flat = 12;
  panel.subStats.atk_pct = 7;
  panel.subStats.def_flat = 5;
  panel.subStats.cr = 9;
  panel.subStats.cd = 4;
  panel.subStats.pen_val = 6;
  panel.subStats.am = 11;

  panel.setEffects.set0 = 'atk_pct_10';
  panel.setEffects.set1 = 'cd_16';
  panel.setEffects.set2 = 'er_pct_20';
}

/** 后端不可用时给出明确原因而不是让断言莫名失败。 */
function requireBackend(): void {
  if (!backendUrl) {
    throw new Error(`后端未就绪，三方对拍无法进行：${backendError ?? '未知原因'}`);
  }
}

describe('三方对拍 · legacy ≡ Vue3 ≡ Python', () => {
  it('默认空配置：12 行结果逐字符一致', async () => {
    requireBackend();
    const wrapper = mountVue();
    await flushCalc();

    expect(vueVisibleLabels(wrapper)).toHaveLength(12);
    expect(vueVisibleLabels(wrapper)).toEqual(legacyVisibleLabels());
    expect(readVueRows(wrapper)).toEqual(legacyRows());
  });

  it('满配：数值与明细文案完全一致', async () => {
    requireBackend();
    applyFullBuildLegacy();
    const wrapper = mountVue();
    applyFullBuildVue();
    // legacy 直接写 DOM 是同步的；Vue 侧需等防抖 + HTTP + 渲染。
    await flushCalc();

    expect(vueVisibleLabels(wrapper)).toEqual(legacyVisibleLabels());
    expect(readVueRows(wrapper)).toEqual(legacyRows());
  });

  it('命破代理人：贯穿力行与命破专属字段一致', async () => {
    requireBackend();
    applyLegacyAgent('命破', 'ep-1299');
    const wrapper = mountVue();
    usePanelStore().selectAgentRole('命破');
    useAgentPreset().applyAgentPreset('ep-1299');
    await flushCalc();

    expect(vueVisibleLabels(wrapper)).toContain('贯穿力');
    expect(vueVisibleLabels(wrapper)).toEqual(legacyVisibleLabels());
    expect(readVueRows(wrapper)).toEqual(legacyRows());
  });

  it('锋御代理人：实际暴击率与锐暴伤害行一致', async () => {
    requireBackend();
    applyLegacyAgent('锋御', 'ep-2145');
    const wrapper = mountVue();
    usePanelStore().selectAgentRole('锋御');
    useAgentPreset().applyAgentPreset('ep-2145');
    await flushCalc();

    const labels = vueVisibleLabels(wrapper);
    expect(labels).toContain('实际暴击率');
    expect(labels).toContain('锐暴伤害');
    expect(labels).toContain('锐能自动累积');
    expect(vueVisibleLabels(wrapper)).toEqual(legacyVisibleLabels());
    expect(readVueRows(wrapper)).toEqual(legacyRows());
  });
});