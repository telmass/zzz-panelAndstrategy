import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { enableAutoUnmount, mount, type VueWrapper } from '@vue/test-utils';
import { nextTick } from 'vue';
import { NCascader } from 'naive-ui';

import CalculatorView from '@/views/CalculatorView.vue';
import { isSpecialAttribute, specialAgentAttributes, useAgentPreset } from '@/composables/useAgentPreset';
import { displayEnergyAttributeLabel, usePanelMode } from '@/composables/usePanelMode';
import { useSubStatLimit } from '@/composables/useSubStatLimit';
import { usePanelStore } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
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

/** 数值/文本输入框。 */
function input(wrapper: VueWrapper, id: string): HTMLInputElement {
  return wrapper.get(`#${id}`).element as HTMLInputElement;
}

/** 代理人职业标签全集，分组顺序即此顺序。 */
const AGENT_ROLE_TAGS = ['强攻', '击破', '异常', '支援', '防护', '命破', '锋御'];

/** 代理人属性类型全集。 */
const AGENT_ATTRIBUTES = ['火', '冰', '电', '以太', '物理', '烈霜', '玄墨', '凛刃', '风', '流明'];

/** 代理人评级全集。 */
const AGENT_GRADES = ['S', 'A'];

/** 音擎职业标签全集，分组顺序即此顺序。 */
const WEAPON_ROLE_TAGS = ['强攻', '击破', '异常', '支援', '防护', '命破', '锋御'];

/** 取预设库里的全部音擎，供不依赖界面直接验证 store 的用例使用。 */
function allWeapons() {
  return usePresetStore().weapons;
}

/**
 * 代理人选择器的 cascader。
 *
 * 页面上有两个 cascader（代理人、音擎），用例必须按 class 定位：
 * `findComponent(NCascader)` 只会命中先渲染的那个，改了模块顺序就指错人。
 */
function agentCascader(wrapper: VueWrapper) {
  return wrapper.getComponent<typeof NCascader>('.agent-picker-input');
}

/** 音擎选择器的 cascader。 */
function weaponCascader(wrapper: VueWrapper) {
  return wrapper.getComponent<typeof NCascader>('.weapon-picker-input');
}

describe('音 cascader 分组与回填', () => {
  it('未选音擎时不出卡片，只读回填区为初始态', () => {
    const wrapper = mountView();
    expect(wrapper.find('.weapon-card').exists()).toBe(false);
    expect(usePanelStore().selectedWeapon).toBeNull();
    expect(input(wrapper, 'weapon_base_value').value).toBe('0');
    expect(input(wrapper, 'weapon_sub_type').value).toBe('—');
  });

  it('按 7 个职业标签分组，组序固定为 WEAPON_ROLE_TAGS', () => {
    const groups = usePanelStore().weaponPresetGroups;
    expect(groups.map((group) => group.label)).toEqual(WEAPON_ROLE_TAGS);
    // 一级项的 value 即职业标签，二级项才是具体音擎
    expect(groups.every((group) => group.value === group.label)).toBe(true);
  });

  it('等级不再是筛选轴：全部音擎都在分组内，且每个职业标签都非空', () => {
    const panel = usePanelStore();
    const weapons = allWeapons();
    const grouped = panel.weaponPresetGroups.flatMap((group) => group.children ?? []);

    expect(grouped).toHaveLength(weapons.length);
    // 每条音擎恰好出现一次，不重不漏
    expect(new Set(grouped.map((option) => option.value)).size).toBe(weapons.length);
    for (const roleTag of WEAPON_ROLE_TAGS) {
      expect(weapons.some((weapon) => weapon.roleTag === roleTag)).toBe(true);
    }
  });

  it('选项文案为「名称 / 职业 / 等级」，且不含推荐标记（数据源尚未落地）', () => {
    const weapons = allWeapons();
    const grouped = usePanelStore().weaponPresetGroups.flatMap((group) => group.children ?? []);
    const offense = weapons.find((weapon) => weapon.roleTag === '强攻');
    const offenseLabel = grouped.find((option) => option.value === offense?.id)?.label;

    expect(offenseLabel).toBe(`${offense?.name} / 强攻 / ${offense?.grade}级`);
    expect(offenseLabel).not.toContain('角色推荐');
    // 段数固定为 3：多一段说明推荐接缝意外产出了值
    expect(offenseLabel?.split(' / ')).toHaveLength(3);
  });

  it('展开浮层 Teleport 到 body，一级项与 store 分组同源', async () => {
    const wrapper = mountView();

    expect(document.body.querySelector('.n-cascader-menu')).toBeNull();
    await wrapper.get('.weapon-picker-input .n-base-selection').trigger('click');
    await nextTick();

    // 浮层 Teleport 到 body，不在 wrapper 树内。选项本身在 n-virtual-list 内，
    // jsdom 无布局时容器高度为 0、一项都不会渲染，所以「7 个一级项」在上面的
    // store 用例里断言；此处只验证浮层确实被打开。
    expect(document.body.querySelector('.n-cascader-menu')).not.toBeNull();
    expect(weaponCascader(wrapper).props('options')).toHaveLength(WEAPON_ROLE_TAGS.length);
  });

  it('render-prefix：一级取 roletag 图标、二级取音擎头像，未知 roletag 不渲染', () => {
    const wrapper = mountView();
    const renderPrefix = weaponCascader(wrapper).props('renderPrefix') as
      (props: { option: unknown }) => { props: Record<string, unknown> } | null;

    // 一级项带 children，value 即职业标签
    const group = usePanelStore().weaponPresetGroups[0];
    const groupIcon = renderPrefix({ option: group });
    expect(groupIcon?.props.src).toBe('/images/icons/strike.png');

    // 二级项是叶子，value 即音擎 id
    const weapon = allWeapons()[0];
    const leafIcon = renderPrefix({ option: group.children?.[0] });
    expect(leafIcon?.props.src).toBe(`/images/weapons/${weapon.id}.png`);
    // 图标是纯装饰，不参与 filterable 的匹配，故 alt 必须为空
    expect(groupIcon?.props.alt).toBe('');

    // 职业标签不在映射表里时返回 null——宁可没有图标，也不要破图方块
    expect(renderPrefix({ option: { label: 'x', value: '未知职业', children: [{}] } })).toBeNull();
    expect(renderPrefix({ option: { label: 'x', value: '' } })).toBeNull();
  });

  it('render-label：浏览时二级项只显示名称，但选项 label 与选中后展示仍是完整文案', () => {
    const wrapper = mountView();
    const renderLabel = weaponCascader(wrapper).props('renderLabel') as (option: unknown) => string | undefined;
    const panel = usePanelStore();
    const weapon = allWeapons()[0];

    const group = panel.weaponPresetGroups[0];
    const leaf = group.children?.find((option) => option.value === weapon.id);
    expect(leaf).toBeDefined();

    // 浏览过程中：一级仍是职业标签，二级只有武器名称，不含 roletag 与评级
    expect(renderLabel(group)).toBe('强攻');
    expect(renderLabel(leaf)).toBe(weapon.name);
    expect(renderLabel(leaf)).not.toContain(weapon.roleTag);
    expect(renderLabel(leaf)).not.toContain(`${weapon.grade}级`);

    // 完整文案必须留在 label 上：naive-ui 渲染折叠框时直接读 rawNode.label，
    // 不经过 renderLabel，所以选中后仍显示「名称 / 职业 / 等级」
    expect(leaf?.label).toBe(`${weapon.name} / ${weapon.roleTag} / ${weapon.grade}级`);

    // 未知 id 退回原 label，不渲染空白项
    expect(renderLabel({ label: '未知项', value: 'ep-does-not-exist' })).toBe('未知项');
  });

  it('cascader 上报叶子值后回填基础值、固定副词条、职业标签与等级', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    const weapon = allWeapons()[0];

    // 走组件自己的 onSelect，而不是绕过它直接调 store
    weaponCascader(wrapper).vm.$emit('update:value', weapon.id);
    await nextTick();

    expect(panel.weapon.roleTag).toBe(weapon.roleTag);
    expect(panel.weapon.grade).toBe(weapon.grade);
    expect(panel.weapon.baseValue).toBe(weapon.baseKind === 'def' ? weapon.baseDefense : weapon.baseAttack);
    expect(panel.weapon.subType).toBe(weapon.substat.label);
    expect(panel.weapon.subValue).toBe(weapon.substat.value);
  });

  it('cascader 上报 null 走 clearable 路径，清除选择', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    panel.selectWeaponPreset(allWeapons()[0].id, (text) => text);
    await nextTick();

    weaponCascader(wrapper).vm.$emit('update:value', null);
    await nextTick();

    expect(panel.weapon.preset).toBe('');
    expect(wrapper.find('.weapon-card').exists()).toBe(false);
  });

  it('选中后展示头像卡片：名称、职业/等级与按 id 拼出的图片路径', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    const weapon = allWeapons()[0];

    expect(wrapper.find('.weapon-card').exists()).toBe(false);
    panel.selectWeaponPreset(weapon.id, (text) => text);
    await nextTick();

    const card = wrapper.get('.weapon-card');
    expect(card.get('.weapon-card-name').text()).toBe(weapon.name);
    expect(card.get('.weapon-card-meta').text()).toBe(`${weapon.roleTag} / ${weapon.grade}级`);
    // public/ 原样拷贝到 dist 根，故按 URL 取而非 import
    expect(card.get('.weapon-card-avatar').attributes('src')).toBe(`/images/weapons/${weapon.id}.png`);
  });

  it('清除选择后 preset、职业标签、等级与回填区一并复位', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    panel.selectWeaponPreset(allWeapons()[0].id, (text) => text);
    await nextTick();
    expect(wrapper.find('.weapon-card').exists()).toBe(true);

    // cascader 的 clearable 走的就是「值为 null」这条回调
    panel.selectWeaponPreset('', (text) => text);
    await nextTick();

    expect(panel.weapon.preset).toBe('');
    expect(panel.weapon.roleTag).toBe('');
    expect(panel.weapon.grade).toBe('');
    expect(panel.weapon.baseValue).toBe(0);
    expect(panel.weapon.subType).toBe('—');
    expect(panel.weapon.baseLabel).toBe('基础攻击力');
    expect(wrapper.find('.weapon-card').exists()).toBe(false);
  });

  it('锋御音擎（baseKind=def）回填基础防御力', () => {
    const panel = usePanelStore();
    const defWeapon = allWeapons().find((w) => w.baseKind === 'def');
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

describe('代理人 cascader 分组与载入', () => {
  it('未选代理人时值为空且不锁定，展开浮层仍可选可搜', () => {
    const wrapper = mountView();
    expect(wrapper.find('.agent-card').exists()).toBe(false);
    expect(usePanelStore().selectedAgent).toBeNull();

    // 旧的「未选标签则禁用代理人下拉」状态已不存在：cascader 一律可点可搜
    const cascader = agentCascader(wrapper);
    expect(cascader.props('value')).toBeNull();
    expect(cascader.props('filterable')).toBe(true);
    expect(cascader.props('options')).toHaveLength(AGENT_ROLE_TAGS.length);
    expect(wrapper.get('.agent-picker-input .n-base-selection').classes()).not.toContain(
      'n-base-selection--disabled',
    );
  });

  it('分组覆盖全部代理人，组序固定为 AGENT_ROLE_TAGS，组内保持数据原序', () => {
    const panel = usePanelStore();
    const agents = usePresetStore().agents;

    expect(panel.agentPresetGroups.map((group) => group.label)).toEqual(AGENT_ROLE_TAGS);
    const grouped = panel.agentPresetGroups.flatMap((group) => group.children ?? []);
    // 不重不漏：分组只是换了展示形态，不能丢代理人
    expect(grouped).toHaveLength(agents.length);
    expect(new Set(grouped.map((option) => option.value)).size).toBe(agents.length);
    // 组内保持 data/agent-presets.json 的原序
    for (const group of panel.agentPresetGroups) {
      const expected = agents.filter((agent) => agent.roleTag === group.label).map((a) => a.id);
      expect(group.children?.map((option) => option.value)).toEqual(expected);
    }
  });

  it('每条代理人都带合法 attribute 与 grade', () => {
    const agents = usePresetStore().agents;

    expect(agents).toHaveLength(60);
    for (const agent of agents) {
      expect(AGENT_ATTRIBUTES).toContain(agent.attribute);
      expect(AGENT_GRADES).toContain(agent.grade);
    }
  });

  it('特殊属性 = 当前只有一名代理人持有的属性', () => {
    const agents = usePresetStore().agents;
    const counts = new Map<string, number>();
    for (const agent of agents) {
      counts.set(agent.attribute, (counts.get(agent.attribute) ?? 0) + 1);
    }

    expect([...specialAgentAttributes(agents)].sort()).toEqual(
      [...counts].filter(([, count]) => count === 1).map(([key]) => key).sort(),
    );

    // 规则只看人数：风 有两名持有人，因此不是特殊属性
    expect(counts.get('风')).toBe(2);
    expect(isSpecialAttribute('风', agents)).toBe(false);
    expect(isSpecialAttribute('烈霜', agents)).toBe(true);
    expect(isSpecialAttribute('火', agents)).toBe(false);
    expect(isSpecialAttribute('不存在的属性', agents)).toBe(false);
  });

  it('特殊属性不写死名单：一个全新的单人属性同样被判为特殊', () => {
    const base = usePresetStore().agents[0];
    const roster = [
      { ...base, id: 'ep-9001', name: '甲', attribute: '玄墨' },
      { ...base, id: 'ep-9002', name: '乙', attribute: '玄墨' },
      { ...base, id: 'ep-9003', name: '丙', attribute: '全新属性' },
    ];

    expect([...specialAgentAttributes(roster)]).toEqual(['全新属性']);
  });

  it('选项文案为「名称 / 职业」，职业与模式同字时只出现一次', () => {
    const panel = usePanelStore();
    const agents = usePresetStore().agents;
    const grouped = panel.agentPresetGroups.flatMap((group) => group.children ?? []);

    // 通用模式的中文名被 panelModeTagLabel 隐去，故只剩「职业 / 属性 / 评级」三段
    const standard = agents.find((agent) => agent.panelMode === 'standard');
    expect(grouped.find((option) => option.value === standard?.id)?.label).toBe(
      `${standard?.name} / ${standard?.roleTag} / ${standard?.attribute} / ${standard?.grade}级`,
    );

    // 命破代理人的 roleTag 与模式名同字，去重后仍是 4 段而不是 5 段
    const rupture = agents.find((agent) => agent.panelMode === 'rupture');
    const ruptureLabel = grouped.find((option) => option.value === rupture?.id)?.label;
    expect(ruptureLabel).toBe(
      `${rupture?.name} / 命破 / ${rupture?.attribute} / ${rupture?.grade}级`,
    );
    expect(ruptureLabel?.split(' / ')).toHaveLength(4);
    expect(ruptureLabel).not.toContain('命破 / 命破');

    // 每个选项都带属性与评级，且用的是官方写法「电」而不是「雷」
    for (const agent of agents) {
      const label = grouped.find((option) => option.value === agent.id)?.label ?? '';
      expect(label).toContain(` / ${agent.attribute} / `);
      expect(label).toContain(` / ${agent.grade}级`);
      expect(AGENT_ATTRIBUTES).toContain(agent.attribute);
    }

    // 三个模式都不出现「通用」二字
    for (const option of grouped) {
      expect(option.label).not.toContain('通用');
    }
  });

  it('折叠框只显示叶子文案，职业标签不重复（show-path 已关）', () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    const agents = usePresetStore().agents;

    // naive-ui 的 showPath 默认为 true，此时折叠框显示的是「整条路径的 label 拼接」
    // （Cascader.mjs 的 selectedOptionRef → getPathLabel）。一级项正是职业标签，
    // 叶子文案里又带着同一个职业标签，于是会显示成
    // 「强攻 / 伊芙琳·舒瓦利耶 / 强攻 / 火 / S级」——职业标签出现两次。
    expect(agentCascader(wrapper).props('showPath')).toBe(false);

    // 关掉后折叠框只显示叶子文案，故叶子文案自身不得重复职业标签
    for (const agent of agents) {
      const label = panel.agentPresetGroups
        .flatMap((group) => group.children ?? [])
        .find((option) => option.value === agent.id)?.label;
      expect(label?.split(' / ')).toHaveLength(4);
      expect(label?.split(agent.roleTag)).toHaveLength(2);
    }
  });

  it('音擎折叠框同样只显示叶子文案（show-path 已关）', () => {
    const wrapper = mountView();
    const weapons = allWeapons();

    expect(weaponCascader(wrapper).props('showPath')).toBe(false);

    const grouped = usePanelStore().weaponPresetGroups.flatMap((group) => group.children ?? []);
    for (const weapon of weapons) {
      const label = grouped.find((option) => option.value === weapon.id)?.label;
      expect(label?.split(' / ')).toHaveLength(3);
      expect(label?.split(weapon.roleTag)).toHaveLength(2);
    }
  });

  it('render-prefix：一级取 roletag 图标、二级取代理人头像', () => {
    const wrapper = mountView();
    const renderPrefix = agentCascader(wrapper).props('renderPrefix') as (
      props: { option: unknown },
    ) => { props: Record<string, unknown> } | null;

    const group = usePanelStore().agentPresetGroups[0];
    expect(renderPrefix({ option: group })?.props.src).toBe('/images/icons/strike.png');

    const agent = usePresetStore().agents.find((item) => item.roleTag === group.label);
    expect(renderPrefix({ option: group.children?.[0] })?.props.src).toBe(
      `/images/agents/${agent?.id}.png`,
    );
    // 装饰性图标不参与 filterable 的匹配，故 alt 必须为空
    expect(renderPrefix({ option: group })?.props.alt).toBe('');
  });

  it('render-label：浏览时二级项只显示名称，选项 label 与选中后展示仍是完整文案', () => {
    const wrapper = mountView();
    const renderLabel = agentCascader(wrapper).props('renderLabel') as (
      option: unknown,
    ) => string | undefined;

    const group = usePanelStore().agentPresetGroups[0];
    const leaf = group.children?.[0];
    const agent = usePresetStore().agents.find((item) => item.id === leaf?.value);

    // 一级仍是职业标签；二级只有名称，不含 roletag、属性与评级
    expect(renderLabel(group)).toBe(group.label);
    expect(renderLabel(leaf)).toBe(agent?.name);
    expect(renderLabel(leaf)).not.toContain(agent?.roleTag);
    expect(renderLabel(leaf)).not.toContain(agent?.attribute);

    // 完整文案必须留在 label 上：naive-ui 渲染折叠框时直接读 rawNode.label，
    // 不经过 renderLabel，所以选中后仍显示「名称 / 职业 / 属性 / 评级」
    // （模式与角色同字时合成一段，故恒为 4 段）
    expect(leaf?.label.split(' / ')).toHaveLength(4);
    expect(leaf?.label).toBe(
      `${agent?.name} / ${agent?.roleTag} / ${agent?.attribute} / ${agent?.grade}级`,
    );

    // 未知 id 退回原 label，不渲染空白项
    expect(renderLabel({ label: '未知项', value: 'ep-does-not-exist' })).toBe('未知项');
  });

  it('cascader 上报叶子值后同步标签、写入预设并切到该代理人的面板模式', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    const agent = usePresetStore().agents.find((item) => item.roleTag === '命破');

    // 走组件自己的 onSelect，而不是绕过它直接调 store
    agentCascader(wrapper).vm.$emit('update:value', agent?.id);
    await nextTick();

    // 两个 action 顺序反了面板模式会停在 requestedMode，故此处断言真实模式
    expect(panel.agent.roleTag).toBe(agent?.roleTag);
    expect(panel.agent.presetId).toBe(agent?.id);
    expect(panel.panelMode).toBe(agent?.panelMode);
    expect(panel.core.core1).not.toBe('');
    expect(panel.agentNote.tone).toBe('neutral');
  });

  it('cascader 上报 null 走 clearable 路径，清空标签与预设并回落面板模式', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    const agent = usePresetStore().agents.find((item) => item.panelMode === 'rupture');

    panel.selectAgentRole(agent?.roleTag ?? '');
    useAgentPreset().applyAgentPreset(agent?.id ?? '');
    await nextTick();
    expect(panel.panelMode).toBe('rupture');

    panel.requestedMode = 'standard';
    agentCascader(wrapper).vm.$emit('update:value', null);
    await nextTick();

    expect(panel.agent.roleTag).toBe('');
    expect(panel.agent.presetId).toBe('');
    expect(panel.panelMode).toBe('standard');
    expect(wrapper.find('.agent-card').exists()).toBe(false);
  });

  it('选中后展示头像卡片：名称、职业与按 id 拼出的图片路径', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    const agent = usePresetStore().agents.find((item) => item.panelMode === 'standard');

    panel.selectAgentRole(agent?.roleTag ?? '');
    useAgentPreset().applyAgentPreset(agent?.id ?? '');
    await nextTick();

    const card = wrapper.get('.agent-card');
    expect(card.get('.agent-card-name').text()).toBe(agent?.name);
    // 通用模式的中文名被隐去，副信息为「职业 / 属性 / 评级」
    expect(card.get('.agent-card-meta').text()).toBe(
      `${agent?.roleTag} / ${agent?.attribute} / ${agent?.grade}级`,
    );
    // public/ 原样拷贝到 dist 根，故按 URL 取而非 import
    expect(card.get('.agent-card-avatar').attributes('src')).toBe(`/images/agents/${agent?.id}.png`);
  });

  it('通用代理人不显示「通用」二字，命破/锋御照常显示', async () => {
    const wrapper = mountView();
    const panel = usePanelStore();
    const agents = usePresetStore().agents;

    for (const mode of ['standard', 'rupture', 'fengyu'] as const) {
      const agent = agents.find((item) => item.panelMode === mode);
      if (!agent) {
        continue;
      }
      panel.selectAgentRole(agent.roleTag);
      useAgentPreset().applyAgentPreset(agent.id);
      await nextTick();

      // 三种模式的副信息都是「职业 / 属性 / 评级」三段：通用是因为模式名被隐去，
      // 命破/锋御是因为角色与模式同字被去重
      expect(wrapper.get('.agent-card-meta').text()).toBe(
        `${agent.roleTag} / ${agent.attribute} / ${agent.grade}级`,
      );
      // 面板模式本身不受影响，仍照常驱动计算
      expect(panel.panelMode).toBe(mode);
      // 整个页面（选项文案 + 卡片 + 载入提示）都看不到「通用」
      expect(wrapper.text()).not.toContain('通用');
    }
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
    panel.selectWeaponPreset(allWeapons()[0].id, (text) => text);

    panel.selectAgentRole('强攻');
    useAgentPreset().applyAgentPreset(
      usePresetStore().agents.find((agent) => agent.roleTag === '强攻')?.id ?? '',
    );

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
    const preset = allWeapons()[0];
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
