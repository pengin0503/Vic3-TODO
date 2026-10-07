import json
import shutil
import tempfile
import unittest
from pathlib import Path
from tools import install_probe as i
from tools import collect_results as c
from tools import audit_vanilla as a
from tools import build_probe as b
from tests.test_audit_vanilla import FIXTURE

class HandoffTests(unittest.TestCase):
    def test_collector_never_infers_pass(self):
        r=c.normalize_results({'unicode_input':'PASS','slot_isolation':'FAIL'})
        self.assertEqual(r['unicode_input'],'PASS');self.assertEqual(r['slot_isolation'],'FAIL')
        self.assertEqual(r['full_restart_text'],'NOT_TESTED')
        with self.assertRaises(ValueError):c.normalize_results({'unicode_input':'yes'})
    def test_bundle_copies_log_tail_and_records_user_reports_only(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);logs=p/'logs';logs.mkdir();(logs/'error.log').write_text('test error 日本\n')
            out=c.collect({'unicode_input':'FAIL'},p/'results',logs,notes='input lost')
            r=json.loads((out/'results.json').read_text())
            self.assertEqual(r['results']['unicode_input'],'FAIL');self.assertFalse(r['phase0_decision_executed'])
            self.assertIn('日本',(out/'error.log').read_text())
            self.assertFalse((out/'gui.log').exists())
    def test_installer_refuses_unrelated_mod_and_leaves_it_intact(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);out=p/'mod/Vic3TODOProbe';out.mkdir(parents=True);(out/'keep.txt').write_text('unrelated')
            with self.assertRaises(ValueError):i.publish_install(p/'missing',p/'mod')
            self.assertEqual((out/'keep.txt').read_text(),'unrelated')
    def test_installer_publishes_validated_mod_and_descriptor(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);e=p/'e.json';a.write_evidence(a.audit_game(FIXTURE),e);dist=p/'dist';b.build_probe(FIXTURE,e,dist)
            target=i.publish_install(dist,p/'userdata/mod')
            self.assertTrue((target/'.metadata/metadata.json').exists())
            descriptor=(target.parent/'Vic3TODOProbe.mod').read_text('utf-8')
            self.assertIn('supported_version="1.14.*"',descriptor);self.assertIn(target.as_posix(),descriptor)
    def test_archive_installed_comparison_records_hash_and_capability_differences(self):
        r=a.audit_game(FIXTURE);other=json.loads(json.dumps(r));other['source_hashes']['gui/journal_entry.gui']='different';other['capabilities']['relations']='unsupported'
        cmp=a.compare_reports(r,other);self.assertIn('gui/journal_entry.gui',cmp['hash_mismatches']);self.assertIn('relations',cmp['capability_differences'])
    def test_installer_protects_source_archive_before_any_output_write(self):
        import zipfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);game=p/'game';shutil.copytree(FIXTURE,game);(game/'binaries').mkdir();(game/'binaries/victoria3.exe').write_text('synthetic')
            repo=p/'repo';repo.mkdir();ud=p/'userdata';target=ud/'mod/Vic3TODOProbe';(target/'.metadata').mkdir(parents=True)
            (target/'.metadata/metadata.json').write_text(json.dumps({'id':'vic3_todo_probe'}))
            archive=target/'source.zip'
            with zipfile.ZipFile(archive,'w') as z:
                for f in FIXTURE.rglob('*'):
                    if f.is_file():z.write(f,f.relative_to(FIXTURE))
            before=archive.read_bytes()
            with patch.object(i,'ROOT',repo):
                with self.assertRaises(ValueError):i.install(game,ud,archive)
            self.assertEqual(archive.read_bytes(),before);self.assertFalse((repo/'research').exists())
    def test_installer_rejects_repo_in_game_before_evidence_writes(self):
        import zipfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);game=p/'game';shutil.copytree(FIXTURE,game);(game/'binaries').mkdir();(game/'binaries/victoria3.exe').write_text('synthetic')
            repo=game/'project';repo.mkdir();archive=p/'source.zip'
            with zipfile.ZipFile(archive,'w') as z:
                for f in FIXTURE.rglob('*'):
                    if f.is_file():z.write(f,f.relative_to(FIXTURE))
            with patch.object(i,'ROOT',repo):
                with self.assertRaises(ValueError):i.install(game,p/'userdata',archive)
            self.assertFalse((repo/'research').exists())

if __name__=='__main__':unittest.main()
