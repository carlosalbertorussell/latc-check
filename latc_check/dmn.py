"""DMN decision tables and their gap / overlap analysis (baseline B4).

Model
-----
A DMN table has input columns, one output column, a hit policy (UNIQUE, ANY,
FIRST or PRIORITY) and rules.  An input entry is ``ANY`` ("-"), a ``Point``, a
``OneOf`` list of points, a numeric ``Interval`` with open or closed bounds, or
``Not`` of a point, list or interval (S-FEEL not(...)).  A negated numeric
entry becomes a ``Union`` of up to two intervals, so a rule can be more than
one hyper-rectangle, as for multi-valued entries in Calvanese et al.  An input is either *enumerated* (declared allowed values) or
*numeric* (a declared range, optionally with declared bins used only to
convert to and from the exact-tuple model).

Analysis
--------
This module follows the geometric reading of Calvanese et al. ("Semantics and
Analysis of DMN Decision Tables", BPM 2016; extended in Information Systems,
2018).  Each rule is a hyper-rectangle in the input space.  The analysis
sweeps one dimension at a time, keeping the set of rules still active in the
current slab:

* a slab where no rule is active is a *missing rule* (gap), a hyper-rectangle
  that spans the full domain in every later dimension;
* in the last dimension, a segment where two or more rules are active gives
  an overlapping rule set; the maximal such sets are the output of Calvanese
  et al.'s overlap algorithm, and the pairs inside them are also kept;
* adjacent gap rectangles are then merged.

The choices made where the description leaves room (D-1 .. D-7):

D-1  Numeric dimensions are real intervals.  The sweep's elementary cells are
     every rule bound inside the declared range plus the range's own bounds,
     kept as alternating point cells [p, p] and open cells (p, q), so open and
     closed bounds are handled exactly.  Integer-valued inputs are NOT
     special-cased: a gap such as (59, 60) that holds no integer would still
     be reported.  None arises in the tables used here.
D-2  Enumerated dimensions use the declared allowed values (DMN inputValues)
     when given, otherwise the values the rules mention.  ``from_exact``
     makes this choice explicit; both are reported, because a DMN tool can
     only find a missing value if the value is declared.
D-3  Within a dimension, cells are grouped into one segment when they have
     the same active rule set and are contiguous: in numeric order, or in
     declared order for enumerations ("contiguous", the default, which treats
     an enumeration as an ordered line).  ``enum_grouping="set"`` groups
     enumeration values with the same active set regardless of order, which
     DMN can write as a list entry ("a","b").
D-4  Gap merging is greedy: for each dimension in turn, gaps that agree on
     all other dimensions are merged when their segments touch (numeric) or
     can form one segment (enumerations, as in D-3).  This repeats to a fixed
     point.  The result is a cover of the gap space by disjoint rectangles,
     not necessarily a minimal one (minimal rectangle cover is NP-hard in
     general); the region count depends on dimension order.
D-5  Overlaps are reported as maximal rule sets (as in Calvanese et al.) and
     as rule pairs, each with one witness region.  The overlaps do not depend
     on the hit policy; ``violations`` applies it: UNIQUE flags every
     overlapping pair, ANY flags pairs with different outputs, FIRST and
     PRIORITY flag masked rules (a rule covered by one rule of higher
     priority).  PRIORITY takes priorities from the order of the declared
     output values, as the DMN standard does.
D-6  DMN has no valid-state constraint.  States that are impossible in the
     domain are gaps to DMN.  ``compare`` reports them natively and also
     after filtering expanded gaps with the exact model's constraint, which
     happens outside DMN.
D-7  Entries are clipped to the declared range or allowed values.  Values
     outside them are input-validation errors in DMN and not part of the
     analysed space.  A rule entry naming an undeclared value is recorded in
     ``Analysis.undeclared``.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Sequence

from .model import Attribute, DecisionTable, Row

INF = math.inf
HIT_POLICIES = ("UNIQUE", "ANY", "FIRST", "PRIORITY")


# -- entries -------------------------------------------------------------------

class _Any:
    def __repr__(self) -> str:
        return "ANY"


ANY = _Any()


@dataclass(frozen=True)
class Point:
    value: object


@dataclass(frozen=True)
class OneOf:
    values: frozenset


@dataclass(frozen=True)
class Interval:
    lo: float = -INF
    hi: float = INF
    lo_closed: bool = True
    hi_closed: bool = True

    def is_empty(self) -> bool:
        return self.lo > self.hi or (self.lo == self.hi and not (self.lo_closed and self.hi_closed))

    def contains(self, x: float) -> bool:
        if x < self.lo or x > self.hi:
            return False
        if x == self.lo and not self.lo_closed:
            return False
        return not (x == self.hi and not self.hi_closed)

    def intersect(self, o: "Interval") -> "Interval":
        if self.lo > o.lo:
            lo, lc = self.lo, self.lo_closed
        elif self.lo < o.lo:
            lo, lc = o.lo, o.lo_closed
        else:
            lo, lc = self.lo, self.lo_closed and o.lo_closed
        if self.hi < o.hi:
            hi, hc = self.hi, self.hi_closed
        elif self.hi > o.hi:
            hi, hc = o.hi, o.hi_closed
        else:
            hi, hc = self.hi, self.hi_closed and o.hi_closed
        return Interval(lo, hi, lc, hc)

    def intersects(self, o: "Interval") -> bool:
        return not self.intersect(o).is_empty()

    def issubset(self, o: "Interval") -> bool:
        return self.intersect(o) == self

    def feel(self) -> str:
        """FEEL unary test for this interval."""
        f = _num
        if self.lo == self.hi:
            return f(self.lo)
        if self.lo == -INF:
            return ("<= " if self.hi_closed else "< ") + f(self.hi)
        if self.hi == INF:
            return (">= " if self.lo_closed else "> ") + f(self.lo)
        return f"{'[' if self.lo_closed else '('}{f(self.lo)}..{f(self.hi)}{']' if self.hi_closed else ')'}"


@dataclass(frozen=True)
class Union:
    """A finite union of disjoint, non-touching intervals (from negation)."""
    parts: tuple

    def contains(self, x: float) -> bool:
        return any(p.contains(x) for p in self.parts)

    def is_empty(self) -> bool:
        return all(p.is_empty() for p in self.parts)


@dataclass(frozen=True)
class Not:
    """S-FEEL negation not(Term): every declared value the inner entry excludes."""
    entry: object


def _complement(e: Interval, d: Interval):
    """d minus e, as an Interval or a Union of the remaining parts."""
    e = e.intersect(d)
    if e.is_empty():
        return d
    left = Interval(d.lo, e.lo, d.lo_closed, not e.lo_closed).intersect(d)
    right = Interval(e.hi, d.hi, not e.hi_closed, d.hi_closed).intersect(d)
    parts = tuple(x for x in (left, right) if not x.is_empty())
    return parts[0] if len(parts) == 1 else Union(parts)


def _parts(s) -> tuple:
    return s.parts if isinstance(s, Union) else (s,)


def _bounds(s) -> list:
    return [b for p in _parts(s) for b in (p.lo, p.hi)]


def _meets(b: Interval, s) -> bool:
    return any(b.intersects(p) for p in _parts(s))


def _within(b: Interval, s) -> bool:
    """b is a subset of s (the parts of a Union never touch, so one part must hold b)."""
    return any(b.issubset(p) for p in _parts(s))


def _num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else repr(x)


def closed(lo, hi) -> Interval:
    return Interval(lo, hi, True, True)


def half_open(lo, hi) -> Interval:
    """[lo, hi)"""
    return Interval(lo, hi, True, False)


def at_least(x) -> Interval:
    """>= x"""
    return Interval(x, INF, True, True)


def below(x) -> Interval:
    """< x"""
    return Interval(-INF, x, True, False)


# -- table ---------------------------------------------------------------------

@dataclass(frozen=True)
class Input:
    name: str
    values: tuple | None = None     # enumerated: allowed values, in declared order
    domain: Interval | None = None  # numeric: declared range
    bins: tuple = ()                # numeric: ((label, Interval), ...) for conversion

    @property
    def numeric(self) -> bool:
        return self.domain is not None

    def full(self):
        return self.domain if self.numeric else frozenset(self.values)


@dataclass(frozen=True)
class Rule:
    entries: tuple
    output: str


@dataclass
class DMNTable:
    inputs: tuple
    rules: list
    hit_policy: str = "UNIQUE"
    output_name: str = "Result"
    output_values: tuple = ()

    def __post_init__(self) -> None:
        if self.hit_policy not in HIT_POLICIES:
            raise ValueError(f"hit policy {self.hit_policy!r} not supported")
        for r in self.rules:
            if len(r.entries) != len(self.inputs):
                raise ValueError("rule width does not match inputs")

    def review_size(self) -> dict:
        """What an expert has to read: rules and non-'-' cells."""
        return {"rules": len(self.rules),
                "non_wildcard_cells": sum(e is not ANY for r in self.rules for e in r.entries),
                "cells": len(self.rules) * (len(self.inputs) + 1)}


def entry_set(inp: Input, entry):
    """Normalise an entry to a frozenset (enumerated) or Interval (numeric)."""
    if isinstance(entry, Not):
        if entry.entry is ANY or isinstance(entry.entry, Not):
            raise TypeError(f"{inp.name}: not() takes a value, list or interval")
        inner = entry_set(inp, entry.entry)
        if not inp.numeric:
            return frozenset(inp.values) - inner
        return _complement(inner, inp.domain)
    if inp.numeric:
        if entry is ANY:
            return inp.domain
        if isinstance(entry, Point):
            return closed(entry.value, entry.value).intersect(inp.domain)
        if isinstance(entry, Interval):
            return entry.intersect(inp.domain)
        raise TypeError(f"{inp.name}: numeric input cannot take {entry!r}")
    allowed = frozenset(inp.values)
    if entry is ANY:
        return allowed
    if isinstance(entry, Point):
        return frozenset({entry.value}) & allowed
    if isinstance(entry, OneOf):
        return frozenset(entry.values) & allowed
    raise TypeError(f"{inp.name}: enumerated input cannot take {entry!r}")


def _mentioned(inp: Input, entry) -> set:
    if isinstance(entry, Point):
        return {entry.value}
    if isinstance(entry, OneOf):
        return set(entry.values)
    return set()


# -- sweep analysis -------------------------------------------------------------

@dataclass
class Analysis:
    gaps: list              # merged gap regions (tuple of segments)
    raw_gaps: int           # gap regions before merging
    overlaps: dict          # (i, j) -> witness region
    undeclared: list = field(default_factory=list)  # (rule, input, value)
    overlap_sets: dict = field(default_factory=dict)  # frozenset of rules -> witness region
    fires: frozenset = frozenset()  # FIRST/PRIORITY: rules that win somewhere

    @property
    def overlap_pairs(self) -> list:
        return sorted(self.overlaps)

    @property
    def maximal_overlap_sets(self) -> list:
        """Maximal sets of rules with a non-empty common intersection, as in
        Calvanese et al.: every such set is the active set of some leaf cell."""
        sets = list(self.overlap_sets)
        return sorted(tuple(sorted(x)) for x in sets if not any(x < o for o in sets))


def _cells(inp: Input, sets: list):
    """Elementary cells of one dimension and, per cell, the rules covering it."""
    if not inp.numeric:
        cells = list(inp.values)
        covers = [frozenset(i for i, s in enumerate(sets) if v in s) for v in cells]
        return cells, covers
    d = inp.domain
    pts = {d.lo, d.hi} | {b for s in sets for b in _bounds(s)}
    pts = sorted(p for p in pts if math.isfinite(p) and d.lo <= p <= d.hi)
    cells = []
    if d.lo == -INF:
        cells.append(Interval(-INF, pts[0], True, False) if pts else d)
    for k, p in enumerate(pts):
        point = closed(p, p)
        if not point.intersect(d).is_empty():
            cells.append(point)
        nxt = pts[k + 1] if k + 1 < len(pts) else (INF if d.hi == INF else None)
        if nxt is not None:
            cells.append(Interval(p, nxt, False, nxt == INF))
    reps = [c.lo if c.lo == c.hi else (c.hi - 1 if c.lo == -INF else c.lo + 1 if c.hi == INF
                                       else (c.lo + c.hi) / 2) for c in cells]
    covers = [frozenset(i for i, s in enumerate(sets) if s.contains(r)) for r in reps]
    return cells, covers


def _segment(inp: Input, cells: list):
    if not inp.numeric:
        return frozenset(cells)
    a, b = cells[0], cells[-1]
    return Interval(a.lo, b.hi, a.lo_closed, b.hi_closed)


def _groups(inp: Input, cells, covers, active, enum_grouping):
    """Yield (cells in segment, active rules) for one slab of one dimension."""
    if not inp.numeric and enum_grouping == "set":
        by = defaultdict(list)
        for c, cov in zip(cells, covers):
            by[cov & active].append(c)
        yield from ((cs, act) for act, cs in by.items())
        return
    run, run_act = [], None
    for c, cov in zip(cells, covers):
        act = cov & active
        if run and act != run_act:
            yield run, run_act
            run = []
        run.append(c)
        run_act = act
    if run:
        yield run, run_act


def analyse(table: DMNTable, enum_grouping: str = "contiguous", merge: bool = True) -> Analysis:
    inputs = table.inputs
    n = len(inputs)
    sets = [[entry_set(inp, r.entries[d]) for r in table.rules] for d, inp in enumerate(inputs)]
    dims = [_cells(inp, sets[d]) for d, inp in enumerate(inputs)]
    full = tuple(inp.full() for inp in inputs)
    gaps, overlaps, osets, fires = [], {}, {}, set()
    prio = rule_priorities(table)

    def sweep(d: int, active: frozenset, prefix: tuple) -> None:
        cells, covers = dims[d]
        for seg_cells, act in _groups(inputs[d], cells, covers, active, enum_grouping):
            seg = _segment(inputs[d], seg_cells)
            if not act:
                gaps.append(prefix + (seg,) + full[d + 1:])
            elif d == n - 1:
                region = prefix + (seg,)
                if prio is not None:
                    fires.add(max(act, key=lambda i: prio[i]))
                if len(act) > 1:
                    osets.setdefault(act, region)
                for pair in combinations(sorted(act), 2):
                    overlaps.setdefault(pair, region)
            else:
                sweep(d + 1, act, prefix + (seg,))

    sweep(0, frozenset(range(len(table.rules))), ())
    undeclared = [(i, inp.name, v) for d, inp in enumerate(inputs) if not inp.numeric
                  for i, r in enumerate(table.rules)
                  for v in _mentioned(inp, r.entries[d]) if v not in inp.values]
    merged = merge_regions(gaps, inputs, enum_grouping) if merge else gaps
    return Analysis(merged, len(gaps), overlaps, undeclared, osets, frozenset(fires))


def _merge_segments(inp: Input, segs: list, enum_grouping: str) -> list:
    if not inp.numeric:
        union = frozenset().union(*segs)
        if enum_grouping == "set":
            return [union]
        runs, run = [], []
        for v in inp.values:
            if v in union:
                run.append(v)
            elif run:
                runs.append(frozenset(run))
                run = []
        if run:
            runs.append(frozenset(run))
        return runs
    segs = sorted(segs, key=lambda s: (s.lo, not s.lo_closed))
    out = [segs[0]]
    for s in segs[1:]:
        cur = out[-1]
        if cur.hi == s.lo and (cur.hi_closed or s.lo_closed):
            out[-1] = Interval(cur.lo, s.hi, cur.lo_closed, s.hi_closed)
        else:
            out.append(s)
    return out


def merge_regions(regions: Sequence[tuple], inputs: Sequence[Input],
                  enum_grouping: str = "contiguous") -> list:
    """D-4: greedy merge of disjoint gap rectangles, to a fixed point."""
    regions = list(dict.fromkeys(regions))
    changed = True
    while changed:
        changed = False
        for d, inp in enumerate(inputs):
            groups = defaultdict(list)
            for r in regions:
                groups[r[:d] + r[d + 1:]].append(r[d])
            new = []
            for key, segs in groups.items():
                merged = _merge_segments(inp, segs, enum_grouping)
                changed |= len(merged) < len(segs)
                new += [key[:d] + (s,) + key[d:] for s in merged]
            regions = new
    return regions


def rule_priorities(table: DMNTable):
    """Priority key per rule (higher wins), or None for UNIQUE / ANY.

    FIRST: the order of the rules.  PRIORITY: the order of the declared output
    values, as in the DMN standard (first value = highest priority); rules with
    the same output share a priority.  Calvanese et al. model both as a
    priority function over rules, FIRST being the case where it follows the
    table order.
    """
    if table.hit_policy == "FIRST":
        return [-i for i in range(len(table.rules))]
    if table.hit_policy == "PRIORITY":
        if not table.output_values:
            raise ValueError("PRIORITY needs the output values in priority order")
        rank = {v: -k for k, v in enumerate(table.output_values)}
        return [rank[r.output] for r in table.rules]
    return None


def _rule_sets(table: DMNTable, i: int) -> list:
    return [entry_set(inp, table.rules[i].entries[d]) for d, inp in enumerate(table.inputs)]


def _rule_empty(table: DMNTable, i: int) -> bool:
    return any((not x) if isinstance(x, frozenset) else x.is_empty() for x in _rule_sets(table, i))


def _rule_within(table: DMNTable, a: int, b: int) -> bool:
    """Every input that triggers rule a also triggers rule b."""
    for inp, sa, sb in zip(table.inputs, _rule_sets(table, a), _rule_sets(table, b)):
        if not inp.numeric:
            if not sa <= sb:
                return False
        elif not all(p.is_empty() or _within(p, sb) for p in _parts(sa)):
            return False
    return True


def violations(table: DMNTable, analysis: Analysis) -> dict:
    """D-5: apply the hit policy to the geometric overlaps.

    An overlap is any non-empty intersection.  It violates UNIQUE always and
    ANY only when outputs differ.  Under FIRST and PRIORITY it is resolved by
    precedence; the correctness condition of Calvanese et al. is then that no
    rule is *masked*, i.e. covered by a single rule of higher priority
    (``masked_pairs``: (masked rule, masking rule)).  ``never_fire`` also lists
    rules that never win because the union of higher-priority rules covers them.
    """
    pairs = analysis.overlap_pairs
    differ = [p for p in pairs if table.rules[p[0]].output != table.rules[p[1]].output]
    prio = rule_priorities(table)
    masked, never = [], []
    if prio is not None:
        live = [i for i in range(len(table.rules)) if not _rule_empty(table, i)]
        masked = [(x, y) for x in live for y in live
                  if prio[y] > prio[x] and _rule_within(table, x, y)]
        never = [x for x in live if x not in analysis.fires]
    if table.hit_policy == "UNIQUE":
        bad = pairs
    elif table.hit_policy == "ANY":
        bad = differ
    else:
        bad = masked
    return {"overlapping_pairs": len(pairs), "pairs_with_different_outputs": len(differ),
            "maximal_overlap_sets": analysis.maximal_overlap_sets,
            "violating_pairs": bad, "masked_pairs": masked, "never_fire": never}


# -- conversion to and from the exact-tuple model --------------------------------------

def _labels(inp: Input, seg) -> tuple[list, bool]:
    """Exact-model labels a segment covers, and whether any is only partly covered."""
    if not inp.numeric:
        return [v for v in inp.values if v in seg], False
    if not inp.bins:
        raise ValueError(f"numeric input {inp.name!r} has no declared bins")
    hit = [(lab, b) for lab, b in inp.bins if _meets(b, seg)]
    return [lab for lab, _ in hit], any(not _within(b, seg) for _, b in hit)


def expand(regions: Sequence[tuple], inputs: Sequence[Input]) -> tuple[list, int]:
    """Exact tuples covered by regions; second value = partly covered labels seen."""
    out, partial = [], 0
    for reg in regions:
        per_dim = []
        for inp, seg in zip(inputs, reg):
            labs, part = _labels(inp, seg)
            partial += part
            per_dim.append(labs)
        out.extend(product(*per_dim))
    return out, partial


def exact_attributes(table: DMNTable) -> tuple:
    return tuple(Attribute(i.name, tuple(lab for lab, _ in i.bins) if i.numeric else tuple(i.values))
                 for i in table.inputs)


def to_exact(table: DMNTable, constraint=None) -> tuple[DecisionTable, dict]:
    """Discretise a DMN table into exact tuples using the declared bins.

    UNIQUE/ANY keep every tuple a rule produces (overlaps become duplicate
    rows the structural checks will flag); FIRST and PRIORITY keep the tuple of
    the highest-priority rule.
    """
    rows, seen, misaligned = [], set(), []
    prio = rule_priorities(table)
    order = (sorted(range(len(table.rules)), key=lambda k: -prio[k]) if prio is not None
             else range(len(table.rules)))
    for i in order:
        r = table.rules[i]
        per_dim = []
        for inp, e in zip(table.inputs, r.entries):
            labs, part = _labels(inp, entry_set(inp, e))
            if part:
                misaligned.append((i, inp.name))
            per_dim.append(labs)
        for cond in product(*per_dim):
            if prio is not None and cond in seen:
                continue
            seen.add(cond)
            rows.append(Row(cond, r.output))
    outcomes = table.output_values or tuple(dict.fromkeys(r.output for r in table.rules))
    return (DecisionTable(exact_attributes(table), rows, outcomes, constraint),
            {"misaligned_entries": misaligned})


def from_exact(table: DecisionTable, numeric: dict | None = None, hit_policy: str = "UNIQUE",
               values: str = "declared") -> DMNTable:
    """Exact-tuple table -> DMN with point entries (bin intervals for numeric).

    ``numeric``: {attribute: (domain Interval, ((label, Interval), ...))}.
    ``values``: "declared" uses the attribute's declared domain as the DMN
    allowed values; "observed" uses only the values T0 mentions (D-2).
    """
    numeric = numeric or {}
    inputs = []
    for j, a in enumerate(table.attributes):
        if a.name in numeric:
            dom, bins = numeric[a.name]
            inputs.append(Input(a.name, domain=dom, bins=tuple(bins)))
        elif values == "declared":
            inputs.append(Input(a.name, values=a.domain))
        else:
            seen = tuple(dict.fromkeys(r.condition[j] for r in table.rows))
            inputs.append(Input(a.name, values=seen))
    rules = []
    for r in table.rows:
        entries = []
        for inp, v in zip(inputs, r.condition):
            entries.append(dict(inp.bins)[v] if inp.numeric else Point(v))
        rules.append(Rule(tuple(entries), r.outcome))
    return DMNTable(tuple(inputs), rules, hit_policy, output_values=table.outcomes)


# -- DMN 1.4 XML export ------------------------------------------------------------------

DMN14_NS = "https://www.omg.org/spec/DMN/20211108/MODEL/"


def _feel_str(v) -> str:
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _feel_entry(inp: Input, e) -> str:
    if e is ANY:
        return "-"
    if isinstance(e, Point):
        return _num(e.value) if inp.numeric else _feel_str(e.value)
    if isinstance(e, OneOf):
        return ",".join(_feel_str(v) for v in sorted(e.values, key=str))
    if isinstance(e, Not):
        return f"not({_feel_entry(inp, e.entry)})"
    return e.feel()


def to_dmn_xml(table: DMNTable, name: str = "decision") -> str:
    """Serialise as DMN 1.4 XML (no diagram interchange)."""
    ET.register_namespace("", DMN14_NS)
    q = lambda tag: f"{{{DMN14_NS}}}{tag}"
    defs = ET.Element(q("definitions"), id=f"{name}_defs", name=name,
                      namespace="https://example.org/latc_check")
    dec = ET.SubElement(defs, q("decision"), id=f"{name}_decision", name=name)
    dt = ET.SubElement(dec, q("decisionTable"), id=f"{name}_table", hitPolicy=table.hit_policy)
    for k, inp in enumerate(table.inputs):
        el = ET.SubElement(dt, q("input"), id=f"input_{k}", label=inp.name)
        ie = ET.SubElement(el, q("inputExpression"), id=f"input_expr_{k}",
                           typeRef="number" if inp.numeric else "string")
        ET.SubElement(ie, q("text")).text = inp.name
        iv = ET.SubElement(el, q("inputValues"), id=f"input_values_{k}")
        ET.SubElement(iv, q("text")).text = (inp.domain.feel() if inp.numeric
                                             else ",".join(_feel_str(v) for v in inp.values))
    out = ET.SubElement(dt, q("output"), id="output_0", name=table.output_name, typeRef="string")
    if table.output_values:
        ov = ET.SubElement(out, q("outputValues"), id="output_values_0")
        ET.SubElement(ov, q("text")).text = ",".join(_feel_str(v) for v in table.output_values)
    for i, r in enumerate(table.rules):
        rule = ET.SubElement(dt, q("rule"), id=f"rule_{i}")
        for k, (inp, e) in enumerate(zip(table.inputs, r.entries)):
            ent = ET.SubElement(rule, q("inputEntry"), id=f"rule_{i}_in_{k}")
            ET.SubElement(ent, q("text")).text = _feel_entry(inp, e)
        oe = ET.SubElement(rule, q("outputEntry"), id=f"rule_{i}_out")
        ET.SubElement(oe, q("text")).text = _feel_str(r.output)
    ET.indent(defs)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(defs, encoding="unicode")


def describe_region(region: tuple, inputs: Sequence[Input]) -> str:
    parts = []
    for inp, seg in zip(inputs, region):
        if seg == inp.full():
            parts.append("-")
        elif inp.numeric:
            parts.append(seg.feel())
        else:
            parts.append(",".join(str(v) for v in inp.values if v in seg))
    return " | ".join(parts)
