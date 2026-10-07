# Vic3-TODO Phase 0 Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible Victoria 3 1.14.x feasibility probe that can determine whether Vic3-TODO can persist arbitrary Unicode TODO text, maintain independent TODO/tracker state, capture creation-time baselines, and integrate safely with the Journal before any production TODO implementation begins.

**Architecture:** Keep Phase 0 isolated from production code. A Python offline auditor reads either the user's supplied `Vic3_todo_source.zip` reference archive or an installed Victoria 3 1.14.x tree and emits a machine-readable API/evidence manifest; a generated probe mod then exercises the smallest possible GUI/script paths for text capture, fixed slots, tracker selection, baseline persistence, and Journal presentation. Probes are intentionally independent so Tasks 1–6 can be completed in one uninterrupted offline run even when one capability is unsupported or still needs runtime proof. Runtime evidence is recorded separately and is the hard gate for the later production implementation plan.

**Tech Stack:** Victoria 3 1.14.x PDXScript/Jomini GUI/localization, Python 3.10+ standard library, `unittest`, PowerShell installer/launcher helper.

**Spec:** `docs/superpowers/specs/2026-10-07-vic3-todo-journal-design.md`

## Global Constraints

- Target Victoria 3 1.14.x; baseline verification is Victoria 3 1.14.5.
- Do not implement the production TODO system in this plan.
- Execute Tasks 1–6 continuously in one run without pausing for user confirmation unless an irreversible/security-sensitive action is required.
- Arbitrary Unicode free-text persistence across full game restart/load is a hard gate.
- Do not use state/city/company/military-formation/treaty or other visible game-object names as hidden storage.
- Do not add native code or third-party framework dependencies.
- Do not silently downgrade to session-only text.
- Prefer Journal custom-widget/injection mechanisms over broad vanilla GUI overrides.
- Namespace all mod-owned keys, variables, widgets, and localization with `vic3_todo_`.
- The probe may use only the minimum simulation hooks needed to test persistence; it must not change AI, economy, construction behavior, diplomacy, or balance.
- Use the latest `main` as source of truth for project code at execution time; do not treat the plan-time commit SHA as permanent.
- For vanilla Victoria 3 API/GUI evidence, prefer the user-supplied `Vic3_todo_source.zip` when available. Treat it as read-only source material, not project code. If a full installed 1.14.x tree is also available, compare overlapping files and record any mismatch rather than silently choosing one.
- Run TDD for Python tooling/static validation, systematic-debugging for unexpected failures, and verification-before-completion before claiming the probe ready.

## Review Focus

1. **Unicode round-trip:** Japanese and punctuation must pass through generated files and probe configuration without Python-side encoding loss; Task 1 tests UTF-8 evidence/output handling.
2. **Slot isolation:** two TODO probe slots must never share text/config/completion/baseline state; Task 4 tests distinct slot identifiers and generated bindings.
3. **Baseline recapture:** cosmetic text edits must preserve a tracker baseline while tracker identity/target/mode changes must recapture it exactly once; Task 4 statically validates distinct actions and the runtime checklist verifies behavior.
4. **Unsupported vanilla API:** absence of a required 1.14.x callback/integration point must yield an explicit `unsupported` capability, never guessed code; Tasks 1 and 5 test/report this.
5. **Unsafe GUI override:** the build must reject generation that would replace broad vanilla Journal GUI files when a narrower custom-widget path is available; Task 2 tests the override allowlist.

---

### Task 1: Installed-game API evidence auditor

**Files:**
- Create: `tools/audit_vanilla.py`
- Create: `tests/fixtures/vanilla_minimal/game/gui/frontend/shared/edit_boxes.gui`
- Create: `tests/fixtures/vanilla_minimal/game/gui/journal_entry.gui`
- Create: `tests/fixtures/vanilla_minimal/game/gui/journal_entry_widgets/custom_widgets.gui`
- Create: `tests/fixtures/vanilla_minimal/game/common/journal_entries/journal_entries.md`
- Create: `tests/fixtures/vanilla_minimal/game/common/buildings/01_industry.txt`
- Create: `tests/fixtures/vanilla_minimal/game/common/scripted_effects/00_victoria_scripted_effects.txt`
- Create: `tests/test_audit_vanilla.py`
- Generated at runtime, never hand-edited: `research/generated/phase0-api-evidence.json`

**Interfaces:**
- Produces CLI accepting exactly one source input:
  - `python tools/audit_vanilla.py --source-archive <Vic3_todo_source.zip> --output research/generated/phase0-api-evidence.json`
  - `python tools/audit_vanilla.py --game-dir <Victoria3Root> --output research/generated/phase0-api-evidence.json`
- Produces JSON keys: `source_kind`, `source_identity`, `evidence[]`, `capabilities{}`, `source_hashes{}`.
- Each `capabilities.<id>` is exactly one of `supported`, `candidate`, `unsupported`.
- Capability IDs: `editbox`, `ontextedited`, `oneditingfinished`, `journal_custom_widget`, `journal_progress_bar`, `journal_scripted_progress_bar`, `journal_status_desc`, `journal_pin`, `script_variable`, `building_level_sum`, `gdp`, `total_population`, `literacy_rate`, `army_size`, `navy_size`, `technology_trigger`, `law_trigger`, `relations`, `country_rank`.

- [ ] **Step 1: Write failing auditor tests**

Add tests named:
- `test_detects_required_gui_and_journal_evidence`
- `test_marks_missing_capability_unsupported`
- `test_hashes_every_evidence_source`
- `test_writes_utf8_json_without_ascii_escaping_japanese`

Assertions must verify the exact capability enum and that `日本で家具工場を10レベル建てる` survives JSON write/read unchanged.

- [ ] **Step 2: Run the tests and verify failure**

Run: `python -m unittest tests.test_audit_vanilla -v`

Expected: FAIL because `tools.audit_vanilla` does not exist.

- [ ] **Step 3: Implement the minimal auditor**

Implement:
- `audit_game(game_dir: pathlib.Path) -> dict`
- `audit_archive(source_archive: pathlib.Path) -> dict`
- `write_evidence(report: dict, output: pathlib.Path) -> None`
- `main(argv: list[str] | None = None) -> int`

The auditor must search only documented candidate locations/patterns, include matched snippets/paths and SHA-256 hashes, and use UTF-8 JSON with `ensure_ascii=False`. Archive extraction/inspection must be read-only with respect to the source and must reject unsafe ZIP traversal paths. The archive's directory layout may contain an extra wrapper directory; locate `game/` or the expected `gui/`/`common/` roots without assuming a fixed top-level folder. Missing evidence is `unsupported`; ambiguous evidence is `candidate`, not `supported`.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_audit_vanilla -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/audit_vanilla.py tests/fixtures/vanilla_minimal tests/test_audit_vanilla.py
git commit -m "test: add Victoria 3 API evidence auditor"
```

### Task 2: Deterministic Phase 0 probe builder and safe file layout

**Files:**
- Create: `tools/build_probe.py`
- Create: `tests/test_build_probe.py`
- Create: `.gitignore`
- Create: `probe_src/.metadata/metadata.json`
- Create: `probe_src/localization/english/vic3_todo_probe_l_english.yml`
- Create: `probe_src/localization/japanese/vic3_todo_probe_l_japanese.yml`
- Generated output: `dist/Vic3TODOProbe/`

**Interfaces:**
- Consumes: Task 1 evidence JSON and the same vanilla source used by Task 1.
- Produces CLI with either `--game-dir <Victoria3Root>` or `--source-archive <Vic3_todo_source.zip>` together with `--evidence ... --output dist/Vic3TODOProbe`.
- Produces a complete probe mod only when mandatory static prerequisites are present.
- Function signatures:
  - `build_probe(game_dir: pathlib.Path, evidence_path: pathlib.Path, output_dir: pathlib.Path) -> list[pathlib.Path]`
  - `validate_output(output_dir: pathlib.Path) -> None`
- Allowed vanilla GUI replacement list defaults to empty. Any non-empty override must be explicitly justified by the evidence manifest and a narrow allowlist in code.

- [ ] **Step 1: Write failing builder tests**

Add:
- `test_build_rejects_missing_mandatory_evidence`
- `test_build_is_reproducible`
- `test_build_rejects_broad_journal_gui_override`
- `test_probe_metadata_targets_vic3_1_14`
- `test_localization_is_utf8_and_contains_probe_labels`

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_build_probe -v`

Expected: FAIL because `tools.build_probe` does not exist.

- [ ] **Step 3: Implement builder and minimal static probe source**

The builder must stage to a temporary directory, validate it, then atomically replace the requested output. It must never write inside the game installation or mutate the source archive.

Do not create production TODO files. At this task, the probe source contains metadata/localization only; later tasks add probe-specific GUI/script files. `.gitignore` must exclude `dist/`, Python cache files, and locally generated installed-game evidence unless a later task explicitly commits a text report.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_build_probe -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/build_probe.py tests/test_build_probe.py probe_src
git commit -m "build: add safe Phase 0 probe builder"
```

### Task 3: Free-text capture and persistence probe

**Files:**
- Create when 1.14.5 evidence proves directory autoload: `probe_src/gui/journal_entry_widgets/vic3_todo_probe_widget.gui`
- Otherwise generate only the narrow evidence-backed `journal_entry_widgets/custom_widgets.gui` override from the user's installed file; never hand-copy a stale vanilla file into the repository.
- Create: `probe_src/common/journal_entries/vic3_todo_probe.txt`
- Create only if supported by evidence: the narrowest namespaced script/callback files required to transfer editbox text into save-serialized state.
- Modify: `tools/build_probe.py`
- Modify: `tests/test_build_probe.py`
- Create: `docs/feasibility/free-text-persistence-probe.md`

**Interfaces:**
- Consumes: Task 1 capability evidence and Task 2 build layout.
- Produces an in-game probe with exactly one text field initialized/verified with `日本で家具工場を10レベル建てる`.
- Provides visible controls/status sufficient to distinguish:
  - editbox accepts text;
  - text reached persistent mod-owned state;
  - restored value after UI recreation/load.
- If no mod-definable callback/storage path can be justified from installed 1.14.x evidence, this task records `unsupported` or `candidate` with evidence. It does **not** block Tasks 4–6; those probes must remain independently buildable so one game session can validate all other capabilities.

- [ ] **Step 1: Add static tests for probe wiring**

Tests must assert:
- the generated GUI contains one namespaced editbox;
- any callback referenced by the probe is backed by verified evidence, not an invented method name;
- the probe contains no visible-object-name storage mechanism;
- the Japanese test string survives source/build output byte-for-byte as UTF-8.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_build_probe -v`

Expected: FAIL until the text probe source/wiring exists.

- [ ] **Step 3: Implement the smallest evidence-backed text probe**

Use only callbacks/storage mechanisms proven by Task 1. Do not infer that a vanilla engine callback is callable with arbitrary mod state. If new files in `journal_entry_widgets/` are not auto-loaded, the builder may generate a minimal patch from the installed `custom_widgets.gui` only when Task 1 evidence proves that file is the required integration surface.

If the only evidence-backed result is session-local editbox text, mark free-text persistence unsupported for the pure-mod path, but continue Tasks 4–6. Do not turn that limitation into a production implementation.

- [ ] **Step 4: Run static verification**

Run:
```bash
python -m unittest discover -s tests -v
python -m py_compile tools/audit_vanilla.py tools/build_probe.py tests/test_audit_vanilla.py tests/test_build_probe.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add probe_src tools/build_probe.py tests/test_build_probe.py docs/feasibility/free-text-persistence-probe.md
git commit -m "feat: add free-text persistence feasibility probe"
```

### Task 4: Fixed-slot, selector, and baseline probes

**Files:**
- Create: `probe_src/common/scripted_effects/vic3_todo_probe_effects.txt`
- Create: `probe_src/common/scripted_triggers/vic3_todo_probe_triggers.txt`
- Create: `probe_src/common/script_values/vic3_todo_probe_values.txt`
- Modify: `probe_src/gui/journal_entry_widgets/vic3_todo_probe_widget.gui`
- Modify: `probe_src/common/journal_entries/vic3_todo_probe.txt`
- Modify: `tests/test_build_probe.py`
- Create: `docs/feasibility/slot-selector-baseline-probe.md`

**Interfaces:**
- Consumes: Task 2 build layout and Task 1 capability evidence. It must not depend on Task 3 succeeding.
- Produces two independent numeric/configuration probe slots and one tracker slot per probe item. Static localized labels may stand in for arbitrary user text so slot/baseline behavior can be tested independently of free-text persistence.
- Probe tracker kinds required here:
  - building target: `building_furniture_manufacturies`;
  - boolean target: one installed-game technology selected from verified 1.14.x data;
  - target-country metric: relations, only if Task 1 marks relations target binding at least `candidate`.
- Baseline operation is conceptually `capture_baseline(slot, tracker)`, represented with namespaced PDXScript variables/scopes rather than invented runtime functions.
- Building current value must use an evidence-backed sum of player-owned relevant building levels.
- Cosmetic text update path must not touch the baseline variable; tracker target/kind/mode update path must explicitly recapture it.

- [ ] **Step 1: Add static slot/baseline tests**

Add assertions that:
- slot 0 and slot 1 use distinct storage identifiers;
- tracker storage identifiers are namespaced by TODO slot;
- building baseline and current-value expressions are distinct;
- text-edit action contains no baseline mutation;
- tracker-reconfiguration action contains exactly one baseline capture;
- relations UI is omitted if capability evidence is unsupported.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_build_probe -v`

Expected: FAIL before slot/tracker probe files are complete.

- [ ] **Step 3: Implement fixed-slot and baseline probe**

Keep the probe deliberately at two probe slots and one tracker each. The production limits of 32 × 4 are not implemented in Phase 0. If free-text capture is unavailable, use fixed localized probe labels and continue testing slot isolation, selector state, and baseline persistence.

- [ ] **Step 4: Run all static verification**

Run:
```bash
python -m unittest discover -s tests -v
python -m py_compile tools/audit_vanilla.py tools/build_probe.py tests/test_audit_vanilla.py tests/test_build_probe.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add probe_src tests/test_build_probe.py docs/feasibility/slot-selector-baseline-probe.md
git commit -m "feat: add slot selector and baseline feasibility probes"
```

### Task 5: Journal presentation probe and tracker capability matrix

**Files:**
- Modify: `probe_src/gui/journal_entry_widgets/vic3_todo_probe_widget.gui`
- Modify: `probe_src/common/journal_entries/vic3_todo_probe.txt`
- Create when supported: `probe_src/common/scripted_progress_bars/vic3_todo_probe_progress_bars.txt`
- Create: `tools/render_capability_matrix.py`
- Create: `tests/test_capability_matrix.py`
- Generated at runtime: `docs/feasibility/tracker-capability-matrix.md`

**Interfaces:**
- Consumes: Task 1 evidence and Task 2 build layout; it must not depend on Task 3 succeeding.
- Produces CLI: `python tools/render_capability_matrix.py --evidence research/generated/phase0-api-evidence.json --output docs/feasibility/tracker-capability-matrix.md`
- Matrix rows: building level, GDP, population, literacy, army size, navy size, technology, law, relations, country rank.
- Matrix status values: `supported`, `supported-with-limitation`, `unsupported`.
- Probe UI demonstrates, where evidence permits:
  - one numeric progress bar;
  - one boolean complete/incomplete indicator;
  - dynamic status text;
  - pin behavior only if a safe exposed path exists.

- [ ] **Step 1: Write failing matrix and presentation tests**

Tests must verify:
- all ten initial tracker families appear exactly once;
- unsupported APIs cannot be rendered as supported;
- limitations include evidence path/reason;
- scripted progress bar is emitted only when evidence supports it;
- pin UI is absent or visibly marked unsupported when no safe API is proven.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_capability_matrix -v`

Expected: FAIL because the renderer does not exist.

- [ ] **Step 3: Implement renderer and presentation probe**

The matrix must be generated from evidence, not maintained as an optimistic hand-written list.

- [ ] **Step 4: Run all static verification**

Run:
```bash
python -m unittest discover -s tests -v
python -m py_compile tools/*.py tests/*.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add probe_src tools/render_capability_matrix.py tests/test_capability_matrix.py docs/feasibility
git commit -m "feat: add Journal presentation probe and capability matrix"
```

### Task 6: Windows install path and runtime verification handoff

**Files:**
- Create: `tools/install_probe.ps1`
- Create: `tools/collect_phase0_results.ps1`
- Create: `docs/runtime-verification-phase0.md`
- Create: `README.md`
- Modify: `tests/test_build_probe.py`

**Interfaces:**
- Consumes: Task 2 builder plus Tasks 3–5 probe content.
- Installer command:
  `powershell -ExecutionPolicy Bypass -File .\tools\install_probe.ps1 -GameDir "<Victoria 3 root>"`
- Installer output:
  `Documents\Paradox Interactive\Victoria 3\mod\Vic3TODOProbe`
- Result collector command:
  `powershell -ExecutionPolicy Bypass -File .\tools\collect_phase0_results.ps1`
- Result collector writes a timestamped text/JSON bundle under `research/runtime/` containing the user's entered PASS/FAIL values plus copies of relevant `error.log`/`gui.log` excerpts when available.
- Runtime evidence to record manually:
  - Probe A: text persistence sequence from the spec;
  - Probe B: two-slot isolation;
  - Probe C: selector persistence/evaluation;
  - Probe D: baseline once-only behavior and edit semantics;
  - Probe E: Journal progress/status/pin behavior;
  - `error.log` and `gui.log` parse/property errors.

- [ ] **Step 1: Add installer/output-safety tests**

Tests must verify the builder refuses:
- output inside the game tree;
- output equal to the source/probe tree;
- partial publish after validation failure.

- [ ] **Step 2: Implement `install_probe.ps1`, `collect_phase0_results.ps1`, and runtime checklist**

The installer may auto-detect conventional Steam locations, but `-GameDir` must override detection. It invokes the Python auditor first, then the builder, then copies/publishes only after successful validation.

The collector must never infer a PASS. It records explicit user-entered PASS/FAIL/NOT_TESTED values and gathers relevant log evidence to reduce the next handoff to one bundle.

The runtime checklist must use the exact Japanese string `日本で家具工場を10レベル建てる` and explicitly require full process exit/restart before declaring Probe A passed.

- [ ] **Step 3: Run final offline verification**

Run:
```bash
python -m unittest discover -s tests -v
python -m py_compile tools/*.py tests/*.py
```

Expected: PASS.

Also search executable/release-facing files for unfinished placeholder markers, invented callback names, and visible-object-name storage hacks.

- [ ] **Step 4: Build against the best available 1.14.5 source**

If `Vic3_todo_source.zip` is available, run the auditor and builder against it first. If an installed-game tree is also available, audit both and compare overlapping source hashes/capabilities; record mismatches explicitly. Commit only derived text evidence/reports, never copyrighted vanilla source files or extracted archive contents.

If neither the source archive nor a full installed-game tree is available in the execution environment, do not fabricate the result. Confirm fixture tests pass and leave the exact Windows command in the handoff.

- [ ] **Step 5: Commit**

```bash
git add README.md tools/install_probe.ps1 tools/collect_phase0_results.ps1 docs/runtime-verification-phase0.md tests/test_build_probe.py
git commit -m "docs: prepare Phase 0 runtime verification"
```

### Task 7: Verification-before-completion and Phase 0 decision record

**Files:**
- Create or update after runtime evidence exists: `docs/feasibility/phase0-decision.md`
- Modify if necessary: `docs/feasibility/tracker-capability-matrix.md`
- Modify: `README.md`

**Interfaces:**
- Produces one final decision: `PURE_MOD_VIABLE` or `PURE_MOD_BLOCKED`.
- `PURE_MOD_VIABLE` requires runtime success for Probes A–D.
- Probe E may have documented presentation limitations only.
- `PURE_MOD_BLOCKED` is mandatory if arbitrary free-text cannot survive full restart/load.

- [ ] **Step 1: Do not execute this task until runtime evidence is supplied**

If the agent cannot launch Victoria 3, stop after Task 6 and report exactly which runtime results are needed. Do not mark Task 7 complete.

- [ ] **Step 2: When runtime evidence is available, classify every probe**

Record PASS/FAIL with reproduction notes and relevant log excerpts. No inferred PASS values.

- [ ] **Step 3: Write the decision**

If `PURE_MOD_BLOCKED`, stop the project at the approved architecture gate and do not create native code.

If `PURE_MOD_VIABLE`, state that the next action is to write a **new production implementation plan** from the now-verified APIs. Do not implement the 32 × 4 production system under this Phase 0 plan.

- [ ] **Step 4: Run verification-before-completion**

Re-run all offline tests and validate that the decision document agrees with the recorded runtime evidence and capability matrix.

- [ ] **Step 5: Commit**

```bash
git add docs/feasibility README.md
git commit -m "docs: record Vic3 TODO Phase 0 feasibility decision"
```
