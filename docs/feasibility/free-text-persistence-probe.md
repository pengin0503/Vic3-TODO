# Free-text probe: candidate, no verified persistent bridge

Primary evidence: `gui/frontend/shared/edit_boxes.gui`, `gui/power_bloc_formation_panel.gui`, `gui/companies_panel.gui`, and `common/journal_entries/journal_entries.md` in the supplied 1.14.5 archive. Engine-defined `OnEditName`/terrain setters do not accept arbitrary mod-owned save state. They are not reused. `set_variable` alone proves neither a Unicode string type nor an editbox transfer path.

The dedicated namespaced editbox deliberately has no text callback. Enter `日本で家具工場を10レベル建てる`, ASCII, punctuation, near-200 characters, empty input and newlines. The adjacent localized sample validates localization, not user-text storage. Observe UI recreation separately. Save/load and full process restart must be recorded as FAIL or NOT_TESTED if no restoration path exists; never PASS because the localized sample remains visible.

Missing bridge evidence is `candidate / insufficient coverage`, not an exhaustive unsupported declaration. The curated archive lacks scripted GUI definitions and an engine API inventory. Numeric/selector/presentation probes do not depend on this field. Production remains blocked pending verified arbitrary-text persistence. No visible object name, native DLL or framework is used.

Journal widget attachment is explicit (`widget.gui`, `name`, `container`); source docs and `00_meiji_restoration.txt` demonstrate this exact integration. No directory-autoload assumption and no vanilla GUI override are required.
