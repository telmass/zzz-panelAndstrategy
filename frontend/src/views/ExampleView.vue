<script setup lang="ts">
import { onMounted } from 'vue';

import {
  AgentBaseModule,
  CoreModule,
  DiscMainModule,
  DiscSubModule,
  ResultPanel,
  SetEffectModule,
  WeaponModule,
} from '@/components/calculator';
import { BackToLauncher } from '@/components/layout';
import { SUB_STATS } from '@/constants/calculatorOptions';
import { usePanelStore } from '@/stores/panelStore';
import type { BaseStats } from '@/types/panel';

/**
 * 面板计算器（标准版）示例页。迁自 legacy/pages/example-template.html
 * （迁移第 5 步第 21 条），是该页在 Vue 侧的对应物。
 *
 * 与统一计算器（`/calculator`）的分工：
 *   - 统一计算器由代理人预设驱动面板模式，支持命破 / 锋御；
 *   - 本页是「标准版」示例，不选代理人、不切模式，打开即是一组填好的示例值，
 *     另配「重置为示例值」按钮。
 *
 * 因此本页**不再自带一份计算逻辑与选项表**——legacy 原文在 `<script>` 里
 * 复制了 CORE_OPTIONS / SUB_STATS / SET_OPTIONS 等表和一份 calc()，
 * 与统一计算器重复。统一后改为复用同一套模块与后端接口
 * （`usePanelCalc` → `POST /api/panel/calc`），选项仍来自 `@data/options.json`。
 *
 * 一处无法照搬的差异：legacy 示例的音擎是自由输入（基础攻击 500 + 生命% 30），
 * 而统一计算器的音擎由预设驱动（`buildRequest` 只在 `weapon.preset` 有值时
 * 才带上音擎加成），没有「手填音擎」这条路径。故示例值里音擎留空，
 * 其余模块（基础面板 / 核心 / 4-6号 / 副词条 / 二件套）逐项照搬。
 */

/** 示例基础面板。数值与 legacy `example-template.html` 的 input 默认值一致。 */
const EXAMPLE_BASE: BaseStats = {
  hp: 8000,
  atk: 1000,
  def: 600,
  impact: 0,
  cr: 5,
  cd: 50,
  ac: 0,
  am: 0,
  pr: 0,
  er: 0,
  penforce: 0,
  energyAccumulation: 0,
};

/**
 * 示例选择。id 取自 `data/options.json`，对应 legacy 里按下标选中的同一项：
 * 核心①=暴击率14.4%(index 4)、核心②=基础攻击75(index 1)；
 * 4号=暴击率24%(index 3)、5号=增伤30%(index 4)、6号=能量回复60%(index 5)；
 * 第1组=暴击率+8%(index 3)、第2组=增伤+10%(index 7)。
 */
const EXAMPLE_CORE = { core1: 'cr', core2: 'atk_base' };
const EXAMPLE_DISC = { disc4: 'cr_24', disc5: 'dmg_30', disc6: 'er_pct_60' };
const EXAMPLE_SETS = { set0: 'cr_8', set1: 'dmg_10', set2: '' };

/** 副词条条数。legacy 示例为「暴击率×6、暴伤×6」。 */
const EXAMPLE_SUBSTAT_COUNTS: Record<string, number> = { cr: 6, cd: 6 };

const panel = usePanelStore();

/** 把整页恢复为 legacy 示例值。挂在「重置为示例值」按钮上。 */
function applyExample(): void {
  panel.setPanelMode('standard');
  panel.requestedMode = 'standard';
  panel.base = { ...EXAMPLE_BASE };
  panel.core = { ...EXAMPLE_CORE };
  panel.discMain = { ...EXAMPLE_DISC };
  panel.setEffects = { ...EXAMPLE_SETS };
  panel.subStats = Object.fromEntries(
    SUB_STATS.map((stat) => [stat.id, EXAMPLE_SUBSTAT_COUNTS[stat.id] ?? 0]),
  );
  panel.resetWeaponSelection();
}

onMounted(applyExample);
</script>

<template>
  <BackToLauncher />

  <div class="container page-with-back">
    <h1>面板计算器（标准版）</h1>
    <p class="subtitle">
      基于《面板计算方式学习指南》· 8选2核心（可重复）/ 6盘主副词条 / 0~3组2件套 · 攻防血先乘后加，其余纯加法
    </p>

    <div class="layout">
      <div class="left">
        <AgentBaseModule />
        <WeaponModule />
        <CoreModule />
        <DiscMainModule />
        <DiscSubModule />
        <SetEffectModule />
      </div>

      <ResultPanel>
        <button class="reset-btn" type="button" @click="applyExample">重置为示例值</button>
      </ResultPanel>
    </div>
  </div>
</template>
