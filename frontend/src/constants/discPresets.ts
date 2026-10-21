import discs from '@data/catalog/drive-discs.json';

/**
 * 驱动盘套装数据。
 *
 * **构建期静态读，不走后端接口。** 30 条静态数据、约 30 KB，与规则表
 * （`@data/rules/calculator-rules.json`）同一模式——下拉框要瞬时可用，
 * 不能等一次 HTTP 往返。走接口要动 loader / schema / 校验 / 打包 / 接口
 * 五处，对这点数据不值当。
 *
 * 数据本体是 `data/catalog/drive-discs.json`，由
 * `.github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py` 从
 * 官方 Wiki 抓取，路径登记在 `data/manifest.json`。
 */

/** 一套驱动盘。 */
export interface DiscPreset {
  /** `ep-<entry_page_id>`，与 Wiki 详情页一一对应。 */
  id: string;
  name: string;
  /** 二件套效果，Wiki 原文。 */
  setEffect2: string;
  /** 四件套效果，Wiki 原文。 */
  setEffect4: string;
  /** 套装图标，`/images/…` URL。 */
  image: string;
  /**
   * 二件套效果对应的规则表 ``setOptions`` 选项 id。
   *
   * **为 null 表示这套的 2 件套效果算不进出口面板**：
   * - 属性伤害（以太 / 冰 / 火 / 电 / 风 伤害 +10% 等）——面板**没有**
   *   「属性伤害」这一行，加一行会破坏三方对拍（参照实现的行集是固定的）；
   * - 条件触发（如「[普通攻击]造成的伤害提升15%」）——不是固定面板值。
   *
   * 这两类用 ``effect2Note`` 说明原因，UI 据此告诉用户「不计入面板」。
   */
  effect2: string | null;
  /** ``effect2`` 为 null 时的原因说明。 */
  effect2Note?: string;
}

/** 全部套装。 */
export const DISC_PRESETS = discs as DiscPreset[];

/** 按 id 查套装。 */
export const DISC_BY_ID = new Map(DISC_PRESETS.map((disc) => [disc.id, disc]));

/** 算不进出口面板的套装数（UI 提示用）。 */
export const UNCOMPUTABLE_DISC_COUNT = DISC_PRESETS.filter((disc) => !disc.effect2).length;

/**
 * 按 2 件套效果分组的套装。
 *
 * 同一效果常有多套等价套装（如「物理伤害 +10%」有獠牙重金属与沧浪行歌），
 * 「按套装选」时把它们放在一起更容易挑。
 */
export function discsByEffect(): Map<string, DiscPreset[]> {
  const groups = new Map<string, DiscPreset[]>();
  for (const disc of DISC_PRESETS) {
    if (!disc.effect2) continue;
    const list = groups.get(disc.effect2) ?? [];
    list.push(disc);
    groups.set(disc.effect2, list);
  }
  return groups;
}
