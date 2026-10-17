"""COMPLETE (exact enumeration) vs DMN gap/overlap analysis (baseline B4).

Each function returns a plain dict for results.json; ``report`` prints them.
"""

from __future__ import annotations

import csv
import random
import time
from itertools import product
from statistics import mean

from . import examples as ex
from . import latc, randomized
from .checks import structural_report
from .compare import compare
from .dmn import (ANY, DMNTable, Input, Point, Rule, _cells, analyse, at_least, below, closed,
                  describe_region, entry_set, expand, from_exact, half_open, to_exact, violations)
from .model import RV, Attribute, DecisionTable, Row, attrs
from .reference import exact_complement

# -- pension rule as DMN -------------------------------------------------------------

AGE_DOMAIN = closed(*ex.AGE_RANGE)
CONTRIB_DOMAIN = closed(*ex.CONTRIBUTION_RANGE)
AGE_BINS = ((">=65", closed(65, ex.AGE_RANGE[1])), ("60-64", half_open(60, 65)),
            ("<60", half_open(ex.AGE_RANGE[0], 60)))
CONTRIB_BINS = ((">=30", closed(30, ex.CONTRIBUTION_RANGE[1])),
                ("<30", half_open(ex.CONTRIBUTION_RANGE[0], 30)))
PENSION_NUMERIC = {"Age": (AGE_DOMAIN, AGE_BINS), "ContributionYears": (CONTRIB_DOMAIN, CONTRIB_BINS)}

PENSION_INPUTS = (
    Input("Sex", values=("M", "F")),
    Input("Activity", values=("D", "I")),
    Input("ContributionYears", domain=CONTRIB_DOMAIN, bins=CONTRIB_BINS),
    Input("Age", domain=AGE_DOMAIN, bins=AGE_BINS),
)


def pension_t0_dmn(hit_policy: str = "UNIQUE") -> DMNTable:
    """Table 1a as a DMN table: one rule per row, bin intervals for the numbers."""
    return from_exact(ex.pension_table(), PENSION_NUMERIC, hit_policy)


def pension_compact_dmn() -> DMNTable:
    """The completed rule (Table 1a + Table 2 bis outcomes) written compactly.

    Hand-written; ``tests`` check it expands to exactly the 24 completed rows.
    """
    M, F, D, I = Point("M"), Point("F"), Point("D"), Point("I")
    ge30, lt30 = at_least(30), below(30)
    rules = [
        Rule((ANY, ANY, ANY, below(60)), "NO"),
        Rule((M, ANY, ANY, half_open(60, 65)), "NO"),
        Rule((M, D, ANY, at_least(65)), "YES"),
        Rule((M, I, ge30, at_least(65)), "YES"),
        Rule((M, I, lt30, at_least(65)), RV),
        Rule((F, D, ANY, at_least(60)), "YES"),
        Rule((F, I, ge30, at_least(60)), "YES"),
        Rule((F, I, lt30, at_least(60)), RV),
    ]
    return DMNTable(PENSION_INPUTS, rules, "UNIQUE", output_values=("YES", "NO", RV))


# Raw Table 1 (before normalisation), Age written as the experts wrote it.
RAW_TABLE1 = [
    (("M", "D", ">=30", ">=65"), "YES"),
    (("M", "I", ">=30", ">=65"), "YES"),
    (("F", "D", ">=30", ">=60"), "YES"),
    (("F", "I", ">=30", ">=60"), "YES"),
    (("F", "I", ">=30", "<60"), "NO"),
    (("M", "I", "<30", ">=65"), "YES"),
    (("M", "I", "<30", "<65"), "NO"),
    (("F", "D", "<30", ">=60"), RV),
]
RAW_AGE = {">=65": at_least(65), ">=60": at_least(60), "<60": below(60), "<65": below(65)}
RAW_CONTRIB = {">=30": at_least(30), "<30": below(30)}


def raw_table1_dmn(hit_policy: str = "UNIQUE") -> DMNTable:
    rules = [Rule((Point(s), Point(a), RAW_CONTRIB[c], RAW_AGE[g]), out)
             for (s, a, c, g), out in RAW_TABLE1]
    return DMNTable(PENSION_INPUTS, rules, hit_policy, output_values=("YES", "NO", RV))


def raw_table1_as_labels() -> DecisionTable:
    """What LATC sees if the raw Age labels are taken as opaque values."""
    return DecisionTable(attrs([("Sex", "MF"), ("Activity", "DI"), ("ContributionYears", (">=30", "<30")),
                                ("Age", (">=65", ">=60", "<60", "<65"))]),
                         [Row(c, o) for c, o in RAW_TABLE1])


# -- shared helpers ------------------------------------------------------------------

def dmn_gap_tuples(dmn: DMNTable, **kw) -> tuple[list, dict]:
    a = analyse(dmn, **kw)
    tuples, partial = expand(a.gaps, dmn.inputs)
    return tuples, {"gap_regions": len(a.gaps), "gap_regions_unmerged": a.raw_gaps,
                    "gap_tuples": len(tuples), "partial_bins": partial,
                    "overlap_pairs": len(a.overlaps), "analysis": a}


def _strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "analysis"}


# -- (a) T0 as DMN -------------------------------------------------------------------

def pension_t0() -> dict:
    dmn = pension_t0_dmn()
    t = ex.pension_table()
    tuples, info = dmn_gap_tuples(dmn)
    _, info_set = dmn_gap_tuples(dmn, enum_grouping="set")
    r = compare(tuples, t)
    return {"complete_rows": len(exact_complement(t)), **_strip(info),
            "gap_regions_set_grouping": info_set["gap_regions"],
            "gap_tuples_equal_complete": r.exact, "comparison": r.as_dict(),
            "regions": [describe_region(g, dmn.inputs) for g in info["analysis"].gaps],
            "review_size_complete": {"rows": 16, "cells": 16 * 5},
            "review_size_dmn_gaps": {"rules": info["gap_regions"], "cells": info["gap_regions"] * 5}}


# -- (b) compact rule ----------------------------------------------------------------

def pension_compact() -> dict:
    dmn = pension_compact_dmn()
    a = analyse(dmn)
    exact, conv = to_exact(dmn)
    completed = {r.condition: r.outcome for r in ex.pension_completed().rows}
    same = {r.condition: r.outcome for r in exact.rows} == completed and len(exact.rows) == 24
    rep = structural_report(exact)

    # Two seeded faults, checked by both analyses.
    drop = DMNTable(dmn.inputs, dmn.rules[:4] + dmn.rules[5:], "UNIQUE", output_values=dmn.output_values)
    widen_rules = list(dmn.rules)
    widen_rules[1] = Rule((Point("M"), ANY, ANY, at_least(60)), "NO")
    widen = DMNTable(dmn.inputs, widen_rules, "UNIQUE", output_values=dmn.output_values)
    faults = {}
    for name, t in (("drop_rule_5", drop), ("widen_rule_2", widen)):
        fa = analyse(t)
        fx, _ = to_exact(t)
        frep = structural_report(fx)
        faults[name] = {
            "dmn_gap_regions": len(fa.gaps), "dmn_gap_tuples": len(expand(fa.gaps, t.inputs)[0]),
            "dmn_overlap_pairs": fa.overlap_pairs, "dmn_violations": len(violations(t, fa)["violating_pairs"]),
            "complete_uncovered": frep["uncovered"], "complete_multi_hit": frep["multi_hit_tuples"],
            "complete_conflicts": frep["conflicting_tuples"]}
    return {"expands_to_completed_table": same, "gap_regions": len(a.gaps),
            "overlap_pairs": len(a.overlaps), "structural": rep,
            "misaligned": conv["misaligned_entries"],
            "review_compact": dmn.review_size(),
            "review_exact": {"rules": 24, "non_wildcard_cells": 24 * 4, "cells": 24 * 5},
            "faults": faults}


# -- (c) raw Table 1 -----------------------------------------------------------------

def raw_table1() -> dict:
    out = {}
    for hp in ("UNIQUE", "ANY", "FIRST"):
        dmn = raw_table1_dmn(hp)
        a = analyse(dmn)
        out[hp] = violations(dmn, a)
    dmn = raw_table1_dmn()
    a = analyse(dmn)
    exact, conv = to_exact(dmn)
    gap_tuples, _ = expand(a.gaps, dmn.inputs)
    complement = exact_complement(exact)
    covered_raw = {r.condition for r in exact.rows}
    per_row = []
    t1a = ex.PENSION_T0
    for k, ((s, ac, c, g), o) in enumerate(RAW_TABLE1):
        raw_rows = [r.condition for r in to_exact(DMNTable(dmn.inputs, [dmn.rules[k]]))[0].rows]
        per_row.append({"row": k + 1, "raw": f"{s} {ac} {c} {g} -> {o}", "raw_tuples": len(raw_rows),
                        "table1a": " ".join(t1a[k].condition) + f" -> {t1a[k].outcome}",
                        "table1a_within_raw": t1a[k].condition in raw_rows,
                        "outcome_changed": t1a[k].outcome != o})
    labels = raw_table1_as_labels()
    age = dmn.inputs[3]
    age_cells = [c.feel() for c in _cells(age, [entry_set(age, r.entries[3]) for r in dmn.rules])[0]]
    return {"overlaps_by_policy": {k: {"pairs": v["overlapping_pairs"],
                                       "violating": v["violating_pairs"]} for k, v in out.items()},
            "dmn_gap_regions": len(a.gaps), "dmn_gap_tuples": len(gap_tuples),
            "dmn_gaps_equal_complete": set(gap_tuples) == set(complement) and len(gap_tuples) == len(complement),
            "raw_rules_cover_tuples": len(covered_raw), "table1a_covers": len(ex.PENSION_T0),
            "misaligned": conv["misaligned_entries"],
            "latc_label_view": {"card_age": 4, "product": latc.product_of_cards(labels),
                                "missing": latc.missing_count(labels)},
            "age_elementary_cells": age_cells, "per_row": per_row}


# -- (d) counterexample and random scenarios -------------------------------------------

def counterexample() -> dict:
    out = {}
    for name, t in (("T0", ex.counterexample_table()), ("twin", ex.counterexample_twin())):
        tuples, info = dmn_gap_tuples(from_exact(t))
        out[name] = {**_strip(info), "exact": compare(tuples, t).exact,
                     "regions": [describe_region(g, from_exact(t).inputs) for g in info["analysis"].gaps]}
    return out


VARIANTS = ("dmn_declared_values", "dmn_observed_values", "dmn_declared+constraint_filter")


def random_scenarios(trials: int = 1000, seed: int = 20210101) -> dict:
    """Same generator and seed as RQ2.3, so these are the same tables."""
    rng = random.Random(seed)
    out = {}
    for scenario in randomized.SCENARIOS:
        acc = {v: {"exact": 0, "missed": [], "outside": [], "regions": []} for v in VARIANTS}
        points = []
        for _ in range(trials):
            t = randomized.generate_case(rng, scenario)
            points.append(len(exact_complement(t)))
            for v in VARIANTS:
                dmn = from_exact(t, values="observed" if v == "dmn_observed_values" else "declared")
                tuples, info = dmn_gap_tuples(dmn)
                if v.endswith("constraint_filter"):
                    tuples = [c for c in tuples if t.is_valid(c)]
                r = compare(tuples, t)
                a = acc[v]
                a["exact"] += r.exact
                a["missed"].append(r.missed)
                a["outside"].append(r.outside_space)
                a["regions"].append(info["gap_regions"])
        out[scenario] = {v: {"exact_rate": a["exact"] / trials, "mean_missed": mean(a["missed"]),
                             "mean_outside_space": mean(a["outside"]),
                             "mean_gap_regions": mean(a["regions"])} for v, a in acc.items()}
        out[scenario]["mean_missing_points"] = mean(points)
    return out


# -- (e) timing ------------------------------------------------------------------------

DMN_FIELDS = ["n_attrs", "card", "space", "t0_rows", "missing", "complete_s", "dmn_s",
              "dmn_gap_regions", "dmn_raw_gaps"]


def bench(grid=None, max_space: int = 65_536, fill: float = 0.5, seed: int = 0,
          csv_path: str | None = None) -> list[dict]:
    from .bench import DEFAULT_GRID
    rng = random.Random(seed)
    res = []
    for n, c in (grid or DEFAULT_GRID):
        if c ** n > max_space:
            continue
        attributes = tuple(Attribute(f"attr_{i}", tuple(f"val_{j}" for j in range(c))) for i in range(n))
        space = list(product(*(a.domain for a in attributes)))
        t = DecisionTable(attributes, [Row(x, "YES") for x in rng.sample(space, int(len(space) * fill))])
        t0 = time.perf_counter()
        missing = exact_complement(t)
        complete_s = time.perf_counter() - t0
        dmn = from_exact(t)
        t0 = time.perf_counter()
        a = analyse(dmn)
        dmn_s = time.perf_counter() - t0
        res.append({"n_attrs": n, "card": c, "space": len(space), "t0_rows": len(t.rows),
                    "missing": len(missing), "complete_s": round(complete_s, 4), "dmn_s": round(dmn_s, 4),
                    "dmn_gap_regions": len(a.gaps), "dmn_raw_gaps": a.raw_gaps})
    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=DMN_FIELDS)
            w.writeheader()
            w.writerows(res)
    return res
