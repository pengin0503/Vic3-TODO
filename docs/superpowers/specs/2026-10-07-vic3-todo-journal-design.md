# Victoria 3 TODO Journal — Design Specification

Date: 2026-10-07  
Target: Victoria 3 1.14.x, baseline verification on 1.14.5  
Repository: `pengin0503/Vic3-TODO`  
Status: Approved

> **2026-10-10 update:** the free-text gate was resolved with evidence from an in-game 1.14.5 test by another mod: a mod editbox cannot reach script, but the base game's company-rename popup can. The production mod is implemented in `mod/Vic3TODO` and goes beyond this v1 scope (a real Journal Entry per journal, failure conditions, 40 tracker kinds). Current design and its evidence: [docs/design/custom-journals.md](../../design/custom-journals.md). In-game verification is still pending: [docs/runtime-checklist.md](../../runtime-checklist.md).

## 1. Purpose

Vic3-TODO adds a player-authored TODO system that behaves like Victoria 3's Journal rather than like an external notepad.

A TODO can be a plain free-text reminder, or it can use selected Journal-style features such as progress tracking, automatic completion, deadline/status display, and pinning.

The core use case is:

> Create "Build 10 Furniture Manufactories", attach a building tracker, and have the game show progress such as 6 / 10 automatically from the live game state.

The mod must not alter simulation outcomes merely because a TODO exists.

## 2. Design principles

1. **Player text and machine tracking are separate.**  
   The player may write arbitrary text, but the mod does not infer game logic from natural language. Tracking behavior is configured explicitly through the TODO builder.

2. **Journal features are opt-in per TODO.**  
   A TODO may use zero or more supported Journal-style features.

3. **Trackers are modular.**  
   One TODO may contain multiple trackers of different kinds.

4. **Delta tracking uses the creation-time baseline.**  
   For "build 10 more Furniture Manufactories", the baseline is captured when the tracker is created. Existing levels do not count toward progress.

5. **Persistence is a hard requirement.**  
   A free-text TODO is not considered implemented if it disappears after save/load or a full game restart.

6. **No observable storage hacks.**  
   State, city, company, military formation, treaty, or other player-visible game object names must not be repurposed as hidden string storage.

7. **Pure-mod implementation is preferred, not assumed.**  
   If Victoria 3 1.14.x cannot safely persist arbitrary user text or support the required dynamic UI flow through normal modding, implementation stops after the feasibility report. A native/plugin fallback requires a separate design decision.

## 3. Scope

### 3.1 v1 user-visible capabilities

A TODO contains:

- one free-text text field;
- manual completed / incomplete state;
- edit and delete operations;
- optional progress tracking;
- optional automatic completion;
- optional deadline display;
- optional dynamic status display;
- optional pinning;
- zero to four trackers.

The v1 storage limit is 32 TODO slots total, counting both active and completed TODOs.

Free-text input limit is 200 Unicode characters per TODO.

Japanese and English localization are required.

### 3.2 Non-goals for v1

The following are intentionally excluded:

- natural-language parsing of TODO text;
- AI-generated TODOs;
- automatic game actions from a TODO;
- arbitrary scripted buttons that modify game state;
- drag-and-drop ordering;
- categories/tags;
- reminder notifications;
- nested TODOs;
- multiplayer synchronization guarantees beyond what vanilla save-state behavior naturally provides;
- external cloud sync;
- native code unless separately approved after the pure-mod feasibility gate.

## 4. User experience

### 4.1 TODO creation flow

The Journal exposes a TODO entry point. Creating a TODO opens a builder conceptually equivalent to:

```text
New TODO
────────────────────────────────
Text
[ Build up the industrial base             ]

Journal features
[x] Progress tracking
[x] Auto-complete when conditions are met
[ ] Deadline
[ ] Dynamic status
[x] Pin

Progress conditions

1. Building
   Target: Furniture Manufactories
   Mode: Increase from creation
   Goal: 10

   [+ Add tracker]

2. GDP
   Mode: Increase from creation
   Goal: £20M

Completion rule
(*) All trackers
( ) Any tracker

[Create TODO]
```

The exact visual layout should reuse vanilla Victoria 3 Journal widgets and visual language where practical.

### 4.2 Plain TODO

If no tracker or other optional feature is selected, the TODO behaves as a persistent free-text checklist item.

### 4.3 Tracked TODO

A tracked TODO shows each tracker independently.

Example:

```text
Second Industrialization

Furniture Manufactories   6 / 10
████████████░░░░░░░░

Railways                   3 / 5
████████████░░░░░░░░

GDP                       £13M / £20M
█████████████░░░░░░░
```

### 4.4 Completion rule

A TODO with multiple trackers has one explicit aggregation rule:

- **ALL**: every tracker must be complete.
- **ANY**: at least one tracker must be complete.

If auto-complete is enabled, the TODO transitions to completed when the aggregation rule is satisfied.

If auto-complete is disabled, reaching 100% only marks the tracked condition as satisfied; the player completes the TODO manually.

Manual completion remains available for TODOs, including tracked TODOs. A completed TODO can be returned to the incomplete state.

### 4.5 Editing, deletion, and completed items

The player can edit the text and supported feature configuration of an existing TODO.

If an edit changes tracker identity, target, or measurement mode in a way that changes baseline semantics, the tracker baseline is recaptured at the time that edit is confirmed. Purely cosmetic text edits do not recapture baselines.

Completed TODOs are shown separately from active TODOs. The player can:

- reopen a completed TODO;
- delete an individual TODO;
- delete all completed TODOs with an explicit confirmation.

Deleting a TODO permanently frees its fixed storage slot.

## 5. Tracker architecture

Trackers are conceptually independent modules behind one common contract.

The implementation language is PDXScript/GUI rather than an object-oriented runtime, but files, scripted values/triggers, state variables, and UI bindings should preserve this separation.

Conceptual interface:

```text
TrackerDefinition
- id
- value_type
- supported_target_modes
- target selector
- capture_baseline
- read_current_value
- calculate_progress
- is_complete
- format_current_value
- format_goal_value
```

Adding a new tracker kind must not require redesigning TODO storage or the TODO builder.

## 6. Tracker value models

### 6.1 Numeric trackers

Numeric trackers support one or more of:

- `DELTA_INCREASE`
- `ABSOLUTE_AT_LEAST`
- `DELTA_DECREASE`
- `ABSOLUTE_AT_MOST`

Not every tracker is required to expose every mode.

For `DELTA_INCREASE`:

```text
raw_delta = current_value - baseline_value
progress_value = clamp(raw_delta, 0, goal)
progress_ratio = clamp(progress_value / goal, 0, 1)
```

The baseline is captured exactly once when the tracker is created.

Progress is **net change from the baseline**, not cumulative historical actions. Therefore, if a building level is added and later demolished, building progress may decrease.

This semantics intentionally matches the already-approved "B" behavior.

### 6.2 Boolean trackers

Boolean trackers represent a condition such as a technology being researched or a law being active.

They display an incomplete/complete state rather than pretending that an intermediate percentage exists.

### 6.3 Ordinal trackers

Rank-like trackers use an ordered game-defined target and display incomplete/complete plus current state. They do not invent a misleading linear percentage unless the engine exposes a meaningful one.

## 7. Initial tracker catalog

The architecture supports multiple tracker kinds from the beginning.

The v1 design targets these tracker families, subject to Phase 0/API verification:

| Tracker | Value model | Example |
| --- | --- | --- |
| Building level | Numeric | Increase Furniture Manufactories by 10 levels |
| GDP | Numeric | Increase GDP by £20M / reach £100M |
| Population | Numeric | Increase population by 5M |
| Literacy | Numeric | Reach 80% literacy |
| Army size | Numeric | Increase army size by 50 |
| Navy size | Numeric | Reach 50 |
| Technology | Boolean | Research Telephone |
| Law | Boolean | Enact Universal Suffrage |
| Relations | Numeric | Reach +80 relations with France |
| Country rank | Ordinal | Reach Great Power |

Additional trackers such as prestige, bureaucracy, authority, convoys, innovation, radicals, loyalists, standard of living, goods output, market prices, state-level metrics, and company prosperity are extension points, not v1 requirements.

## 8. Building tracker semantics

The building tracker counts **building levels**, not the number of state-local building entities.

For a Furniture Manufactories tracker:

- target type: `building_furniture_manufacturies`;
- baseline: sum of the player's relevant building levels when the tracker is created;
- current: current sum of those levels;
- delta progress: `max(0, current - baseline)`.

Example:

```text
Creation-time total = 4
Goal delta          = 10
Current total       = 9
Displayed progress  = 5 / 10
Completion total    = 14
```

Vanilla script patterns already demonstrate iteration over `every_scope_building`, filtering with `is_building_type`, and summing `level`. The exact ownership/scope rules must be verified against 1.14.5 before implementation.

## 9. Journal feature model

Journal-style features are independent flags/configurations on a TODO.

### 9.1 Progress tracking

Enables the tracker list and progress UI.

A TODO may contain 1–4 trackers when enabled.

### 9.2 Automatic completion

If enabled, evaluate the TODO's ALL/ANY aggregation rule and mark the TODO completed when satisfied.

### 9.3 Deadline

Stores a game date and displays remaining/overdue status.

In v1, missing a deadline does **not** delete or fail the TODO. It becomes overdue and remains actionable.

Automatic failure behavior is deferred.

### 9.4 Dynamic status

Allows a TODO to show computed status text such as:

- In progress
- Conditions satisfied
- Overdue
- Completed

The design should reuse vanilla-style `status_desc` behavior where technically appropriate.

### 9.5 Pinning

Allows the TODO to participate in the closest safe equivalent of vanilla Journal pinning.

Exact pinning behavior is a Phase 0/implementation validation item because custom Journal widgets may not expose every engine-owned pin API to script mods.

## 10. Persistence model

Persistence is the highest-risk subsystem.

Conceptually, each TODO requires:

```text
TodoSlot
- occupied
- text
- completed
- auto_complete
- completion_rule
- deadline_enabled
- deadline
- status_enabled
- pinned
- tracker_count
- trackers[0..3]
```

Each tracker requires:

```text
TrackerSlot
- kind
- target identifier
- target scope/reference where needed
- target mode
- baseline
- goal
- auxiliary configuration
```

### 10.1 Fixed-slot recommendation for pure mod

Because PDXScript may not provide a general dynamic object store, the preferred pure-mod architecture is a bounded fixed-slot model:

- 32 TODO slots;
- 4 tracker slots per TODO;
- unused slots hidden;
- stable slot IDs used for save/load and UI binding.

This trades theoretical flexibility for deterministic persistence and testability.

### 10.2 Free-text persistence hard gate

Numeric, boolean, date, and scope-related state are not sufficient by themselves. The actual arbitrary Unicode TODO text must survive save/load.

Do not claim persistence based only on editbox behavior.

The implementation must prove:

1. arbitrary text can leave the editbox;
2. the mod can capture it;
3. it can be serialized safely;
4. it can be reconstructed after loading;
5. Japanese Unicode remains byte/character-equivalent in meaning;
6. a full application restart does not lose it.

## 11. Phase 0 — feasibility gate

No production implementation begins until the following probes succeed or are conclusively classified.

### 11.1 Probe A: free-text persistence

Input:

`日本で家具工場を10レベル建てる`

Verify persistence after:

1. closing/reopening the Journal;
2. switching panels;
3. save;
4. return to main menu;
5. load;
6. exit Victoria 3;
7. restart Victoria 3;
8. load the same save.

Also test:

- ASCII;
- Japanese;
- spaces;
- digits;
- common punctuation;
- near-200-character input;
- empty input rejection;
- newline behavior if multiline is considered.

### 11.2 Probe B: dynamic TODO slots

Verify that at least two independently configured TODO slots can:

- display different text;
- preserve separate completion state;
- preserve separate tracker configuration;
- survive save/load without cross-slot corruption.

### 11.3 Probe C: tracker selector data flow

Verify that a player can select a tracker kind and required target from the builder and that the chosen target can be stored and later evaluated.

At minimum prove:

- one building target;
- one boolean target such as technology;
- one target-country metric if relations is to be in v1.

### 11.4 Probe D: baseline capture

Create a building tracker while the country has a known current value, save the baseline once, change the game state, and prove that the baseline is not recomputed on Journal reopen or save/load.

Also verify edit semantics:

- editing TODO text alone preserves the baseline;
- changing tracker identity, target, or measurement mode recaptures the baseline exactly once when the edit is confirmed.

### 11.5 Probe E: Journal integration

Verify the safest available 1.14.5 integration point for:

- custom Journal widget/panel content;
- progress bar presentation;
- dynamic status;
- optional pin behavior.

Prefer custom Journal entry/widget integration over broad vanilla GUI replacement.

### 11.6 Tracker capability matrix

Phase 0 must record every proposed v1 tracker family as one of:

- supported by verified 1.14.5 script/GUI APIs;
- supported with a documented limitation;
- unsupported for the pure-mod v1 path.

The initial catalog is a design target, not permission to fake or approximate unavailable game values.

### 11.7 Phase 0 success criteria

The pure-mod path is viable only if A–D succeed. E may degrade only for non-core presentation details such as exact pin behavior.

If arbitrary free-text persistence fails, stop. Do not silently ship a session-only TODO system.

Produce a feasibility report documenting:

- investigated APIs;
- evidence;
- successful paths;
- failed paths;
- blockers;
- whether a pure-mod solution remains viable;
- whether a native/plugin design should be considered separately.

## 12. Known vanilla evidence to validate against 1.14.5

Existing Victoria 3 script/GUI patterns show that:

- Journal entries expose goal/progress functions including current and total goal values;
- Journal UI can render scripted progress bars;
- one Journal Entry can own multiple scripted progress bars;
- building scopes can be iterated and building levels summed;
- `gdp`, `total_population`, `army_size`, and `navy_size` are used as script values/triggers;
- `has_technology_researched` and `has_law` exist as boolean triggers;
- relations and country-rank checks exist in vanilla script;
- editable GUI text boxes exist, but vanilla examples commonly route text through engine-defined callbacks.

These facts support the tracker concept but **do not prove arbitrary mod-defined string persistence**. The latter remains a Phase 0 gate.

## 13. Update model and performance

TODO tracking must avoid adding unnecessary simulation load.

Preferred rules:

- no per-frame scripted evaluation;
- no global daily scanning solely for TODOs unless required by engine constraints;
- use UI-time/current-value evaluation where safe;
- if periodic updates are necessary, use the least frequent cadence that still feels correct;
- only evaluate occupied TODO/tracker slots;
- cap v1 at 32 TODOs × 4 trackers.

The mod must not modify AI, economy, pops, construction behavior, diplomacy, or other simulation mechanics merely to support tracking.

## 14. Error handling

The UI must reject or safely handle:

- empty TODO text;
- goal <= 0 where invalid;
- unsupported mode for a tracker;
- missing target selection;
- deleted/invalid target country or scope;
- tracker configuration that becomes impossible after game-state changes.

If a target becomes invalid, the TODO remains visible and reports an unavailable/invalid target state instead of silently completing or deleting itself.

## 15. Compatibility

Priority order:

1. avoid overriding broad vanilla GUI files;
2. use supported Journal custom-widget/injection paths where available;
3. keep TODO logic in namespaced files and keys;
4. avoid dependencies on third-party frameworks for v1 unless Phase 0 proves they are required;
5. document any unavoidable GUI override and likely UI-mod conflicts.

All keys, variables, widgets, scripted values/triggers, and localization keys must use a project-specific prefix such as `vic3_todo_`.

## 16. Localization

Required languages:

- English;
- Japanese.

Player-authored text is not localized.

System UI, tracker names, validation errors, status labels, and builder labels are localized.

## 17. Testing strategy

### 17.1 Static tests

Automate where practical:

- expected file layout;
- syntax-sensitive generated/config files;
- localization key coverage;
- duplicate widget/key detection;
- fixed-slot index bounds;
- tracker capability table consistency;
- goal-mode validation;
- no accidental broad GUI overrides;
- no simulation effects outside the TODO namespace;
- no placeholder/TBD tokens in release artifacts.

### 17.2 Runtime verification

A dedicated runtime checklist must cover:

- free-text input;
- Japanese input;
- TODO create/edit/delete;
- manual complete/uncomplete;
- multiple trackers;
- ALL/ANY rules;
- auto-complete on/off;
- building baseline delta;
- numeric progress regression when the underlying value falls;
- boolean tracker completion;
- deadline/overdue display;
- save/load;
- full restart/load;
- 32 total stored TODO capacity boundary;
- 4 tracker capacity boundary;
- target invalidation;
- compatibility with an otherwise unmodified 1.14.5 UI.

## 18. Implementation boundaries

Implementation should be decomposed into these subsystems:

1. feasibility probes and evidence;
2. persistence/storage abstraction;
3. TODO slot model;
4. tracker registry and tracker implementations;
5. Journal integration;
6. TODO builder UI;
7. TODO display UI;
8. localization;
9. static validation/tests;
10. runtime verification documentation.

No subsystem may bypass the persistence gate by introducing a different storage hack.

## 19. Acceptance criteria for v1

v1 is complete only when all of the following are true:

- a player can create, edit, complete, reopen, and delete a free-text TODO in the Journal;
- completed TODOs are separated from active TODOs and can be cleared in bulk with confirmation;
- Japanese text persists across full restart/load;
- a TODO can contain multiple trackers;
- building delta tracking follows creation-time baseline semantics;
- at least all tracker families declared as v1-supported after Phase 0 are functional;
- progress displays update from actual game state;
- ALL/ANY aggregation works;
- auto-complete is optional;
- manual completion works;
- deadlines can become overdue without deleting the TODO;
- save/load preserves TODO and tracker state;
- no player-visible game object is abused as storage;
- no unrelated simulation mechanics are changed;
- static verification passes;
- runtime verification on Victoria 3 1.14.5 is recorded.

## 20. Deferred decisions

There are no unresolved product-design decisions required before the implementation plan.

Technical support for each tracker API, arbitrary string persistence, dynamic selector binding, and exact Journal integration are intentionally classified as Phase 0 feasibility questions, not hidden assumptions.

If Phase 0 invalidates the pure-mod architecture, work stops at the documented decision point and a new architecture is designed before any native implementation.
