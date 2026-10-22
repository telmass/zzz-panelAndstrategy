<script setup lang="ts">
import { computed } from 'vue';

import {
  FILTER_ATTRIBUTES,
  FILTER_GRADES,
  FILTER_ROLES,
  type StrategyFilterOption,
} from '@/constants/strategyGuides';
import { isFilterEmpty, type StrategyFilter } from '@/types/strategy';

/**
 * 攻略选择页的筛选栏。
 *
 * 交互学的是米游社 WIKI 的代理人列表页：一排**图标方块**当筛选按钮
 * （级别 / 属性 / 职业），配一个搜索框和「重置」。
 *
 * 图标本身带颜色（`S RANK` 橙牌、火焰红标……），所以按钮面就是图标 + 深色底
 * （与卡片左上角的徽标同一套视觉语言），选中时加一圈强调色描边——
 * 不另造一套「每个维度一个颜色」，那会多出十几个没有语义的色值。
 *
 * 级别是**单选**（点已选的取消），属性与职业是**多选**。
 */
const props = defineProps<{
  modelValue: StrategyFilter;
  total: number;
  shown: number;
}>();

const emit = defineEmits<{
  'update:modelValue': [StrategyFilter];
  'toggle-grade': [string];
  'toggle-list': ['attributes' | 'roles', string];
  'reset': [];
}>();

const grades = FILTER_GRADES;
const attributes = FILTER_ATTRIBUTES;
const roles = FILTER_ROLES;

const empty = computed(() => isFilterEmpty(props.modelValue));

function onQuery(event: Event): void {
  const query = (event.target as HTMLInputElement).value;
  emit('update:modelValue', { ...props.modelValue, query });
}

function clearQuery(): void {
  emit('update:modelValue', { ...props.modelValue, query: '' });
}

function isOn(option: StrategyFilterOption, list: 'attributes' | 'roles'): boolean {
  return props.modelValue[list].includes(option.value);
}
</script>

<template>
  <section class="strategy-filter" aria-label="代理人筛选">
    <div class="strategy-filter__search">
      <svg
        class="strategy-filter__search-icon"
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="m21 21l-4.343-4.343m0 0A8 8 0 1 0 5.343 5.343a8 8 0 0 0 11.314 11.314" />
      </svg>
      <input
        class="strategy-filter__input"
        type="search"
        :value="modelValue.query"
        placeholder="搜索代理人"
        aria-label="搜索代理人"
        @input="onQuery"
      />
      <button
        v-if="modelValue.query"
        class="strategy-filter__clear"
        type="button"
        title="清除搜索"
        aria-label="清除搜索"
        @click="clearQuery"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 15 15"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            d="M3.64 2.27L7.5 6.13l3.84-3.84A.92.92 0 0 1 12 2a1 1 0 0 1 1 1a.9.9 0 0 1-.27.66L8.84 7.5l3.89 3.89A.9.9 0 0 1 13 12a1 1 0 0 1-1 1a.92.92 0 0 1-.69-.27L7.5 8.87l-3.85 3.85A.92.92 0 0 1 3 13a1 1 0 0 1-1-1a.9.9 0 0 1 .27-.66L6.16 7.5L2.27 3.61A.9.9 0 0 1 2 3a1 1 0 0 1 1-1c.24.003.47.1.64.27"
          />
        </svg>
      </button>
    </div>

    <div class="strategy-filter__row">
      <span class="strategy-filter__label">级别</span>
      <div class="strategy-filter__opts">
        <button
          v-for="option in grades"
          :key="option.value"
          class="strategy-filter__opt"
          :class="{ 'is-on': modelValue.grade === option.value }"
          type="button"
          :aria-pressed="modelValue.grade === option.value"
          :title="option.value"
          @click="emit('toggle-grade', option.value)"
        >
          <img :src="option.icon" :alt="option.value" loading="lazy" />
        </button>
      </div>
    </div>

    <div class="strategy-filter__row">
      <span class="strategy-filter__label">属性</span>
      <div class="strategy-filter__opts">
        <button
          v-for="option in attributes"
          :key="option.value"
          class="strategy-filter__opt"
          :class="{ 'is-on': isOn(option, 'attributes') }"
          type="button"
          :aria-pressed="isOn(option, 'attributes')"
          :title="option.value"
          @click="emit('toggle-list', 'attributes', option.value)"
        >
          <img :src="option.icon" :alt="option.value" loading="lazy" />
        </button>
      </div>
    </div>

    <div class="strategy-filter__row">
      <span class="strategy-filter__label">职业</span>
      <div class="strategy-filter__opts">
        <button
          v-for="option in roles"
          :key="option.value"
          class="strategy-filter__opt"
          :class="{ 'is-on': isOn(option, 'roles') }"
          type="button"
          :aria-pressed="isOn(option, 'roles')"
          :title="option.value"
          @click="emit('toggle-list', 'roles', option.value)"
        >
          <img :src="option.icon" :alt="option.value" loading="lazy" />
        </button>
      </div>
    </div>

    <div class="strategy-filter__foot">
      <span class="strategy-filter__count">显示 {{ shown }} / {{ total }}</span>
      <button
        class="strategy-filter__reset"
        type="button"
        :disabled="empty"
        @click="emit('reset')"
      >
        重置
      </button>
    </div>
  </section>
</template>
