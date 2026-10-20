"""Independent recomputation of the Paper C protocol (PROTOCOL.md sections 2 to 8).

Written from paperC/verify/PROTOCOL.md alone, without reading or importing the
harness or latc_check. Standard library only; Python 3.12.

Usage: python3.12 paperC/verify/recompute.py paperC/specs/NZ-SLP [more folders]
Writes paperC/verify/<ID>/runs.csv, controls.csv and summary.md.

Readings chosen where PROTOCOL.md leaves room are listed in READINGS.md.
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
STAT_METRICS = ("valid_coverage", "missed_valid", "spurious", "spurious_share",
                "workload", "contradictory_pairs", "min_value_coverage",
                "unseen_values", "reported_missing", "true_gap")
RUN_COLUMNS = ("sample", "source", "size", "seed", "condition",
               "n_examples", "n_distinct_examples", "examples_invalid",
               "examples_disagree_gt", "contradictory_pairs", "value_coverage",
               "min_value_coverage", "unseen_values", "reported_missing", "true_gap",
               "workload", "covered_valid", "valid_coverage", "missed_valid",
               "spurious_excluded", "spurious_rejected", "spurious", "spurious_share",
               "complete", "size_exceeds_valid")
HERE = os.path.dirname(os.path.abspath(__file__))


class Abort(Exception):
    pass


# ---------------------------------------------------------------- loading

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ctrl_hash(folder):
    listed = {}
    with open(os.path.join(folder, "SHA256SUMS"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            digest, sep, rest = line[:64], line[64:66], line[66:]
            if len(digest) != 64 or sep not in ("  ", " *"):
                return False, "malformed line: " + line
            listed[rest] = digest
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
            problems.append("unlisted " + rel)
        elif sha256(os.path.join(folder, rel)) != listed[rel]:
            problems.append("mismatch " + rel)
    for rel in sorted(listed):
        if rel not in present:
            problems.append("absent " + rel)
    return not problems, "; ".join(problems) or f"{len(present)} files match"


class Sample:
    def __init__(self, folder):
        self.folder = folder
        ok, detail = ctrl_hash(folder)
        self.ctrl_hash = (ok, detail)
        if not ok:
            raise Abort("CTRL-HASH failed: " + detail)
        with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
            self.spec = json.load(f)
        self.id = self.spec["id"]
        self.names = [a["name"] for a in self.spec["attributes"]]
        self.domains = [list(a["values"]) for a in self.spec["attributes"]]
        self.m = len(self.names)
        self.outputs = list(self.spec["output"]["values"])
        # odometer index: last attribute varies fastest
        self.weights = [0] * self.m
        w = 1
        for j in range(self.m - 1, -1, -1):
            self.weights[j] = w
            w *= len(self.domains[j])
        self.size_D = w
        self.label_index = [{v: i for i, v in enumerate(d)} for d in self.domains]
        self._load_gt()
        self._load_official()
        self._exclusions()

    def index(self, cond):
        return sum(self.label_index[j][cond[j]] * self.weights[j] for j in range(self.m))

    def cond(self, idx):
        out = []
        for j in range(self.m):
            q, idx = divmod(idx, self.weights[j])
            out.append(self.domains[j][q])
        return tuple(out)

    def _load_gt(self):
        problems = []
        with open(os.path.join(self.folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
            raw = f.read()
        if "\r" in raw:
            problems.append("CR in ground_truth.csv")
        rows = list(csv.reader(raw.splitlines()))
        if rows[0] != self.names + ["output"]:
            problems.append("header differs")
        body = rows[1:]
        if len(body) != self.size_D:
            problems.append(f"{len(body)} rows, |D| = {self.size_D}")
        allowed = set(self.outputs) | {"EXCLUDED", "REJECTED"}
        self.gt = []
        for i, (r, c) in enumerate(zip(body, itertools.product(*self.domains))):
            if tuple(r[:-1]) != c:
                problems.append(f"row {i + 1} out of odometer order")
                break
            if r[-1] not in allowed:
                problems.append(f"row {i + 1} output {r[-1]!r}")
            self.gt.append(r[-1])
        self.gt_problems = problems
        if problems:
            raise Abort("CTRL-GT failed: " + "; ".join(problems))
        self.E = {i for i, y in enumerate(self.gt) if y == "EXCLUDED"}
        self.R = {i for i, y in enumerate(self.gt) if y == "REJECTED"}
        self.V_list = [i for i, y in enumerate(self.gt) if y not in ("EXCLUDED", "REJECTED")]
        self.V = set(self.V_list)

    def _load_official(self):
        with open(os.path.join(self.folder, "official_examples.csv"), encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        if rows[0] != ["case_id"] + self.names + ["output"]:
            raise Abort("CTRL-GT failed: official_examples.csv header differs")
        self.official = []
        for r in rows[1:]:
            c = tuple(r[1:-1])
            for j in range(self.m):
                if c[j] not in self.label_index[j]:
                    raise Abort(f"CTRL-GT failed: undeclared label {c[j]!r} in OFFICIAL")
            self.official.append((self.index(c), r[-1]))

    def _exclusions(self):
        # PROTOCOL.md s 2 prescribes eval() with empty builtins; the predicates are first
        # restricted to the node whitelist of the 2026-10-20 clarification 1.
        allowed = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
                   ast.Compare, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Tuple, ast.List,
                   ast.Set, ast.Name, ast.Load, ast.Constant)
        preds = []
        for e in self.spec.get("exclusions", []):
            tree = ast.parse(e["predicate"], mode="eval")
            for node in ast.walk(tree):
                ok = isinstance(node, allowed)
                ok = ok and not (isinstance(node, ast.Name) and node.id not in self.names)
                ok = ok and not (isinstance(node, ast.Constant) and not isinstance(node.value, str))
                if not ok:
                    raise Abort(f"predicate {e['id']} has a disallowed node {type(node).__name__}")
            preds.append(compile(tree, e["id"], "eval"))
        self.S = set()
        for i, c in enumerate(itertools.product(*self.domains)):
            row = dict(zip(self.names, c))
            if not any(eval(p, {"__builtins__": {}}, row) for p in preds):
                self.S.add(i)
        notS = set(range(self.size_D)) - self.S
        self.excl_disagree = len(notS ^ self.E)


# ---------------------------------------------------------------- example sources

def uniform(sample, n, seed):
    rng = random.Random(seed)
    drawn = rng.choices(sample.V_list, k=n)
    return [(c, sample.gt[c]) for c in drawn]


def zipf(sample, n, seed):
    rng = random.Random(seed)
    perm = list(sample.V_list)
    rng.shuffle(perm)
    drawn = rng.choices(perm, weights=[1.0 / (k ** 1.0) for k in range(1, len(perm) + 1)], k=n)
    return [(c, sample.gt[c]) for c in drawn]


def example_sets(sample):
    if sample.official:
        yield "OFFICIAL", "-", len(sample.official), list(sample.official)
    yield "FULL", "-", len(sample.V_list), [(c, sample.gt[c]) for c in sample.V_list]
    for name, fn in (("UNIFORM", uniform), ("ZIPF", zipf)):
        for n in SIZES:
            for seed in SEEDS:
                yield name, seed, n, fn(sample, n, seed)


# ---------------------------------------------------------------- generation

def observed_domains(sample, conds):
    """Per attribute, the label indices seen in the examples, first-appearance order."""
    seen = [dict() for _ in range(sample.m)]
    for c in conds:
        for j in range(sample.m):
            q = (c // sample.weights[j]) % len(sample.domains[j])
            seen[j].setdefault(q, None)
    return [list(s) for s in seen]


def product_indices(sample, doms):
    parts = [[q * sample.weights[j] for q in doms[j]] for j in range(sample.m)]
    acc = [0]
    for p in parts:
        acc = [a + b for a in acc for b in p]
    return acc if all(doms) else []


def generate(sample, cond, X, X_list):
    """Return (G_list, reported_missing)."""
    if cond == "C1":
        doms = observed_domains(sample, X_list)
        assembled = product_indices(sample, doms)
        G_list = [c for c in assembled if c not in X]
        cards = math.prod(len(d) for d in doms)
        return G_list, cards - len(X_list)
    if cond == "C2":
        return [c for c in range(sample.size_D) if c not in X], sample.size_D - len(X_list)
    G_list = [c for c in range(sample.size_D) if c in sample.S and c not in X]
    return G_list, len(sample.S) - len(X_list)


# ---------------------------------------------------------------- metrics

def metrics(sample, examples, cond):
    X_list = [c for c, _ in examples]
    X = set(X_list)
    G_list, reported = generate(sample, cond, X, X_list)
    G = set(G_list)
    EuR = sample.E | sample.R
    by_cond = {}
    for c, y in examples:
        by_cond.setdefault(c, []).append(y)
    contradictory = 0
    for ys in by_cond.values():
        counts = {}
        for y in ys:
            counts[y] = counts.get(y, 0) + 1
        total = len(ys)
        same = sum(k * (k - 1) // 2 for k in counts.values())
        contradictory += total * (total - 1) // 2 - same
    cov_parts, ratios, unseen = [], [], 0
    for j in range(sample.m):
        dj = len(sample.domains[j])
        seen = {(c // sample.weights[j]) % dj for c in X}
        cov_parts.append(f"{sample.names[j]}={len(seen)}/{dj}")
        ratios.append(len(seen) / dj)
        unseen += dj - len(seen)
    XG = X | G
    covered = len(sample.V & XG)
    nV = len(sample.V)
    sp_e, sp_r = len(G & sample.E), len(G & sample.R)
    spurious = len(G & EuR)
    vc = covered / nV if nV else 1.0
    return {
        "n_examples": len(X_list),
        "n_distinct_examples": len(X),
        "examples_invalid": sum(1 for c in X_list if c in EuR),
        "examples_disagree_gt": sum(1 for c, y in examples if y != sample.gt[c]),
        "contradictory_pairs": contradictory,
        "value_coverage": ";".join(cov_parts),
        "min_value_coverage": min(ratios),
        "unseen_values": unseen,
        "reported_missing": reported,
        "true_gap": len(sample.V - X),
        "workload": len(G_list),
        "covered_valid": covered,
        "valid_coverage": vc,
        "missed_valid": nV - covered,
        "spurious_excluded": sp_e,
        "spurious_rejected": sp_r,
        "spurious": spurious,
        "spurious_share": spurious / len(G) if G else 0.0,
        "complete": 1 if vc == 1 and spurious == 0 else 0,
    }


def plant(sample, examples):
    """CTRL-PLANT on one example set. Returns (passed, v, c2_count, expected, c1_count)."""
    d0 = sample.domains[0]
    w0 = sample.weights[0]
    counts = [0] * len(d0)
    for c, _ in examples:
        counts[c // w0] += 1
    v = min(range(len(d0)), key=lambda q: (counts[q], q))
    kept = [(c, y) for c, y in examples if c // w0 != v]
    X_list = [c for c, _ in kept]
    X = set(X_list)
    G2, _ = generate(sample, "C2", X, X_list)
    G1, _ = generate(sample, "C1", X, X_list)
    target = set(range(v * w0, (v + 1) * w0))
    c2 = len(target & set(G2))
    c1 = len(target & set(G1))
    return c2 == w0, d0[v], c2, w0, c1, len(examples) - len(kept)


# ---------------------------------------------------------------- statistics

def pct(xs, p):
    xs = sorted(xs)
    h = (len(xs) - 1) * p
    lo = math.floor(h)
    hi = xs[lo + 1] if lo + 1 < len(xs) else xs[lo]
    return xs[lo] + (h - lo) * (hi - xs[lo])


def wilson(k, n):
    z = statistics.NormalDist().inv_cdf(0.975)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def fmt(v):
    return repr(v) if isinstance(v, float) else str(v)


# ---------------------------------------------------------------- run

def run(folder, outroot):
    s = Sample(folder)
    out = os.path.join(outroot, s.id)
    os.makedirs(out, exist_ok=True)
    runs = []
    plant_results = []
    for source, seed, size, ex in example_sets(s):
        for cond in CONDITIONS:
            r = {"sample": s.id, "source": source, "size": size, "seed": seed, "condition": cond}
            r.update(metrics(s, ex, cond))
            r["size_exceeds_valid"] = 1 if source in ("UNIFORM", "ZIPF") and size > len(s.V) else 0
            runs.append(r)
        plant_results.append((source, size, seed) + plant(s, ex))
    with open(os.path.join(out, "runs.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(RUN_COLUMNS)
        for r in runs:
            w.writerow([fmt(r[c]) for c in RUN_COLUMNS])

    with open(os.path.join(out, "plant.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(("source", "size", "seed", "pass", "v", "c2_generated_with_v", "expected",
                    "c1_generated_with_v", "removed_rows"))
        for p in plant_results:
            w.writerow((p[0], p[1], p[2], int(p[3])) + p[4:])
    c3 = [r for r in runs if r["condition"] == "C3"]
    h3_fail = [r for r in c3 if not (r["valid_coverage"] == 1 and r["spurious"] == 0)]
    plant_fail = [p for p in plant_results if not p[3]]
    controls = [
        ("CTRL-HASH", "pass", s.ctrl_hash[1]),
        ("CTRL-GT", "pass", f"|D|={s.size_D} rows in odometer order; {len(s.official)} OFFICIAL rows use declared labels"),
        ("CTRL-EXCL", "pass" if s.excl_disagree == 0 else "fail", f"{s.excl_disagree} disagreeing rows"),
        ("CTRL-FULL", "n/a", "no pass criterion outside CTRL-NUR"),
        ("CTRL-PLANT", "pass" if not plant_fail else "fail",
         f"{len(plant_results)} example sets, {len(plant_fail)} failures; "
         f"C1 count for v nonzero in {sum(1 for p in plant_results if p[7])} sets"),
        ("CTRL-H3", "pass" if not h3_fail else "fail",
         f"{len(c3)} C3 runs, {len(h3_fail)} failures; |R|={len(s.R)}"),
    ]
    with open(os.path.join(out, "controls.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(("sample", "control", "result", "detail"))
        for c in controls:
            w.writerow((s.id,) + c)

    write_summary(s, runs, controls, plant_results, os.path.join(out, "summary.md"))
    return s, runs, controls


def write_summary(s, runs, controls, plant_results, path):
    L = [f"# {s.id}: independent recomputation", "",
         f"|D| = {s.size_D}, |E| = {len(s.E)}, |R| = {len(s.R)}, |V| = {len(s.V)}, "
         f"|S| = {len(s.S)}, OFFICIAL rows = {len(s.official)}.", ""]
    big = [n for n in SIZES if n > len(s.V)]
    if big:
        L += [f"Sizes exceeding the valid space: {big}.", ""]
    if not s.official:
        L += ["OFFICIAL skipped: official_examples.csv has no data rows.", ""]
    L += ["## Controls", "", "| control | result | detail |", "|---|---|---|"]
    L += [f"| {c} | {r} | {d} |" for c, r, d in controls]
    L += ["", "## OFFICIAL and FULL (single runs)", "",
          "| source | condition | n | unseen_values | reported_missing | true_gap | workload | missed_valid | spurious | spurious_share | valid_coverage | complete |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in runs:
        if r["source"] in ("OFFICIAL", "FULL"):
            L.append(f"| {r['source']} | {r['condition']} | {r['n_examples']} | {r['unseen_values']} | "
                     f"{r['reported_missing']} | {r['true_gap']} | {r['workload']} | {r['missed_valid']} | "
                     f"{r['spurious']} | {fmt(r['spurious_share'])} | {fmt(r['valid_coverage'])} | {r['complete']} |")
    L += ["", "## UNIFORM and ZIPF over 30 seeds", "",
          "Per metric: mean / median / p2.5 / p97.5 (type 7). Completion share with Wilson 95% interval.", ""]
    groups = {}
    for r in runs:
        if r["source"] in ("UNIFORM", "ZIPF"):
            groups.setdefault((r["condition"], r["source"], r["size"]), []).append(r)
    L += ["| condition | source | n | " + " | ".join(STAT_METRICS) + " | complete share [Wilson 95%] |",
          "|---|---|---:|" + "---|" * len(STAT_METRICS) + "---|"]
    for cond in CONDITIONS:
        for src in ("UNIFORM", "ZIPF"):
            for n in SIZES:
                g = groups[(cond, src, n)]
                cells = []
                for mname in STAT_METRICS:
                    xs = [r[mname] for r in g]
                    cells.append(" / ".join(fmt4(v) for v in (statistics.fmean(xs), statistics.median(xs),
                                                              pct(xs, 0.025), pct(xs, 0.975))))
                k = sum(r["complete"] for r in g)
                lo, hi = wilson(k, len(g))
                cells.append(f"{k}/{len(g)} [{lo:.4f}, {hi:.4f}]")
                L.append(f"| {cond} | {src} | {n} | " + " | ".join(cells) + " |")
    L += ["", "## Hypothesis indicators for this sample", ""]
    off = {r["condition"]: r for r in runs if r["source"] == "OFFICIAL"}
    full = {r["condition"]: r for r in runs if r["source"] == "FULL"}
    if off:
        L.append(f"* H1: OFFICIAL unseen_values = {off['C1']['unseen_values']} (>0: {off['C1']['unseen_values'] > 0}); "
                 f"C1 missed_valid = {off['C1']['missed_valid']} (>0: {off['C1']['missed_valid'] > 0}); "
                 f"C1 reported_missing = {off['C1']['reported_missing']} vs true_gap = {off['C1']['true_gap']}.")
        L.append(f"* H2 secondary: OFFICIAL spurious_share C1 = {fmt(off['C1']['spurious_share'])}, C2 = {fmt(off['C2']['spurious_share'])}.")
    L.append(f"* H2: FULL C2 spurious_share = {fmt(full['C2']['spurious_share'])} (>= 0.10: {full['C2']['spurious_share'] >= 0.10}).")
    for cond in ("C1", "C2"):
        xs = [r["spurious_share"] for r in groups[(cond, "UNIFORM", 1000)]]
        L.append(f"* H2 secondary: UNIFORM n=1000 {cond} median spurious_share = {fmt(statistics.median(xs))}.")
    h3 = [c for c in controls if c[0] == "CTRL-H3"][0]
    L.append(f"* H3: CTRL-H3 {h3[1]} ({h3[2]}).")
    L.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def fmt4(v):
    if isinstance(v, int):
        return str(v)
    return f"{v:.4f}" if v != int(v) else str(int(v))


if __name__ == "__main__":
    for folder in sys.argv[1:]:
        try:
            s, runs, controls = run(folder, HERE)
            print(s.id, len(runs), "runs;", ", ".join(f"{c}={r}" for c, r, _ in controls))
        except Abort as e:
            print(folder, "ABORTED:", e)
