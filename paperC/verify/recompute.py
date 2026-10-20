"""Independent recomputation of the Paper C protocol (PROTOCOL.md sections 2 to 8).

Written from PROTOCOL.md and FORMAT.md alone: it does not read or import
paperC/harness/ or latc_check. Python 3.12, standard library only.

Usage: python3.12 paperC/verify/recompute.py <spec folder> <out folder>
Writes runs.csv, controls.csv and summary.md into <out folder>.

Conditions are represented by their odometer index in D (the row number of
ground_truth.csv), so every set operation of section 6 becomes an operation on
integer sets. `naive_check` recomputes the same metrics with label tuples and
literal set algebra and is used to cross-check the fast path (see selftest.py).
"""

import ast
import csv
import hashlib
import io
import json
import math
import os
import random
import statistics
import sys

SIZES = [10, 20, 50, 100, 200, 500, 1000]
SEEDS = list(range(30))
CONDITIONS = ["C1", "C2", "C3"]

RUN_COLUMNS = [
    "sample", "source", "n", "seed", "condition",
    "n_examples", "n_distinct_examples", "examples_invalid", "examples_disagree_gt",
    "contradictory_pairs", "value_coverage", "min_value_coverage", "unseen_values",
    "reported_missing", "true_gap", "workload", "covered_valid", "valid_coverage",
    "missed_valid", "spurious_excluded", "spurious_rejected", "spurious",
    "spurious_share", "complete", "size_exceeds_valid",
]

STAT_METRICS = [
    "valid_coverage", "missed_valid", "spurious", "spurious_share", "workload",
    "contradictory_pairs", "min_value_coverage", "unseen_values", "reported_missing",
    "true_gap",
]

# category codes of a condition in D
CAT_VALID, CAT_EXCLUDED, CAT_REJECTED = 0, 1, 2


class Abort(Exception):
    pass


# ---------------------------------------------------------------- loading


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ctrl_hash(folder):
    """CTRL-HASH: every file (recursive, minus SHA256SUMS, __pycache__, *.pyc)
    listed with a matching sha256, and no listed file absent."""
    listed = {}
    with open(os.path.join(folder, "SHA256SUMS"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            digest, rest = line[:64], line[64:]
            if len(digest) != 64 or rest[:1] != " " or rest[1:2] not in (" ", "*"):
                return False, "malformed line: %r" % line
            listed[rest[2:]] = digest.lower()
    present = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), folder).replace(os.sep, "/")
            if rel == "SHA256SUMS" or fn.endswith(".pyc"):
                continue
            present.append(rel)
    problems = []
    for rel in sorted(present):
        if rel not in listed:
            problems.append("unlisted " + rel)
        elif sha256_file(os.path.join(folder, rel)) != listed[rel]:
            problems.append("mismatch " + rel)
    for rel in sorted(listed):
        if rel not in present:
            problems.append("absent " + rel)
    return not problems, "; ".join(problems) or "%d files match" % len(present)


ALLOWED_NODES = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
                 ast.Compare, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Tuple,
                 ast.List, ast.Set, ast.Name, ast.Load, ast.Constant)


def compile_predicate(pred, names):
    tree = ast.parse(pred, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise Abort("predicate node not allowed: %s in %r" % (type(node).__name__, pred))
        if isinstance(node, ast.Name) and node.id not in names:
            raise Abort("unknown name %s in %r" % (node.id, pred))
        if isinstance(node, ast.Constant) and not isinstance(node.value, str):
            raise Abort("non-string constant in %r" % pred)
    return compile(pred, "<predicate>", "eval")


class Sample:
    def __init__(self, folder):
        self.folder = folder
        with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
            self.spec = json.load(f)
        self.id = self.spec["id"]
        self.names = [a["name"] for a in self.spec["attributes"]]
        self.domains = [list(a["values"]) for a in self.spec["attributes"]]
        self.m = len(self.names)
        self.outputs = list(self.spec["output"]["values"])
        self.label_index = [{v: i for i, v in enumerate(dom)} for dom in self.domains]
        # strides for odometer index (last attribute fastest)
        self.strides = [0] * self.m
        s = 1
        for j in range(self.m - 1, -1, -1):
            self.strides[j] = s
            s *= len(self.domains[j])
        self.size_D = s

    def index(self, c):
        return sum(self.label_index[j][c[j]] * self.strides[j] for j in range(self.m))

    def tuple_at(self, i):
        out = []
        for j in range(self.m):
            d, i = divmod(i, self.strides[j])
            out.append(self.domains[j][d])
        return tuple(out)

    def odometer(self):
        # generator of D in odometer order
        idx = [0] * self.m
        for _ in range(self.size_D):
            yield tuple(self.domains[j][idx[j]] for j in range(self.m))
            j = self.m - 1
            while j >= 0:
                idx[j] += 1
                if idx[j] < len(self.domains[j]):
                    break
                idx[j] = 0
                j -= 1

    def load(self):
        """CTRL-GT and data loading. Raises Abort on failure."""
        header_expected = self.names + ["output"]
        allowed = set(self.outputs) | {"EXCLUDED", "REJECTED"}
        with open(os.path.join(self.folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        if rows[0] != header_expected:
            raise Abort("CTRL-GT: header %r" % rows[0])
        if len(rows) - 1 != self.size_D:
            raise Abort("CTRL-GT: %d rows, |D| = %d" % (len(rows) - 1, self.size_D))
        self.gt = []
        for i, (row, c) in enumerate(zip(rows[1:], self.odometer())):
            if tuple(row[:-1]) != c:
                raise Abort("CTRL-GT: row %d out of odometer order" % (i + 1))
            if row[-1] not in allowed:
                raise Abort("CTRL-GT: row %d output %r" % (i + 1, row[-1]))
            self.gt.append(row[-1])
        self.cat = bytearray(self.size_D)
        for i, y in enumerate(self.gt):
            if y == "EXCLUDED":
                self.cat[i] = CAT_EXCLUDED
            elif y == "REJECTED":
                self.cat[i] = CAT_REJECTED
        self.V_list = [i for i in range(self.size_D) if self.cat[i] == CAT_VALID]
        self.nV = len(self.V_list)
        self.nE = self.cat.count(CAT_EXCLUDED)
        self.nR = self.cat.count(CAT_REJECTED)

        with open(os.path.join(self.folder, "official_examples.csv"), encoding="utf-8", newline="") as f:
            orow = list(csv.reader(f))
        if orow[0] != ["case_id"] + header_expected:
            raise Abort("CTRL-GT: official header %r" % orow[0])
        self.official = []
        for r in orow[1:]:
            c = tuple(r[1:-1])
            for j in range(self.m):
                if c[j] not in self.label_index[j]:
                    raise Abort("CTRL-GT: official row %r uses undeclared label" % r[0])
            if r[-1] not in self.outputs:
                raise Abort("CTRL-GT: official row %r output %r" % (r[0], r[-1]))
            self.official.append((self.index(c), r[-1]))

        # S via exclusion predicates
        codes = [compile_predicate(x["predicate"], set(self.names)) for x in self.spec["exclusions"]]
        self.inS = bytearray(self.size_D)
        for i, c in enumerate(self.odometer()):
            row = dict(zip(self.names, c))
            self.inS[i] = 0 if any(eval(code, {"__builtins__": {}}, row) for code in codes) else 1
        self.nS = sum(self.inS)
        self.excl_disagree = sum(1 for i in range(self.size_D)
                                 if (self.cat[i] == CAT_EXCLUDED) != (self.inS[i] == 0))
        # category counts inside S and inside D
        self.cnt_D = [self.cat.count(k) for k in range(3)]
        self.cnt_S = [0, 0, 0]
        for i in range(self.size_D):
            if self.inS[i]:
                self.cnt_S[self.cat[i]] += 1


# ---------------------------------------------------------------- sources


def source_official(s):
    return list(s.official)


def source_full(s):
    return [(i, s.gt[i]) for i in s.V_list]


def source_uniform(s, n, seed):
    rng = random.Random(seed)
    drawn = rng.choices(s.V_list, k=n)
    return [(i, s.gt[i]) for i in drawn]


def source_zipf(s, n, seed):
    rng = random.Random(seed)
    perm = list(s.V_list)
    rng.shuffle(perm)
    drawn = rng.choices(perm, weights=[1.0 / (k ** 1.0) for k in range(1, len(perm) + 1)], k=n)
    return [(i, s.gt[i]) for i in drawn]


# ---------------------------------------------------------------- metrics


def observed_product(s, X):
    """Indices of the product of the observed values (C1's enumeration space)."""
    seen = [set() for _ in range(s.m)]
    for i in X:
        t = i
        for j in range(s.m):
            d, t = divmod(t, s.strides[j])
            seen[j].add(d)
    idx = [0]
    for j in range(s.m):
        offs = [d * s.strides[j] for d in sorted(seen[j])]
        idx = [a + b for a in idx for b in offs]
    return idx, seen


def run_metrics(s, examples, condition):
    X_list = [i for i, _ in examples]
    X = set(X_list)
    cat = s.cat
    r = {}
    r["n_examples"] = len(X_list)
    r["n_distinct_examples"] = len(X)
    r["examples_invalid"] = sum(1 for i in X_list if cat[i] != CAT_VALID)
    r["examples_disagree_gt"] = sum(1 for i, y in examples if y != s.gt[i])
    groups = {}
    for i, y in examples:
        groups.setdefault(i, {}).setdefault(y, 0)
        groups[i][y] += 1
    cp = 0
    for ys in groups.values():
        tot = sum(ys.values())
        cp += tot * (tot - 1) // 2 - sum(k * (k - 1) // 2 for k in ys.values())
    r["contradictory_pairs"] = cp
    P1, seen = observed_product(s, X)
    parts, ratios, unseen = [], [], 0
    for j in range(s.m):
        parts.append("%s=%d/%d" % (s.names[j], len(seen[j]), len(s.domains[j])))
        ratios.append(len(seen[j]) / len(s.domains[j]))
        unseen += len(s.domains[j]) - len(seen[j])
    r["value_coverage"] = ";".join(parts)
    r["min_value_coverage"] = min(ratios)
    r["unseen_values"] = unseen

    # category counts of X, and of X within S
    cX = [0, 0, 0]
    cXS = [0, 0, 0]
    for i in X:
        cX[cat[i]] += 1
        if s.inS[i]:
            cXS[cat[i]] += 1
    if condition == "C1":
        cP = [0, 0, 0]
        for i in P1:
            cP[cat[i]] += 1
        # X is contained in P1 by construction
        cG = [cP[k] - cX[k] for k in range(3)]
        r["reported_missing"] = len(P1) - len(X_list)
    elif condition == "C2":
        cG = [s.cnt_D[k] - cX[k] for k in range(3)]
        r["reported_missing"] = s.size_D - len(X_list)
    else:
        cG = [s.cnt_S[k] - cXS[k] for k in range(3)]
        r["reported_missing"] = s.nS - len(X_list)
    nG = sum(cG)
    r["true_gap"] = s.nV - cX[CAT_VALID]
    r["workload"] = nG
    covered = cX[CAT_VALID] + cG[CAT_VALID]
    r["covered_valid"] = covered
    r["valid_coverage"] = covered / s.nV if s.nV else 1.0
    r["missed_valid"] = s.nV - covered
    r["spurious_excluded"] = cG[CAT_EXCLUDED]
    r["spurious_rejected"] = cG[CAT_REJECTED]
    r["spurious"] = cG[CAT_EXCLUDED] + cG[CAT_REJECTED]
    r["spurious_share"] = r["spurious"] / nG if nG else 0.0
    r["complete"] = 1 if (r["valid_coverage"] == 1 and r["spurious"] == 0) else 0
    return r


def naive_metrics(s, examples, condition):
    """Literal set-algebra version over label tuples, for cross-checking."""
    if not hasattr(s, "_naive"):
        D = list(s.odometer())
        GT = dict(zip(D, s.gt))
        E = {c for c in D if GT[c] == "EXCLUDED"}
        R = {c for c in D if GT[c] == "REJECTED"}
        V = set(D) - E - R
        S = {c for c, ins in zip(D, s.inS) if ins}
        s._naive = (D, E, R, V, S)
    D, E, R, V, S = s._naive
    ex = [(s.tuple_at(i), y) for i, y in examples]
    X_list = [c for c, _ in ex]
    X = set(X_list)
    if condition == "C1":
        obs = []
        for j in range(s.m):
            o = []
            for c in X_list:
                if c[j] not in o:
                    o.append(c[j])
            obs.append(o)
        import itertools
        G_list = [c for c in itertools.product(*obs) if c not in X]
        rm = math.prod(len(o) for o in obs) - len(ex)
    elif condition == "C2":
        G_list = [c for c in D if c not in X]
        rm = len(D) - len(ex)
    else:
        G_list = [c for c in D if c in S and c not in X]
        rm = len(S) - len(ex)
    G = set(G_list)
    cov = len(V & (X | G))
    sp = len(G & (E | R))
    return {
        "reported_missing": rm, "true_gap": len(V - X), "workload": len(G_list),
        "covered_valid": cov, "missed_valid": len(V - (X | G)),
        "spurious_excluded": len(G & E), "spurious_rejected": len(G & R), "spurious": sp,
        "spurious_share": sp / len(G) if G else 0.0,
        "valid_coverage": cov / len(V) if V else 1.0,
    }


def plant(s, examples):
    """CTRL-PLANT on one example set. Returns (passed, v, expected, c2_count, c1_count)."""
    counts = [0] * len(s.domains[0])
    for i, _ in examples:
        counts[i // s.strides[0]] += 1
    vd = min(range(len(counts)), key=lambda d: (counts[d], d))
    remaining = [(i, y) for i, y in examples if i // s.strides[0] != vd]
    Xr = set(i for i, _ in remaining)
    lo, hi = vd * s.strides[0], (vd + 1) * s.strides[0]
    expected = hi - lo  # = prod_{j>=2} |D_j|
    # C2 on the remaining rows: G = D \ Xr; count of block v inside G
    c2 = sum(1 for i in range(lo, hi) if i not in Xr)
    P1, _ = observed_product(s, Xr)
    c1 = sum(1 for i in P1 if lo <= i < hi and i not in Xr)
    return c2 == expected, s.domains[0][vd], expected, c2, c1


# ---------------------------------------------------------------- statistics


def pct(xs, p):
    xs = sorted(xs)
    N = len(xs)
    h = (N - 1) * p
    lo = math.floor(h)
    hi_val = xs[lo + 1] if lo + 1 < N else xs[lo]
    return xs[lo] + (h - lo) * (hi_val - xs[lo])


def wilson(k, N):
    z = statistics.NormalDist().inv_cdf(0.975)
    p = k / N
    centre = (p + z * z / (2 * N)) / (1 + z * z / N)
    half = z * math.sqrt(p * (1 - p) / N + z * z / (4 * N * N)) / (1 + z * z / N)
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------- main


def fmt(v):
    if isinstance(v, float):
        return repr(v)
    return str(v)


def main(folder, out):
    os.makedirs(out, exist_ok=True)
    controls = []
    ok, detail = ctrl_hash(folder)
    controls.append(("CTRL-HASH", "pass" if ok else "fail", detail))
    if not ok:
        raise Abort("CTRL-HASH failed: " + detail)
    s = Sample(folder)
    s.load()
    controls.append(("CTRL-GT", "pass", "%d rows in odometer order" % s.size_D))
    controls.append(("CTRL-EXCL", "pass" if s.excl_disagree == 0 else "fail",
                     "%d disagreeing rows" % s.excl_disagree))

    example_sets = []
    if s.official:
        example_sets.append(("OFFICIAL", len(s.official), "-", source_official(s)))
    example_sets.append(("FULL", s.nV, "-", source_full(s)))
    for src, fn in (("UNIFORM", source_uniform), ("ZIPF", source_zipf)):
        for n in SIZES:
            for seed in SEEDS:
                example_sets.append((src, n, seed, fn(s, n, seed)))

    runs = []
    plant_fail, plant_rows = 0, []
    for src, n, seed, ex in example_sets:
        for cond in CONDITIONS:
            r = {"sample": s.id, "source": src, "n": n, "seed": seed, "condition": cond}
            r.update(run_metrics(s, ex, cond))
            r["size_exceeds_valid"] = 1 if (src in ("UNIFORM", "ZIPF") and n > s.nV) else 0
            runs.append(r)
        p = plant(s, ex)
        plant_rows.append((src, n, seed) + p)
        if not p[0]:
            plant_fail += 1
    controls.append(("CTRL-PLANT", "pass" if plant_fail == 0 else "fail",
                     "%d of %d example sets fail" % (plant_fail, len(example_sets))))
    c3 = [r for r in runs if r["condition"] == "C3"]
    bad = [r for r in c3 if not (r["valid_coverage"] == 1 and r["spurious"] == 0)]
    controls.append(("CTRL-H3", "pass" if not bad else "fail",
                     "%d of %d C3 runs fail; max spurious_rejected %d" %
                     (len(bad), len(c3), max([r["spurious_rejected"] for r in c3] or [0]))))
    if s.id == "CTRL-NUR":
        full_c1 = [r for r in runs if r["source"] == "FULL" and r["condition"] == "C1"][0]
        ok = full_c1["reported_missing"] == 0 and full_c1["workload"] == 0
        controls.append(("CTRL-FULL", "pass" if ok else "fail", ""))

    with open(os.path.join(out, "runs.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(RUN_COLUMNS)
        for r in runs:
            w.writerow([fmt(r[k]) for k in RUN_COLUMNS])
    with open(os.path.join(out, "controls.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["control", "result", "detail"])
        for c in controls:
            w.writerow(c)
    with open(os.path.join(out, "plant.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["source", "n", "seed", "pass", "v", "expected", "c2_generated_v", "c1_generated_v"])
        for p in plant_rows:
            w.writerow([p[0], p[1], p[2], int(p[3]), p[4], p[5], p[6], p[7]])
    write_summary(s, runs, controls, out)
    return s, runs, controls


def write_summary(s, runs, controls, out):
    L = []
    L.append("# %s: independent recomputation summary" % s.id)
    L.append("")
    L.append("Produced by `paperC/verify/recompute.py` (independent of paperC/harness and latc_check).")
    L.append("")
    L.append("|D| = %d, |V| = %d, |E| = %d, |R| = %d, |S| = %d; OFFICIAL rows = %d." %
             (s.size_D, s.nV, s.nE, s.nR, s.nS, len(s.official)))
    if not s.official:
        L.append("OFFICIAL skipped: official_examples.csv has no data rows.")
    big = [n for n in SIZES if n > s.nV]
    if big:
        L.append("Sizes exceeding the valid space: %s." % ", ".join(map(str, big)))
    L.append("")
    L.append("## Controls")
    L.append("")
    L.append("| control | result | detail |")
    L.append("|---|---|---|")
    for c in controls:
        L.append("| %s | %s | %s |" % c)
    L.append("")
    L.append("## OFFICIAL and FULL (single runs)")
    L.append("")
    cols = ["source", "condition", "n_examples", "unseen_values", "reported_missing", "true_gap",
            "workload", "missed_valid", "valid_coverage", "spurious", "spurious_share", "complete"]
    L.append("| " + " | ".join(cols) + " |")
    L.append("|" + "---|" * len(cols))
    for r in runs:
        if r["source"] in ("OFFICIAL", "FULL"):
            L.append("| " + " | ".join(fmt(r[k]) for k in cols) + " |")
    L.append("")
    L.append("## UNIFORM and ZIPF over 30 seeds")
    L.append("")
    L.append("Each cell: mean / median / p2.5 / p97.5 (Hyndman and Fan type 7). "
             "complete: share of seeds and Wilson 95% interval.")
    L.append("")
    hdr = ["condition", "source", "n"] + STAT_METRICS + ["complete share [Wilson 95%]"]
    L.append("| " + " | ".join(hdr) + " |")
    L.append("|" + "---|" * len(hdr))
    for cond in CONDITIONS:
        for src in ("UNIFORM", "ZIPF"):
            for n in SIZES:
                rs = [r for r in runs if r["condition"] == cond and r["source"] == src and r["n"] == n]
                cells = [cond, src, str(n)]
                for mtr in STAT_METRICS:
                    xs = [r[mtr] for r in rs]
                    cells.append("%s / %s / %s / %s" % (fmt(statistics.mean(xs)), fmt(statistics.median(xs)),
                                                         fmt(pct(xs, 0.025)), fmt(pct(xs, 0.975))))
                k = sum(r["complete"] for r in rs)
                lo, hi = wilson(k, len(rs))
                cells.append("%s [%s, %s]" % (fmt(k / len(rs)), fmt(lo), fmt(hi)))
                L.append("| " + " | ".join(cells) + " |")
    L.append("")
    L.append("## Hypothesis indicators for this sample")
    L.append("")
    off = {r["condition"]: r for r in runs if r["source"] == "OFFICIAL"}
    full = {r["condition"]: r for r in runs if r["source"] == "FULL"}
    if off:
        L.append("* H1: OFFICIAL unseen_values = %d (> 0: %s); C1 missed_valid = %d (> 0: %s); "
                 "C1 reported_missing = %d versus true_gap = %d." %
                 (off["C1"]["unseen_values"], off["C1"]["unseen_values"] > 0,
                  off["C1"]["missed_valid"], off["C1"]["missed_valid"] > 0,
                  off["C1"]["reported_missing"], off["C1"]["true_gap"]))
        L.append("* H2 secondary: OFFICIAL spurious_share C1 = %s, C2 = %s." %
                 (fmt(off["C1"]["spurious_share"]), fmt(off["C2"]["spurious_share"])))
    L.append("* H2: FULL C2 spurious_share = %s (>= 0.10: %s)." %
             (fmt(full["C2"]["spurious_share"]), full["C2"]["spurious_share"] >= 0.10))
    for cond in ("C1", "C2"):
        xs = [r["spurious_share"] for r in runs if r["source"] == "UNIFORM" and r["n"] == 1000 and r["condition"] == cond]
        L.append("* H2 secondary: UNIFORM n = 1000 median %s spurious_share = %s." % (cond, fmt(statistics.median(xs))))
    h3 = [c for c in controls if c[0] == "CTRL-H3"][0]
    L.append("* H3: CTRL-H3 %s (%s); R non-empty: %s." % (h3[1], h3[2], s.nR > 0))
    L.append("")
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    try:
        main(sys.argv[1], sys.argv[2])
    except Abort as e:
        print("ABORT:", e)
        sys.exit(2)
