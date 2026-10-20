"""Oracle for NZ-SLP: Supported Living Payment eligibility in OpenFisca Aotearoa.

Encoding: https://github.com/digitalaotearoa/openfisca-aotearoa at commit
9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb (AGPL-3.0), variable
supported_living_payment__entitled, week 2019-W01.  Needs openfisca_aotearoa
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

PERIOD = "2019-W01"
OUTPUT_VAR = "supported_living_payment__entitled"
TEST_FILES = ["openfisca_aotearoa/tests/social_security/supported_living_payment/*.yaml"]
ATTR_VARS = {a["name"] for a in SPEC["attributes"]}
REP = {a["name"]: a["representative"] for a in SPEC["attributes"]}
FIXED_CHECKS: list = []
VALID_FROM, VALID_UNTIL = "2018-11-26", None  # formula_2018_11_26; parameters constant since

AGE_BANDS = [("<16", None, 16), ("16-17", 16, 18), ("18-19", 18, 20), (">=20", 20, None)]


def build_unit(row, uid):
    r = {n: REP[n][row[n]] for n in REP}
    person = {
        "supported_living_payment__restricted_work_capacity": {PERIOD: r["supported_living_payment__restricted_work_capacity"]},
        "totally_blind": r["totally_blind"],
        "social_security__residential_requirement": {PERIOD: r["social_security__residential_requirement"]},
        "age": {PERIOD: r["age"]},
        "supported_living_payment__disability_self_inflicted": r["supported_living_payment__disability_self_inflicted"],
        "supported_living_payment__caring_for_another_person": {PERIOD: r["supported_living_payment__caring_for_another_person"]},
        "social_security__dependent_children": {PERIOD: r["social_security__dependent_children"]},
    }
    pid = f"{uid}_applicant"
    return {pid: person}, {"families": {f"{uid}_family": {"principal": pid}}}, pid


def _band(value, bands):
    for label, lo, hi in bands:
        if (lo is None or value >= lo) and (hi is None or value < hi):
            return label
    raise Unmappable(f"value {value} outside every band")


def map_person(sim, i, period):
    from openfisca_core import periods
    p = periods.period(period)
    return {
        "supported_living_payment__restricted_work_capacity": label_bool(sim.calculate("supported_living_payment__restricted_work_capacity", p.first_week)[i]),
        "totally_blind": label_bool(sim.calculate("totally_blind", p.start)[i]),
        "social_security__residential_requirement": label_bool(sim.calculate("social_security__residential_requirement", p.first_week)[i]),
        "age": _band(int(sim.calculate("age", p.start)[i]), AGE_BANDS),
        "supported_living_payment__disability_self_inflicted": label_bool(sim.calculate("supported_living_payment__disability_self_inflicted", p)[i]),
        "supported_living_payment__caring_for_another_person": label_bool(sim.calculate("supported_living_payment__caring_for_another_person", p.first_week)[i]),
        "social_security__dependent_children": "0" if int(sim.calculate("social_security__dependent_children", p.first_week)[i]) == 0 else ">=1",
    }

