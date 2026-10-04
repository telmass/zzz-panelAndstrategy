---
name: read-zzz-agent-stats
description: Read a named Zenless Zone Zero agent's level-60 base panel and fully upgraded core-skill bonuses from the official HoYoLAB Wiki.
---

# Read ZZZ Agent Stats

Use this skill when the user gives an agent's name and asks to read the two stat groups used by the panel calculators:

1. The level-60 base panel, excluding core-skill bonuses.
2. The total bonus from fully upgrading core skill nodes A through F.
3. The agent's official profession/role label (职业), such as 强攻 or 异常, when preparing data for a calculator preset.
4. The agent's official grade (评级, `S` or `A`) and attribute (属性, such as 火 or 烈霜), when preparing data for a calculator preset.

## Source

Use the official HoYoLAB ZZZ Wiki:

- Agent index: <https://baike.mihoyo.com/zzz/wiki/channel/map/2/43>
- Agent detail pages are linked from the index. Find the card whose exact title/name matches the requested agent and follow its detail URL; do not assume a fixed content ID.

Prefer the browser tools for the dynamic page and its sliders. If the page cannot be accessed or a control cannot be operated, report that limitation and the data actually visible. Never fill gaps by guessing or by substituting third-party values without clearly asking permission.

## Reading the level-60 base panel

1. Open the agent detail page from the official agent index.
2. Find the slider in the **晋升需求** section. It controls the base-stat table.
3. Move the slider to **初始** and record every displayed base stat.
4. Move the same slider to **满级** (agent level 60) and record every displayed stat.
5. Construct the level-60 base panel without core bonuses by starting with the initial table and replacing each attribute that has a displayed level-60 value with that level-60 value. Attributes absent from the max-level table retain their initial value. This is a field-by-field merge, not a difference or sum of the two panels.
6. Report all available fields, preserving units and whether each value is flat or a percentage. Include both initial and max-level observations when they help explain the merge.

Use the slider's rendered mark labels and actual position to operate it. A slider can be off-screen or horizontally displaced in a wide viewport; scroll it into view and use its rail geometry to drag the thumb to the requested mark. Re-read the table after every move to confirm the selected mark and data.

## Reading fully upgraded core-skill bonuses

1. Locate **技能展示 → 核心技** and find its A–F upgrade slider.
2. Read the effect at each rank A, B, C, D, E, and F individually. Confirm the rank shown and the corresponding effect text before recording it.
3. Sum bonuses for matching attributes across the six ranks. State the per-rank mapping as well as the total. Do not assume a universal alternating pattern; verify each rank on the requested agent's page.
4. Distinguish base-stat bonuses (for example, 基础攻击力 +25) from percentage bonuses (for example, 暴击率 +4.8%). Keep these bonuses separate from the level-60 base panel.

## Output

When available, record the exact **职业** label from the official agent profile separately from the agent's element/attribute. This role label is for display in the calculator preset selector and does not determine whether the calculator uses standard, 命破, or 锋御 formulas.

Present the result in three clearly separated groups:

### Agent profession/tag

List the exact official Wiki profession label (职业), distinct from the element/attribute.

### Level-60 base panel (excluding core)

List each attribute and value.

### Fully upgraded core skill (A–F total)

Show each rank's effect and a summed total grouped by attribute and bonus type.

Include a source link to the official agent detail page. Be explicit about any field that was unavailable, ambiguous, or could not be verified. Do not modify calculator files unless the user separately requests an implementation.

## Reading the grade and the attribute

`scripts/refresh_agent_presets.py` reads both from the same `role_base_info` component that
carries the name and the 特性 tag, so a browser pass is not needed for them:

- **评级 `grade`** — `role_base_info.grade`, verbatim. Agents only use `S` and `A`.
  Write whatever the Wiki says: a new grade must reach `data/agent-presets.json` and be
  rejected by the backend whitelist, not vanish silently at scrape time.
  `GRADE_ORDER` in the script is for **sorting only** (S before A).
- **属性 `role_attribute`** — an English slug, translated through the script's
  `ATTRIBUTE_LABELS`:

  | slug | 页面显示 | slug | 页面显示 |
  | --- | --- | --- | --- |
  | `fire` | 火 | `frost` | 烈霜 |
  | `ice` | 冰 | `auricink` | 玄墨 |
  | `electric` | **电** | `honed_edge` | 凛刃 |
  | `ether` | 以太 | `wind` | 风 |
  | `physical` | 物理 | `Lumiflux` | 流明 |

  Copy the page's own wording. `electric` is **电** on the official site even though the
  community says 雷, and 凛刃 stays 凛刃 even though the page itself calls it a
  higher-tier form of 物理. An unregistered slug makes the script **skip that agent** and
  name it in the `SKIPPED:` report — never guess a special attribute into a regular one.

The script fails an agent whose page carries no grade, so a missing field is reported
rather than written as an empty string.

## What counts as a special attribute

**An attribute is special if and only if exactly one agent currently holds it.**

That single condition is the whole rule. Do not add further conditions, and do not
hardcode the current answers (烈霜 / 玄墨 / 凛刃 / 流明): a hardcoded list goes stale the
moment the next single-holder attribute appears, and it also breaks in the other
direction — 风 currently has two holders and is therefore **not** special.

The answer is derived from the data, so it changes as the roster grows. Re-derive it on
every use instead of caching. Implementations, both unit-tested:

- backend `backend/src/zzz_panel/presets/attributes.py` → `special_agent_attributes()`
- frontend `frontend/src/composables/useAgentPreset.ts` → `specialAgentAttributes()`

## Batch refresh of `data/agent-presets.json`

`scripts/refresh_agent_presets.py` performs the same reads without a browser. It scans
`entry_page_id=1..2600` on `https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id=<id>`
and keeps every page that exposes a `role_base_info` component, which currently yields 60 agents.

Run from the repository root; the default `--config` and `--out` paths are repo-root relative.

```
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python tools/sync_presets.py --to-legacy
```

`data/agent-presets.json` is the single source of truth for the whole repository. The
parity fixture's `frontend/tests/fixtures/legacy-calculator/data/agent-presets.js` is
generated from it by `sync_presets.py --to-legacy`; never write that file from this
script. After a refresh, run that command so the fixture stays in sync, and
`python tools/sync_presets.py --to-legacy --check` must exit 0.

`--config` defaults to
`frontend/tests/fixtures/legacy-calculator/scripts/calculator-config.js`, which the
script parses for core-option values. That file is the pre-migration option table and is
now the only remaining consumer of the old format; keep its formatting intact, or the
regex parse fails silently.

- The level-60 panel comes from the 晋升需求 slider rows 初始/满级, merged field by field.
- Legacy labels are normalized (`生命/攻击/防御`, `暴击/暴伤`, `异常掌控`, `基础能量自动回复提升0.12点/秒`).
- 命破 agents put `贯穿力` into `additionalBaseStats.penforce` and `闪能自动累积` into `additionalBaseStats.energyAccumulation`; missing `pr`/`er` are listed in `unavailableBaseStats`.
- 锋御 agents put `锐能自动累积` into `base.er`. `锐暴伤害` is already modeled by the calculator: it is a fixed 150% intrinsic stat displayed only in the 锋御 final panel, never as a calculation input. The scraper still writes the Wiki label into `unmodeledBaseStats` for traceability, and the calculator filters it out via `MODELED_BASE_STAT_LABELS`; never describe it to the user as unmodeled. Only genuinely unmodelled attributes belong there.
- Core ranks are read per rank letter and only `A`–`F` are accepted; older pages also emit empty `2..6` entries.
- Presets are written sorted by official grade (S before A) then by id. Serialization reuses `tools/sync_presets.py`, so the output is canonical and byte-deterministic: a rerun must reproduce the same file.

## Verified example: 叶瞬光

This example records the browser-read values confirmed by the user; it also serves as a process sanity check, not as a substitute for rereading the requested agent's page.

- Initial base panel: HP 617, ATK 135, DEF 49, Impact 83, CR 5%, CD 50%, Anomaly Mastery 94, Anomaly Proficiency 93, PEN Ratio 0%, Energy Regen 1.2.
- Level-60 displayed values: HP 7673, ATK 863, DEF 606.
- Merged level-60 base panel without core: HP 7673, ATK 863, DEF 606, Impact 83, CR 5%, CD 50%, Anomaly Proficiency 94, Anomaly Mastery 93, PEN Ratio 0%, Energy Regen 1.2.
- Core ranks A/C/E each give CR +4.8%; ranks B/D/F each give base ATK +25. Full-core totals: CR +14.4% and base ATK +75.
