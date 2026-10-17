"""Structural checks on a (completed) decision table, and a rule evaluator.

* coverage    - share of the valid space matched by at least one row (want 1)
* single-hit  - every valid tuple is matched by at most one row
* conflicts   - tuples whose rows carry different assigned outcomes
* referral    - inputs outside the declared domains go to the Out-of-Range
                referral row; they are never mapped to an in-domain row
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import prod
from typing import Callable, Mapping

from .keying import DigestIndex, PrimeKeyer
from .latc import frequency_table, observed_domains
from .model import OUT_OF_RANGE, UNKNOWN, Condition, DecisionTable


def structural_report(table: DecisionTable) -> dict:
    by_cond: dict[Condition, list[str]] = defaultdict(list)
    for r in table.rows:
        by_cond[r.condition].append(r.outcome)
    space = list(table.valid_space())
    covered = sum(1 for c in space if c in by_cond)
    multi_hit = sum(1 for c, outs in by_cond.items() if len(outs) > 1)
    conflicts = sum(1 for outs in by_cond.values()
                    if len({o for o in outs if o != UNKNOWN}) > 1)
    return {
        "rows": len(table.rows),
        "valid_space": len(space),
        "coverage": covered / len(space) if space else 1.0,
        "uncovered": len(space) - covered,
        "multi_hit_tuples": multi_hit,
        "single_hit": multi_hit == 0,
        "conflicting_tuples": conflicts,
        "rows_outside_valid_space": sum(1 for r in table.rows if not table.is_valid(r.condition)),
        "unknown_outcomes": sum(1 for r in table.rows if r.outcome == UNKNOWN),
        "undeclared_outcomes": sum(1 for r in table.rows
                                   if r.outcome not in table.outcomes and r.outcome != UNKNOWN),
    }


def is_sound(report: dict) -> bool:
    """Complete, single-hit, conflict-free, nothing outside the space."""
    return (report["coverage"] == 1.0 and report["single_hit"]
            and report["conflicting_tuples"] == 0 and report["rows_outside_valid_space"] == 0)


def summed_frequency_check(table: DecisionTable) -> bool:
    """The source's completeness check (Table 7, "sum of frequencies").

    True when every observed value of Ai occurs prod Card / Card(Ai) times.
    Necessary for completeness of a duplicate-free table, NOT sufficient:
    a table with repeated rows can pass it while missing tuples.
    """
    total = prod(len(d) for d in observed_domains(table))
    return len(table.rows) == total and all(
        n == total // len(f) for f in frequency_table(table) for n in f.values())


# -- evaluator -------------------------------------------------------------------

@dataclass(frozen=True)
class Decision:
    outcome: str
    row: int | None   # index into table.rows, None for referral
    reason: str = ""


class Evaluator:
    """Execute a completed table.  ``backend``: 'dict', 'sha512' or 'prime'."""

    def __init__(self, table: DecisionTable, backend: str = "sha512",
                 binners: Mapping[str, Callable] | None = None,
                 digest_index: DigestIndex | None = None,
                 prime_keyer: PrimeKeyer | None = None):
        rep = structural_report(table)
        if not rep["single_hit"]:
            raise ValueError("table is not single-hit; refusing to execute it")
        self.table, self.backend, self.binners = table, backend, dict(binners or {})
        names = table.names
        if backend == "dict":
            self._index = {r.condition: i for i, r in enumerate(table.rows)}
            self._lookup = self._index.get
        elif backend == "sha512":
            idx = digest_index or DigestIndex(names)
            for i, r in enumerate(table.rows):
                idx.add(r.condition, i)
            self._lookup = idx.lookup
        elif backend == "prime":
            pk = prime_keyer or PrimeKeyer.distinct(table.attributes)
            self._index = {}
            for i, r in enumerate(table.rows):
                k = pk.key(r.condition)
                if k in self._index:
                    raise ValueError(f"prime key collision for {r.condition!r}")
                self._index[k] = i
            self._lookup = lambda c: self._index.get(pk.key(c))
        else:
            raise ValueError(backend)

    def normalise(self, inputs: Mapping) -> tuple[Condition | None, list[str]]:
        problems, cond = [], []
        extra = set(inputs) - set(self.table.names)
        problems += [f"unexpected attribute {n!r}" for n in sorted(extra)]
        for a in self.table.attributes:
            if a.name not in inputs:
                problems.append(f"{a.name} missing")
                cond.append(None)
                continue
            raw = inputs[a.name]
            v = self.binners[a.name](raw) if a.name in self.binners else raw
            if v is None or v not in a.domain:
                problems.append(f"{a.name}={raw!r} out of range")
            cond.append(v)
        return (None if problems else tuple(cond)), problems

    def evaluate(self, inputs: Mapping) -> Decision:
        cond, problems = self.normalise(inputs)
        if problems:
            return Decision(OUT_OF_RANGE, None, "; ".join(problems))
        if not self.table.is_valid(cond):
            return Decision(OUT_OF_RANGE, None, "invalid state (constraint)")
        i = self._lookup(cond)
        if i is None:
            return Decision(OUT_OF_RANGE, None, "not covered by any row")
        return Decision(self.table.rows[i].outcome, i)
