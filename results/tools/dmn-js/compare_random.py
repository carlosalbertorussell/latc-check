"""Compare the 2016 dmn-js verifier (Laurson & Maggi) with the DMN sweep and the oracle.

Table sets
  random_observed  the 1,000 tables of randomized.py's "observed" scenario (seed 20210101,
                   the first 1,000 draws of generate_case, as in randomized.run), as DMN via
                   dmn.from_exact (declared domains as inputValues, point entries, UNIQUE)
  pension_V1, car_V1
                   results/tools/inputs/*_V1.dmn (full declared domain, one value removed from T0),
                   read back with dmn_import for the sweep and the oracle
  c2_enum_dash, c2_enum_empty (supplementary, for overlaps)
                   the tables of the C.2 differential test (dmn_oracle.random_table, seed
                   20210101, 1,000 draws) whose inputs are all enumerated and have no not(...)
                   entry, exported by dmn.to_dmn_xml.  "dash" is the file as exported ('-' for
                   any); "empty" writes '' for any, the dmn-js 0.5 convention, and runs with
                   run_random.js's WILDCARD_EMPTY input shim.  The verifier ignores the hit
                   policy, so overlaps are compared with the oracle's geometric overlap pairs.

Comparison per table
  gaps: the verifier's "No rule exists for (...)" regions expanded over the domain the verifier
        uses (tool_domains: the values in the rule cells; 'any' = that domain), against the
        oracle's uncovered points (a) restricted to the verifier's domain and (b) on the full
        declared domain.  The sweep (dmn.analyse, expanded) is checked against the oracle too.
  overlaps: pairs inside every "Rules a, b, ... are overlapping" row, against the oracle's
        overlapping pairs (and the sweep's), and the verifier's maximal groups against the
        oracle's maximal overlap sets.

Run from the repo root:
  python -I results/tools/dmn-js/compare_random.py <dmn-js-repo-dir> [--work DIR] [--n 1000]
Writes results/tools/dmn-js/random_tables.json.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from itertools import combinations, product

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
from latc_check import dmn_import, dmn_oracle, randomized  # noqa: E402
from latc_check.dmn import ANY, Not, analyse, expand, from_exact, to_dmn_xml  # noqa: E402


def unq(s: str) -> str:
    s = s.strip()
    return s[1:-1] if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s


def cell_values(cell, dom):
    if cell == "any":
        return [v for v in dom if v != ""]
    return [unq(x) for x in str(cell).replace("[", "").replace("]", "").split(",")]


def tool_states(res, labels):
    dom = res["tool_domains"]
    states, total = set(), 0
    for g in res["gap_regions"]:
        per = [cell_values(c, dom[lab]) for c, lab in zip(g, labels)]
        for s in product(*per):
            states.add(s)
            total += 1
    return states, total


def compare(table, res):
    labels = [i.name for i in table.inputs]
    rec = {"rules": len(table.rules), "inputs": len(labels), "outcome": res.get("outcome"),
           "verifier_runtime_s": res.get("runtime_s"), "wall_s": res.get("wall_s")}
    o = dmn_oracle.oracle(table)
    a = analyse(table)
    oracle_missing = set(o["uncovered"])
    sweep_missing = set(expand(a.gaps, table.inputs)[0])
    rec["oracle_missing"] = len(oracle_missing)
    rec["sweep_regions"] = len(a.gaps)
    rec["sweep_equals_oracle_gaps"] = sweep_missing == oracle_missing
    rec["sweep_equals_oracle_pairs"] = a.overlap_pairs == o["pairs"]
    rec["oracle_pairs"] = len(o["pairs"])
    if res.get("outcome", "").startswith("error"):
        rec["error"] = res.get("error", res.get("outcome"))
        return rec
    dom = {lab: [v for v in res["tool_domains"][lab] if v != ""] for lab in labels}
    declared = {i.name: list(i.values) for i in table.inputs}
    rec["tool_domain_equals_declared"] = all(sorted(dom[k]) == sorted(declared[k]) for k in labels)
    rec["tool_domain_missing_values"] = {k: sorted(set(declared[k]) - set(dom[k])) for k in labels
                                         if set(declared[k]) - set(dom[k])}
    ts, total = tool_states(res, labels)
    restricted = {s for s in oracle_missing if all(v in dom[lab] for v, lab in zip(s, labels))}
    rec["verifier_regions"] = res["n_gap_regions"]
    rec["verifier_states"] = len(ts)
    rec["verifier_region_overlap_states"] = total - len(ts)
    rec["gaps_agree_on_verifier_domain"] = ts == restricted
    rec["gaps_agree_on_declared_domain"] = ts == oracle_missing
    rec["false_gaps"] = len(ts - oracle_missing)
    rec["missed_on_verifier_domain"] = len(restricted - ts)
    rec["missed_on_declared_domain"] = len(oracle_missing - ts)
    groups = [tuple(sorted(r - 1 for r in g["rules"])) for g in res.get("overlap_groups", [])]
    pairs = sorted({p for g in groups for p in combinations(g, 2)})
    gs = set(groups)
    tool_max = sorted(g for g in gs if not any(set(g) < set(h) for h in gs))
    rec["verifier_overlap_rows"] = len(groups)
    rec["verifier_pairs"] = len(pairs)
    rec["pairs_agree"] = pairs == o["pairs"]
    rec["maximal_sets_agree"] = tool_max == o["maximal_sets"]
    if not rec["pairs_agree"]:
        rec["pairs_detail"] = {"verifier_only": [p for p in pairs if p not in o["pairs"]],
                               "oracle_only": [p for p in o["pairs"] if p not in pairs]}
    if not rec["maximal_sets_agree"]:
        rec["maximal_sets_detail"] = {"verifier": tool_max, "oracle": o["maximal_sets"]}
    if not rec["gaps_agree_on_verifier_domain"]:
        rec["gap_detail"] = {"verifier_only": sorted(ts - restricted)[:10],
                             "oracle_only": sorted(restricted - ts)[:10],
                             "verifier_regions": res["gap_regions"][:10]}
    return rec


def summarise(recs):
    ok = [r for r in recs if "error" not in r]
    s = {"tables": len(recs), "verifier_errors": len(recs) - len(ok),
         "sweep_equals_oracle_gaps": sum(r["sweep_equals_oracle_gaps"] for r in recs),
         "sweep_equals_oracle_pairs": sum(r["sweep_equals_oracle_pairs"] for r in recs),
         "tables_with_overlaps_oracle": sum(r["oracle_pairs"] > 0 for r in recs)}
    if ok:
        s.update({
            "analysed": len(ok),
            "tool_domain_equals_declared": sum(r["tool_domain_equals_declared"] for r in ok),
            "gaps_agree_on_verifier_domain": sum(r["gaps_agree_on_verifier_domain"] for r in ok),
            "gaps_agree_on_declared_domain": sum(r["gaps_agree_on_declared_domain"] for r in ok),
            "tables_with_false_gaps": sum(r["false_gaps"] > 0 for r in ok),
            "tables_with_overlapping_verifier_regions": sum(r["verifier_region_overlap_states"] > 0 for r in ok),
            "pairs_agree": sum(r["pairs_agree"] for r in ok),
            "maximal_sets_agree": sum(r["maximal_sets_agree"] for r in ok),
            "oracle_missing_states_total": sum(r["oracle_missing"] for r in ok),
            "verifier_states_total": sum(r["verifier_states"] for r in ok),
            "verifier_regions_total": sum(r["verifier_regions"] for r in ok),
            "sweep_regions_total": sum(r["sweep_regions"] for r in ok),
            "tables_verifier_fewer_regions": sum(r["verifier_regions"] < r["sweep_regions"] for r in ok),
            "tables_verifier_more_regions": sum(r["verifier_regions"] > r["sweep_regions"] for r in ok),
            "verifier_runtime_s_total": round(sum(r["verifier_runtime_s"] or 0 for r in ok), 3),
            "verifier_runtime_s_max": max(r["verifier_runtime_s"] or 0 for r in ok),
        })
    errs = {}
    for r in recs:
        if "error" in r:
            key = r["error"].split(" | ")[0][:120]
            errs[key] = errs.get(key, 0) + 1
    if errs:
        s["error_kinds"] = errs
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="dmn-js verifier clone (with _harness/node_modules)")
    ap.add_argument("--deps", default=None)
    ap.add_argument("--work", default=None, help="directory for the exported DMN files")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20210101)
    ap.add_argument("--node", default="node")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()
    deps = args.deps or os.path.join(args.repo, "_harness")
    work = args.work or tempfile.mkdtemp(prefix="dmnjs_random_")
    os.makedirs(work, exist_ok=True)
    t_start = time.time()

    jobs, tables = [], {}

    def add(set_name, key, table, xml=None, path=None, wildcard_empty=False):
        if path is None:
            path = os.path.join(work, f"{key}.dmn")
            with open(path, "w", encoding="utf-8") as f:
                f.write(xml)
        tables[key] = (set_name, table)
        jobs.append({"id": key, "file": os.path.abspath(path), "wildcard_empty": wildcard_empty})

    rng = random.Random(args.seed)
    for k in range(args.n):
        t = randomized.generate_case(rng, "observed")
        d = from_exact(t)  # declared domains, point entries, UNIQUE
        add("random_observed", f"r{k:04d}", d, to_dmn_xml(d, f"r{k:04d}"))

    manifest = json.load(open(os.path.join(REPO, "results", "tools", "inputs", "manifest.json"), encoding="utf-8"))
    for c in manifest["cases"]:
        if c["dataset"] not in ("pension", "car"):
            continue
        p = os.path.join(REPO, c["files"]["V1"])
        imported, err = dmn_import.import_file(p)
        assert err is None and imported and imported[0].dmn is not None, (p, err)
        add(f"{c['dataset']}_V1", os.path.basename(p)[:-4], imported[0].dmn, path=p)

    rng2 = random.Random(args.seed)
    for k in range(1000):
        t = dmn_oracle.random_table(rng2)
        if any(i.numeric for i in t.inputs) or any(isinstance(e, Not) for r in t.rules for e in r.entries):
            continue
        xml = to_dmn_xml(t, f"c{k:04d}")
        add("c2_enum_dash", f"c{k:04d}_dash", t, xml)
        add("c2_enum_empty", f"c{k:04d}_empty", t, xml.replace("<text>-</text>", "<text></text>"),
            wildcard_empty=True)

    list_path = os.path.join(work, "jobs.json")
    out_path = os.path.join(work, "verifier.jsonl")
    with open(list_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f)
    t0 = time.time()
    subprocess.run([args.node, os.path.join(HERE, "run_random.js"), args.repo, deps, list_path, out_path,
                    str(args.concurrency)], check=True)
    verifier_wall = time.time() - t0
    results = {}
    with open(out_path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            results[r["id"]] = r

    per_set, records = {}, {}
    for key, (set_name, table) in tables.items():
        rec = compare(table, results[key])
        rec["id"] = key
        if set_name.startswith("c2"):
            rec["hit_policy"] = table.hit_policy
            rec["has_wildcard"] = any(e is ANY for r in table.rules for e in r.entries)
        per_set.setdefault(set_name, []).append(rec)
    for name, recs in per_set.items():
        records[name] = {"summary": summarise(recs), "tables": recs}
    for name in ("c2_enum_dash", "c2_enum_empty"):
        if name in records:
            recs = records[name]["tables"]
            for flag in (False, True):
                sub = [r for r in recs if r["has_wildcard"] == flag]
                records[name]["summary"]["with_wildcard" if flag else "without_wildcard"] = summarise(sub)

    commit = subprocess.run(["git", "-C", args.repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    node_v = subprocess.run([args.node, "--version"], capture_output=True, text=True).stdout.strip()
    out = {"tool": "Laurson & Maggi DMN verifier (ulaurson/dmn-js), lib/features/verifier/Verifier.js",
           "commit": commit, "node": node_v, "python": sys.version.split()[0],
           "harness": "results/tools/dmn-js/harness.js via run_random.js", "seed": args.seed,
           "random_tables": args.n,
           "verifier_wall_s_all_files": round(verifier_wall, 1),
           "total_wall_s": round(time.time() - t_start, 1),
           "files_run": len(jobs),
           "sets": records}
    with open(os.path.join(HERE, "random_tables.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    for name, r in records.items():
        print(name, json.dumps(r["summary"]))
    print(f"verifier wall {verifier_wall:.1f} s, total {time.time() - t_start:.1f} s, work dir {work}")


if __name__ == "__main__":
    main()
