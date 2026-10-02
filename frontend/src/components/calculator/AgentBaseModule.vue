<script setup lang="ts">
import { PanelModule, NumberField, SelectField } from '@/components/ui';

/**
 * 一、基础面板。对应 legacy 的 `.module.base`。
 *
 * 面板模式相关的显隐（`pr` / `er` / `penforce` / `energyAccumulation`）
 * 与锋御文案替换在第 2 步由 `usePanelMode` 驱动，此处先按 standard 模式
 * 给出与 legacy 一致的初始显隐状态。
 */
</script>

<template>
  <PanelModule title="一、基础面板" tag="角色本体" variant="base">
    <p class="note note--lead">
      填写角色纯基础面板（不含核心）。若游戏内显示已含核心基础值，请先减去再填。
    </p>

    <!-- TODO(第 2 步)：options 由 agentStore 拉取，agent_preset 的 disabled
         随 agent_role 联动 -->
    <div class="agent-selector-grid" style="margin-bottom: 8px">
      <SelectField name="agent_role" label="代理人标签" />
      <SelectField
        name="agent_preset"
        label="代理人名称"
        placeholder="请先选择标签"
        disabled
      />
    </div>

    <!-- TODO(第 2 步)：文案由 applyAgentPreset 依据预设的 unmodeledBaseStats
         与 additionalBaseStats 生成，此处先固定展示 legacy 的默认提示 -->
    <p class="note note--lead">
      选择预设会填入基础面板和核心加成；音擎与驱动盘配装默认留空，固定的1/2/3号盘主词条除外。
    </p>

    <div class="base-grid">
      <NumberField name="base_hp" label="生命值" :model-value="8000" />
      <NumberField name="base_atk" label="攻击力" :model-value="1000" />
      <NumberField name="base_def" label="防御力" :model-value="600" />
      <NumberField name="base_impact" label="冲击力" :model-value="90" />
      <NumberField name="base_cr" label="暴击率" unit="%" :model-value="5" />
      <NumberField name="base_cd" label="暴击伤害" unit="%" :model-value="50" />
      <NumberField name="base_ac" label="异常掌控" :model-value="100" />
      <NumberField name="base_am" label="异常精通" :model-value="100" />
      <NumberField name="base_pr" label="穿透率" unit="%" :model-value="0" />
      <!-- 命破专属，第 2 步按 panelMode === 'rupture' 显示 -->
      <NumberField name="base_penforce" label="基础贯穿力" :model-value="0" hidden />
      <NumberField name="base_er" label="能量自动回复" :model-value="1.2" />
      <!-- 命破专属，第 2 步按 panelMode === 'rupture' 显示 -->
      <NumberField name="base_energy_accumulation" label="闪能自动累积" :model-value="0" hidden />
    </div>
  </PanelModule>
</template>