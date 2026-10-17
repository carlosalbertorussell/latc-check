"""Randomised property tests: LATC readings vs the exact complement.

Three scenarios, each a stress the source's assumptions do or do not cover:

observed     every declared value appears in T0, no constraint (the setting
             the source's corollaries assume)
unobserved   one declared value never appears in T0 (I-1: LATC cannot see it)
constrained  a valid-state constraint forbids some combinations (I-5)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import product
from statistics import mean

from . import latc
from .compare import best_block_order, compare
from .model import Attribute, DecisionTable, Row
from .reference import exact_complement

SCENARIOS = ("observed", "unobserved", "constrained")
METHODS = ("reference", "latc_A_deficit_fill", "latc_A_best_order", "latc_B_odometer")


def _domains(rng: random.Random, max_cells: int) -> list[Attribute]:
    while True:
        n = rng.randint(2, 4)
        cards = [rng.randint(2, 4) for _ in range(n)]
        total = 1
        for c in cards:
            total *= c
        if total <= max_cells:
            return [Attribute(f"A{i}", tuple(f"v{i}{j}" for j in range(c)))
                    for i, c in enumerate(cards)]


def _covers_all(rows, attributes, skip=None) -> bool:
    for j, a in enumerate(attributes):
        seen = {r[j] for r in rows}
        need = set(a.domain) - ({skip[1]} if skip and skip[0] == j else set())
        if not need <= seen:
            return False
    return True


def generate_case(rng: random.Random, scenario: str, max_cells: int = 48) -> DecisionTable:
    for _ in range(1000):
        attributes = _domains(rng, max_cells)
        space = list(product(*(a.domain for a in attributes)))
        constraint, skip = None, None
        if scenario == "constrained":
            forbidden = set(rng.sample(space, max(1, len(space) // 4)))
            constraint = lambda c, f=frozenset(forbidden): c not in f
            space = [c for c in space if c not in forbidden]
        elif scenario == "unobserved":
            j = rng.randrange(len(attributes))
            skip = (j, rng.choice(attributes[j].domain))
            space = [c for c in space if c[j] != skip[1]]
        if len(space) < 2:
            continue
        size = rng.randint(1, len(space) - 1)
        rows = rng.sample(space, size)
        if _covers_all(rows, attributes, skip):
            return DecisionTable(tuple(attributes), [Row(c, rng.choice(("YES", "NO", "Rv"))) for c in rows],
                                 constraint=constraint)
    raise RuntimeError("could not generate a case")


@dataclass
class Tally:
    trials: int = 0
    exact: int = 0
    missed: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    regenerated_t0: list = field(default_factory=list)
    outside_space: list = field(default_factory=list)

    def add(self, r) -> None:
        self.trials += 1
        self.exact += r.exact
        self.missed.append(r.missed)
        self.duplicates.append(r.duplicates)
        self.regenerated_t0.append(r.regenerated_t0)
        self.outside_space.append(r.outside_space)

    def summary(self) -> dict:
        if not self.trials:
            return {"trials": 0}
        return {"trials": self.trials, "exact_rate": self.exact / self.trials,
                "mean_missed": mean(self.missed), "max_missed": max(self.missed),
                "mean_duplicates": mean(self.duplicates),
                "mean_regenerated_t0": mean(self.regenerated_t0),
                "mean_outside_space": mean(self.outside_space),
                "any_error_rate": sum(1 for m, d, t, o in zip(self.missed, self.duplicates,
                                                              self.regenerated_t0, self.outside_space)
                                      if m or d or t or o) / self.trials}


def run(trials: int = 1000, seed: int = 20210101, order_limit: int = 2000) -> dict:
    """Return {scenario: {method: summary, 'count_checks': {...}}}."""
    rng = random.Random(seed)
    out = {}
    for scenario in SCENARIOS:
        tallies = {m: Tally() for m in METHODS}
        cor3_ok = check12_ok = check_gen_ok = 0
        for _ in range(trials):
            t = generate_case(rng, scenario)
            ref = exact_complement(t)
            tallies["reference"].add(compare(ref, t))
            tallies["latc_A_deficit_fill"].add(compare(latc.deficit_fill(t), t))
            best = best_block_order(t, limit=order_limit)
            if best is not None:
                tallies["latc_A_best_order"].add(best[0])
            tallies["latc_B_odometer"].add(compare(latc.latc_odometer(t), t))
            cor3_ok += latc.missing_count(t) == len(ref)
            check12_ok += not latc.deficit_check(ref, t)
            check_gen_ok += not latc.deficit_check(ref, t, latc.valid_space_deficits(t))
        out[scenario] = {m: tallies[m].summary() for m in METHODS}
        out[scenario]["count_checks"] = {
            "corollary3_count_equals_true_missing": cor3_ok / trials,
            "complement_passes_[12]_deficit_check": check12_ok / trials,
            "complement_passes_valid_space_deficit_check": check_gen_ok / trials,
        }
    return out
