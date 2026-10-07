# Two-slot tracker probe

Only two TODO probe slots, one tracker each. Numeric country variables have distinct `vic3_todo_slot_0_` / `vic3_todo_slot_1_` identifiers. Each dedicated Journal entry initializes its own slot once, guarded by occupied state. Baseline capture count makes recapture observable. Reopen/load does not invoke an unguarded reset.

Actions: `create`, `cosmetic_edit`, `complete`, `reopen`, `select_furniture`, `select_textile`, `select_technology`, `select_absolute`, `select_delta`, `goal_5`, `goal_10`; `select_gbr` and `select_fra` only with numeric relations evidence. Cosmetic editing changes a fixed-label ID, not arbitrary user text. Identical confirmed target/mode/goal is a no-op; a changed target/mode/goal captures exactly once. Building progress is net change, clamped at zero and goal; demolishing levels may reduce it. Technology is 0/1; no research percentage is fabricated.

## Primary evidence

- `common/script_values/je_values.txt`: country scope `every_scope_building`, `is_building_type`, `add = this.level`.
- `common/buildings/01_industry.txt`: Furniture Manufactories alias; building levels, not entity counts. Country-scoped building collection concerns domestic buildings, not proof of financial ownership; test foreign investment/overseas ownership separately before defining v1 ownership semantics.
- `common/scripted_effects/00_chris_scripted_effects.txt`: variable assignment from a script value.
- `common/technology/technologies/10_production.txt`: `telephone` target; vanilla triggers demonstrate `has_technology_researched`.
- `common/script_values/ip4_cuba_values.txt`: numeric `add = c:USA.relations:root`. Probe target country IDs are fixed selectable GBR/FRA and never rename countries or change relations.
- `gui/journal_entry_widgets/ep2_japan_widgets.gui`: full `GetScriptedGui(...).Execute(GuiScope.SetRoot(JournalEntry.GetCountry.MakeScope).End)` callback.

The archive does **not** include `common/scripted_guis` declarations. Its builder therefore emits no guessed scripted-GUI definition or selector callback, and marks the interactive selector candidate. The installer audits the installed tree separately. Only if country `scope = country` and `effect = { ... }` are demonstrated in that tree does the builder generate the namespaced action wrappers and GUI controls. This explicit conditional gate is not proof that runtime parsing succeeds.

If controls are absent, use the game's Script Explorer to run the namespaced scripted effect on the player country, or mark selection NOT_TESTED. Do not treat manual effects as successful production selector UI. Archive/installed evidence and mismatches remain separate.
