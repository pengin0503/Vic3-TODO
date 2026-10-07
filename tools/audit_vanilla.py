"""Read-only, bounded ZIP/tree inspection. 'supported' means static API evidence only."""
import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

# Candidate locations are restricted to GUI and common modding data.
RULES = {
 'editbox': ('gui/', r'\beditbox\s*=\s*\{'),
 'ontextedited': ('gui/', r'\bontextedited\s*='),
 'oneditingfinished': ('gui/', r'\boneditingfinished\s*='),
 'journal_custom_widget': ('common/journal_entries/', r'\bwidget\s*=\s*\{'),
 'journal_progress_bar': ('common/journal_entries/', r'\bprogressbar\s*=\s*yes'),
 'journal_scripted_progress_bar': ('common/journal_entries/', r'\bscripted_progress_bar\s*='),
 'journal_status_desc': ('common/journal_entries/', r'\bstatus_desc\s*='),
 'journal_pin': ('gui/', r'JournalEntry\.TogglePinInOutliner'),
 'script_variable': ('common/', r'\bset_variable\s*='),
 'building_level_sum': ('common/script_values/', r'\bevery_scope_building\s*='),
 'gdp': ('common/', r'\b(?:value|add)\s*=\s*(?:[\w:]+\.)?gdp\b'),
 'total_population': ('common/', r'\b(?:value|add)\s*=\s*(?:[\w:]+\.)?total_population\b'),
 'literacy_rate': ('common/', r'\b(?:value|add)\s*=\s*(?:[\w:]+\.)?literacy_rate\b'),
 'army_size': ('common/', r'\b(?:value|add)\s*=\s*(?:[\w:]+\.)?army_size\b'),
 'navy_size': ('common/', r'\b(?:value|add)\s*=\s*(?:[\w:]+\.)?navy_size\b'),
 'technology_trigger': ('common/', r'\bhas_technology_researched\s*='),
 'law_trigger': ('common/', r'\bhas_law\s*='),
 'relations': ('common/', r'\b(?:[\w:]+\.)?relations:(?:ROOT|root|scope:[\w_]+)'),
 'country_rank': ('common/', r'\bcountry_rank\s*(?:=|[<>]=?)'),
 # Extra evidence used to gate independently buildable probes.
 'scripted_gui_execution': ('gui/', r'GetScriptedGui\([^\n]+\.Execute\(GuiScope\.SetRoot\(JournalEntry\.GetCountry\.MakeScope\)\.End\)'),
 'scripted_gui_definition': ('common/scripted_guis/', r'\bscope\s*=\s*country'),
 'script_value_binding': ('gui/', r'MakeScope\.ScriptValue\('),
 'bar_update': ('common/', r'\bset_bar_progress\s*='),
 'player_trigger': ('common/', r'\bis_player\s*=\s*yes'),
 'furniture_target': ('common/buildings/', r'\bbuilding_furniture_manufacturies\b'),
 'technology_target': ('common/technology/', r'^telephone\s*='),
 'law_target': ('common/laws/', r'^law_universal_suffrage\s*='),
}
MAX_BYTES = 256 * 1024 * 1024
MAX_FILES = 50000

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe_member(info):
    name=info.filename; p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or stat.S_ISLNK(info.external_attr >> 16):
        raise ValueError('Unsafe ZIP member: '+name)
    return p

def detect_root(names):
    roots=set()
    for name in names:
        parts=PurePosixPath(name).parts
        if not parts or parts[0]=='__MACOSX':continue
        for i,part in enumerate(parts):
            if part in ('gui','common'):
                roots.add('/'.join(parts[:i]));break
    if len(roots)!=1:raise ValueError('Expected exactly one GUI/common source root, found '+repr(sorted(roots)))
    return next(iter(roots))

def read_source(path):
    """Never extracts ZIP data; validates every member before reading any payload."""
    path=Path(path)
    if path.is_file():
        with zipfile.ZipFile(path) as z:
            infos=z.infolist()
            if len(infos)>MAX_FILES or sum(i.file_size for i in infos)>MAX_BYTES:raise ValueError('Source limit exceeded')
            for i in infos:safe_member(i)
            names=[i.filename for i in infos if not i.is_dir() and not i.filename.startswith('__MACOSX/')]
            if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP member')
            root=detect_root(names);prefix=root+'/' if root else ''
            data={n[len(prefix):]:z.read(n) for n in sorted(names) if n.startswith(prefix) and n[len(prefix):].startswith(('gui/','common/','localization/'))}
            coverage={}
            for n in (prefix+'phase0-source-coverage.json','phase0-source-coverage.json'):
                if n in names:coverage=json.loads(z.read(n))
            identity={'name':path.name,'sha256':sha(path.read_bytes()),'root':root,'version':'1.14.5 (user supplied, not independently proven)','entry_count':len(infos),'archive_members':sorted(i.filename for i in infos)}
        return 'archive',identity,data,coverage
    if not path.is_dir():raise ValueError('Source does not exist')
    # Scan relevant candidates without following symlinks.
    names=[]
    for p in path.rglob('*'):
        if p.is_file() and not p.is_symlink() and not any(x.is_symlink() for x in p.parents if x!=path):
            names.append(p.relative_to(path).as_posix())
    root_names=names+[p.relative_to(path).as_posix()+'/__root_marker__' for p in path.rglob('*') if p.is_dir() and p.name in ('gui','common') and not p.is_symlink()]
    root=detect_root(root_names);base=path/root;data={}
    for n in sorted(names):
        p=Path(n)
        try:relative=p.relative_to(root).as_posix() if root else n
        except ValueError:continue
        if relative.startswith(('gui/','common/','localization/')):
            data[relative]=(path/n).read_bytes()
    if len(data)>MAX_FILES or sum(map(len,data.values()))>MAX_BYTES:raise ValueError('Source limit exceeded')
    cp=base/'phase0-source-coverage.json'
    if not cp.exists():cp=path/'phase0-source-coverage.json'
    coverage=json.loads(cp.read_text('utf-8')) if cp.exists() else {}
    # An installation marker proves GUI/common completeness only when the caller supplies a full install.
    installed=(path/'binaries/victoria3.exe').is_file() and (base/'common').is_dir() and (base/'gui').is_dir()
    if installed:coverage={'complete_directories':['gui','common'],'basis':'installation executable and game roots; user must verify unmodified installation'}
    return 'tree',{'name':path.name,'root':root,'version':'verify installed version manually','installed_marker':installed},data,coverage

def audit(path):
    kind,identity,data,coverage=read_source(path)
    hashes={n:sha(b) for n,b in sorted(data.items())}
    evidence=[];caps={};details={}
    complete=coverage.get('complete_directories',[])
    for key,(location,pattern) in RULES.items():
        matches=[]
        for n,b in sorted(data.items()):
            if not n.startswith(location) or Path(n).suffix not in ('.txt','.gui','.md'):continue
            text=b.decode('utf-8-sig',errors='replace')
            if Path(n).suffix!='.md':text=re.sub(r'#[^\n]*','',text) # strings containing markup aren't evidence for our patterns
            found=list(re.finditer(pattern,text,re.MULTILINE))
            if key=='building_level_sum' and not (re.search(r'\badd\s*=\s*(?:this\.)?level',text) and 'is_building_type' in text):found=[]
            if key=='scripted_gui_definition' and not re.search(r'\beffect\s*=\s*\{',text):found=[]
            for m in found[:2]:
                line=text.count('\n',0,m.start())+1
                matches.append({'capability':key,'path':n,'line':line,'snippet':text[m.start():min(m.end()+100,len(text))].split('\n')[0],'sha256':hashes[n]})
            if len(matches)>=6:break
        is_complete=any(location.startswith(x.rstrip('/')+'/') or location.rstrip('/')==x.rstrip('/') for x in complete)
        status='supported' if matches else ('unsupported' if is_complete else 'candidate')
        reason='Static syntax evidence; runtime behavior unverified' if matches else ('No match in declared complete candidate scope' if is_complete else 'No match; insufficient coverage of authoritative source set')
        caps[key]=status;details[key]={'status':status,'reason':reason,'coverage_complete':is_complete,'evidence_paths':sorted({x['path'] for x in matches})}
        evidence.extend(matches)
    # Editbox callbacks are engine-owned examples, never proof of mod-owned string serialization.
    caps['free_text_persistence']='candidate'
    details['free_text_persistence']={'status':'candidate','reason':'No verified editbox-to-mod-owned save-string bridge. Engine name callbacks are excluded; not an exhaustive engine API inventory.','evidence_paths':details['ontextedited']['evidence_paths'],'coverage_complete':False}
    tree_digest=sha(json.dumps(hashes,sort_keys=True).encode())
    identity['source_set_sha256']=tree_digest
    return {'schema_version':1,'source_kind':kind,'source_identity':identity,'source_hashes':hashes,'source_coverage':coverage,'directory_counts':{d:sum(n.startswith(d+'/') for n in data) for d in sorted({n.rsplit('/',1)[0] for n in data})},'capabilities':caps,'capability_details':details,'evidence':evidence,'runtime_verified':False}

def audit_game(game_dir):return audit(game_dir)
def audit_archive(source_archive):return audit(source_archive)

def compare_reports(archive,installed):
    common=set(archive['source_hashes']) & set(installed['source_hashes'])
    return {'overlap_count':len(common),'hash_mismatches':{n:{'archive':archive['source_hashes'][n],'installed':installed['source_hashes'][n]} for n in sorted(common) if archive['source_hashes'][n]!=installed['source_hashes'][n]},'capability_differences':{k:{'archive':v,'installed':installed['capabilities'][k]} for k,v in archive['capabilities'].items() if installed['capabilities'][k]!=v},'only_archive':sorted(set(archive['source_hashes'])-common),'only_installed':sorted(set(installed['source_hashes'])-common)}

def write_evidence(report,output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--source-archive',type=Path);g.add_argument('--game-dir',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--compare-evidence',type=Path)
    args=p.parse_args(argv);source=args.source_archive or args.game_dir
    if args.output.resolve()==source.resolve() or (source.is_dir() and args.output.resolve().is_relative_to(source.resolve())):p.error('Output overlaps read-only source')
    try:
        r=audit(source)
        if args.compare_evidence:r['comparison']=compare_reports(json.loads(args.compare_evidence.read_text('utf-8')),r)
        write_evidence(r,args.output)
    except (ValueError,OSError,zipfile.BadZipFile) as e:p.error(str(e))
    return 0
if __name__=='__main__':raise SystemExit(main())
