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
    from tools.audit_vanilla import audit, read_source, write_evidence
except ModuleNotFoundError:
    from audit_vanilla import audit, read_source, write_evidence

PROBE_SOURCE=Path(__file__).resolve().parents[1]/'probe_src'
MANDATORY=('journal_custom_widget','script_variable')
ALLOWED_GUI={'gui/journal_entry_widgets/vic3_todo_probe_widget.gui'}

def parse_definitions(text):
    """Read top-level PDX definitions, respecting comments, strings and braces."""
    clean=re.sub(r'#[^\n]*','',text)
    tokens=list(re.finditer(r'"(?:[^"\\]|\\.)*"|[{}=]|[^\s{}=]+',clean))
    result={};i=0
    while i<len(tokens):
        if i+2>=len(tokens) or tokens[i+1].group()!='=' or tokens[i+2].group()!='{':
            raise ValueError('Invalid top-level PDX definition')
        name=tokens[i].group();start=tokens[i+2].end();depth=1;j=i+3
        while j<len(tokens) and depth:
            token=tokens[j].group()
            if token=='{':depth+=1
            elif token=='}':depth-=1
            j+=1
        if depth:raise ValueError('Unbalanced PDX braces')
        if name in result:raise ValueError('Duplicate definition: '+name)
        result[name]=clean[start:tokens[j-1].start()];i=j
    return result

def add_slot_probes(stage,r):
    caps=r['capabilities']
    values=stage/'common/script_values/vic3_todo_probe_values.txt'
    if not values.exists():return
    if caps.get('building_level_sum')!='supported':
        raise ValueError('Building level-sum evidence required for numeric slots')
    effects=stage/'common/scripted_effects/vic3_todo_probe_effects.txt'
    v=values.read_text('utf-8');e=effects.read_text('utf-8')
    technology=caps.get('technology_trigger')=='supported' and caps.get('technology_target')=='supported'
    relations=caps.get('relations_numeric')=='supported'
    # Technology is boolean: 0/1 only, baseline still recorded for isolation, never used as a fractional research metric.
    if technology:
        v+='\nvic3_todo_technology_current = { value = 0 if = { limit = { has_technology_researched = telephone } value = 1 } }\n'
        for i in (0,1):
            name=f'vic3_todo_slot_{i}_current'
            old=parse_definitions(v)[name]
            v=v.replace(name+' = {'+old+'}',name+' = {'+old+f'    if = {{ limit = {{ var:vic3_todo_slot_{i}_target = 3 }} value = vic3_todo_technology_current }}\n'+'}')
            name=f'vic3_todo_slot_{i}_progress';old=parse_definitions(v)[name]
            v=v.replace(name+' = {'+old+'}',name+' = {'+old+f'    if = {{ limit = {{ var:vic3_todo_slot_{i}_target = 3 }} value = vic3_todo_technology_current }}\n'+'}')
            name=f'vic3_todo_slot_{i}_ratio';old=parse_definitions(v)[name]
            v=v.replace(name+' = {'+old+'}',name+' = {'+old+f'    if = {{ limit = {{ var:vic3_todo_slot_{i}_target = 3 }} value = vic3_todo_technology_current multiply = 100 }}\n'+'}')
            # Separate boolean completion contract; numeric goal must not block technology satisfaction.
            triggers=stage/'common/scripted_triggers/vic3_todo_probe_triggers.txt'
            ts=triggers.read_text('utf-8')
            key=f'vic3_todo_slot_{i}_satisfied'
            block=parse_definitions(ts)[key]
            ts=ts.replace(key+' = {'+block+'}',key+' = { OR = { AND = { var:vic3_todo_slot_'+str(i)+'_target = 3 has_technology_researched = telephone } AND = { NOT = { var:vic3_todo_slot_'+str(i)+'_target = 3 } vic3_todo_slot_'+str(i)+'_progress >= var:vic3_todo_slot_'+str(i)+'_goal } } }')
            triggers.write_text(ts,encoding='utf-8')
    if relations:
        # Primary numeric scope evidence: c:USA.relations:root / c:CSA.relations:root in ip4_cuba_values.txt.
        v+='\nvic3_todo_relations_gbr = { value = 0 if = { limit = { exists = c:GBR } add = c:GBR.relations:root } }\n'
        v+='vic3_todo_relations_fra = { value = 0 if = { limit = { exists = c:FRA } add = c:FRA.relations:root } }\n'
        for i in (0,1):
            name=f'vic3_todo_slot_{i}_current';old=parse_definitions(v)[name]
            extra=f' if = {{ limit = {{ var:vic3_todo_slot_{i}_target = 4 }} value = vic3_todo_relations_gbr }} if = {{ limit = {{ var:vic3_todo_slot_{i}_target = 5 }} value = vic3_todo_relations_fra }}\n'
            v=v.replace(name+' = {'+old+'}',name+' = {'+old+extra+'}')
            for action,n in (('select_gbr',4),('select_fra',5)):
                p=f'vic3_todo_slot_{i}_'
                e+=f'{p}{action} = {{ if = {{ limit = {{ NOT = {{ var:{p}target = {n} }} }} set_variable = {{ name = {p}target value = {n} }} {p}capture = yes }} }}\n'
    if not technology:
        for i in (0,1):
            key=f'vic3_todo_slot_{i}_select_technology';old=parse_definitions(e)[key]
            e=e.replace(key+' = {'+old+'}','')
    triggers=stage/'common/scripted_triggers/vic3_todo_probe_triggers.txt';ts=triggers.read_text('utf-8')
    for i in (0,1):
        p=f'vic3_todo_slot_{i}_'
        choices=f'var:{p}target = 1 var:{p}target = 2'
        if technology:choices+=f' var:{p}target = 3'
        if relations:
            choices+=f' AND = {{ var:{p}target = 4 exists = c:GBR NOT = {{ c:GBR = root }} }} AND = {{ var:{p}target = 5 exists = c:FRA NOT = {{ c:FRA = root }} }}'
        ts+=f'\n{p}target_valid = {{ OR = {{ {choices} }} }}\n'
        old=parse_definitions(ts)[p+'satisfied']
        ts=ts.replace(p+'satisfied = {'+old+'}',p+'satisfied = { '+p+'target_valid = yes '+old+'}')
        old=parse_definitions(v)[p+'progress']
        v=v.replace(p+'progress = {'+old+'}',p+'progress = {'+old+f' if = {{ limit = {{ NOT = {{ {p}target_valid = yes }} }} value = 0 }} '+'}')
    triggers.write_text(ts,encoding='utf-8')
    values.write_text(v,encoding='utf-8');effects.write_text(e,encoding='utf-8')
    gui=stage/'gui/journal_entry_widgets/vic3_todo_probe_widget.gui'
    g=gui.read_text('utf-8');parts=[]
    if caps.get('script_value_binding')=='supported':
        for i in (0,1):
            for metric in ('current','baseline_display','goal_display','target_display','mode_display','capture_count_display','completed_display','label_display','progress'):
                key=f'vic3_todo_slot_{i}_{metric}'
                label=key+'_label'
                for lang in ('english','japanese'):
                    loc=stage/f'localization/{lang}/vic3_todo_probe_l_{lang}.yml'
                    with loc.open('a',encoding='utf-8') as f:
                        f.write(f' {label}: "Slot {i} {metric}: [JournalEntry.GetCountry.MakeScope.ScriptValue(\'{key}\')|v0]"\n')
                parts.append(f'        text_single = {{ text = "{label}" }}')
    actions_ready=caps.get('scripted_gui_definition')=='supported' and caps.get('scripted_gui_execution')=='supported'
    if actions_ready:
        definitions=[]
        for key in parse_definitions(e):
            if key.endswith(('_capture','_create')):continue
            # Emit only after an actual country scope + effect declaration is present in same source file.
            definitions.append(f'{key}_gui = {{ scope = country effect = {{ {key} = yes }} }}')
            # The full Execute+GuiScope+JournalEntry.GetCountry.MakeScope chain is evidenced by ep2_japan_widgets.gui.
            for lang in ('english','japanese'):
                loc=stage/f'localization/{lang}/vic3_todo_probe_l_{lang}.yml'
                with loc.open('a',encoding='utf-8') as f:
                    f.write(f' {key}: "'+key.replace('vic3_todo_slot_','Slot ').replace('_',' ')+'"\n')
            parts.append(f'        button = {{ using = default_button_action size = {{ 460 30 }} text = "{key}" onclick = "[GetScriptedGui(\'{key}_gui\').Execute(GuiScope.SetRoot(JournalEntry.GetCountry.MakeScope).End)]" }}')
        p=stage/'common/scripted_guis/vic3_todo_probe_actions.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('\n'.join(definitions)+'\n',encoding='utf-8')
    else:parts.append('        text_single = { text = "vic3_todo_selector_limit" }')
    g=g.replace('        text_single = { text = "vic3_todo_text_storage_limit" }','        text_single = { text = "vic3_todo_text_storage_limit" }\n'+'\n'.join(parts))
    gui.write_text(g,encoding='utf-8')
    write_evidence({'slot_count':2,'tracker_count_per_slot':1,'selector_ui':'static-evidence-ready' if actions_ready else 'candidate-insufficient-coverage','technology_probe':technology,'relations_probe':relations,'runtime_verified':False},stage/'vic3_todo_slot_capabilities.json')

def add_presentation(stage,r):
    caps=r['capabilities'];je=stage/'common/journal_entries/vic3_todo_probe.txt'
    text=je.read_text('utf-8');bars=stage/'common/scripted_progress_bars/vic3_todo_probe_progress_bars.txt'
    bar_ready=caps.get('journal_scripted_progress_bar')=='supported' and caps.get('bar_update')=='supported'
    if not bar_ready and bars.exists():bars.unlink()
    for i in (0,1):
        key=f'vic3_todo_slot_{i}_probe';block=parse_definitions(text)[key];extra=''
        if caps.get('journal_status_desc')=='supported':
            extra+=f"""
    status_desc = {{ first_valid = {{
        triggered_desc = {{ desc = vic3_todo_status_completed trigger = {{ var:vic3_todo_slot_{i}_completed = 1 }} }}
        triggered_desc = {{ desc = vic3_todo_status_invalid trigger = {{ NOT = {{ vic3_todo_slot_{i}_target_valid = yes }} }} }}
        triggered_desc = {{ desc = vic3_todo_status_satisfied trigger = {{ vic3_todo_slot_{i}_satisfied = yes }} }}
        triggered_desc = {{ desc = vic3_todo_status_in_progress trigger = {{ always = yes }} }}
    }} }}
"""
        if bar_ready:
            extra+=f"""
    scripted_progress_bar = vic3_todo_slot_{i}_bar
    on_weekly_pulse = {{ effect = {{ scope:journal_entry = {{
        set_bar_progress = {{ value = ROOT.vic3_todo_slot_{i}_ratio name = vic3_todo_slot_{i}_bar }}
    }} }} }}
"""
        text=text.replace(key+' = {'+block+'}',key+' = {'+block+extra+'}')
    je.write_text(text,encoding='utf-8')
    gui=stage/'gui/journal_entry_widgets/vic3_todo_probe_widget.gui';g=gui.read_text('utf-8')
    if caps.get('journal_pin')=='supported':
        pin='        button = { using = default_button_action size = { 460 30 } text = "vic3_todo_pin_toggle" onclick = "[JournalEntry.TogglePinInOutliner]" }'
    else:pin='        text_single = { text = "vic3_todo_pin_limit" }'
    if caps.get('technology_trigger')=='supported' and caps.get('technology_target')=='supported' and caps.get('script_value_binding')=='supported':
        pin+='\n        text_single = { text = "vic3_todo_technology_status" }'
    g=g.replace('        text_single = { text = "vic3_todo_unicode" }','        text_single = { text = "vic3_todo_unicode" }\n'+pin)
    gui.write_text(g,encoding='utf-8')
    write_evidence({'scripted_progress_bar':bar_ready,'bar_update_cadence':'weekly','pin':'vanilla-journal-toggle' if caps.get('journal_pin')=='supported' else 'candidate-or-unsupported','status':caps.get('journal_status_desc'),'runtime_verified':False},stage/'vic3_todo_presentation_capabilities.json')

def validate_output(output_dir,source=None):
    output_dir=Path(output_dir)
    definitions=set()
    loc_keys={}
    journals={};groups={};building_references=set()
    for p in output_dir.rglob('*'):
        if p.is_symlink():raise ValueError('Symlink in probe')
        if not p.is_file():continue
        n=p.relative_to(output_dir).as_posix()
        if n.startswith('gui/') and n not in ALLOWED_GUI:raise ValueError('Unapproved vanilla GUI override: '+n)
        if p.suffix=='.txt':
            text=p.read_text('utf-8-sig');blocks=parse_definitions(text)
            if n.startswith('common/journal_entries/'):journals.update(blocks)
            if n.startswith('common/journal_entry_groups/'):groups.update(blocks)
            building_references.update(re.findall(r'\bis_building_type\s*=\s*(\w+)',text))
            for key in blocks:
                if not key.startswith('vic3_todo_') or key in definitions:raise ValueError('Unnamespaced or duplicate PDX definition: '+key)
                definitions.add(key)
        if p.suffix=='.gui':parse_definitions(p.read_text('utf-8-sig'))
        if p.suffix=='.yml':
            keys=re.findall(r'^\s+(\w+):',p.read_text('utf-8-sig'),re.MULTILINE)
            if len(keys)!=len(set(keys)) or any(not k.startswith('vic3_todo_') for k in keys):raise ValueError('Duplicate or unnamespaced localization')
            loc_keys[p.parent.name]=set(keys)
        if p.suffix in ('.gui','.txt','.yml'):
            s=p.read_text('utf-8-sig')
            if re.search(r'\b(set_name|rename_state|rename_company|set_country_name|SetTextPersistent|SaveTodoText)\b',s):raise ValueError('Unverified callback or visible-name storage')
            if re.search(r'\b(TBD|FIXME|PLACEHOLDER)\b',s):raise ValueError('Unfinished release marker')
    if loc_keys.get('english')!=loc_keys.get('japanese'):raise ValueError('Localization key coverage differs')
    for key,body in journals.items():
        group=re.search(r'\bgroup\s*=\s*(\w+)',body)
        if not group or not re.search(r'\bcontext\s*=\s*country\b',groups.get(group[1],'')):
            raise ValueError('Journal requires a defined country-context group: '+key)
        for lang in ('english','japanese'):
            if not {key,key+'_reason'}.issubset(loc_keys.get(lang,set())):
                raise ValueError('Missing Journal localization in '+lang+': '+key)
    if source is not None:
        _,_,data,_=read_source(source)
        building_ids=set()
        for name,raw in data.items():
            if name.startswith('common/buildings/') and name.endswith('.txt'):
                # Only actual database declarations qualify; aliases are not trigger IDs.
                building_ids.update(re.findall(r'^\s*(building_\w+)\s*=\s*\{',raw.decode('utf-8-sig'),re.MULTILINE))
        missing=building_references-building_ids
        if missing:raise ValueError('Undefined building type in source: '+', '.join(sorted(missing)))
    md=json.loads((output_dir/'.metadata/metadata.json').read_text('utf-8'))
    if md.get('supported_game_version')!='1.14.*':raise ValueError('Wrong game version')
    for lang in ('english','japanese'):
        raw=(output_dir/f'localization/{lang}/vic3_todo_probe_l_{lang}.yml').read_bytes()
        if not raw.startswith(b'\xef\xbb\xbf'):raise ValueError('Localization requires UTF-8 BOM')
        if not raw.decode('utf-8-sig').startswith('l_'+lang+':'):raise ValueError('Wrong localization header')

def guard_output(source,evidence,output):
    # Check the lexical path before resolve(), which hides final-component symlinks.
    if output.is_symlink():raise ValueError('Output must not be a symlink')
    output=output.resolve()
    for protected in (source.resolve(),PROBE_SOURCE.resolve(),evidence.resolve()):
        if output==protected or output in protected.parents or (protected.is_dir() and output.is_relative_to(protected)):
            raise ValueError('Output overlaps protected source/evidence/probe tree')
    if output.is_relative_to(PROBE_SOURCE.parent.resolve()) and not output.is_relative_to((PROBE_SOURCE.parent/'dist').resolve()):
        raise ValueError('Output overlaps repository source files')
    if output.exists():
        if not output.is_dir():raise ValueError('Output must be a real directory')
        metadata=output/'.metadata/metadata.json';manifest=output/'vic3_todo_build_manifest.json'
        if not metadata.is_file() or not manifest.is_file() or json.loads(metadata.read_text('utf-8')).get('id')!='vic3_todo_probe':
            raise ValueError('Refusing to replace unrelated existing output directory')

def build_probe(game_dir,evidence_path,output_dir):
    source=Path(game_dir);evidence=Path(evidence_path);output=Path(output_dir)
    guard_output(source,evidence,output)
    r=json.loads(evidence.read_text('utf-8'));actual=audit(source)
    if actual['source_hashes']!=r.get('source_hashes') or actual['source_identity']['source_set_sha256']!=r.get('source_identity',{}).get('source_set_sha256'):
        raise ValueError('Evidence does not match read-only source')
    for key,status in r.get('capabilities',{}).items():
        if status=='supported' and actual['capabilities'].get(key)!='supported':
            raise ValueError('Evidence upgrades an unproven source API: '+key)
    for c in MANDATORY:
        if r.get('capabilities',{}).get(c)!='supported':raise ValueError('Missing mandatory static evidence: '+c)
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.vic3_todo_build_',dir=output.parent));backup=None
    try:
        shutil.copytree(PROBE_SOURCE,stage,dirs_exist_ok=True)
        add_slot_probes(stage,r)
        add_presentation(stage,r)
        for p in sorted(stage.rglob('*.yml')):
            s=p.read_text('utf-8-sig');p.write_bytes(b'\xef\xbb\xbf'+s.encode('utf-8'))
        write_evidence({'free_text_persistence':r['capability_details']['free_text_persistence'],
                        'unicode_input':'日本で家具工場を10レベル建てる',
                        'input_only':True,'runtime_verified':False}, stage/'vic3_todo_probe_capabilities.json')
        validate_output(stage,source)
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
