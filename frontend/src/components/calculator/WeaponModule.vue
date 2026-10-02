<script setup lang="ts">
import { PanelModule, NumberField, SelectField, TextField } from '@/components/ui';

/**
 * 二、音擎。对应 legacy 的 `.module.weapon`。
 *
 * 三级联动（等级 → 类别 → 名称）与固定属性回填在第 2 步实现，
 * 对应 legacy 的 `updateWeaponGrade` / `updateWeaponRole` / `updateWeaponSelection`。
 */
</script>

<template>
  <PanelModule title="二、音擎" tag="选择音擎以自动载入固定属性" variant="weapon">
    <div class="weapon-grid">
      <!-- TODO(第 2 步)：options 来自 weaponStore，级联清空与 disabled 联动 -->
      <SelectField name="weapon_grade" label="等级" />
      <SelectField name="weapon_role" label="类别" disabled />
      <SelectField name="weapon_preset" label="音擎名称" disabled />
      <!-- 只读回填区，第 2 步由所选音擎写入 weapon.baseLabel / baseValue / subType / subValue -->
      <NumberField name="weapon_base_value" label="基础攻击力" :model-value="0" readonly />
      <!-- 沿用 legacy 的 type="text"：该字段承载「—」等非数值占位符 -->
      <TextField name="weapon_sub_type" label="固定副词条属性" model-value="—" readonly />
      <NumberField name="weapon_sub_val" label="固定副词条数值" :model-value="0" readonly />
    </div>
  </PanelModule>
</template>