---
name: do_calculatorModel
description: Read an agent's official level-60 stats and core bonuses, then add a tagged preset with the correct calculation mode to the unified ZZZ calculator.
---

# Add an Agent Preset to the Unified Panel Calculator

Use this skill when the user provides:

1. An agent name.
2. A desired calculator mode: standard (普通), special-break (命破), or sharp-guard (锋御). If the mode is omitted and cannot be determined from the request, ask which mode to use.

The repository has one unified calculator, currently `frontend/legacy/pages/calculator.html`. Add the agent to that calculator regardless of mode: selecting its preset applies the corresponding final-panel calculation. Do not create or update a separate calculator page for each mode.

## Read verified agent data

Use the `read-zzz-agent-stats` skill procedure and the official HoYoLAB ZZZ Wiki. Find the exact matching agent from the Wiki index; read the initial and level-60 promotion tables, merge them field by field, and inspect every core rank A–F individually. Never infer missing values from another agent or assume a universal core-rank pattern.

If the official source is unavailable, the agent match is ambiguous, or any required stat/rank effect cannot be verified, stop before adding a guessed preset. Report the specific missing data and ask for what is needed.

## Identify the unified calculator and preset architecture

Use the unified calculator and its external preset data rather than guessing filenames:

Inspect `frontend/legacy/pages/calculator.html`, `frontend/legacy/scripts/calculator.js`, `frontend/legacy/scripts/calculator-config.js`, `frontend/legacy/data/agent-presets.js`, and the current calculation-mode handling. Preset data belongs in the separate JavaScript data file, not embedded as a large object in calculator HTML.

The pages above live under `frontend/legacy/` and are the pre-Vue3 native implementation kept for reference during migration. The Vue3 replacement is planned under `frontend/src/` with the calculation rules moving to `backend/src/zzz_panel/core/`; until that migration lands, edit the legacy files only.

## Add accurate, maintainable preset data

Store for each agent:

- Stable ID and display name.
- The verified in-game profession/tag shown on the official Wiki (for example, `强攻` or `异常`), used in the preset selector.
- `panelMode`: `standard`, `rupture`, or `fengyu`, corresponding to the user-requested calculator mode. Profession/tag and calculation mode are distinct fields; do not infer 命破/锋御 mode solely from the agent's profession.
- Official Wiki detail URL.
- Level-60 base stats excluding core: HP, ATK, DEF, impact, CR, CD, anomaly control, anomaly proficiency, PEN ratio, and energy regen, where available.
- Any agent-specific base attributes shown by the Wiki (for example, a 命破 agent's base 贯穿力 or special energy accumulation) must be stored as additional base stats when the calculator has corresponding fields. Mark standard stats absent from the Wiki explicitly as unavailable rather than silently substituting another attribute or guessing.
- In 锋御 mode, the calculator's energy-regen field represents 锐能自动累积; use the official 锐能自动累积 base value there and show the 锋御-specific label throughout the calculator.
- If a displayed base attribute has no corresponding calculator input, record it in `unmodeledBaseStats` and show the user that it is not included in calculations; do not map it to a different attribute.
- Core ranks A–F mapped to their verified effect, distinguishing flat base-stat additions from percentages.
- Aggregate bonuses in the exact shape the target calculator can apply.

Use a clear mapping between Wiki attributes and the calculator's existing field/core-option IDs. Preserve percentage units and distinguish base attack/defense from flat additions applied elsewhere. A core bonus may use `optionCount` to repeat an existing manual core option when its exact value equals `option.value × optionCount`; omitted `optionCount` means 1. The expanded entries must still fill exactly the two core selectors, and the ranks/per-rank value must sum to the aggregate.

Before implementation, verify that the target calculator can represent the agent's complete A–F total exactly. If it cannot, extend the calculator's core-preset handling in a type-safe, minimally invasive way so the preset still applies accurately; do not silently approximate, discard an effect, or force an incorrect option. Keep manual core selection working.

Each `roleTag` must be the agent's specific official profession label. Do not use calculation-mode labels such as `通用` as role tags. The calculator derives a deduplicated first-stage tag selector from `roleTag`, then only displays agents belonging to the selected tag in the second-stage selector. Validate that every preset has a unique ID, name, and recognized, non-empty role tag so no agent is omitted or reachable without first choosing its tag.

## Preset selection behavior

Agent presets use a mandatory two-stage selector: choose a specific `roleTag`, then choose an agent from that tag's filtered list. Do not expose the full agent list before the tag is selected, and do not add a direct “all agents” shortcut.

Selecting the agent must:

1. Fill all available base-panel inputs with the verified level-60 values, excluding core bonuses.
2. Apply that agent's verified fully upgraded A–F core bonuses without double-counting them in the base panel.
3. Show the agent name, that core bonuses are fully upgraded, rank-to-effect/total information, and an external link to the official Wiki source.
4. Activate the preset's `panelMode` and immediately show the corresponding final-panel formula; non-special agents use standard calculations, 命破 uses `0.3 × final ATK + 0.1 × final HP` for penetration force, and 锋御 uses actual CR.
5. Recalculate the result immediately and surface a visible error if preset data is malformed or unsupported.

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

- The new agent appears in the preset selector with its profession/tag and calculation-mode label.
- Selecting it fills every base stat and applies each core aggregate to the correct field exactly once.
- Selecting it activates the requested panel mode: standard, 命破, or 锋御. The two special formulas must be mutually exclusive and hidden for standard agents.
- The final panel recalculates and the source link points to the official Wiki page.
- Engine/weapon values, drive-disc main stats, and substat counts remain unchanged when switching presets.
- All two-piece set selectors reset to “请选择” when switching presets, and “无” remains selectable.
- The empty initial state retains the blank defaults and the set option “无”.
- Manual core selection still works.

Run a syntax check for any external JavaScript data and inline scripts touched, plus `git diff --check`. Report the files changed, the Wiki source, the verified base/core values, and validation results.

## Example invocation

“Use `do_calculatorModel` to add 叶瞬光 in standard mode to the unified calculator.”

Expected behavior: reread/verify 叶瞬光 and its profession/tag using `read-zzz-agent-stats`; add the verified 60-level base panel, A–F totals, tag, and `panelMode: 'standard'` to the external preset data; then test the tagged preset, mode, and untouched loadout fields in the unified calculator.
