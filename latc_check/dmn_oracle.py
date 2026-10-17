"""Exhaustive oracle for the DMN analysis, for differential tests.

The oracle shares no code with ``dmn.analyse``: it evaluates every rule on
every point of a grid, straight from the entry definitions, and derives gaps,
overlaps, masking and never-firing rules by brute force.

The grid is exhaustive for the tables it accepts.  Numeric inputs must have a
closed integer domain and integer entry bounds; then the integers and
half-integers of the domain hit every elementary cell of the sweep (each
point bound and each open cell between two consecutive bounds), so a
property that holds on the grid holds on the real domain.
"""

from __future__ import annotations

import random
from itertools import combinations, product

from .dmn import (ANY, DMNTable, Input, Interval, Not, OneOf, Point, Rule, analyse,
                  rule_priorities, violations)


def matches(inp: Input, entry, x) -> bool:
    """Does value x satisfy the input entry?  Written from the S-FEEL semantics."""
    if entry is ANY:
        return True
    if isinstance(entry, Not):
        return not matches(inp, entry.entry, x)
    if isinstance(entry, Point):
        return x == entry.value
    if isinstance(entry, OneOf):
        return x in entry.values
    if isinstance(entry, Interval):
        lo_ok = x > entry.lo or (x == entry.lo and entry.lo_closed)
        hi_ok = x < entry.hi or (x == entry.hi and entry.hi_closed)
        return lo_ok and hi_ok
    raise TypeError(entry)


def grid(inp: Input) -> list:
    if not inp.numeric:
        return list(inp.values)
    d = inp.domain
    if not (d.lo_closed and d.hi_closed and float(d.lo).is_integer() and float(d.hi).is_integer()):
        raise ValueError("the oracle needs a closed integer domain")
    return [k / 2 for k in range(int(2 * d.lo), int(2 * d.hi) + 1)]


def oracle(table: DMNTable) -> dict:
    """Brute-force analysis over the grid."""
    points = list(product(*(grid(i) for i in table.inputs)))
    hits = {x: frozenset(k for k, r in enumerate(table.rules)
                         if all(matches(i, e, v) for i, e, v in zip(table.inputs, r.entries, x)))
            for x in points}
    by_rule = [frozenset(x for x in points if k in hits[x]) for k in range(len(table.rules))]
    sets = {h for h in hits.values() if len(h) > 1}
    pairs = sorted({p for h in sets for p in combinations(sorted(h), 2)})
    differ = [p for p in pairs if table.rules[p[0]].output != table.rules[p[1]].output]
    out = {"uncovered": sorted(x for x in points if not hits[x]),
           "pairs": pairs, "pairs_differ": differ,
           "maximal_sets": sorted(tuple(sorted(s)) for s in sets if not any(s < o for o in sets))}
    prio = rule_priorities(table)
    if prio is not None:
        live = [k for k in range(len(table.rules)) if by_rule[k]]
        out["masked"] = [(a, b) for a in live for b in live
                         if prio[b] > prio[a] and by_rule[a] <= by_rule[b]]
        winners = {max(h, key=lambda k: prio[k]) for h in hits.values() if h}
        out["never_fire"] = [k for k in live if k not in winners]
    return out


def _in_region(region: tuple, x: tuple) -> bool:
    return all((v in seg) if isinstance(seg, frozenset) else seg.contains(v)
               for seg, v in zip(region, x))


def differential(table: DMNTable) -> dict:
    """Compare ``analyse`` + ``violations`` with the oracle; True where they agree."""
    o = oracle(table)
    a = analyse(table)
    v = violations(table, a)
    points = list(product(*(grid(i) for i in table.inputs)))
    in_gaps = sorted(x for x in points if any(_in_region(g, x) for g in a.gaps))
    res = {"gaps": in_gaps == o["uncovered"],
           "gaps_disjoint": all(sum(_in_region(g, x) for g in a.gaps) <= 1 for x in points),
           "pairs": a.overlap_pairs == o["pairs"],
           "maximal_sets": a.maximal_overlap_sets == o["maximal_sets"]}
    if table.hit_policy == "UNIQUE":
        res["violations"] = v["violating_pairs"] == o["pairs"]
    elif table.hit_policy == "ANY":
        res["violations"] = v["violating_pairs"] == o["pairs_differ"]
    else:
        res["violations"] = v["violating_pairs"] == o["masked"]
        res["never_fire"] = v["never_fire"] == o["never_fire"]
    return res


def random_table(rng: random.Random, hit_policy: str | None = None) -> DMNTable:
    """A small random table: 1-3 inputs, 1-6 rules, every entry kind."""
    inputs = []
    for k in range(rng.randint(1, 3)):
        if rng.random() < 0.5:
            inputs.append(Input(f"e{k}", values=tuple("abcd"[:rng.randint(2, 4)])))
        else:
            inputs.append(Input(f"x{k}", domain=Interval(0, rng.randint(2, 6))))
    outputs = ("p", "q", "r")

    def entry(inp: Input):
        roll = rng.random()
        if roll < 0.2:
            return ANY
        if not inp.numeric:
            vals = rng.sample(inp.values, rng.randint(1, len(inp.values)))
            base = Point(vals[0]) if len(vals) == 1 else OneOf(frozenset(vals))
        else:
            hi_dom = int(inp.domain.hi)
            lo = rng.randint(0, hi_dom)
            hi = rng.randint(lo, hi_dom)
            base = Interval(lo, hi, rng.random() < 0.6, rng.random() < 0.6)
            if base.is_empty():
                base = Interval(lo, lo)
            if lo == hi and rng.random() < 0.3:
                base = Point(lo)
        return Not(base) if roll > 0.85 else base

    rules = [Rule(tuple(entry(i) for i in inputs), rng.choice(outputs))
             for _ in range(rng.randint(1, 6))]
    return DMNTable(tuple(inputs), rules, hit_policy or rng.choice(("UNIQUE", "ANY", "FIRST", "PRIORITY")),
                    output_values=outputs)


def run(trials: int = 2000, seed: int = 20210101) -> dict:
    """Differential test summary: how many random tables agree on each property."""
    rng = random.Random(seed)
    agree, total, failures = {}, {}, []
    for t in range(trials):
        table = random_table(rng)
        res = differential(table)
        for k, ok in res.items():
            total[k] = total.get(k, 0) + 1
            agree[k] = agree.get(k, 0) + ok
        if not all(res.values()) and len(failures) < 5:
            failures.append({"trial": t, "result": res})
    return {"trials": trials, "seed": seed, "agree": agree, "total": total, "failures": failures}
