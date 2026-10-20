"""Oracle for NZ-AS: Accommodation Supplement eligibility (SSA 2018 formula) in OpenFisca Aotearoa.

Encoding: https://github.com/digitalaotearoa/openfisca-aotearoa at commit
9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb (AGPL-3.0), variable
accommodation_supplement__entitled, week 2022-W01.  Needs openfisca_aotearoa
installed (paperC/openfisca_nz/ENVIRONMENT.md); --check-official also needs the
clone's test files (environment variable OPENFISCA_AOTEAROA_DIR, or the
editable install's source tree).

    python oracle.py --enumerate                  writes ground_truth.csv
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

PERIOD = "2022-W01"
MONTH = "2022-01"  # period.first_month of 2022-W01 (Monday 2022-01-03)
OUTPUT_VAR = "accommodation_supplement__entitled"
TEST_FILES = ["openfisca_aotearoa/tests/social_security/accommodation_supplement/2018/*.yaml",
              "openfisca_aotearoa/tests/social_security/accommodation_supplement/1964/*.yaml"]
ATTR_VARS = ({a["name"] for a in SPEC["attributes"]} - {"partner_accommodation_supplement__receiving"}
             | {"accommodation_supplement__receiving"})
REP = {a["name"]: a["representative"] for a in SPEC["attributes"]}
FIXED_CHECKS: list = []
VALID_FROM, VALID_UNTIL = "2018-11-26", None  # formula_2018_11_26; parameters constant since

WEEK_VARS = [
    "social_security__residential_requirement", "accommodation_type", "accommodation_costs",
    "social_security__in_a_relationship", "social_security__dependent_children",
    "accommodation_supplement__cash_assets", "basic_grant__receiving",
    "independent_circumstances_grant__receiving", "basic_grant__would_be_entitled",
    "independent_circumstances_grant__would_be_entitled", "accommodation_supplement__disability",
]
MONTH_VARS = ["basic_grant__entitled", "independent_circumstances_grant__entitled"]
COSTS = [("<=0", None, 0.0000001), (">0", 0.0000001, None)]
CASH = [("<=8100", None, 8101), ("8101-16200", 8101, 16201), (">16200", 16201, None)]


def build_unit(row, uid):
    applicant = {n: {PERIOD: REP[n][row[n]]} for n in WEEK_VARS}
    applicant.update({n: {MONTH: REP[n][row[n]]} for n in MONTH_VARS})
    pid = f"{uid}_applicant"
    persons = {pid: applicant}
    family = {"principal": pid}
    if row["social_security__in_a_relationship"] == "True":
        partner = f"{uid}_partner"
        persons[partner] = {
            "accommodation_supplement__receiving": {PERIOD: REP["partner_accommodation_supplement__receiving"][row["partner_accommodation_supplement__receiving"]]},
            "accommodation_supplement__cash_assets": {PERIOD: 0},
        }
        family["partners"] = [partner]
    groups = {
        "families": {f"{uid}_family": family},
        "tenancies": {f"{uid}_tenancy": {"principal": pid}},
        "ownerships": {f"{uid}_ownership": {"principal": pid}},
    }
    return persons, groups, pid


def _band(value, bands):
    for label, lo, hi in bands:
        if (lo is None or value >= lo) and (hi is None or value < hi):
            return label
    raise Unmappable(f"value {value} outside every band")


def _group(sim, entity_key, i):
    pop = getattr(sim.persons, entity_key)
    roles = [r.key for r in pop.members_role]
    g = pop.members_entity_id[i]
    return roles, [j for j in range(len(roles)) if pop.members_entity_id[j] == g and j != i]


def map_person(sim, i, period):
    from openfisca_core import periods
    p = periods.period(period)
    w = p.first_week
    roles, members = _group(sim, "family", i)
    if roles[i] != "principal":
        raise Unmappable(f"person has role {roles[i]} in the family; the table describes the family's principal")
    partners = [j for j in members if roles[j] == "partner"]
    if len(partners) > 1:
        raise Unmappable("family has more than one partner")
    for key in ("tenancy", "ownership"):
        r2, m2 = _group(sim, key, i)
        if r2[i] != "principal" or m2:
            raise Unmappable(f"the person is not the sole principal of their {key}")
    cash = sim.calculate("accommodation_supplement__cash_assets", w)
    receiving = sim.calculate("accommodation_supplement__receiving", w)
    costs = float(sim.calculate("accommodation_costs", w)[i])
    row = {
        "social_security__residential_requirement": label_bool(sim.calculate("social_security__residential_requirement", w)[i]),
        "accommodation_type": sim.calculate("accommodation_type", w).decode()[i].name,
        "accommodation_costs": _band(costs, COSTS),
        "social_security__in_a_relationship": label_bool(sim.calculate("social_security__in_a_relationship", w)[i]),
        "social_security__dependent_children": "0" if int(sim.calculate("social_security__dependent_children", w)[i]) < 1 else ">=1",
        "accommodation_supplement__cash_assets": _band(int(cash[i] + sum(cash[j] for j in partners)), CASH),
        "partner_accommodation_supplement__receiving": label_bool(any(receiving[j] for j in partners)),
    }
    for n in ["basic_grant__receiving", "independent_circumstances_grant__receiving",
              "basic_grant__would_be_entitled", "independent_circumstances_grant__would_be_entitled",
              "accommodation_supplement__disability"]:
        row[n] = label_bool(sim.calculate(n, w)[i])
    for n in MONTH_VARS:
        row[n] = label_bool(sim.calculate(n, p.first_month)[i])
    return {n: row[n] for n in NAMES}
