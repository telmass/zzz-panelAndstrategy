<script setup lang="ts">
import { DISC4_OPTIONS, DISC5_OPTIONS, DISC6_OPTIONS, DISC_FIXED_STATS } from '@/constants/placeholderOptions';
import { PanelModule, SelectField } from '@/components/ui';

/**
 * 四、驱动盘主词条。对应 legacy 的 `.module.disc`。
 *
 * 1/2/3 号固定主词条当前为前端常量，第 3 步下沉到 `core/constants.py`
 * 后改为由后端下发，与 `panel.py` 的计算口径保持同源。
 */

/** 4/5/6 号沿用 legacy 的四格不换行空格缩进，使其与上方徽标对齐。 */
const INDENT = '\u00a0\u00a0\u00a0\u00a0';
const SLOTS = [
  { name: 'disc4', label: `${INDENT}4号`, unit: '6选1', options: DISC4_OPTIONS },
  { name: 'disc5', label: `${INDENT}5号`, unit: '5选1', options: DISC5_OPTIONS },
  { name: 'disc6', label: `${INDENT}6号`, unit: '6选1', options: DISC6_OPTIONS },
];
</script>

<template>
  <PanelModule title="四、驱动盘主词条" tag="1~3固定 · 4/5/6可选" variant="disc">
    <div class="disc-main-grid" style="margin-bottom: 10px">
      <div v-for="stat in DISC_FIXED_STATS" :key="stat.slot" class="fixed-stat">
        {{ stat.slot }}号 {{ stat.label }} <span class="v">+{{ stat.value }}</span>
      </div>
    </div>

    <div class="disc-main-grid">
      <!-- TODO(第 2 步)：改为 v-model="panel.discMain.disc4/5/6" -->
      <SelectField
        v-for="slot in SLOTS"
        :key="slot.name"
        :name="slot.name"
        :label="slot.label"
        :label-unit="slot.unit"
        :options="slot.options"
      />
    </div>
  </PanelModule>
</template>