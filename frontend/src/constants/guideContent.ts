/**
 * 学习指南页的内容数据——与模板解耦。
 *
 * 从 GuideView.vue 的 `<script>` 常量抽取而来；编辑指南文字/数值
 * 只需改本文件，不再触碰 Vue 模板。
 *
 * 文字与数值迁自 legacy/pages/guide.html，一字未改（包括原文的两处笔误）。
 */

import type { SideNavGroup } from '@/components/common';

/** 侧边目录。二级条目指向「六大模块详解」内各模块的小标题锚点。 */
export const NAV_GROUPS: SideNavGroup[] = [
  { id: 'overview', label: '整体结构概览' },
  {
    id: 'modules',
    label: '六大模块详解',
    sub: [
      { id: 'mod-base', label: '基础面板' },
      { id: 'mod-core', label: '核心加成' },
      { id: 'mod-weapon', label: '音擎加成' },
      { id: 'mod-drive', label: '驱动盘' },
      { id: 'mod-set', label: '2件套效果' },
    ],
  },
  { id: 'attack', label: '攻防血通用计算' },
  { id: 'crit', label: '双爆与其他属性' },
  { id: 'drive', label: '驱动盘进阶知识' },
  { id: 'summary', label: '规律与概念总结' },
];

/** 「基础面板」属性卡片。 */
export const BASE_ATTRS = [
  { label: '生命值', value: '7673' },
  { label: '攻击力', value: '888' },
  { label: '防御力', value: '612' },
  { label: '冲击力', value: '93' },
  { label: '暴击率', value: '19.4%' },
  { label: '暴击伤害', value: '50%' },
  { label: '异常掌控', value: '94' },
  { label: '异常精通', value: '93' },
  { label: '穿透率', value: '0%' },
  { label: '能量自动回复', value: '1.2' },
  { label: '增伤', value: '0%' },
  { label: '穿透值', value: '0' },
];

/** 「音擎加成」属性卡片。 */
export const WEAPON_ATTRS = [
  { label: '基础攻击力', value: '713' },
  { label: '基础防御力', value: '0' },
  { label: '副词条：暴击率', value: '24%' },
];

/** 文末「最终面板一览」卡片。 */
export const FINAL_ATTRS = [
  { label: '生命值', value: '10781.4' },
  { label: '攻击力', value: '3066' },
  { label: '防御力', value: '913' },
  { label: '暴击率', value: '72.2%' },
  { label: '暴击伤害', value: '155.6%' },
  { label: '增伤', value: '10%' },
  { label: '穿透率', value: '24%' },
  { label: '穿透值', value: '9' },
  { label: '冲击力', value: '93' },
  { label: '异常掌控', value: '94' },
  { label: '异常精通', value: '102' },
  { label: '能量自动回复', value: '1.2' },
];
