import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import type { RouteLocationNormalized } from 'vue-router';

import StrategyPickerView from '@/views/StrategyPickerView.vue';
import { strategyGuides } from '@/constants/strategyGuides';
import { useStrategyFilter } from '@/composables/useStrategyFilter';
import { scrollBehavior } from '@/router';
import { readPickerMemory, writePickerMemory } from '@/strategy/pickerMemory';

/**
 * 攻略选择页的筛选：**级别 / 属性 / 职业** + 搜索。
 *
 * 维度之间是「与」，同一维度内是「或」；级别是单选，属性与职业是多选。
 * 筛选状态写进 URL 查询串（「只看 S 级异常」可以直接把链接发出去）。
 */
function mountPicker() {
  // RouterLink 的全局桩见 tests/support/setup.ts（渲染成 <a>，保留 slot）。
  return mount(StrategyPickerView);
}

function names(wrapper: ReturnType<typeof mountPicker>): string[] {
  return wrapper.findAll('.strategy-card__name').map((node) => node.text()?.trim() ?? '');
}

describe('攻略选择页的筛选', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.history.replaceState(null, '', '/strategy');
  });

  it('默认显示全部代理人', () => {
    const wrapper = mountPicker();
    expect(names(wrapper)).toHaveLength(strategyGuides.length);
    expect(wrapper.find('.strategy-filter__count').text()).toContain(
      `显示 ${strategyGuides.length} / ${strategyGuides.length}`,
    );
  });

  it('按级别筛选（单选，点已选的取消）', () => {
    const wrapper = mountPicker();
    const sButton = wrapper.findAll('.strategy-filter__row')[0].findAll('.strategy-filter__opt')[0];
    const aButton = wrapper.findAll('.strategy-filter__row')[0].findAll('.strategy-filter__opt')[1];

    sButton.trigger('click');
    return nextTick().then(() => {
      const expected = strategyGuides.filter((guide) => guide.grade === 'S').length;
      expect(names(wrapper)).toHaveLength(expected);
      expect(names(wrapper).length).toBeGreaterThan(0);

      // 换选 A 级 → 换成另一批
      aButton.trigger('click');
      return nextTick().then(() => {
        const expectedA = strategyGuides.filter((guide) => guide.grade === 'A').length;
        expect(names(wrapper)).toHaveLength(expectedA);
      });
    });
  });

  it('按属性筛选（多选，同维度内是「或」）', async () => {
    const wrapper = mountPicker();
    const attributeRow = wrapper.findAll('.strategy-filter__row')[1];
    const buttons = attributeRow.findAll('.strategy-filter__opt');

    await buttons[0].trigger('click');
    const first = strategyGuides.filter((guide) => guide.attribute === '火').length;
    expect(names(wrapper)).toHaveLength(first);

    // 再选一个属性 → 两个属性的并集
    await buttons[3].trigger('click');
    const both = strategyGuides.filter(
      (guide) => guide.attribute === '火' || guide.attribute === '以太',
    ).length;
    expect(names(wrapper)).toHaveLength(both);
  });

  it('按职业筛选（多选）', async () => {
    const wrapper = mountPicker();
    const roleRow = wrapper.findAll('.strategy-filter__row')[2];
    await roleRow.findAll('.strategy-filter__opt')[0].trigger('click');

    const expected = strategyGuides.filter((guide) => guide.roleTag === '强攻').length;
    expect(names(wrapper)).toHaveLength(expected);
  });

  it('维度之间是「与」', async () => {
    const wrapper = mountPicker();
    const rows = wrapper.findAll('.strategy-filter__row');

    await rows[0].findAll('.strategy-filter__opt')[0].trigger('click'); // S
    await rows[1].findAll('.strategy-filter__opt')[0].trigger('click'); // 火

    const expected = strategyGuides.filter(
      (guide) => guide.grade === 'S' && guide.attribute === '火',
    ).length;
    expect(names(wrapper)).toHaveLength(expected);
  });

  it('搜索按中名 / 短名 / 英文名', async () => {
    const wrapper = mountPicker();
    const input = wrapper.find('.strategy-filter__input');

    await input.setValue('洛克茜');
    const byName = strategyGuides.filter((guide) => guide.name.includes('洛克茜')).length;
    expect(names(wrapper)).toHaveLength(byName);

    await input.setValue('roxy');
    expect(names(wrapper)).toHaveLength(
      strategyGuides.filter((guide) => guide.en.toLowerCase().includes('roxy')).length,
    );
  });

  it('筛选为空时显示空状态', async () => {
    const wrapper = mountPicker();
    await wrapper.find('.strategy-filter__input').setValue('不存在的代理人');
    expect(names(wrapper)).toHaveLength(0);
    expect(wrapper.find('.strategy-picker__empty').exists()).toBe(true);
  });

  it('重置清空全部条件', async () => {
    const wrapper = mountPicker();
    const rows = wrapper.findAll('.strategy-filter__row');
    await rows[0].findAll('.strategy-filter__opt')[0].trigger('click');
    await rows[1].findAll('.strategy-filter__opt')[0].trigger('click');
    await wrapper.find('.strategy-filter__input').setValue('洛克茜');
    expect(names(wrapper).length).toBeLessThan(strategyGuides.length);

    await wrapper.find('.strategy-filter__reset').trigger('click');
    await nextTick();
    expect(names(wrapper)).toHaveLength(strategyGuides.length);
  });

  it('筛选状态写进 URL 查询串，并能读回来', async () => {
    const { filter, toggleGrade, toggleIn } = useStrategyFilter();
    toggleGrade('S');
    toggleIn('attributes', '火');
    toggleIn('roles', '异常');
    // watcher 是异步 flush 的，等一拍再看地址栏。
    await nextTick();

    const query = new URLSearchParams(window.location.search);
    expect(query.get('grade')).toBe('S');
    expect(query.get('attr')).toBe('火');
    expect(query.get('role')).toBe('异常');
    expect(filter.value.grade).toBe('S');
  });
});

/**
 * 选择页的排序：**先按评级（S 在前、A 在后），再按 agentId 从大到小**。
 *
 * 顺序写在生成器（``tools/gen_strategy_guides.py``）里——那张表的顺序**就是**
 * 选择页的卡片顺序，前端不再二次排序（两处排序迟早会打架）。
 */
describe('选择页的排序', () => {
  it('S 级全部排在 A 级之前', () => {
    const grades = strategyGuides.map((guide) => guide.grade);
    const firstA = grades.indexOf('A');
    expect(firstA).toBeGreaterThan(0);
    expect(grades.slice(0, firstA).every((grade) => grade === 'S')).toBe(true);
    expect(grades.slice(firstA).every((grade) => grade === 'A')).toBe(true);
  });

  it('同一评级内 agentId 从大到小', () => {
    const number = (agentId: string) => Number(agentId.replace('ep-', ''));
    for (const grade of ['S', 'A']) {
      const ids = strategyGuides
        .filter((guide) => guide.grade === grade)
        .map((guide) => number(guide.agentId));
      expect(ids).toEqual([...ids].sort((a, b) => b - a));
    }
  });

  it('页面上第一张卡就是排序后的第一位', () => {
    const wrapper = mountPicker();
    const first = wrapper.find('.strategy-card__name').text()?.trim() ?? '';
    expect(first).toBe(strategyGuides[0].name);
  });
});

/**
 * **返回记忆**：从详情页回到选择页时，回到离开时的位置与筛选。
 *
 * 位置由路由的 `scrollBehavior` 归还（`savedPosition` 只覆盖浏览器的「后退」，
 * 站内「返回代理人选择」是 push 导航，得自己记）；筛选在选择页挂载时还原——
 * 列表内容变了，记下来的位置也就没有意义。
 */
describe('选择页的返回记忆', () => {
  /** 造一个只有路由名够用的假路由对象。 */
  function route(name: string): RouteLocationNormalized {
    return { name } as RouteLocationNormalized;
  }

  beforeEach(() => {
    setActivePinia(createPinia());
    window.sessionStorage.clear();
    window.history.replaceState(null, '', '/strategy');
  });

  it('记忆能写进去也能读回来', () => {
    writePickerMemory({ scrollTop: 860, query: 'grade=S&attr=火' });
    const memory = readPickerMemory();
    expect(memory?.scrollTop).toBe(860);
    expect(memory?.query).toBe('grade=S&attr=火');
  });

  it('没有记忆或记忆坏了，都当没有', () => {
    expect(readPickerMemory()).toBeNull();
    window.sessionStorage.setItem('strategyPickerMemory', '不是 JSON');
    expect(readPickerMemory()).toBeNull();
  });

  it('离开选择页时记下滚动位置与筛选', async () => {
    const wrapper = mountPicker();
    await wrapper.findAll('.strategy-filter__row')[0].findAll('.strategy-filter__opt')[0].trigger('click');
    Object.defineProperty(window, 'scrollY', { value: 420, configurable: true });

    wrapper.unmount();

    const memory = readPickerMemory();
    expect(memory?.scrollTop).toBe(420);
    expect(memory?.query).toContain('grade=S');
    delete (window as unknown as { scrollY?: number }).scrollY;
  });

  it('带着记忆回来时，列表按记住的筛选还原', () => {
    writePickerMemory({ scrollTop: 860, query: 'grade=S' });
    const wrapper = mountPicker();
    const expected = strategyGuides.filter((guide) => guide.grade === 'S').length;
    expect(names(wrapper)).toHaveLength(expected);
  });

  it('路由：从详情页回到选择页时还回记住的位置', () => {
    writePickerMemory({ scrollTop: 860, query: '' });
    expect(scrollBehavior(route('strategy-picker'), route('strategy'), null)).toEqual({ top: 860 });
  });

  it('路由：浏览器「后退」用浏览器给的位置', () => {
    writePickerMemory({ scrollTop: 860, query: '' });
    expect(scrollBehavior(route('strategy-picker'), route('strategy'), { left: 0, top: 120 })).toEqual({
      left: 0,
      top: 120,
    });
  });

  it('路由：其它导航照旧回顶部（记忆不乱用）', () => {
    writePickerMemory({ scrollTop: 860, query: '' });
    // 从启动页进选择页：不是「从详情页回来」，回顶部。
    expect(scrollBehavior(route('strategy-picker'), route('launcher'), null)).toEqual({ top: 0 });
    // 从详情页去别的页：也回顶部。
    expect(scrollBehavior(route('guide'), route('strategy'), null)).toEqual({ top: 0 });
  });
});
