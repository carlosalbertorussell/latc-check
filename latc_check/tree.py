"""A small ID3 decision-tree learner and its conversion to DMN rules.

Used for the review-load comparison in the spirit of Calvanese et al., who
analyse DMN tables derived from decision trees: a complete exact table (one
row per state) is compressed into rules that read only the attributes on a
root-to-leaf path.

ID3 (Quinlan 1986) with multiway splits on categorical attributes and
information gain; ties are broken by attribute order, so the tree is
deterministic.  A node is a leaf when its rows share one class, when no
attribute is left, or when it has no rows (then it takes the parent's majority
class, the usual convention; on a full product table this never happens).
On a consistent table (one class per tuple) the tree classifies every training
row correctly, so its rules reproduce the table exactly.

``to_dmn`` writes one rule per leaf: ``Point`` entries on the path, ``ANY``
elsewhere.  With ``merge_siblings=True`` the leaf children of one node that
share a class become a single rule with a ``OneOf`` entry, which is still
disjoint from every other rule.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .dmn import ANY, DMNTable, Input, OneOf, Point, Rule
from .model import DecisionTable


@dataclass
class Node:
    label: str | None = None             # class at a leaf
    attribute: int | None = None         # split attribute at an inner node
    children: dict = field(default_factory=dict)  # value -> Node, in declared order
    n: int = 0

    @property
    def leaf(self) -> bool:
        return self.attribute is None


def _entropy(counts: Counter) -> float:
    total = sum(counts.values())
    return -sum(c / total * math.log2(c / total) for c in counts.values() if c)


def _majority(rows, outcomes) -> str:
    c = Counter(r.outcome for r in rows)
    order = {o: k for k, o in enumerate(outcomes)}
    return max(c, key=lambda o: (c[o], -order.get(o, len(order))))


def id3(table: DecisionTable) -> Node:
    attrs = table.attributes

    def grow(rows, free: tuple, default: str) -> Node:
        if not rows:
            return Node(label=default, n=0)
        classes = Counter(r.outcome for r in rows)
        if len(classes) == 1 or not free:
            return Node(label=_majority(rows, table.outcomes), n=len(rows))
        base = _entropy(classes)
        best, best_gain = None, -1.0
        for j in free:
            parts: dict = {}
            for r in rows:
                parts.setdefault(r.condition[j], Counter())[r.outcome] += 1
            rem = sum(sum(c.values()) / len(rows) * _entropy(c) for c in parts.values())
            gain = base - rem
            if gain > best_gain + 1e-12:
                best, best_gain = j, gain
        maj = _majority(rows, table.outcomes)
        node = Node(attribute=best, n=len(rows))
        rest = tuple(j for j in free if j != best)
        for v in attrs[best].domain:
            node.children[v] = grow([r for r in rows if r.condition[best] == v], rest, maj)
        return node

    return grow(list(table.rows), tuple(range(len(attrs))), _majority(table.rows, table.outcomes))


def stats(node: Node) -> dict:
    leaves, depth, inner = 0, 0, 0

    def walk(n: Node, d: int) -> None:
        nonlocal leaves, depth, inner
        if n.leaf:
            leaves += 1
            depth = max(depth, d)
            return
        inner += 1
        for c in n.children.values():
            walk(c, d + 1)

    walk(node, 0)
    return {"leaves": leaves, "inner_nodes": inner, "max_depth": depth}


def classify(node: Node, cond: tuple) -> str:
    while not node.leaf:
        node = node.children[cond[node.attribute]]
    return node.label


def to_dmn(node: Node, table: DecisionTable, merge_siblings: bool = False,
           hit_policy: str = "UNIQUE") -> DMNTable:
    """One rule per root-to-leaf path (or per same-class leaf group)."""
    n = len(table.attributes)
    rules = []

    def walk(nd: Node, path: dict) -> None:
        if nd.leaf:
            rules.append(_rule(path, nd.label))
            return
        j = nd.attribute
        if merge_siblings:
            groups: dict = {}
            for v, ch in nd.children.items():
                if ch.leaf:
                    groups.setdefault(ch.label, []).append(v)
            for label, vals in groups.items():
                if len(vals) == len(nd.children) and not path:
                    rules.append(_rule(path, label))     # single-class root
                else:
                    e = Point(vals[0]) if len(vals) == 1 else OneOf(frozenset(vals))
                    rules.append(_rule({**path, j: e}, label))
            for v, ch in nd.children.items():
                if not ch.leaf:
                    walk(ch, {**path, j: Point(v)})
        else:
            for v, ch in nd.children.items():
                walk(ch, {**path, j: Point(v)})

    def _rule(path: dict, label: str) -> Rule:
        return Rule(tuple(path.get(k, ANY) for k in range(n)), label)

    walk(node, {})
    inputs = tuple(Input(a.name, values=a.domain) for a in table.attributes)
    return DMNTable(inputs, rules, hit_policy, output_values=table.outcomes)
