"""Static checks for the Vic3 TODO mod (no game needed).

Catches what the engine would only report in game: encoding, unbalanced
braces, references to undefined scripted GUIs / script values / effects /
triggers / custom localization / GUI types / localization keys, and files
that would replace vanilla files.

    python tools/lint_mod.py [--mod mod/Vic3TODO] [--catalog data/vic3_catalog.json]
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdx_parse import brace_balance, parse  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ("english", "japanese")

# Vanilla script values/triggers/effects this mod calls by name.
VANILLA_NAMES = set()


def read(path):
    with open(path, "rb") as fh:
        data = fh.read()
    return data


def walk(mod):
    for base, _dirs, files in os.walk(mod):
        for f in files:
            yield os.path.relpath(os.path.join(base, f), mod).replace(os.sep, "/")


def defined_top_keys(text):
    out = set()
    for key, _op, _v in parse(text):
        if key:
            out.add(key)
    return out


def lint(mod, catalog_path):
    errors = []
    files = sorted(walk(mod))
    texts = {}
    for rel in files:
        data = read(os.path.join(mod, rel))
        if rel == ".metadata/metadata.json":
            if data.startswith(b"\xef\xbb\xbf"):
                errors.append("%s: metadata.json must not have a BOM" % rel)
            try:
                json.loads(data.decode("utf-8"))
            except ValueError as e:
                errors.append("%s: invalid JSON (%s)" % (rel, e))
            continue
        if not data.startswith(b"\xef\xbb\xbf"):
            errors.append("%s: missing UTF-8 BOM" % rel)
        try:
            texts[rel] = data.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            errors.append("%s: not UTF-8 (%s)" % (rel, e))
        if "vic3_todo" not in os.path.basename(rel) and not rel.startswith(".metadata/"):
            errors.append("%s: file name lacks the vic3_todo prefix (could replace a vanilla file)" % rel)
        if "\r" in texts.get(rel, ""):
            errors.append("%s: CR characters" % rel)

    script = {r: t for r, t in texts.items() if r.endswith(".txt") or r.endswith(".gui")}
    for rel, text in script.items():
        ok, msg = brace_balance(text)
        if not ok:
            errors.append("%s: %s" % (rel, msg))
        if re.search(r"\b(TBD|FIXME|XXX)\b", text):
            errors.append("%s: placeholder token" % rel)
        if "{{" in text or "}}" in text:
            errors.append("%s: unexpanded template macro" % rel)
        if rel.endswith(".gui"):
            for n, line in enumerate(text.splitlines(), 1):
                code = line.split("#", 1)[0] if '"' not in line.split("#", 1)[0] else line
                if code.count('"') % 2:
                    errors.append("%s:%d: odd number of quotes" % (rel, n))
                if code.count("[") != code.count("]"):
                    errors.append("%s:%d: unbalanced [ ]" % (rel, n))
                if code.count("(") != code.count(")"):
                    errors.append("%s:%d: unbalanced ( )" % (rel, n))

    def defs(prefix):
        out = set()
        for rel, text in script.items():
            if rel.startswith(prefix):
                try:
                    out |= defined_top_keys(text)
                except ValueError as e:
                    errors.append("%s: parse error (%s)" % (rel, e))
        return out

    sguis = defs("common/scripted_guis/")
    svalues = defs("common/script_values/")
    effects = defs("common/scripted_effects/")
    triggers = defs("common/scripted_triggers/")
    customloc = defs("common/customizable_localization/")
    jes = defs("common/journal_entries/")
    groups = defs("common/journal_entry_groups/")
    companies = defs("common/company_types/")
    buildings = defs("common/buildings/")
    modifiers = defs("common/static_modifiers/")
    on_actions = defs("common/on_actions/")

    gui_text = "\n".join(t for r, t in script.items() if r.endswith(".gui"))
    gui_types = set(re.findall(r"\btype\s+([A-Za-z0-9_]+)\s*=", gui_text))
    gui_names = set(re.findall(r'\bname\s*=\s*"([A-Za-z0-9_]+)"', gui_text))

    # localization
    loc = {lang: {} for lang in LANGS}
    for rel, text in texts.items():
        if not rel.startswith("localization/"):
            continue
        lang = rel.split("/")[1]
        lines = text.splitlines()
        if not lines or lines[0].strip() != "l_%s:" % lang:
            errors.append("%s: first line must be l_%s:" % (rel, lang))
        if not rel.endswith("_l_%s.yml" % lang):
            errors.append("%s: file name must end with _l_%s.yml" % (rel, lang))
        for n, line in enumerate(lines[1:], 2):
            if not line.strip() or line.strip().startswith("#"):
                continue
            m = re.match(r'^ ([A-Za-z0-9_.]+):\d* "(.*)"\s*$', line)
            if not m:
                errors.append("%s:%d: malformed localization line" % (rel, n))
                continue
            key = m.group(1)
            if key in loc[lang]:
                errors.append("%s:%d: duplicate key %s" % (rel, n, key))
            loc[lang][key] = m.group(2)
    if set(loc["english"]) != set(loc["japanese"]):
        diff = set(loc["english"]) ^ set(loc["japanese"])
        errors.append("localization keys differ between languages: %s" % sorted(diff)[:20])

    with open(catalog_path, encoding="utf-8") as fh:
        cat = json.load(fh)
    vanilla_loc = {i["key"] for s in ("buildings", "technologies", "laws", "goods", "interest_groups") for i in cat[s]}
    vanilla_loc |= {l["group"] for l in cat["laws"]}

    def need_loc(key, where):
        if key in vanilla_loc:
            return
        for lang in LANGS:
            if key not in loc[lang]:
                errors.append("%s: localization key %s missing in %s" % (where, key, lang))

    for rel, text in script.items():
        if rel.endswith(".gui"):
            for key in re.findall(r'\b(?:text|tooltip)\s*=\s*"([A-Za-z0-9_]+)"', text):
                need_loc(key, rel)
        else:
            for key in re.findall(r"\b(?:text|desc|localization_key|custom_completion_header)\s*=\s*([A-Za-z0-9_-]+)", text):
                if key not in ("yes", "no"):
                    need_loc(key, rel)
    for key in jes:
        need_loc(key, "journal entry")
        need_loc(key + "_reason", "journal entry")
    for key in groups | companies | buildings | modifiers:
        need_loc(key, "definition")
    for key in modifiers:
        need_loc(key + "_desc", "modifier")
    # $key$ splices in localization
    for lang in LANGS:
        for key, value in loc[lang].items():
            for ref in re.findall(r"\$([A-Za-z0-9_]+)\$", value):
                if ref not in loc[lang]:
                    errors.append("localization %s/%s: $%s$ undefined" % (lang, key, ref))

    # references from GUI and localization
    everything = gui_text + "\n" + "\n".join(v for lang in LANGS for v in loc[lang].values())
    for name in set(re.findall(r"GetScriptedGui\(\s*'([A-Za-z0-9_]+)'", everything)):
        if name not in sguis:
            errors.append("undefined scripted GUI %s" % name)
    for name in set(re.findall(r"ScriptValue\(\s*'([A-Za-z0-9_]+)'", everything)):
        if name not in svalues:
            errors.append("undefined script value %s" % name)
    for name in set(re.findall(r"GetCustom\(\s*'([A-Za-z0-9_]+)'", everything)):
        if name not in customloc:
            errors.append("undefined custom localization %s" % name)
    for name in set(re.findall(r"GetPlayerJournalEntry\(\s*'([A-Za-z0-9_]+)'", everything)):
        if name not in jes:
            errors.append("undefined journal entry %s" % name)
    for name in set(re.findall(r"SelectLocalization\([^']*'([A-Za-z0-9_]+)',\s*'([A-Za-z0-9_]+)'", everything)):
        for key in name:
            need_loc(key, "SelectLocalization")
    for name in set(re.findall(r"^\s*(vic3_todo_[A-Za-z0-9_]+)\s*=\s*\{", gui_text, re.M)):
        if name not in gui_types:
            errors.append("GUI uses undefined type %s" % name)

    # scripted widgets and JE widgets
    for rel, text in texts.items():
        if rel.startswith("gui/scripted_widgets/"):
            for path, name in re.findall(r"^\s*([^#\s=]+)\s*=\s*([A-Za-z0-9_]+)\s*$", text, re.M):
                if path not in texts:
                    errors.append("%s: registers missing file %s" % (rel, path))
                elif not re.search(r'name\s*=\s*"%s"' % name, texts[path]):
                    errors.append("%s: widget %s not found in %s" % (rel, name, path))
    for rel, text in script.items():
        if rel.startswith("common/journal_entries/"):
            for path, name in re.findall(r'gui\s*=\s*"([^"]+)"\s*name\s*=\s*"([^"]+)"', text):
                if path not in texts:
                    errors.append("%s: widget file %s missing" % (rel, path))
                elif name not in gui_names:
                    errors.append("%s: widget %s missing" % (rel, name))
            for g in re.findall(r"\bgroup\s*=\s*([A-Za-z0-9_]+)", text):
                if g not in groups:
                    errors.append("%s: undefined journal group %s" % (rel, g))

    # calls of our own scripted effects / triggers / values from script
    callables = effects | triggers | svalues
    for rel, text in script.items():
        if not rel.startswith("common/"):
            continue
        body = "\n".join(l.split("#", 1)[0] for l in text.splitlines())
        for name in set(re.findall(r"(?<![A-Za-z0-9_:.'])(vic3_todo_[A-Za-z0-9_]+)\s*(?:=\s*(?:yes|no|\{)|[<>]=?|=\s*-?\d)", body)):
            if name in callables or name in sguis or name in jes or name in groups or name in customloc:
                continue
            if name in companies or name in buildings or name in modifiers or name in on_actions:
                continue
            if re.search(r"\b(?:name|has_variable|remove_variable|set_variable|has_tag|add_tag|remove_tag|variable|list)\s*=\s*\{?\s*%s\b" % name, body):
                continue
            errors.append("%s: %s is not a defined effect, trigger or script value" % (rel, name))

    # variables read must be written somewhere
    allscript = "\n".join(t for r, t in script.items() if r.startswith("common/")) + "\n" + gui_text + "\n" + \
        "\n".join(v for lang in LANGS for v in loc[lang].values())
    written = set(re.findall(r"set_variable\s*=\s*\{\s*name\s*=\s*([A-Za-z0-9_$]+)", allscript))
    written |= set(re.findall(r"set_variable\s*=\s*([A-Za-z0-9_$]+)\s*$", allscript, re.M))
    written |= set(re.findall(r"change_variable\s*=\s*\{\s*name\s*=\s*([A-Za-z0-9_$]+)", allscript))
    lists = set(re.findall(r"add_to_variable_list\s*=\s*\{\s*name\s*=\s*([A-Za-z0-9_$]+)", allscript))

    def expand(names):
        out = set()
        for n in names:
            if "$SLOT$" in n:
                out |= {n.replace("$SLOT$", str(i)) for i in range(64)}
            else:
                out.add(n)
        return out
    written, lists = expand(written), expand(lists)
    reads = set(re.findall(r"var:(vic3_todo_[A-Za-z0-9_]+)", allscript))
    reads |= set(re.findall(r"Var\('(vic3_todo_[A-Za-z0-9_]+)'\)", allscript))
    reads |= set(re.findall(r"HasVariable\('(vic3_todo_[A-Za-z0-9_]+)'\)", allscript))
    reads |= set(re.findall(r"GetVariableValue\('(vic3_todo_[A-Za-z0-9_]+)'\)", allscript))
    for name in sorted(reads):
        if name not in written:
            errors.append("variable %s is read but never set" % name)
    list_reads = set(re.findall(r"GetList\('(vic3_todo_[A-Za-z0-9_]+)'\)", allscript))
    list_reads |= set(re.findall(r"(?<![A-Za-z_])(?:has_variable_list|variable)\s*=\s*(vic3_todo_[A-Za-z0-9_$]+)", allscript))
    for name in sorted(expand(list_reads)):
        if name not in lists and not name.endswith("_$SLOT$"):
            errors.append("variable list %s is read but never added to" % name)
    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mod", default=os.path.join(ROOT, "mod", "Vic3TODO"))
    ap.add_argument("--catalog", default=os.path.join(ROOT, "data", "vic3_catalog.json"))
    args = ap.parse_args(argv)
    errors = lint(args.mod, args.catalog)
    for e in errors:
        print(e)
    print("%d problem(s)" % len(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
