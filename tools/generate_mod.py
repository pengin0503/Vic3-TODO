"""Generate the repetitive parts of the Vic3 TODO mod.

Inputs: data/vic3_catalog.json (tools/build_catalog.py) and the tracker kind
table below. Outputs: files whose names contain "generated" under
mod/Vic3TODO. Hand-written files are never touched.

    python tools/generate_mod.py            # write
    python tools/generate_mod.py --check    # exit 1 if any output is stale
"""

import argparse
import json
import os
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "mod", "Vic3TODO")
CATALOG = os.path.join(ROOT, "data", "vic3_catalog.json")

SLOTS = 32
OWNER = "var:vic3_todo_owner"

# ---------------------------------------------------------------------------
# Tracker kinds. ids are stored in saves (vic3_todo_kind): never renumber.
#
# fmt: 1 integer, 2 large amount (K/M), 3 one decimal, 4 percent (value is
#      scaled by 100 for display), 5 yes/no, 6 country rank, 7 days
# modes: allowed modes (1 increase, 2 reach at least, 3 decrease, 4 reach at
#        most); discrete kinds use mode 2 only.
# ---------------------------------------------------------------------------
CATEGORIES = OrderedDict([
    ("economy", ("経済", "Economy")),
    ("society", ("社会", "Society")),
    ("politics", ("政治・技術", "Politics & Technology")),
    ("diplomacy", ("外交・国力", "Diplomacy & Power")),
    ("military", ("軍事", "Military")),
    ("state", ("州", "States")),
    ("time", ("時間", "Time")),
])

ALL = (1, 2, 3, 4)


def K(id, key, cat, fmt, steps, ja, en, raw=None, target=None, discrete=False,
      default_mode=1, modes=ALL, fraction=False, nonneg=False, raw_tree=None):
    return dict(id=id, key=key, cat=cat, fmt=fmt, steps=steps, ja=ja, en=en, raw=raw,
                target=target, discrete=discrete, default_mode=default_mode,
                modes=(2,) if discrete else modes, fraction=fraction, nonneg=nonneg,
                raw_tree=raw_tree)


def owner_value(link):
    return ["add = %s.%s" % (OWNER, link)]


def state_value(link):
    return ["if = {", "\tlimit = { exists = var:vic3_todo_target }", "\tadd = var:vic3_todo_target.%s" % link, "}"]


KINDS = [
    K(1, "building", "economy", 1, (1, 5, 10), "建物のレベル", "Building levels", target="building",
      raw=['if = {', '\tlimit = { exists = var:vic3_todo_target }',
           '\tadd = "%s.country_has_building_type_levels(scope:vic3_todo_calc.var:vic3_todo_target)"' % OWNER,
           '}'], nonneg=True),
    K(2, "gdp", "economy", 2, (1000000, 10000000, 100000000), "GDP", "GDP", raw=owner_value("gdp"), nonneg=True),
    K(3, "population", "society", 2, (100000, 1000000, 10000000), "人口", "Population",
      raw=owner_value("total_population"), nonneg=True),
    K(4, "literacy", "society", 4, (0.01, 0.05, 0.1), "識字率 (%)", "Literacy (%)",
      raw=owner_value("literacy_rate"), default_mode=2, fraction=True),
    K(5, "army", "military", 1, (1, 10, 50), "陸軍の大隊数", "Army battalions", raw=owner_value("army_size"), nonneg=True),
    K(6, "navy", "military", 1, (1, 5, 20), "海軍の艦隊数", "Navy flotillas", raw=owner_value("navy_size"), nonneg=True),
    K(7, "technology", "politics", 5, (1, 1, 1), "技術の研究", "Technology researched", target="technology",
      discrete=True, raw_tree="technology"),
    K(8, "law", "politics", 5, (1, 1, 1), "法律の制定", "Law enacted", target="law", discrete=True, raw_tree="law"),
    K(9, "relations", "diplomacy", 1, (5, 10, 25), "他国との関係", "Relations with a country", target="country",
      raw=['if = {', '\tlimit = {', '\t\texists = var:vic3_todo_target',
           '\t\tNOT = { var:vic3_todo_target = %s }' % OWNER, '\t}',
           '\tadd = "%s.relations(scope:vic3_todo_calc.var:vic3_todo_target)"' % OWNER, '}'],
      default_mode=2),
    K(10, "rank", "diplomacy", 6, (1, 1, 1), "国家ランク", "Country rank", target="rank", discrete=True,
      raw=owner_value("country_rank")),
    K(11, "prestige", "diplomacy", 1, (10, 50, 250), "威信", "Prestige", raw=owner_value("prestige")),
    K(12, "sol", "society", 3, (0.5, 1, 5), "平均生活水準", "Average standard of living",
      raw=owner_value("average_sol"), default_mode=2, nonneg=True),
    K(13, "infamy", "diplomacy", 3, (1, 5, 25), "悪名", "Infamy", raw=owner_value("infamy"), default_mode=4, nonneg=True),
    K(14, "techs", "politics", 1, (1, 5, 10), "研究済み技術の数", "Technologies researched",
      raw=owner_value("techs_researched"), nonneg=True),
    K(15, "states", "diplomacy", 1, (1, 5, 10), "保有する州の数", "States owned", raw=owner_value("num_states"), nonneg=True),
    K(16, "income", "economy", 2, (1000, 10000, 100000), "週収入", "Weekly income", raw=owner_value("income"), nonneg=True),
    K(17, "legitimacy", "politics", 1, (1, 5, 10), "正統性", "Legitimacy", raw=owner_value("legitimacy"),
      default_mode=2, nonneg=True),
    K(18, "gold", "economy", 2, (10000, 100000, 1000000), "金準備", "Gold reserves", raw=owner_value("gold_reserves"),
      nonneg=True),
    K(19, "debt", "economy", 2, (10000, 100000, 1000000), "負債（元本）", "Debt (principal)",
      raw=owner_value("principal"), default_mode=4, nonneg=True),
    K(20, "scaled_debt", "economy", 4, (0.05, 0.1, 0.25), "負債の上限比 (%)", "Debt to ceiling (%)",
      raw=owner_value("scaled_debt"), default_mode=4, nonneg=True),
    K(21, "investment_pool", "economy", 2, (10000, 100000, 1000000), "投資プール", "Investment pool",
      raw=owner_value("investment_pool"), nonneg=True),
    K(22, "trade_value", "economy", 2, (10000, 100000, 1000000), "総貿易額", "Total trade value",
      raw=owner_value("total_trade_value"), nonneg=True),
    K(23, "goods_production", "economy", 2, (100, 1000, 10000), "市場の商品生産量", "Goods produced in our market",
      target="goods", raw_tree="goods_production", nonneg=True),
    K(24, "goods_price", "economy", 4, (0.05, 0.1, 0.25), "商品価格の基準比 (%)", "Goods price vs base (%)",
      target="goods", raw_tree="goods_price", default_mode=4),
    K(25, "urbanization", "society", 4, (0.01, 0.05, 0.1), "都市化率 (%)", "Urbanization (%)",
      raw=owner_value("country_urbanization_rate"), default_mode=2, fraction=True),
    K(26, "radicals", "society", 4, (0.01, 0.05, 0.1), "急進派の割合 (%)", "Radicals (%)",
      raw=owner_value("radical_fraction"), default_mode=4, fraction=True),
    K(27, "loyalists", "society", 4, (0.01, 0.05, 0.1), "支持派の割合 (%)", "Loyalists (%)",
      raw=owner_value("loyalist_fraction"), default_mode=2, fraction=True),
    K(28, "ig_approval", "politics", 3, (1, 2, 5), "利益集団の支持", "Interest group approval",
      target="interest_group", raw_tree="ig_approval", default_mode=2),
    K(29, "ig_clout", "politics", 4, (0.01, 0.05, 0.1), "利益集団の影響力 (%)", "Interest group clout (%)",
      target="interest_group", raw_tree="ig_clout", default_mode=2, fraction=True),
    K(30, "authority", "politics", 1, (10, 50, 100), "権威", "Authority", raw=owner_value("authority")),
    K(31, "bureaucracy", "politics", 1, (10, 50, 100), "官僚", "Bureaucracy", raw=owner_value("bureaucracy")),
    K(32, "peace", "military", 5, (1, 1, 1), "平和である", "At peace", discrete=True,
      raw=['if = {', '\tlimit = { %s = { is_at_war = no } }' % OWNER, '\tadd = 1', '}']),
    K(33, "days", "time", 7, (30, 365, 3650), "経過日数", "Days passed", raw=["add = game_date"], modes=(1,)),
    K(34, "state_population", "state", 2, (10000, 100000, 1000000), "州の人口", "State population", target="state",
      raw=state_value("state_population"), nonneg=True),
    K(35, "state_sol", "state", 3, (0.5, 1, 5), "州の平均生活水準", "State standard of living", target="state",
      raw=state_value("average_sol"), default_mode=2, nonneg=True),
    K(36, "state_literacy", "state", 4, (0.01, 0.05, 0.1), "州の識字率 (%)", "State literacy (%)", target="state",
      raw=state_value("literacy_rate"), default_mode=2, fraction=True),
    K(37, "state_radicals", "state", 4, (0.01, 0.05, 0.1), "州の急進派の割合 (%)", "State radicals (%)", target="state",
      raw=state_value("radical_fraction"), default_mode=4, fraction=True),
    K(38, "state_turmoil", "state", 4, (0.01, 0.05, 0.1), "州の騒乱 (%)", "State turmoil (%)", target="state",
      raw=state_value("turmoil"), default_mode=4, fraction=True),
    K(39, "state_infrastructure", "state", 1, (5, 10, 50), "州のインフラ", "State infrastructure", target="state",
      raw=state_value("infrastructure"), default_mode=2, nonneg=True),
    K(40, "war_with", "military", 5, (1, 1, 1), "特定の国と戦争中", "At war with a country", target="country",
      discrete=True,
      raw=['if = {', '\tlimit = {', '\t\texists = var:vic3_todo_target',
           '\t\tNOT = { var:vic3_todo_target = %s }' % OWNER,
           '\t\t%s = { has_war_with = scope:vic3_todo_calc.var:vic3_todo_target }' % OWNER, '\t}',
           '\tadd = 1', '}']),
]

TARGET_TYPES = OrderedDict([
    ("building", 1), ("technology", 2), ("law", 3), ("country", 4), ("rank", 5),
    ("goods", 6), ("interest_group", 7), ("state", 8),
])

RANK_NAMES = {
    "great_power": ("列強", "Great Power"),
    "major_power": ("大国", "Major Power"),
    "minor_power": ("中堅国", "Minor Power"),
    "insignificant_power": ("小国", "Insignificant Power"),
    "unrecognized_major_power": ("未承認の大国", "Unrecognized Major Power"),
    "unrecognized_regional_power": ("未承認の地域大国", "Unrecognized Regional Power"),
    "unrecognized_power": ("未承認国", "Unrecognized Power"),
    "decentralized_power": ("分権国家", "Decentralized Power"),
}

BUILDING_SECTIONS = OrderedDict([
    ("industry", ("工業", "Industry", {"bg_light_industry", "bg_heavy_industry", "bg_military_industry"})),
    ("resources", ("農業・資源", "Agriculture & Resources", {
        "bg_staple_crops", "bg_plantations", "bg_ranching", "bg_agriculture", "bg_fishing", "bg_whaling",
        "bg_logging", "bg_rubber", "bg_mining", "bg_oil_extraction"})),
    ("infrastructure", ("インフラ・政府", "Infrastructure & Government", None)),
    ("monuments", ("記念碑・運河", "Monuments & Canals", {"bg_monuments", "bg_canals"})),
])

TECH_CATEGORIES = OrderedDict([
    ("production", ("生産", "Production")),
    ("military", ("軍事", "Military")),
    ("society", ("社会", "Society")),
])

ERAS = ["era_1", "era_2", "era_3", "era_4", "era_5"]

BOM = "﻿"


def fmt_num(v):
    if isinstance(v, float) and not v.is_integer():
        return repr(v)
    return str(int(v))


def indent(lines, n):
    return ["\t" * n + l if l else l for l in lines]


def header(what):
    return [
        "# GENERATED by tools/generate_mod.py from data/vic3_catalog.json - do not edit.",
        "# " + what,
        "",
    ]


# ---------------------------------------------------------------------------
# helpers producing script
# ---------------------------------------------------------------------------

def live(items):
    """Catalog items still present in the game (removed ones keep their idx)."""
    return [i for i in items if not i.get("removed")]


def idx_tree(items, leaf, var="var:vic3_todo_target_idx"):
    """Balanced if/else tree over the items' stable "idx"; leaf(idx, item) -> lines.

    Script values and effects both accept nested if/else."""
    entries = sorted(((i["idx"], i) for i in live(items)), key=lambda e: e[0])

    def build(part):
        if len(part) <= 4:
            out = []
            for idx, item in part:
                out += ["if = {", "\tlimit = { %s = %d }" % (var, idx)] + indent(leaf(idx, item), 1) + ["}"]
            return out
        half = len(part) // 2
        cut = part[half - 1][0]
        return (["if = {", "\tlimit = { %s <= %d }" % (var, cut)] + indent(build(part[:half]), 1) + ["}",
                 "else = {"] + indent(build(part[half:]), 1) + ["}"])
    return build(entries)


def kind_chain(pairs, default=None):
    """if/else_if chain on var:vic3_todo_kind. pairs: [(kind_id, lines)]."""
    out = []
    for n, (kid, body) in enumerate(pairs):
        out += ["%s = {" % ("if" if n == 0 else "else_if"), "\tlimit = { var:vic3_todo_kind = %d }" % kid]
        out += indent(body, 1) + ["}"]
    if default is not None:
        out += ["else = {"] + indent(default, 1) + ["}"]
    return out


def gen_values(cat):
    L = header("Per-kind script values in tracker scope.")
    L += ["vic3_todo_max_items = %d" % SLOTS, ""]

    # raw reading
    trees = {
        "technology": lambda i, t: ["if = {", "\tlimit = { %s = { has_technology_researched = %s } }" % (OWNER, t["key"]),
                                    "\tadd = 1", "}"],
        "law": lambda i, t: ["if = {", "\tlimit = { %s = { has_law = law_type:%s } }" % (OWNER, t["key"]),
                             "\tadd = 1", "}"],
        "goods_production": lambda i, g: ["if = {", "\tlimit = { exists = %s.market }" % OWNER,
                                          "\tadd = %s.market.mg:%s.market_goods_production" % (OWNER, g["key"]), "}"],
        "goods_price": lambda i, g: ["if = {", "\tlimit = { exists = %s.market }" % OWNER,
                                     "\tadd = %s.market.mg:%s.market_goods_pricier" % (OWNER, g["key"]), "}"],
        "ig_approval": lambda i, g: ["if = {", "\tlimit = { exists = %s.ig:%s }" % (OWNER, g["key"]),
                                     "\tadd = %s.ig:%s.ig_approval" % (OWNER, g["key"]), "}"],
        "ig_clout": lambda i, g: ["if = {", "\tlimit = { exists = %s.ig:%s }" % (OWNER, g["key"]),
                                  "\tadd = %s.ig:%s.ig_clout" % (OWNER, g["key"]), "}"],
    }
    tree_items = {"technology": cat["technologies"], "law": cat["laws"], "goods_production": cat["goods"],
                  "goods_price": cat["goods"], "ig_approval": cat["interest_groups"], "ig_clout": cat["interest_groups"]}
    for name, leaf in trees.items():
        L += ["vic3_todo_tr_raw_%s = {" % name, "\tvalue = 0", "\tif = {",
              "\t\tlimit = { has_variable = vic3_todo_target_idx }"]
        L += indent(idx_tree(tree_items[name], leaf), 2)
        L += ["\t}", "}", ""]

    pairs = []
    for k in KINDS:
        body = ["add = vic3_todo_tr_raw_%s" % k["raw_tree"]] if k["raw_tree"] else list(k["raw"])
        pairs.append((k["id"], body))
    L += ["# The kind's current reading, in the game's own units.", "vic3_todo_tr_raw = {", "\tvalue = 0",
          "\tsave_temporary_scope_as = vic3_todo_calc"]
    L += indent(kind_chain(pairs), 1) + ["}", ""]

    def simple(name, getter, doc):
        out = ["# " + doc, "%s = {" % name]
        groups = OrderedDict()
        for k in KINDS:
            groups.setdefault(fmt_num(getter(k)), []).append(k["id"])
        values = list(groups.items())
        default_value = max(values, key=lambda kv: len(kv[1]))[0]
        out.append("\tvalue = %s" % default_value)
        for v, ids in values:
            if v == default_value:
                continue
            ors = " ".join("var:vic3_todo_kind = %d" % i for i in ids)
            out += ["\tif = {", "\t\tlimit = { OR = { %s } }" % ors, "\t\tvalue = %s" % v, "\t}"]
        return out + ["}", ""]

    L += simple("vic3_todo_tr_step_s", lambda k: k["steps"][0], "Small goal step.")
    L += simple("vic3_todo_tr_step_m", lambda k: k["steps"][1], "Medium goal step; the default delta goal.")
    L += simple("vic3_todo_tr_step_l", lambda k: k["steps"][2], "Large goal step.")
    L += simple("vic3_todo_tr_scale", lambda k: 100 if k["fmt"] == 4 else 1, "Display scale (100 for shares).")
    L += simple("vic3_todo_tr_fmt", lambda k: k["fmt"], "Display format, see the kind table in tools/generate_mod.py.")
    L += simple("vic3_todo_tr_default_mode", lambda k: 2 if k["discrete"] else k["default_mode"], "Mode a new tracker starts in.")
    L += simple("vic3_todo_tr_target_type", lambda k: TARGET_TYPES.get(k["target"], 0),
                "Which picker the tracker needs: %s." % ", ".join("%d %s" % (v, n) for n, v in TARGET_TYPES.items()))
    L += simple("vic3_todo_tr_category", lambda k: list(CATEGORIES).index(k["cat"]) + 1, "Kind category.")

    # todo scope: is the journal's own Journal Entry active? Gates the GUI
    # that reads it through GetPlayerJournalEntry (untested for an inactive
    # entry), so nothing reads an entry the player does not hold.
    def je_leaf(n, _item):
        return ["if = {", "\tlimit = { %s = { has_journal_entry = je_vic3_todo_%d } }" % (OWNER, n), "\tvalue = 1", "}"]
    L += ["# todo scope: 1 while the journal's Journal Entry is active.", "vic3_todo_je_active = {", "\tvalue = 0",
          "\tif = {", "\t\tlimit = { has_variable = vic3_todo_slot }"]
    L += indent(idx_tree([{"idx": n} for n in range(SLOTS)], je_leaf, var="var:vic3_todo_slot"), 2) + ["\t}", "}", ""]
    return L


def gen_triggers():
    L = header("Per-kind scripted triggers in tracker scope.")

    def ors(name, pred, doc):
        ids = [k["id"] for k in KINDS if pred(k)]
        return ["# " + doc, "%s = {" % name, "\tOR = {"] + ["\t\tvar:vic3_todo_kind = %d" % i for i in ids] + ["\t}", "}", ""]

    L += ors("vic3_todo_tr_discrete", lambda k: k["discrete"], "Yes/no and rank kinds: no partial percentage, no goal steps.")
    L += ors("vic3_todo_tr_needs_target", lambda k: k["target"] is not None, "Kinds that need a target picked.")
    L += ors("vic3_todo_tr_fraction_kind", lambda k: k["fraction"], "Shares kept within 0..1.")
    L += ors("vic3_todo_tr_nonnegative_kind", lambda k: k["nonneg"], "Readings that are never negative.")
    L += ors("vic3_todo_tr_modes_all", lambda k: tuple(k["modes"]) == ALL, "Kinds that offer all four modes.")
    L += ors("vic3_todo_tr_scope_target", lambda k: k["target"] in ("building", "country", "state"),
             "Kinds whose target is a scope held in vic3_todo_target.")
    L += ors("vic3_todo_tr_country_target", lambda k: k["target"] == "country", "Kinds whose target is another country.")
    # Journal Entry slot triggers, parameterised by $SLOT$.
    L += [
        "# country scope: the journal bound to slot $SLOT$ is completed / failed / overdue / met.",
        "vic3_todo_slot_done = {",
        "\thas_variable_list = vic3_todo_slot_$SLOT$",
        "\tany_in_list = {",
        "\t\tvariable = vic3_todo_slot_$SLOT$",
        "\t\thas_tag = vic3_todo_done",
        "\t}",
        "}",
        "vic3_todo_slot_failed = {",
        "\thas_variable_list = vic3_todo_slot_$SLOT$",
        "\tany_in_list = {",
        "\t\tvariable = vic3_todo_slot_$SLOT$",
        "\t\thas_tag = vic3_todo_failed",
        "\t}",
        "}",
        "vic3_todo_slot_overdue = {",
        "\thas_variable_list = vic3_todo_slot_$SLOT$",
        "\tany_in_list = {",
        "\t\tvariable = vic3_todo_slot_$SLOT$",
        "\t\tvic3_todo_overdue > 0",
        "\t}",
        "}",
        "vic3_todo_slot_met = {",
        "\thas_variable_list = vic3_todo_slot_$SLOT$",
        "\tany_in_list = {",
        "\t\tvariable = vic3_todo_slot_$SLOT$",
        "\t\tvic3_todo_met > 0",
        "\t}",
        "}",
        "vic3_todo_slot_tracked = {",
        "\thas_variable_list = vic3_todo_slot_$SLOT$",
        "\tany_in_list = {",
        "\t\tvariable = vic3_todo_slot_$SLOT$",
        "\t\tvic3_todo_tr_count > 0",
        "\t}",
        "}",
        "",
    ]
    return L


def gen_effects(cat):
    L = header("Generated effects: targets, tracker creation by op, Journal Entry slots, country choices.")

    # building target
    L += ["# tracker scope: turn vic3_todo_target_idx into the scope a kind reads.",
          "vic3_todo_tr_apply_target = {", "\tif = {", "\t\tlimit = { var:vic3_todo_kind = 1 }"]
    L += indent(idx_tree(cat["buildings"], lambda i, b: ["set_variable = { name = vic3_todo_target value = bt:%s }" % b["key"]]), 2)
    L += ["\t}", "}", ""]

    # The picked index arrives as a value scope; copy it as a literal so the
    # stored variable is a plain number whatever the engine does with scopes.
    max_idx = max([i["idx"] for s in ("buildings", "technologies", "laws", "goods", "interest_groups") for i in cat[s]] +
                  [r["rank_value"] for r in cat["ranks"]])
    L += ["# tracker scope, scope:vic3_todo_op = the picked index (0..%d)." % max_idx,
          "vic3_todo_tr_set_target_idx = {"]
    L += indent(idx_tree([{"idx": n} for n in range(max_idx + 1)],
                         lambda n, _i: ["set_variable = { name = vic3_todo_target_idx value = %d }" % n],
                         var="scope:vic3_todo_op"), 1)
    L += ["}", ""]

    L += ["# country scope, scope:vic3_todo_op = 100 + kind.", "vic3_todo_tracker_add_by_op = {"]
    for n, k in enumerate(KINDS):
        L += ["\t%s = {" % ("if" if n == 0 else "else_if"), "\t\tlimit = { scope:vic3_todo_op = %d }" % (100 + k["id"]),
              "\t\tvic3_todo_tracker_add = { KIND = %d }" % k["id"], "\t}"]
    L += ["}", ""]

    # slot binding
    L += ["# country scope, scope:vic3_todo_new: give the new journal the first free",
          "# Journal Entry slot and add that Journal Entry.",
          "vic3_todo_bind_slot = {"]
    for n in range(SLOTS):
        L += ["\t%s = {" % ("if" if n == 0 else "else_if"),
              "\t\tlimit = { NOT = { has_variable = vic3_todo_slot_used_%d } }" % n,
              "\t\tvic3_todo_bind_to = { SLOT = %d }" % n, "\t}"]
    L += ["}", "",
          "# country scope, scope:vic3_todo_new.",
          "vic3_todo_bind_to = {",
          "\tset_variable = vic3_todo_slot_used_$SLOT$",
          "\tif = {",
          "\t\tlimit = { has_variable_list = vic3_todo_slot_$SLOT$ }",
          "\t\tclear_variable_list = vic3_todo_slot_$SLOT$",
          "\t}",
          "\tadd_to_variable_list = { name = vic3_todo_slot_$SLOT$ target = scope:vic3_todo_new }",
          "\tscope:vic3_todo_new = { set_variable = { name = vic3_todo_slot value = $SLOT$ } }",
          "\tset_variable = { name = vic3_todo_title_$SLOT$ value = scope:vic3_todo_new.var:vic3_todo_line1 }",
          "\tif = {",
          "\t\tlimit = { NOT = { has_journal_entry = je_vic3_todo_$SLOT$ } }",
          "\t\tadd_journal_entry = { type = je_vic3_todo_$SLOT$ }",
          "\t}",
          "}", ""]

    def slot_tree0(body_for_slot):
        """Tree over var:vic3_todo_slot (0-based) in todo scope."""
        slots = [{"idx": n} for n in range(SLOTS)]
        return (["if = {", "\tlimit = { has_variable = vic3_todo_slot }"] +
                indent(idx_tree(slots, lambda n, _i: body_for_slot(n), var="var:vic3_todo_slot"), 1) + ["}"])

    L += ["# todo scope: free its slot. Its Journal Entry then turns invalid and",
          "# leaves the journal silently. The title copy stays until the slot is reused.",
          "vic3_todo_unbind_slot = {"]
    L += indent(slot_tree0(lambda n: [
        "%s = {" % OWNER,
        "\tremove_variable = vic3_todo_slot_used_%d" % n,
        "\tif = {",
        "\t\tlimit = { has_variable_list = vic3_todo_slot_%d }" % n,
        "\t\tclear_variable_list = vic3_todo_slot_%d" % n,
        "\t}",
        "}"]), 1)
    L += ["\tremove_variable = vic3_todo_slot", "}", ""]

    L += ["# todo scope: copy line 1 to the country, where the Journal Entry's name reads it.",
          "vic3_todo_sync_title = {"]
    L += indent(slot_tree0(lambda n: [
        "save_scope_as = vic3_todo_title_src",
        "%s = { set_variable = { name = vic3_todo_title_%d value = scope:vic3_todo_title_src.var:vic3_todo_line1 } }" % (OWNER, n)]), 1)
    L += ["}", ""]

    L += ["# todo scope: re-add its Journal Entry (after reopening a completed or failed journal).",
          "vic3_todo_ensure_je = {"]
    L += indent(slot_tree0(lambda n: [
        "%s = {" % OWNER,
        "\tif = {",
        "\t\tlimit = { NOT = { has_journal_entry = je_vic3_todo_%d } }" % n,
        "\t\tadd_journal_entry = { type = je_vic3_todo_%d }" % n,
        "\t}",
        "}"]), 1)
    L += ["}", ""]

    # country choices
    L += ["# country scope: the relations picker's list, the 48 largest economies",
          "# other than us, as capitals (the GUI names a country through its capital).",
          "vic3_todo_build_country_choices = {",
          "\tsave_scope_as = vic3_todo_chooser",
          "\tif = {",
          "\t\tlimit = { has_variable_list = vic3_todo_country_choices }",
          "\t\tclear_variable_list = vic3_todo_country_choices",
          "\t}"]
    for pos in range(48):
        L += ["\tordered_country = {",
              "\t\tlimit = {",
              "\t\t\tNOT = { this = scope:vic3_todo_chooser }",
              "\t\t\texists = capital",
              "\t\t}",
              "\t\torder_by = gdp",
              "\t\tposition = %d" % pos,
              "\t\tcheck_range_bounds = no",
              "\t\tcapital = {",
              "\t\t\tscope:vic3_todo_chooser = {",
              "\t\t\t\tadd_to_variable_list = { name = vic3_todo_country_choices target = PREV }",
              "\t\t\t}",
              "\t\t}",
              "\t}"]
    L += ["}", ""]
    return L


def gen_journal_entries():
    L = header("One Journal Entry per journal slot. A slot's entry is added when a journal is bound to it\n"
               "# (vic3_todo_bind_to) and leaves silently when the slot is freed (invalid).")
    for n in range(SLOTS):
        L += [
            "je_vic3_todo_%d = {" % n,
            "\tgroup = je_group_vic3_todo",
            '\ticon = "gfx/interface/icons/event_icons/event_industry.dds"',
            "",
            "\twidget = {",
            '\t\tgui = "gui/journal_entry_widgets/vic3_todo_je_widgets_generated.gui"',
            '\t\tname = "vic3_todo_je_widget_%d"' % n,
            '\t\tcontainer = "custom_widget_container_1"',
            "\t}",
            "",
            "\tcomplete = {",
            "\t\tcustom_tooltip = {",
            "\t\t\ttext = je_vic3_todo_complete_tt",
            "\t\t\tvic3_todo_slot_done = { SLOT = %d }" % n,
            "\t\t}",
            "\t}",
            "\tfail = {",
            "\t\tcustom_tooltip = {",
            "\t\t\ttext = je_vic3_todo_fail_tt",
            "\t\t\tvic3_todo_slot_failed = { SLOT = %d }" % n,
            "\t\t}",
            "\t}",
            "\tinvalid = {",
            "\t\tNOT = { has_variable = vic3_todo_slot_used_%d }" % n,
            "\t}",
            "",
            "\tstatus_desc = {",
            "\t\tfirst_valid = {",
            "\t\t\ttriggered_desc = {",
            "\t\t\t\tdesc = je_vic3_todo_status_overdue",
            "\t\t\t\ttrigger = { vic3_todo_slot_overdue = { SLOT = %d } }" % n,
            "\t\t\t}",
            "\t\t\ttriggered_desc = {",
            "\t\t\t\tdesc = je_vic3_todo_status_met",
            "\t\t\t\ttrigger = { vic3_todo_slot_met = { SLOT = %d } }" % n,
            "\t\t\t}",
            "\t\t\ttriggered_desc = {",
            "\t\t\t\tdesc = je_vic3_todo_status_tracked",
            "\t\t\t\ttrigger = { vic3_todo_slot_tracked = { SLOT = %d } }" % n,
            "\t\t\t}",
            "\t\t\ttriggered_desc = {",
            "\t\t\t\tdesc = je_vic3_todo_status_plain",
            "\t\t\t\ttrigger = { always = yes }",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "",
            "\ton_weekly_pulse = {",
            "\t\teffect = {",
            "\t\t\tif = {",
            "\t\t\t\tlimit = { has_variable_list = vic3_todo_slot_%d }" % n,
            "\t\t\t\tevery_in_list = {",
            "\t\t\t\t\tvariable = vic3_todo_slot_%d" % n,
            "\t\t\t\t\tvic3_todo_evaluate_one = yes",
            "\t\t\t\t}",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "",
            "\tweight = 100",
            "\ttransferable = no",
            "\tcan_revolution_inherit = no",
            "}",
            "",
        ]
    return L


def gen_custom_loc(cat):
    L = header("Customizable localization: names of trackers' kinds and targets (container scope).")

    def block(name, entries, doc, fallback="vic3_todo_target_none"):
        out = ["# " + doc, "%s = {" % name, "\ttype = container", "\trandom_valid = no"]
        for trig, key in entries:
            out += ["\ttext = {", "\t\ttrigger = { %s }" % trig, "\t\tlocalization_key = %s" % key, "\t}"]
        out += ["\ttext = {", "\t\ttrigger = { always = yes }", "\t\tlocalization_key = %s" % fallback, "\t}", "}", ""]
        return out

    L += block("vic3_todo_kind_name", [("var:vic3_todo_kind = %d" % k["id"], "vic3_todo_kind_%s" % k["key"]) for k in KINDS],
               "Tracker kind.", "vic3_todo_kind_unknown")
    sections = [("building", cat["buildings"]), ("technology", cat["technologies"]), ("law", cat["laws"]),
                ("goods", cat["goods"]), ("interest_group", cat["interest_groups"])]
    for name, items in sections:
        L += block("vic3_todo_tn_%s" % name,
                   [("has_variable = vic3_todo_has_target var:vic3_todo_target_idx = %d" % it["idx"], it["key"])
                    for it in live(items)],
                   "Target name for %s trackers." % name)
    L += block("vic3_todo_tn_rank",
               [("has_variable = vic3_todo_has_target var:vic3_todo_target_idx = %d" % r["rank_value"], "vic3_todo_rank_%s" % r["key"])
                for r in cat["ranks"]], "Target rank.")
    L += block("vic3_todo_rank_current",
               [("vic3_todo_tr_raw = %d" % r["rank_value"], "vic3_todo_rank_%s" % r["key"]) for r in cat["ranks"]],
               "The country's current rank (rank trackers).", "vic3_todo_target_none")
    L += block("vic3_todo_mode_name",
               [("var:vic3_todo_mode = 1", "vic3_todo_mode_1"), ("var:vic3_todo_mode = 2", "vic3_todo_mode_2"),
                ("var:vic3_todo_mode = 3", "vic3_todo_mode_3"), ("var:vic3_todo_mode = 4", "vic3_todo_mode_4")],
               "Tracker mode.", "vic3_todo_mode_2")
    L += block("vic3_todo_status",
               [("has_tag = vic3_todo_done", "vic3_todo_status_done"),
                ("has_tag = vic3_todo_failed", "vic3_todo_status_failed"),
                ("vic3_todo_overdue > 0", "vic3_todo_status_overdue"),
                ("vic3_todo_met > 0", "vic3_todo_status_met"),
                ("vic3_todo_tr_count > 0", "vic3_todo_status_progress")],
               "Journal status (todo scope).", "vic3_todo_status_plain")
    return L


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

def sgui_exec(name, op, extra=""):
    scope = "GuiScope.SetRoot( GetPlayer.MakeScope )%s.AddScope( 'vic3_todo_op', MakeScopeValue( '(CFixedPoint)%d' ) ).End" % (extra, op)
    return ("[GetScriptedGui('%s').IsValid( %s )]" % (name, scope),
            "[GetScriptedGui('%s').Execute( %s )]" % (name, scope))


def picker_button(text, op, sgui="vic3_todo_pick_sgui", width=250):
    enabled, onclick = sgui_exec(sgui, op)
    return [
        "button = {",
        "\tusing = default_button",
        "\tsize = { %d 26 }" % width,
        '\ttext = "%s"' % text,
        '\tenabled = "%s"' % enabled,
        '\tonclick = "%s"' % onclick,
        '\tonclick = "[GetVariableSystem.Clear(\'vic3_todo_picker_open\')]"',
        "\tusing = fontsize_small",
        "}",
    ]


def grid(buttons, per_row=2):
    out = ["flowcontainer = {", "\tdirection = vertical", "\tspacing = 3"]
    for i in range(0, len(buttons), per_row):
        out += ["\tflowcontainer = {", "\t\tdirection = horizontal", "\t\tspacing = 4"]
        for b in buttons[i:i + per_row]:
            out += indent(b, 2)
        out += ["\t}"]
    return out + ["}"]


def section_title(key):
    return ["textbox = {", '\ttext = "%s"' % key, "\tusing = fontsize_medium", '\tdefault_format = "#title"',
            "\tautoresize = yes", "\tmargin_top = 6", "\talign = left|nobaseline", "}"]


def gen_gui_pickers(cat):
    L = header("Picker types used by gui/vic3_todo_window.gui.")
    L.append("types vic3_todo_generated_types {")
    body = []

    # kind picker
    body += ["### Tracker kinds, grouped. Each button: vic3_todo_edit_sgui op 100 + kind.",
             "type vic3_todo_kind_picker = flowcontainer {", "\tdirection = vertical", "\tspacing = 4"]
    for c in CATEGORIES:
        body += indent(section_title("vic3_todo_cat_%s" % c), 1)
        btns = []
        for k in [k for k in KINDS if k["cat"] == c]:
            enabled, onclick = sgui_exec("vic3_todo_edit_sgui", 100 + k["id"])
            btns.append(["button = {", "\tusing = default_button", "\tsize = { 250 26 }",
                         '\ttext = "vic3_todo_kind_%s"' % k["key"], "\tusing = fontsize_small",
                         '\ttooltip = "vic3_todo_kind_%s_tt"' % k["key"],
                         '\tenabled = "%s"' % enabled, '\tonclick = "%s"' % onclick,
                         '\tonclick = "[GetVariableSystem.Clear(\'vic3_todo_kind_picker\')]"', "}"])
        body += indent(grid(btns), 1)
    body += ["}", ""]

    # buildings
    body += ["### Building types (op = catalog index).", "type vic3_todo_picker_building = flowcontainer {",
             "\tdirection = vertical", "\tspacing = 4"]
    index = {b["key"]: b["idx"] for b in live(cat["buildings"])}
    assigned = set()
    for sec, (_ja, _en, groups) in BUILDING_SECTIONS.items():
        if groups is None:
            continue
        items = [b for b in live(cat["buildings"]) if b["group"] in groups]
        assigned |= {b["key"] for b in items}
        body += indent(section_title("vic3_todo_bsec_%s" % sec), 1)
        body += indent(grid([picker_button(b["key"], index[b["key"]]) for b in items]), 1)
    rest = [b for b in live(cat["buildings"]) if b["key"] not in assigned]
    body += indent(section_title("vic3_todo_bsec_infrastructure"), 1)
    body += indent(grid([picker_button(b["key"], index[b["key"]]) for b in rest]), 1)
    body += ["}", ""]

    # technologies: by category tab, era headers
    tindex = {t["key"]: t["idx"] for t in live(cat["technologies"])}
    for tc in TECH_CATEGORIES:
        body += ["### Technologies: %s (op = catalog index)." % tc,
                 "type vic3_todo_picker_technology_%s = flowcontainer {" % tc, "\tdirection = vertical", "\tspacing = 4"]
        for era in ERAS:
            items = [t for t in live(cat["technologies"]) if t["category"] == tc and t["era"] == era]
            if not items:
                continue
            body += indent(section_title("vic3_todo_%s" % era), 1)
            body += indent(grid([picker_button(t["key"], tindex[t["key"]]) for t in items]), 1)
        others = [t for t in live(cat["technologies"]) if t["category"] == tc and t["era"] not in ERAS]
        if others:
            body += indent(grid([picker_button(t["key"], tindex[t["key"]]) for t in others]), 1)
        body += ["}", ""]
    leftovers = [t for t in live(cat["technologies"]) if t["category"] not in TECH_CATEGORIES]
    if leftovers:
        raise SystemExit("technology categories not covered: %s" % sorted({t["category"] for t in leftovers}))

    # laws by group
    lindex = {l["key"]: l["idx"] for l in live(cat["laws"])}
    body += ["### Laws by law group (op = catalog index).", "type vic3_todo_picker_law = flowcontainer {",
             "\tdirection = vertical", "\tspacing = 4"]
    groups = OrderedDict()
    for l in sorted(live(cat["laws"]), key=lambda l: (l["group"], l["key"])):
        groups.setdefault(l["group"], []).append(l)
    for g, items in groups.items():
        body += indent(section_title(g), 1)
        body += indent(grid([picker_button(l["key"], lindex[l["key"]]) for l in items]), 1)
    body += ["}", ""]

    # goods
    gindex = {g["key"]: g["idx"] for g in live(cat["goods"])}
    body += ["### Goods (op = catalog index).", "type vic3_todo_picker_goods = flowcontainer {", "\tdirection = vertical",
             "\tspacing = 4"]
    body += indent(grid([picker_button(g["key"], gindex[g["key"]], width=165) for g in live(cat["goods"])], per_row=3), 1)
    body += ["}", ""]

    # interest groups
    body += ["### Interest groups (op = catalog index).", "type vic3_todo_picker_interest_group = flowcontainer {",
             "\tdirection = vertical", "\tspacing = 4"]
    body += indent(grid([picker_button(g["key"], g["idx"]) for g in live(cat["interest_groups"])]), 1)
    body += ["}", ""]

    # ranks
    body += ["### Country ranks (op = rank_value).", "type vic3_todo_picker_rank = flowcontainer {", "\tdirection = vertical",
             "\tspacing = 4"]
    ranks = sorted(cat["ranks"], key=lambda r: -r["rank_value"])
    body += indent(grid([picker_button("vic3_todo_rank_%s" % r["key"], r["rank_value"]) for r in ranks]), 1)
    body += ["}", ""]

    # vanilla pin buttons per slot (GetPlayerJournalEntry needs a literal key)
    body += ["### The vanilla outliner pin of the journal's own Journal Entry. Only the",
             "### child for the journal's slot is visible, so only its datacontext is read.",
             "type vic3_todo_pin_buttons = widget {", "\tsize = { 26 26 }"]
    for n in range(SLOTS):
        body += ["\twidget = {",
                 "\t\tsize = { 26 26 }",
                 "\t\tvisible = \"[And( EqualTo_CFixedPoint( ScriptContainer.MakeScope.ScriptValue('vic3_todo_je_active'), '(CFixedPoint)1' ), And( ScriptContainer.HasVariable('vic3_todo_slot'), EqualTo_CFixedPoint( ScriptContainer.GetVariableValue('vic3_todo_slot'), '(CFixedPoint)%d' ) ) )]\"" % n,
                 "\t\tbutton_icon_pin = {",
                 "\t\t\tdatacontext = \"[GetPlayerJournalEntry('je_vic3_todo_%d')]\"" % n,
                 "\t\t\tsize = { 100% 100% }",
                 "\t\t\tvisible = \"[JournalEntry.IsPinnedInOutliner]\"",
                 "\t\t\tonclick = \"[JournalEntry.TogglePinInOutliner]\"",
                 "\t\t\ttooltip = \"vic3_todo_unpin_tt\"",
                 "\t\t}",
                 "\t\tbutton_icon_unpin = {",
                 "\t\t\tdatacontext = \"[GetPlayerJournalEntry('je_vic3_todo_%d')]\"" % n,
                 "\t\t\tsize = { 100% 100% }",
                 "\t\t\tvisible = \"[Not( JournalEntry.IsPinnedInOutliner )]\"",
                 "\t\t\tonclick = \"[JournalEntry.TogglePinInOutliner]\"",
                 "\t\t\ttooltip = \"vic3_todo_pin_tt\"",
                 "\t\t}",
                 "\t}"]
    body += ["}", ""]

    L += indent(body, 1)
    L.append("}")
    return L


def gen_je_widgets():
    L = header("The custom widget of each slot's Journal Entry. The slot list vic3_todo_slot_<n>\n"
               "# holds exactly the journal bound to the slot, so a datamodel over it gives the\n"
               "# widget that journal's ScriptContainer without a Var() promote.")
    for n in range(SLOTS):
        L += ["flowcontainer = {",
              '\tname = "vic3_todo_je_widget_%d"' % n,
              "\tdirection = vertical",
              "\tvisible = \"[JournalEntry.IsActive]\"",
              "\tdatamodel = \"[JournalEntry.GetCountry.MakeScope.GetList('vic3_todo_slot_%d')]\"" % n,
              "\titem = {",
              "\t\tvic3_todo_je_body = {",
              "\t\t\tdatacontext = \"[Scope.GetScriptContainer]\"",
              "\t\t}",
              "\t}",
              "}",
              ""]
    return L


def yml_escape(s):
    return s.replace('"', '\\"')


def gen_loc(cat, lang):
    j = lang == "japanese"
    L = ["l_%s:" % lang,
         " # GENERATED by tools/generate_mod.py - do not edit."]

    def add(key, ja, en):
        L.append(' %s:0 "%s"' % (key, yml_escape(ja if j else en)))

    for c, (ja, en) in CATEGORIES.items():
        add("vic3_todo_cat_%s" % c, ja, en)
    tips = {
        1: ("国内にある、選んだ種類の建物のレベル合計。建設中のレベルは含みません。", "Total levels of the chosen building type in our states."),
        33: ("作成してからの日数。リマインダーや「○日後に見直す」に使えます。", "Days since the tracker was created. Useful as a reminder."),
        32: ("どの国とも戦争していない状態。", "Not at war with anyone."),
        7: ("選んだ技術を研究済みかどうか。研究途中の割合は表示しません。", "Whether the chosen technology is researched. No partial progress is shown."),
        8: ("選んだ法律が施行されているかどうか。", "Whether the chosen law is in force."),
        10: ("国家ランクが選んだランク以上かどうか。", "Whether our rank is at least the chosen one."),
        9: ("選んだ国との関係値（-100〜100）。", "Relations with the chosen country (-100 to 100)."),
        40: ("選んだ国と戦争中かどうか。失敗条件にすると「この国と戦争になったら失敗」も作れます。",
             "Whether we are at war with the chosen country. As a failure condition: fail if war breaks out."),
        34: ("選んだ自国の州の人口。", "Population of the chosen state of ours."),
        38: ("選んだ自国の州の騒乱（0〜100%）。", "Turmoil in the chosen state of ours (0-100%)."),
    }
    for k in KINDS:
        add("vic3_todo_kind_%s" % k["key"], k["ja"], k["en"])
        tja, ten = tips.get(k["id"], ("%sの値を追跡します。" % k["ja"], "Tracks %s." % k["en"].lower()))
        add("vic3_todo_kind_%s_tt" % k["key"], tja, ten)
    for sec, (ja, en, _g) in BUILDING_SECTIONS.items():
        add("vic3_todo_bsec_%s" % sec, ja, en)
    for i, era in enumerate(ERAS, 1):
        add("vic3_todo_%s" % era, "第%d時代" % i, "Era %d" % i)
    for tc, (ja, en) in TECH_CATEGORIES.items():
        add("vic3_todo_techcat_%s" % tc, ja, en)
    for r in cat["ranks"]:
        ja, en = RANK_NAMES.get(r["key"], (r["key"], r["key"]))
        add("vic3_todo_rank_%s" % r["key"], ja, en)
    for n in range(SLOTS):
        L.append(" je_vic3_todo_%d:0 \"[JournalEntry.GetCountry.MakeScope.Var('vic3_todo_title_%d').GetFlagName]\"" % (n, n))
        L.append(" je_vic3_todo_%d_reason:0 \"$vic3_todo_je_reason$\"" % n)
        L.append(" je_vic3_todo_%d_status:0 \"$je_vic3_todo_status_plain$\"" % n)
    return L


# ---------------------------------------------------------------------------
# Template expansion for the hand-written window layout
# ---------------------------------------------------------------------------

TEMPLATE = os.path.join(ROOT, "tools", "templates", "vic3_todo_window.gui.in")
_MACRO = __import__("re").compile(r"\{\{([^{}]*)\}\}")
_ROOT = "GuiScope.SetRoot( GetPlayer.MakeScope )"
_CMP = {"eq": "EqualTo_CFixedPoint", "gt": "GreaterThan_CFixedPoint", "lt": "LessThan_CFixedPoint",
        "ge": "GreaterThanOrEqualTo_CFixedPoint", "le": "LessThanOrEqualTo_CFixedPoint"}


def _op(n):
    return ".AddScope( 'vic3_todo_op', MakeScopeValue( '(CFixedPoint)%s' ) )" % n


def _expand_one(m):
    parts = m.group(1).split(":")
    name, args = parts[0], parts[1:]
    if name in ("exec", "valid"):
        (sgui,) = args
        return "GetScriptedGui('%s').%s( %s.End )" % (sgui, "Execute" if name == "exec" else "IsValid", _ROOT)
    if name in ("exec_op", "valid_op"):
        sgui, n = args
        return "GetScriptedGui('%s').%s( %s%s.End )" % (sgui, "Execute" if name == "exec_op" else "IsValid", _ROOT, _op(n))
    if name in ("exec_item", "valid_item"):
        sgui, n = args
        return "GetScriptedGui('%s').%s( %s.AddScope( 'vic3_todo_item', ScriptContainer.MakeScope )%s.End )" % (
            sgui, "Execute" if name == "exec_item" else "IsValid", _ROOT, _op(n))
    if name == "sv":
        return "ScriptContainer.MakeScope.ScriptValue('%s')" % args[0]
    if name == "psv":
        return "GetPlayer.MakeScope.ScriptValue('%s')" % args[0]
    if name in _CMP:
        expr, n = args
        return "%s( %s, '(CFixedPoint)%s' )" % (_CMP[name], expr, n)
    raise SystemExit("unknown template macro: %s" % m.group(0))


def expand_template(text):
    while True:
        new = _MACRO.sub(_expand_one, text)
        if new == text:
            return new
        text = new


def gen_window():
    with open(TEMPLATE, encoding="utf-8") as fh:
        text = expand_template(fh.read())
    lines = ["### GENERATED by tools/generate_mod.py from tools/templates/vic3_todo_window.gui.in - do not edit."]
    return lines + text.splitlines()


def gen_static_loc(lang):
    sys.path.insert(0, os.path.join(ROOT, "tools", "templates"))
    from loc_strings import STRINGS
    j = 0 if lang == "japanese" else 1
    lines = ["l_%s:" % lang, " # GENERATED by tools/generate_mod.py from tools/templates/loc_strings.py - do not edit."]
    for key in sorted(STRINGS):
        lines.append(' %s:0 "%s"' % (key, yml_escape(STRINGS[key][j]).replace("\n", "\\n")))
    return lines


def outputs(cat):
    return OrderedDict([
        ("common/script_values/vic3_todo_generated_values.txt", gen_values(cat)),
        ("common/scripted_triggers/vic3_todo_generated_triggers.txt", gen_triggers()),
        ("common/scripted_effects/vic3_todo_generated_effects.txt", gen_effects(cat)),
        ("common/journal_entries/vic3_todo_generated_journal_entries.txt", gen_journal_entries()),
        ("common/customizable_localization/vic3_todo_generated_loc.txt", gen_custom_loc(cat)),
        ("gui/vic3_todo_generated_pickers.gui", gen_gui_pickers(cat)),
        ("gui/journal_entry_widgets/vic3_todo_je_widgets_generated.gui", gen_je_widgets()),
        ("gui/vic3_todo_window_generated.gui", gen_window()),
        ("localization/japanese/vic3_todo_generated_l_japanese.yml", gen_loc(cat, "japanese")),
        ("localization/english/vic3_todo_generated_l_english.yml", gen_loc(cat, "english")),
        ("localization/japanese/vic3_todo_ui_generated_l_japanese.yml", gen_static_loc("japanese")),
        ("localization/english/vic3_todo_ui_generated_l_english.yml", gen_static_loc("english")),
    ])


def render(lines):
    return BOM + "\n".join(lines).rstrip("\n") + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--mod", default=MOD)
    args = ap.parse_args(argv)
    with open(args.catalog, encoding="utf-8") as fh:
        cat = json.load(fh)
    ids = [k["id"] for k in KINDS]
    assert len(ids) == len(set(ids)), "duplicate kind ids"
    stale = []
    for rel, lines in outputs(cat).items():
        path = os.path.join(args.mod, rel)
        text = render(lines)
        current = None
        if os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as fh:
                current = fh.read()
        if current != text:
            stale.append(rel)
            if not args.check:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
    if args.check:
        for rel in stale:
            print("stale: " + rel)
        return 1 if stale else 0
    print("wrote %d file(s)" % len(stale))
    return 0


if __name__ == "__main__":
    sys.exit(main())
