import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools import audit_vanilla as a

FIXTURE = Path(__file__).parent / 'fixtures/vanilla_minimal'

class AuditTests(unittest.TestCase):
    def test_detects_required_gui_and_journal_evidence(self):
        r = a.audit_game(FIXTURE)
        for key in ('editbox','ontextedited','oneditingfinished','journal_custom_widget','journal_progress_bar','journal_scripted_progress_bar','journal_status_desc','journal_pin','script_variable','building_level_sum'):
            self.assertEqual(r['capabilities'][key], 'supported', key)
    def test_marks_missing_capability_unsupported_when_source_scope_is_complete(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t); (p/'game/gui').mkdir(parents=True); (p/'game/common').mkdir()
            (p/'phase0-source-coverage.json').write_text(json.dumps({'complete_directories':['gui','common']}))
            self.assertEqual(a.audit_game(p)['capabilities']['relations'],'unsupported')
    def test_marks_missing_archive_evidence_candidate_when_archive_scope_is_partial(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'source.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('wrapper/game/gui/journal.gui','widget = {}')
            r=a.audit_archive(p)
            self.assertEqual(r['capabilities']['relations'],'candidate')
            self.assertIn('insufficient coverage',r['capability_details']['relations']['reason'])
    def test_hashes_every_evidence_source(self):
        r=a.audit_game(FIXTURE)
        for e in r['evidence']:
            self.assertEqual(e['sha256'],hashlib.sha256((FIXTURE/'game'/e['path']).read_bytes()).hexdigest())
    def test_writes_utf8_json_without_ascii_escaping_japanese(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'r.json';a.write_evidence({'text':'日本で家具工場を10レベル建てる'},p)
            self.assertIn('日本',p.read_text());self.assertEqual(json.loads(p.read_text())['text'],'日本で家具工場を10レベル建てる')
    def test_rejects_traversal_absolute_windows_and_symlink_members(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.zip'
            for name in ('../escape','/tmp/escape','C:/escape','a\\..\\escape'):
                with zipfile.ZipFile(p,'w') as z:z.writestr(name,'x')
                with self.assertRaises(ValueError):a.audit_archive(p)
            with zipfile.ZipFile(p,'w') as z:
                i=zipfile.ZipInfo('link');i.external_attr=0o120777<<16;z.writestr(i,'/tmp')
            with self.assertRaises(ValueError):a.audit_archive(p)
    def test_ignores_commented_out_live_apis(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'gui').mkdir();(p/'gui/a.gui').write_text('# ontextedited = "[Fake.Edit]"\neditbox = {}')
            self.assertEqual(a.audit_game(p)['capabilities']['ontextedited'],'candidate')
    def test_detects_ambiguous_roots(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'a.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('a/game/gui/a.gui','');z.writestr('b/game/gui/b.gui','')
            with self.assertRaises(ValueError):a.audit_archive(p)

if __name__=='__main__':unittest.main()
