"""Build the target catalog the TODO mod's pickers are generated from.

The catalog lists only definition keys (building types, technologies, laws,
country ranks) and the grouping the pickers need. Keys are read from game
script; nothing from vanilla localization is copied, because every key is
also its own vanilla localization key.

Sources, in order of preference for each section:
  --source         an installed game directory (…/Victoria 3) or the
                   Vic3_todo_source.zip archive. Partial archives are fine:
                   a section that is missing or incomplete there falls back.
  --parsed-vanilla a directory of parsed 1.14.5 vanilla JSON
                   (common/technologies.json, common/country_ranks.json, …)
                   used for sections the source lacks.

The catalog records where each section came from.
"""

import argparse
import hashlib
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdx_parse import parse  # noqa: E402

# Building types a TODO cannot meaningfully target: engine-owned subsistence
# and company headquarters. Monuments and other non-buildable types are left
# out by the buildable = no rule.
EXCLUDED_BUILDINGS = {"building_company_headquarter", "building_company_regional_headquarter"}

SECTIONS = ("buildings", "technologies", "laws", "ranks", "goods", "interest_groups")


class Source:
    """Read files under game/ from either a directory or a zip archive."""

    def __init__(self, path):
        self.path = path
        self.zip = None
        self.root = None
        if os.path.isfile(path):
            self.zip = zipfile.ZipFile(path)
            names = [n for n in self.zip.namelist() if not n.startswith("__MACOSX/")]
            roots = sorted({n[: n.index("game/") + 5] for n in names if "game/" in n}, key=len)
            if not roots:
                raise SystemExit("no game/ directory inside %s" % path)
            self.root = roots[0]
            self.names = names
        else:
            game = os.path.join(path, "game")
            self.root = game if os.path.isdir(game) else path

    def list(self, rel_dir):
        rel_dir = rel_dir.rstrip("/") + "/"
        if self.zip:
            prefix = self.root + rel_dir
            return sorted(
                n[len(self.root):]
                for n in self.names
                if n.startswith(prefix) and n.endswith(".txt") and "/" not in n[len(prefix):]
            )
        full = os.path.join(self.root, rel_dir)
        if not os.path.isdir(full):
            return []
        return sorted(rel_dir + f for f in os.listdir(full) if f.endswith(".txt"))

    def read(self, rel):
        if self.zip:
            data = self.zip.read(self.root + rel)
        else:
            with open(os.path.join(self.root, rel), "rb") as fh:
                data = fh.read()
        return data.decode("utf-8-sig", errors="replace")

    def describe(self):
        if self.zip:
            with open(self.path, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            return {"kind": "archive", "name": os.path.basename(self.path), "sha256": digest}
        return {"kind": "directory", "name": os.path.basename(os.path.abspath(self.path))}


def _definitions(source, rel_dir):
    out = []
    for rel in source.list(rel_dir):
        for key, _op, value in parse(source.read(rel)):
            if key and not key.startswith("@") and hasattr(value, "get"):
                out.append((key, value, rel))
    return out


def buildings_from(source):
    items = []
    for key, value, _rel in _definitions(source, "common/buildings"):
        if value.get("buildable", "yes") == "no" or key in EXCLUDED_BUILDINGS:
            continue
        items.append({"key": key, "group": value.get("building_group", "")})
    return items


def technologies_from(source):
    items = []
    for key, value, _rel in _definitions(source, "common/technology/technologies"):
        items.append({"key": key, "era": value.get("era", ""), "category": value.get("category", "")})
    return items


def laws_from(source):
    items = []
    for key, value, _rel in _definitions(source, "common/laws"):
        if not key.startswith("law_"):
            continue
        items.append({"key": key, "group": value.get("group", "")})
    return items


def ranks_from(source):
    items = []
    for key, value, _rel in _definitions(source, "common/country_ranks"):
        rv = value.get("rank_value")
        if rv is not None:
            items.append({"key": key, "rank_value": int(rv)})
    return items


def goods_from(source):
    return [{"key": key} for key, _value, _rel in _definitions(source, "common/goods")]


def interest_groups_from(source):
    return [{"key": key} for key, _value, _rel in _definitions(source, "common/interest_groups")]


def _parsed_value(entry, field, default=""):
    # parsed JSON entries look like ["=", {"field": ["=", "value"], ...}]
    body = entry[1] if isinstance(entry, list) and len(entry) == 2 else entry
    raw = body.get(field) if isinstance(body, dict) else None
    if isinstance(raw, list) and len(raw) == 2:
        return raw[1]
    return default


def from_parsed(parsed_dir, section):
    files = {
        "buildings": "buildings.json",
        "technologies": "technologies.json",
        "laws": "laws.json",
        "ranks": "country_ranks.json",
        "goods": "goods.json",
        "interest_groups": "interest_groups.json",
    }
    path = os.path.join(parsed_dir, "common", files[section])
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    items = []
    for key, entry in data.items():
        if section == "buildings":
            if _parsed_value(entry, "buildable", "yes") == "no" or key in EXCLUDED_BUILDINGS:
                continue
            items.append({"key": key, "group": _parsed_value(entry, "building_group")})
        elif section == "technologies":
            items.append({"key": key, "era": _parsed_value(entry, "era"), "category": _parsed_value(entry, "category")})
        elif section == "laws":
            if key.startswith("law_"):
                items.append({"key": key, "group": _parsed_value(entry, "group")})
        elif section in ("goods", "interest_groups"):
            items.append({"key": key})
        else:
            rv = _parsed_value(entry, "rank_value", None)
            if rv is not None:
                items.append({"key": key, "rank_value": int(rv)})
    return items


# A source section smaller than this share of the parsed reference is treated
# as a partial archive (the supplied ZIP holds one technology file of three).
COMPLETENESS_RATIO = 0.9


INDEXED = ("buildings", "technologies", "laws", "goods", "interest_groups")


def assign_indexes(section, items, previous):
    """Give every item a stable 1-based "idx" (saved games store it).

    Keys keep the index they had in the previous catalog; new keys get the
    next free indexes in key order; keys that disappeared stay as
    {"removed": true} so their index is never reused."""
    old = {i["key"]: i for i in (previous or {}).get(section, [])}
    out = []
    next_idx = max([i["idx"] for i in old.values()] + [0]) + 1
    current = {i["key"] for i in items}
    for item in items:
        prev = old.get(item["key"])
        if prev:
            item = dict(item, idx=prev["idx"])
        else:
            item = dict(item, idx=next_idx)
            next_idx += 1
        out.append(item)
    for key, prev in old.items():
        if key not in current:
            out.append(dict(prev, removed=True))
    return sorted(out, key=lambda i: i["idx"])


def build_catalog(source_path=None, parsed_dir=None, previous=None):
    readers = {
        "buildings": buildings_from,
        "technologies": technologies_from,
        "laws": laws_from,
        "ranks": ranks_from,
        "goods": goods_from,
        "interest_groups": interest_groups_from,
    }
    source = Source(source_path) if source_path else None
    catalog = {"format": 1, "provenance": {}}
    for section in SECTIONS:
        primary = readers[section](source) if source else []
        reference = from_parsed(parsed_dir, section) if parsed_dir else None
        if primary and (reference is None or len(primary) >= COMPLETENESS_RATIO * len(reference)):
            items, origin = primary, dict(source.describe(), section_count=len(primary))
        elif reference:
            items, origin = reference, {
                "kind": "parsed-vanilla",
                "name": "1.14.5 parsed vanilla JSON",
                "section_count": len(reference),
                "source_section_count": len(primary),
            }
        else:
            raise SystemExit("no data for section %s" % section)
        key = "rank_value" if section == "ranks" else "key"
        items = sorted({i["key"]: i for i in items}.values(), key=lambda i: (i[key], i["key"]))
        if section in INDEXED:
            items = assign_indexes(section, items, previous)
        catalog[section] = items
        catalog["provenance"][section] = origin
    return catalog


def write_catalog(catalog, output):
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", help="installed game directory or source zip")
    ap.add_argument("--parsed-vanilla", help="directory with parsed vanilla JSON")
    ap.add_argument("--output", default="data/vic3_catalog.json")
    args = ap.parse_args(argv)
    if not args.source and not args.parsed_vanilla:
        ap.error("give --source and/or --parsed-vanilla")
    previous = None
    if os.path.exists(args.output):
        with open(args.output, encoding="utf-8") as fh:
            previous = json.load(fh)
    catalog = build_catalog(args.source, args.parsed_vanilla, previous)
    write_catalog(catalog, args.output)
    for section in SECTIONS:
        print("%-13s %4d  (%s)" % (section, len(catalog[section]), catalog["provenance"][section]["kind"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
