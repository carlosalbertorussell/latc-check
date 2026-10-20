"""Independent recomputation of the Paper C protocol (PROTOCOL.md sections 2 to 8).

Written from paperC/verify/PROTOCOL.md (copied from branch paperc-harness) alone,
without reading paperC/harness/ and without importing latc_check. Python 3.12,
standard library only.

Usage: python3.12 paperC/verify/recompute.py <spec folder> <out folder>
Writes runs.csv, controls.csv and summary.md into <out folder>.
The readings chosen where PROTOCOL.md is open are listed in paperC/verify/READINGS.md.
"""

import ast
import csv
import hashlib
import itertools
import json
import math
import os
import random
import statistics
import sys

SIZES = (10, 20, 50, 100, 200, 500, 1000)
SEEDS = range(30)
CONDITIONS = ("C1", "C2", "C3")
SPECIAL = ("EXCLUDED", "REJECTED")

RUN_COLUMNS = [
    "sample", "source", "n", "seed", "condition",
    "n_examples", "n_distinct_examples", "examples_invalid", "examples_disagree_gt",
    "contradictory_pairs", "value_coverage", "min_value_coverage", "unseen_values",
    "reported_missing", "true_gap", "workload", "covered_valid", "valid_coverage",
    "missed_valid", "spurious_excluded", "spurious_rejected", "spurious",
    "spurious_share", "complete", "size_exceeds_valid",
]

STAT_METRICS = ["valid_coverage", "missed_valid", "spurious", "spurious_share", "workload",
                "contradictory_pairs", "min_value_coverage", "unseen_values",
                "reported_missing", "true_gap"]


class Abort(Exception):
    pass


# ---------------------------------------------------------------- loading

def check_hashes(folder):
    """CTRL-HASH: every file (recursively, minus SHA256SUMS, __pycache__, *.pyc) is
    listed with a matching sha256, and every listed file exists."""
    listed = {}
    with open(os.path.join(folder, "SHA256SUMS"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            digest, rest = line[:64], line[64:]
            if len(digest) != 64 or rest[:1] != " " or rest[1:2] not in (" ", "*"):
                raise Abort(f"CTRL-HASH: malformed line {line!r}")
            listed[rest[2:]] = digest.lower()
    present = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), folder).replace(os.sep, "/")
            if rel == "SHA256SUMS" or name.endswith(".pyc"):
                continue
            present.append(rel)
    problems = []
    for rel in sorted(present):
        if rel not in listed:
            problems.append(f"unlisted {rel}")
            continue
        with open(os.path.join(folder, rel), "rb") as f:
            if hashlib.sha256(f.read()).hexdigest() != listed[rel]:
                problems.append(f"hash mismatch {rel}")
    for rel in sorted(listed):
        if rel not in present:
            problems.append(f"missing {rel}")
    if problems:
        raise Abort("CTRL-HASH: " + "; ".join(problems))
    return len(present)


ALLOWED_NODES = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
                 ast.Compare, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Is, ast.IsNot,
                 ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Tuple, ast.List, ast.Set,
                 ast.Name, ast.Load, ast.Constant)


def compile_predicate(expr, names):
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise Abort(f"predicate node {type(node).__name__} not allowed: {expr}")
        if isinstance(node, ast.Name) and node.id not in names:
            raise Abort(f"predicate name {node.id} is not an attribute: {expr}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, str):
            raise Abort(f"predicate constant {node.value!r} is not a string: {expr}")
    return compile(tree, "<predicate>", "eval")


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


class Sample:
    def __init__(self, folder):
        self.folder = folder
        self.n_files = check_hashes(folder)
        with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
            self.spec = spec = json.load(f)
        self.id = spec["id"]
        self.names = [a["name"] for a in spec["attributes"]]
        self.domains = [list(a["values"]) for a in spec["attributes"]]
        self.outputs = list(spec["output"]["values"])
        self.m = len(self.names)
        self.predicates = [compile_predicate(e["predicate"], set(self.names))
                           for e in spec["exclusions"]]

        # D in odometer order: itertools.product varies the last factor fastest.
        self.D = [tuple(c) for c in itertools.product(*self.domains)]
        self.index = {c: i for i, c in enumerate(self.D)}

        header, body = read_csv(os.path.join(folder, "ground_truth.csv"))
        if header != self.names + ["output"]:
            raise Abort(f"CTRL-GT: header {header}")
        if len(body) != len(self.D):
            raise Abort(f"CTRL-GT: {len(body)} rows, |D| = {len(self.D)}")
        allowed = set(self.outputs) | set(SPECIAL)
        self.GT = []
        for i, r in enumerate(body):
            if tuple(r[:-1]) != self.D[i]:
                raise Abort(f"CTRL-GT: row {i} out of odometer order")
            if r[-1] not in allowed:
                raise Abort(f"CTRL-GT: row {i} output {r[-1]!r}")
            self.GT.append(r[-1])

        oheader, obody = read_csv(os.path.join(folder, "official_examples.csv"))
        if oheader != ["case_id"] + self.names + ["output"]:
            raise Abort(f"CTRL-GT: official header {oheader}")
        self.official = []
        for r in obody:
            c = tuple(r[1:-1])
            if c not in self.index:
                raise Abort(f"CTRL-GT: official row {r[0]} uses undeclared labels")
            self.official.append((self.index[c], r[-1]))

        self.E = {i for i, y in enumerate(self.GT) if y == "EXCLUDED"}
        self.R = {i for i, y in enumerate(self.GT) if y == "REJECTED"}
        self.ER = self.E | self.R
        self.V_list = [i for i, y in enumerate(self.GT) if y not in SPECIAL]
        self.V = set(self.V_list)
        self.Dset = set(range(len(self.D)))
        self.S = {i for i, c in enumerate(self.D) if not self.excluded(c)}
        self.excl_disagree = sum(1 for i in range(len(self.D))
                                 if (self.GT[i] == "EXCLUDED") != (i not in self.S))

    def excluded(self, c):
        row = dict(zip(self.names, c))
        return any(eval(p, {"__builtins__": {}}, row) for p in self.predicates)


# ---------------------------------------------------------------- example sources

def source_cells(s):
    """Yields (source, n, seed, rows) in the run order of section 5; rows are
    (D index, output label) pairs in example order."""
    if s.official:
        yield "OFFICIAL", len(s.official), "-", list(s.official)
    yield "FULL", len(s.V_list), "-", [(i, s.GT[i]) for i in s.V_list]
    for n in SIZES:
        for seed in SEEDS:
            rng = random.Random(seed)
            drawn = rng.choices(s.V_list, k=n)
            yield "UNIFORM", n, seed, [(i, s.GT[i]) for i in drawn]
    for n in SIZES:
        for seed in SEEDS:
            rng = random.Random(seed)
            perm = list(s.V_list)
            rng.shuffle(perm)
            weights = [1.0 / (k ** 1.0) for k in range(1, len(perm) + 1)]
            drawn = rng.choices(perm, weights=weights, k=n)
            yield "ZIPF", n, seed, [(i, s.GT[i]) for i in drawn]


# ---------------------------------------------------------------- conditions

def observed(s, idx_list):
    """Labels seen per attribute, in order of first appearance among the examples."""
    seen = [dict() for _ in range(s.m)]
    for i in idx_list:
        for j, label in enumerate(s.D[i]):
            seen[j].setdefault(label, None)
    return [list(d) for d in seen]


def c1_generated(s, idx_list, xset):
    """LATC as published: product of the observed labels minus the example rows."""
    obs = observed(s, idx_list)
    product = [s.index[c] for c in itertools.product(*obs)] if idx_list else []
    return [i for i in product if i not in xset], math.prod(len(o) for o in obs)


def generated(s, cond, idx_list, xset):
    if cond == "C1":
        g_list, prod_obs = c1_generated(s, idx_list, xset)
        return g_list, prod_obs - len(idx_list)
    if cond == "C2":
        return [i for i in range(len(s.D)) if i not in xset], len(s.D) - len(idx_list)
    return [i for i in range(len(s.D)) if i in s.S and i not in xset], len(s.S) - len(idx_list)


# ---------------------------------------------------------------- metrics

def ratio(a, b, empty):
    return a / b if b else empty


def run_metrics(s, rows, cond):
    idx_list = [i for i, _ in rows]
    xset = set(idx_list)
    g_list, reported = generated(s, cond, idx_list, xset)
    gset = set(g_list)
    seen = [{s.D[i][j] for i in xset} for j in range(s.m)]
    pairs = 0
    by_cond = {}
    for i, y in rows:
        by_cond.setdefault(i, []).append(y)
    for ys in by_cond.values():
        counts = {}
        for y in ys:
            counts[y] = counts.get(y, 0) + 1
        total = len(ys)
        same = sum(k * (k - 1) // 2 for k in counts.values())
        pairs += total * (total - 1) // 2 - same
    covered = len(s.V & (xset | gset))
    sp_e = len(gset & s.E)
    sp_r = len(gset & s.R)
    spurious = sp_e + sp_r
    valid_cov = ratio(covered, len(s.V), 1.0)
    return {
        "n_examples": len(idx_list),
        "n_distinct_examples": len(xset),
        "examples_invalid": sum(1 for i in idx_list if i in s.ER),
        "examples_disagree_gt": sum(1 for i, y in rows if y != s.GT[i]),
        "contradictory_pairs": pairs,
        "value_coverage": ";".join(f"{s.names[j]}={len(seen[j])}/{len(s.domains[j])}"
                                   for j in range(s.m)),
        "min_value_coverage": min(len(seen[j]) / len(s.domains[j]) for j in range(s.m)),
        "unseen_values": sum(len(set(s.domains[j]) - seen[j]) for j in range(s.m)),
        "reported_missing": reported,
        "true_gap": len(s.V - xset),
        "workload": len(g_list),
        "covered_valid": covered,
        "valid_coverage": valid_cov,
        "missed_valid": len(s.V - (xset | gset)),
        "spurious_excluded": sp_e,
        "spurious_rejected": sp_r,
        "spurious": spurious,
        "spurious_share": ratio(spurious, len(gset), 0.0),
        "complete": 1 if valid_cov == 1 and spurious == 0 else 0,
    }


def plant(s, rows):
    """CTRL-PLANT for one example set. Returns (pass, v, expected, found, c1_count)."""
    domain = s.domains[0]
    counts = {v: 0 for v in domain}
    for i, _ in rows:
        counts[s.D[i][0]] += 1
    v = min(domain, key=lambda lab: (counts[lab], domain.index(lab)))
    kept = [(i, y) for i, y in rows if s.D[i][0] != v]
    idx_list = [i for i, _ in kept]
    xset = set(idx_list)
    g2, _ = generated(s, "C2", idx_list, xset)
    target = {i for i, c in enumerate(s.D) if c[0] == v}
    expected = math.prod(len(d) for d in s.domains[1:])
    found = len(target & set(g2))
    g1, _ = generated(s, "C1", idx_list, xset)
    c1_count = sum(1 for i in g1 if s.D[i][0] == v)
    return found == len(target) == expected, v, expected, found, c1_count


# ---------------------------------------------------------------- statistics

def percentile(values, p):
    x = sorted(values)
    h = (len(x) - 1) * p
    lo = math.floor(h)
    upper = x[lo + 1] if lo + 1 < len(x) else x[lo]
    return x[lo] + (h - lo) * (upper - x[lo])


def wilson(k, n):
    z = statistics.NormalDist().inv_cdf(0.975)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------- main

def fmt(v):
    return repr(v) if isinstance(v, float) else str(v)


def main(spec_folder, out_folder):
    s = Sample(spec_folder)
    os.makedirs(out_folder, exist_ok=True)
    runs = []
    plant_results = []
    for source, n, seed, rows in source_cells(s):
        plant_results.append((source, n, seed) + plant(s, rows))
        for cond in CONDITIONS:
            r = {"sample": s.id, "source": source, "n": n, "seed": seed, "condition": cond}
            r.update(run_metrics(s, rows, cond))
            r["size_exceeds_valid"] = 1 if n > len(s.V) else 0
            runs.append(r)

    with open(os.path.join(out_folder, "runs.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(RUN_COLUMNS)
        for r in runs:
            w.writerow([fmt(r[c]) for c in RUN_COLUMNS])

    plant_fail = [p for p in plant_results if not p[3]]
    c3 = [r for r in runs if r["condition"] == "C3"]
    h3_fail = [r for r in c3 if not (r["valid_coverage"] == 1 and r["spurious"] == 0)]
    controls = [
        ("CTRL-HASH", "pass", f"{s.n_files} files"),
        ("CTRL-GT", "pass", f"|D|={len(s.D)}, official rows={len(s.official)}"),
        ("CTRL-EXCL", "pass" if s.excl_disagree == 0 else "fail",
         f"{s.excl_disagree} disagreeing rows"),
        ("CTRL-FULL", "n/a", "pass criterion only for CTRL-NUR"),
        ("CTRL-PLANT", "pass" if not plant_fail else "fail",
         f"{len(plant_results) - len(plant_fail)}/{len(plant_results)} example sets; "
         f"C1 count for v nonzero in {sum(1 for p in plant_results if p[7])} sets"),
        ("CTRL-H3", "pass" if not h3_fail else "fail",
         f"{len(c3) - len(h3_fail)}/{len(c3)} C3 runs complete; "
         f"max spurious_rejected={max((r['spurious_rejected'] for r in c3), default=0)}"),
    ]
    with open(os.path.join(out_folder, "controls.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["control", "result", "detail"])
        w.writerows(controls)

    write_summary(s, runs, controls, out_folder)


def write_summary(s, runs, controls, out_folder):
    L = [f"# {s.id}: independent recomputation", "",
         f"|D| = {len(s.D)}, |V| = {len(s.V)}, |E| = {len(s.E)}, |R| = {len(s.R)}, "
         f"|S| = {len(s.S)}, official rows = {len(s.official)}.", ""]
    if not s.official:
        L += ["OFFICIAL skipped: official_examples.csv has no data rows.", ""]
    over = [n for n in SIZES if n > len(s.V)]
    if over:
        L += [f"Sizes exceeding the valid space (|V| = {len(s.V)}): "
              + ", ".join(map(str, over)) + ".", ""]
    L += ["## Controls", "", "| control | result | detail |", "|---|---|---|"]
    L += [f"| {c} | {r} | {d} |" for c, r, d in controls]
    L += ["", "## OFFICIAL and FULL (one run per condition)", "",
          "| source | condition | " + " | ".join(STAT_METRICS) + " | complete |",
          "|---|---|" + "---|" * (len(STAT_METRICS) + 1)]
    for r in runs:
        if r["source"] in ("OFFICIAL", "FULL"):
            L.append(f"| {r['source']} | {r['condition']} | "
                     + " | ".join(fmt(r[k]) for k in STAT_METRICS) + f" | {r['complete']} |")
    L += ["", "## UNIFORM and ZIPF over 30 seeds", "",
          "Each cell: mean / median / p2.5 / p97.5 (Hyndman and Fan type 7). "
          "complete: share of seeds with complete = 1 and Wilson 95% interval.", ""]
    for cond in CONDITIONS:
        L += [f"### {cond}", "",
              "| source | n | " + " | ".join(STAT_METRICS) + " | complete |",
              "|---|---|" + "---|" * (len(STAT_METRICS) + 1)]
        for source in ("UNIFORM", "ZIPF"):
            for n in SIZES:
                cell = [r for r in runs if r["source"] == source and r["n"] == n
                        and r["condition"] == cond]
                parts = []
                for k in STAT_METRICS:
                    xs = [r[k] for r in cell]
                    parts.append(" / ".join(f"{v:.6g}" for v in (
                        sum(xs) / len(xs), percentile(xs, 0.5),
                        percentile(xs, 0.025), percentile(xs, 0.975))))
                k = sum(r["complete"] for r in cell)
                lo, hi = wilson(k, len(cell))
                parts.append(f"{k / len(cell):.4g} [{lo:.4f}, {hi:.4f}]")
                L.append(f"| {source} | {n} | " + " | ".join(parts) + " |")
        L.append("")
    with open(os.path.join(out_folder, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    try:
        main(sys.argv[1], sys.argv[2])
    except Abort as e:
        sys.exit(f"ABORTED: {e}")
