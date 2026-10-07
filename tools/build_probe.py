"""Deterministic source-bound Phase 0 builder; no vanilla GUI overrides."""
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
try:
    from tools.audit_vanilla import audit, write_evidence
except ModuleNotFoundError:
    from audit_vanilla import audit, write_evidence

PROBE_SOURCE=Path(__file__).resolve().parents[1]/'probe_src'
MANDATORY=('journal_custom_widget','script_variable')
ALLOWED_GUI={'gui/journal_entry_widgets/vic3_todo_probe_widget.gui'}

def validate_output(output_dir):
    output_dir=Path(output_dir)
    for p in output_dir.rglob('*'):
        if p.is_symlink():raise ValueError('Symlink in probe')
        if not p.is_file():continue
        n=p.relative_to(output_dir).as_posix()
        if n.startswith('gui/') and n not in ALLOWED_GUI:raise ValueError('Unapproved vanilla GUI override: '+n)
        if p.suffix in ('.gui','.txt','.yml'):
            s=p.read_text('utf-8-sig')
            if re.search(r'\b(set_name|rename_state|rename_company|set_country_name|SetTextPersistent|SaveTodoText)\b',s):raise ValueError('Unverified callback or visible-name storage')
            if re.search(r'\b(TBD|FIXME|PLACEHOLDER)\b',s):raise ValueError('Unfinished release marker')
    md=json.loads((output_dir/'.metadata/metadata.json').read_text('utf-8'))
    if md.get('supported_game_version')!='1.14.*':raise ValueError('Wrong game version')
    for lang in ('english','japanese'):
        raw=(output_dir/f'localization/{lang}/vic3_todo_probe_l_{lang}.yml').read_bytes()
        if not raw.startswith(b'\xef\xbb\xbf'):raise ValueError('Localization requires UTF-8 BOM')
        if not raw.decode('utf-8-sig').startswith('l_'+lang+':'):raise ValueError('Wrong localization header')

def guard_output(source,evidence,output):
    output=output.resolve()
    for protected in (source.resolve(),PROBE_SOURCE.resolve(),evidence.resolve()):
        if output==protected or output in protected.parents or (protected.is_dir() and output.is_relative_to(protected)):
            raise ValueError('Output overlaps protected source/evidence/probe tree')
    if output.exists() and (not output.is_dir() or output.is_symlink()):raise ValueError('Output must be a real directory')

def build_probe(game_dir,evidence_path,output_dir):
    source=Path(game_dir);evidence=Path(evidence_path);output=Path(output_dir)
    guard_output(source,evidence,output)
    r=json.loads(evidence.read_text('utf-8'));actual=audit(source)
    if actual['source_hashes']!=r.get('source_hashes') or actual['source_identity']['source_set_sha256']!=r.get('source_identity',{}).get('source_set_sha256'):
        raise ValueError('Evidence does not match read-only source')
    for c in MANDATORY:
        if r.get('capabilities',{}).get(c)!='supported':raise ValueError('Missing mandatory static evidence: '+c)
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.vic3_todo_build_',dir=output.parent));backup=None
    try:
        shutil.copytree(PROBE_SOURCE,stage,dirs_exist_ok=True)
        for p in sorted(stage.rglob('*.yml')):
            s=p.read_text('utf-8-sig');p.write_bytes(b'\xef\xbb\xbf'+s.encode('utf-8'))
        write_evidence({'free_text_persistence':r['capability_details']['free_text_persistence'],
                        'unicode_input':'日本で家具工場を10レベル建てる',
                        'input_only':True,'runtime_verified':False}, stage/'vic3_todo_probe_capabilities.json')
        validate_output(stage)
        manifest={'schema_version':1,'source_identity':r['source_identity'],'capabilities':r['capabilities'],'runtime_verified':False,'files':{p.relative_to(stage).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob('*')) if p.is_file()}}
        write_evidence(manifest,stage/'vic3_todo_build_manifest.json')
        if output.exists():
            backup=Path(tempfile.mkdtemp(prefix='.vic3_todo_backup_',dir=output.parent));backup.rmdir();os.replace(output,backup)
        try:os.replace(stage,output)
        except BaseException:
            if backup is not None:os.replace(backup,output);backup=None
            raise
        if backup is not None:shutil.rmtree(backup)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return [p for p in sorted(output.rglob('*')) if p.is_file()]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--game-dir',type=Path);g.add_argument('--source-archive',type=Path)
    p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(argv)
    try:files=build_probe(args.game_dir or args.source_archive,args.evidence,args.output)
    except (ValueError,OSError) as e:p.error(str(e))
    print('Built '+str(len(files))+' files; runtime verification pending');return 0
if __name__=='__main__':raise SystemExit(main())
