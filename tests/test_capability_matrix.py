import json
import tempfile
import unittest
from pathlib import Path
from tools import render_capability_matrix as m
from tools import build_probe as b
from tools import audit_vanilla as a
from tests.test_audit_vanilla import FIXTURE

class MatrixTests(unittest.TestCase):
    def test_all_ten_families_appear_once(self):
        rows=m.matrix_rows(a.audit_game(FIXTURE))
        self.assertEqual([x['tracker'] for x in rows],['Building level','GDP','Population','Literacy','Army size','Navy size','Technology','Law','Relations','Country rank'])
    def test_unsupported_not_rendered_supported(self):
        r=a.audit_game(FIXTURE);r['capabilities']['gdp']='unsupported'
        rows=m.matrix_rows(r);self.assertEqual(next(x for x in rows if x['tracker']=='GDP')['status'],'unsupported')
    def test_candidate_is_explicitly_unverified(self):
        rows=m.matrix_rows(a.audit_game(FIXTURE));row=next(x for x in rows if x['tracker']=='Population')
        self.assertEqual(row['status'],'supported-with-limitation');self.assertIn('candidate',row['limitation']);self.assertIn('insufficient coverage',row['limitation'])
    def test_limits_cite_evidence_path(self):
        row=m.matrix_rows(a.audit_game(FIXTURE))[0]
        self.assertIn('common/script_values/test.txt',row['evidence']);self.assertIn('runtime',row['limitation'])
    def test_progress_status_and_pin_are_gated(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);e=root/'e.json';r=a.audit_game(FIXTURE);r['capabilities']['journal_scripted_progress_bar']='unsupported';r['capabilities']['journal_pin']='unsupported';a.write_evidence(r,e)
            out=root/'mod';b.build_probe(FIXTURE,e,out)
            self.assertFalse((out/'common/scripted_progress_bars/vic3_todo_probe_progress_bars.txt').exists())
            je=(out/'common/journal_entries/vic3_todo_probe.txt').read_text()
            self.assertNotIn('scripted_progress_bar =',je)
            self.assertIn('status_desc',je)
            gui=(out/'gui/journal_entry_widgets/vic3_todo_probe_widget.gui').read_text();self.assertNotIn('TogglePinInOutliner',gui)
            self.assertIn('vic3_todo_pin_limit',gui)
if __name__=='__main__':unittest.main()
