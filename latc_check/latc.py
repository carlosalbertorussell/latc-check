"""Reconstruction of LATC (Raggio & Russell, IJSER 12(1), 2021).

The source's formulas survive only partly (equation objects were lost in the
.docx conversions), so each step below records the reading taken.

Steps common to both readings
-----------------------------
I-1  Card(Ai) is the number of *distinct values of Ai that appear in T0*
     (the source's V_{ai,j} = union over the n instances).  Declared domains
     are NOT consulted.  Consequence: a domain value no expert example uses is
     invisible to LATC.
I-2  Frequency table: freq(Ai = v) = number of rows of T0 with that value.
     Duplicate rows of T0 are counted (q(T) counts instances, not distinct
     tuples).  Values are listed in order of first appearance in T0, which
     reproduces the order printed in the source's frequency table.
I-3  Corollary 3 [11b] (no previously selected attributes):
         q(Cp) = prod_i Card(Ai) - q(T0)                  ("missing count")
I-4  Corollary 4 [12]:
         k(Ax = v) = prod_i Card(Ai) / Card(Ax) - freq(Ax = v)
     ("per-value deficit").  The source's worked example gives
     M 8, F 8, D 9, I 7, >=30 7, <30 9, >=65 5, 60-64 4, <60 7, which this
     formula reproduces.
I-5  No valid-state constraint exists in the source; LATC counts every
     combination of observed values as a required row.

Reading A - deficit block fill  (``deficit_fill``)
--------------------------------------------------
The literal reading of "columns filled in frequency-table order, each column
filled with value blocks in sequence": build q(Cp) rows; column j receives
k(v1) copies of v1, then k(v2) copies of v2, ... in frequency-table order,
independently of the other columns.  Each column then has exactly the deficit
marginals, but the *rows* are whatever the independent columns line up into.
A negative deficit (possible only when T0 has duplicate rows) is treated as 0
and the column is truncated or padded with None to q(Cp) rows; None marks a
cell the procedure could not fill.

Reading B - odometer assembly  (``odometer_assembly``)
------------------------------------------------------
The IJSER appendix ("Assembling the Table") builds the table from the
*summed* frequency table of T0 u Cp (each value of Ai occurring
prod Card / Card(Ai) times), with a "quantity of repetitions" per column, and
then replaces the placeholder outcome of every assembled row that matches a
T0 row with that row's result (footnote 7: keep the same order in all
generated tables so rows can be matched).  The worked example's Table 3 /
Table 9 shows exactly this: all 24 rows in odometer order, T0 results marked
with their instance numbers, the other 16 marked "?".  Read this way LATC is
explicit enumeration of the product of observed domains followed by
membership matching, and the deficits are only a cross-check.  The
repetition count for column j is r_j = prod_{k>j} Card(Ak) (truth-table
generation); the source's exact expression is lost.
"""

from __future__ import annotations

from collections import Counter
from itertools import permutations, product
from math import prod
from typing import Iterator, Sequence

from .model import Condition, DecisionTable


# -- I-1 .. I-4 -------------------------------------------------------------

def observed_domains(table: DecisionTable) -> list[tuple]:
    """Per attribute: distinct values seen in T0, in first-appearance order."""
    seen: list[dict] = [dict() for _ in table.attributes]
    for cond in table.conditions():
        for j, v in enumerate(cond):
            seen[j].setdefault(v, None)
    return [tuple(s) for s in seen]


def frequency_table(table: DecisionTable) -> list[dict]:
    counts = [Counter() for _ in table.attributes]
    for cond in table.conditions():
        for j, v in enumerate(cond):
            counts[j][v] += 1
    return [{v: counts[j][v] for v in dom} for j, dom in enumerate(observed_domains(table))]


def product_of_cards(table: DecisionTable) -> int:
    return prod(len(d) for d in observed_domains(table))


def missing_count(table: DecisionTable) -> int:
    """Corollary 3 [11b]: prod Card(Ai) - q(T0)."""
    return product_of_cards(table) - len(table.rows)


def deficits(table: DecisionTable) -> list[dict]:
    """Corollary 4 [12]: k(Ax=v) = prod Card / Card(Ax) - freq(Ax=v)."""
    total = product_of_cards(table)
    return [{v: total // len(f) - n for v, n in f.items()} for f in frequency_table(table)]


# -- Reading A ---------------------------------------------------------------

def deficit_fill(table: DecisionTable,
                 value_orders: Sequence[Sequence] | None = None) -> list[Condition]:
    """Fill q(Cp) rows column by column with deficit-sized value blocks.

    ``value_orders`` overrides the block order per column (default:
    frequency-table order); used by ``best_block_order`` to give Reading A
    every possible chance.
    """
    m = missing_count(table)
    if m <= 0:
        return []
    columns = []
    for j, k in enumerate(deficits(table)):
        order = value_orders[j] if value_orders is not None else list(k)
        col = [v for v in order for _ in range(max(k[v], 0))]
        col = (col + [None] * m)[:m]
        columns.append(col)
    return list(zip(*columns))


def block_orders(table: DecisionTable) -> Iterator[list[tuple]]:
    """Every combination of per-column block orders (prod of Card(Ai)!)."""
    return (list(p) for p in product(*(permutations(d) for d in observed_domains(table))))


def n_block_orders(table: DecisionTable) -> int:
    from math import factorial
    return prod(factorial(len(d)) for d in observed_domains(table))


# -- Reading B ---------------------------------------------------------------

def odometer_assembly(table: DecisionTable) -> tuple[list[Condition], list[Condition]]:
    """Return (assembled table of prod Card rows, rows not matched in T0)."""
    doms = observed_domains(table)
    total = prod(len(d) for d in doms)
    columns = []
    for j, dom in enumerate(doms):
        reps = prod(len(d) for d in doms[j + 1:])     # quantity of repetitions
        columns.append([dom[(i // reps) % len(dom)] for i in range(total)])
    assembled = list(zip(*columns))
    present = set(table.conditions())
    return assembled, [c for c in assembled if c not in present]


def latc_odometer(table: DecisionTable) -> list[Condition]:
    return odometer_assembly(table)[1]


# -- counts kept as a check ----------------------------------------------------

def marginals(rows: Sequence[Condition], n_attrs: int) -> list[Counter]:
    out = [Counter() for _ in range(n_attrs)]
    for r in rows:
        for j, v in enumerate(r):
            out[j][v] += 1
    return out


def valid_space_deficits(table: DecisionTable) -> list[dict]:
    """Generalised [12]: marginals of the declared valid space minus T0 freq.

    Equals ``deficits`` when every declared value appears in T0, there is no
    constraint and T0 has no duplicates; unlike [12] it stays correct when a
    constraint removes states or a declared value is unobserved.
    """
    space = marginals(list(table.valid_space()), len(table.attributes))
    t0 = marginals(table.conditions(), len(table.attributes))
    return [{v: space[j][v] - t0[j][v] for v in a.domain}
            for j, a in enumerate(table.attributes)]


def deficit_check(candidate: Sequence[Condition], table: DecisionTable,
                  expected: list[dict] | None = None) -> list[str]:
    """Compare the candidate's marginals with the expected deficits.

    Returns human-readable mismatches (empty list = counts agree).  Passing
    this check is necessary but NOT sufficient for a correct completion.
    """
    expected = expected if expected is not None else deficits(table)
    got = marginals(candidate, len(table.attributes))
    problems = []
    if sum(expected[0].values()) != len(candidate):
        problems.append(f"row count {len(candidate)} != expected {sum(expected[0].values())}")
    for j, (exp, g) in enumerate(zip(expected, got)):
        for v in set(exp) | set(g):
            if exp.get(v, 0) != g.get(v, 0):
                problems.append(f"{table.attributes[j].name}={v!r}: got {g.get(v, 0)}, expected {exp.get(v, 0)}")
    return problems
