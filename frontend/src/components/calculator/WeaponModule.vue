<script setup lang="ts">
import { computed, h, ref } from 'vue';
import { NCascader, type CascaderOption } from 'naive-ui';

import { usePanelMode } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';
import { usePresetStore } from '@/stores/presetStore';
import { WEAPON_ROLE_TAGS } from '@/constants/calculatorOptions';
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

/* ====== 选项前缀图标（纯展示层，不参与任何数据流） ====== */

type WeaponRoleTag = (typeof WEAPON_ROLE_TAGS)[number];

/**
 * 职业标签 → roletag 图标文件名（不含扩展名）。
 *
 * 取值是官方 Wiki 的 profession key，与既有抓取脚本
 * `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py:39-47`
 * 同源，不另造一套拼音或意译——`armero`（锋御）看着费解，但改了就与脚本脱节。
 *
 * 声明为 `Record<WeaponRoleTag, string>` 而非 `Record<string, string>`：
 * 这样 `WEAPON_ROLE_TAGS` 将来扩容而此处漏配时，`vue-tsc` 会直接报错，
 * 而不是运行时静默缺图。
 */
const ROLE_ICON: Record<WeaponRoleTag, string> = {
  强攻: 'strike',
  击破: 'pierce',
  异常: 'abnormal',
  支援: 'support',
  防护: 'guard',
  命破: 'rupture',
  锋御: 'armero',
};

/**
 * 选项前缀图片路径；无法确定时返回空串。
 *
 * 以 `children` 判层级而非查表：一级项带 `children`（职业标签组），
 * 二级项是叶子（`value` 即音擎 id）。查表只用于一级项取 slug。
 *
 * 返回空串而不是拼一个可能不存在的路径：破图在浏览器里会显示成小方块图标，
 * 正是这里要避免的观感。`public/` 原样拷贝到 `dist/` 根，故按 URL 取而非 import。
 */
function optionIconSrc(option: CascaderOption): string {
  const value = typeof option.value === 'string' ? option.value : '';
  if (!value) {
    return '';
  }
  if (option.children?.length) {
    const slug = ROLE_ICON[value as WeaponRoleTag];
    return slug ? `/images/icons/${slug}.png` : '';
  }
  return `/images/weapons/${value}.png`;
}

/**
 * naive-ui 的 `render-prefix`：给每个选项渲染前缀节点。
 *
 * `option` 是 `tmNode.rawNode`，即 store 交给 cascader 的原始选项对象，
 * 故这里只读 `value` / `children` 判断层级，不新增任何字段——
 * 数据结构与 store 均不受影响。
 */
function renderOptionPrefix({ option }: { option: CascaderOption }) {
  const src = optionIconSrc(option);
  if (!src) {
    return null;
  }
  return h('img', {
    class: 'weapon-option-icon',
    src,
    // 装饰性图标，标签文字已表达含义，避免读屏重复朗读
    alt: '',
    loading: 'lazy',
    // 资源真缺时隐藏，而不是留一个破图方块
    onError: (event: Event) => {
      (event.target as HTMLImageElement).style.display = 'none';
    },
  });
}

/**
 * 菜单选项文案：浏览过程中二级项只显示武器名称。
 *
 * 完整文案「名称 / 职业 / 等级」仍留在选项的 `label` 字段上，因此
 * **选中后折叠框显示的仍是完整文案**（naive-ui 的 `Cascader.mjs:402`
 * 直接读 `rawNode.label` 渲染 `selectedOption`，不经过 `renderLabel`），
 * 选中后的头像卡片也照旧显示图标、名称与「职业 / 等级」。
 *
 * 一级项是职业标签分组，按 `children` 判定后原样返回 `label`。
 * 二级项按 `value`（音擎 id）从 `presetStore.weaponById` 取 `name`，
 * 而不切分 `label` 字符串——名称里若出现分隔符，切分会取错。
 */
function renderOptionLabel(option: CascaderOption) {
  if (option.children?.length) {
    return option.label;
  }
  const value = typeof option.value === 'string' ? option.value : '';
  return presets.weaponById.get(value)?.name ?? option.label;
}
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