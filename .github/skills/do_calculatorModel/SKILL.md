---
name: do_calculatorModel
description: Read an agent's official level-60 stats and core bonuses, then add a tagged preset with the correct calculation mode to the unified ZZZ calculator.
---

# Add an Agent Preset to the Unified Panel Calculator

Use this skill when the user provides:

1. An agent name.
2. A desired calculator mode: standard (通用), special-break (命破), or sharp-guard (锋御). If the mode is omitted and cannot be determined from the request, ask which mode to use.

The repository has one unified calculator, now the Vue3 app at `frontend/src/` (page `frontend/src/views/CalculatorView.vue`, route `/calculator`, served by Vite on `http://localhost:5173`). Add the agent to that calculator regardless of mode: selecting its preset applies the corresponding final-panel calculation. Do not create or update a separate calculator page for each mode.

## Read verified agent data

Use the `read-zzz-agent-stats` skill procedure and the official HoYoLAB ZZZ Wiki. Find the exact matching agent from the Wiki index; read the initial and level-60 promotion tables, merge them field by field, and inspect every core rank A–F individually. Never infer missing values from another agent or assume a universal core-rank pattern.

If the official source is unavailable, the agent match is ambiguous, or any required stat/rank effect cannot be verified, stop before adding a guessed preset. Report the specific missing data and ask for what is needed.

## Identify the unified calculator and preset architecture

Use the unified calculator and its external preset data rather than guessing filenames:

Inspect `data/agent-presets.json` (the single source of truth), `backend/src/zzz_panel/presets/` for how it is loaded and validated, `backend/src/zzz_panel/core/modes.py` for the calculation-mode handling, and `frontend/src/components/calculator/AgentBaseModule.vue` for the UI that consumes presets (the picker plus the success note; the base-panel numeric fields below it are hand-edited and never written by a preset alone). Preset data belongs in its own JSON data file, not embedded as a large object in a component.

The Vue3 migration is complete: the calculator lives in `frontend/src/`, the calculation rules live in `backend/src/zzz_panel/core/`, and presets are served by `GET /api/presets/agents` (plural). The pre-Vue3 native implementation has been deleted, except for a **read-only reference fixture** at `frontend/tests/fixtures/legacy-calculator/` that the parity tests compare against. Never edit anything under `tests/fixtures/` — changing the baseline makes the comparison compare the implementation with itself.

## Add accurate, maintainable preset data

Store for each agent:

- Stable ID and display name.
- The verified in-game profession/tag shown on the official Wiki (for example, `强攻` or `异常`), used in the preset selector.
- `panelMode`: `standard`, `rupture`, or `fengyu`, corresponding to the user-requested calculator mode. Profession/tag and calculation mode are distinct fields; do not infer 命破/锋御 mode solely from the agent's profession.
- Official Wiki detail URL.
- Level-60 base stats excluding core: HP, ATK, DEF, impact, CR, CD, anomaly control, anomaly proficiency, PEN ratio, and energy regen, where available.
- Any agent-specific base attributes shown by the Wiki (for example, a 命破 agent's base 贯穿力 or special energy accumulation) must be stored as additional base stats when the calculator has corresponding fields. Mark standard stats absent from the Wiki explicitly as unavailable rather than silently substituting another attribute or guessing.
- In 锋御 mode, the calculator's energy-regen field represents 锐能自动累积; use the official 锐能自动累积 base value there and show the 锋御-specific label throughout the calculator.
- If a displayed base attribute has no corresponding calculator input, record it in `unmodeledBaseStats` and show the user that it is not included in calculations; do not map it to a different attribute. Exception: `锐暴伤害` is already modeled as a fixed 150% intrinsic stat shown only in the 锋御 final panel. Do not give it a calculator input and never report it as unmodeled.
- Core ranks A–F mapped to their verified effect, distinguishing flat base-stat additions from percentages.
- Aggregate bonuses in the exact shape the target calculator can apply.

Use a clear mapping between Wiki attributes and the calculator's existing field/core-option IDs. Preserve percentage units and distinguish base attack/defense from flat additions applied elsewhere. A core bonus may use `optionCount` to repeat an existing manual core option when its exact value equals `option.value × optionCount`; omitted `optionCount` means 1. The expanded entries must still fill exactly the two core selectors, and the ranks/per-rank value must sum to the aggregate.

Before implementation, verify that the target calculator can represent the agent's complete A–F total exactly. If it cannot, extend the calculator's core-preset handling in a type-safe, minimally invasive way so the preset still applies accurately; do not silently approximate, discard an effect, or force an incorrect option. Keep manual core selection working.

Each `roleTag` must be the agent's specific official profession label. Do not use calculation-mode labels such as `通用` as role tags. The calculator groups every preset by `roleTag` into the first level of its cascader selector, keeping the group order fixed by `AGENT_ROLE_TAGS` and the in-group order identical to `data/agent-presets.json`. Validate that every preset has a unique ID, name, and recognized, non-empty role tag so no agent is omitted or hidden inside an empty group.

## Preset selection behavior

Agent presets use a single searchable, clearable `n-cascader`, structurally identical to the W-Engine picker: level 1 is a `roleTag` group, level 2 is the agent itself. There is **no separate tag dropdown and no "choose a tag first" gate** — the user picks the tag and the agent in one action, and picking the agent determines `agent.roleTag`. Do not reintroduce a disabled-until-tag-chosen second dropdown, and do not add a direct "all agents" shortcut.

Option labels are built by `agentOptionLabel` in `frontend/src/stores/panelStore.ts` as 「名称 / 职业 / 属性 / 评级」. The shared segments come from `agentTagSegments` in `frontend/src/constants/calculatorOptions.ts`, which is also what the agent card's sub-line and the load-success note render, so the three surfaces cannot drift apart. The panel-mode name is folded into the same segments: 命破/锋御 agents' `roleTag` already equals their mode name, so it is deduplicated, and the 通用 mode name is hidden entirely (see below) — either way the label is always four segments. While browsing, a leaf shows only the agent's name via the shared `renderLabel` in `composables/useCascaderIcons.ts`; the full label stays on the option so the collapsed box and `filterable` search still show it after selection, and typing an attribute (「玄墨」) or a grade (「S」) matches.

Selecting the agent must:

1. Fill all available base-panel inputs with the verified level-60 values, excluding core bonuses.
2. Apply that agent's verified fully upgraded A–F core bonuses without double-counting them in the base panel.
3. Show the agent name, that core bonuses are fully upgraded, rank-to-effect/total information, and an external link to the official Wiki source.
4. Activate the preset's `panelMode` and immediately show the corresponding final-panel formula; non-special agents use standard calculations, 命破 uses `0.3 × final ATK + 0.1 × final HP` for penetration force, and 锋御 uses actual CR.
5. Recalculate the result immediately and surface a visible error if preset data is malformed or unsupported.

The component chains two existing actions in a fixed order — `panelStore.selectAgentRole(agent.roleTag)` then `useAgentPreset().applyAgentPreset(agent.id)` — because `selectAgentRole` resets `panelMode` back to `requestedMode` while `applyAgentPreset` writes the agent's real mode. Keep that order; reversing it leaves the panel on the wrong formula. Do not fold the load logic into the store. Clearing the picker only needs `selectAgentRole('')`, which already clears the preset id, restores the base panel/core/two-piece sets, falls back the panel mode, and resets the W-Engine.

`通用` is hidden from all agent-facing text by `HIDE_STANDARD_MODE_LABEL` in `frontend/src/constants/calculatorOptions.ts`, reached through `panelModeTagLabel()`. This is display-only: `panelMode` is still written as `'standard'` and all three modes' formulas are unchanged. Do not "fix" this by deleting the `standard` key from `PANEL_MODE_LABELS` — `useAgentPreset` uses that table to validate `panelMode`, and removing the key breaks every standard agent. Flip the constant to restore the text.

When an agent preset is imported or cleared, reset the selected W-Engine to “请选择” and clear its read-only base-ATK and fixed-substat values to zero. Drive-disc main stats and substat counts belong to the user's build and must be preserved. Reset all three two-piece set selectors to “请选择” whenever an agent preset is imported so the user can re-evaluate the set choices for that agent. Keep the distinct “无” option available.
For 命破 mode, hide the standard base PEN-ratio and energy-regen inputs, and show the agent-specific base penetration-force and special energy-accumulation fields. For standard and 锋御 modes, show the PEN-ratio and energy-regen inputs and hide the 命破-only fields.

When the calculator starts with no agent selected, preserve the established blank build defaults:

- Weapon/engine base value, engine substat value, and all drive-disc substat counts start at zero.
- Engine substat and disc 4/5/6 main-stat selectors start at “请选择”.
- Core selectors start at “请选择” until an agent preset is selected or the user chooses core manually.
- Disc 1/2/3 fixed main stats remain active.
- Two-piece set selectors start at “请选择” and retain a distinct “无” option.

Selecting an agent must not auto-fill equipment or disturb the blank build defaults.

## Validation

Use the browser or an equivalent DOM test to verify in the requested calculator that:

- The new agent appears in the preset selector under its profession/tag group, with the four-segment label 「名称 / 职业 / 属性 / 评级」 (e.g. 「仪玄 / 命破 / 玄墨 / S级」) that contains no `通用`. The attribute and grade shown must be the ones read from the official page for that agent.
- Selecting it fills every base stat and applies each core aggregate to the correct field exactly once.
- Selecting it activates the requested panel mode: standard, 命破, or 锋御. The two special formulas must be mutually exclusive and hidden for standard agents.
- The final panel recalculates and the source link points to the official Wiki page.
- Engine/weapon values, drive-disc main stats, and substat counts remain unchanged when switching presets.
- All two-piece set selectors reset to “请选择” when switching presets, and “无” remains selectable.
- The empty initial state retains the blank defaults and the set option “无”.
- Manual core selection still works.
- The agent's PNG exists at `frontend/public/images/agents/<id>.png`; a missing file must degrade to text only, never a broken-image box.

Two testing traps apply to this picker: jsdom renders no cascader options at all (they live in an `n-virtual-list` with zero measured height), so assert through `findComponent(NCascader).props('renderPrefix')` / `props('renderLabel')` or against the `panelStore` getters, never against `.n-cascader-option` DOM. And the page now has **two** cascaders (agent and W-Engine), so locate them by `.agent-picker-input` / `.weapon-picker-input` — a bare `findComponent(NCascader)` returns whichever rendered first.

Run the preset-schema tests (`uv run pytest backend/tests/test_presets.py`) and the frontend suite (`npm run test` in `frontend/`) after changing preset data, plus `git diff --check`. `npm run test` includes a three-way parity test that compares the Vue3 page, the Python backend, and the read-only legacy fixture; it must stay green, which means the preset must be added through the normal JSON pipeline rather than by editing anything else. Note that the parity spec drives the Vue side through `selectAgentRole` + `applyAgentPreset` rather than the UI, so option-label changes never reach it.

Because editing `data/agent-presets.json` changes a deployed input, also refresh the downstream generated artifacts before shipping:

```
python tools/sync_presets.py --to-legacy        # 对拍夹具的 JS 包装
python tools/bundle_worker_data.py              # Worker 编译产物，Cloudflare 部署硬闸
python tools/bundle_worker_data.py --check      # 漂移闸，退出码非 0 = 产物已过期
```

`bundle_worker_data.py` recompiles `data/agent-presets.json` and `data/weapon-presets.json` into `backend/src/zzz_panel/_bundled_data.py`. `pywrangler` uploads only `.py` files, so without it a newly added agent is silently absent in production: the live `/api/presets/*` still serves the previous data (or returns 503 when no generated module exists at all). The module is a build artifact and is gitignored, so nothing else catches the omission.

Report the files changed, the Wiki source, the verified base/core values, and validation results.

## Example invocation

“Use `do_calculatorModel` to add 叶瞬光 in standard mode to the unified calculator.”

Expected behavior: reread/verify 叶瞬光 and its profession/tag using `read-zzz-agent-stats`; add the verified 60-level base panel, A–F totals, tag, and `panelMode: 'standard'` to the external preset data; then test the tagged preset, mode, and untouched loadout fields in the unified calculator.

## Frontend files this skill touches

| File | Role |
| --- | --- |
| `data/agent-presets.json` | **the only file to edit** for a new agent |
| `frontend/src/components/calculator/AgentBaseModule.vue` | picker + success note; reads presets, never hardcodes them |
| `frontend/src/stores/panelStore.ts` | `agentPresetGroups` (cascader options), `selectedAgent` (avatar card), `agentOptionLabel` (label text) |
| `frontend/src/composables/useAgentPreset.ts` | `applyAgentPreset` validation + load, `agentTagLabel` (note/card text) |
| `frontend/src/constants/calculatorOptions.ts` | `AGENT_ROLE_TAGS`, `PANEL_MODE_LABELS`, `HIDE_STANDARD_MODE_LABEL` |
| `frontend/src/composables/useCascaderIcons.ts` | shared `renderPrefix` / `renderLabel`; `ROLE_ICON` roletag→PNG slug map |
| `frontend/public/images/agents/` | one `<id>.png` per agent |
