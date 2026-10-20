---
name: agent-strategy
description: Produce a complete "代理人攻略" (agent strategy) page for any Zenless Zone Zero agent — scrape the official HoYoLAB Wiki, structure guide data, author editorial content, compute a graduation panel, and register the page. Reference implementation in strategy/ye-shunguang/.
---

# ZZZ Agent Strategy Page

Use this skill when the user names a ZZZ agent and asks for a 攻略 page / strategy page / agent guide page.

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

If the scraper didn't download an attribute icon (check `profile.icons.attribute`), manually place it at `frontend/public/images/attributes/<slug>.png` using the naming table below.

### Step 3 — Author `<slug>.strategy.json`

Create the editorial content. Schema is documented in `strategy/README.md`.

**Fields you must confirm with the user first** (editorial content is NOT derivable from the Wiki):

1. Skill priority chain and target levels
2. Weapon recommendations (tiers: 专属 / 下位 / 备选 / 四星)
3. Drive disc builds (4-set + 2-set, main stats, sub-stat priority). **If the 4-set differs between builds, write them as separate entries in the `driveBuilds` array** — even if the 2-set, mainStats, and subPriority are identical (see roxy: 非锋御队 4 山大王 vs 锋御队 4 静听嘉音). Name each build with its usage scenario prefix (e.g. "非锋御队：…" / "锋御队：…"). Do NOT merge different 4-sets into one build with a set4 array; that pattern is deprecated.
4. Graduation panel spec (weapon, sets, cores, main stats, 54 sub-stat allocation)
5. Team compositions (~3 teams)
6. Text guide (competitive notes)

> The export card also renders `driveBuilds[].mainStats[]`: `main` is the primary main stat and `alt` is the alternative shown as「备选」. Fill `alt` for every slot (write `"无"` when there is no alternative); the card hides `"无"` automatically.

### Step 4 — Compute the graduation panel

```powershell
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
  --strategy strategy/<slug>/data/<slug>.strategy.json \
  --agent-id <id> --weapon-id <id> --set4-id <id> --set2-id <id> \
  --core1 <id> --core2 <id> \
  --disc4 <id> --disc5 <id> --disc6 <id> \
  --set4-effect <id> --set2-effect <id> \
  --sub-stats "cr:13,cd:16,atk_pct:16,atk_flat:5,pen_val:4" \
  --rows atk,cr,cd,pv \
  --core-spec "..." --main-spec "..." --sub-spec "..."
```

The `--check` flag compares without writing. `--check-all` validates all strategy files structurally.

**Hard rule:** Every agent's graduation panel is unique. NEVER copy one agent's build parameters to another. Confirm the spec with the user.

**Sub-stats must total 54** (initial 4 + 5 upgrades × 6 discs = 9 per disc × 6 = 54).

> **Display note:** the page/export card splits the 54 rolls into major + minor (e.g. Roxy = `47+7`). This is display-only, implemented in `frontend/src/strategy/substats.ts`; keep the full 54-roll allocation in `subStats` and do not rewrite it to `47+7`.

### Step 5 — Register

```powershell
python tools/gen_strategy_guides.py
```

This generates `frontend/src/constants/strategyGuides.ts` from mapping + strategy data. Never hand-edit it.

### Step 6 — Verify

```powershell
python tools/normalize_strategy.py --check
python tools/gen_strategy_guides.py --check
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all
cd frontend; npm run test; npm run build
```

## Export card (保存攻略)

`保存攻略` no longer screenshots the page. It builds an off-screen card from the same JSON via `frontend/src/strategy/strategyCard.ts` and exports a PNG:

- 1360px wide, white background, dark text; root class is `strategy-card strategy-card--export` so it overrides the launcher `.strategy-card` / `.strategy-card__tachie` rules in `components.css`;
- left side uses `strategy.background` (fallback: `assets.tachie`);
- six branches: 技能加点 / 命座 / 武器 / 驱动盘 / 队伍 / 毕业面板;
- 命座 shows only the 01–06 slots with key levels highlighted (no note text in the export card);
- 驱动盘 shows build rows + 4/5/6 main-stat cards, each with `main` and `alt` (备选);
- 毕业面板 shows both full and non-full panels, with the major+minor roll summary.

`保存一图流` still captures the full page. When changing card markup or the roll display, run the card tests:

```powershell
cd frontend
npm test -- --run tests/strategy-card.spec.ts tests/substats.spec.ts
```

## Naming conventions

| Chinese | English / icon slug | Type |
| --- | --- | --- |
| 流明 | lumiflux | attribute |
| 玄墨 | auric-ink | attribute |
| 凛刃 | honed-edge | attribute |
| 烈霜 | frost | attribute |
| 风 | wind | attribute |
| 火 | fire | attribute |
| 冰 | ice | attribute |
| 以太 | ether | attribute |
| 物理 | physical | attribute |
| 电 | electric | attribute |
| 强攻 | attack | profession |
| 击破 | stun | profession |
| 异常 | anomaly | profession |
| 支援 | support | profession |
| 防护 | defense | profession |
| 命破 | rupture | profession |
| 锋御 | armorer | profession |

**All strategy-specific image filenames must be lowercase**: `film.png` (cinema priority), `tachie.png`, `background.png`, `cinema-2.png`, `cinema-3.png`. The `/images/…` URL in JSON must match the on-disk filename exactly — Cloudflare's CDN is case-sensitive even though local dev on Windows/macOS is not.

## Cinema priority (optional field)

To add a cinema priority section to an agent's strategy page, include this in `<slug>.strategy.json`:

```json
"cinemaPriority": {
  "image": "/images/strategy/<slug>/film.png",
  "keyLevels": [1, 2, 6],
  "note": "核心命座说明…"
}
```

- `image`: path to the cinema priority icon (typically `film.png`, ~48KB)
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
- 克拉蕾: `strategy/claret/` (fengyu mode, defense-based)
