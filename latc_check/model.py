"""Finite-domain decision-table model.

A decision table has:

* an ordered list of attributes, each with a declared finite domain;
* an optional valid-state constraint (a predicate over a full condition
  tuple) that removes impossible combinations from the condition space;
* a list of rows ``(condition tuple, outcome)``.  The list form (rather than
  a dict) is deliberate: it lets the structural checks *see* duplicate rows
  and conflicting outcomes instead of having them silently merged;
* an outcome set.  Outcomes include the non-decision category ``Rv`` used in
  the LATC paper, and ``UNKNOWN`` marks a row whose outcome the experts have
  not yet assigned (the paper's "¿?").

A referral row ``OUT_OF_RANGE`` is not part of the condition space: it is what
the evaluator returns for inputs that fall outside the declared domains (see
``checks.Evaluator``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable, Hashable, Iterable, Iterator, Sequence

Value = Hashable
Condition = tuple  # one value per attribute, in attribute order

UNKNOWN = "?"            # outcome not yet assigned by the experts ("¿?")
RV = "Rv"                # non-decision category from the source paper
OUT_OF_RANGE = "Out of Range"  # referral row for out-of-domain inputs


@dataclass(frozen=True)
class Attribute:
    name: str
    domain: tuple  # declared finite domain, in declaration order

    def __post_init__(self) -> None:
        if len(set(self.domain)) != len(self.domain):
            raise ValueError(f"attribute {self.name!r} has repeated domain values")
        if not self.domain:
            raise ValueError(f"attribute {self.name!r} has an empty domain")

    @property
    def card(self) -> int:
        return len(self.domain)


@dataclass(frozen=True)
class Row:
    condition: Condition
    outcome: str = UNKNOWN


@dataclass
class DecisionTable:
    attributes: tuple[Attribute, ...]
    rows: list[Row] = field(default_factory=list)
    outcomes: tuple[str, ...] = ("YES", "NO", RV)
    constraint: Callable[[Condition], bool] | None = None

    # -- condition space -------------------------------------------------
    @property
    def names(self) -> tuple[str, ...]:
        return tuple(a.name for a in self.attributes)

    def in_domain(self, cond: Condition) -> bool:
        return len(cond) == len(self.attributes) and all(
            v in a.domain for a, v in zip(self.attributes, cond)
        )

    def is_valid(self, cond: Condition) -> bool:
        """In the declared domains and allowed by the valid-state constraint."""
        if not self.in_domain(cond):
            return False
        return self.constraint is None or bool(self.constraint(cond))

    def full_space(self) -> Iterator[Condition]:
        """Cartesian product of the declared domains (no constraint)."""
        return product(*(a.domain for a in self.attributes))

    def valid_space(self) -> Iterator[Condition]:
        for cond in self.full_space():
            if self.constraint is None or self.constraint(cond):
                yield cond

    def valid_space_size(self) -> int:
        return sum(1 for _ in self.valid_space())

    # -- rows ------------------------------------------------------------
    def conditions(self) -> list[Condition]:
        return [r.condition for r in self.rows]

    def with_rows(self, rows: Iterable[Row]) -> "DecisionTable":
        return DecisionTable(self.attributes, list(rows), self.outcomes, self.constraint)

    def as_dicts(self) -> list[dict]:
        return [dict(zip(self.names, r.condition), outcome=r.outcome) for r in self.rows]


def attrs(spec: Sequence[tuple[str, Sequence[Value]]]) -> tuple[Attribute, ...]:
    """Shorthand: ``attrs([("Sex", "MF"), ...])``."""
    return tuple(Attribute(name, tuple(dom)) for name, dom in spec)
