<script setup lang="ts">
import { CORE_OPTIONS } from '@/constants/placeholderOptions';
import { PanelModule, SelectField } from '@/components/ui';

/**
 * 三、核心加成。对应 legacy 的 `.module.core`。
 *
 * 9 选 2 且可重复的互斥校验在第 2 步实现；
 * 选项列表第 4 步改由 `GET /api/presets/core` 下发。
 */
</script>

<template>
  <PanelModule title="三、核心加成" tag="9选2 · 可重复选" variant="core">
    <p class="note note--lead">
      从8项中选2项，可重复（如两次暴击率=28.8%）。<br />核心互斥：同一属性不会同时给基础值与百分比。
    </p>

    <div class="grid-2">
      <!-- TODO(第 2 步)：改为 v-model="panel.core.core1" / "core2" -->
      <SelectField name="core1" label="核心选择 ①" :options="CORE_OPTIONS" />
      <SelectField name="core2" label="核心选择 ②" :options="CORE_OPTIONS" />
    </div>

    <!-- TODO(第 2 步)：由 coreLabels 派生，输出「已选：…」或未选择警示 -->
    <p class="note" />
  </PanelModule>
</template>