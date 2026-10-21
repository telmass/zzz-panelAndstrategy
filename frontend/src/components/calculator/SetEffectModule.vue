<script setup lang="ts">
import { computed } from 'vue';

import { SET_OPTIONS } from '@/constants/calculatorOptions';
import { DISC_BY_ID, DISC_PRESETS, discsByEffect } from '@/constants/discPresets';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { PanelModule, SelectField } from '@/components/common';
import type { SetSlot } from '@/types/panel';

/**
 * 模块 06 · 二件套效果。对应 legacy 的 `.module.set`。
 *
 * 组数语义（2+2+2=3 组、4+2=2 组、2+散件=1 组、全散件=0 组）
 * 由三组下拉的留空数量隐含表达——留空即未组成一组。
 *
 * **两种填法**（同一批槽位）：
 *
 * - **按效果**（默认，行为与旧版完全一致）：每组选一个**效果**。用户可能只知道
 *   「我要 +16% 暴击伤害」而不知道哪套能给。
 * - **按套装**：每组选一套**驱动盘**，选中后自动把它的 2 件套效果写进该组。
 *   用户按套装想（他身上穿着的就是某套），还能看到套装图标与 4 件套效果文本。
 *
 * 两种填法写的都是**效果 id**（`setEffects`），所以**面板计算口径完全不变**；
 * 按套装时额外记一份套装 id（`setDiscs`）用于显示与导出。
 *
 * 使用共享 `SelectField` 组件（与其他下拉模块一致的样式与行为）。
 */
const panel = usePanelStore();
const { localize } = usePanelMode();

/** 二件套选项含「能量回复 +20%」，锋御模式需替换为锐能文案。 */
const options = computed(() =>
  SET_OPTIONS.map((option) => ({ value: option.id, label: localize(option.label) })),
);

/**
 * 套装选项。
 *
 * 按 2 件套效果分组排序（同一效果的多套等价套装放在一起，如「物理伤害 +10%」
 * 有獠牙重金属与沧浪行歌），算不出效果的套装排在最后。
 */
const discOptions = computed(() => {
  const groups = discsByEffect();
  const ordered: string[] = [];
  for (const list of groups.values()) {
    for (const disc of list) {
      ordered.push(disc.id);
    }
  }
  const rest = DISC_PRESETS.filter((disc) => !disc.effect2).map((disc) => disc.id);
  return [...ordered, ...rest].map((id) => {
    const disc = DISC_BY_ID.get(id)!;
    return {
      value: disc.id,
      label: disc.effect2
        ? `${disc.name} · ${disc.setEffect2}`
        : `${disc.name} · ${disc.setEffect2}（不计入面板：${disc.effect2Note ?? '该效果未建模'}）`,
    };
  });
});

const SLOTS = [
  { key: 'set0' as SetSlot, index: 1 },
  { key: 'set1' as SetSlot, index: 2 },
  { key: 'set2' as SetSlot, index: 3 },
];

/** 每组当前选中的套装。 */
function discOf(slot: SetSlot) {
  const id = panel.setDiscs[slot];
  return id ? (DISC_BY_ID.get(id) ?? null) : null;
}
</script>

<template>
  <PanelModule title="二件套效果" tag="0~3组" variant="set" index="06">
    <p class="note note--lead">
      2+2+2=3组 · 4+2=2组 · 2+散件=1组 · 全散件=0组。每组选一种属性。
    </p>

    <div class="set-mode" role="group" aria-label="二件套填法">
      <button
        class="set-mode__btn"
        :class="{ 'is-active': panel.setPickMode === 'effect' }"
        type="button"
        :aria-pressed="panel.setPickMode === 'effect'"
        @click="panel.setPickMode = 'effect'"
      >
        按效果
      </button>
      <button
        class="set-mode__btn"
        :class="{ 'is-active': panel.setPickMode === 'disc' }"
        type="button"
        :aria-pressed="panel.setPickMode === 'disc'"
        @click="panel.setPickMode = 'disc'"
      >
        按套装
      </button>
    </div>

    <div class="set-grid">
      <div v-for="slot in SLOTS" :key="slot.key" class="set-item">
        <SelectField
          v-if="panel.setPickMode === 'effect'"
          :name="`set${slot.index - 1}`"
          :label="`第${slot.index}组`"
          :options="options"
          :model-value="panel.setEffects[slot.key]"
          @update:model-value="panel.setEffect(slot.key, $event)"
        />
        <SelectField
          v-else
          :name="`disc${slot.index - 1}`"
          :label="`第${slot.index}组`"
          :options="discOptions"
          :model-value="panel.setDiscs[slot.key]"
          @update:model-value="panel.setDisc(slot.key, $event)"
        />
        <p
          v-if="panel.setPickMode === 'disc' && discOf(slot.key)"
          class="set-item__disc"
          :title="discOf(slot.key)?.setEffect4"
        >
          <img
            v-if="discOf(slot.key)?.image"
            class="set-item__disc-icon"
            :src="discOf(slot.key)?.image"
            :alt="`${discOf(slot.key)?.name}图标`"
            loading="lazy"
            onerror="this.style.display = 'none'"
          />
          <span class="set-item__disc-name">{{ discOf(slot.key)?.name }}</span>
          <span v-if="!discOf(slot.key)?.effect2" class="set-item__disc-note">
            {{ discOf(slot.key)?.effect2Note }}
          </span>
        </p>
      </div>
    </div>
  </PanelModule>
</template>
