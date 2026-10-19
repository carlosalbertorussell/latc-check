"""Three more complete UCI decision tables: Lenses, Balance Scale, MONK's problems.

Each is a full Cartesian product of its declared attribute values with one
class per state, like Car Evaluation and Nursery (``datasets``):

* Lenses (Cendrowska 1987): 3 x 2 x 2 x 2 = 24 states, an expert table;
* Balance Scale (Siegler 1976, donated by T. Hume): 5^4 = 625 states, the class
  given by a rule (compare left weight x distance with right weight x distance);
* MONK's problems (Thrun et al. 1991): 3 x 3 x 2 x 3 x 4 x 2 = 432 states and
  three rule-defined targets on the same inputs.  The ``monks-N.test`` files
  contain the whole space; the ``.train`` files are subsets (124, 169, 122
  rows), and only ``monks-3.train`` has class noise (the .names file: "5% class
  noise added to the training set").  The loaders read the ``.test`` files.

Declared domains.  None of the three ships a ``.c45-names`` file; the only
description is the prose ``.names`` file.  The loaders parse the value lists
under "7. Attribute Information" (as data, nothing is executed), check the
stated value count where the file gives one (Balance Scale: "5 (1, 2, 3, 4,
5)"), and keep the codes exactly as the ``.data`` files spell them (Lenses
uses numeric codes; their labels are kept in ``file_info["value_labels"]``).

The experiments are those of ``datasets_report`` (random and structured
removal, COMPLETE, LATC Readings A and B, DMN gap analysis with declared and
observed values, restore check), with the same seed scheme, plus the
Corollary 3 / Corollary 1 view: LATC's missing count  prod Card(Ai) - q(T0)
on the observed cardinalities, and whether it is 0, i.e. LATC declares T0
complete.  ``random_removal`` draws exactly the T0s that
``datasets_report.random_removal`` draws for the same name and seed.
"""

from __future__ import annotations

import os
import random
import re
from collections import Counter
from math import prod
from statistics import mean

from . import latc
from .datasets import DATA_DIR, verify
from .datasets_report import METHODS, _agg, restore_check, run_methods
from .model import Attribute, DecisionTable, Row
from .reference import exact_complement

UCI = "https://archive.ics.uci.edu/dataset/"
DATASETS = {
    "lenses": {"dir": "lenses", "data": "lenses.data", "names": "lenses.names", "title": "UCI Lenses",
               "url": UCI + "58/lenses"},
    "balance": {"dir": "balance-scale", "data": "balance-scale.data", "names": "balance-scale.names",
                "title": "UCI Balance Scale", "url": UCI + "12/balance+scale"},
    **{f"monks{p}": {"dir": "monks", "data": f"monks-{p}.test", "train": f"monks-{p}.train",
                     "names": "monks.names", "title": f"UCI MONK's problem {p}", "problem": p,
                     "url": UCI + "70/monk+s+problems"} for p in (1, 2, 3)},
}
SPACES = {"lenses": ("lenses",), "balance": ("balance",), "monks": ("monks1", "monks2", "monks3")}

_VALUE = re.compile(r"^[A-Za-z0-9_.\-]+$")


# -- description files ------------------------------------------------------------------

def _section7(text: str) -> list[str]:
    out, inside = [], False
    for ln in text.splitlines():
        if re.match(r"^\s*7\.\s*Attribute info", ln, re.I):
            inside = True
            continue
        if inside and re.match(r"^\s*8\.", ln):
            break
        if inside:
            out.append(ln)
    if not out:
        raise ValueError("no '7. Attribute Information' section")
    return out


def _check_values(vals) -> tuple:
    vals = tuple(vals)
    if not vals or not all(_VALUE.match(v) for v in vals) or len(set(vals)) != len(vals):
        raise ValueError(f"unexpected values {vals!r}")
    return vals


def parse_lenses_names(text: str) -> dict:
    """Classes and attributes of lenses.names: '1. age of the patient: (1) young, ...'."""
    classes, attrs, labels = [], [], {}
    for ln in _section7(text):
        m = re.match(r"^\s*(\d+)\s*:\s*(.+?),?\s*$", ln)
        if m and not attrs:
            classes.append((m.group(1), m.group(2)))
            continue
        m = re.match(r"^\s*\d+\.\s*([A-Za-z ]+?):\s*(\(\d+\).*)$", ln)
        if m:
            name = m.group(1).strip().replace(" ", "_")
            pairs = re.findall(r"\((\d+)\)\s*([^,(]+)", m.group(2))
            attrs.append((name, _check_values(c for c, _ in pairs)))
            labels[name] = {c: lab.strip() for c, lab in pairs}
    return {"classes": _check_values(c for c, _ in classes), "attributes": attrs,
            "value_labels": labels, "class_labels": {c: lab.rstrip(".") for c, lab in classes}}


def parse_balance_names(text: str) -> dict:
    """'1. Class Name: 3 (L, B, R)', '2. Left-Weight: 5 (1, 2, 3, 4, 5)'."""
    classes, attrs, counts_ok = None, [], True
    for ln in _section7(text):
        m = re.match(r"^\s*\d+\.\s*([A-Za-z\- ]+?):\s*(\d+)\s*\((.+)\)\s*$", ln)
        if not m:
            continue
        vals = _check_values(v.strip() for v in m.group(3).split(","))
        counts_ok &= int(m.group(2)) == len(vals)
        if m.group(1).strip() == "Class Name":
            classes = vals
        else:
            attrs.append((m.group(1).strip().replace("-", "_"), vals))
    if classes is None:
        raise ValueError("no class line")
    return {"classes": classes, "attributes": attrs, "stated_counts_match": counts_ok}


def parse_monks_names(text: str) -> dict:
    """'1. class: 0, 1', '2. a1:    1, 2, 3', ...; the Id line is not an attribute."""
    classes, attrs = None, []
    for ln in _section7(text):
        m = re.match(r"^\s*\d+\.\s*(\w+):\s*(.+?)\s*$", ln)
        if not m or m.group(1) == "Id":
            continue
        vals = _check_values(v.strip() for v in m.group(2).split(","))
        if m.group(1) == "class":
            classes = vals
        else:
            attrs.append((m.group(1), vals))
    if classes is None:
        raise ValueError("no class line")
    return {"classes": classes, "attributes": attrs}


def stated_class_counts(text: str, key: str) -> dict | None:
    """Class distribution as stated in the .names file (None if it gives none)."""
    if key == "lenses":
        m = re.findall(r"^\s*(\d)\.\s*(?:hard|soft|no) contact lenses:\s*(\d+)", text, re.M)
        return {c: int(n) for c, n in m} or None
    if key == "balance":
        m = re.search(r"Number of Instances:\s*\d+\s*\((\d+) balanced, (\d+) left, (\d+) right\)", text)
        return {"B": int(m.group(1)), "L": int(m.group(2)), "R": int(m.group(3))} if m else None
    return None


# -- rules that generated the classes (from the .names files) ----------------------------

def balance_rule(c) -> str:
    lw, ld, rw, rd = map(int, c)
    return "L" if lw * ld > rw * rd else "R" if lw * ld < rw * rd else "B"


MONK_TARGETS = {   # monks.names, section 9
    1: lambda a: a[0] == a[1] or a[4] == 1,
    2: lambda a: sum(x == 1 for x in a) == 2,
    3: lambda a: (a[4] == 3 and a[3] == 1) or (a[4] != 4 and a[1] != 3),
}


def monk_rule(problem: int, c) -> str:
    return str(int(MONK_TARGETS[problem](tuple(map(int, c)))))


# -- data files --------------------------------------------------------------------------

def _read_rows(path: str, key: str, n_attr: int):
    rows, ids, blank, bad = [], [], 0, []
    with open(path, encoding="ascii", newline="") as f:
        for k, ln in enumerate(f, 1):
            ln = ln.strip()
            if not ln:
                blank += 1
                continue
            if key == "balance":
                p = ln.split(",")
                ok = len(p) == n_attr + 1
                cls, cond, ident = (p[0], tuple(p[1:]), None) if ok else (None, None, None)
            else:
                p = ln.split()
                ok = len(p) == n_attr + 2
                if key == "lenses":     # id, attributes, class
                    cls, cond, ident = (p[-1], tuple(p[1:-1]), p[0]) if ok else (None, None, None)
                else:                   # MONK's: class, attributes, id
                    cls, cond, ident = (p[0], tuple(p[1:-1]), p[-1]) if ok else (None, None, None)
            if not ok:
                bad.append(k)
                continue
            rows.append(Row(cond, cls))
            ids.append(ident)
    return rows, ids, blank, bad


def load(key: str, data_dir: str | None = None) -> tuple[DecisionTable, dict]:
    """Return (DecisionTable of every row with its class, file info)."""
    spec = DATASETS[key]
    base = os.path.join(data_dir or DATA_DIR, spec["dir"])
    with open(os.path.join(base, spec["names"]), encoding="latin-1") as f:
        text = f.read()
    kind = "monks" if key.startswith("monks") else key
    desc = {"lenses": parse_lenses_names, "balance": parse_balance_names, "monks": parse_monks_names}[kind](text)
    attributes = tuple(Attribute(n, v) for n, v in desc["attributes"])
    rows, ids, blank, bad = _read_rows(os.path.join(base, spec["data"]), kind, len(attributes))
    table = DecisionTable(attributes, rows, outcomes=desc["classes"])
    info = {"dataset": key, "title": spec["title"], "url": spec["url"], "data_file": spec["data"],
            "names_file": spec["names"], "domains_from": f"{spec['names']} section 7 (no .c45-names file exists)",
            "blank_lines": blank, "malformed_lines": bad,
            "domains": {a.name: list(a.domain) for a in attributes}, "classes": list(desc["classes"])}
    for k in ("value_labels", "class_labels", "stated_counts_match"):
        if k in desc:
            info[k] = desc[k]
    stated = stated_class_counts(text, kind)
    if stated is not None:
        info["stated_class_counts"] = stated
        info["stated_class_counts_match"] = stated == dict(Counter(r.outcome for r in rows))
    if kind == "lenses":
        info["ids_are_line_order"] = ids == [str(i) for i in range(1, len(ids) + 1)]
    if kind == "balance":
        info["rows_disagreeing_with_rule"] = sum(balance_rule(r.condition) != r.outcome for r in rows)
    if kind == "monks":
        p = spec["problem"]
        info["problem"] = p
        info["ids_unique"] = len(set(ids)) == len(ids)
        info["rows_disagreeing_with_target"] = sum(monk_rule(p, r.condition) != r.outcome for r in rows)
        info["train"] = train_check(key, table, data_dir)
    return table, info


def train_check(key: str, full: DecisionTable, data_dir: str | None = None) -> dict:
    """The .train file against the .test file (the full space) and the target rule."""
    spec = DATASETS[key]
    path = os.path.join(data_dir or DATA_DIR, spec["dir"], spec["train"])
    rows, ids, blank, bad = _read_rows(path, "monks", len(full.attributes))
    truth = {r.condition: r.outcome for r in full.rows}
    conds = Counter(r.condition for r in rows)
    disagree = [i for i, r in zip(ids, rows) if truth.get(r.condition) != r.outcome]
    return {"file": spec["train"], "rows": len(rows), "distinct_conditions": len(conds),
            "duplicate_conditions": sum(n - 1 for n in conds.values() if n > 1),
            "all_in_test": all(c in truth for c in conds), "blank_lines": blank, "malformed_lines": bad,
            "labels_differing_from_test": len(disagree), "differing_ids": disagree,
            "labels_differing_from_target": sum(monk_rule(spec["problem"], r.condition) != r.outcome
                                                for r in rows)}


# -- experiments: the datasets_report experiments plus the Corollary 3 / 1 view -------------

def latc_view(t0: DecisionTable, n_states: int) -> dict:
    """LATC's own count on the observed cardinalities (Corollary 3) against the truth."""
    observed_product = latc.product_of_cards(t0)
    cor3 = observed_product - len(t0.rows)
    true_missing = n_states - len(set(t0.conditions()))
    return {"corollary3_count": cor3, "true_missing": true_missing,
            "corollary3_correct": cor3 == true_missing,
            "declares_complete": cor3 == 0,          # Corollary 1: q(T0) = prod Card(Ai)
            "states_outside_observed_product": n_states - observed_product,
            "unobserved_declared_values": sum(a.card - len(o) for a, o in
                                              zip(t0.attributes, latc.observed_domains(t0)))}


def agg_view(views: list[dict]) -> dict:
    dc = [v for v in views if v["declares_complete"]]
    return {"runs": len(views),
            "corollary3_correct": sum(v["corollary3_correct"] for v in views),
            "declares_complete": len(dc),
            "declares_complete_while_incomplete": sum(v["true_missing"] > 0 for v in dc),
            "mean_states_missed_when_declared_complete": mean(v["true_missing"] for v in dc) if dc else None,
            "max_states_missed_when_declared_complete": max(v["true_missing"] for v in dc) if dc else None,
            "runs_with_unobserved_value": sum(v["unobserved_declared_values"] > 0 for v in views),
            "mean_states_outside_observed_product": mean(v["states_outside_observed_product"] for v in views)}


def keep_count(level: float, n: int) -> int:
    """T0 size for a keep share: max(1, round(level * n)) as in datasets_report (round half to even)."""
    return max(1, round(level * n))


def draw_t0s(full: DecisionTable, name: str, levels, seeds: int, base_seed: int):
    """Yield (level, keep, T0) in exactly the order and with exactly the draws of
    ``datasets_report.random_removal``."""
    rng = random.Random(f"{base_seed}:{name}")
    n = len(full.rows)
    for level in levels:
        keep = keep_count(level, n)
        for _ in range(seeds):
            idx = sorted(rng.sample(range(n), keep))
            yield level, keep, full.with_rows([full.rows[i] for i in idx])


def random_removal(full: DecisionTable, name: str, levels, seeds: int, base_seed: int,
                   methods: bool = True) -> dict:
    """datasets_report.random_removal plus the LATC view.  ``methods=False`` skips the
    completion methods (used to add the LATC view to the stored Car / Nursery runs)."""
    truth = {r.condition: r.outcome for r in full.rows}
    n_states = prod(a.card for a in full.attributes)
    per = {}
    for level, keep, t0 in draw_t0s(full, name, levels, seeds, base_seed):
        d = per.setdefault(str(level), {"keep_share": level, "t0_rows": keep, "seeds": seeds,
                                        "_runs": [], "_restores": [], "_views": []})
        if methods:
            d["_runs"].append(run_methods(t0))
            d["_restores"].append(restore_check(t0, exact_complement(t0), truth))
        d["_views"].append(latc_view(t0, n_states))
    out = {}
    for lv, d in per.items():
        views = d.pop("_views")
        runs, restores = d.pop("_runs"), d.pop("_restores")
        r = dict(d)
        if methods:
            r["methods"] = _agg(runs)
            r["restore_ok"] = sum(x["sound"] and x["equals_full_table"] for x in restores)
            r["restore_runs"] = len(restores)
        r["mean_unobserved_declared_values"] = mean(v["unobserved_declared_values"] for v in views)
        r["runs_with_unobserved_value"] = sum(1 for v in views if v["unobserved_declared_values"])
        r["latc"] = agg_view(views)
        out[lv] = r
        if methods:
            print(f"  {name} keep {float(lv):>5}: T0 {r['t0_rows']:>6} | " + " | ".join(
                f"{m.split(' (')[0][:6]} {r['methods'][m]['exact_rate']:.2f}" for m in METHODS)
                + f" | LATC says complete {r['latc']['declares_complete']}/{seeds}", flush=True)
    return out


def structured_removal(full: DecisionTable, name: str) -> dict:
    """datasets_report.structured_removal plus the LATC view."""
    truth = {r.condition: r.outcome for r in full.rows}
    n_states = prod(a.card for a in full.attributes)
    cases, runs, views = [], [], []
    for j, a in enumerate(full.attributes):
        for v in a.domain:
            t0 = full.with_rows([r for r in full.rows if r.condition[j] != v])
            res = run_methods(t0)
            rest = restore_check(t0, exact_complement(t0), truth)
            view = latc_view(t0, n_states)
            runs.append(res)
            views.append(view)
            cases.append({"attribute": a.name, "value": v, "t0_rows": len(t0.rows),
                          "missing": len(full.rows) - len(t0.rows),
                          "methods": {m: {k: res[m][k] for k in ("exact", "missed", "duplicates",
                                                                  "regenerated_t0", "outside_space",
                                                                  "n_candidate")}
                                      | ({"regions": res[m]["regions"]} if "regions" in res[m] else {})
                                      for m in METHODS},
                          "restore": rest, "latc": view})
    agg = _agg(runs)
    t0_rows = [c["t0_rows"] for c in cases]
    out = {"cases": cases, "methods": agg, "t0_rows_min": min(t0_rows), "t0_rows_max": max(t0_rows),
           "restore_ok": sum(c["restore"]["sound"] and c["restore"]["equals_full_table"] for c in cases),
           "restore_runs": len(cases), "latc": agg_view(views)}
    print(f"  {name} structured ({len(cases)} cases): " + " | ".join(
        f"{m.split(' (')[0][:6]} {agg[m]['exact_rate']:.2f}" for m in METHODS)
        + f" | LATC says complete {out['latc']['declares_complete']}/{len(cases)}", flush=True)
    return out


def structured_view(full: DecisionTable) -> dict:
    """LATC view of the structured removals only (no methods); for the stored Car / Nursery runs."""
    n_states = prod(a.card for a in full.attributes)
    views = []
    for j, a in enumerate(full.attributes):
        for v in a.domain:
            views.append(latc_view(full.with_rows([r for r in full.rows if r.condition[j] != v]), n_states))
    return agg_view(views)


# -- trap probabilities (trap_frequency) ---------------------------------------------------

TRAP_KS = (5, 8, 10, 17, 20, 30)


def trap_table(domains, ks=TRAP_KS, extra_ks=()) -> dict:
    """Exact P(trap | k) and E[missing | trap] for a uniform k-subset of the product."""
    from . import trap_frequency as tf
    n_states = prod(domains)
    coef = tf.avoid_coefficients(domains)
    rows = {}
    for k in sorted({k for k in tuple(ks) + tuple(extra_ks) if 1 <= k <= n_states}):
        p = tf.p_trap_exact(domains, k, coef)
        m = tf.expected_missing_exact(domains, k)
        rows[str(k)] = {"p_trap": float(p), "p_trap_fraction": f"{p.numerator}/{p.denominator}",
                        "expected_missing": float(m), "expected_missing_given_trap": float(m / p) if p else None}
    th = tf.thresholds_exact(domains)
    return {"domains": list(domains), "states": n_states, "declared_values": sum(domains),
            "ks": [k for k in ks if k <= n_states], "by_k": rows,
            "smallest_k": {a: v["exact_without_replacement"] for a, v in th.items()},
            "thresholds": th}


# -- runner ----------------------------------------------------------------------------------

def _stored(key: str, path: str):
    import json
    p = os.path.join(path, f"uci_{key}.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def comparison(key: str, stored: dict, levels, seeds: int, seed: int, data_dir: str | None = None) -> dict:
    """Car / Nursery: rates from results/datasets, LATC view recomputed on the same T0 draws."""
    from . import datasets
    full = datasets.load(key, data_dir)[0]
    view = random_removal(full, key, levels, seeds, seed, methods=False)
    st = stored["random_removal"]
    same = all(lv in st
               and view[lv]["t0_rows"] == st[lv]["t0_rows"]
               and view[lv]["runs_with_unobserved_value"] == st[lv]["runs_with_unobserved_value"]
               and abs(view[lv]["mean_unobserved_declared_values"] - st[lv]["mean_unobserved_declared_values"]) < 1e-12
               for lv in view)
    return {"title": stored["title"], "verification": stored["verification"],
            "random_removal": {lv: {**st[lv], "latc": view[lv]["latc"]} for lv in view if lv in st},
            "structured_removal": {**{k: v for k, v in stored["structured_removal"].items() if k != "cases"},
                                   "latc": structured_view(full)},
            "draws_reproduce_stored_runs": same, "source": f"results/datasets/uci_{key}.json"}


def main(argv=None) -> int:
    import argparse
    import json
    import platform
    import time
    from . import __version__
    from .datasets_report import LEVELS, REPO
    p = argparse.ArgumentParser(description="Lenses, Balance Scale and MONK's: the public-dataset experiments.")
    p.add_argument("--seed", type=int, default=20210101)
    p.add_argument("--seeds", type=int, default=20)
    p.add_argument("--levels", default=",".join(map(str, LEVELS)))
    p.add_argument("--datasets", default=",".join(DATASETS))
    p.add_argument("--data-dir", default=None)
    p.add_argument("--compare", default=os.path.join(REPO, "results", "datasets"),
                   help="directory with the Car / Nursery results (uci_car.json, uci_nursery.json)")
    p.add_argument("--out", default=os.path.join(REPO, "results", "datasets_more"))
    args = p.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    levels = [float(x) for x in args.levels.split(",") if x]
    start = time.perf_counter()
    res = {"meta": {"version": __version__, "python": platform.python_version(), "platform": platform.platform(),
                    "seed": args.seed, "seeds": args.seeds, "levels": levels,
                    "keep_rule": "T0 rows = max(1, round(share x rows)) with Python's round (half to even), "
                                 "as in datasets_report.random_removal"},
           "datasets": {}, "comparison": {}, "trap": {}}
    print(f"latc_check {__version__} | Python {platform.python_version()} | {platform.platform()}")
    for key in [k for k in args.datasets.split(",") if k]:
        full, info = load(key, args.data_dir)
        ver = verify(full)
        print(f"{info['title']}: {ver['rows']} rows, states {ver['states']}, full product {ver['full_product']}, "
              f"one class per tuple {ver['one_class_per_tuple']}", flush=True)
        d = {"title": info["title"], "file_info": info, "verification": ver}
        d["random_removal"] = random_removal(full, key, levels, args.seeds, args.seed)
        d["structured_removal"] = structured_removal(full, key)
        res["datasets"][key] = d
    for key in ("car", "nursery"):
        st = _stored(key, args.compare)
        if st is not None:
            print(f"{st['title']}: LATC view on the stored T0 draws ...", flush=True)
            res["comparison"][key] = comparison(key, st, levels, args.seeds, args.seed, args.data_dir)
    spaces = {}
    for key, d in res["datasets"].items():
        sp = "monks" if key.startswith("monks") else key
        title = "UCI MONK's problems" if sp == "monks" else d["title"]
        spaces.setdefault(sp, (title, d["verification"]["domain_sizes"], d["random_removal"]))
    for key, d in res["comparison"].items():
        spaces[key] = (d["title"], d["verification"]["domain_sizes"], d["random_removal"])
    for sp, (title, doms, rr) in spaces.items():
        t = trap_table(doms, extra_ks=[r["t0_rows"] for r in rr.values()])
        t["title"] = title
        t["experiment_levels"] = {lv: {"t0_rows": r["t0_rows"], "p_trap": t["by_k"][str(r["t0_rows"])]["p_trap"],
                                       "expected_runs": r["seeds"] * t["by_k"][str(r["t0_rows"])]["p_trap"],
                                       "observed_runs": r["runs_with_unobserved_value"], "seeds": r["seeds"]}
                                  for lv, r in rr.items()}
        res["trap"][sp] = t
    res["meta"]["total_seconds"] = time.perf_counter() - start
    with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    with open(os.path.join(args.out, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write(summary_md(res))
    print(f"wrote {args.out} in {res['meta']['total_seconds']:.1f} s")
    return 0


# -- SUMMARY.md --------------------------------------------------------------------------------

def _m(x, nd=2) -> str:
    return "–" if x is None else f"{x:.{nd}f}"


def _fmt_p(p: float) -> str:
    if p == 0:
        return "0"
    if p >= 1e-3:
        return f"{p:.4f}"
    return f"{p:.2e}"


def summary_md(res: dict) -> str:
    from .datasets_report import _row
    L = []
    w = L.append
    meta = res["meta"]
    w("# More public datasets: Lenses, Balance Scale, MONK's\n")
    w(f"Generated by `python run_datasets_more.py` (latc_check {meta['version']}, Python {meta['python']}, "
      f"{meta['platform']}). Base seed {meta['seed']}, {meta['seeds']} seeds per removal level, with the seed "
      "scheme of `datasets_report.random_removal` (`random.Random(f\"{seed}:{dataset key}\")`, one `sample` "
      "per run, levels in order). Everything except the times is determined by the seed. Times are "
      "wall-clock means per run and depend on the machine.\n")
    w(f"T0 size: {meta['keep_rule']}. For Lenses (24 rows) this gives 22, 18, 12, 6, 2 and 1 rows for "
      "90/75/50/25/10/1 %: 1 % of 24 is 0.24, which rounds to 0 and is raised to the minimum of 1 row. "
      "Rounding half to even matters for Balance Scale: 90 % = 562.5 -> 562, 50 % = 312.5 -> 312, "
      "10 % = 62.5 -> 62.\n")
    w("The three MONK's problems share one input space and the completion methods never read the class, so "
      "their completion results differ only through the T0 draws (each problem has its own seed stream, "
      "`monks1`, `monks2`, `monks3`); the structured cases are identical across the three.\n")
    w("## Data checks\n")
    w("Domains are read from section 7 of each prose `.names` file (none of the three datasets has a "
      "`.c45-names` file); values are kept exactly as the `.data` files spell them. MONK's tables are read "
      "from the `.test` files, which hold the full space.\n")
    w("| dataset | data file | attributes | domain sizes | states | rows | full product | duplicate tuples | "
      "tuples with >1 class | blank lines | classes (counts) | other checks |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for key, d in res["datasets"].items():
        v, i = d["verification"], d["file_info"]
        other = []
        if "stated_class_counts_match" in i:
            other.append(f"class counts = .names: {i['stated_class_counts_match']}")
        if "stated_counts_match" in i:
            other.append(f"stated value counts match: {i['stated_counts_match']}")
        if "rows_disagreeing_with_rule" in i:
            other.append(f"rows disagreeing with the weight x distance rule: {i['rows_disagreeing_with_rule']}")
        if "rows_disagreeing_with_target" in i:
            tr = i["train"]
            other.append(f"rows disagreeing with the target concept: {i['rows_disagreeing_with_target']}; "
                         f"{tr['file']}: {tr['rows']} rows, all in .test: {tr['all_in_test']}, labels differing "
                         f"from .test: {tr['labels_differing_from_test']}"
                         + (f" ({', '.join(tr['differing_ids'])})" if tr["differing_ids"] else ""))
        cls = ", ".join(f"{c}: {v['class_counts'].get(c, 0)}" for c in i["classes"])
        w(f"| {d['title']} | {i['data_file']} | {v['attributes']} | {'x'.join(map(str, v['domain_sizes']))} | "
          f"{v['states']} | {v['rows']} | {v['full_product']} | {v['duplicate_condition_tuples']} | "
          f"{v['tuples_with_more_than_one_class']} | {i['blank_lines']} | {cls} | {'; '.join(other) or '–'} |")
    w("")
    lab = res["datasets"].get("lenses", {}).get("file_info", {})
    if lab:
        w("Lenses codes (from `lenses.names`): " + "; ".join(
            f"{a} " + ", ".join(f"{c} = {t}" for c, t in m.items()) for a, m in lab["value_labels"].items())
          + "; class " + "; ".join(f"{c} = {t}" for c, t in lab["class_labels"].items()) + ".\n")
    w("## Completion: one comparable table\n")
    w("Exact rate = share of runs whose output equals the exact complement. `Cor. 3 right` = runs in which "
      "LATC's missing count on the observed cardinalities (Corollary 3, prod Card(Ai) - q(T0)) equals the true "
      "number of missing states. `LATC says complete` = runs in which that count is 0, so that by Corollary 1 "
      "LATC declares T0 complete (Reading B then outputs nothing); `missed then` = mean number of states "
      "actually missing in those runs. Car and Nursery rates are copied from `results/datasets/uci_*.json`; "
      "their LATC columns are recomputed here on the same T0 draws.\n")
    w("| dataset | experiment | T0 rows | runs | COMPLETE | Reading A | Reading B | DMN declared | DMN observed | "
      "Cor. 3 right | LATC says complete | missed then (mean) | restore = full table |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    groups = [d for d in res["datasets"].values()] + [d for d in res["comparison"].values()]
    for d in groups:
        rr, s = d["random_removal"], d["structured_removal"]
        items = [(f"random keep {float(lv):.0%}", str(r["t0_rows"]), r) for lv, r in rr.items()]
        items.append((f"structured ({s['restore_runs']} cases)", f"{s['t0_rows_min']}-{s['t0_rows_max']}", s))
        for exp, t0r, r in items:
            m, lt = r["methods"], r["latc"]
            n = m["COMPLETE"]["runs"]
            w(f"| {d['title']} | {exp} | {t0r} | {n} | " + " | ".join(f"{m[x]['exact_rate']:.3f}" for x in METHODS)
              + f" | {lt['corollary3_correct']}/{n} | {lt['declares_complete']}/{n} | "
              f"{_m(lt['mean_states_missed_when_declared_complete'], 1)} | {r['restore_ok']}/{r['restore_runs']} |")
    w("")
    for key, d in res["comparison"].items():
        w(f"{d['title']}: the redrawn T0s reproduce the stored runs (T0 size, runs with an unobserved value and "
          f"mean unobserved values at every level): {d['draws_reproduce_stored_runs']}.\n")
    w("## Full metrics (same columns as `results/datasets/SUMMARY.md`)\n")
    w("`missed` = complement rows not produced; `dup` = repeated output rows; `regen` = output rows already in "
      "T0; `outside` = output rows outside the declared space; `missing` = size of the exact complement; "
      "`regions` = merged DMN gap regions; time in ms per run. Means over runs.\n")
    w("| dataset | experiment | attributes | domain sizes | states | T0 rows | method | runs | exact rate | "
      "mean missed | duplicates | regen T0 | outside | missing | DMN regions | time (ms) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for key, d in res["datasets"].items():
        v = d["verification"]
        sizes = "x".join(map(str, v["domain_sizes"]))
        rows = []
        for lv, r in d["random_removal"].items():
            rows += [_row(d["title"], f"random keep {float(lv):.0%}", v["attributes"], sizes, v["states"],
                          r["t0_rows"], m, r["methods"][m]) for m in METHODS]
        s = d["structured_removal"]
        rows += [_row(d["title"], f"structured: one value removed ({s['restore_runs']} cases)", v["attributes"],
                      sizes, v["states"], f"{s['t0_rows_min']}-{s['t0_rows_max']}", m, s["methods"][m])
                 for m in METHODS]
        for r in rows:
            w(f"| {r['dataset']} | {r['experiment']} | {r['attributes']} | {r['domain_sizes']} | {r['states']} | "
              f"{r['t0_rows']} | {r['method']} | {r['runs']} | {r['exact_rate']:.3f} | {r['mean_missed']:.2f} | "
              f"{r['mean_duplicates']:.2f} | {r['mean_regenerated_t0']:.2f} | {r['mean_outside_space']:.2f} | "
              f"{r['mean_missing_states']:.2f} | "
              f"{'–' if r['mean_dmn_regions'] == '' else format(r['mean_dmn_regions'], '.1f')} | {r['mean_ms']:.2f} |")
    w("")
    for key, d in res["datasets"].items():
        w(f"### {d['title']}: restore check, unobserved values, LATC's verdict\n")
        w("| T0 share | T0 rows | runs with an unobserved declared value | mean unobserved values | "
          "mean states outside the observed product | Cor. 3 right | LATC says complete (of which incomplete) | "
          "restore = full table and sound |")
        w("|---|---|---|---|---|---|---|---|")
        for lv, r in d["random_removal"].items():
            lt = r["latc"]
            w(f"| {float(lv):.0%} | {r['t0_rows']} | {r['runs_with_unobserved_value']}/{r['seeds']} | "
              f"{r['mean_unobserved_declared_values']:.2f} | {lt['mean_states_outside_observed_product']:.2f} | "
              f"{lt['corollary3_correct']}/{lt['runs']} | {lt['declares_complete']} "
              f"({lt['declares_complete_while_incomplete']}) | {r['restore_ok']}/{r['restore_runs']} |")
        s = d["structured_removal"]
        lt = s["latc"]
        w(f"| structured | {s['t0_rows_min']}-{s['t0_rows_max']} | {lt['runs_with_unobserved_value']}/{lt['runs']} | "
          f"1.00 | {lt['mean_states_outside_observed_product']:.2f} | {lt['corollary3_correct']}/{lt['runs']} | "
          f"{lt['declares_complete']} ({lt['declares_complete_while_incomplete']}) | "
          f"{s['restore_ok']}/{s['restore_runs']} |")
        w("")
        w("Structured removal, per removed value (missed rows; DMN regions for the declared-value variant; "
          "LATC's Corollary 3 count):\n")
        w("| attribute = value | T0 rows | missing | COMPLETE | LATC A | LATC B | DMN declared (regions) | "
          "DMN observed | Cor. 3 count |")
        w("|---|---|---|---|---|---|---|---|---|")
        for c in s["cases"]:
            ms = c["methods"]
            w(f"| {c['attribute']} = {c['value']} | {c['t0_rows']} | {c['missing']} | "
              f"{ms['COMPLETE']['missed']} | {ms['LATC A (deficit fill)']['missed']} | "
              f"{ms['LATC B (odometer)']['missed']} | {ms['DMN (declared values)']['missed']} "
              f"({ms['DMN (declared values)']['regions']}) | {ms['DMN (observed values)']['missed']} | "
              f"{c['latc']['corollary3_count']} |")
        w("")
    w("## Trap probability (exact, `trap_frequency`)\n")
    w("P(trap | k) = probability that k rows drawn uniformly without replacement from the full product miss at "
      "least one declared value; E[missing | trap] = expected number of states outside the observed product, "
      "given a trap. `k for 5 % / 1 %` = smallest k with P(trap) <= 0.05 / 0.01 (exact, without replacement). "
      "A dash means k > |D|.\n")
    ks = TRAP_KS
    w("| space | domain sizes | states | declared values | " + " | ".join(f"k={k}" for k in ks)
      + " | k for 5 % | k for 1 % |")
    w("|---|---|---|---|" + "---|" * len(ks) + "---|---|")
    for sp, t in res["trap"].items():
        cells = ["–" if str(k) not in t["by_k"] else _fmt_p(t["by_k"][str(k)]["p_trap"]) for k in ks]
        w(f"| {t['title']} | {'x'.join(map(str, t['domains']))} | {t['states']} | {t['declared_values']} | "
          + " | ".join(cells) + f" | {t['smallest_k'].get('0.05')} | {t['smallest_k'].get('0.01')} |")
    w("")
    w("E[missing | trap] for the same k:\n")
    w("| space | " + " | ".join(f"k={k}" for k in ks) + " |")
    w("|---|" + "---|" * len(ks))
    for sp, t in res["trap"].items():
        cells = []
        for k in ks:
            r = t["by_k"].get(str(k))
            cells.append("–" if r is None or r["expected_missing_given_trap"] is None
                         else f"{r['expected_missing_given_trap']:.1f}")
        w(f"| {t['title']} | " + " | ".join(cells) + " |")
    w("")
    w("Exact P(trap) at the T0 sizes of the random-removal runs, against the runs observed (for MONK's, the "
      "draws of problem 1):\n")
    w("| space | T0 share | T0 rows | P(trap) | expected runs with a trap | observed |")
    w("|---|---|---|---|---|---|")
    for sp, t in res["trap"].items():
        for lv, e in t["experiment_levels"].items():
            w(f"| {t['title']} | {float(lv):.0%} | {e['t0_rows']} | {_fmt_p(e['p_trap'])} | "
              f"{e['expected_runs']:.2f} | {e['observed_runs']}/{e['seeds']} |")
    w("")
    return "\n".join(L) + "\n"
