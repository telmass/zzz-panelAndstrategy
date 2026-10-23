---
name: agent-strategy
description: Produce a complete "代理人攻略" (agent strategy) page for any Zenless Zone Zero agent — scrape the official HoYoLAB Wiki, structure guide data, author editorial content, compute a graduation panel, and register the page. Reference implementation in strategy/ye-shunguang/.
---

# ZZZ Agent Strategy Page

> 🧭 本 skill 是 `get-agent-strategy` 的子流程，通常由它编排调用；单独使用同样有效。
> 共享规则见 [`_shared/naming.md`](../_shared/naming.md)。

Use this skill when the user names a ZZZ agent and asks for a 攻略 page / strategy page / agent guide page.
**整页部署（含预设、图片、面板、登记表、闸门）优先调用 `get-agent-strategy`**（`python tools/agent_deploy.py --name <中文名>`），
本 skill 是它的阶段 C/D/E 实现。

The output is a data-driven page mounted into the main app: one folder per agent under `strategy/` (folder name = route slug). Rendering is shared — do NOT create `index.html / app.js / styles.css`.

```
strategy/<slug>/
└── data/
    ├── <slug>.json           # scrape product (scrape_agent_guide.py)
    └── <slug>.strategy.json  # editorial content + computed graduation panel
```

## Workflow

### Step 1 — Scrape the Wiki

```powershell
python .github/skills/agent-strategy/scripts/scrape_agent_guide.py \
  --entry-page-id <id> --slug <slug> \
  --output strategy/<slug>/data/<slug>.json
```

- Find `<id>` from the agent index: https://baike.mihoyo.com/zzz/wiki/channel/map/2/43
- The script downloads all images to `frontend/public/images/` and writes `/images/…` URLs.
- Verify the summary printout: agent name, attribute/profession/grade, 10 base panel items, 6 skill categories, 6 cinema levels.

### Step 2 — Place the attribute icon (manual)

If the scraper didn't download an attribute icon (check `profile.icons.attribute`), manually place it at `frontend/public/images/attributes/<slug>.webp` using the naming table in [`_shared/naming.md`](../_shared/naming.md).

### Step 3 — Author `<slug>.strategy.json`

Create the editorial content. Schema is documented in `strategy/README.md`.

**Fields you must confirm with the user first** (editorial content is NOT derivable from the Wiki):

1. Skill priority chain and target levels
2. Weapon recommendations (tiers: 专属 / 下位 / 备选 / 四星)
3. Drive disc builds. **Two装法 only** (contract in `strategy/README.md`):
   - **4+2** — one 4-piece set plus one 2-piece group. `set4` is the 4-piece set; it may be an **array of candidates** (三选一, each with a `scene` saying when to use it). `set2` is the first 2-piece group.
   - **2+2+2** — three 2-piece groups and no 4-piece set: `set4` is `null`, the groups are `set2` / `set2b` / `set2c`.
   **If the 4-set differs between builds, write them as separate entries in the `driveBuilds` array** — even if the 2-set, mainStats, and subPriority are identical (see roxy: 非锋御队 4 山大王 vs 锋御队 4 静听嘉音). Name each build with its usage scenario prefix (e.g. "非锋御队：…" / "锋御队：…").
   Within a group, `main` / `alt` are **candidates** (二选一) and may themselves be arrays (多套同效果的候选套装).
4. Graduation panel spec (weapon, sets, cores, main stats, 54 sub-stat allocation)
5. Team compositions (~3 teams)
6. Text guide (competitive notes)

> The export card also renders `driveBuilds[].mainStats[]`: `main` is the primary main stat and `alt` is the alternative shown as「备选」. Fill `alt` for every slot (write `"无"` when there is no alternative); the card hides `"无"` automatically. Main stats are grouped per build: when every build uses the same main stats the card prints one shared「主词条」row, otherwise each build gets its own row labelled with the build name. Each slot is one small box (4/5/6 号位共三个框), and its alternative stays inside the same box as the primary.

### Step 4 — Compute the graduation panel

```powershell
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
  --strategy strategy/<slug>/data/<slug>.strategy.json \
  --agent-id <id> --weapon-id <id> --set4-id <id> --set2-id <id> \
  --core1 <id> --core2 <id> \
  --disc4 <id> --disc5 <id> --disc6 <id> \
  --set4-effect <id> --set2-effect <id> \
  [--set2b-id <id> --set2b-effect <id>] \
  [--set2c-id <id> --set2c-effect <id>] \
  --sub-stats "cr:13,cd:16,atk_pct:16,atk_flat:5,pen_val:4" \
  --rows atk,cr,cd,pv \
  --core-spec "..." --main-spec "..." --sub-spec "..."
```

The `--check` flag compares without writing. `--check-all` validates all strategy files structurally.

**Empty vs `none`.** An empty flag means "not specified, use the default"; `none` means
"this group does not exist". For a 2+2+2 build pass `--set4-id none` (no 4-piece set)
and fill `--set2-id` / `--set2b-id` / `--set2c-id`.

**6 pieces of the same set.** If the 4-piece group and a 2-piece group are the **same**
set, the actual effect is **one 2-piece effect + one 4-piece effect** — the same set's
2-piece bonus does not stack just because you wear two more pieces. The script merges
the duplicate group away (and prints a note) instead of counting it twice.
A group whose 2-piece effect cannot be computed (属性伤害 / 条件触发 — see
`data/catalog/drive-discs.json`'s `effect2Note`) takes **no slot** but is still recorded
as worn.

**Hard rule:** Every agent's graduation panel is unique. NEVER copy one agent's build parameters to another. Confirm the spec with the user.

**Sub-stats must total 54** (initial 4 + 5 upgrades × 6 discs = 9 per disc × 6 = 54).

> **Display note:** the page/export card splits the 54 rolls into major + minor (e.g. Roxy = `47+7`). This is display-only, implemented in `frontend/src/strategy/substats.ts`; keep the full 54-roll allocation in `subStats` and do not rewrite it to `47+7`.

### Step 5 — Register

```powershell
python tools/gen_strategy_guides.py
python tools/sync_manifest.py
python tools/bundle_worker_data.py
```

The first command generates `frontend/src/constants/strategyGuides.ts` from mapping +
strategy data. Never hand-edit it.

The second refreshes `data/manifest.json`'s derived fields (`count` / `sha256`). Any change
to a dataset's content changes both — **skipping it leaves the repository failing
`sync_manifest.py --check` and turns CI red**.

The third recompiles the Worker data module. `pywrangler` uploads only `.py` files, so a
refreshed preset that is not recompiled never reaches production.

### Step 6 — Verify

```powershell
python tools/normalize_strategy.py --check
python tools/gen_strategy_guides.py --check
python tools/sync_manifest.py --check
python tools/bundle_worker_data.py --check
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check
python tools/check_ui_contrast.py --check
python tools/check_ui_scale.py --check
cd frontend; npm run test; npm run build
```

The second-to-last panel check is the **reference instance** (叶瞬光): it recomputes the
published panel and compares it. The other 60 agents' panels are not recomputed — that is a
known gap (see `docs/overview/requirements.md` §7).

## Export card (保存攻略)

`保存攻略` no longer screenshots the page. It builds an off-screen card from the same JSON via `frontend/src/strategy/strategyCard.ts` and exports a PNG:

- 1360px wide, white background, dark text; root class is `strategy-card strategy-card--export` so it overrides the launcher `.strategy-card` / `.strategy-card__tachie` rules in `components.css`;
- left side uses `strategy.background` (fallback: `assets.tachie`);
- six branches: 技能加点 / 命座 / 武器 / 驱动盘 / 队伍 / 毕业面板;
- 命座 shows only the 01–06 slots with key levels highlighted (no note text in the export card);
- 驱动盘 shows build rows + compact 4/5/6 main-stat boxes, each with `main` and `alt` (备选) inside the same box and left-aligned. The card shows only the stat name and strips the numeric suffix (`异常精通 +92` → `异常精通`); the detail page still renders the full value.
- 驱动盘套装按**装备组**出栏：`set2` / `set2b` / `set2c` 三组 2 件套（并列，都要装）各一栏，编号 ①②③ 并带套装名；**没有 4 件套组时（2+2+2）整个「4 件套」栏不渲染**。
- 毕业面板 shows both full and non-full panels, with the major+minor roll summary.

Export-card layout rules (the card is rasterised by html2canvas):

- only use flex — `display: grid` is flattened into vertical stacking by html2canvas;
- `.strategy-card` in `components.css` (launcher cards) also matches the export card, so reset `flex-direction: row`, `align-items: stretch` and `justify-content: flex-start` explicitly;
- do not rely on `object-fit` (unsupported): size images with `max-width` / `max-height`.

`复制攻略` puts the **same card** into the system clipboard (falls back to a download when the
clipboard is unavailable), so the image can be pasted directly. When changing card markup
or the roll display, run the card tests:

```powershell
cd frontend
npm test -- --run tests/strategy-card.spec.ts tests/substats.spec.ts
```

## Naming conventions

Attribute / profession / grade → icon slug mapping: see [`_shared/naming.md`](../_shared/naming.md) (single source of truth; the mapping table lives there, not here).

**All strategy-specific image filenames must be lowercase**: `film.webp` (cinema priority), `tachie.webp`, `background.webp`, `cinema-2.webp`, `cinema-3.webp`. The `/images/…` URL in JSON must match the on-disk filename exactly — Cloudflare's CDN is case-sensitive even though local dev on Windows/macOS is not.

## Cinema priority (optional field)

To add a cinema priority section to an agent's strategy page, include this in `<slug>.strategy.json`:

```json
"cinemaPriority": {
  "image": "/images/strategy/<slug>/film.webp",
  "keyLevels": [1, 2, 6],
  "note": "核心命座说明…"
}
```

- `image`: path to the cinema priority icon (typically `film.webp`, ~48KB)
- `keyLevels`: array of cinema numbers (1–6) that are key investment nodes
- `note`: explanatory text shown below the image and numbered slots

The renderer displays a 56px image on the left and six numbered slots (01–06) on the right; key levels are highlighted with accent color. Agents without this field skip the section entirely. The export card reuses the same 01–06 slots and highlights but omits the `note` text.

## Key rules

- **Images go only under `frontend/public/images/`** — JSON writes `/images/…` URLs only.
- **Never edit `frontend/tests/fixtures/legacy-calculator/`** — it is the three-way parity baseline.
- **Graduation panels are computed, not hand-written** — always use `calc_graduation_panel.py`.
- **Unknown option IDs are silently ignored** — verify the final panel has all expected segments.
- **If a set effect has no matching option (e.g. 原始朋克's shield +15%), pass `--set4-effect none`** explicitly.

## Reference implementations

- 叶瞬光: `strategy/ye-shunguang/` (standard mode, attack-focused)
- 般岳: `strategy/banyue/` (rupture mode, HP-focused)
- 克拉蕾: `strategy/claret/` (armorer mode, defense-based)
