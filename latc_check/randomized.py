"""Randomised property tests: LATC readings vs the exact complement.

Three scenarios, each a stress the source's assumptions do or do not cover:

observed     every declared value appears in T0, no constraint (the setting
             the source's corollaries assume)
unobserved   one declared value never appears in T0 (I-1: LATC cannot see it)
constrained  a valid-state constraint forbids some combinations (I-5)

A fourth scenario, ``structured`` (``run_structured``), replaces the random
forbidden set with 1-3 structured constraints (implication, excluded value
pair, ordinal compatibility, "n/a iff" dependency).  It uses its own generator
so the three scenarios above are reproduced unchanged.
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


def generator_profile(trials: int = 1000, seed: int = 20210101, baseline_draws: int = 100_000) -> dict:
    """What the redraw in ``generate_case`` does to the cases of ``run``.

    Replays exactly the draws of ``run`` (same seed, same order) and reports, per scenario,
    the mean share of the valid space that T0 covers and the mean sizes of the product and
    valid spaces.  ``without_redraw`` gives the same means for the generator's distribution
    before the coverage condition: T0's share is then 1/2 by construction (a size drawn
    uniformly from 1 to |V| - 1), and the product size comes from ``baseline_draws`` draws
    of ``_domains`` with seed 1."""
    rng = random.Random(seed)
    out = {}
    for scenario in SCENARIOS:
        share, dsize, vsize = [], [], []
        for _ in range(trials):
            t = generate_case(rng, scenario)
            n = 1
            for a in t.attributes:
                n *= len(a.domain)
            v = n if t.constraint is None else sum(
                1 for c in product(*(a.domain for a in t.attributes)) if t.constraint(c))
            share.append(len(t.rows) / v)
            dsize.append(n)
            vsize.append(v)
        out[scenario] = {"trials": trials, "mean_t0_share_of_valid_space": mean(share),
                         "mean_product_size": mean(dsize), "mean_valid_space_size": mean(vsize)}
    r = random.Random(1)
    sizes = []
    for _ in range(baseline_draws):
        n = 1
        for a in _domains(r, 48):
            n *= len(a.domain)
        sizes.append(n)
    out["without_redraw"] = {"mean_t0_share_of_valid_space": 0.5, "mean_product_size": mean(sizes),
                             "draws": baseline_draws}
    return out


# -- structured valid-state constraints ----------------------------------------
#
# The "constrained" scenario above forbids a random quarter of the product
# space.  Real valid-state constraints are structured: dependencies between
# attributes, excluded value pairs, ordinal compatibilities, and "not
# applicable" values.  The "structured" scenario draws 1-3 such constraints at
# random.  It is kept out of ``SCENARIOS`` (and run from its own generator
# seeded with the same seed) so that the published numbers of the three
# original scenarios, and every other report that iterates ``SCENARIOS``, are
# reproduced bit for bit.

STRUCTURED = "structured"
CONSTRAINT_KINDS = ("implication", "exclusion", "ordinal", "undefined_when")


@dataclass(frozen=True)
class Implication:
    """If A_i = v then A_j not in ``banned`` (equivalently A_j in the rest)."""
    i: int
    v: object
    j: int
    banned: frozenset
    kind: str = "implication"

    def __call__(self, c) -> bool:
        return c[self.i] != self.v or c[self.j] not in self.banned


@dataclass(frozen=True)
class Exclusion:
    """not (A_i = v and A_j = w)."""
    i: int
    v: object
    j: int
    w: object
    kind: str = "exclusion"

    def __call__(self, c) -> bool:
        return not (c[self.i] == self.v and c[self.j] == self.w)


@dataclass(frozen=True)
class Ordinal:
    """If A_i is in its top values then A_j is not in its bottom values.

    "Top" and "bottom" follow the declared domain order (last = top).
    """
    i: int
    top: frozenset
    j: int
    bottom: frozenset
    kind: str = "ordinal"

    def __call__(self, c) -> bool:
        return c[self.i] not in self.top or c[self.j] not in self.bottom


@dataclass(frozen=True)
class UndefinedWhen:
    """A_j takes its reserved value ``na`` (the last declared value) iff A_i = v."""
    i: int
    v: object
    j: int
    na: object
    kind: str = "undefined_when"

    def __call__(self, c) -> bool:
        return (c[self.j] == self.na) == (c[self.i] == self.v)


@dataclass(frozen=True)
class AllOf:
    """Conjunction of structured constraints; the DecisionTable constraint."""
    parts: tuple

    def __call__(self, c) -> bool:
        return all(p(c) for p in self.parts)


def draw_constraint(rng: random.Random, attributes) -> object:
    """One structured constraint over two distinct attributes."""
    kind = rng.choice(CONSTRAINT_KINDS)
    i, j = rng.sample(range(len(attributes)), 2)
    di, dj = attributes[i].domain, attributes[j].domain
    if kind == "implication":
        banned = frozenset(rng.sample(dj, rng.randint(1, len(dj) - 1)))
        return Implication(i, rng.choice(di), j, banned)
    if kind == "exclusion":
        return Exclusion(i, rng.choice(di), j, rng.choice(dj))
    if kind == "ordinal":
        t = rng.randint(1, max(1, len(di) // 2))
        b = rng.randint(1, max(1, len(dj) // 2))
        return Ordinal(i, frozenset(di[-t:]), j, frozenset(dj[:b]))
    return UndefinedWhen(i, rng.choice(di), j, dj[-1])


def draw_structured_constraint(rng: random.Random, attributes, max_tries: int = 1000):
    """1-3 structured constraints leaving at least 2 valid states.

    Returns (AllOf constraint, list of valid tuples).
    """
    space = list(product(*(a.domain for a in attributes)))
    for _ in range(max_tries):
        k = rng.randint(1, 3)
        constraint = AllOf(tuple(draw_constraint(rng, attributes) for _ in range(k)))
        valid = [c for c in space if constraint(c)]
        if len(valid) >= 2:
            return constraint, valid
    raise RuntimeError("could not draw a structured constraint")


def generate_structured_case(rng: random.Random, max_cells: int = 48) -> DecisionTable:
    """Random table whose valid space is cut by 1-3 structured constraints.

    T0 is a random proper subset of the valid states that observes every value
    occurring in some valid state (values the constraints eliminate entirely
    cannot be observed); redrawn otherwise, as in ``generate_case``.
    """
    for _ in range(1000):
        attributes = _domains(rng, max_cells)
        constraint, valid = draw_structured_constraint(rng, attributes)
        live = [{c[j] for c in valid} for j in range(len(attributes))]
        size = rng.randint(1, len(valid) - 1)
        rows = rng.sample(valid, size)
        if all(live[j] <= {r[j] for r in rows} for j in range(len(attributes))):
            return DecisionTable(tuple(attributes), [Row(c, rng.choice(("YES", "NO", "Rv"))) for c in rows],
                                 constraint=constraint)
    raise RuntimeError("could not generate a structured case")


def run_structured(trials: int = 1000, seed: int = 20210101, order_limit: int = 2000) -> dict:
    """The "structured" scenario, same harness and metrics as ``run``, plus
    the excluded share of the product space and the generalised cardinality
    check (|M| = |V| - |T0| and per-value frequencies over V) applied to
    COMPLETE's output and to Reading B's output."""
    rng = random.Random(seed)
    tallies = {m: Tally() for m in METHODS}
    cor3_ok = check12_ok = gen_ref_ok = gen_b_ok = gen_a_ok = 0
    excluded, kinds, n_constraints, dead_values, product_space = [], {k: 0 for k in CONSTRAINT_KINDS}, [], 0, 0
    for _ in range(trials):
        t = generate_structured_case(rng)
        ref = exact_complement(t)
        odo = latc.latc_odometer(t)
        fill = latc.deficit_fill(t)
        tallies["reference"].add(compare(ref, t))
        tallies["latc_A_deficit_fill"].add(compare(fill, t))
        best = best_block_order(t, limit=order_limit)
        if best is not None:
            tallies["latc_A_best_order"].add(best[0])
        tallies["latc_B_odometer"].add(compare(odo, t))
        vdef = latc.valid_space_deficits(t)
        cor3_ok += latc.missing_count(t) == len(ref)
        check12_ok += not latc.deficit_check(ref, t)
        gen_ref_ok += not latc.deficit_check(ref, t, vdef)
        gen_b_ok += not latc.deficit_check(odo, t, vdef)
        gen_a_ok += not latc.deficit_check(fill, t, vdef)
        full = 1
        for a in t.attributes:
            full *= a.card
        excluded.append(1 - t.valid_space_size() / full)
        n_constraints.append(len(t.constraint.parts))
        for p in t.constraint.parts:
            kinds[p.kind] += 1
        live = latc.observed_domains(t)
        dead_values += any(len(d) < a.card for d, a in zip(live, t.attributes))
        product_space += set(t.valid_space()) == set(product(*live))
    out = {m: tallies[m].summary() for m in METHODS}
    out["count_checks"] = {
        "corollary3_count_equals_true_missing": cor3_ok / trials,
        "complement_passes_[12]_deficit_check": check12_ok / trials,
        "complement_passes_valid_space_deficit_check": gen_ref_ok / trials,
        "latc_B_passes_valid_space_deficit_check": gen_b_ok / trials,
        "latc_A_deficit_fill_passes_valid_space_deficit_check": gen_a_ok / trials,
    }
    out["constraints"] = {
        "excluded_share_mean": mean(excluded), "excluded_share_min": min(excluded),
        "excluded_share_max": max(excluded),
        "mean_constraints_per_table": mean(n_constraints),
        "constraint_kind_counts": kinds,
        "tables_with_a_declared_value_absent_from_valid_space": dead_values / trials,
        # V = product of the values that occur in V: the constraints only
        # removed whole values, which is the one case Reading B gets right
        "valid_space_is_product_of_its_values": product_space / trials,
    }
    return out
