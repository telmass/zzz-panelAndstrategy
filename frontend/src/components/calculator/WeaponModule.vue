<script setup lang="ts">
import { computed } from 'vue';

import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { NumberField, PanelModule, SelectField, TextField } from '@/components/common';

/**
 * 二、音擎。对应 legacy 的 `.module.weapon`。
 *
 * 三级联动（等级 → 类别 → 名称）与固定属性回填由 store 的
 * `selectWeaponGrade` / `selectWeaponRole` / `selectWeaponPreset` 承担，
 * 语义与 legacy 的 `updateWeaponGrade` / `updateWeaponRole` /
 * `updateWeaponSelection` 完全一致：每次上游变更都清空下游并重置只读回填区。
 */
const panel = usePanelStore();
const { localize } = usePanelMode();

/** 等级选项文案带「级」后缀，与 legacy 的 `${grade}级` 一致。 */
const gradeOptions = computed(() =>
  panel.weaponGradeOptions.map((grade) => ({ value: grade, label: `${grade}级` })),
);

const roleOptions = computed(() =>
  panel.weaponRoleOptions.map((role) => ({ value: role, label: role })),
);

const presetOptions = computed(() =>
  panel.filteredWeaponPresets.map((weapon) => ({ value: weapon.id, label: weapon.name })),
);
</script>

<template>
  <PanelModule title="二、音擎" tag="选择音擎以自动载入固定属性" variant="weapon">
    <div class="weapon-grid">
      <SelectField
        name="weapon_grade"
        label="等级"
        :model-value="panel.weapon.grade"
        :options="gradeOptions"
        @update:model-value="panel.selectWeaponGrade($event)"
      />
      <SelectField
        name="weapon_role"
        label="类别"
        :model-value="panel.weapon.roleTag"
        :options="roleOptions"
        :disabled="!panel.weapon.grade"
        @update:model-value="panel.selectWeaponRole($event)"
      />
      <SelectField
        name="weapon_preset"
        label="音擎名称"
        :model-value="panel.weapon.preset"
        :options="presetOptions"
        :disabled="!panel.weapon.grade || !panel.weapon.roleTag"
        @update:model-value="panel.selectWeaponPreset($event, localize)"
      />

      <!-- 只读回填区，由所选音擎的 baseKind 与 substat 决定 -->
      <NumberField name="weapon_base_value" :label="panel.weapon.baseLabel" :model-value="panel.weapon.baseValue" readonly />
      <TextField name="weapon_sub_type" label="固定副词条属性" :model-value="panel.weapon.subType" readonly />
      <NumberField name="weapon_sub_val" label="固定副词条数值" :model-value="panel.weapon.subValue" readonly />
    </div>
  </PanelModule>
</template>