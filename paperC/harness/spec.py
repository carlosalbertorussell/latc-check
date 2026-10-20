"""Read and verify a sample folder in the format of paperC/specs/FORMAT.md.

Implements PROTOCOL.md section 2 (D, E, R, V, S) and the aborting controls of
section 7 (CTRL-HASH, CTRL-GT).  CTRL-EXCL is computed here and reported by
the runner.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
from dataclasses import dataclass
from itertools import product
from math import prod

EXCLUDED = "EXCLUDED"
REJECTED = "REJECTED"


class SpecError(Exception):
    """A sample folder fails CTRL-HASH or CTRL-GT; the run is aborted."""


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def folder_files(folder: str) -> list[str]:
    """Relative paths ('/'-separated) of every file under ``folder`` that
    SHA256SUMS must list: everything except SHA256SUMS, __pycache__ and *.pyc."""
    out = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in files:
            if name.endswith(".pyc"):
                continue
            rel = os.path.relpath(os.path.join(root, name), folder).replace(os.sep, "/")
            if rel != "SHA256SUMS":
                out.append(rel)
    return sorted(out)


def verify_sha256sums(folder: str) -> list[str]:
    """CTRL-HASH.  Returns problems (empty list = pass).

    SHA256SUMS lines are in ``sha256sum`` output form: 64 hex digits, a space,
    a space or '*', then the relative path.
    """
    path = os.path.join(folder, "SHA256SUMS")
    if not os.path.exists(path):
        return ["SHA256SUMS missing"]
    listed: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln.strip():
                continue
            digest, rest = ln[:64].lower(), ln[64:]
            if len(rest) < 3 or rest[0] != " " or rest[1] not in " *":
                return [f"malformed SHA256SUMS line: {ln!r}"]
            listed[rest[2:].removeprefix("./")] = digest
    problems = []
    present = folder_files(folder)
    for rel in present:
        if rel not in listed:
            problems.append(f"{rel}: not listed in SHA256SUMS")
        elif sha256_file(os.path.join(folder, rel)) != listed[rel]:
            problems.append(f"{rel}: sha256 mismatch")
    for rel in sorted(set(listed) - set(present)):
        problems.append(f"{rel}: listed in SHA256SUMS but absent")
    return problems


# Exclusion predicates are Python expressions (FORMAT.md).  Before they are
# evaluated, every node is checked against this whitelist, so a predicate can only
# compare attribute names with string constants and combine the results.
_ALLOWED_NODES = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
                  ast.Compare, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Lt, ast.LtE,
                  ast.Gt, ast.GtE, ast.Name, ast.Load, ast.Constant, ast.Tuple,
                  ast.List, ast.Set)


def compile_predicate(expr: str, names: tuple[str, ...]):
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise SpecError(f"predicate {expr!r}: {type(node).__name__} is not allowed")
        if isinstance(node, ast.Name) and node.id not in names:
            raise SpecError(f"predicate {expr!r}: unknown attribute {node.id!r}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, str):
            raise SpecError(f"predicate {expr!r}: constants must be label strings")
    return compile(tree, "<predicate>", "eval")


def _read_csv(path: str) -> list[list[str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return [r for r in csv.reader(f)]


@dataclass
class Sample:
    """One sample folder, loaded and checked.  Condition tuples hold labels."""

    folder: str
    spec: dict
    names: tuple[str, ...]
    domains: tuple[tuple[str, ...], ...]
    outputs: tuple[str, ...]
    exclusions: tuple[dict, ...]
    gt: dict[tuple, str]                  # D -> output cell
    gt_order: list[tuple]                 # D in ground_truth.csv order (odometer)
    official: list[tuple[tuple, str]]     # (condition, output) in file order

    @property
    def sample_id(self) -> str:
        return self.spec["id"]

    @property
    def declared_size(self) -> int:
        return prod(len(d) for d in self.domains)

    def excluded_by_spec(self, cond: tuple) -> bool:
        row = dict(zip(self.names, cond))
        return any(bool(eval(code, {"__builtins__": {}}, row)) for code in self._predicates)

    def build_sets(self) -> None:
        self._predicates = [compile_predicate(e["predicate"], self.names) for e in self.exclusions]
        self.E = frozenset(c for c in self.gt_order if self.gt[c] == EXCLUDED)
        self.R = frozenset(c for c in self.gt_order if self.gt[c] == REJECTED)
        self.V_list = [c for c in self.gt_order if self.gt[c] not in (EXCLUDED, REJECTED)]
        self.V = frozenset(self.V_list)
        self.S = frozenset(c for c in self.gt_order if not self.excluded_by_spec(c))
        # CTRL-EXCL: GT(c) = EXCLUDED iff c not in S.
        self.excl_disagreements = sum(
            1 for c in self.gt_order if (self.gt[c] == EXCLUDED) != (c not in self.S))


def load_sample(folder: str, verify_hashes: bool = True) -> Sample:
    if verify_hashes:
        problems = verify_sha256sums(folder)
        if problems:
            raise SpecError("CTRL-HASH failed: " + "; ".join(problems))
    with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    names = tuple(a["name"] for a in spec["attributes"])
    domains = tuple(tuple(a["values"]) for a in spec["attributes"])
    outputs = tuple(spec["output"]["values"])
    for n in names:
        if not n.isidentifier():
            raise SpecError(f"attribute name {n!r} is not a Python identifier")
    for n, d in zip(names, domains):
        if not d or len(set(d)) != len(d) or not all(isinstance(v, str) for v in d):
            raise SpecError(f"attribute {n!r}: values must be distinct non-empty strings")
    if prod(len(d) for d in domains) > 200_000:
        raise SpecError("declared space exceeds 200,000 combinations")

    # CTRL-GT
    rows = _read_csv(os.path.join(folder, "ground_truth.csv"))
    if not rows or rows[0] != list(names) + ["output"]:
        raise SpecError("CTRL-GT failed: ground_truth.csv header")
    allowed = set(outputs) | {EXCLUDED, REJECTED}
    expected = product(*domains)
    gt: dict[tuple, str] = {}
    order: list[tuple] = []
    for i, r in enumerate(rows[1:], start=2):
        want = next(expected, None)
        if len(r) != len(names) + 1:
            raise SpecError(f"CTRL-GT failed: ground_truth.csv line {i} has {len(r)} cells")
        cond = tuple(r[:-1])
        if cond != want:
            raise SpecError(f"CTRL-GT failed: ground_truth.csv line {i} is out of odometer order")
        if r[-1] not in allowed:
            raise SpecError(f"CTRL-GT failed: ground_truth.csv line {i} output {r[-1]!r}")
        gt[cond] = r[-1]
        order.append(cond)
    if next(expected, None) is not None:
        raise SpecError("CTRL-GT failed: ground_truth.csv has fewer rows than the declared space")

    off_rows = _read_csv(os.path.join(folder, "official_examples.csv"))
    if not off_rows or off_rows[0] != ["case_id"] + list(names) + ["output"]:
        raise SpecError("CTRL-GT failed: official_examples.csv header")
    official = []
    for i, r in enumerate(off_rows[1:], start=2):
        if len(r) != len(names) + 2:
            raise SpecError(f"CTRL-GT failed: official_examples.csv line {i} has {len(r)} cells")
        cond = tuple(r[1:-1])
        if cond not in gt:
            raise SpecError(f"CTRL-GT failed: official_examples.csv line {i} uses an undeclared label")
        official.append((cond, r[-1]))

    s = Sample(folder, spec, names, domains, outputs, tuple(spec.get("exclusions", [])),
               gt, order, official)
    s.build_sets()
    return s
