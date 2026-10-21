import type {
  CoreSelection,
  DiscMainStats,
  PanelMode,
  SetDiscs,
  SetEffects,
  SubStatCounts,
} from '@/types/panel';

/**
 * 配装方案（build preset）。
 *
 * **本地数据，不进仓库的 `data/`。** 它是「某个用户自己的一套配装」，不是
 * 游戏的事实数据；仓库里只存游戏事实（代理人 / 音擎 / 套装 / 规则表）。
 *
 * 存在哪：
 *
 * - `localStorage`（键 `zzz.builds.v1`）——本机保存的方案列表；
 * - 文件导出 / 导入（`.json`）——把一套配装发给队友；
 * - URL 片段（`#build=…`）——一条链接直接复现一套配装。
 *
 * **URL 分享只放本地编码的内容**，不落服务端：站点公开、无鉴权，没有可写
 * 的服务端数据面（见 `docs/overview/requirements.md` 的 C7）。
 */

/** 方案的数据形状版本。字段含义变了就递增。 */
export const BUILD_SCHEMA_VERSION = 1;

/** 一套配装。 */
export interface BuildPreset {
  schemaVersion: number;
  /** 方案名。用户可改，默认「<代理人名> 方案」。 */
  name: string;
  /** 代理人预设 id。 */
  agentId: string;
  /** 音擎预设 id。 */
  weaponId: string;
  /** 两个核心加成选项 id。 */
  core: CoreSelection;
  /** 4/5/6 号位主词条选项 id。 */
  discMain: DiscMainStats;
  /** 副词条 id -> 条数。 */
  subStats: SubStatCounts;
  /** 三组二件套的**效果** id。 */
  sets: SetEffects;
  /** 三组二件套选中的**套装** id（仅「按套装选」时有值）。 */
  setDiscs: SetDiscs;
  /** 面板模式。 */
  mode: PanelMode;
  /** ISO 时间戳。 */
  savedAt: string;
}

/** 存在 localStorage 里的方案列表。 */
export interface BuildLibrary {
  schemaVersion: number;
  builds: BuildPreset[];
}

/**
 * 分享链接用的**紧凑形状**。
 *
 * 键名压到一个字母、空值省略——URL 片段越短越好分享。解码时补回完整形状。
 */
export interface CompactBuild {
  v: number;
  n?: string;
  a?: string;
  w?: string;
  c?: [string, string];
  d?: [string, string, string];
  s?: Record<string, number>;
  t?: [string, string, string];
  g?: [string, string, string];
  m?: PanelMode;
}

/** 把完整方案压成紧凑形状（丢空值）。 */
export function toCompact(preset: BuildPreset): CompactBuild {
  const compact: CompactBuild = { v: preset.schemaVersion };
  if (preset.name) compact.n = preset.name;
  if (preset.agentId) compact.a = preset.agentId;
  if (preset.weaponId) compact.w = preset.weaponId;
  const core = [preset.core.core1, preset.core.core2];
  if (core.some(Boolean)) compact.c = core as [string, string];
  const disc = [preset.discMain.disc4, preset.discMain.disc5, preset.discMain.disc6];
  if (disc.some(Boolean)) compact.d = disc as [string, string, string];
  const subs = Object.fromEntries(
    Object.entries(preset.subStats).filter(([, count]) => count > 0),
  );
  if (Object.keys(subs).length) compact.s = subs;
  const sets = [preset.sets.set0, preset.sets.set1, preset.sets.set2];
  if (sets.some(Boolean)) compact.t = sets as [string, string, string];
  const discs = [preset.setDiscs.set0, preset.setDiscs.set1, preset.setDiscs.set2];
  if (discs.some(Boolean)) compact.g = discs as [string, string, string];
  if (preset.mode) compact.m = preset.mode;
  return compact;
}

/** 把紧凑形状还原成完整方案。非法输入抛错，由调用方转成提示。 */
export function fromCompact(compact: CompactBuild): BuildPreset {
  if (!compact || typeof compact !== 'object' || compact.v !== BUILD_SCHEMA_VERSION) {
    throw new Error('配装链接的格式不对（版本不符）');
  }
  return {
    schemaVersion: compact.v,
    name: compact.n ?? '',
    agentId: compact.a ?? '',
    weaponId: compact.w ?? '',
    core: { core1: compact.c?.[0] ?? '', core2: compact.c?.[1] ?? '' },
    discMain: {
      disc4: compact.d?.[0] ?? '',
      disc5: compact.d?.[1] ?? '',
      disc6: compact.d?.[2] ?? '',
    },
    subStats: { ...(compact.s ?? {}) },
    sets: {
      set0: compact.t?.[0] ?? '',
      set1: compact.t?.[1] ?? '',
      set2: compact.t?.[2] ?? '',
    },
    setDiscs: {
      set0: compact.g?.[0] ?? '',
      set1: compact.g?.[1] ?? '',
      set2: compact.g?.[2] ?? '',
    },
    mode: compact.m ?? 'standard',
    savedAt: new Date().toISOString(),
  };
}

/** 校验一份方案是否「像样」——导入外部文件时用。 */
export function isUsableBuild(value: unknown): value is BuildPreset {
  if (!value || typeof value !== 'object') return false;
  const preset = value as Partial<BuildPreset>;
  if (preset.schemaVersion !== BUILD_SCHEMA_VERSION) return false;
  if (typeof preset.core !== 'object' || preset.core === null) return false;
  if (typeof preset.sets !== 'object' || preset.sets === null) return false;
  if (typeof preset.subStats !== 'object' || preset.subStats === null) return false;
  return true;
}
