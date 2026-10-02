<script setup lang="ts">
import { SET_OPTIONS } from '@/constants/placeholderOptions';
import { PanelModule } from '@/components/ui';

/**
 * 六、二件套效果。对应 legacy 的 `.module.set`。
 *
 * legacy 由 JS 注入 `#sets_container` 的三个 `.set-item`；此处静态渲染。
 * 组数语义（2+2+2=3 组、4+2=2 组、2+散件=1 组、全散件=0 组）
 * 在第 2 步由 `panelStore.setEffects` 的空位数量隐含表达。
 */
const SET_SLOTS = [1, 2, 3];
</script>

<template>
  <PanelModule title="六、二件套效果" tag="0~3组" variant="set">
    <p class="note note--lead">
      2+2+2=3组 · 4+2=2组 · 2+散件=1组 · 全散件=0组。每组选一种属性。
    </p>

    <!-- TODO(第 2 步)：改为 v-model="panel.setEffects.set${i}"，
         options 第 4 步改为后端下发 -->
    <div class="set-grid">
      <div v-for="index in SET_SLOTS" :key="index" class="set-item">
        <label :for="`set${index - 1}`">第{{ index }}组</label>
        <select :id="`set${index - 1}`">
          <option value="">请选择</option>
          <option v-for="opt in SET_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </div>
  </PanelModule>
</template>