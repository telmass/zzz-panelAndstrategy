# Project Repair Plan

Status: **proposed, not implemented**  
Audit date: **2026-10-18**  
Scope: repository architecture, reference paths, generated data, tests, CI, and technical documentation.

This document is the working repair plan produced by the full-project audit. It records what is currently broken, why it matters, which files to change, and how to verify the repair.

The core architecture is sound: Vue SPA → `src/api` → FastAPI → `services` → pure `core`, with generated presets and a shared Vue strategy renderer. The problems are concentrated in generated-data integrity, untracked release artifacts, a few architecture-boundary violations, and stale documentation.

> **Revision note (third audit pass):** added path-fragility finding P2-17 (skill scripts `parents[N]`), image-weight finding P2-18 (240 MB unoptimized PNGs), guide-content finding P2-19 (GuideView monolith), and stale-path finding P2-20 (fix-agent SKILL.md).
>
> **Revision note (second audit pass):** this revision adds the main-page and navigation findings P1-12–P1-16, the bundle/asset-packaging findings P2-15–P2-16, and the dedicated “Main page entry points and navigation policy” section.

## 1. Verified baseline

| Check | Result |
| --- | --- |
| Backend tests | `310 passed` |
| Frontend tests | `118 passed` |
| `npm run typecheck` | pass |
| `npm run build` | pass |
| Agents | 60 |
| Weapons | 101 |
| Drive-disc sets | 30 |
| Strategy directories | 60 |
| Generated strategy registry | 60 |
| Name mapping rows | 62 (2 unreleased) |
| Images | 398 PNG: 60 agents, 100 weapons, 30 discs, 7 roles, 6 skills, 10 attributes, 2 grades, 183 strategy-specific |
| `gen_strategy_guides.py --check` | **fails (exit 1)** |
| `calc_graduation_panel.py --check` | **fails with defaults; not a valid repository-wide gate** |
| Clean-clone readiness | **not ready**: Caesar data/images and `tools/seed_main_stat_notes.py` are untracked |

## 2. P0 — Release blockers

| ID | Problem and evidence | Repair |
| --- | --- | --- |
| P0-1 | Untracked files required by the current tree and CI: `strategy/caesar/data/*`, `frontend/public/images/strategy/caesar/*`, `tools/seed_main_stat_notes.py`. CI already calls `seed_main_stat_notes.py --check`, so a clean clone fails immediately. | Review and stage all three groups. Confirm `.gitignore` does not exclude them. Add a clean-clone CI check. |
| P0-2 | Generated registry drift. `gen_strategy_guides.py --check` fails because the checked-in `strategyGuides.ts` contains manual additions the generator does not produce: `attributeIcon` for `astra-yao`/`nicole`, and `roleIcon` for `qingyi`/`zhu-yuan`. Source `strategy/<slug>/data/<slug>.json` is missing icons for five agents: `astra-yao` (attribute), `nicole` (attribute), `ben`/`qingyi`/`zhu-yuan` (profession). CI runs this gate, so the current branch cannot pass CI. | Fix the five source `profile.icons` entries and/or add deterministic icon fallback in `gen_strategy_guides.py` using `agent-presets.json` (`attribute`, `roleTag`, `grade`). Regenerate the TS file; never hand-edit it. Add a test that runs the generator in check mode. |
| P0-3 | `calc_graduation_panel.py --check` is not reproducible. With no flags it exits 1 because its default build text/substats do not match the stored `ye-shunguang` panel. With the exact per-agent flags, the stored totals do match (e.g. Caesar 182.0 / 20859.4 / 1900.6 / 2167.2; Ye Shunguang 3907.5 / 50.6 / 238.8 / 36). The current changelog claims this check passes globally, which is false. | Store a machine-readable `graduationBuild` spec per strategy JSON: agent/weapon/set ids, core ids, disc ids, set-effect ids, sub-stat counts, rows, mode, and text fields. Add `--from-spec` / `--check-all`. Then `--check` becomes a real gate. Until then, remove the global-pass claim from `docs/changelog.md`. |
| P0-4 | Broken strategy data references: `strategy/trigger/data/trigger.strategy.json` references `ep-2074` for 波可娜, but the preset id is `ep-1191`; the member also has an empty avatar. `burnice` and `yanagi` still contain `"专武（名称待确认）"` with empty icons. `pyrois` has `cinemaBackdrops: {}`. `zhao`'s first `driveBuilds` entry has no `name`. `claret` uses `月相·弦` while the preset is `「月相」-弦`. | Correct the trigger id to `ep-1191` and add the avatar. Replace/remove placeholder weapons. Backfill pyrois cinema backdrops or add an explicit fallback. Add the missing zhao build name. Normalize the claret name or reference sets/weapons by id. Add cross-reference tests. |
| P0-5 | Missing weapon icon: `data/weapon-presets.json` has 101 entries but `frontend/public/images/weapons/` has 100. Missing `ep-2259` (`涅槃初翎`). The UI has a fallback, but the asset contract and docs claim completeness. | Preferred: add `ep-2259.png`, then update image totals from 398→399 and weapon icons from 100→101 everywhere. Alternative: document a deliberate exception and keep the fallback. |
| P0-6 | `docs/changelog.md` top entry claims `strategyGuides.ts` was regenerated and `calc_graduation_panel.py --check` passed; both are currently false. | After P0-2/P0-3, re-run the checks and rewrite the entry with actual command output. Do not claim a gate passed unless it was run with the correct arguments. |

## 3. P1 — Architecture and data-integrity issues

| ID | Problem and evidence | Repair |
| --- | --- | --- |
| P1-1 | `StrategyView.vue:37-38` calls `fetch()` directly. This violates `docs/architecture.md:82` (“components must not fetch directly; all network access goes through `src/api/`”) and `frontend/src/README.md`. | Add `frontend/src/api/strategy.ts` with a typed `fetchStrategy(slug)` function. Move fetch/error handling there. Keep cache/abort behavior. Add tests. |
| P1-2 | `renderStrategy.ts:17` imports `@data/agent-name-mapping.json`, while `docs/data-schema.md:164` says `calculatorOptions.ts` is the **only** `@data` consumer. The renderer bundles the whole mapping just to resolve short names. | Add `shortName` (and any needed canonical name) to the generated `StrategyGuide` interface and generated TS. Pass it from `StrategyView` or look it up from `strategyGuides`. Remove the runtime `@data` import. Alternatively, update the docs and accept two consumers, but removing it is cleaner. |
| P1-3 | Duplicate identity/asset maps: `ROLE_ICON` in `useCascaderIcons.ts` and `ROLE_ICON_MAP` in `renderStrategy.ts`; frontend/backend `AGENT_ATTRIBUTES`/`AGENT_ROLE_TAGS` are manually mirrored; `ATTRIBUTE_TILE_COLORS` is separate. New roles/attributes can drift silently. | Introduce one shared mapping (e.g. `data/asset-map.json` or generated TS/JSON) for attribute/role/grade → icon slug. Consume it in the scraper, generator, cascader, and renderer. Add a test comparing the Python and TypeScript whitelists. |
| P1-4 | Strategy data duplicates canonical names/icons/effects from `agent-presets.json`, `weapon-presets.json`, and `drive-disc-presets.json`, but `test_strategy_data.py` only validates base panels and a few icon paths. It does not catch the trigger id, placeholder weapons, empty avatars, or weapon/name mismatches. | Add a cross-reference test that validates: every team `agentId` exists; team names match presets; every weapon name/icon matches a weapon preset; every disc name/icon matches a disc preset; every `/images/…` reference resolves; `cinemaBackdrops` is non-empty; no placeholder text remains; `driveBuilds[*].name` exists. |
| P1-5 | `test_strategy_data.py:207` skips if a strategy agent is not in `agent-presets.json`. The project’s own rule is “pytest must have 0 skips.” A future unreleased agent page would silently skip a guard. `test_strategy_data.py:259` still contains dead `app.js`/`DATA_URL` logic. | Replace the skip with an actionable failure, or add an explicit allowlist for unreleased agents and assert it is empty. Remove the dead `app.js` branch. Add a `test_every_strategy_dir_has_preset` test. |
| P1-6 | External runtime dependency contradicts the deployment docs. `renderStrategy.ts:81` loads `html2canvas` from `https://unpkg.com` when saving an image, while `docs/deployment.md:3` says “no external service dependencies.” There is no SRI and no offline behavior guarantee. | Self-host `html2canvas` (npm dependency with dynamic `import()` or pinned vendored file). Update `docs/deployment.md`, `docs/architecture.md`, and `docs/requirements.md`. Add an SRI/version pin if vendored. |
| P1-7 | API contract documentation is wrong for fractional sub-stats. `PanelRequest.sub_stats` is `Dict[str, int]`; `3.9` returns **422**, while `docs/api-reference.md:173-174` says `3.9` will not 422 and `docs/calculation-rules.md:77-78` implies API-level flooring. The test `test_fractional_sub_stat_count_is_rejected` confirms 422. | Keep the intentional “reject fractional at the API” behavior and correct the docs. Clarify that `core` floors only when called directly, and negative counts clamp to zero at core level. |
| P1-8 | Set-option docs are wrong: `data/options.json` has **12** `setOptions`, including `def_pct_16`; `docs/calculation-rules.md:85` says 11 and omits that row. `docs/calculation-rules.md:105-109` says `pr_8` is the only extra beyond the legacy fixture, but `def_pct_16` is also absent from the fixture. `backend/src/zzz_panel/core/options.py` repeats the “only exception is pr_8” claim. | Rewrite the set-option section with all 12 rows. State that both `def_pct_16` and `pr_8` are beyond the legacy fixture. Update the Python comment. |
| P1-9 | `docs/api-reference.md:158` has invalid JSONC: `"label": "暴击伤害"` is missing a comma. | Fix the example and run a Markdown/JSONC example check if possible. |
| P1-10 | `test_strategy_data.py` icon validation only checks `attributes|icons`; it does not validate `agents`, `weapons`, `discs`, or `strategy/` images. This is why `ep-2259` and the trigger avatar gap were missed. | Add one comprehensive asset-reference test over all strategy JSON and `strategyGuides.ts`, resolving every `/images/...` path case-sensitively under `frontend/public`. |
| P1-11 | CI completeness: `.github/workflows/ci.yml` runs the data gates, but `gen_strategy_guides --check` currently fails and `seed_main_stat_notes.py` is untracked. There is no docs/path consistency check and no Worker packaging dry-run. | Stage the seed tool; make the generator pass; add `tools/check_docs.py` and optionally a separate Worker dry-run job (`uv sync --group worker`, `pywrangler deploy --dry-run`). Standardize on `uv run python` for Python commands. |
| P1-12 | The main page shows stale user-facing counts. `LauncherView.vue:22` and `:28` say `100 项音擎预设`, but `data/weapon-presets.json` has **101** entries. The counts are hardcoded in two places and are not asserted by tests. | Replace hardcoded counts with data-driven values (or a single constants module generated from the data). Update the copy to 101 and add a test that compares the launcher copy with the preset counts. |
| P1-13 | There is no catch-all route. `router/index.ts` defines only `/`, `/calculator`, `/guide`, `/strategy`, and `/strategy/:slug`; an unknown top-level path such as `/foo` renders a blank `router-view` instead of returning the user to the main page. | Add a catch-all route (`/:pathMatch(.*)*`) that redirects to the launcher or shows a small `NotFoundView`. Add a test for unknown paths. Keep the existing invalid-slug guard for `/strategy/:slug`. |
| P1-14 | Navigation is defined three times and can drift: the site-nav links and the entry cards in `LauncherView.vue:39-96`, the route table in `router/index.ts`, and the deployment self-check list in `docs/deployment.md`. Tests assert the exact lists, so adding a functional area requires edits in several files. | Add `frontend/src/constants/navigation.ts` as the single manifest of top-level functional areas (`id`, `label`, `path`, `description`, `features`, `showInNav`, `showAsCard`). Derive the site nav, launcher cards, and test expectations from it. Add a test that every top-level route (except detail/catch-all) has a manifest entry and vice versa. |
| P1-15 | The repository root `index.html` is a developer guide, but it contains a hardcoded `http://localhost:5173/` “打开应用” button and an “三个入口分别在哪” table that mixes source/dev/build paths with product navigation. This makes the product’s real main page ambiguous and creates a direct-link redirect outside the SPA. | Define the SPA route `/` (`LauncherView`) as the only product main page. Treat root `index.html` as developer documentation only: remove the hardcoded “open app” button or replace it with a command-only instruction, rename the table to “开发入口”, and link to `docs/development.md`. Do not add URL-input/redirect fields to the main page. |
| P1-16 | The only dynamic external navigation is not URL-validated. `renderStrategy.ts:331` interpolates `meta.source` into an `href` with HTML escaping only. A malformed or malicious `javascript:`/`data:` value would become a clickable redirect. | Validate external URLs before rendering: allow only `https://` and an allowlist of official hosts (for example `baike.mihoyo.com`, `act-api-takumi.mihoyo.com`, `mihoyo.com` subdomains). Keep `target="_blank"` and `rel="noopener noreferrer"`. Add a test for rejected schemes/hosts. |

## 4. P2 — Code and documentation maintainability

| ID | Problem and evidence | Repair |
| --- | --- | --- |
| P2-1 | `agent-strategy/SKILL.md` is **207 KB / 2,072 lines** and contains 60 per-agent “instance” sections. It duplicates `strategy/*.json` and `docs/changelog.md`, contains stale ids/counts, and its description still says “render the local responsive web template,” although no template exists. | Rewrite it as a concise procedure (~10–15 KB): inputs to confirm, 7 workflow steps, hard rules (54 sub-stats, no fixture edits, image root), schema link, verification. Keep 1–2 verified examples. Move the per-agent dossiers to `docs/completeds/agent-strategy-examples.md` or delete them; the data already lives in `strategy/<slug>/`. |
| P2-2 | `docs/structure-review.md` is internally contradictory: the status table says P1-2/P1-4 are fixed, but the body still describes old problems as current and references non-existent `tools/check.ps1`, `strategy/README.md`, and `strategy/_shared/`. `docs/README.md` still presents it as the current-issues document. | Rewrite it as a dated historical audit with a “residual risks” section, or move it to `docs/completeds/` and add a new concise current technical-debt doc. Remove or implement references to non-existent files. Update `docs/README.md`. |
| P2-3 | `strategy/ye-shunguang/README.md` is the shared strategy data contract but sits inside one agent’s data directory, contradicting “`strategy/<slug>/` contains only data.” Its schema table is also wrong: it says `drives`/`builds[]` instead of `driveBuilds[]`; `skillPriority` fields `key/label/note` instead of `key/label/icon/level/maxLevel/next`; `weapons` omits `tier/items`; `graduationPanel` lists `title` although the stored field has `build/totals/note/computedAt`. | Move it to `strategy/README.md`. Rewrite the contract from the actual JSON schema (top-level keys: `_meta`, `skillPriority`, `weapons`, `driveBuilds`, `teams`, `textGuide`, `graduationPanel`, optional `graduationPanelAlt`/`background`). Update links in `docs/README.md`, `docs/architecture.md`, `agent-strategy`, and `fix-agent`. |
| P2-4 | `docs/changelog.md` is **254 KB** and mixes release history with full per-agent editorial content. The top entry is currently false. | Archive older months into `docs/changelog/2026-10.md`, etc., or add a strict “only user-visible/release-level changes” policy. Correct the top entry after P0 fixes. Link to strategy data instead of copying it. |
| P2-5 | Count/path drift across docs: `docs/directory-layout.md:32` says 180 strategy images (actual 183), `:63` says 75 tokens (actual 76), `:97` says 100 weapon icons (actual 100, but 101 presets); `docs/deployment.md:408` expects 100 weapons; `docs/deployment.md:470` says “no CI” although `.github/workflows/ci.yml` exists; `docs/testing.md:188` says 160 presets (actual 161); `README.md:163` lists only 4 of 8 tools; `read-zzz-engine-stats/SKILL.md:146` says 100 presets / 47 S (actual 101 / 48 S). | Patch these counts and statements. If `ep-2259.png` is added, update 398→399 and 100→101 consistently in `README.md`, `docs/project-overview.md`, `docs/directory-layout.md`, `docs/deployment.md`, and `frontend/src/README.md`. |
| P2-6 | Stale `DATA_URL` references: `docs/README.md:70` and `docs/data-schema.md:35` tell `fix-agent` to fix `DATA_URL`, but no `DATA_URL` exists after the Vue migration. `tools/README.md:63` still says `normalize_strategy.py` handles `app.js` data URLs. | Remove `DATA_URL` wording and describe JSON-only references. |
| P2-7 | Stale guard claims: `docs/architecture.md:116` and `docs/data-schema.md:39-40` say `agent-name-mapping.json` has no automatic guard, while `gen_strategy_guides.py` and `test_strategy_data.py` now enforce directory/registry consistency. | Update to describe the actual guard; add a mapping↔preset↔directory test if that specific gap remains. |
| P2-8 | `docs/architecture.md:103` still describes strategy pages as `strategy/<slug>/` static pages. They are Vue-rendered. | Rewrite the row: consumers are `StrategyView` + `renderStrategy.ts`; `strategy/<slug>/` only stores JSON. |
| P2-9 | `utf8_report.json` is a tracked root-level one-off audit artifact referencing old paths (`an-bi.json`, `berise.json`, etc.). It is not referenced by any doc or tool. | Delete it, or move it to `docs/completeds/` with a note. If it is a generated diagnostic, add it to `.gitignore`. |
| P2-10 | `backend/src/zzz_panel/cli.py` defines its own `_fmt`, while `core/fmt.py` says it replaces the old CLI formatter and is the canonical formatting implementation. CLI output therefore lacks the thousands separators used by the web UI. | Replace `cli._fmt` with `core.fmt.fmt` plus explicit `%` handling. |
| P2-11 | UI copy mismatch: `CoreModule.vue:28-30` says “9选2” and “从8项中选2项,” while `CORE_OPTIONS` has 12 entries. This is recorded as a known limitation but is user-facing and easy to fix. | Generate the count from `CORE_OPTIONS.length` or update the copy to “12选2.” |
| P2-12 | `usePanelCalc()` is instantiated twice (`ResultPanel.vue:47`, `CoreModule.vue:20`), causing duplicate debounce timers/requests. `SetEffectModule.vue:43` bypasses `SelectField`. | Share one calculation instance via a store/composable provider, or move the summary calculation into a pure selector. Migrate the set-effect selects to `SelectField` for consistent styling. |
| P2-13 | `renderStrategy.ts` is a 1,200+ line `// @ts-nocheck` monolith with direct `innerHTML` and duplicated mappings. It is now the highest-maintenance frontend file. | Add typed boundaries (`RenderStrategyGuide`) and remove `@ts-nocheck`, or split into `renderHero`, `renderSkills`, `renderCinema`, `renderBuilds`, `renderInteractions`. Add tests around the typed boundary. |
| P2-14 | Node version is documented as 20+ but not enforced (`package.json` has no `engines`, no `.nvmrc`). | Add `engines` and/or `.nvmrc`, or explicitly keep it as a documented soft requirement. |
| P2-15 | All route views are eagerly imported in `router/index.ts`, including the 1,200-line strategy renderer and the generated 60-entry registry. The production main bundle is ~491 KB raw / ~155 KB gzip. This is not a correctness bug, but it makes the launcher pay for the entire strategy feature before the user opens it. | Use route-level dynamic imports for `GuideView`, `StrategyPickerView`, and `StrategyView` (and dynamic-import `html2canvas` with P1-6). Keep `/` and `/calculator` eager if desired. Re-measure the bundle and update `docs/deployment.md` if it documents bundle size. |
| P2-16 | `vite.config.ts:listStrategyDataDirs()` copies **every** directory under `strategy/` that has `data/`, not only published/registered slugs. An unreleased or incomplete agent directory would be shipped in `dist/strategy/...` and be fetchable by URL even though the router does not register it. | Restrict `generateBundle` to released slugs (for example, the intersection of `agent-name-mapping.json`, `agent-presets.json`, and generated registry), or add an explicit `published`/allowlist manifest. Add a build test asserting unregistered directories are not emitted. |
| P2-17 | Five skill scripts use fragile `Path(__file__).resolve().parents[4]` to locate the repo root: `calc_graduation_panel.py:74`, `scrape_agent_guide.py:107`, `refresh_agent_presets.py`, `refresh_disc_presets.py`, `refresh_weapon_presets.py`. If any file moves or the repo is nested differently, the path silently resolves to the wrong directory. | Replace `parents[N]` with a marker-file search: walk up from `__file__` until a `pyproject.toml` or `.git` is found, or use a shared `_repo_root()` utility. Add a smoke test that runs each script with `--help` from a different working directory. |
| P2-18 | The repository carries **~240 MB** of unoptimized PNG images. 28 cinema backdrop files exceed 2 MB each (largest: `ye-shunguang/cinema-2.png` at 2.9 MB). There is no image compression, WebP/AVIF conversion, or responsive-variant pipeline. This bloats the repo and slows Cloudflare asset uploads. | Add a batch image-optimization step (e.g. `sharp`/`pngquant` lossless compression, plus optional WebP variants with `<picture>` fallback). Set a size budget (e.g. ≤1 MB per cinema backdrop). Document the pipeline in `tools/README.md` and run it as part of the strategy-page skill workflow. |
| P2-19 | `GuideView.vue` is a 684-line monolith that hardcodes all guide content (`NAV_GROUPS`, `BASE_ATTRS`, `WEAPON_ATTRS`, `FINAL_ATTRS`) as Vue component constants. Editing guide text requires editing a `.vue` file, which mirrors the pre-migration strategy-page problem where content lived in `app.js`. | Extract guide content to a `data/guide-content.json` or `frontend/src/constants/guideContent.ts` data module. Keep `GuideView.vue` as a pure template that maps data to the existing `GuideSection`/`GuideTable`/`GuideAttrGrid` components. Add a test that validates the data shape. |
| P2-20 | `fix-agent/SKILL.md:89` references `strategy/renderStrategy.ts` but the file lives at `frontend/src/strategy/renderStrategy.ts`. This is a stale path that would send an agent to the wrong location. | Fix the path in `fix-agent/SKILL.md` and add a link check to the proposed `tools/check_docs.py` that validates all backtick-quoted paths in SKILL.md files. |

## 5. Main page entry points and navigation policy

The product main page is the SPA route `/` (`LauncherView`). The repository-root `index.html` is developer documentation and must not be treated as a second product entry point.

### Canonical functional areas

The current primary functional areas are:

1. **Calculator** — `/calculator`
2. **Guide** — `/guide`
3. **Strategy** — `/strategy` (then `/strategy/:slug`)

Developer-only destinations (FastAPI `/docs`, repository docs) are secondary links in documentation, not primary cards on the product main page. If a new user-facing area is added, it must be added to the navigation manifest before it is exposed.

### Required behavior

- Exactly one primary card and one site-nav link per functional area, both generated from `frontend/src/constants/navigation.ts`.
- Internal navigation must use `RouterLink` or `router.push` with a known route name/path. Do not use `<input type="url">`, URL text fields, `window.location =`, `location.href =`, or `location.assign()` for product navigation.
- Do not accept arbitrary `redirect`, `next`, or `returnUrl` query parameters. Existing intentional deep links such as `/strategy/:slug` and the calculator `?mode=` parameter are allowed, but their values must be validated.
- In-page hash links (`#section`) are allowed. External citations are allowed only when they are `https://` and pass the official-host allowlist described in P1-16.
- Unknown paths must redirect to the launcher (or a dedicated 404 view), not render a blank page.
- The launcher title and subtitle should describe the suite (calculator, guide, strategy), not only the calculator.
- User-facing counts on the launcher must be derived from data or a single constants module; they must not be hardcoded twice.

### Required tests

- Every top-level route (except `/strategy/:slug` and the catch-all) has a manifest entry; every manifest entry resolves to a route.
- The launcher renders one card per `showAsCard` entry and the site nav renders one link per `showInNav` entry.
- No URL input or location-based redirect exists in `frontend/src/views` or `frontend/src/components`.
- Unknown path redirects to the launcher; invalid `/strategy/:slug` redirects to the launcher.
- Launcher counts match `data/agent-presets.json` and `data/weapon-presets.json`.
- External hrefs from strategy data reject non-`https` schemes and non-allowlisted hosts.

### Files to change

- Add `frontend/src/constants/navigation.ts`.
- Update `frontend/src/views/LauncherView.vue` to render from the manifest and use data-driven counts.
- Update `frontend/src/router/index.ts` with the catch-all route.
- Update root `index.html` and `docs/directory-layout.md` to clarify that it is developer-only.
- Add/extend `frontend/tests/calculator-view.spec.ts` and `frontend/tests/strategy-ui.spec.ts` for the tests above.

## 6. Documentation rewrite plan

### Rewrite (not patch)

| Document | Action |
| --- | --- |
| `.github/skills/agent-strategy/SKILL.md` | Rewrite to a concise operational procedure. Remove the 60 per-agent dossiers; keep only the workflow, hard rules, schema reference, and 1–2 examples. |
| `docs/structure-review.md` | Rewrite as a historical audit + residual risks, or move to `docs/completeds/`. Remove current-tense claims that are no longer true. |
| `strategy/ye-shunguang/README.md` | Move to `strategy/README.md` and rewrite the schema table from the actual JSON shape. |
| `docs/changelog.md` | Do not rewrite history, but correct the current top entry and split/archive older content by month or by release. |

### Patch (targeted corrections)

`README.md`, `docs/README.md`, `docs/project-overview.md`, `docs/architecture.md`, `docs/directory-layout.md`, `docs/development.md`, `docs/testing.md`, `docs/deployment.md`, `docs/requirements.md`, `docs/api-reference.md`, `docs/calculation-rules.md`, `docs/data-schema.md`, `data/README.md`, `tools/README.md`, `frontend/src/README.md`, `backend/tests/README.md`, `frontend/tests/README.md`, `.github/skills/read-zzz-engine-stats/SKILL.md`, `.github/skills/read-zzz-drive-disc/SKILL.md`, `.github/skills/fix-agent/SKILL.md`.

Navigation-specific documentation updates:

- `docs/requirements.md`: add a functional requirement for one explicit entry per top-level area, internal `RouterLink` navigation, and no URL-input/redirect behavior.
- `docs/architecture.md`: document the navigation manifest, catch-all route, and the rule that only static in-page hash links and validated external citation links may use raw `<a href>`.
- `docs/directory-layout.md`: add `frontend/src/constants/navigation.ts` and clarify that root `index.html` is developer documentation, not the product main page; update the route count from 5 to 6 (including the catch-all).
- `docs/deployment.md`: update the `/` self-check to “one card per functional area”, add the catch-all to the SPA route table, and correct the 100→101 weapon count.
- `docs/testing.md`: add the manifest/router coverage, unknown-route, no-URL-input, launcher-count, and external-URL allowlist tests.

Also fix the absolute Markdown link in `read-zzz-drive-disc/SKILL.md` (`/data/README.md` → `../../../data/README.md`).

## 7. Ordered execution plan

### Phase 1 — Make the repository releasable (P0)

1. Stage `strategy/caesar/`, `frontend/public/images/strategy/caesar/`, and `tools/seed_main_stat_notes.py`.
2. Fix the five missing strategy icons and make `gen_strategy_guides.py` deterministic; regenerate `strategyGuides.ts`.
3. Fix trigger/burnice/yanagi/pyrois/zhao/claret data references.
4. Add the missing `ep-2259.png` (preferred) or document the exception.
5. Add a machine-readable `graduationBuild` spec and a real `--check-all`.
6. Run all six existing data gates plus the new graduation gate. All must exit 0.
7. Correct the changelog top entry with actual results.

### Phase 2 — Enforce architecture boundaries (P1)

8. Move strategy fetching into `src/api/strategy.ts`.
9. Remove the `@data/agent-name-mapping.json` import from `renderStrategy.ts`; add `shortName` to the generated registry.
10. Centralize icon maps and add cross-reference/asset tests.
11. Replace `html2canvas` CDN loading with a self-hosted dependency.
12. Fix API/calculation docs (`3.9` → 422, 12 set options, missing comma).
13. Expand CI with docs/path checks and optional Worker dry-run.
14. Add `frontend/src/constants/navigation.ts`, derive the site nav and launcher cards from it, and add a manifest↔router coverage test.
15. Add the catch-all route, replace the launcher’s hardcoded 100-weapon copy with data-driven counts, and make the launcher title describe the full suite.
16. Remove the hardcoded localhost “open app” link from root `index.html`; mark that file as developer-only documentation.
17. Add the no-URL-input/no-location-redirect guard and the external URL allowlist for strategy source links.

### Phase 3 — Rewrite and repair documentation (P2)

18. Rewrite `agent-strategy/SKILL.md`.
19. Rewrite/move the strategy contract README.
20. Rewrite `docs/structure-review.md`.
21. Patch all count/path/stale-reference issues listed above.
22. Add `tools/check_docs.py` for relative links, counts, stale paths, and generated-file claims.
23. Remove or archive `utf8_report.json`.
24. Split/archive the changelog if time permits.
25. Replace `parents[N]` path resolution in skill scripts with marker-file search (P2-17).
26. Add the image-optimization pipeline and compress existing oversize assets (P2-18).
27. Extract `GuideView.vue` content to a data module (P2-19).
28. Fix the stale path in `fix-agent/SKILL.md` and add SKILL.md link validation to `check_docs.py` (P2-20).

### Phase 4 — Acceptance

Run from the repository root:

```powershell
uv run pytest
cd frontend; npm run test; npm run typecheck; npm run build; cd ..
python tools/sync_presets.py --to-legacy --check
python tools/sync_presets.py --options --check
python tools/bundle_worker_data.py --check
python tools/normalize_strategy.py --check
python tools/gen_strategy_guides.py --check
python tools/seed_main_stat_notes.py --check
python tools/check_docs.py
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all
```

Additional navigation checks:

```powershell
# Must return no matches in product code:
rg "<input[^>]+type=\"url\"|window\.location\s*=|location\.href\s*=|location\.assign\(" frontend/src
# Must return no matches (the developer guide must not hardcode the app URL):
rg "http://localhost:5173" index.html
```

Expected final state:

- Backend `310 passed`, frontend tests (including new navigation tests), typecheck/build clean.
- All data gates exit 0.
- `strategyGuides.ts` is exactly generator output; no manual icon edits.
- Every strategy image/weapon/disc/team reference resolves.
- A clean clone passes CI without untracked files.
- The main page has exactly one card and one nav link per top-level functional area, sourced from the navigation manifest.
- Unknown paths and invalid strategy slugs return the user to the launcher; no route renders a blank page.
- No URL input, arbitrary `redirect`/`next` parameter, or location-based redirect exists in product navigation.
- Launcher counts match the data (60 agents, 101 weapons).
- Root `index.html` is clearly developer-only and does not hardcode the app URL.
- Docs contain no current-state references to `DATA_URL`, removed `app.js`/`styles.css` templates, non-existent `tools/check.ps1`, or incorrect counts.
- No changes to `frontend/tests/fixtures/legacy-calculator/` at any point.

## 8. Constraints

- Do not modify anything under `frontend/tests/fixtures/legacy-calculator/`; it is the three-way parity baseline.
- Keep `data/` as the only authoritative calculator data source.
- Keep `strategy/<slug>/` data-only after moving the contract README.
- Keep all image references in the form `/images/...` under `frontend/public/images/`.
- The product main page is `/` (`LauncherView`); root `index.html` is developer-only documentation. Do not add URL-input or arbitrary redirect fields to product navigation.
- Do not hand-edit generated files: `strategyGuides.ts`, fixture `data/*.js`, or `_bundled_data.py`.
