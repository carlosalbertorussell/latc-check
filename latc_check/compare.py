"""Compare a candidate completion with the exact complement."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

from . import latc
from .model import Condition, DecisionTable
from .reference import exact_complement


@dataclass(frozen=True)
class CompletionResult:
    n_candidate: int     # rows produced
    n_expected: int      # rows in the exact complement
    missed: int          # complement rows the candidate does not contain
    duplicates: int      # candidate rows that repeat an earlier candidate row
    regenerated_t0: int  # candidate rows that are already in T0
    outside_space: int   # candidate rows that are not valid condition tuples
    exact: bool          # candidate == complement, as a set and with no repeats

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def compare(candidate: Sequence[Condition], table: DecisionTable) -> CompletionResult:
    expected = set(exact_complement(table))
    t0 = set(table.conditions())
    counts = Counter(candidate)
    cand = set(counts)
    return CompletionResult(
        n_candidate=len(candidate),
        n_expected=len(expected),
        missed=len(expected - cand),
        duplicates=sum(n - 1 for n in counts.values()),
        regenerated_t0=sum(n for c, n in counts.items() if c in t0),
        outside_space=sum(n for c, n in counts.items() if not table.is_valid(c)),
        exact=(cand == expected and len(candidate) == len(expected)),
    )


def best_block_order(table: DecisionTable, limit: int = 5000):
    """Reading A with the *best* per-column block order (an oracle bound).

    Returns (best CompletionResult, number of orders tried, any order exact).
    Orders are tried exhaustively up to ``limit``; ``None`` if over the limit.
    """
    if latc.n_block_orders(table) > limit:
        return None
    best, tried, any_exact = None, 0, False
    for order in latc.block_orders(table):
        r = compare(latc.deficit_fill(table, order), table)
        tried += 1
        any_exact |= r.exact
        if best is None or (r.missed + r.duplicates) < (best.missed + best.duplicates):
            best = r
    return best, tried, any_exact


def count_marginal_solutions(cells: Sequence[Condition], targets: list[dict]) -> int:
    """Number of distinct subsets of ``cells`` whose per-value counts equal ``targets``.

    Dynamic programming over cells; the state is the remaining count for every
    (attribute, value).  Used to show how many different row sets satisfy the
    same deficit table.
    """
    keys = [(j, v) for j, t in enumerate(targets) for v in t]
    index = {k: i for i, k in enumerate(keys)}
    start = tuple(targets[j][v] for j, v in keys)
    if any(x < 0 for x in start):
        return 0
    cell_idx = [tuple(index.get((j, v), -1) for j, v in enumerate(c)) for c in cells]
    if any(-1 in ci for ci in cell_idx):
        cell_idx = [ci for ci in cell_idx if -1 not in ci]

    @lru_cache(maxsize=None)
    def go(i: int, rem: tuple) -> int:
        if i == len(cell_idx):
            return int(not any(rem))
        total = go(i + 1, rem)                     # skip cell i
        if all(rem[p] > 0 for p in cell_idx[i]):    # take cell i
            r = list(rem)
            for p in cell_idx[i]:
                r[p] -= 1
            total += go(i + 1, tuple(r))
        return total

    return go(0, start)
