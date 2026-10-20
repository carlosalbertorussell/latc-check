"""Example sources, conditions C1-C3 and per-run metrics (PROTOCOL.md 4-7)."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from math import comb, prod

from latc_check.latc import latc_odometer, missing_count
from latc_check.model import Attribute, DecisionTable, Row
from latc_check.reference import exact_complement

from .spec import Sample

SOURCES = ("OFFICIAL", "FULL", "UNIFORM", "ZIPF")
SIZES = (10, 20, 50, 100, 200, 500, 1000)
SEEDS = tuple(range(30))
CONDITIONS = ("C1", "C2", "C3")
ZIPF_S = 1.0

Example = tuple[tuple, str]   # (condition tuple of labels, output label)


# -- sources (section 5) -------------------------------------------------------

def uniform_examples(sample: Sample, n: int, seed: int) -> list[Example]:
    rng = random.Random(seed)
    drawn = rng.choices(sample.V_list, k=n)
    return [(c, sample.gt[c]) for c in drawn]


def zipf_examples(sample: Sample, n: int, seed: int) -> list[Example]:
    rng = random.Random(seed)
    perm = list(sample.V_list)
    rng.shuffle(perm)
    weights = [1.0 / (k ** ZIPF_S) for k in range(1, len(perm) + 1)]
    drawn = rng.choices(perm, weights=weights, k=n)
    return [(c, sample.gt[c]) for c in drawn]


def full_examples(sample: Sample) -> list[Example]:
    return [(c, sample.gt[c]) for c in sample.V_list]


def example_sets(sample: Sample):
    """Yield (source, size, seed, examples) in the run order of section 5.
    Seed is None for OFFICIAL and FULL."""
    if sample.official:
        yield "OFFICIAL", len(sample.official), None, list(sample.official)
    full = full_examples(sample)
    yield "FULL", len(full), None, full
    for source, fn in (("UNIFORM", uniform_examples), ("ZIPF", zipf_examples)):
        for n in SIZES:
            for seed in SEEDS:
                yield source, n, seed, fn(sample, n, seed)


# -- conditions (section 4) ----------------------------------------------------

def make_table(sample: Sample, examples: list[Example], with_exclusions: bool) -> DecisionTable:
    attributes = tuple(Attribute(n, d) for n, d in zip(sample.names, sample.domains))
    S = sample.S
    return DecisionTable(attributes, [Row(c, y) for c, y in examples], sample.outputs,
                         (lambda c: c in S) if with_exclusions else None)


def generate(sample: Sample, examples: list[Example], condition: str) -> tuple[list, int]:
    """Return (G_list, reported missing count) for one condition."""
    if condition == "C1":
        t = make_table(sample, examples, False)
        return latc_odometer(t), missing_count(t)
    if condition == "C2":
        t = make_table(sample, examples, False)
        return exact_complement(t), prod(len(d) for d in sample.domains) - len(t.rows)
    if condition == "C3":
        t = make_table(sample, examples, True)
        return exact_complement(t), t.valid_space_size() - len(t.rows)
    raise ValueError(condition)


# -- metrics (section 6) -------------------------------------------------------

def contradictory_pairs(examples: list[Example]) -> int:
    by_cond: dict[tuple, Counter] = defaultdict(Counter)
    for c, y in examples:
        by_cond[c][y] += 1
    total = 0
    for outs in by_cond.values():
        total += comb(sum(outs.values()), 2) - sum(comb(k, 2) for k in outs.values())
    return total


def example_metrics(sample: Sample, examples: list[Example]) -> dict:
    X_list = [c for c, _ in examples]
    X = set(X_list)
    seen = [set() for _ in sample.names]
    for c in X:
        for j, v in enumerate(c):
            seen[j].add(v)
    ratios = [len(seen[j] & set(d)) / len(d) for j, d in enumerate(sample.domains)]
    bad = sample.E | sample.R
    return {
        "n_examples": len(X_list),
        "n_distinct_examples": len(X),
        "examples_invalid": sum(1 for c in X_list if c in bad),
        "examples_disagree_gt": sum(1 for c, y in examples if y != sample.gt[c]),
        "contradictory_pairs": contradictory_pairs(examples),
        "value_coverage": ";".join(f"{n}={len(seen[j] & set(d))}/{len(d)}"
                                   for j, (n, d) in enumerate(zip(sample.names, sample.domains))),
        "min_value_coverage": min(ratios),
        "unseen_values": sum(len(set(d) - seen[j]) for j, d in enumerate(sample.domains)),
        "true_gap": len(sample.V - X),
        "_X": X,
    }


def run_metrics(sample: Sample, ex: dict, G_list: list, reported: int) -> dict:
    X, V = ex["_X"], sample.V
    G = set(G_list)
    covered = len(V & (X | G))
    sp_e, sp_r = len(G & sample.E), len(G & sample.R)
    spurious = sp_e + sp_r
    coverage = covered / len(V) if V else 1.0
    return {
        "reported_missing": reported,
        "workload": len(G_list),
        "covered_valid": covered,
        "valid_coverage": coverage,
        "missed_valid": len(V) - covered,
        "spurious_excluded": sp_e,
        "spurious_rejected": sp_r,
        "spurious": spurious,
        "spurious_share": spurious / len(G) if G else 0.0,
        "complete": int(coverage == 1.0 and spurious == 0),
    }


# -- planted defect (section 7b) ---------------------------------------------

def planted_value(sample: Sample, examples: list[Example]) -> str:
    counts = Counter(c[0] for c, _ in examples)
    first = sample.domains[0]
    return min(first, key=lambda v: (counts[v], first.index(v)))


def planted_defect(sample: Sample, examples: list[Example]) -> dict:
    v = planted_value(sample, examples)
    kept = [(c, y) for c, y in examples if c[0] != v]
    g2, _ = generate(sample, kept, "C2")
    g1, _ = generate(sample, kept, "C1")
    expected = prod(len(d) for d in sample.domains[1:])
    got2 = sum(1 for c in set(g2) if c[0] == v)
    return {
        "value": v,
        "removed": len(examples) - len(kept),
        "expected": expected,
        "c2_generated": got2,
        "c1_generated": sum(1 for c in g1 if c[0] == v),
        "pass": got2 == expected,
    }
