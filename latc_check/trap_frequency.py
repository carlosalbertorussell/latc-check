"""How often does the observed-domain trap occur naturally?

LATC takes each attribute's cardinality from the values observed in the
experts' example rows T0.  If a declared value of some attribute appears in no
example row, the observed product is smaller than the declared product, LATC's
Corollaries 1/3 are evaluated on the wrong space, and every state that carries
the unobserved value is silently missing.  This module computes

    P(trap | k) = P(a set of k example rows misses at least one declared value
                    of at least one attribute)

and the number of states left outside the observed product,
``|D| - prod_i m_i`` (``m_i`` = number of observed values of attribute i).

Uniform sampling without replacement (exact)
--------------------------------------------
T0 is a uniformly random k-subset of D = D_1 x ... x D_n (no constraint).  For
excluded value sets S_i subset of D_i the number of states avoiding all of them
is N_S = prod_i (|D_i| - |S_i|), and P(all k rows avoid them) =
C(N_S, k) / C(|D|, k).  By inclusion-exclusion

    P(no trap) = sum over (S_1..S_n) of (-1)^(sum |S_i|) C(N_S, k) / C(|D|, k)

(the empty choice contributes 1).  Terms depend only on the sizes |S_i|, and
attributes with the same domain size are interchangeable, so the sum is taken
over, for each group of c attributes of size d, the counts c_0..c_{d-1} of
attributes with |S_i| = j (multiplicity multinomial(c; c_j) * prod C(d, j)^c_j).
Terms with N_S equal are merged; everything is integer arithmetic, divided once
by C(|D|, k), so the result is an exact ``Fraction`` (no cancellation error).

Expected missing states.  By symmetry under per-attribute relabelling,
E[prod m_i] = |D| * q, where q = P(the n values of one fixed state are all
observed) = sum_T (-1)^|T| C(N_T, k) / C(|D|, k) over attribute subsets T, with
N_T = prod_{i in T} (d_i - 1) prod_{i not in T} d_i.  E[missing] = |D| (1 - q);
missing = 0 without a trap, so E[missing | trap] = E[missing] / P(trap).

With replacement (approximation, and any product distribution)
--------------------------------------------------------------
With k i.i.d. rows from a product distribution the attributes are independent,
so P(no trap) = prod_i P(all values of attribute i seen in k draws), and each
factor is the coupon-collector sum  sum_{S subset D_i} (-1)^|S| (1 - p_i(S))^k.
E[prod m_i] = prod_i sum_v (1 - (1 - p_iv)^k).

Rule of thumb
-------------
P(value v of attribute i missed) <= (1 - 1/d_i)^k (with or without
replacement), so the union bound gives P(trap) <= sum_i d_i (1 - 1/d_i)^k <=
V exp(-k / d_max) with V = sum_i d_i.  Hence k >= d_max * ln(V / alpha) rows
are enough for P(trap) <= alpha.

Non-uniform sampling (Monte Carlo, illustrative)
------------------------------------------------
Two transparent models of "experts write typical cases": (a) rows of the real
table drawn without replacement with weight proportional to the empirical
frequency of the row's class; (b) values drawn independently per attribute
from a Zipf(s=1) law over the declared value order, duplicate states rejected
(= weighted sampling without replacement, weight prod_i p_i(v_i)).  Each
Monte Carlo draw samples sequentially until every declared value has been seen
(the cover time T); a prefix of a sequential sample is a sample of that size,
so trap(k) = [T > k] for every k from one draw.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import os
import platform
import random
import sys
import time
from collections import Counter
from fractions import Fraction
from statistics import mean

SEED = 20210101
KS = (5, 8, 10, 17, 20, 30, 50, 100, 200, 500)
ALPHAS = (0.05, 0.01)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "results", "trap_frequency")


# -- exact, uniform without replacement ---------------------------------------------------

def _groups(domains) -> list[tuple[int, int]]:
    """[(domain size d, number of attributes with that size)]."""
    return sorted(Counter(domains).items())


def _compositions(total: int, parts: int):
    """All tuples of `parts` non-negative ints summing to `total`."""
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            yield (first,) + rest


def _multinomial(counts) -> int:
    out, n = 1, 0
    for c in counts:
        n += c
        out *= math.comb(n, c)
    return out


def avoid_coefficients(domains) -> dict[int, int]:
    """{N_S: signed multiplicity} of the inclusion-exclusion sum for P(no trap).

    Excluding a whole domain (|S_i| = d_i) gives N_S = 0, whose term vanishes
    for k >= 1, so |S_i| ranges over 0..d_i-1.
    """
    coef = {1: 1}
    for d, c in _groups(domains):
        part: dict[int, int] = {}
        for counts in _compositions(c, d):          # counts[j] = attributes with |S_i| = j
            mult = _multinomial(counts)
            factor, sign = 1, 0
            for j, cj in enumerate(counts):
                mult *= math.comb(d, j) ** cj
                factor *= (d - j) ** cj
                sign += j * cj
            part[factor] = part.get(factor, 0) + (-1) ** sign * mult
        new: dict[int, int] = {}
        for a, x in coef.items():
            for b, y in part.items():
                new[a * b] = new.get(a * b, 0) + x * y
        coef = {k: v for k, v in new.items() if v}
    return coef


def p_trap_exact(domains, k: int, coef: dict | None = None) -> Fraction:
    """Exact P(trap) for a uniform k-subset of the full product space."""
    n_states = math.prod(domains)
    if not 0 <= k <= n_states:
        raise ValueError("k must be between 0 and |D|")
    coef = coef if coef is not None else avoid_coefficients(domains)
    num = sum(v * math.comb(ns, k) for ns, v in coef.items())
    return 1 - Fraction(num, math.comb(n_states, k))


def _all_observed_coefficients(domains) -> dict[int, int]:
    """{N_T: signed multiplicity} for q = P(the values of one fixed state are all observed)."""
    coef = {1: 1}
    for d, c in _groups(domains):
        part = {(d - 1) ** t * d ** (c - t): (-1) ** t * math.comb(c, t) for t in range(c + 1)}
        new: dict[int, int] = {}
        for a, x in coef.items():
            for b, y in part.items():
                new[a * b] = new.get(a * b, 0) + x * y
        coef = {k: v for k, v in new.items() if v}
    return coef


def expected_missing_exact(domains, k: int) -> Fraction:
    """Exact E[|D| - prod m_i] for a uniform k-subset (0 when there is no trap)."""
    n_states = math.prod(domains)
    coef = _all_observed_coefficients(domains)
    q = Fraction(sum(v * math.comb(nt, k) for nt, v in coef.items()), math.comb(n_states, k))
    return n_states * (1 - q)


# -- with replacement / product distributions ---------------------------------------------

def uniform_probs(domains) -> list[list[Fraction]]:
    return [[Fraction(1, d)] * d for d in domains]


def zipf_probs(domains, s: int = 1) -> list[list[Fraction]]:
    """Zipf(s) over the declared value order: p_j proportional to 1/j^s (exact rationals)."""
    out = []
    for d in domains:
        w = [Fraction(1, j ** s) for j in range(1, d + 1)]
        tot = sum(w)
        out.append([x / tot for x in w])
    return out


def _cover_prob(p: list[Fraction], k: int) -> Fraction:
    """P(all values seen in k i.i.d. draws from p): inclusion-exclusion over subsets."""
    tot = Fraction(0)
    for r in range(len(p) + 1):
        for sub in itertools.combinations(p, r):
            tot += (-1) ** r * (1 - sum(sub)) ** k
    return tot


def p_trap_with_replacement(probs, k: int) -> Fraction:
    """P(trap) for k i.i.d. rows from the product distribution `probs` (exact)."""
    return 1 - math.prod((_cover_prob(p, k) for p in probs), start=Fraction(1))


def expected_missing_with_replacement(probs, k: int) -> Fraction:
    n_states = math.prod(len(p) for p in probs)
    return n_states - math.prod((sum(1 - (1 - x) ** k for x in p) for p in probs), start=Fraction(1))


# -- bounds and thresholds -----------------------------------------------------------------

def union_bound(domains, k: int) -> float:
    return sum(d * (1 - 1 / d) ** k for d in domains)


def rule_of_thumb_k(domains, alpha: float) -> int:
    """Smallest integer k >= d_max * ln(sum d_i / alpha): sufficient for P(trap) <= alpha."""
    return math.ceil(max(domains) * math.log(sum(domains) / alpha))


def smallest_k(pred, lo: int, hi: int) -> int | None:
    """Smallest k in [lo, hi] with pred(k) True, for pred monotone (False..False True..True)."""
    top, hi = hi, min(lo, hi)                     # galloping: avoid evaluating huge k
    while not pred(hi):
        if hi == top:
            return None
        lo, hi = hi + 1, min(2 * hi, top)
    while lo < hi:
        mid = (lo + hi) // 2
        if pred(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def thresholds_exact(domains, alphas=ALPHAS) -> dict:
    """Smallest k with P(trap) <= alpha: exact, with replacement, union bound, rule of thumb."""
    n_states = math.prod(domains)
    coef = avoid_coefficients(domains)
    probs = uniform_probs(domains)
    hi_wr = 10 * rule_of_thumb_k(domains, min(alphas))
    out = {}
    for a in alphas:
        out[str(a)] = {
            "exact_without_replacement": smallest_k(lambda k: p_trap_exact(domains, k, coef) <= a, 1, n_states),
            "with_replacement": smallest_k(lambda k: p_trap_with_replacement(probs, k) <= a, 1, hi_wr),
            "union_bound": smallest_k(lambda k: union_bound(domains, k) <= a, 1, hi_wr),
            "rule_of_thumb_dmax_ln_V_over_alpha": rule_of_thumb_k(domains, a),
        }
    return out


# -- brute force (tests) -------------------------------------------------------------------

def brute_force(domains, k: int) -> tuple[Fraction, Fraction]:
    """(P(trap), E[missing]) by enumerating every k-subset; tiny spaces only."""
    states = list(itertools.product(*(range(d) for d in domains)))
    n_states = len(states)
    traps = missing = total = 0
    for sub in itertools.combinations(states, k):
        obs = [len({s[i] for s in sub}) for i in range(len(domains))]
        prod_obs = math.prod(obs)
        traps += prod_obs < n_states
        missing += n_states - prod_obs
        total += 1
    return Fraction(traps, total), Fraction(missing, total)


# -- Monte Carlo ---------------------------------------------------------------------------

class UniformSampler:
    """Distinct uniform states by rejection (with_replacement=True: i.i.d. states)."""

    def __init__(self, domains, rng, with_replacement=False):
        self.domains, self.rng, self.wr = list(domains), rng, with_replacement

    def reset(self):
        self.seen = set()

    def next(self):
        rr = self.rng.randrange
        while True:
            s = tuple(rr(d) for d in self.domains)
            if self.wr or s not in self.seen:
                self.seen.add(s)
                return s


class ZipfSampler(UniformSampler):
    """Per-attribute Zipf(s) values over the declared order; distinct states unless with_replacement."""

    def __init__(self, domains, rng, s=1, with_replacement=False):
        super().__init__(domains, rng, with_replacement)
        self.cum = [list(itertools.accumulate(1 / j ** s for j in range(1, d + 1))) for d in domains]
        self.pops = [list(range(d)) for d in domains]

    def next(self):
        ch = self.rng.choices
        while True:
            s = tuple(ch(p, cum_weights=c)[0] for p, c in zip(self.pops, self.cum))
            if self.wr or s not in self.seen:
                self.seen.add(s)
                return s


class ClassWeightedSampler:
    """Rows of a real table without replacement, weight proportional to the row's class frequency."""

    def __init__(self, table, rng):
        self.rng = rng
        index = [{v: j for j, v in enumerate(a.domain)} for a in table.attributes]
        by_class: dict[str, list] = {}
        for r in table.rows:
            by_class.setdefault(r.outcome, []).append(tuple(ix[v] for ix, v in zip(index, r.condition)))
        self.classes = sorted(by_class)
        self.rows = [by_class[c] for c in self.classes]
        self.weight = [len(x) for x in self.rows]          # class frequency
        self.domains = [a.card for a in table.attributes]

    def reset(self):
        self.left = [list(x) for x in self.rows]

    def next(self):
        w = [len(l) * wc for l, wc in zip(self.left, self.weight)]
        c = self.rng.choices(range(len(w)), weights=w)[0]
        rows = self.left[c]
        j = self.rng.randrange(len(rows))
        rows[j], rows[-1] = rows[-1], rows[j]
        return rows.pop()


def monte_carlo(sampler, domains, ks, draws: int, cap: int | None = None) -> dict:
    """Per k: trap rate, its standard error, mean missing states; and the cover times."""
    n_states = math.prod(domains)
    n_values = sum(domains)
    cap = cap or n_states
    kset = set(ks)
    traps = {k: 0 for k in ks}
    miss = {k: 0 for k in ks}
    miss_sq = {k: 0 for k in ks}
    covers = []
    for _ in range(draws):
        sampler.reset()
        obs = [set() for _ in domains]
        seen = t = 0
        while seen < n_values and t < cap:
            s = sampler.next()
            t += 1
            for o, v in zip(obs, s):
                if v not in o:
                    o.add(v)
                    seen += 1
            if t in kset and seen < n_values:
                m = n_states - math.prod(len(o) for o in obs)
                traps[t] += 1
                miss[t] += m
                miss_sq[t] += m * m
        covers.append(t if seen == n_values else None)
    out = {}
    for k in ks:
        p = traps[k] / draws
        mm = miss[k] / draws
        var = max(miss_sq[k] / draws - mm * mm, 0.0)
        out[str(k)] = {"p_trap": p, "se": math.sqrt(p * (1 - p) / draws), "traps": traps[k],
                       "mean_missing": mm, "mean_missing_se": math.sqrt(var / draws),
                       "mean_missing_given_trap": (miss[k] / traps[k]) if traps[k] else None}
    return {"draws": draws, "per_k": out, "cover_times": covers}


def mc_thresholds(covers, alphas=ALPHAS) -> dict:
    """Smallest k with (share of draws whose cover time exceeds k) <= alpha."""
    n = len(covers)
    finite = sorted(c for c in covers if c is not None)
    out = {}
    for a in alphas:
        allowed = math.floor(a * n + 1e-9)                    # draws allowed to exceed k
        idx = n - allowed - 1                                 # k = (n - allowed)-th smallest cover time
        out[str(a)] = finite[idx] if idx < len(finite) else None
    return out


# -- binomial helpers ----------------------------------------------------------------------

def binom_pmf(n: int, x: int, p: float) -> float:
    return math.comb(n, x) * p ** x * (1 - p) ** (n - x)


def binom_cdf(n: int, x: int, p: float) -> float:
    return sum(binom_pmf(n, i, p) for i in range(x + 1))


def clopper_pearson(x: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    a = (1 - conf) / 2

    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid):
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
    lower = 0.0 if x == 0 else solve(lambda p: 1 - binom_cdf(n, x - 1, p) >= a)
    upper = 1.0 if x == n else solve(lambda p: binom_cdf(n, x, p) <= a)
    return lower, upper


# -- experiment ----------------------------------------------------------------------------

def spaces():
    from . import datasets
    car = datasets.car()
    nursery = datasets.nursery()
    return [
        {"key": "pension", "title": "Pension worked example", "domains": [2, 2, 2, 3], "table": None},
        {"key": "car", "title": "UCI Car Evaluation", "domains": [a.card for a in car.attributes], "table": car},
        {"key": "nursery", "title": "UCI Nursery", "domains": [a.card for a in nursery.attributes],
         "table": nursery},
        {"key": "4^12", "title": "12 attributes x 4 values", "domains": [4] * 12, "table": None},
    ]


VALIDATION = [  # (domains, ks) for exact vs Monte Carlo on small spaces
    ([3, 4], [2, 3, 4, 5, 6, 8]),
    ([2, 3, 4], [3, 4, 6, 8, 12]),
    ([2, 2, 2, 3], [3, 4, 5, 8, 10]),
    ([4, 4, 4, 3, 3, 3], [5, 10, 17, 30]),
]


def _f(x: Fraction | None) -> float | None:
    return None if x is None else float(x)


def _log10(x: Fraction) -> float | None:
    return None if x <= 0 else math.log10(x.numerator) - math.log10(x.denominator)


def run(draws: int = 20000, seed: int = SEED, validation_draws: int = 20000) -> dict:
    t_start = time.perf_counter()
    res = {"meta": {"seed": seed, "draws": draws, "validation_draws": validation_draws,
                    "python": sys.version.split()[0], "platform": platform.platform(), "ks": list(KS),
                    "alphas": list(ALPHAS)}}

    # 1. validation: exact vs brute force (tiny) and vs Monte Carlo
    val = []
    for domains, ks in VALIDATION:
        rng = random.Random(f"{seed}:validate:{domains}")
        mc = monte_carlo(UniformSampler(domains, rng), domains, ks, validation_draws)
        rng_wr = random.Random(f"{seed}:validate-wr:{domains}")
        mc_wr = monte_carlo(UniformSampler(domains, rng_wr, with_replacement=True), domains, ks,
                            validation_draws, cap=10 ** 6)
        probs = uniform_probs(domains)
        for k in ks:
            ex = float(p_trap_exact(domains, k))
            em = float(expected_missing_exact(domains, k))
            wr = float(p_trap_with_replacement(probs, k))
            wrm = float(expected_missing_with_replacement(probs, k))
            m, mw = mc["per_k"][str(k)], mc_wr["per_k"][str(k)]
            row = {"domains": domains, "k": k, "exact_p": ex, "mc_p": m["p_trap"], "mc_se": m["se"],
                   "z_p": (m["p_trap"] - ex) / m["se"] if m["se"] else 0.0,
                   "exact_missing": em, "mc_missing": m["mean_missing"], "mc_missing_se": m["mean_missing_se"],
                   "z_missing": (m["mean_missing"] - em) / m["mean_missing_se"] if m["mean_missing_se"] else 0.0,
                   "wr_p": wr, "mc_wr_p": mw["p_trap"], "mc_wr_se": mw["se"],
                   "z_wr_p": (mw["p_trap"] - wr) / mw["se"] if mw["se"] else 0.0,
                   "wr_missing": wrm, "mc_wr_missing": mw["mean_missing"]}
            if math.prod(domains) <= 24 and math.comb(math.prod(domains), k) <= 1_000_000:
                bp, bm = brute_force(domains, k)
                row["brute_p"], row["brute_missing"] = float(bp), float(bm)
                row["brute_equal"] = (bp == p_trap_exact(domains, k) and bm == expected_missing_exact(domains, k))
            val.append(row)
    res["validation"] = val
    print(f"validation done ({time.perf_counter() - t_start:.1f}s)", flush=True)

    # 2./3. the four spaces
    out = {}
    for sp in spaces():
        domains, key = sp["domains"], sp["key"]
        n_states = math.prod(domains)
        ks = [k for k in KS if k <= n_states]
        coef = avoid_coefficients(domains)
        probs = uniform_probs(domains)
        zprobs = zipf_probs(domains)
        rows = {}
        for k in ks:
            p = p_trap_exact(domains, k, coef)
            m = expected_missing_exact(domains, k)
            pw = p_trap_with_replacement(probs, k)
            pz = p_trap_with_replacement(zprobs, k)
            rows[str(k)] = {"p_trap_exact": _f(p), "log10_p_trap_exact": _log10(p),
                            "expected_missing": _f(m),
                            "expected_missing_given_trap": _f(m / p) if p else None,
                            "p_trap_with_replacement": _f(pw), "union_bound": min(union_bound(domains, k), 1.0),
                            "zipf_with_replacement_exact": _f(pz),
                            "zipf_expected_missing_with_replacement": _f(expected_missing_with_replacement(zprobs, k))}
        entry = {"title": sp["title"], "domains": domains, "states": n_states, "declared_values": sum(domains),
                 "ks": ks, "uniform": rows, "thresholds_uniform": thresholds_exact(domains),
                 "monte_carlo": {}}
        models = [("uniform", lambda r: UniformSampler(domains, r)),
                  ("zipf_s1", lambda r: ZipfSampler(domains, r, s=1))]
        if sp["table"] is not None:
            models.append(("class_frequency", lambda r, t=sp["table"]: ClassWeightedSampler(t, r)))
            entry["class_counts"] = dict(Counter(r.outcome for r in sp["table"].rows))
        for name, make in models:
            t0 = time.perf_counter()
            mc = monte_carlo(make(random.Random(f"{seed}:{key}:{name}")), domains, ks, draws)
            covers = mc.pop("cover_times")
            fin = [c for c in covers if c is not None]
            mc["thresholds"] = mc_thresholds(covers)
            mc["mean_cover_time"] = mean(fin) if fin else None
            mc["max_cover_time"] = max(fin) if fin else None
            mc["seconds"] = round(time.perf_counter() - t0, 2)
            entry["monte_carlo"][name] = mc
            print(f"  {key} {name}: {mc['seconds']}s", flush=True)
        if key == "pension":
            from .examples import PENSION_ATTRS, PENSION_T0
            obs = [len({r.condition[i] for r in PENSION_T0}) for i in range(len(PENSION_ATTRS))]
            entry["published_t0"] = {"rows": len(PENSION_T0), "observed_values": obs,
                                     "declared_values": [a.card for a in PENSION_ATTRS],
                                     "trap": math.prod(obs) < n_states}
        out[key] = entry
    res["spaces"] = out

    # consistency with results/datasets (20 uniform 1% samples per dataset)
    cons = {}
    path = os.path.join(REPO, "results", "datasets")
    for key in ("car", "nursery"):
        fp = os.path.join(path, f"uci_{key}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            rr = json.load(f)["random_removal"]["0.01"]
        k, n, x = rr["t0_rows"], rr["seeds"], rr["runs_with_unobserved_value"]
        domains = out[key]["domains"]
        p = float(p_trap_exact(domains, k))
        lo, hi = clopper_pearson(x, n)
        cons[key] = {"k": k, "samples": n, "samples_with_trap": x, "exact_p_trap": p,
                     "expected_traps": n * p, "binomial_p_of_observed_count": binom_pmf(n, x, p),
                     "binomial_p_at_least_observed": 1 - binom_cdf(n, x - 1, p) if x else 1.0,
                     "clopper_pearson_95": [lo, hi], "exact_inside_ci": lo <= p <= hi,
                     "observed_mean_unobserved_values": rr["mean_unobserved_declared_values"]}
    res["consistency_with_datasets"] = cons
    res["meta"]["seconds"] = round(time.perf_counter() - t_start, 1)
    return res


# -- output --------------------------------------------------------------------------------

def _fmt_p(p, logp=None) -> str:
    if p is None:
        return "–"
    if p == 0:
        return f"1e{logp:.0f}" if logp is not None else "0"
    if p >= 0.001:
        return f"{p:.4f}"
    return f"{p:.2e}"


def write_outputs(res: dict, out_dir: str = OUT) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    fields = ["space", "domains", "states", "k", "p_trap_exact", "log10_p_trap_exact", "expected_missing",
              "expected_missing_given_trap", "p_trap_with_replacement", "union_bound",
              "mc_uniform_p", "mc_uniform_se", "mc_zipf_p", "mc_zipf_se", "mc_zipf_mean_missing",
              "mc_class_p", "mc_class_se", "mc_class_mean_missing", "zipf_with_replacement_exact"]
    with open(os.path.join(out_dir, "trap_frequency.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key, sp in res["spaces"].items():
            mc = sp["monte_carlo"]
            for k in sp["ks"]:
                u = sp["uniform"][str(k)]
                row = {"space": key, "domains": "x".join(map(str, sp["domains"])), "states": sp["states"], "k": k}
                row.update({x: u[x] for x in ("p_trap_exact", "log10_p_trap_exact", "expected_missing",
                                              "expected_missing_given_trap", "p_trap_with_replacement",
                                              "union_bound", "zipf_with_replacement_exact")})
                for name, tag in (("uniform", "uniform"), ("zipf_s1", "zipf"), ("class_frequency", "class")):
                    if name in mc:
                        e = mc[name]["per_k"][str(k)]
                        row[f"mc_{tag}_p"], row[f"mc_{tag}_se"] = e["p_trap"], e["se"]
                        if f"mc_{tag}_mean_missing" in fields:
                            row[f"mc_{tag}_mean_missing"] = e["mean_missing"]
                w.writerow(row)
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write(summary_md(res))


def summary_md(res: dict) -> str:
    L = []
    w = L.append
    m = res["meta"]
    w("# How often does the observed-domain trap occur naturally?\n")
    w("Generated by `python -I run_trap_frequency.py` (module `latc_check/trap_frequency.py`; "
      f"Python {m['python']}, {m['platform']}; seed {m['seed']}; {m['draws']} Monte Carlo draws per model and "
      f"space; total {m['seconds']} s).\n")
    w("**Trap**: a set of k example rows T0 misses at least one declared value of at least one attribute, so "
      "LATC's observed cardinalities are too small and every state with an unobserved value is missing. "
      "**Missing states** = |D| − ∏ m_i (m_i = observed values of attribute i); it is 0 without a trap.\n")
    w("## Method\n")
    w("* **Exact (uniform, without replacement)**: inclusion–exclusion over excluded value sets, "
      "P(no trap) = Σ (−1)^{Σ|S_i|} C(∏(d_i−|S_i|), k) / C(|D|, k), grouped by the sizes |S_i| and by attributes "
      "of equal domain size; integer arithmetic, one exact division. E[missing] = |D|·(1 − q), "
      "q = Σ_T (−1)^{|T|} C(∏_{i∈T}(d_i−1)∏_{i∉T}d_i, k) / C(|D|, k); E[missing | trap] = E[missing] / P(trap).")
    w("* **With replacement**: attributes become independent, P(no trap) = ∏_i Σ_j (−1)^j C(d_i, j)(1 − j/d_i)^k "
      "(coupon collector per attribute); the same product formula with Zipf probabilities gives the exact "
      "with-replacement Zipf value.")
    w("* **Rule of thumb**: union bound P(trap) ≤ Σ d_i (1 − 1/d_i)^k ≤ V·e^{−k/d_max} (V = Σ d_i), so "
      "k ≥ d_max·ln(V/α) rows suffice for P(trap) ≤ α.")
    w("* **Non-uniform (Monte Carlo, illustrative model only)**: *zipf_s1* — each attribute's value drawn "
      "independently with P(j-th declared value) ∝ 1/j, duplicate states rejected; *class_frequency* — rows of the "
      "real table drawn without replacement with weight ∝ the frequency of the row's class (typical outcomes are "
      "over-represented). Neither is a model of how any real expert writes examples; they only show the "
      "direction and size of the effect of skew. Each draw samples sequentially until every declared value is "
      "seen; trap(k) = [cover time > k].\n")

    w("## Validation (exact vs Monte Carlo and brute force)\n")
    w(f"{m['validation_draws']} uniform draws per space, without and with replacement. z = (MC − exact)/SE.\n")
    w("| domains | k | exact P | MC P (SE) | z | exact E[miss] | MC E[miss] | z | w/repl exact | w/repl MC | z | brute force equal |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for v in res["validation"]:
        w(f"| {'x'.join(map(str, v['domains']))} | {v['k']} | {v['exact_p']:.4f} | {v['mc_p']:.4f} ({v['mc_se']:.4f}) | "
          f"{v['z_p']:+.2f} | {v['exact_missing']:.3f} | {v['mc_missing']:.3f} | {v['z_missing']:+.2f} | "
          f"{v['wr_p']:.4f} | {v['mc_wr_p']:.4f} | {v['z_wr_p']:+.2f} | {v.get('brute_equal', '–')} |")
    zs = [abs(v[z]) for v in res["validation"] for z in ("z_p", "z_missing", "z_wr_p")]
    w(f"\nLargest |z| over {len(zs)} comparisons: {max(zs):.2f} (the comparisons are correlated, and with this "
      "many an |z| near 3 is not unusual). Where the last column is True, the exact P(trap) and E[missing] equal "
      "a brute-force enumeration of every k-subset, as exact fractions.\n")

    for key, sp in res["spaces"].items():
        mc = sp["monte_carlo"]
        w(f"## {sp['title']} ({'x'.join(map(str, sp['domains']))} = {sp['states']:,} states, "
          f"{sp['declared_values']} declared values)\n")
        if "published_t0" in sp:
            pt = sp["published_t0"]
            w(f"The published T0 ({pt['rows']} rows) observes {pt['observed_values']} of {pt['declared_values']} "
              f"values: trap = {pt['trap']}.\n")
        if "class_counts" in sp:
            w("Class counts used as weights: " + ", ".join(f"{c} {n}" for c, n in sp["class_counts"].items()) + ".\n")
        head = ("| k | P(trap) exact | E[missing] | E[missing given trap] | P w/ replacement | union bound | "
                "MC uniform | MC Zipf s=1 (E[miss]) |")
        sep = "|---|---|---|---|---|---|---|---|"
        if "class_frequency" in mc:
            head += " MC class-frequency (E[miss]) |"
            sep += "---|"
        w(head)
        w(sep)
        for k in sp["ks"]:
            u = sp["uniform"][str(k)]
            line = (f"| {k} | {_fmt_p(u['p_trap_exact'], u['log10_p_trap_exact'])} | {u['expected_missing']:.3g} | "
                    f"{'–' if u['expected_missing_given_trap'] is None else format(u['expected_missing_given_trap'], '.4g')} | "
                    f"{_fmt_p(u['p_trap_with_replacement'])} | {_fmt_p(u['union_bound'])} | "
                    f"{_fmt_p(mc['uniform']['per_k'][str(k)]['p_trap'])} | "
                    f"{_fmt_p(mc['zipf_s1']['per_k'][str(k)]['p_trap'])} "
                    f"({mc['zipf_s1']['per_k'][str(k)]['mean_missing']:.3g}) |")
            if "class_frequency" in mc:
                e = mc["class_frequency"]["per_k"][str(k)]
                line += f" {_fmt_p(e['p_trap'])} ({e['mean_missing']:.3g}) |"
            w(line)
        w("\nSmallest k with P(trap) ≤ α:\n")
        w("| α | exact (uniform) | with replacement | union bound | d_max·ln(V/α) | MC uniform | MC Zipf s=1 |"
          + (" MC class-frequency |" if "class_frequency" in mc else ""))
        w("|---|---|---|---|---|---|---|" + ("---|" if "class_frequency" in mc else ""))
        for a in ALPHAS:
            t = sp["thresholds_uniform"][str(a)]
            line = (f"| {a:.0%} | {t['exact_without_replacement']} | {t['with_replacement']} | {t['union_bound']} | "
                    f"{t['rule_of_thumb_dmax_ln_V_over_alpha']} | {mc['uniform']['thresholds'][str(a)]} | "
                    f"{mc['zipf_s1']['thresholds'][str(a)]} |")
            if "class_frequency" in mc:
                line += f" {mc['class_frequency']['thresholds'][str(a)]} |"
            w(line)
        w("")

    w("## Consistency with the 1% random samples in `results/datasets/`\n")
    w("| dataset | k | samples | with an unobserved value | exact P(trap) | expected count | "
      "P(observed count) | Clopper–Pearson 95% | exact inside CI |")
    w("|---|---|---|---|---|---|---|---|---|")
    for key, c in res["consistency_with_datasets"].items():
        w(f"| {key} | {c['k']} | {c['samples']} | {c['samples_with_trap']} | {c['exact_p_trap']:.4f} | "
          f"{c['expected_traps']:.2f} | {c['binomial_p_of_observed_count']:.3f} | "
          f"[{c['clopper_pearson_95'][0]:.4f}, {c['clopper_pearson_95'][1]:.4f}] | {c['exact_inside_ci']} |")
    w("")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--draws", type=int, default=20000)
    p.add_argument("--validation-draws", type=int, default=20000)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--out", default=OUT)
    a = p.parse_args(argv)
    res = run(a.draws, a.seed, a.validation_draws)
    write_outputs(res, a.out)
    print(f"wrote {a.out} ({res['meta']['seconds']} s)")
    return 0
