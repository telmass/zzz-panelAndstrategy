import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { enableAutoUnmount, mount, type VueWrapper } from '@vue/test-utils';
import { nextTick } from 'vue';

import CalculatorView from '@/views/CalculatorView.vue';
import { useAgentPreset } from '@/composables/useAgentPreset';
import { displayEnergyAttributeLabel, usePanelMode } from '@/composables/usePanelMode';
import { useSubStatLimit } from '@/composables/useSubStatLimit';
import { usePanelStore } from '@/stores/panelStore';
import { loadPresets, mockApi, mockPanelApiFailure, requests } from './support/api';
import { flushCalc } from './support/flush';

/**
 * 交互行为测试：对应第 2 步指南第 9、10 项。
 * 数值等价性由 tests/legacy-parity.spec.ts 负责，此处只验证状态流转。
 *
 * 第 3 步起结果来自后端，因此挂载组件前先接上假后端：否则 jsdom 里 fetch
 * 会静默失败，组件停在 `—`，用例会因「碰巧不依赖数值」而通过——
 * 看似绿，实则没验证到渲染路径。第 4 步起预设同样走接口，故一并装载。
 */

let pinia: Pinia;

/**
 * 必须自动卸载。
 *
 * `usePanelCalc` 的 watcher 回调里调用 `usePanelStore()`，在 watcher 作用域外
 * 会回落到 activePinia。若组件不卸载，上一个用例遗留的 watcher 就会跟着
 * 新用例的 store 一起触发，请求计数变得不可预测。
 */
enableAutoUnmount(afterEach);

beforeEach(async () => {
  pinia = createPinia();
  setActivePinia(pinia);
  mockApi();
  await loadPresets();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function mountView(): VueWrapper {
  return mount(CalculatorView, { global: { plugins: [pinia] } });
}

function select(wrapper: VueWrapper, id: string): HTMLSelectElement {
  return wrapper.get(`#${id}`).element as HTMLSelectElement;
}

describe('音擎三级联动', () => {
  it('未选等级时类别与名称均禁用', () => {
    const wrapper = mountView();
    expect(select(wrapper, 'weapon_role').disabled).toBe(true);
    expect(select(wrapper, 'weapon_preset').disabled).toBe(true);
  });

  it('选等级后解锁类别、仍锁定名称，并清空只读回填区', async () => {
    const wrapper = mountView();
    const grade = select(wrapper, 'weapon_grade');
    grade.value = 'S';
    grade.dispatchEvent(new Event('change'));

    await nextTick();
    expect(select(wrapper, 'weapon_role').disabled).toBe(false);
    expect(select(wrapper, 'weapon_preset').disabled).toBe(true);
    expect(select(wrapper, 'weapon_role').options.length).toBeGreaterThan(1);
  });

  it('锁定顺序：等级 → 类别 → 名称，逐级解锁', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();

    panel.selectWeaponGrade('S');
    await nextTick();
    expect(select(wrapper, 'weapon_role').disabled).toBe(false);

    panel.selectWeaponRole('强攻');
    await nextTick();
    expect(select(wrapper, 'weapon_preset').disabled).toBe(false);
  });

  it('切换等级会清空下游选择与回填区', () => {
    const panel = usePanelStore();
    panel.selectWeaponGrade('S');
    panel.selectWeaponRole('强攻');
    panel.selectWeaponPreset(panel.filteredWeaponPresets[0].id, (text) => text);
    expect(panel.weapon.preset).not.toBe('');

    panel.selectWeaponGrade('A');
    expect(panel.weapon.roleTag).toBe('');
    expect(panel.weapon.preset).toBe('');
    expect(panel.weapon.baseValue).toBe(0);
    expect(panel.weapon.subType).toBe('—');
    expect(panel.weapon.baseLabel).toBe('基础攻击力');
  });

  it('选中音擎后回填基础值与固定副词条', () => {
    const panel = usePanelStore();
    panel.selectWeaponGrade('S');
    panel.selectWeaponRole('强攻');
    const weapon = panel.filteredWeaponPresets[0];
    panel.selectWeaponPreset(weapon.id, (text) => text);

    expect(panel.weapon.baseValue).toBe(weapon.baseKind === 'def' ? weapon.baseDefense : weapon.baseAttack);
    expect(panel.weapon.subType).toBe(weapon.substat.label);
    expect(panel.weapon.subValue).toBe(weapon.substat.value);
  });

  it('锋御音擎（baseKind=def）回填基础防御力', () => {
    const panel = usePanelStore();
    panel.selectWeaponGrade('S');
    panel.selectWeaponRole('强攻');
    const defWeapon = panel.filteredWeaponPresets.find((w) => w.baseKind === 'def');
    if (!defWeapon) {
      return;
    }
    panel.selectWeaponPreset(defWeapon.id, (text) => text);
    expect(panel.weapon.baseLabel).toBe('基础防御力');
    expect(panel.weapon.baseValue).toBe(defWeapon.baseDefense);
  });
});

describe('副词条钳制', () => {
  it('合计不超过 54：超出时从最后修改项回填', () => {
    const { setCount, totalCount } = useSubStatLimit();
    setCount('hp_flat', 36);
    setCount('cr', 18);
    expect(totalCount.value).toBe(54);

    // 再加 1 条时，本项被压回可用余量 0
    setCount('cr', 19);
    expect(totalCount.value).toBe(54);
  });

  it('单项上限 36 条', () => {
    const { setCount } = useSubStatLimit();
    setCount('atk_flat', 99);
    expect(usePanelStore().subStats.atk_flat).toBe(36);
  });

  it('负数与小数被归一化', () => {
    const { setCount } = useSubStatLimit();
    const panel = usePanelStore();

    setCount('hp_flat', -5);
    expect(panel.subStats.hp_flat).toBe(0);

    setCount('hp_flat', 7.9);
    expect(panel.subStats.hp_flat).toBe(7);

    setCount('hp_flat', 'abc');
    expect(panel.subStats.hp_flat).toBe(0);
  });

  it('合计达 54 时加号禁用，减号仍可用', async () => {
    const wrapper = mountView();
    useSubStatLimit().setCount('hp_flat', 36);
    useSubStatLimit().setCount('cr', 18);
    await nextTick();

    const rows = wrapper.findAll('.sub-count');
    // 取「暴击率」一行（索引 6）
    const crButtons = rows[6].findAll('.sub-count-btn');
    expect((crButtons[0].element as HTMLButtonElement).disabled).toBe(false);
    expect((crButtons[1].element as HTMLButtonElement).disabled).toBe(true);
    expect(wrapper.text()).toContain('副词条总数：54 / 54');
  });

  it('步进按钮改变条数并联动合计', async () => {
    const wrapper = mountView();
    const row = wrapper.findAll('.sub-count')[0];
    await row.findAll('.sub-count-btn')[1].trigger('click');

    expect(usePanelStore().subStats.hp_flat).toBe(1);
    expect(wrapper.text()).toContain('副词条总数：1 / 54');
    // 1 条 × 112
    expect(row.get('.total').text()).toBe('112');
  });

  it('百分比类副词条的折算值带 % 号', () => {
    const { setCount } = useSubStatLimit();
    setCount('hp_pct', 4);
    const { entries } = useSubStatLimit();
    const entry = entries.value.find((item) => item.def.id === 'hp_pct');
    expect(entry?.total).toBe('12%');
  });

  // 4.8 在二进制浮点下存成 4.799999999999999822…，×3 后落在相邻两个 double 的
  // 正中点，round-half-to-even 舍到 14.399999999999999。不做舍入就会原样显示。
  it('小数单条值的累加不出现浮点误差', () => {
    const { setCount } = useSubStatLimit();
    setCount('def_pct', 3);
    const { entries } = useSubStatLimit();
    const entry = entries.value.find((item) => item.def.id === 'def_pct');
    expect(entry?.total).toBe('14.4%');
  });

  it('固定值累加显示千分位', () => {
    const { setCount } = useSubStatLimit();
    setCount('hp_flat', 36);
    const { entries } = useSubStatLimit();
    const entry = entries.value.find((item) => item.def.id === 'hp_flat');
    expect(entry?.total).toBe('4,032');
  });
});

describe('面板模式与锋御文案', () => {
  it('命破模式隐藏穿透率与能量回复，显示贯穿力与闪能自动累积', () => {
    const panel = usePanelStore();
    panel.setPanelMode('rupture');
    const { showPenetrationInput, showEnergyReplyInput, showPenforceInput, showEnergyAccumulationInput } =
      usePanelMode();

    expect(showPenetrationInput.value).toBe(false);
    expect(showEnergyReplyInput.value).toBe(false);
    expect(showPenforceInput.value).toBe(true);
    expect(showEnergyAccumulationInput.value).toBe(true);
  });

  it('锋御模式把能量类文案替换为锐能', () => {
    expect(displayEnergyAttributeLabel('基础能量自动回复 +0.36', 'fengyu')).toBe('基础锐能自动累积 +0.36');
    expect(displayEnergyAttributeLabel('能量回复 60%', 'fengyu')).toBe('锐能自动累积 60%');
    expect(displayEnergyAttributeLabel('能量自动回复', 'standard')).toBe('能量自动回复');
  });

  it('锋御模式的能量标签同时作用于输入区与结果区', () => {
    const panel = usePanelStore();
    panel.setPanelMode('fengyu');
    const { energyInputLabel, energyResultLabel } = usePanelMode();
    expect(energyInputLabel.value).toBe('锐能自动累积');
    expect(energyResultLabel.value).toBe('锐能自动累积');
  });
});

describe('代理人标签联动与预设载入', () => {
  it('未选标签时代理人下拉禁用', () => {
    const wrapper = mountView();
    expect(select(wrapper, 'agent_preset').disabled).toBe(true);
  });

  it('选标签后解锁并按标签过滤', async () => {
    const wrapper = mountView();
    usePanelStore().selectAgentRole('命破');
    await nextTick();

    const presetSelect = select(wrapper, 'agent_preset');
    expect(presetSelect.disabled).toBe(false);
    // 命破代理人数量 + 1 项占位
    expect(presetSelect.options.length).toBe(
      usePanelStore().filteredAgentPresets.length + 1,
    );
    // 选项文案含角色标签与模式名
    expect(presetSelect.options[1].textContent).toContain('命破');
  });

  it('载入命破预设后写入基础面板、命破专属字段与面板模式', () => {
    const panel = usePanelStore();
    panel.selectAgentRole('命破');
    const note = useAgentPreset().applyAgentPreset('ep-1299');

    expect(note.tone).toBe('neutral');
    expect(panel.panelMode).toBe('rupture');
    expect(panel.base.penforce).toBeGreaterThan(0);
    expect(panel.base.energyAccumulation).toBeGreaterThanOrEqual(0);
    expect(panel.core.core1).not.toBe('');
    expect(panel.core.core2).not.toBe('');
    expect(note.text).toContain('已载入');
  });

  it('载入锋御预设后面板模式为 fengyu 且不含未建模属性提示', () => {
    const panel = usePanelStore();
    panel.selectAgentRole('锋御');
    const note = useAgentPreset().applyAgentPreset('ep-2145');

    expect(panel.panelMode).toBe('fengyu');
    // 锐暴伤害已建模，不应出现在「尚未建模」提示里
    expect(note.text).not.toContain('锐暴伤害');
  });

  it('标签与预设不匹配时给出错误提示且不写入字段', () => {
    const panel = usePanelStore();
    panel.selectAgentRole('强攻');
    const note = useAgentPreset().applyAgentPreset('ep-1299');

    expect(note.tone).toBe('error');
    expect(note.text).toContain('不属于当前选择的');
    expect(panel.agent.presetId).toBe('');
  });

  it('找不到预设时给出错误提示', () => {
    const panel = usePanelStore();
    panel.selectAgentRole('强攻');
    const note = useAgentPreset().applyAgentPreset('ep-does-not-exist');
    expect(note.tone).toBe('error');
    expect(note.text).toContain('找不到');
  });

  it('载入预设会重置音擎与二件套，但保留副词条', () => {
    const panel = usePanelStore();
    useSubStatLimit().setCount('hp_flat', 5);
    panel.setEffects.set0 = 'atk_pct_10';
    panel.selectWeaponGrade('S');

    panel.selectAgentRole('强攻');
    useAgentPreset().applyAgentPreset(panel.filteredAgentPresets[0].id);

    expect(panel.weapon.grade).toBe('');
    expect(panel.setEffects.set0).toBe('');
    expect(panel.subStats.hp_flat).toBe(5);
  });

  it('切换标签会把面板模式回落到 URL 请求的模式', () => {
    const panel = usePanelStore();
    panel.requestedMode = 'rupture';
    panel.setPanelMode('rupture');
    panel.appliedAgentPresetId = 'ep-1299';

    panel.selectAgentRole('强攻');
    expect(panel.panelMode).toBe('rupture');
  });

  it('URL 的 mode 参数非法时回落到 standard', () => {
    const panel = usePanelStore();
    useAgentPreset().initFromQueryParam('not-a-mode');
    expect(panel.requestedMode).toBe('standard');
    expect(panel.panelMode).toBe('standard');
  });

  it('URL 的 mode 参数合法时采用该模式', () => {
    useAgentPreset().initFromQueryParam('fengyu');
    expect(usePanelStore().panelMode).toBe('fengyu');
  });
});

/**
 * 第 3 步新增：计算下沉到后端后，请求组装与失败反馈成为接口契约的一部分。
 * 这些断言无法在第 2 步存在——那时前端自己算，没有网络请求可言。
 */
describe('后端对接', () => {
  it('挂载后发出计算请求，且只带选择不带数值口径', async () => {
    mountView();
    await flushCalc();

    expect(requests.length).toBeGreaterThanOrEqual(1);
    const body = requests[requests.length - 1];
    // 选择以 id 形式上传
    expect(body.core).toEqual({ core1: '', core2: '' });
    expect(body.discMain).toEqual({ disc4: '', disc5: '', disc6: '' });
    expect(body.sets).toEqual({ set0: '', set1: '', set2: '' });
    // 基础面板与模式
    expect(body.mode).toBe('standard');
    expect(body.base.hp).toBe(8000);
    // 未选音擎时不带副词条
    expect(body.weapon.substat).toBeNull();
  });

  it('改动副词条条数会重新请求，且请求体反映最新条数', async () => {
    mountView();
    await flushCalc();
    const before = requests.length;

    useSubStatLimit().setCount('cr', 6);
    await flushCalc();

    expect(requests.length).toBeGreaterThan(before);
    expect(requests[requests.length - 1].subStats.cr).toBe(6);
  });

  it('选定音擎后请求带上基础值与固定副词条', async () => {
    const panel = usePanelStore();
    mountView();
    panel.selectWeaponGrade('S');
    panel.selectWeaponRole('强攻');
    const preset = panel.filteredWeaponPresets[0];
    panel.selectWeaponPreset(preset.id, (text) => text);

    await flushCalc();

    const last = requests[requests.length - 1];
    expect(last.weapon.baseKind).toBe(preset.baseKind ?? 'atk');
    expect(last.weapon.baseValue).toBe(panel.weapon.baseValue);
    expect(last.weapon.substat).toMatchObject({
      value: preset.substat.value,
      label: preset.substat.label,
    });
  });

  it('面板模式变化会带上新的 mode 重新请求', async () => {
    const panel = usePanelStore();
    mountView();
    await flushCalc();

    panel.setPanelMode('rupture');
    await flushCalc();

    expect(requests[requests.length - 1].mode).toBe('rupture');
  });

  it('后端不可用时给出失败提示而不是静默显示占位符', async () => {
    mockPanelApiFailure('服务不可用', 503);
    const wrapper = mountView();
    await flushCalc();

    expect(wrapper.find('.calc-error').text()).toContain('面板计算失败');
    expect(wrapper.find('.calc-error').text()).toContain('服务不可用');
    // 失败时数值回落到占位符
    expect(wrapper.find('.r-value').text()).toBe('—');
  });

  it('请求进行中显示计算中提示', async () => {
    const wrapper = mountView();
    // 防抖窗口内、响应回来之前
    await new Promise((r) => setTimeout(r, 50));
    expect(wrapper.find('.calc-pending').exists()).toBe(true);

    await flushCalc();
    expect(wrapper.find('.calc-pending').exists()).toBe(false);
  });
});