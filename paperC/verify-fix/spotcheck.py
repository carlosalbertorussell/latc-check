"""Step 2: direct OpenFisca spot check of ground_truth.csv.

Builds one OpenFisca Aotearoa simulation per drawn row from spec.json alone (attribute
representatives, fixed_inputs, entry variable at the spec's period). Does not use the
conversion's oracle.py or paperC/openfisca_nz/oracle_core.py.

Usage: <venv>/bin/python paperC/verify/spotcheck.py paperC/specs/NZ-SLP [...]
Writes paperC/verify/<ID>/spotcheck.csv and prints a summary.
"""

import csv
import datetime
import json
import os
import random
import sys

from openfisca_core import periods
from openfisca_core.simulations import SimulationBuilder

from openfisca_aotearoa import CountryTaxBenefitSystem

SEED = 20261020
N = 50
HERE = os.path.dirname(os.path.abspath(__file__))
TBS = CountryTaxBenefitSystem()


def months_of(week):
    p = periods.period(week)
    first = p.start
    last = first.offset(6, "day")
    out = []
    for d in (first, last):
        s = f"{d.year:04d}-{d.month:02d}"
        if s not in out:
            out.append(s)
    return out


def put(store, var, week, value):
    """Store an input for `var` in the period(s) the formulas read around `week`."""
    v = TBS.variables[var]
    unit = v.definition_period
    if unit == "eternity":
        store[var] = {"ETERNITY": value}
    elif unit == "month":
        store[var] = {m: value for m in months_of(week)}
    elif unit == "week":
        store[var] = {week: value}
    elif unit == "day":
        start = periods.period(week).start
        store[var] = {str(start.offset(i, "day")): value for i in range(7)}
    else:
        raise ValueError(f"{var}: unsupported period {unit}")


def build_slp(spec, row, week):
    p0 = {}
    for a in spec["attributes"]:
        put(p0, a["name"], week, a["representative"][row[a["name"]]])
    return ({"p0": p0}, {"f0": {"principal": ["p0"]}}, {"t0": {"principal": ["p0"]}},
            {"o0": {"principal": ["p0"]}})


def build_as(spec, row, week):
    p0, partner = {}, None
    for a in spec["attributes"]:
        name, val = a["name"], a["representative"][row[a["name"]]]
        if name == "partner_accommodation_supplement__receiving":
            continue
        put(p0, name, week, val)
    persons = {"p0": p0}
    family = {"principal": ["p0"]}
    tenancies = {"t0": {"principal": ["p0"]}}
    ownerships = {"o0": {"principal": ["p0"]}}
    if row["social_security__in_a_relationship"] == "True":
        partner = {}
        put(partner, "accommodation_supplement__cash_assets", week, 0)
        put(partner, "accommodation_supplement__receiving", week,
            row["partner_accommodation_supplement__receiving"] == "True")
        persons["p1"] = partner
        family["partners"] = ["p1"]
        tenancies["t1"] = {"principal": ["p1"]}
        ownerships["o1"] = {"principal": ["p1"]}
    return persons, {"f0": family}, tenancies, ownerships


def build_sps(spec, row, week):
    p0 = {}
    persons = {"p0": p0}
    family = {"principal": ["p0"]}
    tenancies = {"t0": {"principal": ["p0"]}}
    ownerships = {"o0": {"principal": ["p0"]}}
    for a in spec["attributes"]:
        name, val = a["name"], a["representative"][row[a["name"]]]
        if name == "children":
            kids = []
            for i, age in enumerate(val):
                k = {}
                put(k, "age", week, age)
                put(k, "social_security__financially_independent", week, False)
                persons[f"c{i}"] = k
                kids.append(f"c{i}")
                tenancies[f"tc{i}"] = {"principal": [f"c{i}"]}
                ownerships[f"oc{i}"] = {"principal": [f"c{i}"]}
            if kids:
                family["children"] = kids
            continue
        put(p0, name, week, val)
    return persons, {"f0": family}, tenancies, ownerships


BUILDERS = {"NZ-SLP": build_slp, "NZ-AS": build_as, "NZ-SPS": build_sps}


def evaluate(spec, row):
    week = spec["fixed_inputs"]["period"]["value"]
    persons, families, tenancies, ownerships = BUILDERS[spec["id"]](spec, row, week)
    sim = SimulationBuilder().build_from_entities(TBS, {
        "persons": persons, "families": families,
        "tenancies": tenancies, "ownerships": ownerships})
    out = sim.calculate(spec["output"]["name"], week)
    return "True" if bool(out[0]) else "False"


def check(folder):
    with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    rng = random.Random(SEED)
    idx = sorted(rng.sample(range(len(rows)), N))
    preds = [(e["id"], compile(e["predicate"], e["id"], "eval")) for e in spec["exclusions"]]
    names = [a["name"] for a in spec["attributes"]]
    out = []
    for i in idx:
        row = rows[i]
        cond = {n: row[n] for n in names}
        gt = row["output"]
        # predicates come from the committed spec.json; empty builtins as in PROTOCOL.md s 2
        held = [x for x, p in preds if eval(p, {"__builtins__": {}}, dict(cond))]
        of = evaluate(spec, cond)
        if gt == "EXCLUDED":
            verdict = "agree-excluded" if held else "EXCLUDED-without-predicate"
        else:
            verdict = "agree" if of == gt and not held else "DISAGREE"
        out.append({"index": i, "csv_line": i + 2, "ground_truth": gt,
                    "openfisca": of, "exclusions_holding": "+".join(held) or "-",
                    "verdict": verdict, **cond})
    os.makedirs(os.path.join(HERE, spec["id"]), exist_ok=True)
    with open(os.path.join(HERE, spec["id"], "spotcheck.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    counts = {}
    for r in out:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(spec["id"], "indices", idx)
    print(spec["id"], counts)
    return spec["id"], idx, out




def full(folder):
    """Supplementary: evaluate every row of ground_truth.csv (EXCLUDED rows included)."""
    with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    names = [a["name"] for a in spec["attributes"]]
    tally, bad = {}, []
    for i, row in enumerate(rows):
        of = evaluate(spec, {n: row[n] for n in names})
        key = (row["output"], of)
        tally[key] = tally.get(key, 0) + 1
        if row["output"] != "EXCLUDED" and of != row["output"]:
            bad.append(i)
    with open(os.path.join(HERE, spec["id"], "fullcheck.txt"), "w", encoding="utf-8") as f:
        f.write(f"{spec['id']}: {len(rows)} rows evaluated directly in OpenFisca\n")
        for (gt, of), k in sorted(tally.items()):
            f.write(f"ground_truth={gt} openfisca={of}: {k}\n")
        f.write(f"valid rows disagreeing: {len(bad)}\n")
        if bad:
            f.write("first disagreeing indices: " + " ".join(map(str, bad[:50])) + "\n")
    print(spec["id"], "full:", tally, "disagree", len(bad))


if __name__ == "__main__":
    if sys.argv[1] == "--full":
        for folder in sys.argv[2:]:
            full(folder)
    else:
        for folder in sys.argv[1:]:
            check(folder)
