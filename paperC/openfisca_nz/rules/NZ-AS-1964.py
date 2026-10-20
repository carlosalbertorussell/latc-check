"""Oracle for NZ-AS-1964: Accommodation Supplement eligibility (SSA 1964 formula) in OpenFisca Aotearoa.

Supplementary table (not a Paper C sample).  Encoding:
https://github.com/digitalaotearoa/openfisca-aotearoa at commit
9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb (AGPL-3.0), variable
accommodation_supplement__entitled, week 2018-W01.  Needs openfisca_aotearoa
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

PERIOD = "2018-W01"
OUTPUT_VAR = "accommodation_supplement__entitled"
TEST_FILES = ["openfisca_aotearoa/tests/social_security/accommodation_supplement/2018/*.yaml",
              "openfisca_aotearoa/tests/social_security/accommodation_supplement/1964/*.yaml"]
ATTR_VARS = {a["name"] for a in SPEC["attributes"]}
REP = {a["name"]: a["representative"] for a in SPEC["attributes"]}
FIXED_CHECKS: list = []
VALID_FROM, VALID_UNTIL = "1964-12-04", "2018-11-25"  # formula_1964_12_04 until formula_2018_11_26

ETERNAL = ["immigration__resident", "immigration__permanent_resident", "citizenship__citizen",
           "social_security__ordinarily_resident_in_new_zealand"]
WEEKLY = ["accommodation_supplement__accommodation_costs", "social_housing__eligible",
          "accommodation_supplement__below_income_threshold", "accommodation_supplement__below_cash_threshold"]
AGE_BANDS = [("<16", None, 16), (">=16", 16, None)]


def build_unit(row, uid):
    person = {n: REP[n][row[n]] for n in ETERNAL}
    person.update({n: {PERIOD: REP[n][row[n]]} for n in WEEKLY})
    person["age"] = {PERIOD: REP["age"][row["age"]]}
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
    row = {"age": _band(int(sim.calculate("age", p.start)[i]), AGE_BANDS)}
    for n in ETERNAL:
        row[n] = label_bool(sim.calculate(n, p.first_month if n == "social_security__ordinarily_resident_in_new_zealand" else p.start)[i])
    for n in WEEKLY:
        row[n] = label_bool(sim.calculate(n, p.first_week)[i])
    return {n: row[n] for n in NAMES}
