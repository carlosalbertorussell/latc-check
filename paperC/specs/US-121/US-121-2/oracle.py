#!/usr/bin/env python3
"""Oracle for US-121-2: section 121 exclusion of gain on a single or joint return
(scope Section121TwoPersons, output income_excluded_from_gross_income as a band).

Holds the table definition (spec.json is written from it with --write-spec), evaluates
rows through the Catala 1.3.0 Python build in paperC/catala_more/, and maps the
official tests onto rows.

  python oracle.py --check-official | --enumerate | --write-official | --check-bands | --write-spec
"""

import copy
import itertools
import os
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(FOLDER, "..", "..", "..", "catala_more")))

import oracle_common as OC  # noqa: E402
import run_official_tests_us121 as R  # noqa: E402
import us121_inputs as U  # noqa: E402
from catala_runtime import Money  # noqa: E402

S121 = "us_tax_code/section_121.catala_en"
TESTS = "us_tax_code/tests/test_section_121.catala_en"
SALE = R.DATA["date_of_sale_or_exchange"]     # |2021-01-01|
RETURN_DATE = R.DATA["return_date"]           # |2021-01-01|
DEATH = "2020-06-01"                          # date_of_spouse_death for SingleReturnSurvivingSpouse


def periods_literal(pairs):
    return "[" + "; ".join(f"Period {{begin: |{b}|, end: |{e}|}}" for b, e in pairs) + "]"


def days_band(pairs):
    return "ge_730_days" if U.aggregate_days_last_five_years(SALE, pairs) >= 730 else "lt_730_days"


RETURN_TYPE = [
    ("single", "single", "SingleReturn content (person 1)"),
    ("joint", "joint", "JointReturn content JointReturn {person1: (person 1), person2: (person 2)}"),
    ("surviving_spouse", "surviving_spouse",
     f"SingleReturnSurvivingSpouse content DeadSpouseInfo {{return: (person 1), date_of_spouse_death: |{DEATH}|, "
     "death_spouse_info_at_time_of_death: (person 2)}"),
]
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
GAIN = [
    ("gt_0_lt_250000", "200000", "$200,000"),
    ("250000_to_lt_500000", "350000", "$350,000"),
    ("ge_500000", "600000", "$600,000"),
]


def setter(*path):
    def apply(raw, value):
        target = raw
        for k in path[:-1]:
            target = target[k]
        target[path[-1]] = value
    return apply


BASE = {"return_type": None, "gain": None,
        "p1": {"ownage": None, "usage": None, "previous_sale": None},
        "p2": {"ownage": None, "usage": None, "previous_sale": None}}


def baseline():
    return copy.deepcopy(BASE)


def return_type_value(raw):
    p1 = U.personal_data(raw["p1"]["ownage"], raw["p1"]["usage"], raw["p1"]["previous_sale"])
    p2 = U.personal_data(raw["p2"]["ownage"], raw["p2"]["usage"], raw["p2"]["previous_sale"])
    kind = raw["return_type"]
    if kind == "single":
        return U.single_return(p1)
    if kind == "joint":
        return U.joint_return(p1, p2)
    return U.surviving_spouse_return(p1, DEATH, p2)


def run(raw):
    out = U.two_persons(return_type_value(raw), SALE, RETURN_DATE, raw["gain"])
    uncapped = out.income_excluded_from_gross_income_uncapped
    excluded = out.income_excluded_from_gross_income
    # The limitation the scope applies: $500,000 under section_121_b_2_A_condition
    # (section_121.catala_en:309-313), otherwise person 1's gain_cap of $250,000 (248).
    cap = Money("500000") if bool(out.section_121_b_2_A_condition) else out.gain_cap_person_1
    if not bool(excluded == (cap if uncapped >= cap else uncapped)):
        raise AssertionError("unexpected output of Section121TwoPersons")
    if bool(uncapped == Money("0")):
        return "no_exclusion"
    if uncapped >= cap:
        return {Money("250000"): "limited_to_250000", Money("500000"): "limited_to_500000"}[cap]
    return "entire_gain"


ATTRIBUTES = [
    OC.Attribute(
        "return_type", "enum", RETURN_TYPE,
        "Section121TwoPersons.return_type, enumeration ReturnType (" + S121 + ":65-68, 80); person1 and person2 "
        "are taken from it at " + S121 + ":95-105; 26 U.S.C. 121(b)(2) (joint returns) and (b)(4) (surviving "
        "spouses)",
        setter("return_type")),
    OC.Attribute("person1_ownership_days_in_5_years", "interval", PERIOD_LABELS,
                 "PersonalData.property_ownage of person 1 (" + S121 + ":50-54), aggregated and compared with 730 "
                 "days by Section121SinglePerson (" + S121 + ":179-198); 26 U.S.C. 121(a)",
                 setter("p1", "ownage")),
    OC.Attribute("person1_use_days_in_5_years", "interval", PERIOD_LABELS,
                 "PersonalData.property_usage_as_principal_residence of person 1 (" + S121 + ":50-54), compared "
                 "with 730 days (" + S121 + ":200-205); 26 U.S.C. 121(a)",
                 setter("p1", "usage")),
    OC.Attribute("person1_other_section_121a_sale", "enum", OTHER_SALE,
                 "PersonalData.other_section_121a_sale of person 1 (" + S121 + ":54), read by "
                 "section_121_b_3_applies (" + S121 + ":371-383); 26 U.S.C. 121(b)(3). within_2_years: 1 day to "
                 "2 years before the date of sale; more_than_2_years: more than 2 years before",
                 setter("p1", "previous_sale")),
    OC.Attribute("person2_ownership_days_in_5_years", "interval", PERIOD_LABELS,
                 "PersonalData.property_ownage of person 2 (" + S121 + ":50-57), as for person 1",
                 setter("p2", "ownage")),
    OC.Attribute("person2_use_days_in_5_years", "interval", PERIOD_LABELS,
                 "PersonalData.property_usage_as_principal_residence of person 2, as for person 1",
                 setter("p2", "usage")),
    OC.Attribute("person2_other_section_121a_sale", "enum", OTHER_SALE,
                 "PersonalData.other_section_121a_sale of person 2, as for person 1",
                 setter("p2", "previous_sale")),
    OC.Attribute("gain", "interval", GAIN,
                 "Section121TwoPersons.gain_from_sale_or_exchange_of_property (" + S121 + ":83); compared with the "
                 "$250,000 and $500,000 limitations (" + S121 + ":236-254, 309-313); 26 U.S.C. 121(b)(1) and "
                 "(b)(2)(A)",
                 setter("gain")),
]

P2_PAIRS = [("person1_ownership_days_in_5_years", "person2_ownership_days_in_5_years", PERIOD_LABELS),
            ("person1_use_days_in_5_years", "person2_use_days_in_5_years", PERIOD_LABELS),
            ("person1_other_section_121a_sale", "person2_other_section_121a_sale", OTHER_SALE)]


def person2_differs_predicate():
    terms = []
    for a1, a2, labels in P2_PAIRS:
        for (l1, _, _), (l2, _, _) in itertools.permutations(labels, 2):
            terms.append(f"({a1} == '{l1}' and {a2} == '{l2}')")
    return "return_type in ('single', 'surviving_spouse') and (" + " or ".join(terms) + ")"


META = {
    "id": "US-121-2",
    "title": "US IRC section 121: amount of gain excluded on a single or joint return",
    "source": {
        "repository": "https://github.com/CatalaLang/catala-examples",
        "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
        "entry_point": "Us_tax_code scope Section121TwoPersons, output income_excluded_from_gross_income "
                       "(Python: generated.Us_tax_code.section121_two_persons, Catala 1.3.0)",
        "files": [S121, "us_tax_code/us_tax_code.catala_en", TESTS],
    },
    "output": {
        "name": "excluded_gain",
        "values": ["no_exclusion", "entire_gain", "limited_to_250000", "limited_to_500000"],
        "source": "Section121TwoPersons.income_excluded_from_gross_income (" + S121 + ":85, 250-254) with "
                  "income_excluded_from_gross_income_uncapped (" + S121 + ":84, 219-224). Labels follow the cases "
                  "of 26 U.S.C. 121: no_exclusion when (a) is not met or (b)(3) applies (uncapped amount $0); "
                  "limited_to_250000 when the gain reaches the (b)(1) limitation; limited_to_500000 when it "
                  "reaches the (b)(2)(A) limitation; entire_gain when the whole gain is excluded below the "
                  "applicable limitation",
    },
    "exclusions": [
        {
            "id": "person2_differs_on_single_return",
            "description": "On a single return, and on a surviving spouse's return in this scope, there is one "
                           "taxpayer: the scope takes person 2 to be person 1 (section_121.catala_en:101-105), so a "
                           "row whose person-2 labels differ from the person-1 labels describes no return",
            "predicate": person2_differs_predicate(),
            "source": S121 + ":95-105 (person1 and person2 both read the single PersonalData of SingleReturn and "
                      "SingleReturnSurvivingSpouse); 26 U.S.C. 121(b)(1)",
        },
    ],
    "fixed_inputs": {
        "date_of_sale_or_exchange": {"value": "|2021-01-01|", "why": "Data scope of the official tests (" + TESTS + ":19)"},
        "return_date": {"value": "|2021-01-01|", "why": "Data scope of the official tests (" + TESTS + ":20); not read by any rule"},
        "DeadSpouseInfo.date_of_spouse_death": {"value": f"|{DEATH}|", "why": "needed to build SingleReturnSurvivingSpouse; Section121TwoPersons does not read it (only Section121TwoPasses does, " + S121 + ":398-431)"},
        "person1, person2, gain_cap (context variables)": {"value": "not redefined (the scope's own definitions)", "why": "the official tests do not redefine them"},
    },
    "notes": "Sub-table 2 of 2 of US-121. Section121TwoPersons is the scope the official tests use; it has no "
             "(b)(2)(B) or (b)(4) rule (those are in Section121TwoPasses, whose PeriodMerge is a placeholder that "
             "returns [] and which no official test exercises), so a surviving spouse is treated like a single "
             "filer and a joint return that misses (b)(2)(A) gets the $250,000 limitation. REJECTED rows: any "
             "row with another section 121(a) sale for a person raises the DateError of "
             + S121 + ":376 (US-121-1 notes).",
}

SPEC = OC.build_spec(META, ATTRIBUTES)
ORACLE = OC.Oracle(SPEC, ATTRIBUTES, baseline, run, (U.CatalaError,))


def evaluate(row: dict[str, str]) -> str:
    return ORACLE.evaluate(row)


# ------------------------------------------------------------- official tests

def gain_band(amount):
    from fractions import Fraction
    g = Fraction(amount)
    if g <= 0:
        return None
    return "gt_0_lt_250000" if g < 250000 else ("250000_to_lt_500000" if g < 500000 else "ge_500000")


def person_labels(prefix, person):
    return {
        f"{prefix}_ownership_days_in_5_years": days_band(person["ownage"]),
        f"{prefix}_use_days_in_5_years": days_band(person["usage"]),
        f"{prefix}_other_section_121a_sale": "none",
    }


def case(name, fn, return_type, p1, p2, expected):
    def direct():
        results = fn()
        return all(ok for _, ok in results), "; ".join(label for label, _ in results)
    row = {"return_type": return_type}
    row.update(person_labels("person1", p1))
    # On a single return the scope's person 2 is person 1 (section_121.catala_en:101-105).
    row.update(person_labels("person2", p2 if return_type == "joint" else p1))
    row["gain"] = gain_band(R.DATA["gain"])
    row = {a.name: row[a.name] for a in ATTRIBUTES}
    return {"case_id": f"test_section_121/{name}", "direct": direct, "row": row, "expected": expected,
            "reason": None}


def single_person_case(name, *_):
    def direct():
        results = R.make_single_person_test(*_)()
        return all(ok for _, ok in results), "; ".join(label for label, _ in results)
    return {"case_id": f"test_section_121/{name}", "direct": direct, "row": None, "expected": None,
            "reason": "tests scope Section121SinglePerson and asserts requirements_met (US-121-1); this table is "
                      "Section121TwoPersons.income_excluded_from_gross_income"}


CASES = [single_person_case(n, o, u, e) for n, o, u, e in R.SINGLE_PERSON_TESTS]
# Test5: SingleReturn person_ok_1, asserts $250,000 = the (b)(1) limitation reached by a $350,000 gain.
CASES.append(case("Test5", R.test5, "single", R.PERSON_OK_1, R.PERSON_OK_1, "limited_to_250000"))
# Test6: JointReturn person_ok_1 / person_ok_2, asserts $350,000 = the whole gain, below the (b)(2)(A) limitation.
CASES.append(case("Test6", R.test6, "joint", R.PERSON_OK_1, R.PERSON_OK_2, "entire_gain"))

# ---------------------------------------------------------------- band probes

PERIOD_PROBES = {
    "lt_730_days": [[], [("2019-01-03", "2021-01-01")], [("2019-01-01", "2020-01-01")], [("2015-01-01", "2017-01-02")]],
    "ge_730_days": [[("2019-01-02", "2021-01-01")], [("2015-01-01", "2017-01-02"), ("2019-01-01", "2020-01-01")],
                    [("2010-01-01", "2021-01-01")]],
}
for lab, alts in PERIOD_PROBES.items():
    for pairs in alts:
        assert days_band(pairs) == lab, (lab, pairs)
SALE_PROBES = {"within_2_years": ["2019-01-01", "2020-12-31"], "more_than_2_years": ["2018-12-31", "2010-01-01"]}
PROBES = {
    "person1_ownership_days_in_5_years": PERIOD_PROBES,
    "person1_use_days_in_5_years": PERIOD_PROBES,
    "person1_other_section_121a_sale": SALE_PROBES,
    "person2_ownership_days_in_5_years": PERIOD_PROBES,
    "person2_use_days_in_5_years": PERIOD_PROBES,
    "person2_other_section_121a_sale": SALE_PROBES,
    "gain": {
        "gt_0_lt_250000": ["0.01", "1000", "249999.99"],
        "250000_to_lt_500000": ["250000", "250000.01", "499999.99"],
        "ge_500000": ["500000", "500000.01", "10000000"],
    },
}

if __name__ == "__main__":
    sys.exit(OC.main(FOLDER, ORACLE, CASES, PROBES))
