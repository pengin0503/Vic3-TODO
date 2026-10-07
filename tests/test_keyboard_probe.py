import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from tools import audit_vanilla as a, build_probe as b
from tests.test_audit_vanilla import FIXTURE


class KeyboardProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'source'
        shutil.copytree(FIXTURE,self.source)
        self.evidence=self.root/'evidence.json';self.out=self.root/'mod'

    def build(self,actions=False):
        if actions:
            p=self.source/'game/common/scripted_guis/actions.txt';p.parent.mkdir(exist_ok=True)
            p.write_text('fixture_action = { scope = country effect = { set_variable = fixture } }')
            (self.source/'game/gui/actions.gui').write_text('button = { onclick = "[GetScriptedGui(\'fixture_action\').Execute(GuiScope.SetRoot(JournalEntry.GetCountry.MakeScope).End)]" }\ntext_single = { text = "[JournalEntry.GetCountry.MakeScope.ScriptValue(\'fixture_value\')]" }')
            (self.source/'game/common/scripted_effects/fixture_journal.txt').write_text('fixture_register = { if = { limit = { NOT = { has_journal_entry = fixture_journal } } add_journal_entry = { type = fixture_journal } } }')
        a.write_evidence(a.audit_game(self.source),self.evidence)
        b.build_probe(self.source,self.evidence,self.out)
        return self.out

    def read(self,out,name):
        self.assertTrue((out/name).is_file(),'Missing generated keyboard artifact: '+name)
        return (out/name).read_text('utf-8-sig')

    def test_hotkey_is_bound_on_always_present_hud_button(self):
        out=self.build()
        hud=self.read(out,'gui/ingame_hud.gui')
        shortcuts=self.read(out,'gui/shortcuts.shortcuts')
        self.assertRegex(shortcuts,r'vic3_todo_toggle_probe\s*=\s*"ctrl\+shift\+T"')
        self.assertIn('shortcut = "vic3_todo_toggle_probe"',hud)
        self.assertIn("GetVariableSystem.Toggle('vic3_todo_keyboard_open')",hud)
        self.assertIn('name = "vic3_todo_keyboard_toggle"',hud)
        self.assertIn('name = "vic3_todo_keyboard_panel"',hud)
        self.assertNotIn('JournalEntry.',hud)

    def test_injections_preserve_every_original_source_byte(self):
        out=self.build()
        for name in ('gui/ingame_hud.gui','gui/shortcuts.shortcuts'):
            self.assertTrue((out/name).is_file())
            raw=(out/name).read_bytes()
            stripped=re.sub(rb'\n# vic3_todo_keyboard_begin\n.*?# vic3_todo_keyboard_end\n',b'',raw,flags=re.S)
            self.assertEqual(stripped,(self.source/'game'/name).read_bytes())

    def test_hud_uses_player_bindings_with_independent_localization(self):
        out=self.build(actions=True);hud=self.read(out,'gui/ingame_hud.gui')
        self.assertIn('GetPlayer.MakeScope',hud)
        self.assertIn('vic3_todo_keyboard_slot_0_current_label',hud)
        loc=(out/'localization/english/vic3_todo_probe_l_english.yml').read_text('utf-8-sig')
        self.assertRegex(loc,r'vic3_todo_keyboard_slot_0_current_label:.*GetPlayer.MakeScope.ScriptValue')
        self.assertNotRegex(loc,r'vic3_todo_keyboard_slot_0_current_label:.*JournalEntry')

    def test_keyboard_initialization_and_registration_are_guarded(self):
        out=self.build(actions=True)
        effects=b.parse_definitions((out/'common/scripted_effects/vic3_todo_probe_effects.txt').read_text())
        self.assertIn('vic3_todo_keyboard_initialize',effects)
        self.assertIn('vic3_todo_slot_0_create = yes',effects['vic3_todo_keyboard_initialize'])
        self.assertIn('vic3_todo_slot_1_create = yes',effects['vic3_todo_keyboard_initialize'])
        register=effects['vic3_todo_keyboard_register']
        self.assertEqual(register.count('add_journal_entry'),3)
        self.assertEqual(register.count('NOT = { has_journal_entry'),3)
        hud=self.read(out,'gui/ingame_hud.gui')
        self.assertIn('vic3_todo_keyboard_initialize_gui',hud)
        self.assertIn('vic3_todo_keyboard_register_gui',hud)

    def test_no_scripted_gui_callbacks_without_source_schema(self):
        out=self.build();hud=self.read(out,'gui/ingame_hud.gui')
        self.assertNotIn('GetScriptedGui(',hud)
        self.assertIn('vic3_todo_selector_limit',hud)
        meta=json.loads((out/'vic3_todo_keyboard_integration.json').read_text())
        self.assertFalse(meta['initialize_enabled']);self.assertFalse(meta['register_enabled'])

    def test_unproven_hud_root_is_rejected_before_publish(self):
        (self.source/'game/gui/ingame_hud.gui').write_text('widget = { name = "other" }')
        with self.assertRaisesRegex(ValueError,'ingame_hud root'):
            self.build()
        self.assertFalse(self.out.exists())

    def test_tampered_vanilla_hud_is_rejected(self):
        out=self.build();p=out/'gui/ingame_hud.gui'
        self.assertTrue(p.is_file())
        p.write_text(p.read_text().replace('existing_hud_child','deleted_hud_child'))
        with self.assertRaisesRegex(ValueError,'source-preserving'):
            b.validate_output(out)

    def test_existing_hotkey_collision_is_rejected(self):
        p=self.source/'game/gui/shortcuts.shortcuts'
        p.write_text('shortcutbindings = { existing = "ctrl+shift+t" }')
        with self.assertRaisesRegex(ValueError,'already bound'):
            self.build()
        self.assertFalse(self.out.exists())

    def test_source_bom_and_crlf_are_preserved(self):
        for name in ('gui/ingame_hud.gui','gui/shortcuts.shortcuts'):
            p=self.source/'game'/name
            p.write_bytes(b'\xef\xbb\xbf'+p.read_bytes().replace(b'\n',b'\r\n'))
        try:out=self.build()
        except ValueError as e:self.fail('Valid BOM/CRLF source was rejected: '+str(e))
        for name in ('gui/ingame_hud.gui','gui/shortcuts.shortcuts'):
            raw=(out/name).read_bytes()
            stripped=re.sub(rb'\n# vic3_todo_keyboard_begin\n.*?# vic3_todo_keyboard_end\n',b'',raw,flags=re.S)
            self.assertEqual(stripped,(self.source/'game'/name).read_bytes())


if __name__=='__main__':unittest.main()
