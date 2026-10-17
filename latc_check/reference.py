"""Reference completion: the exact set-theoretic complement.

    missing(T0) = valid_space  \\  { condition of r : r in T0 }

computed by brute-force enumeration of the declared domains, filtered by the
valid-state constraint.  This is the ground truth every LATC variant is
compared against.  It is exponential in the number of attributes by nature,
but it is exact, and for the table sizes business rules actually reach it is
cheap (see ``bench``).
"""

from __future__ import annotations

from .model import Condition, DecisionTable, Row, UNKNOWN


def exact_complement(table: DecisionTable) -> list[Condition]:
    """Valid condition tuples not covered by any row of ``table``.

    Returned in enumeration order (lexicographic in declared domain order),
    without duplicates.  Rows of T0 that are out of domain or violate the
    constraint are ignored here; ``checks`` reports them separately.
    """
    present = set(table.conditions())
    return [c for c in table.valid_space() if c not in present]


def complete(table: DecisionTable) -> DecisionTable:
    """T0 plus one UNKNOWN-outcome row per missing condition tuple."""
    return table.with_rows(list(table.rows) + [Row(c, UNKNOWN) for c in exact_complement(table)])
