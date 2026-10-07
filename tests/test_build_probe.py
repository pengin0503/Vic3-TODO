import json
import tempfile
import unittest
from pathlib import Path
from tools import build_probe as b
from tools import audit_vanilla as a
from tests.test_audit_vanilla import FIXTURE

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.evidence=self.root/'evidence.json';a.write_evidence(a.audit_game(FIXTURE),self.evidence)
    def build(self,name='mod'):
        out=self.root/name;b.build_probe(FIXTURE,self.evidence,out);return out
    def test_build_rejects_missing_mandatory_evidence(self):
        r=json.loads(self.evidence.read_text());r['capabilities']['journal_custom_widget']='candidate';a.write_evidence(r,self.evidence)
        with self.assertRaises(ValueError):self.build()
    def test_build_is_reproducible(self):
        x=self.build('one');y=self.build('two')
        def files(p):return {f.relative_to(p).as_posix():f.read_bytes() for f in p.rglob('*') if f.is_file()}
        self.assertEqual(files(x),files(y))
    def test_build_rejects_broad_journal_gui_override(self):
        out=self.build();(out/'gui').mkdir(exist_ok=True);(out/'gui/journal.gui').write_text('widget = {}')
        with self.assertRaises(ValueError):b.validate_output(out)
    def test_probe_metadata_targets_vic3_1_14(self):
        r=json.loads((self.build()/'.metadata/metadata.json').read_text());self.assertIn('1.14',r['game_version']);self.assertEqual(r['supported_game_version'],'1.14.*')
    def test_localization_is_utf8_and_contains_probe_labels(self):
        out=self.build()
        for lang in ('english','japanese'):
            text=(out/f'localization/{lang}/vic3_todo_probe_l_{lang}.yml').read_text('utf-8-sig')
            self.assertIn('vic3_todo_probe:',text)
        self.assertIn('日本で家具工場を10レベル建てる',(out/'localization/japanese/vic3_todo_probe_l_japanese.yml').read_text('utf-8-sig'))
    def test_text_probe_has_one_namespaced_editbox_without_unverified_callbacks(self):
        out=self.build();s=(out/'gui/journal_entry_widgets/vic3_todo_probe_widget.gui').read_text()
        self.assertEqual(s.count('editbox = {'),1)
        self.assertIn('name = "vic3_todo_text_input"',s)
        self.assertNotIn('ontextedited',s);self.assertNotIn('oneditingfinished',s)
        self.assertNotIn('SetName',s)
    def test_text_probe_japanese_round_trip_and_explicit_storage_limit(self):
        out=self.build();r=json.loads((out/'vic3_todo_probe_capabilities.json').read_text())
        self.assertEqual(r['free_text_persistence']['status'],'candidate')
        self.assertEqual(r['unicode_input'],'日本で家具工場を10レベル建てる')
        s=(out/'common/journal_entries/vic3_todo_probe.txt').read_text()
        self.assertIn('gui = "gui/journal_entry_widgets/vic3_todo_probe_widget.gui"',s)

    def test_two_slot_storage_and_baseline_actions_are_independent(self):
        out=self.build();s=(out/'common/scripted_effects/vic3_todo_probe_effects.txt').read_text()
        blocks=b.parse_definitions(s)
        for slot in (0,1):
            prefix=f'vic3_todo_slot_{slot}_'
            self.assertIn(prefix+'create',blocks)
            self.assertNotIn(f'vic3_todo_slot_{1-slot}_',blocks[prefix+'create'])
            self.assertNotIn('baseline',blocks[prefix+'cosmetic_edit'])
            for action in ('select_furniture','select_textile','select_technology','select_absolute'):
                self.assertEqual(blocks[prefix+action].count(prefix+'capture = yes'),1)
            self.assertIn('has_variable',blocks[prefix+'create'])
        values=(out/'common/script_values/vic3_todo_probe_values.txt').read_text()
        self.assertIn('add = this.level',values)
        self.assertIn('subtract = var:vic3_todo_slot_0_baseline',values)
    def test_relations_probe_omitted_without_verified_target_binding(self):
        out=self.build()
        self.assertNotIn('relations:',(out/'common/script_values/vic3_todo_probe_values.txt').read_text())
        self.assertNotIn('vic3_todo_relations',(out/'common/journal_entries/vic3_todo_probe.txt').read_text())
    def test_unproven_scripted_gui_definition_does_not_emit_selector_callback(self):
        out=self.build();s=(out/'gui/journal_entry_widgets/vic3_todo_probe_widget.gui').read_text()
        self.assertNotIn('GetScriptedGui(',s)
        self.assertIn('vic3_todo_selector_limit',s)
    def test_verified_installed_schema_enables_selector_gui(self):
        import shutil
        source=self.root/'vanilla';shutil.copytree(FIXTURE,source)
        p=source/'game/common/scripted_guis/test.txt';p.parent.mkdir();p.write_text('original = { scope = country effect = { set_variable = test } }')
        p=source/'game/gui/actions.gui';p.write_text('button = { onclick = "[GetScriptedGui(\'original\').Execute(GuiScope.SetRoot(JournalEntry.GetCountry.MakeScope).End)]" }')
        a.write_evidence(a.audit_game(source),self.evidence)
        out=self.root/'selector';b.build_probe(source,self.evidence,out)
        self.assertTrue((out/'common/scripted_guis/vic3_todo_probe_actions.txt').is_file())
        s=(out/'gui/journal_entry_widgets/vic3_todo_probe_widget.gui').read_text();self.assertIn('vic3_todo_slot_0_select_furniture',s)

if __name__=='__main__':unittest.main()
