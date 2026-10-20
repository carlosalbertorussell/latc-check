#!/usr/bin/env python3
"""Oracle for US-121-1: section 121(a) ownership and use requirements of one taxpayer
(scope Section121SinglePerson, output requirements_met).

Holds the table definition (spec.json is written from it with --write-spec), evaluates
rows through the Catala 1.3.0 Python build in paperC/catala_more/, and maps the
official tests onto rows.

  python oracle.py --check-official | --enumerate | --write-official | --check-bands | --write-spec
"""

import copy
import os
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(FOLDER, "..", "..", "..", "catala_more")))

import oracle_common as OC  # noqa: E402
import run_official_tests_us121 as R  # noqa: E402
import us121_inputs as U  # noqa: E402

S121 = "us_tax_code/section_121.catala_en"
TESTS = "us_tax_code/tests/test_section_121.catala_en"
SALE = R.DATA["date_of_sale_or_exchange"]       # |2021-01-01|, Data scope line 19
GAIN = R.DATA["gain"]                             # $350,000, Data scope line 21
THRESHOLD_DAYS = 730                              # section_121.catala_en:197 and 204


def periods_literal(pairs):
    return "[" + "; ".join(f"Period {{begin: |{b}|, end: |{e}|}}" for b, e in pairs) + "]"


def days_band(pairs):
    days = U.aggregate_days_last_five_years(SALE, pairs)
    return "ge_730_days" if days >= THRESHOLD_DAYS else "lt_730_days"


PERIOD_LABELS = [
    ("lt_730_days", [("2020-01-01", "2021-01-01")], periods_literal([("2020-01-01", "2021-01-01")])),
    ("ge_730_days", [("2017-01-01", "2021-01-01")], periods_literal([("2017-01-01", "2021-01-01")])),
]
OTHER_SALE = [
    ("none", None, "NoOtherSaleWhereSection121aApplied"),
    ("within_2_years", "2020-01-01",
     "MostRecentSaleWhereSection121aApplied content PreviousSaleWhereSection121aApplied "
     "{date_of_sale_or_exchange: |2020-01-01|}"),
    ("more_than_2_years", "2018-06-01",
     "MostRecentSaleWhereSection121aApplied content PreviousSaleWhereSection121aApplied "
     "{date_of_sale_or_exchange: |2018-06-01|}"),
]


def setter(key):
    def apply(raw, value):
        raw[key] = value
    return apply


BASE = {"date_of_sale": SALE, "gain": GAIN, "ownage": None, "usage": None, "previous_sale": None}


def baseline():
    return copy.deepcopy(BASE)


def run(raw):
    out = U.single_person(raw["date_of_sale"], raw["ownage"], raw["usage"], raw["gain"], raw["previous_sale"])
    return "requirements_met" if bool(out.requirements_met) else "requirements_not_met"


ATTRIBUTES = [
    OC.Attribute(
        "ownership_days_in_5_years", "interval", PERIOD_LABELS,
        "Section121SinglePerson.property_ownage (" + S121 + ":36), aggregated by "
        "aggregate_periods_from_last_five_years (" + S121 + ":179-191) and compared with 730 days (" + S121 +
        ":196-198; Treas. Reg. 1.121-1(c)(1)); 26 U.S.C. 121(a): owned for periods aggregating 2 years or more "
        "during the 5 years ending on the date of sale",
        setter("ownage")),
    OC.Attribute(
        "use_days_in_5_years", "interval", PERIOD_LABELS,
        "Section121SinglePerson.property_usage_as_principal_residence (" + S121 + ":38-39), same aggregation, "
        "compared with 730 days (" + S121 + ":200-205); 26 U.S.C. 121(a): used as principal residence for periods "
        "aggregating 2 years or more",
        setter("usage")),
    OC.Attribute(
        "other_section_121a_sale", "enum", OTHER_SALE,
        "Section121SinglePerson.other_section_121a_sale, enumeration OtherSection121aSale (" + S121 + ":26-29, 48); "
        "read by section_121_b_3_applies (" + S121 + ":371-377); 26 U.S.C. 121(b)(3): one sale every 2 years. "
        "within_2_years: the earlier sale took place 1 day to 2 years before the date of sale; more_than_2_years: "
        "more than 2 years before",
        setter("previous_sale")),
]

META = {
    "id": "US-121-1",
    "title": "US IRC section 121(a): ownership and use requirements of one taxpayer",
    "source": {
        "repository": "https://github.com/CatalaLang/catala-examples",
        "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
        "entry_point": "Us_tax_code scope Section121SinglePerson, output requirements_met "
                       "(Python: generated.Us_tax_code.section121_single_person, Catala 1.3.0)",
        "files": [S121, "us_tax_code/us_tax_code.catala_en", TESTS],
    },
    "output": {
        "name": "requirements_met",
        "values": ["requirements_met", "requirements_not_met"],
        "source": "Section121SinglePerson.requirements_met (" + S121 + ":32, rule 207-209): ownership and use "
                  "requirements of 26 U.S.C. 121(a) both met",
    },
    "exclusions": [],
    "fixed_inputs": {
        "date_of_sale_or_exchange": {"value": "|2021-01-01|", "why": "Data scope of the official tests (" + TESTS + ":19)"},
        "gain_from_sale_or_exchange_of_property": {"value": "$350,000", "why": "Data scope of the official tests (" + TESTS + ":21); requirements_met does not read it"},
        "gain_cap, section_121_b_3_applies (context variables)": {"value": "not redefined (the scope's own definitions)", "why": "the official tests do not redefine them"},
    },
    "notes": "Sub-table 1 of 2 of US-121. REJECTED rows: whenever another section 121(a) sale is given, the "
             "comparison `date_of_sale_or_exchange - other_sale.date_of_sale_or_exchange <= 2 year` ("
             + S121 + ":376) compares a duration in days with a duration in years, which Catala rejects at run "
             "time (DateError); the scope computes all its outputs, so requirements_met is not returned either. "
             "The Catala interpreter gives the same error (paperC/catala_more/probes/probe_b3_output.txt).",
}

SPEC = OC.build_spec(META, ATTRIBUTES)
ORACLE = OC.Oracle(SPEC, ATTRIBUTES, baseline, run, (U.CatalaError,))


def evaluate(row: dict[str, str]) -> str:
    return ORACLE.evaluate(row)


# ------------------------------------------------------------- official tests

def single_person_case(name, ownage, usage, expected):
    def direct():
        results = R.make_single_person_test(ownage, usage, expected)()
        return all(ok for _, ok in results), "; ".join(label for label, _ in results)
    row = {
        "ownership_days_in_5_years": days_band(ownage),
        "use_days_in_5_years": days_band(usage),
        "other_section_121a_sale": "none",
    }
    # The band of each list of periods agrees with the scope's own comparisons.
    out = U.single_person(SALE, ownage, usage, GAIN)
    assert (row["ownership_days_in_5_years"] == "ge_730_days") == bool(out.requirements_ownership_met)
    assert (row["use_days_in_5_years"] == "ge_730_days") == bool(out.requirements_usage_met)
    return {"case_id": f"test_section_121/{name}", "direct": direct, "row": row,
            "expected": "requirements_met" if expected else "requirements_not_met", "reason": None}


def two_persons_case(name, fn):
    def direct():
        results = fn()
        return all(ok for _, ok in results), "; ".join(label for label, _ in results)
    return {"case_id": f"test_section_121/{name}", "direct": direct, "row": None, "expected": None,
            "reason": "tests scope Section121TwoPersons and asserts income_excluded_from_gross_income (US-121-2); "
                      "this table is Section121SinglePerson.requirements_met"}


CASES = [single_person_case(n, o, u, e) for n, o, u, e in R.SINGLE_PERSON_TESTS]
CASES += [two_persons_case("Test5", R.test5), two_persons_case("Test6", R.test6)]

# ---------------------------------------------------------------- band probes

PERIOD_PROBES = {
    "lt_730_days": [[], [("2019-01-03", "2021-01-01")], [("2019-01-01", "2020-01-01")],
                    [("2015-01-01", "2017-01-02")], [("2010-01-01", "2015-06-01")]],
    "ge_730_days": [[("2019-01-02", "2021-01-01")], [("2015-01-01", "2017-01-02"), ("2019-01-01", "2020-01-01")],
                    [("2016-01-01", "2021-01-01")], [("2010-01-01", "2021-01-01")]],
}
for lab, alts in PERIOD_PROBES.items():
    for pairs in alts:
        assert days_band(pairs) == lab, (lab, pairs)
PROBES = {
    "ownership_days_in_5_years": PERIOD_PROBES,
    "use_days_in_5_years": PERIOD_PROBES,
    "other_section_121a_sale": {
        # 1 day to 2 years before the sale. A previous sale on the sale date itself (a zero-day
        # difference) is left out of every label: see CONVERSION.md.
        "within_2_years": ["2019-01-01", "2019-01-02", "2020-12-31"],
        "more_than_2_years": ["2018-12-31", "2010-01-01"],
    },
}

if __name__ == "__main__":
    sys.exit(OC.main(FOLDER, ORACLE, CASES, PROBES))
