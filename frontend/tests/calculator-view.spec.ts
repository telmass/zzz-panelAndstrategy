import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { mount, type VueWrapper } from '@vue/test-utils';

import router from '@/router';
import CalculatorView from '@/views/CalculatorView.vue';
import ExampleView from '@/views/ExampleView.vue';
import GuideView from '@/views/GuideView.vue';
import LauncherView from '@/views/LauncherView.vue';
import { usePanelStore } from '@/stores/panelStore';
import { loadPresets, mockApi } from './support/api';
import { flushCalc } from './support/flush';

/**
 * 组件树与测试断言必须共用同一个 pinia 实例：
 * mount 时另建 createPinia() 会让组件读到另一份 store，
 * usePanelStore() 的写入也就不会反映到已挂载的 DOM 上。
 */
let pinia: Pinia;

beforeEach(async () => {
  pinia = createPinia();
  setActivePinia(pinia);
  // 第 3 步起结果来自后端；这里用假后端保证渲染路径可跑通。
  // 数值本身的正确性由 legacy-parity.spec.ts 与后端测试负责。
  mockApi();
  // 第 4 步起预设也来自接口，生产的 main.ts 在 mount 前装载，测试同理。
  await loadPresets();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function mountCalculator(): VueWrapper {
  // RouterLink 桩由 tests/support/setup.ts 全局注入，各 spec 无需再声明 stubs
  return mount(CalculatorView, { global: { plugins: [pinia] } });
}

/** 指南页与示例页不需要 pinia，但统一放这里便于各 describe 复用。 */
function mountGuide(): VueWrapper {
  return mount(GuideView);
}

function mountExample(): VueWrapper {
  return mount(ExampleView, { global: { plugins: [pinia] } });
}

/* ====== 取值助手：vue-tsc 不接受 VueNode<Element> 上的表单属性 ====== */

function input(wrapper: VueWrapper, selector: string): HTMLInputElement {
  return wrapper.get(selector).element as HTMLInputElement;
}

function select(wrapper: VueWrapper, selector: string): HTMLSelectElement {
  return wrapper.get(selector).element as HTMLSelectElement;
}

/** 表单控件所在的外层 `.field`，用于断言整块显隐。 */
function fieldOf(wrapper: VueWrapper, id: string): HTMLElement {
  const field = input(wrapper, `#${id}`).parentElement;
  if (!field) {
    throw new Error(`#${id} 不在任何 .field 内，组件结构已变更`);
  }
  return field;
}

describe('CalculatorView 静态骨架', () => {
  it('渲染六大模块，顺序与标题同 legacy', () => {
    const wrapper = mountCalculator();
    const titles = wrapper.findAll('.module-title');
    expect(titles).toHaveLength(6);
    expect(titles.map((node) => node.find('span').text())).toEqual([
      '一、基础面板',
      '二、音擎',
      '三、核心加成',
      '四、驱动盘主词条',
      '五、驱动盘副词条',
      '六、二件套效果',
    ]);
    expect(titles.map((node) => node.find('.tag').text())).toEqual([
      '角色本体',
      '选择音擎以自动载入固定属性',
      '9选2 · 可重复选',
      '1~3固定 · 4/5/6可选',
      '每盘9条 · 6盘共54条',
      '0~3组',
    ]);
  });

  it('每个模块带对应的左侧色条变体', () => {
    const wrapper = mountCalculator();
    const variants = wrapper.findAll('.module').map((node) => node.classes().join(' '));
    ['base', 'weapon', 'core', 'disc', 'sub', 'set'].forEach((variant, index) => {
      expect(variants[index]).toContain(`module--${variant}`);
    });
  });

  it('基础面板含 12 个字段，命破专属字段默认隐藏', () => {
    const wrapper = mountCalculator();
    expect(wrapper.findAll('.base-grid .field')).toHaveLength(12);

    expect(input(wrapper, '#base_hp').value).toBe('8000');
    expect(input(wrapper, '#base_atk').value).toBe('1000');
    expect(input(wrapper, '#base_er').value).toBe('1.2');

    expect(fieldOf(wrapper, 'base_penforce').hidden).toBe(true);
    expect(fieldOf(wrapper, 'base_energy_accumulation').hidden).toBe(true);
    expect(fieldOf(wrapper, 'base_pr').hidden).toBe(false);
  });

  it('音擎三个下拉与三个只读回填字段齐备', () => {
    const wrapper = mountCalculator();
    expect(select(wrapper, '#weapon_grade').disabled).toBe(false);
    expect(select(wrapper, '#weapon_role').disabled).toBe(true);
    expect(select(wrapper, '#weapon_preset').disabled).toBe(true);
    expect(input(wrapper, '#weapon_sub_type').value).toBe('—');
    expect(input(wrapper, '#weapon_base_value').readOnly).toBe(true);
  });

  it('核心加成两个下拉均提供 12 项', () => {
    const wrapper = mountCalculator();
    for (const id of ['core1', 'core2']) {
      // 1 项占位「请选择」+ 12 项核心
      expect(wrapper.find(`#${id}`).findAll('option')).toHaveLength(13);
    }
  });

  it('驱动盘主词条：3 个固定徽标 + 3 个下拉', () => {
    const wrapper = mountCalculator();
    const fixed = wrapper.findAll('.fixed-stat').map((node) => node.text().replace(/\s+/g, ' ').trim());
    expect(fixed).toEqual(['1号 固定生命 +2200', '2号 固定攻击 +316', '3号 固定防御 +184']);

    expect(wrapper.find('#disc4').findAll('option')).toHaveLength(7);
    expect(wrapper.find('#disc5').findAll('option')).toHaveLength(6);
    expect(wrapper.find('#disc6').findAll('option')).toHaveLength(7);
  });

  it('副词条渲染 10 项步进器且按钮初始禁用', () => {
    const wrapper = mountCalculator();
    const steppers = wrapper.findAll('.sub-count');
    expect(steppers).toHaveLength(10);

    // 副词条用 `.sub-grid`（2 列），累加值要留在步进器同一行，列宽不能像 `.grid-4` 那样只有 172.5px
    const labels = wrapper.findAll('.sub-grid .field > label').map((node) => node.text().trim());
    expect(labels).toEqual([
      '小生命 +112/条',
      '大生命% +3%/条',
      '小攻击 +19/条',
      '大攻击% +3%/条',
      '小防御 +15/条',
      '大防御% +4.8%/条',
      '暴击率 +2.4%/条',
      '暴击伤害 +4.8%/条',
      '穿透值 +9/条',
      '异常精通 +9/条',
    ]);

    // 条数为 0：减号不可用，加号可用（合计 0 < 54）
    const buttons = wrapper.findAll('.sub-count-btn');
    buttons.forEach((button, index) => {
      const isDecrement = index % 2 === 0;
      expect((button.element as HTMLButtonElement).disabled).toBe(isDecrement);
    });
    expect(wrapper.text()).toContain('副词条总数：0 / 54');
  });

  it('二件套渲染 3 组下拉', () => {
    const wrapper = mountCalculator();
    for (const id of ['set0', 'set1', 'set2']) {
      // 1 项占位 + 10 种二件套
      expect(wrapper.find(`#${id}`).findAll('option')).toHaveLength(11);
    }
  });

  it('standard 模式只显示 12 行通用结果', async () => {
    const wrapper = mountCalculator();
    const labels = wrapper.findAll('.r-label').map((node) => node.text());
    expect(labels).toEqual([
      '生命值',
      '攻击力',
      '防御力',
      '暴击率',
      '暴击伤害',
      '增伤',
      '穿透率',
      '穿透值',
      '异常精通',
      '异常掌控',
      '冲击力',
      '能量回复',
    ]);

    // 第 3 步起数值来自后端，需等过防抖 + HTTP 才有内容。
    // 假后端返回生命值 10,200（= 8000 + 驱动盘 1 号固定 2200）。
    await flushCalc();
    expect(wrapper.find('.r-value').text()).toBe('10,200');
    expect(wrapper.findAll('.r-value').every((node) => node.text() !== '—')).toBe(true);
    // 明细不再是空片段
    expect(wrapper.find('.breakdown').html()).toContain('1号主词条');
  });

  it('命破模式追加贯穿力行', () => {
    const panel = usePanelStore();
    panel.panelMode = 'rupture';
    const wrapper = mountCalculator();
    const labels = wrapper.findAll('.r-label').map((node) => node.text());
    expect(labels).toContain('贯穿力');
    expect(labels).not.toContain('实际暴击率');
    expect(labels).toHaveLength(13);
  });

  it('锋御模式追加实际暴击率与锐暴伤害行', () => {
    const panel = usePanelStore();
    panel.panelMode = 'fengyu';
    const wrapper = mountCalculator();
    const labels = wrapper.findAll('.r-label').map((node) => node.text());
    expect(labels).toContain('实际暴击率');
    expect(labels).toContain('锐暴伤害');
    expect(labels).not.toContain('贯穿力');
    expect(labels).toHaveLength(14);
  });
});

describe('LauncherView 静态骨架', () => {
  function mountLauncher() {
    return mount(LauncherView);
  }

  it('保留 eyebrow 与主标题', () => {
    const wrapper = mountLauncher();
    expect(wrapper.find('.eyebrow').text()).toBe('ZENLESS ZONE ZERO · PANEL TOOLS');
    expect(wrapper.find('h1').text()).toBe('代理人面板计算器');
  });

  it('提供计算器、指南与示例三个入口，共用同一套卡片样式', () => {
    const wrapper = mountLauncher();
    const cards = wrapper.findAll('.card');
    expect(cards).toHaveLength(3);
    // 三个入口同源，不加区分色，视觉必然一致
    expect(cards[1].classes()).toEqual(cards[2].classes());
    expect(wrapper.findAll('.badge').map((node) => node.text())).toEqual([
      '统一计算器',
      '学习指南',
      '标准版示例',
    ]);
  });

  it('三张卡片分别指向 /calculator、/guide 与 /example', () => {
    const wrapper = mountLauncher();
    expect(wrapper.findAll('a').map((node) => node.attributes('href'))).toEqual([
      '/calculator',
      '/guide',
      '/example',
    ]);
  });

  it('计算器卡片保留两条公式说明', () => {
    const wrapper = mountLauncher();
    const formula = wrapper.find('.formula').text();
    expect(formula).toContain('命破：贯穿力 = 0.3 × 最终攻击力 + 0.1 × 最终生命值');
    expect(formula).toContain('锋御：实际暴击率 = 最终暴击伤害 × 35% + 原最终暴击率');
  });

  it('启动页本身不放返回按钮', () => {
    expect(mountLauncher().find('.back-link').exists()).toBe(false);
  });
});

describe('子页面返回导航', () => {
  it('计算器页左上角有指向 / 的返回按钮', () => {
    const back = mountCalculator().get('.back-link');
    expect(back.attributes('href')).toBe('/');
    expect(back.text()).toContain('返回主页');
  });

  it('指南页左上角有指向 / 的返回按钮', () => {
    const back = mountGuide().get('.back-link');
    expect(back.attributes('href')).toBe('/');
    expect(back.text()).toContain('返回主页');
  });

  it('返回按钮复用 .btn，与步进器按钮同一套视觉', () => {
    expect(mountGuide().get('.back-link').classes()).toContain('btn');
  });

  it('挂了返回按钮的页面用 .page-with-back 让出顶部空间', () => {
    expect(mountCalculator().find('.page-with-back').exists()).toBe(true);
    expect(mountGuide().find('.page-with-back').exists()).toBe(true);
    expect(mountExample().find('.page-with-back').exists()).toBe(true);
  });

  it('三个子页面都只有返回主页这一个链接，不留死链', () => {
    for (const wrapper of [mountCalculator(), mountGuide(), mountExample()]) {
      expect(wrapper.findAll('a').map((node) => node.attributes('href'))).toEqual(['/']);
    }
  });

  it('四条路由均有对应视图', () => {
    expect(router.getRoutes().map((route) => route.path).sort()).toEqual([
      '/',
      '/calculator',
      '/example',
      '/guide',
    ]);
  });
});

describe('GuideView 吸收 legacy guide.html', () => {
  it('六个章节齐全且带锚点', () => {
    const ids = mountGuide().findAll('h2').map((node) => node.attributes('id'));
    expect(ids).toEqual(['overview', 'modules', 'attack', 'crit', 'drive', 'summary']);
  });

  it('保留 30 秒快速理解的四条要点', () => {
    expect(mountGuide().findAll('.guide-quick li')).toHaveLength(4);
  });

  it('核心加成的 8 项加成表逐行保留', () => {
    const rows = mountGuide().findAll('.guide-card table');
    // 基础面板来源 3 行 + 核心 8 行 + 其余表，核心表按表头文案定位
    const coreTable = rows.find((table) => table.findAll('th').map((th) => th.text()).includes('归属'));
    expect(coreTable?.findAll('tbody tr')).toHaveLength(8);
  });

  it('关键公式与结论文案未丢失', () => {
    const text = mountGuide().text();
    expect(text).toContain('最终属性 = ( 基础总值 ) × ( 1 + 所有百分比加成 ) + 所有固定值加成');
    expect(text).toContain('3064.75');
    expect(text).toContain('先乘后加6种');
  });

  it('复用四个展示组件而不是散落的内联样式', () => {
    const wrapper = mountGuide();
    expect(wrapper.findAll('.guide-callout').length).toBeGreaterThan(10);
    expect(wrapper.findAll('.guide-table').length).toBeGreaterThan(10);
    expect(wrapper.findAll('.guide-attrs').length).toBeGreaterThanOrEqual(3);
  });
});

describe('ExampleView 吸收 legacy example-template.html', () => {
  it('复用统一计算器的六大模块与结果区，不自带第二套实现', () => {
    const wrapper = mountExample();
    expect(wrapper.findAll('.module').length).toBeGreaterThanOrEqual(6);
    expect(wrapper.find('.result-module').exists()).toBe(true);
  });

  it('挂载后预填 legacy 示例值', () => {
    const panel = usePanelStore();
    mountExample();
    expect(panel.base).toMatchObject({ hp: 8000, atk: 1000, def: 600, cr: 5, cd: 50 });
    expect(panel.core).toEqual({ core1: 'cr', core2: 'atk_base' });
    expect(panel.discMain).toEqual({ disc4: 'cr_24', disc5: 'dmg_30', disc6: 'er_pct_60' });
    expect(panel.setEffects).toEqual({ set0: 'cr_8', set1: 'dmg_10', set2: '' });
    expect(panel.subStats.cr).toBe(6);
    expect(panel.subStats.cd).toBe(6);
    expect(panel.subStats.atk_flat).toBe(0);
  });

  it('示例页固定为标准模式，不受命破 / 锋御影响', () => {
    const panel = usePanelStore();
    panel.setPanelMode('rupture');
    mountExample();
    expect(panel.panelMode).toBe('standard');
  });

  it('重置按钮把改过的字段恢复成示例值', async () => {
    const panel = usePanelStore();
    const wrapper = mountExample();
    panel.base.hp = 1;
    panel.subStats.cr = 0;
    await wrapper.get('.reset-btn').trigger('click');
    expect(panel.base.hp).toBe(8000);
    expect(panel.subStats.cr).toBe(6);
  });
});