---
name: fix-agent
description: Fix a single ZZZ agent's strategy page references using its Chinese name — resolve slug from data/catalog/agent-index.json, attribute/roleTag/grade from data/catalog/agents.json, then align strategy/<slug>/ folder, data JSON icon references, and regenerate strategyGuides.ts.
---

# ZZZ Agent Reference Fixer (fix-agent)

> 🧭 本 skill 是 `get-agent-strategy` 的子流程，通常由它编排调用；单独使用同样有效。
> 共享规则见 [`_shared/naming.md`](../_shared/naming.md)。

Fix references for **one agent at a time**. Input: the agent's Chinese name (short or full, e.g. `克拉蕾` or `克拉蕾·弗林特`).

## Base directory

Repository root. Relative paths are relative to the repo root.

> ✅ The canonical reference implementation is `strategy/ye-shunguang/`; its data files
> are named `ye-shunguang.json` / `ye-shunguang.strategy.json`. Use
> `data/catalog/agent-index.json` as the source of truth for new or renamed references;
> do not create another alias.

## Attribute / role / grade maps

属性 / 职业 / 评级 → 图标 slug 的映射表见 [`_shared/naming.md`](../_shared/naming.md)（唯一事实源，不在此处重复）。

Grade icon file name is the grade lowercased (`S` → `s.webp`, `A` → `a.webp`).

**All strategy-specific image filenames must be lowercase**: `film.webp`, `tachie.webp`, `background.webp`, `cinema-2.webp`, `cinema-3.webp`. JSON URL casing must match disk filenames exactly (Cloudflare CDN is case-sensitive).

## Workflow

### Step 1 — Resolve canonical slug, attribute, roleTag, grade

1. Read `data/catalog/agent-index.json`. Find the entry whose `cn_short` or `cn_full` equals the given Chinese name. Record `slug` and `en`.
2. Read `data/catalog/agents.json`. Find the entry whose `name` equals the given Chinese name (or `cn_full`). Record `id` (agentId), `attribute`, `roleTag`, `grade`.
3. Convert: `attribute` → English via the attribute map; `roleTag` → English via the role map; `grade` → lowercase for the icon file name.

**Slug 唯一性与映射表优先**：`data/catalog/agent-index.json` 中的 `slug` 是唯一正确的规范命名。若发现文件夹名、数据文件名、`strategyGuides.ts` 中的 `slug` 字段等与 mapping 的 `slug` 出现相似但不完全一致的情况（如 `orphe-magus` 与 `orphie-magus`），必须以 mapping 的 `slug` 为准，**不可改动 mapping**，而应将其他所有位置统一为 mapping 中的 `slug`。

### Step 2 — Regenerate `frontend/src/constants/strategyGuides.ts`

Do not hand-edit the registry. After Step 1 (and Step 4 if data paths changed), run:

```powershell
python tools/gen_strategy_guides.py
python tools/gen_strategy_guides.py --check
```

The generator reads `data/catalog/agent-index.json` + `strategy/<slug>/data/<slug>.json`
and writes `slug` / `name` / `en` / `agentId` / `tachie` / icons. If the generated entry
has a wrong icon, fix `profile.icons` in the scraped JSON first, then regenerate.

### Step 3 — Fix tachie path

Ensure `tachie:` (and any tachie reference) is `/images/strategy/<slug>/tachie.webp`. Verify `frontend/public/images/strategy/<slug>/tachie.webp` exists; if the folder is named with an old slug, rename it (Step 4).

### Step 4 — Fix the strategy page

1. **Folder name**: `strategy/<slug>/` must exist. If an old folder (e.g. from a previous slug) holds this agent's data, rename it to `strategy/<slug>/`. Likewise rename `frontend/public/images/strategy/<old>/` → `frontend/public/images/strategy/<slug>/`.
2. **Data file names**: inside `strategy/<slug>/data/`, files must be `<slug>.json` and `<slug>.strategy.json`. Rename `<old>.json` / `<old>.strategy.json` if present.
3. **`data/<slug>.json`**: fix `profile.icons`:
   - If `profile.icons` is missing entirely, add it as an object under `profile`.
   - `profile.icons.attribute` → `/images/attributes/<attribute-slug>.webp`
   - `profile.icons.profession` → `/images/icons/<role-slug>.webp` (may be left empty; the shared renderer falls back to the role icon map)
   - `profile.icons.grade` → `/images/grades/<grade_lower>.webp`
   - `profile.icons.title` → specific path or `""` if no title image.
   - Replace any `/images/strategy/<old>/...` path with `/images/strategy/<slug>/...`.
   - **`cinemaBackdrops`**: 确保非空（不为 `{}`）；每个 level 的 `image` 必须为 `/images/strategy/<slug>/cinema-N.webp`（1-3 命用 `cinema-2.webp`，4-6 命用 `cinema-3.webp`），对应图片文件必须存在于 `frontend/public/images/strategy/<slug>/`；缺失则按 `seed` 格式补全 `image`/`imageRemote`。
   - **JSON 有效性**：用 `python -c "import json; json.load(open('strategy/<slug>/data/<slug>.json',encoding='utf-8'))"` 校验；若报 `UnicodeDecodeError`/`JSONDecodeError`（UTF-8 损坏或控制字符），重新运行 agent-strategy Step 1 抓取脚本覆盖该文件，抓取完成后重新执行本节的图标修正与 cinemaBackdrops 修正。
   - **检查该文件中所有 `/images/strategy/<folder>/...` 引用，确保 `<folder>` 等于 `<slug>`；不一致则修正。**
   - Ensure `profile.attribute`, `profile.roleTag`, `profile.grade` match the preset values.
4. **`data/<slug>.strategy.json`**: replace any stale `<old>` slug references in `note`/`editorialSources`/paths with `<slug>`.
   - **JSON 有效性**：同样用 `python -c "import json; json.load(...)"` 校验；损坏时从 `strategy/ye-shunguang/data/ye-shunguang.strategy.json` 复制模板后按 agent-strategy skill 填充，而非手改。
   - **检查该文件中所有 `/images/strategy/<folder>/...` 引用，确保 `<folder>` 等于 `<slug>`；不一致则修正。**
   - **若存在 `cinemaPriority.image`，确保文件名全小写**（如 `film.webp`，不是 `Film.webp`）；同时确认 `frontend/public/images/strategy/<slug>/` 下的磁盘文件名与 JSON 引用大小写一致。
5. **Rendering is shared.** There is no per-agent `app.js` / `index.html` / `styles.css`.
   `StrategyView.vue` + `frontend/src/strategy/renderStrategy.ts` read the JSON and fall back to the
   role icon map when `profile.icons.profession` is empty. Fix the data, not a page copy.
6. **Image folder**: `frontend/public/images/strategy/<slug>/` must exist with `tachie.webp` (and `title.webp`/`cinema-*.webp` if available).

### Step 5 — Verify

1. `grep -r "<old-slug>" strategy/<slug>/ frontend/src/constants/strategyGuides.ts` returns no results.
2. `profile.icons.attribute` and `profile.icons.profession` in `data/<slug>.json` point to existing files.
3. Both `data/<slug>.json` and `data/<slug>.strategy.json` pass `python -c "import json; json.load(...)"`.
4. `python tools/normalize_strategy.py --check`, `python tools/gen_strategy_guides.py --check`, `python tools/sync_manifest.py --check` and `python tools/bundle_worker_data.py --check` all exit 0.
5. Run `npm run build --prefix frontend` and `npm run test --prefix frontend`.

## Notes

- Fix only the single target agent; do not touch other agents.
- Do not hand-edit `graduationPanel`/`graduationPanelAlt` in `<slug>.strategy.json`.
- Attribute/role icon consistency: `attributeIcon`/`roleIcon` in `strategyGuides.ts` must match `profile.attribute`/`profile.roleTag` in `data/<slug>/data/<slug>.json`.
- If `<slug>.strategy.json` is missing, copy `strategy/ye-shunguang/data/ye-shunguang.strategy.json` as a template and fill per the agent-strategy skill.
- This skill only fixes references; it does not author editorial content.
