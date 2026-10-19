---
name: read-zzz-drive-disc
description: Read every Zenless Zone Zero drive-disc set's 2-piece and 4-piece effect text plus the set icon from the official HoYoLAB Wiki, writing data/drive-disc-presets.json.
---

# Read ZZZ Drive-Disc Sets

Use this skill when the drive-disc set effects (2 件套 / 4 件套) are needed as data:
bulk refresh of `data/drive-disc-presets.json`, or a single set's effect text read from
the Wiki.

## Source and transport

- Index/browse page: <https://baike.mihoyo.com/zzz/wiki/channel/map/2/46> (驱动盘 category).
- Detail page: `https://baike.mihoyo.com/zzz/wiki/content/<entry_page_id>/detail`.

The pages are client-rendered, so `webfetch` returns only the empty Nuxt shell. Read the
data from the official content API the page itself calls:

```
https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id=<id>
```

Headers that work: `User-Agent: Mozilla/5.0`, `Referer: https://baike.mihoyo.com/`,
`x-rpc-wiki_app: zzz`. A good response is `{"retcode":0,"message":"OK","data":{"page":{...}}}`.

Notes that cost time if forgotten:

- `https://api-wiki.mihoyo.com/...` does not resolve from this environment. Use the
  `act-api-takumi.mihoyo.com/hoyowiki/zzz` base instead.
- Write responses to a file and read them as UTF-8 explicitly. Piping the response through
  `Get-Content` in Windows PowerShell 5.1 decodes it as GBK and turns every Chinese string
  into mojibake.
- Do not build discovery on `/wapi/entry_pages` or the `/v1/...` endpoints: they return
  `retcode -502` or an empty body here, exactly as for agents and engines.

## Bulk refresh

Run the packaged script from the repository root; the default `--out` path is
repo-root relative.

```
python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py
python tools/sync_presets.py --to-legacy --check   # 预设漂移闸（不动本文件也应退出 0）
```

It scans `entry_page_id=1..2600` with 8 concurrent requests, keeps every page whose
components include `driver_disk`, and rewrites `data/drive-disc-presets.json`. As of
2026-10-12 it produces 30 sets. Reruns are idempotent: the JSON is byte-identical and
images are only rewritten when their bytes change.

Unlike the agent and engine presets, this file is **not** wired into the calculator: it
has no legacy JS wrapper, so `sync_presets.py --to-legacy` does not cover it, and it is
not compiled into `_bundled_data.py`, so `bundle_worker_data.py` does not cover it
either. Both gates must still exit 0 after a refresh, because they prove nothing else
drifted while you were here.

## Parsing rules the script encodes

- A page is a drive-disc page when it carries a `driver_disk` component (the six slot
  names, per-slot max-level main-stat tables, and the disc icon live there). Agents and
  engines never have that component, so the signature cannot collide with them.
- The 2-piece / 4-piece effects sit in the **first** `double_col_table` whose header
  contains 「二件套」. The single row has two cells: 2 件套 first, 4 件套 second. Every
  disc page also carries a 推荐角色 `double_col_table`; its header differs, so filtering
  on the header never reads the wrong table.
- Both cells must be non-empty after tag stripping, otherwise the set is skipped and
  reported rather than written as half a record.
- Effect text stays verbatim from the Wiki, including the full-width 「＋」 in
  混沌爵士's 「异常精通＋30点。」. The script normalizes whitespace only; it never
  rewrites or quantifies the numbers.
- The set icon comes from `material_base_info.img` (the detail-page header image) and
  falls back to the page `icon_url` (the channel listing icon). Both URLs carry the same
  content hash for every set; only the size suffixes differ. The icon is written to
  `frontend/public/images/discs/ep-<entry_page_id>.png`, the same `ep-<entry_page_id>`
  naming `images/agents` and `images/weapons` use, and the JSON's `image` field records
  the served URL `/images/discs/ep-<entry_page_id>.png` — every image reference in this
  repo is a `/images/…` URL rooted at `frontend/public/images/` (never a repo-relative
  or page-relative path).
- The file holds 2 件套 / 4 件套 effect text **only**. Main stats, substats, drop rates,
  and recommended agents are deliberately not written: the consumers only ask what a set
  does at 2 and 4 pieces.

## Output

`data/drive-disc-presets.json` is the single source of truth for drive-disc set effects
and must not be hand-edited; the script overwrites the whole file on each run. Entries
carry `id` (`ep-<entry_page_id>`), `name`, `source` (detail-page link),
`setEffect2` / `setEffect4` (verbatim Wiki text), and `image`
(`/images/discs/ep-<entry_page_id>.png` URL), sorted by `entry_page_id`. Details of the
file's role in the data pipeline live in [`data/README.md`](../../../data/README.md).
