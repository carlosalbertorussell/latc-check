"""Sensitivity of completion to modelling choices, and policy change (Section 9.6).

Two questions:

1. How much do the missing states, and the expert review load, depend on
   modelling choices the domain owner has to approve: interval cut points,
   merged or split values, valid-state constraints?
2. After a policy change, which states and which already-approved rows must be
   reviewed again?

Both reduce to one operation, *migration* between two schemas over the same
raw input space.  Run with ``python run_sensitivity.py``; results go to
``results/sensitivity/``.

Definitions (S-1 .. S-9)
------------------------
S-1  Schema.  An ordered list of dimensions.  Each label of a dimension has a
     *meaning*: a real interval for a numeric dimension (Age, contribution
     years), or a set of atomic values for an enumerated one.  A state's
     meaning is the box (product) of its labels' meanings.  Two schemas are
     comparable when every dimension covers the same raw set (same numeric
     range, same atoms).  Splitting a value v refines the atoms: the old
     label v means {v#1, v#2}, the new labels mean {v#1} and {v#2}.
S-2  Numeric bins.  Cut points c1 < ... < ck on [lo, hi] give the bins
     [lo, c1), [c1, c2), ..., [ck, hi] (labels '<c1', 'c1-(c2-1)', '>=ck',
     integer reading of the labels; the bins themselves are real intervals,
     as in dmn D-1).  Labels are listed in descending order, as in the
     published table.  Ranges: Age 18-120, contribution years 0-60 (the
     assumptions of examples.AGE_RANGE / CONTRIBUTION_RANGE).
S-3  Fate of an old state x (an approved row's condition) in the new schema,
     from the new states y whose box meets x's box:
       unchanged  one y, same box;
       merged     one y, x strictly inside it (x is now part of a larger state);
       split      several y, each inside x (x is the union of them);
       reshaped   several y, at least one only partly inside x.
     An approved row's *meaning changed* iff its fate is not 'unchanged'.
     A T0 row whose fate is merged or reshaped is *misaligned*: some new bin
     is only partly covered by it (the to_exact notion of a misaligned entry).
S-4  Category of a new state y, given approved old rows (condition -> outcome):
       identical    y has the same box as an approved row;
       contained    y lies strictly inside one approved row;
       uniform      y meets several old states, all approved, one outcome;
       conflicting  y meets several old states, all approved, different
                    outcomes (the new schema lumps together inputs the
                    approved rows decide differently);
       partial      y meets approved and unapproved old states;
       unapproved   y meets no approved old state.
     identical, contained and uniform states *inherit* an outcome (the
     approved rows assert it for every input in y).  The others have none.
S-5  Mapped T0 (T0') = the inherited states with their outcomes.  Review load
     = COMPLETE(T0') = conflicting + partial + unapproved (checked).  'Missing'
     always means COMPLETE on the mapped table, never on raw intervals.
S-6  Re-review after a change = every new state that is not identical.  A
     contained or uniform state has an inherited outcome, but its condition
     text changed, and the inherited outcome is the *old* policy's.
S-7  Policy-affected state (pension only, where both rules are modelled): a
     new state containing at least one raw input whose decision differs
     between the old and the new rule.  It is compared with the re-review
     set of S-6: a change that moves no cut point (outcome-only) is invisible
     to a schema comparison and needs a rule comparison.
S-8  Merging two values of a complete table: the merged table stays a
     function iff no merged state is 'conflicting' with every original row
     approved.  The conflict count is the number of merged states whose
     original states carry different classes.
S-9  Fixed T0 for Car and Nursery: 50 % of the rows, drawn with
     random.Random(f"{seed}:{dataset}:t0"), seed 20210101.  The same T0 is
     used in the merge/split, constraint and policy experiments.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass
from itertools import product
from math import prod

from . import __version__, datasets, latc
from . import examples as ex
from .checks import structural_report
from .compare import compare
from .dmn import (ANY, DMNTable, Input, Interval, Point, Rule, analyse, at_least, below, closed,
                  expand, from_exact, half_open, to_exact)
from .dmn_compare import PENSION_NUMERIC, RAW_TABLE1, raw_table1_dmn
from .model import RV, Attribute, DecisionTable, Row
from .rank import RankIndex
from .reference import exact_complement

SEED = 20210101
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# -- S-1, S-2: schemas --------------------------------------------------------------------

@dataclass(frozen=True)
class Dim:
    name: str
    labels: tuple
    meanings: tuple                 # per label: Interval (numeric) or frozenset of atoms
    domain: Interval | None = None  # numeric dimensions only

    @property
    def numeric(self) -> bool:
        return self.domain is not None

    def attribute(self) -> Attribute:
        return Attribute(self.name, self.labels)

    def dmn_input(self) -> Input:
        if self.numeric:
            return Input(self.name, domain=self.domain, bins=tuple(zip(self.labels, self.meanings)))
        return Input(self.name, values=self.labels)

    def bins(self) -> tuple:
        return tuple(zip(self.labels, self.meanings))


def enum_dim(name: str, values, meanings=None) -> Dim:
    values = tuple(values)
    return Dim(name, values, tuple(meanings) if meanings is not None
               else tuple(frozenset({v}) for v in values))


def num_dim(name: str, rng: tuple, cuts) -> Dim:
    """S-2: bins from cut points, labels in descending order."""
    lo, hi = rng
    cuts = sorted(set(cuts))
    if not all(lo < c <= hi for c in cuts):
        raise ValueError(f"{name}: cut points {cuts} outside ({lo}, {hi}]")
    edges = [lo] + cuts
    bins = []
    for k, c in enumerate(edges):
        if k == len(edges) - 1:
            bins.append((f">={c}" if k else f"{lo}-{hi}", closed(c, hi)))
        elif k == 0:
            bins.append((f"<{edges[1]}", half_open(lo, edges[1])))
        else:
            bins.append((f"{c}-{edges[k + 1] - 1}", half_open(c, edges[k + 1])))
    bins.reverse()
    return Dim(name, tuple(b[0] for b in bins), tuple(b[1] for b in bins), closed(lo, hi))


def table_dims(table: DecisionTable) -> tuple:
    return tuple(enum_dim(a.name, a.domain) for a in table.attributes)


def schema_attributes(dims) -> tuple:
    return tuple(d.attribute() for d in dims)


def numeric_of(dims) -> dict:
    return {d.name: (d.domain, d.bins()) for d in dims if d.numeric}


def describe_schema(dims) -> str:
    return "; ".join(f"{d.name} {'/'.join(map(str, d.labels))}" for d in dims)


def _meet(a, b) -> bool:
    return bool(a & b) if isinstance(a, frozenset) else a.intersects(b)


def _sub(a, b) -> bool:
    return a <= b if isinstance(a, frozenset) else a.issubset(b)


def merge_values(dim: Dim, i: int) -> Dim:
    """Merge labels i and i+1 (declared order) into one label 'a+b'."""
    if dim.numeric or not 0 <= i < len(dim.labels) - 1:
        raise ValueError("merge needs an enumerated dimension and an adjacent pair")
    lab = f"{dim.labels[i]}+{dim.labels[i + 1]}"
    labels = dim.labels[:i] + (lab,) + dim.labels[i + 2:]
    meanings = dim.meanings[:i] + (dim.meanings[i] | dim.meanings[i + 1],) + dim.meanings[i + 2:]
    return Dim(dim.name, labels, meanings)


def split_value(dim: Dim, i: int) -> tuple[Dim, Dim]:
    """Split label i into 'v#1' and 'v#2'. Returns (old dim with refined atoms, new dim)."""
    v = dim.labels[i]
    a, b = f"{v}#1", f"{v}#2"
    old = Dim(dim.name, dim.labels, dim.meanings[:i] + (frozenset({a, b}),) + dim.meanings[i + 1:])
    new = Dim(dim.name, dim.labels[:i] + (a, b) + dim.labels[i + 1:],
              dim.meanings[:i] + (frozenset({a}), frozenset({b})) + dim.meanings[i + 1:])
    return old, new


# -- S-3 .. S-5: migration ------------------------------------------------------------------

FATES = ("unchanged", "merged", "split", "reshaped")
CATEGORIES = ("identical", "contained", "uniform", "conflicting", "partial", "unapproved")
INHERITING = ("identical", "contained", "uniform")


class Migration:
    """Box relations between two comparable schemas, addressed by rank (rank.py).

    Because states are boxes, the old states meeting a new state are the
    product of the per-dimension overlaps; nothing is enumerated pairwise.
    """

    def __init__(self, old, new):
        old, new = tuple(old), tuple(new)
        if tuple(d.name for d in old) != tuple(d.name for d in new):
            raise ValueError("schemas have different dimensions")
        for a, b in zip(old, new):
            if a.numeric != b.numeric:
                raise ValueError(f"{a.name}: numeric in one schema only")
            if a.numeric and a.domain != b.domain:
                raise ValueError(f"{a.name}: different numeric ranges")
            if not a.numeric and frozenset().union(*a.meanings) != frozenset().union(*b.meanings):
                raise ValueError(f"{a.name}: different atoms")
        self.old, self.new = old, new
        self.ri_old = RankIndex(schema_attributes(old))
        self.ri_new = RankIndex(schema_attributes(new))
        self.fwd, self.bwd, self.new_in_old, self.old_in_new = [], [], [], []
        for a, b in zip(old, new):
            meet = [[_meet(x, y) for y in b.meanings] for x in a.meanings]
            self.fwd.append([tuple(j for j, m in enumerate(row) if m) for row in meet])
            self.bwd.append([tuple(i for i in range(len(a.labels)) if meet[i][j])
                             for j in range(len(b.labels))])
            self.new_in_old.append([[_sub(y, x) for x in a.meanings] for y in b.meanings])
            self.old_in_new.append([[_sub(x, y) for y in b.meanings] for x in a.meanings])

    @staticmethod
    def _digits(ri: RankIndex, r: int) -> list:
        out = []
        for w in ri.weights:
            i, r = divmod(r, w)
            out.append(i)
        return out

    @staticmethod
    def _rank(ri: RankIndex, digits) -> int:
        return sum(i * w for i, w in zip(digits, ri.weights))

    def old_of(self, r2: int) -> list:
        d = self._digits(self.ri_new, r2)
        return [self._rank(self.ri_old, xs) for xs in product(*(self.bwd[k][j] for k, j in enumerate(d)))]

    def new_of(self, r1: int) -> list:
        d = self._digits(self.ri_old, r1)
        return [self._rank(self.ri_new, ys) for ys in product(*(self.fwd[k][i] for k, i in enumerate(d)))]

    def new_within_old(self, r2: int, r1: int) -> bool:
        return all(self.new_in_old[k][j][i] for k, (j, i) in
                   enumerate(zip(self._digits(self.ri_new, r2), self._digits(self.ri_old, r1))))

    def old_within_new(self, r1: int, r2: int) -> bool:
        return all(self.old_in_new[k][i][j] for k, (i, j) in
                   enumerate(zip(self._digits(self.ri_old, r1), self._digits(self.ri_new, r2))))

    def fate(self, r1: int) -> str:
        ys = self.new_of(r1)
        if len(ys) == 1:
            return "unchanged" if self.new_within_old(ys[0], r1) else "merged"
        return "split" if all(self.new_within_old(y, r1) for y in ys) else "reshaped"

    def apply(self, approved: dict) -> dict:
        """Classify every new state against the approved old rows (S-4, S-5)."""
        appr = {}
        for cond, out in approved.items():
            r = self.ri_old.rank(cond)
            if r is None:
                raise ValueError(f"approved row {cond!r} is outside the old schema")
            appr[r] = out
        outcomes = tuple(dict.fromkeys(approved.values()))
        ri = RankIndex(schema_attributes(self.new), outcomes)
        cats, inherited, category_of = Counter(), {}, []
        conflict_old_states = 0
        for r2 in range(ri.size):
            xs = self.old_of(r2)
            got = [x for x in xs if x in appr]
            if not got:
                cat = "unapproved"
            elif len(got) < len(xs):
                cat = "partial"
            elif len(xs) == 1:
                cat = "identical" if self.old_within_new(xs[0], r2) else "contained"
            else:
                cat = "uniform" if len({appr[x] for x in got}) == 1 else "conflicting"
            if cat == "conflicting":
                conflict_old_states += len(xs)
            if cat in INHERITING:
                inherited[r2] = appr[got[0]]
                ri.codes[r2] = ri.code_of(appr[got[0]])
            cats[cat] += 1
            category_of.append(cat)
        fate_of = {r: self.fate(r) for r in appr}
        rows = [Row(ri.unrank(r2), o) for r2, o in sorted(inherited.items())]
        return {"old_states": self.ri_old.size, "new_states": ri.size, "approved_rows": len(appr),
                "fates": {f: sum(1 for v in fate_of.values() if v == f) for f in FATES},
                "categories": {c: cats[c] for c in CATEGORIES},
                "conflict_old_states": conflict_old_states,
                "fate_of": fate_of, "category_of": category_of, "inherited": inherited,
                "table": DecisionTable(schema_attributes(self.new), rows, outcomes),
                "rank_index": ri}


def strip(res: dict) -> dict:
    """JSON-safe part of a Migration.apply result."""
    return {k: v for k, v in res.items()
            if k not in ("fate_of", "category_of", "inherited", "table", "rank_index")}


def review_load(res: dict) -> int:
    c = res["categories"]
    return c["conflicting"] + c["partial"] + c["unapproved"]


def completion_stats(dims, table: DecisionTable, dmn: bool = True) -> dict:
    """COMPLETE on the mapped table, and the DMN gap analysis of the same rows."""
    t0 = time.perf_counter()
    missing = exact_complement(table)
    out = {"states": table.valid_space_size(), "t0_rows": len(table.rows), "missing": len(missing),
           "complete_ms": 1000 * (time.perf_counter() - t0)}
    if dmn:
        d = from_exact(table, numeric_of(dims))
        t0 = time.perf_counter()
        a = analyse(d)
        tuples, partial = expand(a.gaps, d.inputs)
        out.update(dmn_gap_regions=len(a.gaps), dmn_gap_tuples=len(tuples), dmn_partial_bins=partial,
                   dmn_gaps_equal_complete=(set(tuples) == set(missing) and len(tuples) == len(missing)),
                   dmn_ms=1000 * (time.perf_counter() - t0))
    return out


def _label(cond) -> str:
    return " ".join(map(str, cond))


# -- A: pension cut points ---------------------------------------------------------------------

AGE_CUTS = {"60,65 (published)": (60, 65), "60,67": (60, 67), "62,65": (62, 65), "65": (65,),
            "55,60,65": (55, 60, 65)}
CONTRIB_CUTS = {"30 (published)": (30,), "25": (25,), "35": (35,), "20,30": (20, 30)}


def pension_schema(age_cuts=(60, 65), contrib_cuts=(30,)) -> tuple:
    return (enum_dim("Sex", ("M", "F")), enum_dim("Activity", ("D", "I")),
            num_dim("ContributionYears", ex.CONTRIBUTION_RANGE, contrib_cuts),
            num_dim("Age", ex.AGE_RANGE, age_cuts))


def _t0_dict() -> dict:
    return {r.condition: r.outcome for r in ex.PENSION_T0}


def _complement_dict() -> dict:
    return {c: o for _, c, o in ex.PENSION_PUBLISHED_COMPLEMENT}


def cut_point_case(age_cuts, contrib_cuts) -> dict:
    v1 = pension_schema()
    new = pension_schema(age_cuts, contrib_cuts)
    mig = Migration(v1, new)
    t0, comp = _t0_dict(), _complement_dict()
    m0 = mig.apply(t0)
    mall = mig.apply({**t0, **comp})
    stats = completion_stats(new, m0["table"])
    if stats["missing"] != review_load(m0):
        raise AssertionError("review load does not equal COMPLETE on the mapped T0")
    inputs = tuple(d.dmn_input() for d in new)
    # T0 rows through their raw intervals (no mapping decision): DMN sweep in raw space,
    # and the liberal discretisation of dmn.to_exact (every bin a row touches).
    raw_t0 = from_exact(ex.pension_table(), PENSION_NUMERIC)
    raw = DMNTable(inputs, raw_t0.rules, "UNIQUE", output_values=raw_t0.output_values)
    a = analyse(raw)
    raw_tuples, raw_partial = expand(a.gaps, inputs)
    liberal, conv = to_exact(raw)
    lrep = structural_report(liberal)
    raw1 = raw_table1_dmn()
    _, conv1 = to_exact(DMNTable(inputs, raw1.rules, "UNIQUE", output_values=raw1.output_values))
    ri1 = mig.ri_old
    t0_fates = {_label(c): mall["fate_of"][ri1.rank(c)] for c in t0}
    comp_fates = [{"row": n, "state": _label(c), "outcome": o, "fate": mall["fate_of"][ri1.rank(c)],
                   "new_states": [_label(mig.ri_new.unrank(y)) for y in mig.new_of(ri1.rank(c))]}
                  for n, c, o in ex.PENSION_PUBLISHED_COMPLEMENT]
    conflicting = [_label(mig.ri_new.unrank(y)) for y, cat in enumerate(mall["category_of"])
                   if cat == "conflicting"]
    return {"age_cuts": list(age_cuts), "contribution_cuts": list(contrib_cuts),
            "schema": describe_schema(new), "states": mig.ri_new.size,
            "t0_fates": dict(Counter(t0_fates.values())), "t0_fate_by_row": t0_fates,
            "t0_misaligned_rows": sum(f in ("merged", "reshaped") for f in t0_fates.values()),
            "t0_single_state_rows": sum(f == "unchanged" for f in t0_fates.values()),
            "mapped_t0": strip(m0), "completion": stats,
            "review_breakdown": {k: m0["categories"][k] for k in ("partial", "conflicting", "unapproved")},
            "liberal_mapping": {"rows": lrep["rows"], "multi_hit_tuples": lrep["multi_hit_tuples"],
                                "conflicting_tuples": lrep["conflicting_tuples"],
                                "misaligned_entries": len(conv["misaligned_entries"]),
                                "misaligned_rows": len({i for i, _ in conv["misaligned_entries"]})},
            "dmn_raw_intervals": {"gap_regions": len(a.gaps), "gap_tuples": len(raw_tuples),
                                  "partial_bins": raw_partial},
            "raw_table1_misaligned_rules": len({i for i, _ in conv1["misaligned_entries"]}),
            "published_complement": {
                "unchanged": sum(f["fate"] == "unchanged" for f in comp_fates),
                "fates": dict(Counter(f["fate"] for f in comp_fates)),
                "changed": [f for f in comp_fates if f["fate"] != "unchanged"]},
            "reuse_24_approved": {**strip(mall), "re_review": mall["new_states"] - mall["categories"]["identical"],
                                  "no_outcome": review_load(mall), "conflicting_states": conflicting}}


def cut_points() -> dict:
    out = {"definitions": "S-2 .. S-5 in latc_check/sensitivity.py", "cases": []}
    for an, ac in AGE_CUTS.items():
        for cn, cc in CONTRIB_CUTS.items():
            r = cut_point_case(ac, cc)
            r["age_label"], r["contribution_label"] = an, cn
            out["cases"].append(r)
    return out


# -- B: merged and split values (Car, Nursery) ----------------------------------------------------

def fixed_t0(full: DecisionTable, name: str, seed: int = SEED, share: float = 0.5) -> DecisionTable:
    """S-9."""
    rng = random.Random(f"{seed}:{name}:t0")
    n = len(full.rows)
    idx = sorted(rng.sample(range(n), round(share * n)))
    return full.with_rows([full.rows[i] for i in idx])


def _as_dict(table: DecisionTable) -> dict:
    return {r.condition: r.outcome for r in table.rows}


def value_change(old_dims, new_dims, full: dict, t0: dict, dmn: bool = True) -> dict:
    mig = Migration(old_dims, new_dims)
    mfull = mig.apply(full)
    m0 = mig.apply(t0)
    stats = completion_stats(new_dims, m0["table"], dmn)
    if stats["missing"] != review_load(m0):
        raise AssertionError("review load does not equal COMPLETE on the mapped T0")
    return {"states": mig.ri_new.size,
            "full_table_conflicts": mfull["categories"]["conflicting"],
            "full_table_conflict_original_states": mfull["conflict_old_states"],
            "functional": mfull["categories"]["conflicting"] == 0,
            "full_table": strip(mfull), "mapped_t0": strip(m0), "completion": stats,
            "review_breakdown": {k: m0["categories"][k] for k in ("partial", "conflicting", "unapproved")}}


def merge_split(name: str, full: DecisionTable, t0: DecisionTable, dmn: bool = True,
                attributes=None) -> dict:
    dims = table_dims(full)
    fd, td = _as_dict(full), _as_dict(t0)
    out = {"dataset": name, "t0_rows": len(t0.rows), "baseline": completion_stats(dims, t0, dmn),
           "merges": [], "splits": []}
    for k, d in enumerate(dims):
        if attributes is not None and d.name not in attributes:
            continue
        for i in range(len(d.labels) - 1):
            new = dims[:k] + (merge_values(d, i),) + dims[k + 1:]
            r = value_change(dims, new, fd, td, dmn)
            out["merges"].append({"attribute": d.name, "values": [d.labels[i], d.labels[i + 1]], **r})
        for i in range(len(d.labels)):
            o, n = split_value(d, i)
            r = value_change(dims[:k] + (o,) + dims[k + 1:], dims[:k] + (n,) + dims[k + 1:], fd, td, dmn)
            out["splits"].append({"attribute": d.name, "value": d.labels[i], **r})
    return out


# -- C: valid-state constraints -------------------------------------------------------------------

def _int_bounds(iv: Interval) -> tuple[int, int]:
    lo = math.ceil(iv.lo) if iv.lo_closed else math.floor(iv.lo) + 1
    hi = math.floor(iv.hi) if iv.hi_closed else math.ceil(iv.hi) - 1
    return lo, hi


def contribution_age_constraint(dims, min_age: int = 18):
    """Valid iff some integer pair (c, a) in the state's bins has c <= a - min_age."""
    cb, ab = dict(dims[2].bins()), dict(dims[3].bins())

    def ok(cond) -> bool:
        return _int_bounds(cb[cond[2]])[0] <= _int_bounds(ab[cond[3]])[1] - min_age
    return ok


def constraint_case(dims, table: DecisionTable, explicit_rules=None) -> dict:
    """Valid space, review load before / after, exactness checks, DMN native and explicit."""
    free = DecisionTable(table.attributes, list(table.rows), table.outcomes)
    before = exact_complement(free)
    after = exact_complement(table)
    full = prod(a.card for a in table.attributes)
    valid = table.valid_space_size()
    # Independent checks: filtering the unconstrained complement, and the generalised deficits.
    filtered = [c for c in before if table.is_valid(c)]
    inside = table.with_rows([r for r in table.rows if table.is_valid(r.condition)])
    deficit_problems = latc.deficit_check(after, inside, latc.valid_space_deficits(inside))
    reading_b = compare(latc.latc_odometer(table), table)
    d = from_exact(free, numeric_of(dims))
    a = analyse(d)
    native, _ = expand(a.gaps, d.inputs)
    impossible = sum(1 for c in native if not table.is_valid(c))
    kept = [c for c in native if table.is_valid(c)]
    out = {"states": full, "valid": valid, "excluded": full - valid,
           "t0_rows": len(table.rows),
           "t0_rows_outside_valid": sum(1 for r in table.rows if not table.is_valid(r.condition)),
           "missing_before": len(before), "missing_after": len(after),
           "complete_equals_filtered_unconstrained": filtered == after,
           "deficit_check_problems": len(deficit_problems),
           "reading_b": {"exact": reading_b.exact, "missed": reading_b.missed,
                         "outside_space": reading_b.outside_space},
           "dmn_native": {"gap_regions": len(a.gaps), "gap_tuples": len(native),
                          "impossible_reported_as_gaps": impossible,
                          "filtered_equals_complete": set(kept) == set(after) and len(kept) == len(after)}}
    if explicit_rules is not None:
        e = DMNTable(d.inputs, d.rules + list(explicit_rules), "UNIQUE",
                     output_values=tuple(d.output_values) + ("IMPOSSIBLE",))
        ea = analyse(e)
        et, _ = expand(ea.gaps, e.inputs)
        out["dmn_explicit_impossible_rules"] = {
            "extra_rules": len(explicit_rules), "gap_regions": len(ea.gaps), "gap_tuples": len(et),
            "gaps_equal_complete": set(et) == set(after) and len(et) == len(after),
            "overlap_pairs": len(ea.overlaps)}
    return out


def _bin_rule(dims, cond, out="IMPOSSIBLE") -> Rule:
    return Rule(tuple(dict(d.bins())[v] if d.numeric else Point(v) for d, v in zip(dims, cond)), out)


def pension_constraints() -> list:
    out = []
    v1 = pension_schema()
    base = ex.pension_table()
    rv_states = [r.condition for r in ex.pension_completed().rows if r.outcome == RV]
    out.append({"case": "pension", "constraint": "none", "schema": describe_schema(v1),
                **constraint_case(v1, base)})
    t = DecisionTable(base.attributes, list(base.rows), base.outcomes,
                      constraint=lambda c, s=frozenset(rv_states): c not in s)
    out.append({"case": "pension", "constraint": f"exclude the {len(rv_states)} states the experts marked Rv",
                "excluded_states": [_label(c) for c in rv_states], "schema": describe_schema(v1),
                **constraint_case(v1, t, [_bin_rule(v1, c) for c in rv_states])})
    for cuts in ((60, 65), (45, 60, 65)):
        dims = pension_schema(cuts)
        mapped = Migration(v1, dims).apply(_t0_dict())["table"]
        ok = contribution_age_constraint(dims)
        t = DecisionTable(mapped.attributes, list(mapped.rows), mapped.outcomes, constraint=ok)
        bad = [c for c in t.full_space() if not ok(c)]
        # The excluded bins form one box here (contribution >= 30 and age < 45).
        boxes = sorted({(c[2], c[3]) for c in bad})
        rules = [Rule((ANY, ANY, dict(dims[2].bins())[cb], dict(dims[3].bins())[ab]), "IMPOSSIBLE")
                 for cb, ab in boxes]
        out.append({"case": "pension", "constraint": "contribution years <= age - 18 (integer bins)",
                    "schema": describe_schema(dims), "excluded_states": [_label(c) for c in bad],
                    **constraint_case(dims, t, rules)})
    return out


DATASET_PAIRS = {"car": (("doors", "2"), ("persons", "more")),
                 "nursery": (("form", "foster"), ("children", "more"))}


def dataset_constraints(name: str, full: DecisionTable, t0: DecisionTable, seed: int = SEED,
                        sample_share: float = 0.1, dmn: bool = True) -> list:
    dims = table_dims(full)
    names = full.names
    out = [{"case": name, "constraint": "none", **constraint_case(dims, t0)}]
    (a1, v1), (a2, v2) = DATASET_PAIRS[name]
    k1, k2 = names.index(a1), names.index(a2)
    t = DecisionTable(t0.attributes, list(t0.rows), t0.outcomes,
                      constraint=lambda c: not (c[k1] == v1 and c[k2] == v2))
    rule = Rule(tuple(Point(v1) if j == k1 else Point(v2) if j == k2 else ANY for j in range(len(names))),
                "IMPOSSIBLE")
    out.append({"case": name, "constraint": f"exclude every state with {a1}={v1} and {a2}={v2}",
                **constraint_case(dims, t, [rule])})
    rng = random.Random(f"{seed}:{name}:constraint")
    space = list(full.full_space())
    excluded = frozenset(rng.sample(space, round(sample_share * len(space))))
    t = DecisionTable(t0.attributes, list(t0.rows), t0.outcomes, constraint=lambda c: c not in excluded)
    rules = [Rule(tuple(Point(v) for v in c), "IMPOSSIBLE") for c in sorted(excluded)] if dmn else None
    out.append({"case": name, "constraint": f"exclude a random {sample_share:.0%} of the states "
                                            f"({len(excluded)}), seed '{seed}:{name}:constraint'",
                **constraint_case(dims, t, rules)})
    return out


# -- D: policy change -------------------------------------------------------------------------------

def policy_rule(dims, f: int = 60, m: int = 65, c: int = 30, rv: str = RV) -> DMNTable:
    """The pension rule (dmn_compare.pension_compact_dmn) with its thresholds as parameters.

    f = pension age for F, m = pension age for M (f <= m), c = contribution
    threshold, rv = the outcome of activity I with fewer than c years.
    """
    M, F, D, I = Point("M"), Point("F"), Point("D"), Point("I")
    rules = [
        Rule((ANY, ANY, ANY, below(f)), "NO"),
        Rule((M, ANY, ANY, half_open(f, m)), "NO"),
        Rule((M, D, ANY, at_least(m)), "YES"),
        Rule((M, I, at_least(c), at_least(m)), "YES"),
        Rule((M, I, below(c), at_least(m)), rv),
        Rule((F, D, ANY, at_least(f)), "YES"),
        Rule((F, I, at_least(c), at_least(f)), "YES"),
        Rule((F, I, below(c), at_least(f)), rv),
    ]
    return DMNTable(tuple(d.dmn_input() for d in dims), rules, "UNIQUE", output_values=("YES", "NO", RV))


def rule_outcomes(dims, **params) -> dict:
    exact, conv = to_exact(policy_rule(dims, **params))
    rep = structural_report(exact)
    if conv["misaligned_entries"] or rep["coverage"] != 1.0 or not rep["single_hit"]:
        raise ValueError(f"rule {params} is not aligned with schema {describe_schema(dims)}")
    return {r.condition: r.outcome for r in exact.rows}


PENSION_VERSIONS = [
    ("v2", "M pension age 65 -> 67; schema keeps only the cuts the new rule needs", (60, 67), (30,),
     {"m": 67}),
    ("v2-refined", "M pension age 65 -> 67; schema keeps the old cut 65 as well", (60, 65, 67), (30,),
     {"m": 67}),
    ("v2b", "M 65 -> 67 and F 60 -> 62", (62, 67), (30,), {"f": 62, "m": 67}),
    ("v3", "contribution threshold 30 -> 35", (60, 65), (35,), {"c": 35}),
    ("v4", "outcome-only change: activity I with fewer than 30 years gets NO instead of Rv; "
           "no cut point moves", (60, 65), (30,), {"rv": "NO"}),
]


def pension_policy_case(age_cuts, contrib_cuts, params: dict) -> dict:
    v1 = pension_schema()
    v2 = pension_schema(age_cuts, contrib_cuts)
    mig = Migration(v1, v2)
    v1_out = rule_outcomes(v1)
    v2_out = rule_outcomes(v2, **params)
    t0, comp = _t0_dict(), _complement_dict()
    approved = {**t0, **comp}
    if approved != v1_out:
        raise AssertionError("the parametrised rule does not reproduce the approved table")
    mall, m0 = mig.apply(approved), mig.apply(t0)
    v1_by_rank = {mig.ri_old.rank(c): o for c, o in v1_out.items()}
    v2_by_rank = {mig.ri_new.rank(c): o for c, o in v2_out.items()}
    affected = {y for y in range(mig.ri_new.size)
                if any(v1_by_rank[x] != v2_by_rank[y] for x in mig.old_of(y))}
    flagged = {y for y, cat in enumerate(mall["category_of"]) if cat != "identical"}
    wrong = Counter(mall["category_of"][y] for y, o in mall["inherited"].items() if o != v2_by_rank[y])
    lab = lambda y: _label(mig.ri_new.unrank(y))
    fates = lambda rows: dict(Counter(mall["fate_of"][mig.ri_old.rank(c)] for c in rows))
    return {"schema_v2": describe_schema(v2), "rule_v2": params, "v1_states": mig.ri_old.size,
            "v2_states": mig.ri_new.size,
            "approved_fates": {"t0": fates(t0), "complement": fates(comp)},
            "approved_meaning_changed": [
                {"state": _label(c), "outcome": o, "source": "T0" if c in t0 else "complement",
                 "fate": mall["fate_of"][mig.ri_old.rank(c)],
                 "new_states": [lab(y) for y in mig.new_of(mig.ri_old.rank(c))]}
                for c, o in approved.items() if mall["fate_of"][mig.ri_old.rank(c)] != "unchanged"],
            "v2_categories": mall["categories"], "re_review": len(flagged),
            "no_outcome": review_load(mall),
            "policy_affected": len(affected), "policy_affected_states": sorted(lab(y) for y in affected),
            "affected_within_re_review": affected <= flagged,
            "affected_not_flagged": sorted(lab(y) for y in affected - flagged),
            "wrong_inherited_outcomes": {c: wrong[c] for c in INHERITING},
            "t0_only": {"categories": m0["categories"], "no_approved_row": m0["categories"]["unapproved"],
                        "partly_approved": m0["categories"]["partial"]}}


def pension_policy() -> list:
    return [{"version": v, "change": desc, **pension_policy_case(a, c, p)}
            for v, desc, a, c, p in PENSION_VERSIONS]


def nursery_policy(full: DecisionTable, t0: DecisionTable) -> list:
    dims = table_dims(full)
    k = full.names.index("children")
    ch = dims[k]
    if ch.labels != ("1", "2", "3", "more"):
        raise ValueError("unexpected children domain")
    changes = []
    changes.append(("N1", "merge children 3 and more into one value '3+'", dims,
                    dims[:k] + (Dim("children", ("1", "2", "3+"), (frozenset({"1"}), frozenset({"2"}),
                                                                  frozenset({"3", "more"}))),) + dims[k + 1:]))
    # Boundary move: 'more' is read as the atoms {4, 5+}; the boundary between the last two
    # values moves from 3 | 4+ to 3-4 | 5+.
    old = Dim("children", ch.labels, (frozenset({"1"}), frozenset({"2"}), frozenset({"3"}),
                                      frozenset({"4", "5+"})))
    new = Dim("children", ("1", "2", "3-4", "5+"), (frozenset({"1"}), frozenset({"2"}),
                                                     frozenset({"3", "4"}), frozenset({"5+"})))
    changes.append(("N2", "move the boundary between 3 and more: 1, 2, 3, more becomes 1, 2, 3-4, 5+ (more = {4, 5+})",
                    dims[:k] + (old,) + dims[k + 1:], dims[:k] + (new,) + dims[k + 1:]))
    out = []
    fd, td = _as_dict(full), _as_dict(t0)
    for v, desc, o, n in changes:
        mig = Migration(o, n)
        mfull, m0 = mig.apply(fd), mig.apply(td)
        out.append({"version": v, "change": desc, "v1_states": mig.ri_old.size, "v2_states": mig.ri_new.size,
                    "all_rows_approved": {**strip(mfull), "re_review": mfull["new_states"] - mfull["categories"]["identical"],
                                          "no_outcome": review_load(mfull)},
                    "t0_approved": {**strip(m0), "re_review": m0["new_states"] - m0["categories"]["identical"],
                                    "no_outcome": review_load(m0)}})
    return out


# -- runner -----------------------------------------------------------------------------------------

def _yn(b) -> str:
    return "yes" if b else "NO"


def write_summary(res: dict, path: str) -> None:
    L = []
    w = L.append
    m = res["meta"]
    w("# Sensitivity and policy change\n")
    w(f"Generated by `python run_sensitivity.py` (latc_check {m['version']}, Python {m['python']}). "
      f"Seed {m['seed']}. Definitions S-1 to S-9 are in `latc_check/sensitivity.py`. Everything except "
      "the times is deterministic.\n")
    w("Terms. *Fate* of an approved row in a new schema: unchanged (same box), merged (now inside a larger "
      "state), split (now the union of several states), reshaped (several states, some only partly inside). "
      "*Category* of a new state: identical / contained / uniform (inherits an outcome from approved rows), "
      "conflicting (approved rows with different outcomes meet in it), partial (meets approved and "
      "unapproved states), unapproved. *Missing* = COMPLETE on the mapped T0 = conflicting + partial + "
      "unapproved (checked in every run).\n")

    A = res["cut_points"]["cases"]
    w("## A. Pension: cut points\n")
    w("T0 = Table 1a mapped through its raw intervals. *Misaligned* = T0 rows whose interval only partly "
      "covers some new bin (fate merged or reshaped). *Liberal mapping* = `dmn.to_exact` (every bin a row "
      "touches): multi-hit / conflicting tuples. DMN regions are for the mapped T0 in the new bins; the "
      "sweep on T0's raw intervals gives 7 regions in every case because it uses rule bounds, not bins.\n")
    w("| Age cuts | contribution cuts | states | T0 rows unchanged / split / merged / reshaped | misaligned | "
      "liberal multi-hit / conflicts | mapped T0 rows | missing | of which partial / conflicting | "
      "DMN regions | DMN gaps = COMPLETE | raw Table 1 rules misaligned |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in A:
        f = c["t0_fates"]
        s = c["completion"]
        rb = c["review_breakdown"]
        lm = c["liberal_mapping"]
        w(f"| {c['age_label']} | {c['contribution_label']} | {c['states']} | "
          f"{f.get('unchanged', 0)} / {f.get('split', 0)} / {f.get('merged', 0)} / {f.get('reshaped', 0)} | "
          f"{c['t0_misaligned_rows']} | {lm['multi_hit_tuples']} / {lm['conflicting_tuples']} | "
          f"{s['t0_rows']} | {s['missing']} | {rb['partial']} / {rb['conflicting']} | {s['dmn_gap_regions']} | "
          f"{_yn(s['dmn_gaps_equal_complete'])} | {c['raw_table1_misaligned_rules']} |")
    w("")
    w("Meaning of the 16 published complementary rows, and reuse of all 24 approved rows "
      "(T0 + complement with the experts' outcomes):\n")
    w("| Age cuts | contribution cuts | complement rows unchanged | changed (fate: count) | "
      "new states identical / contained / uniform / conflicting | re-review (not identical) | no outcome (conflicting) |")
    w("|---|---|---|---|---|---|---|")
    for c in A:
        p = c["published_complement"]
        r = c["reuse_24_approved"]
        k = r["categories"]
        ch = ", ".join(f"{f} {n}" for f, n in p["fates"].items() if f != "unchanged") or "–"
        w(f"| {c['age_label']} | {c['contribution_label']} | {p['unchanged']}/16 | {ch} | "
          f"{k['identical']} / {k['contained']} / {k['uniform']} / {k['conflicting']} | {r['re_review']} | "
          f"{r['no_outcome']} |")
    w("")

    w("## B. Car and Nursery: merged and split values\n")
    w("T0 = 50 % of the rows (S-9). *Conflicts* = merged states whose original states carry different "
      "classes in the full table (S-8); a merge with 0 conflicts keeps the table a function. A split "
      "duplicates the rows of the value, so it never creates conflicts.\n")
    for key in ("car", "nursery"):
        b = res["merge_split"].get(key)
        if not b:
            continue
        base = b["baseline"]
        w(f"### {res['titles'][key]}\n")
        w(f"Baseline: {base['states']} states, T0 {base['t0_rows']} rows, missing {base['missing']}, "
          f"DMN regions {base.get('dmn_gap_regions', '–')}.\n")
        w("| change | attribute | values | states | full-table conflicts (original states) | functional | "
          "mapped T0 rows | missing | partial / conflicting / unapproved | DMN regions | DMN = COMPLETE |")
        w("|---|---|---|---|---|---|---|---|---|---|---|")
        for kind, items in (("merge", b["merges"]), ("split", b["splits"])):
            for it in items:
                s, rb = it["completion"], it["review_breakdown"]
                vals = " + ".join(it["values"]) if kind == "merge" else it["value"]
                w(f"| {kind} | {it['attribute']} | {vals} | {it['states']} | {it['full_table_conflicts']} "
                  f"({it['full_table_conflict_original_states']}) | {_yn(it['functional'])} | {s['t0_rows']} | "
                  f"{s['missing']} | {rb['partial']} / {rb['conflicting']} / {rb['unapproved']} | "
                  f"{s.get('dmn_gap_regions', '–')} | {_yn(s['dmn_gaps_equal_complete']) if 'dmn_gaps_equal_complete' in s else '–'} |")
        n_func = sum(it["functional"] for it in b["merges"])
        w(f"\n{n_func} of {len(b['merges'])} adjacent merges keep the table a function.\n")

    w("## C. Valid-state constraints\n")
    w("*Before* / *after* = missing states without / with the constraint. *COMPLETE exact* = COMPLETE "
      "equals the unconstrained complement filtered by the constraint, and the generalised deficit check "
      "(`valid_space_deficits`) passes. *DMN native* has no constraint: impossible states come back as gaps "
      "and must be filtered outside DMN. *Explicit rules* = the impossible states added to the DMN table "
      "as rules with output IMPOSSIBLE.\n")
    w("| case | constraint | states | valid | excluded | T0 rows (outside valid) | missing before | missing after | "
      "COMPLETE exact | Reading B exact (outside space) | DMN native gap tuples (impossible) | DMN filtered = COMPLETE | "
      "explicit rules: rules / gaps = COMPLETE / overlaps |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in res["constraints"]:
        e = c.get("dmn_explicit_impossible_rules")
        ex_s = (f"{e['extra_rules']} / {_yn(e['gaps_equal_complete'])} / {e['overlap_pairs']}" if e else "–")
        dn = c["dmn_native"]
        w(f"| {c['case']} | {c['constraint']} | {c['states']} | {c['valid']} | {c['excluded']} | "
          f"{c['t0_rows']} ({c['t0_rows_outside_valid']}) | {c['missing_before']} | {c['missing_after']} | "
          f"{_yn(c['complete_equals_filtered_unconstrained'] and c['deficit_check_problems'] == 0)} | "
          f"{_yn(c['reading_b']['exact'])} ({c['reading_b']['outside_space']}) | "
          f"{dn['gap_tuples']} ({dn['impossible_reported_as_gaps']}) | {_yn(dn['filtered_equals_complete'])} | {ex_s} |")
    w("")

    w("## D. Policy change\n")
    w("Pension v1 = the published schema and rule; approved rows = T0 (8) + published complement (16). "
      "v2 rules are the compact rule with the moved threshold (`policy_rule`). *Re-review* = new states "
      "that are not identical to an approved row (S-6). *Policy-affected* = new states containing an input "
      "whose decision changes (S-7). *Wrong inherited* = states whose inherited (old) outcome differs "
      "from the new rule's.\n")
    w("| version | change | v2 states | approved rows T0 / complement whose meaning changed | "
      "v2 identical / contained / uniform / conflicting | re-review | no outcome | policy-affected | "
      "affected within re-review | wrong inherited (contained / uniform) | T0 only: no approved row / partly |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for p in res["policy"]["pension"]:
        k = p["v2_categories"]
        f0, fc = p["approved_fates"]["t0"], p["approved_fates"]["complement"]
        ch0 = 8 - f0.get("unchanged", 0)
        chc = 16 - fc.get("unchanged", 0)
        wi = p["wrong_inherited_outcomes"]
        w(f"| {p['version']} | {p['change']} | {p['v2_states']} | {ch0} / {chc} | "
          f"{k['identical']} / {k['contained']} / {k['uniform']} / {k['conflicting']} | {p['re_review']} | "
          f"{p['no_outcome']} | {p['policy_affected']} | {_yn(p['affected_within_re_review'])} | "
          f"{wi['contained']} / {wi['uniform']} | {p['t0_only']['no_approved_row']} / {p['t0_only']['partly_approved']} |")
    w("")
    w("Approved rows whose meaning changed, per version:\n")
    for p in res["policy"]["pension"]:
        rows = "; ".join(f"{r['state']} ({r['source']}, {r['fate']})" for r in p["approved_meaning_changed"]) or "none"
        w(f"* **{p['version']}**: {rows}.")
        if p["affected_not_flagged"]:
            w(f"  Policy-affected but not flagged by the schema comparison: {', '.join(p['affected_not_flagged'])}.")
    w("")
    nur = res["policy"].get("nursery")
    if nur:
        w("Nursery (full table approved, and T0 = 50 % approved):\n")
        w("| version | change | v1 / v2 states | v1 rows unchanged / merged / split / reshaped | "
          "all approved: identical / contained / uniform / conflicting, re-review | T0 approved: re-review, "
          "no outcome (partial / conflicting / unapproved) |")
        w("|---|---|---|---|---|---|")
        for p in nur:
            a, t = p["all_rows_approved"], p["t0_approved"]
            f, k, kt = a["fates"], a["categories"], t["categories"]
            w(f"| {p['version']} | {p['change']} | {p['v1_states']} / {p['v2_states']} | "
              f"{f['unchanged']} / {f['merged']} / {f['split']} / {f['reshaped']} | "
              f"{k['identical']} / {k['contained']} / {k['uniform']} / {k['conflicting']}, {a['re_review']} | "
              f"{t['re_review']}, {t['no_outcome']} ({kt['partial']} / {kt['conflicting']} / {kt['unapproved']}) |")
        w("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--datasets", default="car,nursery")
    p.add_argument("--no-dmn", action="store_true", help="skip the DMN analyses on Car / Nursery")
    p.add_argument("--data-dir", default=None)
    p.add_argument("--out", default=os.path.join("results", "sensitivity"))
    args = p.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    start = time.perf_counter()
    res = {"meta": {"version": __version__, "python": platform.python_version(),
                    "platform": platform.platform(), "seed": args.seed}, "titles": {}}

    def dump(name, obj):
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, default=str)

    print("A. pension cut points ...", flush=True)
    res["cut_points"] = cut_points()
    dump("cut_points.json", res["cut_points"])
    res["constraints"] = pension_constraints()
    res["policy"] = {"pension": pension_policy()}
    res["merge_split"] = {}
    for key in [k for k in args.datasets.split(",") if k]:
        full, info = datasets.load(key, args.data_dir)
        res["titles"][key] = info["title"]
        t0 = fixed_t0(full, key, args.seed)
        print(f"B/C. {info['title']} ...", flush=True)
        res["merge_split"][key] = merge_split(key, full, t0, not args.no_dmn)
        res["constraints"] += dataset_constraints(key, full, t0, args.seed, dmn=not args.no_dmn)
        if key == "nursery":
            res["policy"]["nursery"] = nursery_policy(full, t0)
    dump("merge_split.json", res["merge_split"])
    dump("constraints.json", res["constraints"])
    dump("policy_change.json", res["policy"])
    res["meta"]["total_seconds"] = time.perf_counter() - start
    dump("meta.json", res["meta"])
    write_summary(res, os.path.join(args.out, "SUMMARY.md"))
    print(f"wrote {args.out} in {res['meta']['total_seconds']:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
