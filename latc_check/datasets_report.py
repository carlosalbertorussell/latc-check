"""Public-dataset experiments: UCI Car and Nursery, the DMN TCK, and the baselines.

Writes ``results/datasets/*.json``, ``summary.csv`` and ``SUMMARY.md``.  Run with
``python run_datasets.py`` (see ``--help``).  Every number except the timings
is determined by the base seed.

Experiments
-----------
B. completion on the UCI tables
   * random removal: T0 keeps a share of the rows (90 % ... 1 %), several
     seeds per level;
   * structured removal: T0 drops every row with one value of one attribute
     (every value of every attribute), the "unobserved declared value" case;
   * methods: COMPLETE (exact complement), LATC Reading A (deficit fill),
     LATC Reading B (odometer), DMN gap analysis of T0 as point rules with the
     declared values and with the values T0 shows;
   * restore check: T0 plus COMPLETE's rows, each with its true class from the
     full dataset, must equal the full table and be sound.
C. compact rules: an ID3 tree over each full table as DMN rules (0 gaps, 0
   overlaps, exact expansion), seeded faults, and the rank index.
D. DMN TCK: import every decision table, classify parsed / skipped, analyse
   the parsed ones, oracle where the domain is finite.
Baselines: the pension example and the three random scenarios of
``randomized`` (same generator and seed as ``results/results.json``).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import random
import sys
import time
from collections import Counter
from statistics import mean, median

from . import __version__, datasets, dmn_import, dmn_oracle, latc, randomized, tree
from . import examples as ex
from .checks import is_sound, structural_report
from .compare import compare
from .dmn import (ANY, DMNTable, Input, Interval, Not, OneOf, Point, Rule, analyse, closed,
                  describe_region, expand, from_exact, to_exact, violations)
from .model import DecisionTable, Row
from .rank import RankIndex
from .reference import exact_complement

LEVELS = (0.9, 0.75, 0.5, 0.25, 0.1, 0.01)
METHODS = ("COMPLETE", "LATC A (deficit fill)", "LATC B (odometer)", "DMN (declared values)",
           "DMN (observed values)")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# -- completion methods ---------------------------------------------------------------

def _dmn_gaps(t: DecisionTable, values: str):
    d = from_exact(t, values=values)
    a = analyse(d)
    tuples, _ = expand(a.gaps, d.inputs)
    return tuples, {"regions": len(a.gaps), "raw_regions": a.raw_gaps, "overlap_pairs": len(a.overlaps)}


def run_methods(t: DecisionTable, constraint_filter: bool = False) -> dict:
    """Candidate completion of every method, compared with the exact complement."""
    out = {}
    for m in METHODS:
        t0 = time.perf_counter()
        extra = {}
        if m == "COMPLETE":
            cand = exact_complement(t)
        elif m.startswith("LATC A"):
            cand = latc.deficit_fill(t)
        elif m.startswith("LATC B"):
            cand = latc.latc_odometer(t)
        else:
            cand, extra = _dmn_gaps(t, "declared" if "declared" in m else "observed")
            if constraint_filter:
                cand = [c for c in cand if t.is_valid(c)]
        secs = time.perf_counter() - t0
        r = compare(cand, t).as_dict()
        out[m] = {**r, **extra, "seconds": secs}
    return out


def restore_check(t0: DecisionTable, missing: list, truth: dict) -> dict:
    """T0 + missing rows with their true classes == the full table, and sound."""
    restored = t0.with_rows(list(t0.rows) + [Row(c, truth[c]) for c in missing])
    rep = structural_report(restored)
    same = (len(restored.rows) == len(truth)
            and {r.condition: r.outcome for r in restored.rows} == truth)
    return {"sound": is_sound(rep), "equals_full_table": same, "coverage": rep["coverage"],
            "single_hit": rep["single_hit"], "conflicts": rep["conflicting_tuples"]}


def _agg(runs: list[dict]) -> dict:
    """Mean metrics per method over a list of run_methods results."""
    out = {}
    for m in METHODS:
        rs = [r[m] for r in runs]
        s = {"runs": len(rs), "exact_rate": sum(r["exact"] for r in rs) / len(rs),
             "mean_missed": mean(r["missed"] for r in rs), "max_missed": max(r["missed"] for r in rs),
             "mean_duplicates": mean(r["duplicates"] for r in rs),
             "mean_regenerated_t0": mean(r["regenerated_t0"] for r in rs),
             "mean_outside_space": mean(r["outside_space"] for r in rs),
             "mean_candidate_rows": mean(r["n_candidate"] for r in rs),
             "mean_expected_rows": mean(r["n_expected"] for r in rs),
             "mean_ms": 1000 * mean(r["seconds"] for r in rs)}
        if "regions" in rs[0]:
            s["mean_regions"] = mean(r["regions"] for r in rs)
            s["mean_raw_regions"] = mean(r["raw_regions"] for r in rs)
            s["max_overlap_pairs"] = max(r["overlap_pairs"] for r in rs)
        out[m] = s
    return out


# -- B: completion experiments ------------------------------------------------------------

def random_removal(full: DecisionTable, name: str, levels, seeds: int, base_seed: int) -> dict:
    truth = {r.condition: r.outcome for r in full.rows}
    rng = random.Random(f"{base_seed}:{name}")
    out = {}
    n = len(full.rows)
    for level in levels:
        keep = max(1, round(level * n))
        runs, restores, unobserved = [], [], []
        for _ in range(seeds):
            idx = sorted(rng.sample(range(n), keep))
            t0 = full.with_rows([full.rows[i] for i in idx])
            res = run_methods(t0)
            runs.append(res)
            restores.append(restore_check(t0, exact_complement(t0), truth))
            obs = latc.observed_domains(t0)
            unobserved.append(sum(a.card - len(o) for a, o in zip(full.attributes, obs)))
        out[str(level)] = {"keep_share": level, "t0_rows": keep, "seeds": seeds,
                           "methods": _agg(runs),
                           "mean_unobserved_declared_values": mean(unobserved),
                           "runs_with_unobserved_value": sum(1 for u in unobserved if u),
                           "restore_ok": sum(r["sound"] and r["equals_full_table"] for r in restores),
                           "restore_runs": len(restores)}
        print(f"  {name} keep {level:>5}: T0 {keep:>6} | " + " | ".join(
            f"{m.split(' (')[0][:6]} {out[str(level)]['methods'][m]['exact_rate']:.2f}" for m in METHODS),
            flush=True)
    return out


def structured_removal(full: DecisionTable, name: str) -> dict:
    """Drop every row with value v of attribute j, for every (j, v)."""
    truth = {r.condition: r.outcome for r in full.rows}
    cases, runs = [], []
    for j, a in enumerate(full.attributes):
        for v in a.domain:
            t0 = full.with_rows([r for r in full.rows if r.condition[j] != v])
            res = run_methods(t0)
            rest = restore_check(t0, exact_complement(t0), truth)
            runs.append(res)
            cases.append({"attribute": a.name, "value": v, "t0_rows": len(t0.rows),
                          "missing": len(full.rows) - len(t0.rows),
                          "methods": {m: {k: res[m][k] for k in ("exact", "missed", "duplicates",
                                                                  "regenerated_t0", "outside_space",
                                                                  "n_candidate")}
                                      | ({"regions": res[m]["regions"]} if "regions" in res[m] else {})
                                      for m in METHODS},
                          "restore": rest})
    agg = _agg(runs)
    t0_rows = [c["t0_rows"] for c in cases]
    print(f"  {name} structured ({len(cases)} cases): " + " | ".join(
        f"{m.split(' (')[0][:6]} {agg[m]['exact_rate']:.2f}" for m in METHODS), flush=True)
    return {"cases": cases, "methods": agg, "t0_rows_min": min(t0_rows), "t0_rows_max": max(t0_rows),
            "restore_ok": sum(c["restore"]["sound"] and c["restore"]["equals_full_table"] for c in cases),
            "restore_runs": len(cases)}


# -- C: compact rules, faults, rank index ----------------------------------------------------

def _first_conflicting_widening(d: DMNTable):
    """First rule (in order) whose last non-'-' entry, widened to '-', creates a conflict."""
    for i, r in enumerate(d.rules):
        ks = [k for k, e in enumerate(r.entries) if e is not ANY]
        if not ks:
            continue
        k = ks[-1]
        rules = list(d.rules)
        rules[i] = Rule(r.entries[:k] + (ANY,) + r.entries[k + 1:], r.output)
        cand = DMNTable(d.inputs, rules, d.hit_policy, d.output_name, d.output_values)
        rep = structural_report(to_exact(cand)[0])
        if rep["conflicting_tuples"]:
            return i, k, cand
    return None


def _fault_report(d: DMNTable, faulty: DMNTable, desc: str) -> dict:
    t0 = time.perf_counter()
    a = analyse(faulty)
    v = violations(faulty, a)
    dmn_s = time.perf_counter() - t0
    gap_tuples, _ = expand(a.gaps, faulty.inputs)
    t0 = time.perf_counter()
    exact, _ = to_exact(faulty)
    rep = structural_report(exact)
    missing = exact_complement(exact)
    complete_s = time.perf_counter() - t0
    return {"fault": desc, "dmn_gap_regions": len(a.gaps), "dmn_gap_tuples": len(gap_tuples),
            "dmn_overlap_pairs": len(a.overlaps), "dmn_violating_pairs": len(v["violating_pairs"]),
            "dmn_maximal_overlap_sets": len(v["maximal_overlap_sets"]),
            "complete_uncovered": rep["uncovered"], "complete_multi_hit": rep["multi_hit_tuples"],
            "complete_conflicts": rep["conflicting_tuples"],
            "dmn_gaps_equal_complete_missing": sorted(gap_tuples) == sorted(missing),
            "dmn_detects": bool(a.gaps or v["violating_pairs"]),
            "complete_detects": not is_sound(rep),
            "dmn_ms": 1000 * dmn_s, "complete_ms": 1000 * complete_s}


def compact_rules(full: DecisionTable) -> dict:
    t0 = time.perf_counter()
    root = tree.id3(full)
    learn_s = time.perf_counter() - t0
    truth = {r.condition: r.outcome for r in full.rows}
    n_attr = len(full.attributes)
    out = {"tree": tree.stats(root), "learn_ms": 1000 * learn_s,
           "full_table": {"rules": len(full.rows), "non_wildcard_cells": len(full.rows) * n_attr,
                          "cells": len(full.rows) * (n_attr + 1)},
           "variants": {}}
    for label, merge in (("one rule per leaf", False), ("same-class leaves merged (OneOf)", True)):
        d = tree.to_dmn(root, full, merge_siblings=merge)
        t0 = time.perf_counter()
        a = analyse(d)
        v = violations(d, a)
        an_s = time.perf_counter() - t0
        exact, conv = to_exact(d)
        same = (len(exact.rows) == len(full.rows)
                and {r.condition: r.outcome for r in exact.rows} == truth)
        rep = structural_report(exact)
        kinds = Counter(type(e).__name__ if e is not ANY else "ANY" for r in d.rules for e in r.entries)
        faults = []
        cover = [len(_rule_tuples(d, i)) for i in range(len(d.rules))]
        big = max(range(len(d.rules)), key=lambda i: (cover[i], -i))
        small = min(range(len(d.rules)), key=lambda i: (cover[i], -i))
        for i, what in ((big, "largest"), (small, "smallest")):
            dropped = DMNTable(d.inputs, d.rules[:i] + d.rules[i + 1:], d.hit_policy, d.output_name,
                               d.output_values)
            f = _fault_report(d, dropped, f"drop rule {i} ({what}, covers {len(_rule_tuples(d, i))} tuples)")
            faults.append(f)
        w = _first_conflicting_widening(d)
        if w:
            i, k, cand = w
            faults.append(_fault_report(d, cand, f"widen rule {i}, input {d.inputs[k].name}, to '-'"))
        out["variants"][label] = {
            "review_size": d.review_size(), "entry_kinds": dict(kinds),
            "gap_regions": len(a.gaps), "overlap_pairs": len(a.overlaps),
            "violating_pairs": len(v["violating_pairs"]), "analysis_ms": 1000 * an_s,
            "expands_to_full_table": same, "structural_sound": is_sound(rep),
            "misaligned": len(conv["misaligned_entries"]),
            "faults": faults}
    return out


def _rule_tuples(d: DMNTable, i: int) -> list:
    return expand([tuple(_seg(inp, e) for inp, e in zip(d.inputs, d.rules[i].entries))], d.inputs)[0]


def _seg(inp: Input, e):
    from .dmn import entry_set
    return entry_set(inp, e)


def rank_check(full: DecisionTable) -> dict:
    t0 = time.perf_counter()
    ri = RankIndex.from_table(full)
    build = time.perf_counter() - t0
    t0 = time.perf_counter()
    d = {r.condition: r.outcome for r in full.rows}
    dict_build = time.perf_counter() - t0
    agree = sum(ri.lookup(c) == o for c, o in d.items())
    probes = list(d)
    lat = []
    for c in probes:
        s = time.perf_counter_ns()
        ri.lookup(c)
        lat.append(time.perf_counter_ns() - s)
    bad = tuple("<not a value>" for _ in full.attributes)
    meta = len(json.dumps({"attributes": [[a.name, list(a.domain)] for a in full.attributes],
                           "outcomes": list(full.outcomes)}))
    return {"rows": len(full.rows), "build_ms": 1000 * build, "dict_build_ms": 1000 * dict_build,
            "code_bytes": len(ri.codes), "metadata_bytes": meta,
            "lookups": len(d), "agree_with_dict": agree,
            "out_of_domain_probe_is_referral": ri.lookup(bad) is None,
            "lookup_median_us": median(lat) / 1000, "lookup_p99_us": sorted(lat)[int(0.99 * len(lat))] / 1000}


# -- D: DMN TCK ---------------------------------------------------------------------------

def _dom_str(inp: Input) -> str:
    if not inp.numeric:
        return "{" + ", ".join(map(str, inp.values)) + "}"
    d = inp.domain
    lo = "-inf" if d.lo == -math.inf else str(d.lo)
    hi = "inf" if d.hi == math.inf else str(d.hi)
    return f"{'[' if d.lo_closed and d.lo != -math.inf else '('}{lo}..{hi}{']' if d.hi_closed and d.hi != math.inf else ')'}"


def bounded_proxy(table: DMNTable):
    """Unbounded numeric inputs clipped to [min bound - 1, max bound + 1] (integers only).

    Every elementary cell of the sweep survives the clipping, so overlaps, masking
    and never-firing rules are the same as on the real domain; gap regions are
    the same up to the clipped ends.  Used only to run the oracle.
    """
    inputs = []
    for d, inp in enumerate(table.inputs):
        if not inp.numeric:
            inputs.append(inp)
            continue
        dom = inp.domain
        bounds = []
        for r in table.rules:
            e = r.entries[d]
            e = e.entry if isinstance(e, Not) else e
            if isinstance(e, Point):
                bounds.append(e.value)
            elif isinstance(e, Interval):
                bounds += [e.lo, e.hi]
        bounds = [b for b in bounds if math.isfinite(b)]
        if any(not float(b).is_integer() for b in bounds):
            return None
        lo = dom.lo if math.isfinite(dom.lo) else (min(bounds) - 1 if bounds else 0)
        hi = dom.hi if math.isfinite(dom.hi) else (max(bounds) + 1 if bounds else 0)
        if (math.isfinite(dom.lo) and not dom.lo_closed) or (math.isfinite(dom.hi) and not dom.hi_closed):
            return None
        if not (float(lo).is_integer() and float(hi).is_integer()):
            return None
        inputs.append(Input(inp.name, domain=closed(int(lo), int(hi))))
    return DMNTable(tuple(inputs), table.rules, table.hit_policy, table.output_name, table.output_values)


def _integer_free(region: tuple, inputs) -> bool:
    """A gap region holding no point with integer values on its numeric inputs (see D-1)."""
    for inp, seg in zip(inputs, region):
        if inp.numeric:
            lo = math.ceil(seg.lo) if math.isfinite(seg.lo) else -math.inf
            if lo == seg.lo and not seg.lo_closed:
                lo += 1
            hi = math.floor(seg.hi) if math.isfinite(seg.hi) else math.inf
            if hi == seg.hi and not seg.hi_closed:
                hi -= 1
            if lo > hi:
                return True
    return False


def analyse_imported(it) -> dict:
    d = it.dmn
    t0 = time.perf_counter()
    a = analyse(d)
    v = violations(d, a)
    secs = time.perf_counter() - t0
    res = {"file": it.file, "name": it.name, "hit_policy": it.hit_policy, "inputs": it.n_inputs,
           "rules": it.n_rules, "domains": [f"{i.name}: {_dom_str(i)}" for i in d.inputs],
           "domain_sources": it.domains,
           "gap_regions": len(a.gaps), "gap_regions_unmerged": a.raw_gaps,
           "gaps": [describe_region(g, d.inputs) for g in a.gaps[:12]],
           "overlapping_pairs": v["overlapping_pairs"],
           "pairs_with_different_outputs": v["pairs_with_different_outputs"],
           "maximal_overlap_sets": [list(s) for s in v["maximal_overlap_sets"]],
           "violating_pairs": [list(p) for p in v["violating_pairs"]],
           "masked_pairs": [list(p) for p in v["masked_pairs"]],
           "never_fire": v["never_fire"], "undeclared_values": len(a.undeclared),
           "integer_free_gap_regions": sum(1 for g in a.gaps if _integer_free(g, d.inputs)),
           "ms": 1000 * secs}
    ok, why = dmn_import.finite_for_oracle(d)
    target, mode = (d, "exact domain") if ok else (None, None)
    if not ok:
        p = bounded_proxy(d)
        if p is None:
            why += "; no integer proxy (non-integer bound or open finite domain)"
        else:
            ok2, why2 = dmn_import.finite_for_oracle(p)
            if ok2:
                target, mode, why = p, "bounded proxy", why + "; proxy " + why2
    if target is not None:
        diff = dmn_oracle.differential(target)
        res["oracle"] = {"mode": mode, "agree": all(diff.values()), "properties": diff, "note": why}
    else:
        res["oracle"] = {"mode": "not run", "note": why}
    return res


def tck(root_dir: str) -> dict:
    out = {"root": os.path.basename(os.path.normpath(root_dir))}
    for mode in ("skip", "enum"):
        imp = dmn_import.import_tree(root_dir, booleans=mode)
        ts = imp["tables"]
        parsed = [t for t in ts if t.status == "parsed"]
        out[f"booleans_{mode}"] = {
            "files": imp["files"], "files_with_tables": imp["files_with_tables"],
            "file_errors": imp["file_errors"], "tables": len(ts), "parsed": len(parsed),
            "skipped": len(ts) - len(parsed),
            "versions": dict(Counter(t.version for t in ts)),
            "skip_reasons": dict(Counter(t.reason for t in ts if t.status != "parsed").most_common()),
            "skipped_tables": [{"file": t.file, "name": t.name, "hit_policy": t.hit_policy,
                                "reason": t.reason, "all_reasons": t.reasons, "detail": t.detail}
                               for t in ts if t.status != "parsed"],
            "analysed": [analyse_imported(t) for t in parsed]}
    return out


# -- baselines ---------------------------------------------------------------------------------

def baselines(trials: int, seed: int) -> dict:
    out = {"pension": {}, "random": {}}
    t = ex.pension_table()
    res = run_methods(t)
    out["pension"] = {"states": t.valid_space_size(), "t0_rows": len(t.rows),
                      "domain_sizes": [a.card for a in t.attributes], "methods": _agg([res])}
    rng = random.Random(seed)
    for sc in randomized.SCENARIOS:
        runs, t0_rows, states, cards, attrs_n = [], [], [], [], []
        for _ in range(trials):
            case = randomized.generate_case(rng, sc)
            runs.append(run_methods(case, constraint_filter=False))
            t0_rows.append(len(case.rows))
            states.append(case.valid_space_size())
            attrs_n.append(len(case.attributes))
        out["random"][sc] = {"trials": trials, "mean_t0_rows": mean(t0_rows), "mean_states": mean(states),
                             "attributes": f"{min(attrs_n)}-{max(attrs_n)}", "methods": _agg(runs)}
    # consistency with the reference run in results/results.json
    ref_path = os.path.join(REPO, "results", "results.json")
    if os.path.exists(ref_path) and trials == 1000 and seed == 20210101:
        with open(ref_path, encoding="utf-8") as f:
            ref = json.load(f)
        pairs = {"COMPLETE": ("randomised", "reference"), "LATC A (deficit fill)": ("randomised", "latc_A_deficit_fill"),
                 "LATC B (odometer)": ("randomised", "latc_B_odometer"),
                 "DMN (declared values)": ("dmn", "dmn_declared_values"),
                 "DMN (observed values)": ("dmn", "dmn_observed_values")}
        check = {}
        for sc in randomized.SCENARIOS:
            for m, (src, key) in pairs.items():
                r = (ref["randomised"][sc][key] if src == "randomised"
                     else ref["dmn_baseline"]["random"][sc][key])
                mine = out["random"][sc]["methods"][m]
                check[f"{sc}/{m}"] = (abs(r["exact_rate"] - mine["exact_rate"]) < 1e-12
                                      and abs(r["mean_missed"] - mine["mean_missed"]) < 1e-9)
        out["matches_results_json"] = check
    return out


# -- output ------------------------------------------------------------------------------------

CSV_FIELDS = ["dataset", "experiment", "attributes", "domain_sizes", "states", "t0_rows", "method", "runs",
              "exact_rate", "mean_missed", "mean_duplicates", "mean_regenerated_t0", "mean_outside_space",
              "mean_missing_states", "mean_dmn_regions", "mean_ms"]


def _row(dataset, experiment, n_attr, sizes, states, t0_rows, m, s) -> dict:
    return {"dataset": dataset, "experiment": experiment, "attributes": n_attr, "domain_sizes": sizes,
            "states": states, "t0_rows": t0_rows, "method": m, "runs": s["runs"],
            "exact_rate": s["exact_rate"], "mean_missed": s["mean_missed"],
            "mean_duplicates": s["mean_duplicates"], "mean_regenerated_t0": s["mean_regenerated_t0"],
            "mean_outside_space": s["mean_outside_space"], "mean_missing_states": s["mean_expected_rows"],
            "mean_dmn_regions": s.get("mean_regions", ""), "mean_ms": s["mean_ms"]}


def summary_rows(results: dict) -> list[dict]:
    rows = []
    b = results.get("baselines")
    if b:
        p = b["pension"]
        for m in METHODS:
            rows.append(_row("pension (IJSER 2021)", "worked example", len(p["domain_sizes"]),
                             "x".join(map(str, p["domain_sizes"])), p["states"], p["t0_rows"], m, p["methods"][m]))
        for sc, r in b["random"].items():
            for m in METHODS:
                rows.append(_row("random (randomized.py)", f"scenario {sc}", r["attributes"], "2-4 values",
                                 f"{r['mean_states']:.2f} (mean)", f"{r['mean_t0_rows']:.2f} (mean)", m, r["methods"][m]))
    for key in ("car", "nursery"):
        d = results.get(key)
        if not d:
            continue
        v = d["verification"]
        sizes = "x".join(map(str, v["domain_sizes"]))
        for lv, r in d["random_removal"].items():
            for m in METHODS:
                rows.append(_row(d["title"], f"random keep {float(lv):.0%}", v["attributes"], sizes,
                                 v["states"], r["t0_rows"], m, r["methods"][m]))
        s = d["structured_removal"]
        for m in METHODS:
            rows.append(_row(d["title"], f"structured: one value removed ({s['restore_runs']} cases)",
                             v["attributes"], sizes, v["states"], f"{s['t0_rows_min']}-{s['t0_rows_max']}",
                             m, s["methods"][m]))
    return rows


def _f(x, nd=3) -> str:
    if x == "" or x is None:
        return "–"
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e15 and nd == 3:
            return f"{x:.3f}"
        return f"{x:.{nd}f}"
    return str(x)


def write_summary_md(results: dict, rows: list[dict], path: str) -> None:
    L = []
    w = L.append
    meta = results["meta"]
    w("# Public datasets: completion, DMN analysis and compact rules\n")
    w(f"Generated by `python run_datasets.py` (latc_check {meta['version']}, Python {meta['python']}, "
      f"{meta['platform']}). Base seed {meta['seed']}, {meta['seeds']} seeds per removal level. "
      "Everything except the times is determined by the seed. Times are wall-clock means per run "
      "and depend on the machine.\n")
    w("LendingClub was not used: it needs a Kaggle login.\n")
    w("## Data checks\n")
    w("| dataset | attributes | domain sizes | states | rows | full product | duplicate tuples | "
      "tuples with >1 class | blank lines | value spelling in .names vs data |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for key in ("car", "nursery"):
        d = results.get(key)
        if not d:
            continue
        v, i = d["verification"], d["file_info"]
        w(f"| {d['title']} | {v['attributes']} | {'x'.join(map(str, v['domain_sizes']))} | {v['states']} | "
          f"{v['rows']} | {v['full_product']} | {v['duplicate_condition_tuples']} | "
          f"{v['tuples_with_more_than_one_class']} | {i['blank_lines']} | "
          f"{'; '.join(i['names_spelling_differs']) or 'same'} |")
    w("")
    w("## Completion: one comparable table\n")
    w("`exact` = share of runs whose output equals the exact complement (as a set, no repeats). "
      "`missed` = complement rows not produced; `dup` = repeated output rows; `regen` = output rows "
      "already in T0; `outside` = output rows outside the declared space; `missing` = size of the "
      "exact complement; `regions` = merged DMN gap regions; time in ms per run. Means over runs.\n")
    w("| dataset | experiment | attributes | domain sizes | states | T0 rows | method | runs | exact rate | "
      "mean missed | duplicates | regen T0 | outside | missing | DMN regions | time (ms) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        w(f"| {r['dataset']} | {r['experiment']} | {r['attributes']} | {r['domain_sizes']} | {r['states']} | "
          f"{r['t0_rows']} | {r['method']} | {r['runs']} | {r['exact_rate']:.3f} | {r['mean_missed']:.2f} | "
          f"{r['mean_duplicates']:.2f} | {r['mean_regenerated_t0']:.2f} | {r['mean_outside_space']:.2f} | "
          f"{r['mean_missing_states']:.2f} | "
          f"{'–' if r['mean_dmn_regions'] == '' else format(r['mean_dmn_regions'], '.1f')} | {r['mean_ms']:.2f} |")
    w("")
    b = results.get("baselines")
    if b and "matches_results_json" in b:
        ok = all(b["matches_results_json"].values())
        w(f"The random-scenario rows reproduce `results/results.json` (exact rate and mean missed, "
          f"all 15 scenario/method pairs): {ok}. The pension DMN rows use point entries on the "
          "normalised labels (the README's B4.1 uses interval entries for Age and ContributionYears).\n")
    for key in ("car", "nursery"):
        d = results.get(key)
        if not d:
            continue
        w(f"### {d['title']}: restore check and unobserved values\n")
        rr = d["random_removal"]
        w("| T0 share | T0 rows | runs with an unobserved declared value | mean unobserved values | "
          "restore = full table and sound |")
        w("|---|---|---|---|---|")
        for lv, r in rr.items():
            w(f"| {float(lv):.0%} | {r['t0_rows']} | {r['runs_with_unobserved_value']}/{r['seeds']} | "
              f"{r['mean_unobserved_declared_values']:.2f} | {r['restore_ok']}/{r['restore_runs']} |")
        s = d["structured_removal"]
        w(f"| structured | {s['t0_rows_min']}-{s['t0_rows_max']} | {s['restore_runs']}/{s['restore_runs']} | 1.00 | "
          f"{s['restore_ok']}/{s['restore_runs']} |")
        w("")
        w("Structured removal, per removed value (missed rows; DMN regions for the declared-value variant):\n")
        w("| attribute = value | T0 rows | missing | COMPLETE | LATC A | LATC B | DMN declared (regions) | DMN observed |")
        w("|---|---|---|---|---|---|---|---|")
        for c in s["cases"]:
            ms = c["methods"]
            w(f"| {c['attribute']} = {c['value']} | {c['t0_rows']} | {c['missing']} | "
              f"{ms['COMPLETE']['missed']} | {ms['LATC A (deficit fill)']['missed']} | "
              f"{ms['LATC B (odometer)']['missed']} | {ms['DMN (declared values)']['missed']} "
              f"({ms['DMN (declared values)']['regions']}) | {ms['DMN (observed values)']['missed']} |")
        w("")
    w("## Compact rules from an ID3 tree\n")
    w("Rules are root-to-leaf paths of an ID3 tree over the full table (UNIQUE), with `-` for the "
      "attributes not on the path; the second variant merges same-class leaf siblings into one "
      "`OneOf` entry. `cells` counts inputs plus output per rule, as for the pension example.\n")
    w("| dataset | variant | rules | non-'-' input cells | cells | full table rows | full input cells | "
      "full cells | gaps | overlaps | expands exactly | analysis (ms) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for key in ("car", "nursery"):
        d = results.get(key)
        if not d:
            continue
        c = d["compact_rules"]
        for lab, v in c["variants"].items():
            rs = v["review_size"]
            w(f"| {d['title']} | {lab} | {rs['rules']} | {rs['non_wildcard_cells']} | {rs['cells']} | "
              f"{c['full_table']['rules']} | {c['full_table']['non_wildcard_cells']} | {c['full_table']['cells']} | "
              f"{v['gap_regions']} | {v['overlap_pairs']} | {v['expands_to_full_table']} | {v['analysis_ms']:.1f} |")
    w("")
    w("Seeded faults (DMN analysis of the faulty rules; COMPLETE's structural checks on the faulty rules "
      "expanded to exact tuples):\n")
    w("| dataset | variant | fault | DMN gap regions / tuples | DMN overlap pairs (UNIQUE violations) | "
      "COMPLETE uncovered | multi-hit | conflicts | DMN gaps = COMPLETE missing | detected by DMN / COMPLETE |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for key in ("car", "nursery"):
        d = results.get(key)
        if not d:
            continue
        for lab, v in d["compact_rules"]["variants"].items():
            for f in v["faults"]:
                w(f"| {d['title']} | {lab} | {f['fault']} | {f['dmn_gap_regions']} / {f['dmn_gap_tuples']} | "
                  f"{f['dmn_overlap_pairs']} ({f['dmn_violating_pairs']}) | {f['complete_uncovered']} | "
                  f"{f['complete_multi_hit']} | {f['complete_conflicts']} | {f['dmn_gaps_equal_complete_missing']} | "
                  f"{f['dmn_detects']} / {f['complete_detects']} |")
    w("")
    w("Rank index over the full tables:\n")
    w("| dataset | rows | build (ms) | dict build (ms) | code bytes | metadata bytes | lookups agreeing with dict | "
      "out-of-domain probe is referral | lookup median / p99 (µs) |")
    w("|---|---|---|---|---|---|---|---|---|")
    for key in ("car", "nursery"):
        d = results.get(key)
        if not d:
            continue
        r = d["rank_index"]
        w(f"| {d['title']} | {r['rows']} | {r['build_ms']:.2f} | {r['dict_build_ms']:.2f} | {r['code_bytes']} | "
          f"{r['metadata_bytes']} | {r['agree_with_dict']}/{r['lookups']} | {r['out_of_domain_probe_is_referral']} | "
          f"{r['lookup_median_us']:.2f} / {r['lookup_p99_us']:.2f} |")
    w("")
    t = results.get("tck")
    if t:
        _tck_md(t, w)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def _tck_md(t: dict, w) -> None:
    w("## DMN TCK decision tables\n")
    w("TCK tables test engines, not completeness: gaps and overlaps are often intended (for example, "
      "a FIRST or PRIORITY table relies on overlaps). They are reported, not judged. Domains follow "
      "`dmn_import` I-D1 to I-D3: a string input without declared values gets the sentinel `<other>`, "
      "a number without inputValues is unbounded, and numbers are real-valued (D-1), so a gap such as "
      "(9..10) counts even if the input only ever takes integers; the count in brackets is such "
      "integer-free regions. The oracle runs on the exact domain when it is finite, otherwise on a "
      "bounded integer proxy of the unbounded inputs (which keeps every elementary cell).\n")
    m, e = t["booleans_skip"], t["booleans_enum"]
    w(f"{m['files']} .dmn files, {m['files_with_tables']} with decision tables; {m['tables']} decision tables "
      f"(DMN versions: {m['versions']}). File-level errors: {m['file_errors'] or 'none'}.\n")
    w("| mode | parsed | skipped |")
    w("|---|---|---|")
    w(f"| booleans skipped (the modelled subset) | {m['parsed']} | {m['skipped']} |")
    w(f"| booleans as the enumeration (true, false) (sensitivity) | {e['parsed']} | {e['skipped']} |")
    w("")
    w("Skip reasons (first reason found per table):\n")
    w("| reason | booleans skipped | booleans as enumeration |")
    w("|---|---|---|")
    for r in sorted(set(m["skip_reasons"]) | set(e["skip_reasons"]), key=lambda r: -m["skip_reasons"].get(r, 0)):
        w(f"| {r} | {m['skip_reasons'].get(r, 0)} | {e['skip_reasons'].get(r, 0)} |")
    w("")
    for title, res in (("Parsed tables (booleans skipped)", m), ("Additional tables parsed when booleans are an enumeration", e)):
        rows = res["analysed"]
        if res is e:
            base = {(a["file"], a["name"]) for a in m["analysed"]}
            rows = [a for a in rows if (a["file"], a["name"]) not in base]
        w(f"### {title}\n")
        w("| file | table | hit policy | inputs | rules | domains | gap regions (with no integer point) | overlapping pairs | "
          "maximal overlap sets | violating (policy) | masked (FIRST/PRIORITY) | never fire | oracle | ms |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for a in rows:
            o = a["oracle"]
            orc = o["mode"] if o["mode"] == "not run" else f"{o['mode']}: {'agree' if o['agree'] else 'DISAGREE'}"
            w(f"| {a['file'].split('/')[-1]} | {a['name']} | {a['hit_policy']} | {a['inputs']} | {a['rules']} | "
              f"{'; '.join(a['domains'])} | {a['gap_regions']} ({a['integer_free_gap_regions']}) | {a['overlapping_pairs']} | "
              f"{a['maximal_overlap_sets'] or '–'} | {len(a['violating_pairs'])} | {a['masked_pairs'] or '–'} | "
              f"{a['never_fire'] or '–'} | {orc} | {a['ms']:.2f} |")
        w("")
        n_or = [a for a in rows if a["oracle"]["mode"] != "not run"]
        w(f"Oracle run on {len(n_or)} of {len(rows)} tables "
          f"({sum(a['oracle']['mode'] == 'exact domain' for a in n_or)} on the exact domain, "
          f"{sum(a['oracle']['mode'] == 'bounded proxy' for a in n_or)} on a bounded integer proxy); "
          f"agreement on every property: {sum(a['oracle']['agree'] for a in n_or)}/{len(n_or)}.\n")


def write_outputs(results: dict, out: str, start: float) -> None:
    rows = summary_rows(results)
    with open(os.path.join(out, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    results["meta"]["total_seconds"] = time.perf_counter() - start
    write_summary_md(results, rows, os.path.join(out, "SUMMARY.md"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seed", type=int, default=20210101)
    p.add_argument("--seeds", type=int, default=20, help="random T0 draws per removal level")
    p.add_argument("--levels", default=",".join(map(str, LEVELS)), help="T0 shares, comma-separated")
    p.add_argument("--datasets", default="car,nursery")
    p.add_argument("--trials", type=int, default=1000, help="random-scenario baseline tables per scenario")
    p.add_argument("--tck", default=os.environ.get("LATC_DMN_TCK", os.path.join(os.path.dirname(REPO), "dmn-tck")),
                   help="path of a clone of https://github.com/dmn-tck/tck")
    p.add_argument("--no-tck", action="store_true")
    p.add_argument("--no-baselines", action="store_true")
    p.add_argument("--data-dir", default=None)
    p.add_argument("--out", default=os.path.join("results", "datasets"))
    args = p.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    levels = [float(x) for x in args.levels.split(",") if x]
    start = time.perf_counter()
    results = {"meta": {"version": __version__, "python": platform.python_version(),
                        "platform": platform.platform(), "seed": args.seed, "seeds": args.seeds,
                        "levels": levels}}
    print(f"latc_check {__version__} | Python {platform.python_version()} | {platform.platform()}")
    for key in [k for k in args.datasets.split(",") if k]:
        full, info = datasets.load(key, args.data_dir)
        ver = datasets.verify(full)
        print(f"{info['title']}: {ver['rows']} rows, states {ver['states']}, full product {ver['full_product']}, "
              f"one class per tuple {ver['one_class_per_tuple']}", flush=True)
        d = {"title": info["title"], "file_info": info, "verification": ver}
        d["random_removal"] = random_removal(full, key, levels, args.seeds, args.seed)
        d["structured_removal"] = structured_removal(full, key)
        d["compact_rules"] = compact_rules(full)
        d["rank_index"] = rank_check(full)
        results[key] = d
        with open(os.path.join(args.out, f"uci_{key}.json"), "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, default=str)
    results["meta"]["partial"] = True
    write_outputs(results, args.out, start)      # UCI results first, before the slower parts
    if not args.no_baselines:
        print("baselines ...", flush=True)
        results["baselines"] = baselines(args.trials, args.seed)
        with open(os.path.join(args.out, "baselines.json"), "w", encoding="utf-8") as f:
            json.dump(results["baselines"], f, indent=2, default=str)
        write_outputs(results, args.out, start)
    if not args.no_tck:
        if os.path.isdir(args.tck):
            print("DMN TCK ...", flush=True)
            results["tck"] = tck(args.tck)
            with open(os.path.join(args.out, "dmn_tck.json"), "w", encoding="utf-8") as f:
                json.dump(results["tck"], f, indent=2, default=str)
        else:
            print(f"DMN TCK not found at {args.tck}; skipped (use --tck PATH).")
    results["meta"]["partial"] = False
    write_outputs(results, args.out, start)
    print(f"wrote {args.out} in {results['meta']['total_seconds']:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
