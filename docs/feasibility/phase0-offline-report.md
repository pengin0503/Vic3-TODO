# Phase 0 offline report — Tasks 1–6

Task 1–6 offline deliverables are implemented and verified; game runtime and Windows PowerShell execution are unverified. Task 7 was not executed and no pure-mod viability decision was made. Production 32×4 TODOs, native code and frameworks were not implemented.

## Source identity and coverage

- Source archive: user supplied `Vic3_todo_source.zip` (local copy `01-Vic3_todo_source.zip`).
- SHA-256: `645b43686ad86db50434bbc1fd1dedf97ed3606f48cad5f32de22b11f4e39d7e`.
- Root detected: `Vic3_todo_source/game`.
- ZIP entries: 1125. Relevant source files inventoried/hashed: 875.
- Full member list, directory counts, per-file SHA-256, path/line/snippet evidence: `research/generated/phase0-api-evidence.json`.
- GUI, common, Journal, editboxes, progress bars, building/technology/law sources are present. The set is curated; completeness is not inferred.
- No installed game tree was available on this Linux execution host. The extracted reference tree is the same partial ZIP, not an installed tree. Windows installer audits the installed tree and records explicit overlap/API comparisons before building.
- ZIP hash was rechecked unchanged. No original ZIP or extracted vanilla file is tracked. All fixture data was authored independently.

## Important API / GUI evidence

| Capability | Primary archive evidence |
| --- | --- |
| Editboxes and engine callbacks | `gui/frontend/shared/edit_boxes.gui`, `gui/power_bloc_formation_panel.gui`, `gui/companies_panel.gui` |
| Explicit custom Journal widget attachment | `common/journal_entries/journal_entries.md`, `common/journal_entries/00_meiji_restoration.txt` |
| Widget anchors and pin toggle | `gui/journal_entry.gui`, `gui/journal.gui` |
| Building level sum | `common/script_values/je_values.txt`: country scope iteration, type filter, `add = this.level` |
| Furniture target | `common/buildings/01_industry.txt`: `building_furniture_manufactory` and legacy alias `building_furniture_manufacturies` |
| Baseline variable from a script value | `common/scripted_effects/00_chris_scripted_effects.txt` |
| GUI script-value display and Execute scope chain | `gui/journal_entry_widgets/ep2_japan_widgets.gui` |
| Numeric relations | `common/script_values/ip4_cuba_values.txt`: `c:USA.relations:root` |
| Population numeric operand | `common/script_values/ip4_je_values.txt`: `multiply = total_population` |
| Telephone and Universal Suffrage targets | `common/technology/technologies/10_production.txt`, `common/laws/00_distribution_of_power.txt` |
| Weekly Journal bar update | `common/journal_entries/05_bulgaria_je.txt`: Journal scope `set_bar_progress` with ROOT script value |
| Dynamic status / scripted bar schema | `common/journal_entries/journal_entries.md`, `common/scripted_progress_bars/scripted_progress_bars.md` |

See the generated [tracker capability matrix](tracker-capability-matrix.md) for all ten families, evidence paths and limits. Every runtime result is pending.

## Probe state and rulings

1. Archive build is deterministic, validated and contains 13 files. The minimum Journal integration is a new explicit `widget.gui` file; no vanilla GUI override or folder-autoload assumption.
2. Free-text persistence is **candidate / insufficient coverage**. A single namespaced editbox tests input only; it has no guessed save callback. Fixed Japanese localization is not persisted user text. Engine name callbacks were excluded. Cost: this probe cannot prove an unavailable string storage bridge; production remains gated.
3. There are two independently saved numeric/config slots, one tracker each. Creation is occupied-guarded; cosmetic label edits do not capture; changed target/mode/goal captures once; identical selection does not capture. Domestic building scope versus financial ownership is a documented runtime limitation.
4. Technology is Boolean 0/1, never partial research progress. Relations uses fixed selectable GBR/FRA target identifiers; missing/self targets cannot satisfy conditions.
5. Scripted GUI country definitions are absent from the archive. The ZIP build marks selector UI candidate and omits its callback. Installed-tree builds generate namespaced scope/effect wrappers only after declaration and Execute-chain evidence. Manual Script Explorer actions do not count as production selector success. Cost: ZIP-only builds cannot prove interactive selector support.
6. Journal weekly numeric/Boolean bars, dynamic status and standard pinning are emitted from evidence. All save/load/reopen/full-process-restart behavior is unverified.
7. Work was committed to main as explicitly authorized, without PR. Git transport credentials were unavailable; GitHub connector delivered the upstream snapshot and expected-head non-force updates. Original upstream spec/plan blobs are unchanged.

## Commits

| Task | GitHub commit |
| --- | --- |
| 1 | `927b43f6ebf92abc7e77b0cac7e41a234b3580e7` |
| 2 | `08ab0ed1f3562cdb1a304e3daf140689f5b26260` |
| 3 | `ef1cce80d1518065314570ed3a6a407ba9b3f39d` |
| 4 | `1eac2467048f7eecc053020f12f37e62babae0a1` |
| 5 | `7dbf395a15f18eeac2439ea76bb58baa887a1fa2` |
| 6 | `5d855266fbb10bd1d230e5aa5d51525717e04d4c` |

A following safety-fix commit contains this report and the final regression tests; resolve latest main from GitHub rather than treating this table as a permanent head.

## Verification and final review

Python tooling/static validation was written test-first. Missing modules/files and missing safety behavior were observed RED before implementation; per-task suites passed before committing. Final full suite: **42 tests passed**. `python -m py_compile tools/*.py tests/*.py` passed. ZIP audit and build were rerun successfully; repeated builds matched file bytes.

One read-only final reviewer inspected the complete six-task range; no implementation was delegated. Two Important installer defects were reproduced and fixed: a source ZIP nested in an existing owned mod output was deleted by replacement; a repository inside GameDir wrote research before later rejection. All destinations are now preflighted before the first write. A symlink-output finding was regraded Important because the builder published while returning failure; lexical symlinks are rejected before resolution. Related unrelated-output deletion is prevented by owned metadata/manifest checks. All four regression tests failed before the fix and passed afterward. No deferred minors or declined in-scope judgments remain.

Windows wrappers were inspected but could not run here. Python publish/collector paths were tested against temporary directories. No game runtime PASS was inferred. Installer and collector are ready for their first Windows run, not claimed Windows-validated.

## Runtime handoff

Follow [runtime-verification-phase0.md](../runtime-verification-phase0.md). Verify Japanese input, Journal reopen, save/load and full exit→restart→load; both slot states, baseline, target/config, reconfiguration count, progress regression/update, technology Boolean, status and pin/pin persistence. The first launch can cover most probes together; full-process persistence necessarily requires a second launch.

Collector records explicit PASS/FAIL/NOT_TESTED, defaulting blank to NOT_TESTED, and bundles available log tails/derived evidence. It does not execute Task 7.
