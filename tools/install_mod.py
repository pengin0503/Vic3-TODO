"""Install the Vic3 TODO mod into the Victoria 3 user mod folder.

    python tools/install_mod.py                       # Documents/Paradox Interactive/Victoria 3/mod/Vic3TODO
    python tools/install_mod.py --user-data-dir PATH  # another user data folder
    python tools/install_mod.py --game-dir PATH       # rebuild the target lists from the installed game first

With --game-dir the building / technology / law lists are read from the
installed game, so the pickers match the exact game version; the generated
files are written into the installed copy only, never into the repository.
The copy is linted before it replaces anything, and an existing folder is
replaced only if it is this mod (same metadata id).
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_catalog  # noqa: E402
import generate_mod  # noqa: E402
import lint_mod  # noqa: E402

MOD_ID = "vic3_todo"
SOURCE = os.path.join(ROOT, "mod", "Vic3TODO")
FOLDER = "Vic3TODO"


def default_user_data_dir():
    if os.name == "nt":
        try:
            import ctypes.wintypes
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # CSIDL_PERSONAL (Documents)
            docs = buf.value
        except Exception:
            docs = os.path.join(os.path.expanduser("~"), "Documents")
    else:
        docs = os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.join(docs, "Paradox Interactive", "Victoria 3")


def read_id(folder):
    path = os.path.join(folder, ".metadata", "metadata.json")
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh).get("id")
    except (OSError, ValueError):
        return None


def stage_copy(game_dir, parsed_vanilla):
    stage = tempfile.mkdtemp(prefix="vic3_todo_stage_")
    target = os.path.join(stage, FOLDER)
    shutil.copytree(SOURCE, target)
    catalog_path = os.path.join(ROOT, "data", "vic3_catalog.json")
    if game_dir:
        with open(catalog_path, encoding="utf-8") as fh:
            previous = json.load(fh)
        catalog = build_catalog.build_catalog(game_dir, parsed_vanilla, previous)
        catalog_path = os.path.join(stage, "catalog.json")
        build_catalog.write_catalog(catalog, catalog_path)
        generate_mod.main(["--catalog", catalog_path, "--mod", target])
    errors = lint_mod.lint(target, catalog_path)
    if errors:
        shutil.rmtree(stage)
        raise SystemExit("lint failed, nothing installed:\n" + "\n".join(errors))
    return stage, target


def install(user_data_dir, game_dir=None, parsed_vanilla=None):
    mod_root = os.path.join(user_data_dir, "mod")
    destination = os.path.join(mod_root, FOLDER)
    if os.path.lexists(destination):
        if os.path.islink(destination) or read_id(destination) != MOD_ID:
            raise SystemExit("refusing to replace %s: it is not this mod" % destination)
    stage, built = stage_copy(game_dir, parsed_vanilla)
    try:
        os.makedirs(mod_root, exist_ok=True)
        backup = None
        if os.path.exists(destination):
            backup = destination + ".previous"
            if os.path.exists(backup):
                shutil.rmtree(backup)
            os.replace(destination, backup)
        try:
            shutil.copytree(built, destination)
        except BaseException:
            if os.path.exists(destination):
                shutil.rmtree(destination)
            if backup:
                os.replace(backup, destination)
            raise
        if backup:
            shutil.rmtree(backup)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    probe = os.path.join(mod_root, "Vic3TODOProbe")
    if os.path.isdir(probe):
        print("NOTE: the old Phase 0 probe is still installed (%s). It replaces vanilla HUD files;"
              " disable it in the launcher playset." % probe)
    return destination


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--user-data-dir", default=None)
    ap.add_argument("--game-dir", default=None, help="Victoria 3 installation root (optional)")
    ap.add_argument("--parsed-vanilla", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    destination = install(args.user_data_dir or default_user_data_dir(), args.game_dir, args.parsed_vanilla)
    print("installed: %s" % destination)
    print("Enable \"Vic3 TODO - Custom Journals\" in a launcher playset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
