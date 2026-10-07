"""Collect explicit user reports and local log evidence, never execute the Phase 0 decision."""
import argparse
from collections import deque
from datetime import datetime,timezone
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
CHECKS=('journal_integration','unicode_input','ascii_punctuation_input','length_200_input','empty_input','newline_input','journal_reopen_text','save_load_text','full_restart_text','slot_isolation','slot_completion','baseline_persistence','cosmetic_preserves_baseline','reconfiguration_once','selector_ui','tracker_target_config_persistence','relations_target_binding','building_net_delta','progress_update','technology_boolean','dynamic_status','pinning','pin_persistence','error_log_clean','gui_log_clean')
CHECKS+=('keyboard_open','keyboard_hud_button','keyboard_register')
STATUSES={'PASS','FAIL','NOT_TESTED'}
ROOT=Path(__file__).resolve().parents[1]

def normalize_results(answers):
    if set(answers)-set(CHECKS):raise ValueError('Unknown result key')
    result={}
    for key in CHECKS:
        value=answers.get(key,'NOT_TESTED')
        if value not in STATUSES:raise ValueError(f'Expected PASS/FAIL/NOT_TESTED for {key}')
        result[key]=value
    return result

def collect(answers,output_root,log_dir,notes='',mod_dir=None,game_version='NOT_RECORDED'):
    results=normalize_results(answers);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=Path(output_root)/('vic3_todo_phase0_'+stamp);out.mkdir(parents=True,exist_ok=False)
    try:commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):commit='NOT_RECORDED'
    payload={'schema_version':1,'recorded_at_utc':stamp,'results':results,'result_origin':'explicit user report; not automatically validated','notes':notes,'game_version_reported':game_version,'project_commit':commit,'phase0_decision_executed':False,'logs':{}}
    for name in ('error.log','gui.log','game.log'):
        p=Path(log_dir)/name
        if p.is_file():
            with p.open('r',encoding='utf-8-sig',errors='replace') as f:tail=''.join(deque(f,maxlen=300))
            (out/name).write_text(tail,encoding='utf-8');payload['logs'][name]={'present':True,'tail_lines':300,'sha256':hashlib.sha256(tail.encode()).hexdigest()}
        else:payload['logs'][name]={'present':False}
    for name in ('phase0-api-evidence.json','installed-archive-evidence.json','installed-api-evidence.json','source-comparison.json'):
        p=ROOT/'research/generated'/name
        if p.is_file():shutil.copy2(p,out/name)
    if mod_dir:
        for name in ('vic3_todo_build_manifest.json','vic3_todo_keyboard_integration.json'):
            p=Path(mod_dir)/name
            if p.is_file():shutil.copy2(p,out/p.name)
    (out/'results.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'results.txt').write_text('\n'.join([f'{k}: {v}' for k,v in results.items()])+f'\n\nNotes: {notes}\n\nNo Phase 0 decision executed.\n',encoding='utf-8')
    with zipfile.ZipFile(out.with_suffix('.zip'),'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,p.name)
    return out

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--answers',type=Path,required=True);p.add_argument('--log-dir',type=Path,required=True);p.add_argument('--output-root',type=Path,default=ROOT/'research/runtime');p.add_argument('--mod-dir',type=Path);p.add_argument('--game-version',default='NOT_RECORDED');p.add_argument('--notes',default='')
    args=p.parse_args(argv)
    try:out=collect(json.loads(args.answers.read_text('utf-8-sig')),args.output_root,args.log_dir,args.notes,args.mod_dir,args.game_version)
    except (ValueError,OSError) as e:p.error(str(e))
    print(out.with_suffix('.zip'));return 0
if __name__=='__main__':raise SystemExit(main())
