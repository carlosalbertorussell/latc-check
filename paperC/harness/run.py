"""Paper C harness: run every condition x source x size x seed of PROTOCOL.md.

    python -m paperC.harness.run --spec paperC/specs/<ID> --out paperC/results/<ID>

Writes runs.csv, controls.csv, summary.md and manifest.json into --out.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
from collections import defaultdict

from . import experiment as ex
from .spec import SpecError, folder_files, load_sample, sha256_file
from .stats import describe, wilson

PROTOCOL_COMMIT = "ee7c527080e665df70b906f0cbf091098e84ad5f"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RUN_FIELDS = [
    "sample_id", "source", "size", "seed", "condition",
    "n_examples", "n_distinct_examples", "examples_invalid", "examples_disagree_gt",
    "contradictory_pairs", "value_coverage", "min_value_coverage", "unseen_values",
    "reported_missing", "true_gap", "workload", "covered_valid", "valid_coverage",
    "missed_valid", "spurious_excluded", "spurious_rejected", "spurious",
    "spurious_share", "complete", "size_exceeds_valid",
]
CONTROL_FIELDS = ["control", "source", "size", "seed", "observed", "expected", "pass", "detail"]
STAT_METRICS = [
    "valid_coverage", "missed_valid", "spurious", "spurious_share", "workload",
    "contradictory_pairs", "min_value_coverage", "unseen_values", "reported_missing",
    "true_gap",
]


def _rel(path: str) -> str:
    p = os.path.abspath(path)
    return os.path.relpath(p, REPO).replace(os.sep, "/") if p.startswith(REPO + os.sep) else os.path.basename(p)


def _git(*args: str) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _seed(s) -> str:
    return "-" if s is None else str(s)


def run_all(sample, progress=True):
    """Return (runs, controls).  Runs are dicts with RUN_FIELDS keys."""
    runs, controls = [], []
    plant_ok = plant_n = 0
    for source, size, seed, examples in ex.example_sets(sample):
        em = ex.example_metrics(sample, examples)
        for cond in ex.CONDITIONS:
            g, reported = ex.generate(sample, examples, cond)
            row = {"sample_id": sample.sample_id, "source": source, "size": size,
                   "seed": _seed(seed), "condition": cond}
            row.update({k: v for k, v in em.items() if not k.startswith("_")})
            row.update(ex.run_metrics(sample, em, g, reported))
            row["size_exceeds_valid"] = int(size > len(sample.V))
            runs.append(row)
        pd = ex.planted_defect(sample, examples)
        plant_n += 1
        plant_ok += pd["pass"]
        controls.append({
            "control": "CTRL-PLANT", "source": source, "size": size, "seed": _seed(seed),
            "observed": pd["c2_generated"], "expected": pd["expected"], "pass": int(pd["pass"]),
            "detail": f"{sample.names[0]}={pd['value']}; removed {pd['removed']} example rows; "
                      f"C1 generated {pd['c1_generated']} rows with that value"})
        if progress and (seed is None or seed == ex.SEEDS[-1]):
            print(f"  {source} n={size} done", file=sys.stderr)

    head = [{"control": "CTRL-HASH", "source": "-", "size": "-", "seed": "-",
             "observed": "verified", "expected": "verified", "pass": 1,
             "detail": "every file listed in SHA256SUMS and matching"},
            {"control": "CTRL-GT", "source": "-", "size": "-", "seed": "-",
             "observed": len(sample.gt_order), "expected": sample.declared_size, "pass": 1,
             "detail": "ground_truth.csv header, odometer order and outputs; official labels declared"},
            {"control": "CTRL-EXCL", "source": "-", "size": "-", "seed": "-",
             "observed": sample.excl_disagreements, "expected": 0,
             "pass": int(sample.excl_disagreements == 0),
             "detail": "rows where (output = EXCLUDED) differs from (an exclusion predicate holds)"}]
    full_c1 = next(r for r in runs if r["source"] == "FULL" and r["condition"] == "C1")
    if sample.sample_id == "CTRL-NUR":
        ok = full_c1["reported_missing"] == 0 and full_c1["workload"] == 0
        head.append({"control": "CTRL-FULL", "source": "FULL", "size": full_c1["size"], "seed": "-",
                     "observed": f"missing_count={full_c1['reported_missing']}; workload={full_c1['workload']}",
                     "expected": "missing_count=0; workload=0", "pass": int(ok),
                     "detail": "C1 on the full data set"})
    else:
        head.append({"control": "CTRL-FULL", "source": "FULL", "size": full_c1["size"], "seed": "-",
                     "observed": f"missing_count={full_c1['reported_missing']}; workload={full_c1['workload']}",
                     "expected": "-", "pass": "-",
                     "detail": "recorded without a pass criterion (only CTRL-NUR has one)"})
    c3 = [r for r in runs if r["condition"] == "C3"]
    c3_ok = sum(r["complete"] for r in c3)
    tail = [{"control": "CTRL-PLANT", "source": "ALL", "size": "-", "seed": "-",
             "observed": plant_ok, "expected": plant_n, "pass": int(plant_ok == plant_n),
             "detail": "example sets where C2 regenerated every declared row with the removed value"},
            {"control": "CTRL-H3", "source": "ALL", "size": "-", "seed": "-",
             "observed": c3_ok, "expected": len(c3), "pass": int(c3_ok == len(c3)),
             "detail": f"C3 runs with valid_coverage = 1 and spurious = 0; |R| = {len(sample.R)}"}]
    return runs, head + controls + tail


def _f(x) -> str:
    return f"{x:.4f}"


def _cells(rows, key):
    out = defaultdict(list)
    for r in rows:
        out[(r["condition"], r["source"], r["size"])].append(r[key])
    return out


def h4_indicators(runs) -> list[tuple[str, bool, str]]:
    c1 = [r for r in runs if r["condition"] == "C1"]
    full = next(r for r in c1 if r["source"] == "FULL")
    out = [("(i) CTRL-FULL: C1 on the full set reports 0 missing and generates 0 rows",
            full["reported_missing"] == 0 and full["workload"] == 0,
            f"missing_count={full['reported_missing']}, workload={full['workload']}")]
    rnd = [r for r in c1 if r["source"] in ("UNIFORM", "ZIPF")]
    npos = sum(r["reported_missing"] > 0 for r in rnd)
    out.append(("(ii) every UNIFORM and ZIPF C1 run has reported_missing > 0",
                npos == len(rnd), f"{npos}/{len(rnd)} runs"))
    means = {}
    for src in ("UNIFORM", "ZIPF"):
        means[src] = [sum(r["missed_valid"] for r in rnd if r["source"] == src and r["size"] == n) / len(ex.SEEDS)
                      for n in ex.SIZES]
        ok = all(a >= b for a, b in zip(means[src], means[src][1:]))
        out.append((f"(iii) {src}: mean C1 missed_valid non-increasing in n", ok,
                    ", ".join(f"n={n}: {_f(m)}" for n, m in zip(ex.SIZES, means[src]))))
    out.append(("(iv) UNIFORM n=10: mean C1 missed_valid > 0", means["UNIFORM"][0] > 0,
                _f(means["UNIFORM"][0])))
    return out


def summary_md(sample, runs, controls) -> str:
    L = []
    L.append(f"# Paper C results: {sample.sample_id}\n")
    L.append(f"Protocol: `paperC/PROTOCOL.md`, registered at commit `{PROTOCOL_COMMIT}`.\n")
    L.append(f"Title: {sample.spec.get('title', '')}\n")
    L.append("## Sample\n")
    L.append("| \\|D\\| | \\|V\\| | \\|E\\| | \\|R\\| | official rows | attributes |")
    L.append("|---|---|---|---|---|---|")
    L.append(f"| {sample.declared_size} | {len(sample.V)} | {len(sample.E)} | {len(sample.R)} | "
             f"{len(sample.official)} | {len(sample.names)} |\n")
    if not sample.official:
        L.append("official_examples.csv has no data rows, so the OFFICIAL source is skipped.\n")
    over = [n for n in ex.SIZES if n > len(sample.V)]
    if over:
        L.append(f"Sizes exceeding |V| (draws stay with replacement): {over}.\n")

    L.append("## Controls\n")
    L.append("| control | source | observed | expected | pass | detail |")
    L.append("|---|---|---|---|---|---|")
    for c in controls:
        if c["control"] != "CTRL-PLANT" or c["source"] == "ALL":
            L.append(f"| {c['control']} | {c['source']} | {c['observed']} | {c['expected']} | "
                     f"{c['pass']} | {c['detail']} |")
    L.append("\nCTRL-DET (determinism) is checked outside a single run; see the README.\n")

    single = [r for r in runs if r["source"] in ("OFFICIAL", "FULL")]
    L.append("## OFFICIAL and FULL (one run per condition)\n")
    cols = ["n_examples", "unseen_values", "reported_missing", "true_gap", "workload",
            "valid_coverage", "missed_valid", "spurious", "spurious_share",
            "contradictory_pairs", "examples_disagree_gt", "complete"]
    L.append("| source | condition | " + " | ".join(cols) + " |")
    L.append("|---|---|" + "---|" * len(cols))
    for r in single:
        vals = [_f(r[c]) if isinstance(r[c], float) else str(r[c]) for c in cols]
        L.append(f"| {r['source']} | {r['condition']} | " + " | ".join(vals) + " |")
    L.append("")

    seeded = [r for r in runs if r["source"] in ("UNIFORM", "ZIPF")]
    L.append(f"## UNIFORM and ZIPF: statistics over seeds {ex.SEEDS[0]}..{ex.SEEDS[-1]}\n")
    L.append("Mean, median, 2.5th and 97.5th percentiles (type 7) across seeds.\n")
    for metric in STAT_METRICS:
        cells = _cells(seeded, metric)
        L.append(f"### {metric}\n")
        L.append("| condition | source | n | seeds | mean | median | p2.5 | p97.5 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for (cond, src, n), vals in cells.items():
            d = describe([float(v) for v in vals])
            L.append(f"| {cond} | {src} | {n} | {len(vals)} | {_f(d['mean'])} | {_f(d['median'])} | "
                     f"{_f(d['p2.5'])} | {_f(d['p97.5'])} |")
        L.append("")
    L.append("### COMPLETE share (Wilson 95% interval)\n")
    L.append("| condition | source | n | complete / seeds | share | lower | upper |")
    L.append("|---|---|---|---|---|---|---|")
    for (cond, src, n), vals in _cells(seeded, "complete").items():
        k, N = sum(vals), len(vals)
        lo, hi = wilson(k, N)
        L.append(f"| {cond} | {src} | {n} | {k}/{N} | {_f(k / N)} | {_f(lo)} | {_f(hi)} |")
    L.append("")

    L.append("## Hypothesis indicators for this sample (PROTOCOL.md section 8)\n")
    by = {(r["source"], r["condition"]): r for r in single}
    if ("OFFICIAL", "C1") in by:
        o1 = by[("OFFICIAL", "C1")]
        L.append(f"* H1: OFFICIAL unseen_values = {o1['unseen_values']} (> 0: {o1['unseen_values'] > 0}); "
                 f"C1 missed_valid = {o1['missed_valid']} (> 0: {o1['missed_valid'] > 0}); "
                 f"C1 reported_missing = {o1['reported_missing']}, true_gap = {o1['true_gap']}.")
    else:
        L.append("* H1: no OFFICIAL rows; this sample does not enter the H1 decision.")
    f2 = by[("FULL", "C2")]
    L.append(f"* H2: FULL C2 spurious_share = {_f(f2['spurious_share'])} "
             f"(>= 0.10: {f2['spurious_share'] >= 0.10}).")
    h3 = next(c for c in controls if c["control"] == "CTRL-H3")
    L.append(f"* H3: CTRL-H3 pass = {h3['pass']} ({h3['observed']}/{h3['expected']} C3 runs complete; "
             f"|R| = {len(sample.R)}).")
    if sample.sample_id == "CTRL-NUR":
        ind = h4_indicators(runs)
        L.append(f"* H4: supported = {all(ok for _, ok, _ in ind)}.")
        for text, ok, detail in ind:
            L.append(f"  * {text}: {ok} ({detail})")
    L.append("")
    return "\n".join(L)


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    try:
        sample = load_sample(args.spec)
    except SpecError as e:
        print(f"ABORTED: {e}", file=sys.stderr)
        return 2
    os.makedirs(args.out, exist_ok=True)
    runs, controls = run_all(sample, progress=not args.quiet)

    outputs = {
        "runs.csv": lambda p: _write_csv(p, RUN_FIELDS, runs),
        "controls.csv": lambda p: _write_csv(p, CONTROL_FIELDS, controls),
        "summary.md": lambda p: _write_text(p, summary_md(sample, runs, controls)),
    }
    for name, write in outputs.items():
        write(os.path.join(args.out, name))

    spec_dir = os.path.abspath(args.spec)
    inputs = [os.path.join(spec_dir, f) for f in folder_files(spec_dir) + ["SHA256SUMS"]]
    inputs.append(os.path.join(REPO, "paperC", "PROTOCOL.md"))
    hdir = os.path.dirname(os.path.abspath(__file__))
    inputs += [os.path.join(hdir, f) for f in sorted(os.listdir(hdir)) if f.endswith(".py")]
    inputs += [os.path.join(REPO, "latc_check", f) for f in ("__init__.py", "latc.py", "model.py", "reference.py")]
    tracked = ["paperC/harness", "paperC/PROTOCOL.md", _rel(spec_dir), "latc_check"]
    status = _git("status", "--porcelain", "--", *tracked)
    manifest = {
        "sample_id": sample.sample_id,
        "protocol": {"path": "paperC/PROTOCOL.md", "registered_commit": PROTOCOL_COMMIT},
        "harness_commit": _git("rev-parse", "HEAD") or "unknown",
        "tracked_inputs_unmodified": None if status is None else status == "",
        "python": {"version": platform.python_version(),
                   "implementation": platform.python_implementation()},
        "design": {"sources": list(ex.SOURCES), "sizes": list(ex.SIZES),
                   "seeds": [ex.SEEDS[0], ex.SEEDS[-1]], "conditions": list(ex.CONDITIONS),
                   "zipf_s": ex.ZIPF_S},
        "counts": {"runs": len(runs), "controls_rows": len(controls)},
        "inputs": {_rel(p): sha256_file(p) for p in inputs},
        "outputs": {_rel(os.path.join(args.out, n)): sha256_file(os.path.join(args.out, n)) for n in outputs},
    }
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=False)
        f.write("\n")
    failed = [c["control"] for c in controls if c["pass"] == 0 and c["source"] in ("-", "ALL", "FULL")]
    print(f"{len(runs)} runs; controls failing: {sorted(set(failed)) or 'none'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
