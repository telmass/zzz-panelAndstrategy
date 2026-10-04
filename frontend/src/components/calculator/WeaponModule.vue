<script setup lang="ts">
import { computed, ref } from 'vue';
import { NCascader } from 'naive-ui';

import { createCascaderRenderers } from '@/composables/useCascaderIcons';
import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
import { NumberField, PanelModule, TextField } from '@/components/common';

/**
 * 二、音擎。对应 legacy 的 `.module.weapon`。
 *
 * 与目标站 `zzzcaculator.top` 对齐：单个 cascader，一级为职业标签、二级为音擎，
 * 等级写进选项文案（不再单列筛选轴），可选中后用头像卡片展示「名称 / 职业 / 等级」。
 * 固定属性回填由 store 的 `selectWeaponPreset` 承担，语义与 legacy 的
 * `updateWeaponSelection` 一致：未命中预设时清空并重置只读回填区。
 */
const panel = usePanelStore();
const presets = usePresetStore();
const { localize } = usePanelMode();

const cascaderValue = computed<string | null>(() => panel.weapon.preset || null);

/** 头像路径。`public/` 原样拷贝到 `dist/` 根，故按 URL 取而非 import。 */
const avatarSrc = computed(() =>
  panel.selectedWeapon ? `/images/weapons/${panel.selectedWeapon.id}.png` : '',
);

/** 卡片副信息：`职业 / 等级`。 */
const metaText = computed(() => {
  const weapon = panel.selectedWeapon;
  return weapon ? `${weapon.roleTag} / ${weapon.grade}级` : '';
});

/**
 * 头像缺失时的兜底。
 *
 * 数据增长后可能出现有预设无 PNG 的音擎，此时不能显示破图——
 * 隐藏图片会让卡片只剩文字，布局不至于塌。
 */
const avatarBroken = ref(false);

function onAvatarError(): void {
  avatarBroken.value = true;
}

// 切换音擎后重置兜底，否则上一条的失败会误伤下一条
function onSelect(value: string | null): void {
  avatarBroken.value = false;
  panel.selectWeaponPreset(value ?? '', localize);
}

/* ====== 选项前缀图标与文案（与代理人选择器共用，见 useCascaderIcons） ====== */

const { renderOptionPrefix, renderOptionLabel } = createCascaderRenderers({
  leafIconDir: '/images/weapons',
  leafName: (id) => presets.weaponById.get(id)?.name,
});
</script>

<template>
  <PanelModule title="二、音擎" tag="选择音擎以自动载入固定属性" variant="weapon">
    <div class="weapon-grid">
      <div class="field weapon-picker">
        <span class="weapon-picker-label">音擎</span>
        <n-cascader
          class="weapon-picker-input"
          :options="panel.weaponPresetGroups"
          :value="cascaderValue"
          :render-prefix="renderOptionPrefix"
          :render-label="renderOptionLabel"
          filterable
          clearable
          placeholder="选择音擎"
          @update:value="onSelect"
        />
      </div>

      <!-- 选中后展示：头像 + 名称 + 职业/等级。对应目标站的 .w-engine-select-display -->
      <div v-if="panel.selectedWeapon" class="weapon-card">
        <img
          v-if="!avatarBroken"
          class="weapon-card-avatar"
          :src="avatarSrc"
          :alt="panel.selectedWeapon.name"
          loading="lazy"
          @error="onAvatarError"
        />
        <span class="weapon-card-copy">
          <span class="weapon-card-name">{{ panel.selectedWeapon.name }}</span>
          <span class="weapon-card-meta">{{ metaText }}</span>
        </span>
      </div>

      <!-- 只读回填区，由所选音擎的 baseKind 与 substat 决定 -->
      <NumberField name="weapon_base_value" :label="panel.weapon.baseLabel" :model-value="panel.weapon.baseValue" readonly />
      <TextField name="weapon_sub_type" label="固定副词条属性" :model-value="panel.weapon.subType" readonly />
      <NumberField name="weapon_sub_val" label="固定副词条数值" :model-value="panel.weapon.subValue" readonly />
    </div>
  </PanelModule>
</template>