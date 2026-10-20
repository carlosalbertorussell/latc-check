"""Oracle for CTRL-NUR: the UCI Nursery table read as data.

The "encoding" is the DEX model behind ``data/raw/uci_nursery/nursery.data``; the
data file lists its class for every one of the 12,960 combinations, so the oracle
is a lookup.  Standard library only.

    python oracle.py --enumerate        writes ground_truth.csv next to this file
    python oracle.py --check-official   checks the official cases (there are none)
                                        and every data row against the oracle
"""

from __future__ import annotations

import csv
import json
import os
import sys
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DATA = os.path.join(REPO, "data", "raw", "uci_nursery", "nursery.data")

with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as _f:
    SPEC = json.load(_f)
NAMES = [a["name"] for a in SPEC["attributes"]]


def _load() -> dict[tuple, str]:
    table: dict[tuple, str] = {}
    with open(DATA, encoding="ascii") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            *cond, cls = line.split(",")
            if tuple(cond) in table:
                raise ValueError(f"duplicate row {cond}")
            table[tuple(cond)] = cls
    return table


_TABLE = _load()


def evaluate(row: dict[str, str]) -> str:
    return _TABLE[tuple(row[n] for n in NAMES)]


def enumerate_space() -> None:
    domains = [a["values"] for a in SPEC["attributes"]]
    with open(os.path.join(HERE, "ground_truth.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(NAMES + ["output"])
        for cond in product(*domains):
            w.writerow(list(cond) + [evaluate(dict(zip(NAMES, cond)))])


def check_official() -> int:
    with open(os.path.join(HERE, "official_examples.csv"), encoding="utf-8", newline="") as f:
        official = list(csv.DictReader(f))
    ok = sum(evaluate(r) == r["output"] for r in official)
    print(f"official cases: {ok}/{len(official)} passed (Nursery has no official test cases)")
    data_ok = sum(evaluate(dict(zip(NAMES, c))) == y for c, y in _TABLE.items())
    print(f"data rows through the oracle: {data_ok}/{len(_TABLE)} passed")
    return 0 if ok == len(official) and data_ok == len(_TABLE) else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--enumerate"]:
        enumerate_space()
    elif sys.argv[1:] == ["--check-official"]:
        sys.exit(check_official())
    else:
        sys.exit(__doc__)
