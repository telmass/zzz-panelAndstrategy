---
name: read-zzz-engine-stats
description: Read a named Zenless Zone Zero W-Engine's max-level base ATK and its fixed high-level substat (暴击伤害 etc.) from the official HoYoLAB Wiki.
---

# Read ZZZ W-Engine Stats

Use this skill when the user gives a 音擎 (W-Engine) name and needs the two values the panel
calculators consume:

1. 基础攻击力 at agent level 60 / 0 突破 (the 音擎基础值 input).
2. The fixed 高级属性 at level 60 (暴击伤害 for most S-rank 强攻 engines).

Also report the 突破 bonus table and 音擎特性 when the user asks for more than those two
fields, and record the 职业 tag that the Wiki shows for the engine, which is the same tag used
in the preset selector. There are **seven** tags — 强攻/击破/异常/支援/防护/命破/锋御 (the full
list is `WEAPON_ROLE_TAGS` in `frontend/src/constants/calculatorOptions.ts`) — so do not treat
锋御 as missing: it is the one tag whose engines provide 基础防御力 instead of 基础攻击力
(`baseKind: 'def'`).

## Source and transport

- Index/browse page: <https://baike.mihoyo.com/zzz/wiki/channel/map/2/45> (音擎 category).
- Detail page: `https://baike.mihoyo.com/zzz/wiki/content/<entry_page_id>/detail`.

The detail page is client-rendered, so `webfetch` on it returns only the empty Nuxt shell.
Read the data from the official content API that the page itself calls:

```
https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id=<id>
```

Headers that work: `User-Agent: Mozilla/5.0`, `Referer: https://baike.mihoyo.com/`,
`x-rpc-wiki_app: zzz`. A good response is `{"retcode":0,"message":"OK","data":{"page":{...}}}`.

Notes that cost time if forgotten:

- `https://api-wiki.mihoyo.com/...` does not resolve from this environment. Use the
  `act-api-takumi.mihoyo.com/hoyowiki/zzz` base instead.
- Write the response to a file and read it as UTF-8 explicitly. Piping the response through
  `Get-Content` in Windows PowerShell 5.1 decodes it as GBK and turns every Chinese string
  into mojibake:
  `[System.IO.File]::ReadAllText($file,[System.Text.Encoding]::UTF8) | ConvertFrom-Json`
- `/wapi/entry_pages` and the `/v1/...` endpoints are not reliable for enumeration here; they
  return `retcode -502` or an empty body. Do not build discovery on them.

## Find the entry_page_id

The `entry_page_id` is the number in the detail URL. Do not guess it.

1. Run a web search for the engine name plus `baike.mihoyo.com/zzz/wiki/content`, or for the
   name plus 绝区零 音擎, and read the id out of the matching detail URL.
2. Confirm the id before reading: the response `data.page.name` must equal the requested
   engine name exactly. If it does not, the id is wrong; find another.
3. `data.page.name` is the authoritative name; prefer it for reporting.

## Read the values

In `data.page.modules[].components[]`, each component has a `component_id` and a `data`
field holding a JSON **string** that must be parsed a second time.

- `material_base_info` — rarity grade (`S`/`A`) and name. Reject the page if the grade is not
  what the user expects.
- `role_ascension` — the 突破 table. `list[]` has `tab_name` (`10突破` … `50突破`) and `attr[]`
  with `key`/`value` pairs:
  - `突破前基础` / `突破后基础` = base ATK before/after that breakthrough.
  - `突破前高级` / `突破后高级` = the fixed high-level substat before/after that breakthrough.
  Strip the `<p>` tags from `value` before reporting.
- `multi_table` — the 音擎效果 tab. The cell text contains `初始面板：基础攻击力+50 暴击伤害+19.2%`
  and `满级面板：基础攻击力+743 暴击伤害+48%`, plus the passive text with its rank list
  (`20%/22%/24%/26%/28%`).

Report the two calculator inputs as:

- **基础攻击力 (level 60, 0 突破)** = the 满级面板 value from `multi_table`. It already
  includes level growth and no breakthrough bonus.
- **固定高级词条 (level 60)** = the 暴击伤害/other stat in the same 满级面板 text.

If the 满级面板 says 基础防御力 instead, this is a 锋御 engine: report 基础防御力 as the base
value and tag it 锋御, never 强攻.

Cross-check both against `role_ascension`: the 满级 value must equal the `50突破` `突破后基础`
value minus the breakthrough gain (`743 = 665 + 78`), and the 初始 value must equal the
`0` column. If the two components disagree, report both numbers and the discrepancy instead of
picking one.

Note explicitly that the Wiki page does **not** list the four random substats of a rolled
engine; the fixed 高级属性 is the only substat this page defines. Do not invent per-roll values.

## Output

Present three groups:

### 音擎 and tag

Name, `S`/`A` grade, and the 职业 tag from the Wiki 音擎展示 table (for example `[强攻]`).

### Base values (calculator inputs)

- 基础攻击力 (60级/0突破): the flat number.
- 固定高级词条 (60级): the percentage.

### 突破 table (on request)

Full 突破前/突破后 table for both base ATK and the high-level substat, plus the 音擎特性 text
and the 获取途径 line if present.

Include the detail-page link. State the exact `entry_page_id` used so the read is auditable.
Do not modify calculator files unless the user separately asks for an implementation.

## Verified example: 云霓孤光

Confirmed by reading `entry_page_id=1751` on 2026-10-01.

- Page: `https://baike.mihoyo.com/zzz/wiki/content/1751/detail`, grade `S`, tag `[强攻]`,
  recommended agent 叶瞬光 (`data-entry-id=1687`), obtained from 限定调频「喧哗奏鸣」.
- 满级面板: 基础攻击力+743, 暴击伤害+48%. 初始面板: 基础攻击力+50, 暴击伤害+19.2%.
- 突破 table (基础 ATK / 暴击伤害), 突破前 → 突破后:
  10: 128 → 173, 19.2% → 25%; 20: 251 → 296, 25% → 30.7%; 30: 374 → 419, 30.7% → 36.5%;
  40: 497 → 542, 36.5% → 42.2%; 50: 620 → 665, 42.2% → 48%.
- 音擎特性「玉魄冰心」: ignore 20%/22%/24%/26%/28% physical resistance; while [以太帷幕] is
  open, damage +25%/28.7%/32.5%/36.2%/40% and 暴击伤害 +25%/28.7%/32.5%/36.2%/40% for 40s.
- The two calculator inputs are therefore 基础攻击力 743 and 暴击伤害 48%. The 50-突破
  基础攻击力 665 is a breakthrough bonus on top of 743 and must not be added to it.

## Bulk refresh of every engine

When the user asks for all 音擎 rather than one, do not try to enumerate them through a
listing API. As of 2026-10-01 no reachable endpoint returns a channel's entries:
`/wapi/entry_pages?menu_id=45` returns an empty list, `/v1/content/selector` answers
`应用不存在`, and the `/v1/...` routes 404 on every `act-api-takumi` base. The entry id space
is small and dense instead: existing pages stop around id 2200, so scanning `1..2600` with
8 concurrent requests covers the whole wiki and finds every engine.

Run the packaged script from the repository root:

Run from the repository root; the default `--out` path is repo-root relative.

```
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python tools/sync_presets.py --to-legacy
python tools/bundle_worker_data.py
```

It scans, filters weapon pages, extracts the values, and rewrites `data/weapon-presets.json`.
As of 2026-10-01 it produces 100 presets: 47 S, 37 A, 16 B, of which 4 are 锋御. Reruns are
idempotent, so re-running must leave the file byte-identical; compare hashes to prove nothing
drifted.

`data/weapon-presets.json` is the single source of truth for the whole repository. The
parity fixture's `frontend/tests/fixtures/legacy-calculator/data/weapon-presets.js` is
generated from it by `sync_presets.py --to-legacy`; never write that file from this
script. After a refresh, run that command so the fixture stays in sync, and
`python tools/sync_presets.py --to-legacy --check` must exit 0.

The third command, `python tools/bundle_worker_data.py`, is the Cloudflare deploy gate
and must be re-run after **any** change to `weapon-presets.json` or
`agent-presets.json` (both files are compiled into the same module).
`pywrangler` uploads only `.py` files, so a refreshed preset that is not recompiled
never reaches production: the `.json` is silently dropped, `loader.py` falls back to
the generated `zzz_panel._bundled_data` module, and the live `/api/presets/*` keeps
serving the previous data. With no generated module at all (a clean clone deployed
directly) the route returns 503 instead. The module is a build artifact and is
gitignored, so nothing catches the omission — use
`python tools/bundle_worker_data.py --check` as the drift gate (non-zero exit = stale).

Parsing rules the script encodes, each of which broke an earlier hand-written regex:

- A page is a 音擎 page when its `role_ascension` rows use the keys `突破前基础` /
  `突破后基础`. Agents never use those keys.
- **锋御 engines are not attacks.** Their 满级面板 is `基础防御力+N 防御力+48%`, not
  `基础攻击力`. A parser anchored on 基础攻击力 silently drops all four of them
  (猩红渴望 431, 血髓秘匣 356, 「月相」-弦 282, 喵运当头 356) instead of mislabeling them, so
  always confirm the total engine count after a refresh and never assume every engine is 强攻.
  Presets carry `baseKind: 'atk' | 'def'` plus `baseAttack` and `baseDefense`, with the unused
  one set to 0; the calculator shows 基础防御力 and feeds `wDef` only for `baseKind: 'def'`.
- 初始面板 and 满级面板 sit in one run of text with no separator, so the panel regex must use a
  lookahead for the next panel marker; a `[^\n]+` tail swallows the 满级 value.
- 异常精通 substats have **no** `%` sign (`异常精通+60`), so the percent group is optional.
  A percentage-only regex silently drops the six 异常精通 engines.
- The passive text can follow the panel immediately (`…异常精通+75对于[异常]角色`), so anchor on
  the label with a Chinese-character class and do not scan to end of line.
- 命破 engines label the breakthrough row `攻击力+532` instead of `基础攻击力+532`, so a
  cross-check regex must accept both.
- The 职业 tag comes from `[强攻]角色` style markers in the 音擎效果 text.

Substat label to calculator key mapping used in `data/weapon-presets.json`:

| Wiki label | `substat.to` | `kind` |
|---|---|---|
| 暴击伤害 | `cd` | pct |
| 暴击率 | `cr` | pct |
| 攻击力 | `atk_pct` | pct |
| 生命值 | `hp_pct` | pct |
| 防御力 | `def_pct` | pct |
| 冲击力 | `impact_pct` | pct |
| 能量自动回复 | `er_pct` | pct |
| 穿透率 | `pr` | pct |
| 异常掌控 | `ac_pct` | pct |
| 异常精通 | `am` | flat |

Preset ids are `ep-<entry_page_id>` so every row is traceable to its Wiki page. Presets are
ordered S, then A, then B, then by id.
