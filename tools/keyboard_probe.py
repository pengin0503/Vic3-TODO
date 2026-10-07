"""Source-preserving HUD/shortcut insertion for the independent Phase 0 panel."""
import hashlib
import json
import re
from pathlib import Path
try:
    from tools.audit_vanilla import read_source,write_evidence
except ModuleNotFoundError:
    from audit_vanilla import read_source,write_evidence

INTEGRATED_GUI={'gui/ingame_hud.gui','gui/shortcuts.shortcuts'}
BEGIN='\n# vic3_todo_keyboard_begin\n'
END='# vic3_todo_keyboard_end\n'
HOTKEY='ctrl+shift+T'


def root_span(text,key):
    tokens=[m for m in re.finditer(r'#[^\n]*|"(?:[^"\\]|\\.)*"|[{}=]|[^\s{}=#\ufeff]+',text) if not m.group().startswith('#')]
    depth=0;spans=[];opening=None
    for i,t in enumerate(tokens):
        if depth==0 and t.group()==key and i+2<len(tokens) and tokens[i+1].group()=='=' and tokens[i+2].group()=='{':
            opening=tokens[i+2].end()
        if t.group()=='{':depth+=1
        elif t.group()=='}':
            depth-=1
            if depth<0:raise ValueError('Unbalanced source GUI braces')
            if depth==0 and opening is not None:
                spans.append((opening,t.start()));opening=None
    if depth or len(spans)!=1:raise ValueError('Expected one '+key+' root in source GUI')
    return spans[0]


def inject(text,key,body):
    start,end=root_span(text,key)
    if key=='widget' and not re.search(r'\bname\s*=\s*"ingame_hud"',text[start:end]):
        raise ValueError('Expected ingame_hud root in source GUI')
    if 'vic3_todo_keyboard_begin' in text:raise ValueError('Source already contains keyboard integration')
    addition=BEGIN+body+'\n'+END
    return text[:end]+addition+text[end:],addition


def execute(key):
    return "[GetScriptedGui('"+key+"_gui').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"


def add_keyboard_probe(stage,source,report):
    _,_,data,_=read_source(source)
    if not INTEGRATED_GUI.issubset(data):raise ValueError('Keyboard probe requires source HUD and shortcuts')
    shortcut_source=data['gui/shortcuts.shortcuts'].decode('utf-8')
    bindings=re.findall(r'\b(\w+)\s*=\s*"([^"]+)"',re.sub(r'#[^\n]*','',shortcut_source))
    if any(name=='vic3_todo_toggle_probe' or key.lower().replace(' ','')==HOTKEY.lower() for name,key in bindings):
        raise ValueError('Keyboard probe shortcut already bound in source')
    caps=report['capabilities']
    actions=caps.get('scripted_gui_definition')=='supported' and caps.get('scripted_gui_execution')=='supported'
    live_common='\n'.join(re.sub(r'#[^\n]*','',raw.decode('utf-8-sig',errors='replace')) for name,raw in data.items() if name.startswith('common/') and name.endswith('.txt'))
    register=actions and bool(re.search(r'\badd_journal_entry\s*=\s*\{',live_common)) and bool(re.search(r'\bhas_journal_entry\s*=',live_common))
    initialize=''
    if actions:
        effects=stage/'common/scripted_effects/vic3_todo_probe_effects.txt'
        with effects.open('a',encoding='utf-8') as f:
            f.write('\nvic3_todo_keyboard_initialize = { vic3_todo_slot_0_create = yes vic3_todo_slot_1_create = yes }\n')
            if register:
                f.write('vic3_todo_keyboard_register = {\n')
                for key in ('vic3_todo_probe','vic3_todo_slot_0_probe','vic3_todo_slot_1_probe'):
                    f.write('    if = { limit = { NOT = { has_journal_entry = '+key+' } } add_journal_entry = { type = '+key+' } }\n')
                f.write('}\n')
        sgui=stage/'common/scripted_guis/vic3_todo_probe_actions.txt'
        with sgui.open('a',encoding='utf-8') as f:
            for key in ('vic3_todo_keyboard_initialize',)+(('vic3_todo_keyboard_register',) if register else ()):
                f.write(key+'_gui = { scope = country effect = { '+key+' = yes } }\n')
        initialize='onclick = "'+execute('vic3_todo_keyboard_initialize')+'"'
    gui=(stage/'gui/journal_entry_widgets/vic3_todo_probe_widget.gui').read_text('utf-8')
    # Pinning remains a Journal-specific operation, accessible through the normal Journal UI.
    gui='\n'.join(line for line in gui.splitlines() if 'JournalEntry.TogglePinInOutliner' not in line and 'vic3_todo_pin_limit' not in line)
    gui=gui.replace('JournalEntry.GetCountry','GetPlayer').replace('vic3_todo_probe_widget','vic3_todo_keyboard_content').replace('vic3_todo_text_input','vic3_todo_keyboard_text_input')
    for lang in ('english','japanese'):
        loc=stage/f'localization/{lang}/vic3_todo_probe_l_{lang}.yml'
        original=loc.read_text('utf-8-sig');extra=[]
        for line in original.splitlines():
            if 'JournalEntry.GetCountry.MakeScope' not in line:continue
            key=re.match(r'\s+(\w+):',line)[1]
            new=key.replace('vic3_todo_','vic3_todo_keyboard_',1)
            extra.append(line.replace(key+':',new+':',1).replace('JournalEntry.GetCountry','GetPlayer'))
            gui=gui.replace('text = "'+key+'"','text = "'+new+'"')
        labels={
            'vic3_todo_keyboard_title':('Vic3 TODO direct probe','Vic3 TODO 直接検証画面'),
            'vic3_todo_keyboard_toggle':('TODO probe (Ctrl+Shift+T)','TODO検証 (Ctrl+Shift+T)'),
            'vic3_todo_keyboard_close':('Close','閉じる'),
            'vic3_todo_keyboard_journal':('Open Journal list','Journal一覧を開く'),
            'vic3_todo_keyboard_register':('Register probe Journal entries','検証用Journalを登録'),
            'vic3_todo_keyboard_initialize':('Initialize probe slots','検証用slotを初期化'),
        }
        extra.extend(' '+key+': "'+value[lang=='japanese']+'"' for key,value in labels.items())
        with loc.open('a',encoding='utf-8') as f:f.write('\n'+'\n'.join(extra)+'\n')
    register_button=''
    if register:
        register_button='button = { using = default_button_action size = { 600 32 } text = "vic3_todo_keyboard_register" onclick = "'+execute('vic3_todo_keyboard_register')+'" }'
    body='''    button = {
        name = "vic3_todo_keyboard_toggle"
        parentanchor = top|hcenter
        position = { 160 110 }
        size = { 250 32 }
        using = default_button_action
        visible = "[And(IsInGame, GetPlayer.IsValid)]"
        text = "vic3_todo_keyboard_toggle"
        shortcut = "vic3_todo_toggle_probe"
        INITIALIZE
        onclick = "[GetVariableSystem.Toggle('vic3_todo_keyboard_open')]"
    }
    widget = {
        name = "vic3_todo_keyboard_panel"
        parentanchor = center
        size = { 680 660 }
        visible = "[And(IsInGame, GetVariableSystem.Exists('vic3_todo_keyboard_open'))]"
        using = clickthrough_blocker
        background = { using = default_background }
        vbox = {
            position = { 20 20 }
            spacing = 10
            text_single = { text = "vic3_todo_keyboard_title" }
            button = { using = default_button_action size = { 600 32 } text = "vic3_todo_keyboard_close" onclick = "[GetVariableSystem.Clear('vic3_todo_keyboard_open')]" }
            button = { using = default_button_action size = { 600 32 } text = "vic3_todo_keyboard_journal" onclick = "[InformationPanelBar.OpenPanelCycleTabs('journal', 'default|inactive_journal_entries|nation_formation')]" }
            REGISTER_BUTTON
            scrollarea = {
                size = { 640 440 }
                scrollbarpolicy_horizontal = always_off
                scrollbar_vertical = { using = vertical_scrollbar }
                scrollwidget = {
                    CONTENT
                }
            }
        }
    }'''.replace('INITIALIZE',initialize).replace('REGISTER_BUTTON',register_button).replace('CONTENT',gui)
    inserts={'gui/ingame_hud.gui':body,'gui/shortcuts.shortcuts':'    vic3_todo_toggle_probe = "'+HOTKEY+'"'}
    meta={'shortcut':HOTKEY,'initialize_enabled':actions,'register_enabled':register,'runtime_verified':False,'source_hashes':{},'insertion_hashes':{}}
    for name,insert in inserts.items():
        text,addition=inject(data[name].decode('utf-8'),'widget' if name.endswith('.gui') else 'shortcutbindings',insert)
        (stage/name).write_bytes(text.encode('utf-8'))
        meta['source_hashes'][name]=hashlib.sha256(data[name]).hexdigest()
        meta['insertion_hashes'][name]=hashlib.sha256(addition.encode('utf-8')).hexdigest()
    write_evidence(meta,stage/'vic3_todo_keyboard_integration.json')


def validate_keyboard_probe(output,source=None):
    output=Path(output);metadata=output/'vic3_todo_keyboard_integration.json'
    if not metadata.is_file():raise ValueError('Missing source-preserving keyboard metadata')
    meta=json.loads(metadata.read_text('utf-8'))
    data=read_source(source)[2] if source is not None else None
    for name in sorted(INTEGRATED_GUI):
        raw=(output/name).read_bytes()
        pattern=re.compile(re.escape(BEGIN.encode())+rb'.*?'+re.escape(END.encode()),re.S)
        matches=pattern.findall(raw)
        if len(matches)!=1:raise ValueError('Invalid source-preserving keyboard insertion: '+name)
        original=pattern.sub(b'',raw)
        expected=data[name] if data is not None else None
        if hashlib.sha256(original).hexdigest()!=meta['source_hashes'].get(name) or (expected is not None and original!=expected):
            raise ValueError('Keyboard GUI is not source-preserving: '+name)
        if hashlib.sha256(matches[0]).hexdigest()!=meta['insertion_hashes'].get(name):
            raise ValueError('Keyboard insertion changed after build: '+name)
        root_span(raw.decode('utf-8'),'widget' if name.endswith('.gui') else 'shortcutbindings')
