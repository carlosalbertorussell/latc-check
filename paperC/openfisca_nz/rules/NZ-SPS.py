"""Oracle for NZ-SPS: Sole Parent Support eligibility in OpenFisca Aotearoa.

Encoding: https://github.com/digitalaotearoa/openfisca-aotearoa at commit
9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb (AGPL-3.0), variable
sole_parent_support__entitled, week 2019-W05.  Needs openfisca_aotearoa
installed (paperC/openfisca_nz/ENVIRONMENT.md); --check-official also needs the
clone's test files (environment variable OPENFISCA_AOTEAROA_DIR, or the
editable install's source tree).

    python oracle.py --enumerate                  writes ground_truth.csv (one simulation per row)
    python oracle.py --batch-diagnostic           shows whether batching rows would change results
    python oracle.py --check-official [--write] [--log FILE]
                                                  re-runs every official YAML case
                                                  directly and through the oracle;
                                                  --write rewrites official_examples.csv
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as _f:
    SPEC = json.load(_f)

PERIOD = "2019-W05"
MONTH = "2019-01"  # period.first_month of 2019-W05 (Monday 2019-01-28)
OUTPUT_VAR = "sole_parent_support__entitled"
TEST_FILES = ["openfisca_aotearoa/tests/social_security/sole_parent_support/*.yaml"]
ATTR_VARS = {a["name"] for a in SPEC["attributes"]} - {"children"} | {"social_security__financially_independent"}
REP = {a["name"]: a["representative"] for a in SPEC["attributes"]}
FIXED_CHECKS: list = []
VALID_FROM, VALID_UNTIL = "2018-11-26", None  # formula_2018_11_26; parameters constant since

CHILD_BANDS = [("<14", None, 14), ("14-15", 14, 16), ("16-17", 16, 18), (">=18", 18, None)]
AGE_BANDS = [("<20", None, 20), (">=20", 20, None)]
WEEK_BOOLS = [
    "social_security__in_a_relationship",
    "sole_parent_support__spouse_or_partner_died",
    "sole_parent_support__marriage_or_civil_union_dissolved",
    "sole_parent_support__living_apart_and_lost_support",
    "sole_parent_support__partner_imprisoned",
    "sole_parent_support__partner_supervision",
    "sole_parent_support__receiving",
    "sole_parent_support__principal_caregiver_before_apart",
    "sole_parent_support__principal_caregiver_of_youngest",
    "sole_parent_support__both_primary_caregiver_by_order",
    "social_security__residential_requirement",
]


def build_unit(row, uid):
    applicant = {n: {PERIOD: REP[n][row[n]]} for n in WEEK_BOOLS}
    applicant["social_security__principal_caregiver"] = {MONTH: REP["social_security__principal_caregiver"][row["social_security__principal_caregiver"]]}
    applicant["age"] = {PERIOD: REP["age"][row["age"]]}
    pid = f"{uid}_applicant"
    persons = {pid: applicant}
    kids = []
    for k, a in enumerate(REP["children"][row["children"]]):
        cid = f"{uid}_child{k + 1}"
        persons[cid] = {"age": {PERIOD: a}, "social_security__financially_independent": {PERIOD: False}}
        kids.append(cid)
    family = {"principal": pid}
    if kids:
        family["children"] = kids
    return persons, {"families": {f"{uid}_family": family}}, pid


def _band(value, bands):
    for label, lo, hi in bands:
        if (lo is None or value >= lo) and (hi is None or value < hi):
            return label
    raise Unmappable(f"value {value} outside every band")


def map_person(sim, i, period):
    from openfisca_core import periods
    p = periods.period(period)
    fam = sim.persons.family
    f_id = fam.members_entity_id[i]
    roles = [r.key for r in fam.members_role]
    if roles[i] != "principal":
        raise Unmappable(f"person has role {roles[i]} in the family; the table describes the family's principal")
    members = [j for j in range(len(roles)) if fam.members_entity_id[j] == f_id and j != i]
    others = sorted({roles[j] for j in members if roles[j] != "child"})
    if others:
        raise Unmappable(f"family has members in role(s) {', '.join(others)}; the table fixes a family of principal and children only")
    kids = [j for j in members if roles[j] == "child"]
    if len(kids) > 2:
        raise Unmappable(f"family has {len(kids)} children; the table covers at most 2")
    independent = sim.calculate("social_security__financially_independent", p.first_week)
    if any(independent[j] for j in kids):
        raise Unmappable("a child is financially independent; the table fixes this to False")
    ages = sim.calculate("age", p.start)
    order = [b[0] for b in CHILD_BANDS]
    bands = sorted((_band(int(ages[j]), CHILD_BANDS) for j in kids), key=order.index)
    children = "none" if not bands else f"{len(bands)}:" + "+".join(bands)
    row = {"children": children,
           "social_security__principal_caregiver": label_bool(sim.calculate("social_security__principal_caregiver", p.first_month)[i])}
    for n in WEEK_BOOLS:
        row[n] = label_bool(sim.calculate(n, p.first_week)[i])
    row["age"] = _band(int(sim.calculate("age", p.start)[i]), AGE_BANDS)
    return {n: row[n] for n in NAMES}
