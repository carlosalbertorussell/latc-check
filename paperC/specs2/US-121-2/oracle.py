#!/usr/bin/env python3
"""Oracle for sample US-121-2 (Paper C, second coder, paperC/specs2/US-121-2).

Usage:
  python3 oracle.py --enumerate        # writes ground_truth.csv
  python3 oracle.py --check-official   # official tests: encoding vs oracle
  python3 oracle.py --write-spec --write-official   # regenerate spec.json, official_examples.csv

Assembled by paperC/catala_code2/make_oracles.py from paperC/catala_code2/oracle_parts/.
Requires Python >= 3.12 (Catala 1.3.0 runtime).
"""

# ===== part: us_common.py =====
# ---------------------------------------------------------------------------
# US-121 common part (identical in every US-121-* oracle): imports the Python
# that Catala 1.3.0 generated from catala-examples 2694b17
# (us_tax_code/us_tax_code.catala_en) and the official test data
# (us_tax_code/tests/test_section_121.catala_en, scope Data, lines 6-62).
# ---------------------------------------------------------------------------
import os as _os
import sys as _sys

_GEN = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "catala_code2"))
_sys.path.insert(0, _os.path.join(_GEN, "runtime"))
_sys.path.insert(0, _GEN)

from catala_runtime import Array, Date, Money, Option, Unit  # noqa: E402
from generated import Us_tax_code as us  # noqa: E402

D = lambda s: Date(*map(int, s.split("-")))  # noqa: E731

SALE_DATE = "2021-01-01"      # Data.date_of_sale_or_exchange
RETURN_DATE = "2021-01-01"    # Data.return_date
OFFICIAL_GAIN = "350000"      # Data.gain_from_sale_or_exchange_of_property

# Periods of the official test data (Data, lines 22-36).
FOUR_YEARS_RECENT = ("2017-01-01", "2021-01-01")
ONE_YEAR_RECENT = ("2019-01-01", "2020-01-01")
TWO_YEARS_MIDDLE = ("2015-01-01", "2017-01-02")


def period(p):
    return us.Period(begin=D(p[0]), end=D(p[1]))


def periods(ps):
    return Array([period(p) for p in ps])


def other_sale(date_or_none):
    if date_or_none is None:
        return us.OtherSection121aSale(us.OtherSection121aSale.Code.NoOtherSaleWhereSection121aApplied, Unit())
    return us.OtherSection121aSale(us.OtherSection121aSale.Code.MostRecentSaleWhereSection121aApplied,
                                   us.PreviousSaleWhereSection121aApplied(date_of_sale_or_exchange=D(date_or_none)))


def personal_data(own, use, other=None):
    return us.PersonalData(property_ownage=periods(own), property_usage_as_principal_residence=periods(use),
                           other_section_121a_sale=other_sale(other))


def single_person(own, use, other=None, gain=OFFICIAL_GAIN, sale=SALE_DATE):
    return us.section121_single_person(us.Section121SinglePersonIn(
        date_of_sale_or_exchange_in=D(sale), property_ownage_in=periods(own),
        property_usage_as_principal_residence_in=periods(use), gain_cap_in=Option(None),
        gain_from_sale_or_exchange_of_property_in=Money(gain + ".00"),
        section_121_b_3_applies_in=Option(None), other_section_121a_sale_in=other_sale(other)))


def two_persons(return_type, gain=OFFICIAL_GAIN, sale=SALE_DATE):
    return us.section121_two_persons(us.Section121TwoPersonsIn(
        person1_in=Option(None), person2_in=Option(None), gain_cap_in=Option(None),
        return_type_in=return_type, return_date_in=D(RETURN_DATE), date_of_sale_or_exchange_in=D(sale),
        gain_from_sale_or_exchange_of_property_in=Money(gain + ".00")))


def single_return(pd):
    return us.ReturnType(us.ReturnType.Code.SingleReturn, pd)


def joint_return(pd1, pd2):
    return us.ReturnType(us.ReturnType.Code.JointReturn, us.JointReturn(person1=pd1, person2=pd2))


def surviving_spouse_return(pd, death, dead_pd):
    return us.ReturnType(us.ReturnType.Code.SingleReturnSurvivingSpouse, us.DeadSpouseInfo(
        return__1=pd, date_of_spouse_death=D(death), death_spouse_info_at_time_of_death=dead_pd))


# Official PersonalData values (Data, lines 37-62).
PERSON_OK_1 = ([FOUR_YEARS_RECENT], [FOUR_YEARS_RECENT])
PERSON_OK_2 = ([FOUR_YEARS_RECENT], [TWO_YEARS_MIDDLE, ONE_YEAR_RECENT])

# ===== part: us_121_2.py =====
# ---------------------------------------------------------------------------
# US-121-2: Section121TwoPersons.income_excluded_from_gross_income
# ---------------------------------------------------------------------------
AGG = [("under_730d", [ONE_YEAR_RECENT]), ("730d_or_more", [FOUR_YEARS_RECENT])]
OTHER_SALES = [("none", None), ("under_2_years_before", "2020-01-01"),
               ("exactly_2_years_before", "2019-01-01"), ("over_2_years_before", "2018-06-01")]
NA = "not_applicable"
GAINS = [("under_250000", "100000"), ("250000_to_500000", "350000"), ("over_500000", "600000")]
RETURNS = ["single_return", "joint_return", "surviving_spouse_return"]
SPOUSE_DEATH = "2020-06-01"


def _fmt(ps):
    return "[" + "; ".join("%s..%s" % p for p in ps) + "]"


_AGG_SRC = ("us_tax_code/section_121.catala_en:205-247 (aggregate over the last five years >= 730 day); "
            "the class holds every list whose window-day total is on that side of 730")
_OS_SRC = "us_tax_code/section_121.catala_en:369-383 ((b)(3), <= 2 year)"


def _person_attrs(prefix, na):
    extra = [NA] if na else []
    rep_na = {NA: "absent: the return carries one PersonalData"} if na else {}
    return [
        {"name": prefix + "_property_ownage", "kind": "enum", "values": [l for l, _ in AGG] + extra,
         "representative": dict({l: _fmt(p) for l, p in AGG}, **rep_na), "source": _AGG_SRC},
        {"name": prefix + "_property_usage_as_principal_residence", "kind": "enum", "values": [l for l, _ in AGG] + extra,
         "representative": dict({l: _fmt(p) for l, p in AGG}, **rep_na), "source": _AGG_SRC},
        {"name": prefix + "_other_section_121a_sale", "kind": "interval", "values": [l for l, _ in OTHER_SALES] + extra,
         "representative": dict({l: ("NoOtherSaleWhereSection121aApplied" if d is None else
                                     "MostRecentSaleWhereSection121aApplied, sold " + d) for l, d in OTHER_SALES}, **rep_na),
         "source": _OS_SRC},
    ]


SPEC = {
    "id": "US-121-2",
    "title": "US IRC section 121(a)-(b)(3): Section121TwoPersons.income_excluded_from_gross_income",
    "source": {"repository": "https://github.com/CatalaLang/catala-examples",
               "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
               "entry_point": "Us_tax_code.Section121TwoPersons (output income_excluded_from_gross_income)",
               "files": ["us_tax_code/us_tax_code.catala_en", "us_tax_code/preamble.catala_en",
                         "us_tax_code/section_121.catala_en", "us_tax_code/tests/test_section_121.catala_en"]},
    "attributes": [
        {"name": "return_type", "kind": "enum", "values": RETURNS,
         "representative": {"single_return": "ReturnType.SingleReturn contenu person1",
                            "joint_return": "ReturnType.JointReturn contenu {person1; person2}",
                            "surviving_spouse_return": "ReturnType.SingleReturnSurvivingSpouse contenu {return: person1, date_of_spouse_death: %s, death_spouse_info_at_time_of_death: person_ok_1 of Data}" % SPOUSE_DEATH},
         "source": "us_tax_code/section_121.catala_en:66-74, 96-108"},
    ] + _person_attrs("person1", False) + _person_attrs("person2", True) + [
        {"name": "gain_from_sale_or_exchange_of_property", "kind": "interval", "values": [l for l, _ in GAINS],
         "representative": {l: "$" + g for l, g in GAINS},
         "source": "us_tax_code/section_121.catala_en:254-282 ((b)(1) cap $250,000 compared with >=), 300-323 ((b)(2)(A) $500,000)"},
    ],
    "output": {"name": "income_excluded_from_gross_income",
               "values": ["zero", "full_gain", "capped_at_250000", "capped_at_500000"],
               "source": "us_tax_code/section_121.catala_en:241-246, 276-282; label from the amount: 0 -> zero, = gain -> full_gain, $250,000 -> capped_at_250000, $500,000 -> capped_at_500000"},
    "exclusions": [
        {"id": "person2_iff_joint_return",
         "description": "a second PersonalData exists exactly when the return is a joint return",
         "predicate": "(return_type == 'joint_return') == (person2_property_ownage == 'not_applicable' or person2_property_usage_as_principal_residence == 'not_applicable' or person2_other_section_121a_sale == 'not_applicable')",
         "source": "us_tax_code/section_121.catala_en:66-74 (ReturnType: only JointReturn carries two PersonalData)"},
    ],
    "fixed_inputs": {
        "date_of_sale_or_exchange": {"value": SALE_DATE, "why": "official test value (Data, line 19)"},
        "return_date": {"value": RETURN_DATE, "why": "official test value (Data, line 20); not read by the scope's outputs"},
        "date_of_spouse_death": {"value": SPOUSE_DEATH, "why": "needed to build SingleReturnSurvivingSpouse; Section121TwoPersons reads only its return field"},
        "death_spouse_info_at_time_of_death": {"value": "person_ok_1 of Data", "why": "needed to build SingleReturnSurvivingSpouse; not read by Section121TwoPersons"},
    },
    "notes": "Section121TwoPersons alone, as the official tests call it; the joint-return cap sum of (b)(2)(B) and the surviving-spouse rule of (b)(4) live in Section121TwoPasses and are outside this table. For a single or surviving-spouse return the scope uses the same PersonalData for both persons. Any MostRecentSaleWhereSection121aApplied raises a DateError (REJECTED), as in US-121-1.",
}


def _pd(row, prefix):
    return personal_data(dict(AGG)[row[prefix + "_property_ownage"]],
                         dict(AGG)[row[prefix + "_property_usage_as_principal_residence"]],
                         dict(OTHER_SALES)[row[prefix + "_other_section_121a_sale"]])


def build_inputs(row):
    p1 = _pd(row, "person1")
    rt = row["return_type"]
    if rt == "single_return":
        ret = single_return(p1)
    elif rt == "joint_return":
        ret = joint_return(p1, _pd(row, "person2"))
    else:
        ret = surviving_spouse_return(p1, SPOUSE_DEATH, personal_data(*PERSON_OK_1))
    return ret, dict(GAINS)[row["gain_from_sale_or_exchange_of_property"]]


def label_amount(amount, gain):
    cents = int(amount)
    if cents == 0:
        return "zero"
    if cents == int(Money(gain + ".00")):
        return "full_gain"
    if cents == int(Money("250000.00")):
        return "capped_at_250000"
    if cents == int(Money("500000.00")):
        return "capped_at_500000"
    raise ValueError("unexpected amount %s" % amount)


def run_encoding(inputs):
    ret, gain = inputs
    return label_amount(two_persons(ret, gain).income_excluded_from_gross_income, gain)


OFFICIAL_CASES = [
    {"case_id": "test_section_121.catala_en:Test5",
     "row": {"return_type": "single_return", "person1_property_ownage": "730d_or_more",
             "person1_property_usage_as_principal_residence": "730d_or_more", "person1_other_section_121a_sale": "none",
             "person2_property_ownage": NA, "person2_property_usage_as_principal_residence": NA,
             "person2_other_section_121a_sale": NA, "gain_from_sale_or_exchange_of_property": "250000_to_500000"},
     "expected": "capped_at_250000",
     "original": lambda: run_encoding((single_return(personal_data(*PERSON_OK_1)), OFFICIAL_GAIN))},
    {"case_id": "test_section_121.catala_en:Test6",
     "row": {"return_type": "joint_return", "person1_property_ownage": "730d_or_more",
             "person1_property_usage_as_principal_residence": "730d_or_more", "person1_other_section_121a_sale": "none",
             "person2_property_ownage": "730d_or_more", "person2_property_usage_as_principal_residence": "730d_or_more",
             "person2_other_section_121a_sale": "none", "gain_from_sale_or_exchange_of_property": "250000_to_500000"},
     "expected": "full_gain",
     "original": lambda: run_encoding((joint_return(personal_data(*PERSON_OK_1), personal_data(*PERSON_OK_2)), OFFICIAL_GAIN))},
]

# ===== part: oracle_template.py =====
# ---------------------------------------------------------------------------
# Generic part shared (by copy) by every oracle.py of paperC/specs2/.
# The text between the BEGIN/END GENERIC markers is identical in every oracle.
# ---------------------------------------------------------------------------
# BEGIN GENERIC
import csv
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "catala_code2"))


def _attr_names():
    return [a["name"] for a in SPEC["attributes"]]


def excluded(row):
    for ex in SPEC["exclusions"]:
        if eval(ex["predicate"], {"__builtins__": {}}, dict(row)):
            return True
    return False


def evaluate(row):
    """Label of the decision for one row of declared labels."""
    if excluded(row):
        return "EXCLUDED"
    try:
        return run_encoding(build_inputs(row))
    except Exception as exc:  # error or assertion failure raised by the encoding
        LAST_ERRORS[tuple(row[a] for a in _attr_names())] = _describe(exc)
        return "REJECTED"


LAST_ERRORS = {}


def _describe(exc):
    import re
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(exc)).replace("\n", " ").strip()
    return "%s: %s" % (type(exc).__name__, msg)


def enumerate_rows():
    names = _attr_names()
    domains = [a["values"] for a in SPEC["attributes"]]
    for combo in itertools.product(*domains):
        yield dict(zip(names, combo))


def write_ground_truth(path):
    names = _attr_names()
    counts = {}
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(names + ["output"])
        for row in enumerate_rows():
            out = evaluate(row)
            counts[out] = counts.get(out, 0) + 1
            w.writerow([row[a] for a in names] + [out])
    return counts


def write_spec(path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(SPEC, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_official(path):
    names = _attr_names()
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id"] + names + ["output"])
        for case in OFFICIAL_CASES:
            w.writerow([case["case_id"]] + [case["row"][a] for a in names] + [case["expected"]])


def check_official():
    """Re-run each mappable official test through the encoding (original inputs)
    and through the oracle (mapped labels); both must give the asserted label."""
    ok_enc = ok_orc = 0
    for case in OFFICIAL_CASES:
        enc = case["original"]()
        orc = evaluate(case["row"])
        e_ok = enc == case["expected"]
        o_ok = orc == case["expected"]
        ok_enc += e_ok
        ok_orc += o_ok
        print("%s  %s  encoding=%s oracle=%s expected=%s" % (
            "PASS" if (e_ok and o_ok) else "FAIL", case["case_id"], enc, orc, case["expected"]))
    n = len(OFFICIAL_CASES)
    print("encoding (original inputs): %d/%d passed" % (ok_enc, n))
    print("oracle (mapped labels):     %d/%d passed" % (ok_orc, n))
    return ok_enc == n and ok_orc == n


def main(argv):
    if "--write-spec" in argv:
        write_spec(os.path.join(HERE, "spec.json"))
    if "--write-official" in argv:
        write_official(os.path.join(HERE, "official_examples.csv"))
    if "--enumerate" in argv:
        counts = write_ground_truth(os.path.join(HERE, "ground_truth.csv"))
        print(json.dumps(counts, sort_keys=True))
        kinds = {}
        for err in LAST_ERRORS.values():
            k = err.split(":")[0]
            kinds[k] = kinds.get(k, 0) + 1
        if kinds:
            print("REJECTED by exception type:", json.dumps(kinds, sort_keys=True))
            for msg in sorted(set(LAST_ERRORS.values())):
                print("  error:", msg[:300])
    if "--check-official" in argv:
        if not check_official():
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
# END GENERIC
