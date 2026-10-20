"""Shared machinery for the oracle.py files of paperC/specs/FR-APL/* and paperC/specs/US-121/*.

Each oracle.py defines the table-specific parts (how a row of labels becomes inputs
of the generated Catala code, how the scope output becomes a label, and how each
official test maps onto a row) and calls `main()` below for the three commands of
paperC/specs/FORMAT.md:

  python oracle.py --enumerate        writes ground_truth.csv (and prints the counts)
  python oracle.py --check-official   re-runs every official test directly and through
                                      the oracle and prints pass counts
  python oracle.py --check-bands      evaluates extra points inside every interval
                                      label and reports any label whose output is not
                                      constant (documentation aid; see CONVERSION.md)
  python oracle.py --write-official   writes official_examples.csv from the mapped cases

Only the standard library is used.
"""

import collections
import csv
import itertools
import json
import os
import sys

EXCLUDED = "EXCLUDED"
REJECTED = "REJECTED"


def load_spec(folder):
    with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
        return json.load(f)


def names(spec):
    return [a["name"] for a in spec["attributes"]]


def declared_rows(spec):
    """Cartesian product of the declared labels in odometer order (last attribute fastest)."""
    ns = names(spec)
    for combo in itertools.product(*[a["values"] for a in spec["attributes"]]):
        yield dict(zip(ns, combo))


def excluded_by(spec, row):
    """Ids of the exclusion predicates that hold at `row` (evaluated as in PROTOCOL.md section 2)."""
    # eval with empty builtins is the evaluation rule PROTOCOL.md section 2 prescribes;
    # the predicates come from this repository's own spec.json files.
    return [e["id"] for e in spec["exclusions"] if eval(e["predicate"], {"__builtins__": {}}, dict(row))]


class Oracle:
    """Evaluates rows of labels. A row becomes a raw input description by starting from
    `baseline()` (the fixed inputs) and letting each attribute set its raw value;
    `run(raw)` calls the generated Catala code and returns an output label, or raises
    one of `error_types` (Catala runtime errors), which gives REJECTED."""

    def __init__(self, spec, attributes, baseline, run, error_types):
        self.spec = spec
        self.attributes = attributes
        self.baseline = baseline
        self.run = run
        self.error_types = error_types
        self.last_error = None

    def raw_of(self, row, overrides=None):
        overrides = overrides or {}
        raw = self.baseline()
        for a in self.attributes:
            a.apply(raw, overrides[a.name] if a.name in overrides else a.raw[row[a.name]])
        return raw

    def compute(self, row):
        return self.run(self.raw_of(row))

    def compute_raw(self, row, overrides):
        return self.run(self.raw_of(row, overrides))

    def evaluate(self, row):
        self.last_error = None
        if excluded_by(self.spec, row):
            return EXCLUDED
        try:
            label = self.compute(row)
        except self.error_types as exc:
            self.last_error = exc
            return REJECTED
        if label not in self.spec["output"]["values"]:
            raise ValueError(f"compute() returned {label!r}, which is not a declared output label")
        return label


def error_key(exc):
    """Short, stable description of a Catala runtime error: class name and first source position."""
    pos = exc.source_positions[0] if getattr(exc, "source_positions", None) else None
    where = "" if pos is None else f" at {pos}"
    return f"{type(exc).__name__}{where}"


def enumerate_table(folder, oracle):
    spec = oracle.spec
    ns = names(spec)
    path = os.path.join(folder, "ground_truth.csv")
    counts = collections.Counter()
    reasons = collections.Counter()
    excl_ids = collections.Counter()
    total = 1
    for a in spec["attributes"]:
        total *= len(a["values"])
    if total > 200_000:
        sys.exit(f"declared space has {total} rows, above the 200,000 limit of FORMAT.md")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(ns + ["output"])
        for i, row in enumerate(declared_rows(spec), 1):
            out = oracle.evaluate(row)
            counts[out] += 1
            if out == REJECTED:
                reasons[error_key(oracle.last_error)] += 1
            if out == EXCLUDED:
                for eid in excluded_by(spec, row):
                    excl_ids[eid] += 1
            w.writerow([row[n] for n in ns] + [out])
            if i % 20000 == 0:
                print(f"  {i}/{total} rows", file=sys.stderr)
    print(f"wrote {path}: {total} rows")
    for label in spec["output"]["values"] + [EXCLUDED, REJECTED]:
        print(f"  {label}: {counts[label]}")
    for eid, n in sorted(excl_ids.items()):
        print(f"  exclusion {eid} holds in {n} rows")
    for key, n in sorted(reasons.items()):
        print(f"  REJECTED because of {key}: {n} rows")
    return counts


def check_official(oracle, cases):
    """`cases`: list of dicts with keys case_id, direct (callable returning (ok, detail)),
    row (dict of labels, or None when unmappable), expected (asserted output label or None),
    reason (why unmappable)."""
    n = len(cases)
    direct_ok = mapped = oracle_ok = 0
    for c in cases:
        try:
            ok, detail = c["direct"]()
        except Exception as exc:  # a Catala runtime error counts as a failure
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        direct_ok += bool(ok)
        line = f"{'PASS' if ok else 'FAIL'}  direct  {c['case_id']}: {detail}"
        print(line)
        if c["row"] is None:
            print(f"      not mapped onto this table: {c['reason']}")
            continue
        mapped += 1
        for n_, v in c["row"].items():
            vals = next(a["values"] for a in oracle.spec["attributes"] if a["name"] == n_)
            if v not in vals:
                raise ValueError(f"{c['case_id']}: label {v!r} is not declared for {n_}")
        got = oracle.evaluate(c["row"])
        ok2 = got == c["expected"]
        oracle_ok += ok2
        print(f"{'PASS' if ok2 else 'FAIL'}  oracle  {c['case_id']}: evaluate(row) = {got}, asserted {c['expected']}")
    print(f"\ndirect re-run through the generated Python: {direct_ok}/{n} passed")
    print(f"mapped onto this table: {mapped}/{n}; oracle agrees with the asserted output: {oracle_ok}/{mapped}")
    return direct_ok == n and oracle_ok == mapped


def write_official(folder, spec, cases):
    ns = names(spec)
    path = os.path.join(folder, "official_examples.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id"] + ns + ["output"])
        for c in cases:
            if c["row"] is not None:
                w.writerow([c["case_id"]] + [c["row"][n] for n in ns] + [c["expected"]])
    print(f"wrote {path}")


def check_bands(oracle, probes, base_rows):
    """For each (attribute, label) in `probes` (a dict attr -> label -> list of
    alternative raw values), evaluate every row of `base_rows` with the attribute's
    representative replaced by each alternative value, and report rows where the
    output differs from the output at the representative. `oracle.compute_raw(row,
    overrides)` must evaluate with raw-value overrides."""
    problems = collections.Counter()
    examples = {}
    checked = 0
    for attr, by_label in probes.items():
        for label, alternatives in by_label.items():
            for row in base_rows:
                if row[attr] != label or excluded_by(oracle.spec, row):
                    continue
                ref = oracle.evaluate(row)
                for alt in alternatives:
                    checked += 1
                    try:
                        got = oracle.compute_raw(row, {attr: alt})
                    except oracle.error_types:
                        got = REJECTED
                    if got != ref:
                        problems[(attr, label, alt, ref, got)] += 1
                        examples.setdefault((attr, label, alt, ref, got), dict(row))
    print(f"band check: {checked} evaluations at non-representative values")
    if not problems:
        print("every interval label gave the same output at every probed value")
    for key, n in sorted(problems.items(), key=str):
        attr, label, alt, ref, got = key
        print(f"  {attr}={label} at raw value {alt!r}: {ref} at the representative, {got} here, in {n} rows; e.g. {examples[key]}")
    return problems


class Attribute:
    """One attribute of a table. `labels` is a list of (label, raw value, literal):
    the raw value is what the oracle passes to the input builder, the literal is the
    human-readable concrete value written to spec.json as `representative`."""

    def __init__(self, name, kind, labels, source, apply):
        self.name = name
        self.kind = kind
        self.labels = labels
        self.source = source
        self.apply = apply  # apply(raw_dict, raw_value) sets the input(s)
        self.raw = {lab: r for lab, r, _ in labels}

    def as_json(self):
        return {
            "name": self.name,
            "kind": self.kind,
            "values": [lab for lab, _, _ in self.labels],
            "representative": {lab: lit for lab, _, lit in self.labels},
            "source": self.source,
        }


def build_spec(meta, attributes):
    spec = {"id": meta["id"], "title": meta["title"], "source": meta["source"],
            "attributes": [a.as_json() for a in attributes]}
    for k in ("output", "exclusions", "fixed_inputs", "notes"):
        spec[k] = meta[k]
    return spec


def spec_text(spec):
    return json.dumps(spec, ensure_ascii=False, indent=2) + "\n"


def write_spec(folder, spec):
    path = os.path.join(folder, "spec.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(spec_text(spec))
    print(f"wrote {path}")


def spec_matches_file(folder, spec):
    path = os.path.join(folder, "spec.json")
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        return f.read() == spec_text(spec)


def main(folder, oracle, cases, probes=None, band_rows=None):
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if "--write-spec" in args:
        write_spec(folder, oracle.spec)
        args = [a for a in args if a != "--write-spec"]
    elif not spec_matches_file(folder, oracle.spec):
        sys.exit("spec.json differs from the table definition in oracle.py; run with --write-spec")
    status = 0
    for a in args:
        if a == "--enumerate":
            enumerate_table(folder, oracle)
        elif a == "--check-official":
            status |= 0 if check_official(oracle, cases) else 1
        elif a == "--write-official":
            write_official(folder, oracle.spec, cases)
        elif a == "--check-bands":
            rows = band_rows() if band_rows else list(declared_rows(oracle.spec))
            status |= 1 if check_bands(oracle, probes or {}, rows) else 0
        else:
            print(f"unknown option {a}")
            return 2
    return status
