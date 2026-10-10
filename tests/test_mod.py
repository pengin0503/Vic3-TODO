import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_catalog  # noqa: E402
import generate_mod  # noqa: E402
import install_mod  # noqa: E402
import lint_mod  # noqa: E402
from pdx_parse import brace_balance, parse  # noqa: E402

MOD = os.path.join(ROOT, "mod", "Vic3TODO")
CATALOG = os.path.join(ROOT, "data", "vic3_catalog.json")


def read(rel):
    with open(os.path.join(MOD, rel), encoding="utf-8-sig") as fh:
        return fh.read()


class ParserTests(unittest.TestCase):
    def test_parse_blocks_quotes_comments(self):
        block = parse('a = { b = "x # y" c = 1 } # comment\nd = { e f }\ng >= 3')
        self.assertEqual(block.get("a").get("b"), "x # y")
        self.assertEqual(block.get("d").values(), ["e", "f"])
        self.assertEqual(block[2], ("g", ">=", "3"))

    def test_brace_balance(self):
        self.assertTrue(brace_balance("a = { b = { } }")[0])
        self.assertFalse(brace_balance("a = { b = { }")[0])
        self.assertFalse(brace_balance("a = }")[0])
        self.assertTrue(brace_balance('a = "}" # }')[0])


class CatalogTests(unittest.TestCase):
    def test_indexes_are_stable(self):
        previous = {"technologies": [{"key": "b", "idx": 1}, {"key": "d", "idx": 2}]}
        items = [{"key": "a"}, {"key": "b"}, {"key": "c"}]
        out = build_catalog.assign_indexes("technologies", items, previous)
        by_key = {i["key"]: i for i in out}
        self.assertEqual(by_key["b"]["idx"], 1)
        self.assertTrue(by_key["d"]["removed"])
        self.assertEqual(by_key["d"]["idx"], 2)
        self.assertEqual({by_key["a"]["idx"], by_key["c"]["idx"]}, {3, 4})

    def test_committed_catalog_is_complete(self):
        with open(CATALOG, encoding="utf-8") as fh:
            cat = json.load(fh)
        self.assertIn("building_furniture_manufactory", {b["key"] for b in cat["buildings"]})
        self.assertIn("telephone", {t["key"] for t in cat["technologies"]})
        self.assertIn("law_universal_suffrage", {l["key"] for l in cat["laws"]})
        self.assertEqual(max(r["rank_value"] for r in cat["ranks"]), 7)
        for section in build_catalog.INDEXED:
            idx = [i["idx"] for i in cat[section]]
            self.assertEqual(len(idx), len(set(idx)), section)


class GeneratorTests(unittest.TestCase):
    def test_outputs_are_current(self):
        self.assertEqual(generate_mod.main(["--check"]), 0, "run python tools/generate_mod.py")

    def test_kind_ids_unique_and_localized(self):
        ids = [k["id"] for k in generate_mod.KINDS]
        self.assertEqual(len(ids), len(set(ids)))
        for lang in ("english", "japanese"):
            text = read("localization/%s/vic3_todo_generated_l_%s.yml" % (lang, lang))
            for k in generate_mod.KINDS:
                self.assertIn(" vic3_todo_kind_%s:0 " % k["key"], text)

    def test_template_macros(self):
        out = generate_mod.expand_template("{{eq:{{sv:x}}:1}} {{exec_item:s:2}}")
        self.assertEqual(out.split(" ")[0], "EqualTo_CFixedPoint(")
        self.assertIn("ScriptContainer.MakeScope.ScriptValue('x'), '(CFixedPoint)1' )", out)
        self.assertIn("AddScope( 'vic3_todo_item', ScriptContainer.MakeScope )", out)
        self.assertIn("MakeScopeValue( '(CFixedPoint)2' )", out)

    def test_every_slot_has_entry_widget_and_name(self):
        jes = read("common/journal_entries/vic3_todo_generated_journal_entries.txt")
        widgets = read("gui/journal_entry_widgets/vic3_todo_je_widgets_generated.gui")
        loc = read("localization/japanese/vic3_todo_generated_l_japanese.yml")
        for n in range(generate_mod.SLOTS):
            self.assertIn("je_vic3_todo_%d = {" % n, jes)
            self.assertIn('name = "vic3_todo_je_widget_%d"' % n, widgets)
            self.assertIn(" je_vic3_todo_%d:0 " % n, loc)
            self.assertIn(" je_vic3_todo_%d_reason:0 " % n, loc)

    def test_bound_trees_cover_every_target(self):
        with open(CATALOG, encoding="utf-8") as fh:
            cat = json.load(fh)
        values = read("common/script_values/vic3_todo_generated_values.txt")
        effects = read("common/scripted_effects/vic3_todo_generated_effects.txt")
        for t in generate_mod.live(cat["technologies"]):
            self.assertIn("has_technology_researched = %s }" % t["key"], values)
        for l in generate_mod.live(cat["laws"]):
            self.assertIn("has_law = law_type:%s }" % l["key"], values)
        for b in generate_mod.live(cat["buildings"]):
            self.assertIn("value = bt:%s }" % b["key"], effects)

    def test_no_simulation_effects_outside_namespace(self):
        allowed = {
            "set_variable", "remove_variable", "change_variable", "add_to_variable_list", "remove_list_variable",
            "clear_variable_list", "add_to_temporary_list", "create_container", "destroy_container", "add_tag",
            "remove_tag", "add_journal_entry", "save_scope_as", "save_temporary_scope_as",
            # the input carrier, only while the player types
            "add_company", "remove_company", "set_company_state_region", "add_modifier", "remove_modifier",
        }
        for rel in ("common/scripted_effects/vic3_todo_effects.txt", "common/scripted_effects/vic3_todo_generated_effects.txt",
                    "common/scripted_guis/vic3_todo_sguis.txt"):
            text = read(rel)
            for name in set(re.findall(r"^\s*([a-z_]+)\s*=", text, re.M)):
                if name.startswith("vic3_todo") or name in allowed:
                    continue
                self.assertIn(name, {
                    "if", "else_if", "else", "limit", "effect", "is_valid", "is_shown", "ai_is_valid", "scope",
                    "saved_scopes", "trigger_if", "trigger_else_if", "trigger_else", "custom_tooltip", "text",
                    "name", "value", "target", "list", "variable", "tags", "parent", "type", "every_in_list",
                    "ordered_country", "order_by", "position", "check_range_bounds", "capital", "state_region",
                    "root", "always", "exists", "has_variable", "has_variable_list", "has_tag", "has_company",
                    "has_modifier", "has_journal_entry", "OR", "NOT", "this", "add", "subtract", "multiply",
                    "divide", "round", "min", "max", "days", "variable_list_size", "game_date",
                }, "%s uses %s" % (rel, name))


class LintTests(unittest.TestCase):
    def test_repository_mod_is_clean(self):
        self.assertEqual(lint_mod.lint(MOD, CATALOG), [])

    def _broken(self, rel, old, new):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        copy = os.path.join(tmp, "Vic3TODO")
        shutil.copytree(MOD, copy)
        path = os.path.join(copy, rel)
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8-sig") as fh:
            fh.write(text.replace(old, new, 1))
        return lint_mod.lint(copy, CATALOG)

    def test_detects_unbalanced_brace(self):
        errors = self._broken("common/scripted_effects/vic3_todo_effects.txt", "vic3_todo_carrier_close = {", "vic3_todo_carrier_close = { {")
        self.assertTrue(any("unclosed" in e for e in errors), errors)

    def test_detects_undefined_scripted_gui(self):
        errors = self._broken("gui/vic3_todo_window_generated.gui", "GetScriptedGui('vic3_todo_new_sgui')", "GetScriptedGui('vic3_todo_nope_sgui')")
        self.assertTrue(any("vic3_todo_nope_sgui" in e for e in errors), errors)

    def test_detects_missing_localization(self):
        errors = self._broken("localization/japanese/vic3_todo_ui_generated_l_japanese.yml", " vic3_todo_new:0 ", " vic3_todo_renamed:0 ")
        self.assertTrue(any("vic3_todo_new missing in japanese" in e for e in errors), errors)

    def test_detects_unset_variable(self):
        errors = self._broken("common/scripted_effects/vic3_todo_effects.txt",
                              "set_variable = { name = vic3_todo_in_started value = game_date }",
                              "set_variable = { name = vic3_todo_in_startd value = game_date }")
        self.assertTrue(any("vic3_todo_in_started is read but never set" in e for e in errors), errors)


class InstallTests(unittest.TestCase):
    def test_install_and_refuse_unrelated(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        dest = install_mod.install(tmp)
        self.assertTrue(os.path.isfile(os.path.join(dest, ".metadata", "metadata.json")))
        self.assertEqual(install_mod.read_id(dest), "vic3_todo")
        install_mod.install(tmp)  # replacing our own copy is fine
        other = os.path.join(tmp, "mod", "Vic3TODO", ".metadata", "metadata.json")
        with open(other, "w", encoding="utf-8") as fh:
            json.dump({"id": "someone_else"}, fh)
        with self.assertRaises(SystemExit):
            install_mod.install(tmp)


if __name__ == "__main__":
    unittest.main()
