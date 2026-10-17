"""Mixed-radix rank index: a complete table as a flat array of outcome codes.

For declared domains D_1..D_n (in declared order), the rank of a tuple is

    rank(x) = sum_i idx_i(x_i) * prod_{j>i} |D_j|

i.e. the tuple's position in lexicographic enumeration of the product.  It is
a bijection between the full condition space and range(prod |D_j|), so it is a
collision-free *minimal* perfect hash: no key bytes are stored, nothing is
hashed and nothing is verified on lookup, and a complete table is one byte per
row.  The price is that the table must be dense over the declared product;
an out-of-domain value has no index and is a referral by construction.

Codes: 0 = UNKNOWN (not yet assigned), 1..len(outcomes) = outcomes in order,
255 = INVALID (excluded by the valid-state constraint).
"""

from __future__ import annotations

import json
from math import prod
from typing import Sequence

from .model import UNKNOWN, Attribute, Condition, DecisionTable

INVALID_CODE = 255


class RankIndex:
    def __init__(self, attributes: Sequence[Attribute], outcomes: Sequence[str] = ()):
        self.attributes = tuple(attributes)
        self.index = [{v: i for i, v in enumerate(a.domain)} for a in self.attributes]
        self.cards = [a.card for a in self.attributes]
        self.weights = [prod(self.cards[i + 1:]) for i in range(len(self.cards))]
        self.size = prod(self.cards)
        self.outcomes = tuple(outcomes)
        if len(self.outcomes) > 254:
            raise ValueError("at most 254 outcomes fit in one byte")
        self.codes = bytearray(self.size)  # all UNKNOWN

    # -- addressing ----------------------------------------------------------
    def rank(self, cond: Condition) -> int | None:
        if len(cond) != len(self.index):
            return None
        r = 0
        for idx, w, v in zip(self.index, self.weights, cond):
            i = idx.get(v)
            if i is None:
                return None
            r += i * w
        return r

    def unrank(self, r: int) -> Condition:
        out = []
        for a, w in zip(self.attributes, self.weights):
            i, r = divmod(r, w)
            out.append(a.domain[i])
        return tuple(out)

    # -- contents ------------------------------------------------------------
    def code_of(self, outcome: str) -> int:
        return 0 if outcome == UNKNOWN else self.outcomes.index(outcome) + 1

    def outcome_of(self, code: int) -> str:
        if code == 0:
            return UNKNOWN
        if code == INVALID_CODE:
            return "INVALID"
        return self.outcomes[code - 1]

    def set(self, cond: Condition, outcome: str) -> None:
        r = self.rank(cond)
        if r is None:
            raise KeyError(f"{cond!r} is outside the declared domains")
        self.codes[r] = self.code_of(outcome)

    def lookup(self, cond: Condition) -> str | None:
        r = self.rank(cond)
        return None if r is None else self.outcome_of(self.codes[r])

    @classmethod
    def from_table(cls, table: DecisionTable) -> "RankIndex":
        """Index a single-hit table; constraint-excluded states get INVALID."""
        ri = cls(table.attributes, table.outcomes)
        if table.constraint is not None:
            for r, cond in enumerate(table.full_space()):
                if not table.constraint(cond):
                    ri.codes[r] = INVALID_CODE
        seen = set()
        for row in table.rows:
            r = ri.rank(row.condition)
            if r is None or r in seen:
                raise ValueError(f"row {row.condition!r} is out of domain or repeated")
            seen.add(r)
            ri.codes[r] = ri.code_of(row.outcome)
        return ri

    # -- storage -------------------------------------------------------------
    def save(self, path: str) -> None:
        """Codes as raw bytes in ``path``; domains and outcomes in ``path``.json."""
        with open(path, "wb") as f:
            f.write(self.codes)
        with open(path + ".json", "w", encoding="utf-8") as f:
            json.dump({"attributes": [[a.name, list(a.domain)] for a in self.attributes],
                       "outcomes": list(self.outcomes)}, f)

    @classmethod
    def load(cls, path: str) -> "RankIndex":
        with open(path + ".json", encoding="utf-8") as f:
            meta = json.load(f)
        ri = cls([Attribute(n, tuple(d)) for n, d in meta["attributes"]], meta["outcomes"])
        with open(path, "rb") as f:
            ri.codes = bytearray(f.read())
        if len(ri.codes) != ri.size:
            raise ValueError("code file does not match the declared domains")
        return ri
