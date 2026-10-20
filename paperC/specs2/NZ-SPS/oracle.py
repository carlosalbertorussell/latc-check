#!/usr/bin/env python3
"""Oracle for NZ-SPS (second coder): sole_parent_support__entitled.

Ground truth comes from running OpenFisca Aotearoa 22.0.0
(https://github.com/digitalaotearoa/openfisca-aotearoa, commit
9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb) on a family of a principal P
and one child C per table row; the output is P's entitlement.
Usage: python oracle.py --enumerate | --check-official [--write-official]
"""
import argparse
import copy
import csv
import itertools
import json
import os
import sys

PERIOD = "2019-W05"
FIRST_DAY = "2019-01-28"
MONTHS = "month:2019-01:2"  # the week 2019-W05 spans January and February 2019
SUBJECT_INDEX = 0
OFFICIAL_TESTS = ["social_security/sole_parent_support/sole_parent_support__entitled.yaml"]

# Formula variables between the attributes and the entry variable.
INTERMEDIATES = {
    "sole_parent_support__requirement",
    "sole_parent_support__dependent_child_requirement",
    "sole_parent_support__lost_regular_support",
    "sole_parent_support__split_care",
    "sole_parent_support__entitled_without_split_care_requirement",
    "sole_parent_support__age_threshold",
    "social_security__dependent_children",
}
INTERMEDIATE_PERIODS = [(v, PERIOD) for v in sorted(INTERMEDIATES - {"sole_parent_support__dependent_child_requirement"})] + [
    ("sole_parent_support__dependent_child_requirement", "%s-%d" % (PERIOD, d)) for d in range(1, 8)]

INTERVALS = {
    "age": [("<20", None, 19), ("20+", 20, None)],
    "child_age": [("<14", None, 13), ("14+", 14, None)],
}

# attribute -> (variable, period at which the formula reads it, whose value)
ATTRIBUTE_SOURCES = {
    "residential_requirement": ("social_security__residential_requirement", PERIOD, "self"),
    "age": ("age", FIRST_DAY, "self"),
    "in_a_relationship": ("social_security__in_a_relationship", PERIOD, "self"),
    "spouse_or_partner_died": ("sole_parent_support__spouse_or_partner_died", PERIOD, "self"),
    "marriage_or_civil_union_dissolved": ("sole_parent_support__marriage_or_civil_union_dissolved", PERIOD, "self"),
    "living_apart_and_lost_support": ("sole_parent_support__living_apart_and_lost_support", PERIOD, "self"),
    "partner_imprisoned": ("sole_parent_support__partner_imprisoned", PERIOD, "self"),
    "partner_supervision": ("sole_parent_support__partner_supervision", PERIOD, "self"),
    "principal_caregiver": ("social_security__principal_caregiver", "2019-01", "self"),
    "child_dependent": ("social_security__dependent_child", PERIOD, "child"),
    "child_age": ("age", FIRST_DAY, "child"),
}


def build_situation(v):
    return {
        "persons": {
            "P": {
                "social_security__residential_requirement": {PERIOD: v["residential_requirement"]},
                "age": {PERIOD: v["age"]},
                "social_security__in_a_relationship": {PERIOD: v["in_a_relationship"]},
                "sole_parent_support__spouse_or_partner_died": {PERIOD: v["spouse_or_partner_died"]},
                "sole_parent_support__marriage_or_civil_union_dissolved": {PERIOD: v["marriage_or_civil_union_dissolved"]},
                "sole_parent_support__living_apart_and_lost_support": {PERIOD: v["living_apart_and_lost_support"]},
                "sole_parent_support__partner_imprisoned": {PERIOD: v["partner_imprisoned"]},
                "sole_parent_support__partner_supervision": {PERIOD: v["partner_supervision"]},
                "social_security__principal_caregiver": {MONTHS: v["principal_caregiver"]},
            },
            "C": {
                "social_security__dependent_child": {PERIOD: v["child_dependent"]},
                "age": {PERIOD: v["child_age"]},
            },
        },
        "families": {"F": {"principal": ["P"], "children": ["C"]}},
    }


def structure_problem(sim, i):
    fam = sim.populations["family"]
    f = fam.members_entity_id[i]
    if fam.members_role[i].key != "principal":
        return "person is not the principal of its family (the table is about the principal P)"
    roles = [fam.members_role[k].key for k in range(len(fam.members_entity_id)) if fam.members_entity_id[k] == f]
    if sorted(roles) != ["child", "principal"]:
        return "family is not exactly one principal and one child (the table fixes that composition)"
    return None


def who_index(sim, i, who):
    if who == "self":
        return i
    fam = sim.populations["family"]
    f = fam.members_entity_id[i]
    return [k for k in range(len(fam.members_entity_id))
            if fam.members_entity_id[k] == f and fam.members_role[k].key == "child"][0]


# ---------------------------------------------------------------------------
# Generic part (identical in the three NZ oracles of the second coder).
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as _f:
    SPEC = json.load(_f)
ATTRS = [a["name"] for a in SPEC["attributes"]]
VALUES = {a["name"]: a["values"] for a in SPEC["attributes"]}
KIND = {a["name"]: a["kind"] for a in SPEC["attributes"]}
REPR = {a["name"]: a.get("representative", {}) for a in SPEC["attributes"]}
OUT_VAR = SPEC["source"]["entry_point"]

_TBS = None


def tbs():
    global _TBS
    if _TBS is None:
        from openfisca_aotearoa import CountryTaxBenefitSystem
        _TBS = CountryTaxBenefitSystem()
    return _TBS


def concrete(name, label):
    """Concrete value passed to the encoding for an attribute label."""
    if KIND[name] == "bool":
        return label == "True"
    if label in REPR[name]:
        return REPR[name][label]
    return label


def label_of(name, value):
    """Label of an attribute for a concrete value computed by the encoding."""
    if KIND[name] == "bool":
        return "True" if bool(value) else "False"
    if KIND[name] == "interval":
        for lab, lo, hi in INTERVALS[name]:
            if (lo is None or value >= lo) and (hi is None or value <= hi):
                return lab
        return None
    return str(value)


def excluded(row):
    for ex in SPEC["exclusions"]:
        if eval(ex["predicate"], {"__builtins__": {}}, dict(row)):
            return True
    return False


def evaluate(row):
    """Run the original encoding on one table row; return the output label."""
    from openfisca_core.simulation_builder import SimulationBuilder
    try:
        situation = build_situation({k: concrete(k, row[k]) for k in ATTRS})
        sim = SimulationBuilder().build_from_entities(tbs(), situation)
        value = sim.calculate(OUT_VAR, PERIOD)[SUBJECT_INDEX]
        return "True" if bool(value) else "False"
    except Exception:  # an error of the encoding is a REJECTED cell
        return "REJECTED"


def enumerate_table(path):
    n = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(ATTRS + ["output"])
        for combo in itertools.product(*[VALUES[a] for a in ATTRS]):
            row = dict(zip(ATTRS, combo))
            out = "EXCLUDED" if excluded(row) else evaluate(row)
            w.writerow(list(combo) + [out])
            n += 1
    return n


# ----- official tests -------------------------------------------------------

def _tests_dir():
    import openfisca_aotearoa
    return os.path.join(os.path.dirname(openfisca_aotearoa.__file__), "tests")


def _strip(inp, names):
    inp = copy.deepcopy(inp)
    for k in list(inp):
        if k in names:
            del inp[k]
    if isinstance(inp.get("persons"), dict):
        for p in inp["persons"].values():
            for k in list(p):
                if k in names:
                    del p[k]
    return inp


def _expected(test):
    """Expected output values per person at PERIOD, or None if the test does
    not state the entry variable at PERIOD."""
    out = test.get("output", {}).get(OUT_VAR)
    if out is None:
        return None
    if isinstance(out, dict):
        if PERIOD not in out:
            return None
        out = out[PERIOD]
    elif str(test["period"]) != PERIOD:
        return None
    return out if isinstance(out, list) else [out]


def _build(test, inp):
    from openfisca_core.simulation_builder import SimulationBuilder
    b = SimulationBuilder()
    b.set_default_period(str(test["period"]))
    return b.build_from_dict(tbs(), copy.deepcopy(inp))


def official_cases():
    """Yield (case_id, mapped_row_or_None, reason, expected_label, encoding_label)."""
    import yaml
    base = _tests_dir()
    for rel in OFFICIAL_TESTS:
        with open(os.path.join(base, rel), encoding="utf-8") as f:
            tests = yaml.safe_load(f)
        for ti, test in enumerate(tests):
            sim = _build(test, test["input"])
            ids = list(sim.persons.ids)
            exp = _expected(test)
            if exp is None:
                for pid in ids:
                    yield (f"{rel}#{ti}:{pid}", None,
                           f"entry variable not asserted at the fixed period {PERIOD}", None, None)
                continue
            got = sim.calculate(OUT_VAR, PERIOD)
            stripped = _build(test, _strip(test["input"], INTERMEDIATES))
            got_s = stripped.calculate(OUT_VAR, PERIOD)
            for i, pid in enumerate(ids):
                cid = f"{rel}#{ti}:{pid}"
                e = "True" if bool(exp[i]) else "False"
                g = "True" if bool(got[i]) else "False"
                reason = structure_problem(sim, i)
                if reason is None:
                    changed = [v for v, per in INTERMEDIATE_PERIODS
                               if bool(sim.calculate(v, per)[i]) != bool(stripped.calculate(v, per)[i])]
                    if changed or bool(got[i]) != bool(got_s[i]):
                        reason = ("sets intermediate variable(s) to values their formulas do not give "
                                  "for this case: " + ", ".join(changed or [OUT_VAR]))
                row = None
                if reason is None:
                    row = {}
                    for name, (var, per, who) in ATTRIBUTE_SOURCES.items():
                        j = who_index(sim, i, who)
                        lab = label_of(name, sim.calculate(var, per)[j])
                        if lab is None:
                            reason = f"{var} has no declared label (value not set)"
                            row = None
                            break
                        row[name] = lab
                yield (cid, row, reason, e, g)


def check_official(write=None):
    total = mapped = enc_pass = orc_pass = 0
    rows = []
    for cid, row, reason, exp, got in official_cases():
        total += 1
        if exp is not None and got == exp:
            enc_pass += 1
        if row is None:
            print(f"UNMAPPED {cid}: {reason}")
            continue
        mapped += 1
        o = evaluate(row)
        ok = o == exp
        orc_pass += ok
        print(f"{'PASS' if ok else 'FAIL'} {cid}: oracle={o} expected={exp}")
        rows.append([cid] + [row[a] for a in ATTRS] + [exp])
    print(f"person-cases: {total}; original encoding matches expected: {enc_pass} "
          f"(of cases asserting the entry variable at {PERIOD}); mapped: {mapped}; oracle pass: {orc_pass}/{mapped}")
    if write:
        with open(write, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["case_id"] + ATTRS + ["output"])
            w.writerows(rows)
    return mapped == orc_pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enumerate", action="store_true", help="write ground_truth.csv")
    ap.add_argument("--check-official", action="store_true",
                    help="run official tests through the encoding and the oracle")
    ap.add_argument("--write-official", action="store_true",
                    help="with --check-official, also write official_examples.csv")
    a = ap.parse_args()
    ok = True
    if a.check_official:
        ok = check_official(os.path.join(HERE, "official_examples.csv") if a.write_official else None)
    if a.enumerate:
        n = enumerate_table(os.path.join(HERE, "ground_truth.csv"))
        print(f"wrote {n} rows")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
