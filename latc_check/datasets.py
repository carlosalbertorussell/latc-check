"""Loaders for the public UCI decision tables (Car Evaluation, Nursery).

Both datasets were generated from DEX hierarchical decision models
(Bohanec & Rajkovic 1988, 1990), so each is meant to be a *complete* decision
table: one row per combination of the declared attribute values, one class per
row.  The loaders read the files as data (no code is executed), declare every
domain in the value order given in the dataset's ``.names`` documentation, and
``verify`` checks the three properties the experiments rely on:

* rows = product of the domain sizes;
* no condition tuple occurs twice;
* one class per tuple (no conflicts), and every row in the declared domains.

Value spelling.  The prose ``.names`` files spell four values differently from
the data (car: ``v-high``, ``5-more``, class ``v-good``; nursery:
``non-prob``), while the machine-readable ``.c45-names`` files use the
spelling of the ``.data`` files (``vhigh``, ``5more``, ``vgood``,
``nonprob``).  Domains are therefore read from ``.c45-names`` and their value
order is checked against ``.names`` with hyphens removed; ``verify`` reports
the result (``names_order_matches``).
"""

from __future__ import annotations

import os
import re
from collections import Counter
from math import prod

from .model import Attribute, DecisionTable, Row

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

DATASETS = {
    "car": {"dir": "uci_car", "stem": "car", "title": "UCI Car Evaluation",
            "url": "https://archive.ics.uci.edu/dataset/19/car+evaluation"},
    "nursery": {"dir": "uci_nursery", "stem": "nursery", "title": "UCI Nursery",
                "url": "https://archive.ics.uci.edu/dataset/76/nursery"},
}

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_VALUE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def _paths(name: str, data_dir: str | None) -> tuple[str, str, str]:
    spec = DATASETS[name]
    base = os.path.join(data_dir or DATA_DIR, spec["dir"], spec["stem"])
    return base + ".data", base + ".c45-names", base + ".names"


def parse_c45_names(text: str) -> tuple[tuple[str, ...], list[tuple[str, tuple[str, ...]]]]:
    """(class values, [(attribute, values)]) from a C4.5 names file.

    ``|`` starts a comment; the first non-comment statement lists the classes,
    the others are ``name: v1, v2, ... .``.
    """
    lines = [ln.split("|", 1)[0].strip() for ln in text.splitlines()]
    stmts = [ln.rstrip(".").strip() for ln in lines if ln]   # one statement per line here
    if not stmts:
        raise ValueError("empty names file")
    classes = tuple(v.strip() for v in stmts[0].split(","))
    attributes = []
    for s in stmts[1:]:
        if ":" not in s:
            raise ValueError(f"unexpected statement {s!r}")
        n, vals = s.split(":", 1)
        n = n.strip()
        values = tuple(v.strip() for v in vals.split(","))
        if not _NAME.match(n) or not all(_VALUE.match(v) for v in values + classes):
            raise ValueError(f"unexpected token in {s!r}")
        attributes.append((n, values))
    return classes, attributes


def parse_names_values(text: str) -> dict[str, tuple[str, ...]]:
    """Attribute values listed under '7. Attribute Values' in a prose .names file."""
    out, inside = {}, False
    for ln in text.splitlines():
        if re.match(r"^\s*7\.\s*Attribute Values", ln):
            inside = True
            continue
        if inside and re.match(r"^\s*8\.", ln):
            break
        m = re.match(r"^\s+([A-Za-z_]+)\s{2,}(.+)$", ln) if inside else None
        if m:
            out[m.group(1)] = tuple(v.strip() for v in m.group(2).split(","))
    return out


def load(name: str, data_dir: str | None = None) -> tuple[DecisionTable, dict]:
    """Return (DecisionTable of every row with its class, file info)."""
    data_p, c45_p, names_p = _paths(name, data_dir)
    with open(c45_p, encoding="ascii") as f:
        classes, spec = parse_c45_names(f.read())
    with open(names_p, encoding="latin-1") as f:
        prose = parse_names_values(f.read())
    attributes = tuple(Attribute(n, vals) for n, vals in spec)
    rows, blank, bad = [], 0, []
    with open(data_p, encoding="ascii", newline="") as f:
        for k, ln in enumerate(f, 1):
            ln = ln.strip()
            if not ln:
                blank += 1
                continue
            parts = ln.split(",")
            if len(parts) != len(attributes) + 1:
                bad.append(k)
                continue
            rows.append(Row(tuple(parts[:-1]), parts[-1]))
    order_ok = all(tuple(v.replace("-", "") for v in prose.get(n, ())) == vals for n, vals in spec)
    info = {"dataset": name, "title": DATASETS[name]["title"], "url": DATASETS[name]["url"],
            "data_file": os.path.basename(data_p), "blank_lines": blank, "malformed_lines": bad,
            "names_order_matches": order_ok,
            "names_spelling_differs": sorted(f"{n}: {p!r} vs {v!r}" for n, vals in spec
                                             for p, v in zip(prose.get(n, ()), vals) if p != v)}
    return DecisionTable(attributes, rows, outcomes=classes), info


def verify(table: DecisionTable) -> dict:
    """Is the table a complete, conflict-free function of its declared product?"""
    conds = Counter(r.condition for r in table.rows)
    classes: dict = {}
    for r in table.rows:
        classes.setdefault(r.condition, set()).add(r.outcome)
    states = prod(a.card for a in table.attributes)
    out_of_domain = sum(1 for r in table.rows if not table.in_domain(r.condition))
    undeclared = sorted({r.outcome for r in table.rows} - set(table.outcomes))
    rep = {
        "attributes": len(table.attributes),
        "domain_sizes": [a.card for a in table.attributes],
        "states": states,
        "rows": len(table.rows),
        "rows_equal_product": len(table.rows) == states,
        "duplicate_condition_tuples": sum(n - 1 for n in conds.values() if n > 1),
        "tuples_with_more_than_one_class": sum(1 for s in classes.values() if len(s) > 1),
        "rows_out_of_domain": out_of_domain,
        "undeclared_classes": undeclared,
        "class_counts": dict(Counter(r.outcome for r in table.rows)),
    }
    rep["full_product"] = (rep["rows_equal_product"] and rep["duplicate_condition_tuples"] == 0
                           and out_of_domain == 0 and len(conds) == states)
    rep["one_class_per_tuple"] = rep["tuples_with_more_than_one_class"] == 0
    return rep


def car(data_dir: str | None = None) -> DecisionTable:
    return load("car", data_dir)[0]


def nursery(data_dir: str | None = None) -> DecisionTable:
    return load("nursery", data_dir)[0]
