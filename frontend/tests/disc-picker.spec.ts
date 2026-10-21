import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia, type Pinia } from 'pinia';

import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

import SetEffectModule from '@/components/calculator/SetEffectModule.vue';
import { DISC_BY_ID } from '@/constants/discPresets';
import { usePanelStore } from '@/stores/panelStore';

/**
 * 模块 06 的两种填法。
 *
 * - **按效果**（默认）：每组选一个效果，行为与旧版完全一致；
 * - **按套装**：每组选一套驱动盘，自动把它的 2 件套效果写进该组。
 *
 * 关键约束：**两种填法写的都是效果 id**（`setEffects`），所以面板计算口径
 * 完全不变；按套装时额外记一份套装 id（`setDiscs`）用于显示与导出。
 */
describe('二件套的两种填法', () => {
  let pinia: Pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
  });

  function mountModule() {
    return mount(SetEffectModule, { global: { plugins: [pinia] } });
  }

  it('默认是「按效果」：三个效果下拉，没有套装下拉', () => {
    const wrapper = mountModule();

    const ids = wrapper.findAll('select').map((node) => node.attributes('id'));
    expect(ids).toEqual(['set0', 'set1', 'set2']);
    wrapper.unmount();
  });

  it('切到「按套装」后换成三个套装下拉', async () => {
    const wrapper = mountModule();

    await wrapper.findAll('.set-mode__btn')[1].trigger('click');
    await nextTick();

    const ids = wrapper.findAll('select').map((node) => node.attributes('id'));
    expect(ids).toEqual(['disc0', 'disc1', 'disc2']);
    wrapper.unmount();
  });

  it('选套装后把它的 2 件套效果写进对应组', async () => {
    const wrapper = mountModule();
    const panel = usePanelStore();
    await wrapper.findAll('.set-mode__btn')[1].trigger('click');
    await nextTick();

    const 獠牙重金属 = DISC_BY_ID.get('ep-104')!;
    expect(獠牙重金属.effect2).toBe('dmg_10');

    panel.setDisc('set1', 'ep-104');
    await nextTick();

    expect(panel.setEffects.set1).toBe('dmg_10');
    expect(panel.setDiscs.set1).toBe('ep-104');
    wrapper.unmount();
  });

  it('选算不出效果的套装：套装被记下，效果位留空', async () => {
    const wrapper = mountModule();
    const panel = usePanelStore();
    await wrapper.findAll('.set-mode__btn')[1].trigger('click');
    await nextTick();

    // 混沌重金属 = 以太伤害 +10%，面板没有「属性伤害」这一行。
    const 混沌重金属 = DISC_BY_ID.get('ep-104')!;
    expect(混沌重金属.id).toBe('ep-104');

    const attributeDisc = [...DISC_BY_ID.values()].find(
      (disc) => disc.effect2 === null && disc.effect2Note === '属性伤害',
    );
    expect(attributeDisc).toBeTruthy();

    panel.setDisc('set0', attributeDisc!.id);
    await nextTick();

    expect(panel.setEffects.set0).toBe('');
    expect(panel.setDiscs.set0).toBe(attributeDisc!.id);
    wrapper.unmount();
  });

  it('改回「按效果」时，已写入的效果仍在', async () => {
    const wrapper = mountModule();
    const panel = usePanelStore();

    await wrapper.findAll('.set-mode__btn')[1].trigger('click');
    await nextTick();
    panel.setDisc('set0', 'ep-104');
    await nextTick();

    await wrapper.findAll('.set-mode__btn')[0].trigger('click');
    await nextTick();

    expect(panel.setEffects.set0).toBe('dmg_10');
    wrapper.unmount();
  });

  it('手动改效果时清掉该组记着的套装', () => {
    const panel = usePanelStore();
    panel.setDisc('set0', 'ep-104');
    expect(panel.setDiscs.set0).toBe('ep-104');

    panel.setEffect('set0', 'cd_16');
    expect(panel.setEffects.set0).toBe('cd_16');
    expect(panel.setDiscs.set0).toBe('');
  });

  it('套装下拉的选项标出了「不计入面板」', async () => {
    const wrapper = mountModule();
    await wrapper.findAll('.set-mode__btn')[1].trigger('click');
    await nextTick();

    const labels = wrapper
      .findAll('select')
      .flatMap((node) => node.findAll('option').map((option) => option.text()));
    expect(labels.some((label) => label.includes('不计入面板'))).toBe(true);
    wrapper.unmount();
  });
});
