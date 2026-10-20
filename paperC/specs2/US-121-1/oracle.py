#!/usr/bin/env python3
"""Oracle for sample US-121-1 (Paper C, second coder, paperC/specs2/US-121-1).

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

# ===== part: us_121_1.py =====
# ---------------------------------------------------------------------------
# US-121-1: Section121SinglePerson.requirements_met
# ---------------------------------------------------------------------------
# Period lists, sale on 2021-01-01, so the 5-year mark is 2016-01-01. The
# window-day count is what aggregate_periods_from_last_five_years returns.
PERIOD_LISTS = [
    ("none", []),
    ("one_inside_window_over_730d", [FOUR_YEARS_RECENT]),                 # 1461 d
    ("one_inside_window_730d", [("2018-01-02", "2020-01-02")]),           # 730 d
    ("one_inside_window_under_730d", [ONE_YEAR_RECENT]),                  # 365 d
    ("one_across_5y_mark_over_730d", [("2010-01-01", "2019-01-01")]),     # 1095 d
    ("one_across_5y_mark_730d", [("2010-01-01", "2018-01-01")]),          # 730 d
    ("one_across_5y_mark_under_730d", [TWO_YEARS_MIDDLE]),                # 366 d
    ("one_ended_before_5y_mark", [("2005-01-01", "2015-06-01")]),         # 0 d
    ("two_total_730d_or_more", [TWO_YEARS_MIDDLE, ONE_YEAR_RECENT]),      # 366 + 365 = 731 d
    ("two_total_under_730d", [("2015-01-01", "2016-06-01"), ONE_YEAR_RECENT]),  # 151 + 365 = 516 d
]
OTHER_SALES = [("none", None), ("under_2_years_before", "2020-01-01"),
               ("exactly_2_years_before", "2019-01-01"), ("over_2_years_before", "2018-06-01")]


def _fmt(ps):
    return "[" + "; ".join("%s..%s" % p for p in ps) + "]"


_LIST_SRC = ("us_tax_code/section_121.catala_en:205-247 (aggregate_periods_from_last_five_years: three branches on "
             "begin + 5 year and end + 5 year against the sale date; requirement >= 730 day)")
SPEC = {
    "id": "US-121-1",
    "title": "US IRC section 121(a): Section121SinglePerson.requirements_met",
    "source": {"repository": "https://github.com/CatalaLang/catala-examples",
               "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
               "entry_point": "Us_tax_code.Section121SinglePerson (output requirements_met)",
               "files": ["us_tax_code/us_tax_code.catala_en", "us_tax_code/preamble.catala_en",
                         "us_tax_code/section_121.catala_en", "us_tax_code/tests/test_section_121.catala_en"]},
    "attributes": [
        {"name": "property_ownage", "kind": "enum", "values": [l for l, _ in PERIOD_LISTS],
         "representative": {l: _fmt(p) for l, p in PERIOD_LISTS}, "source": _LIST_SRC},
        {"name": "property_usage_as_principal_residence", "kind": "enum", "values": [l for l, _ in PERIOD_LISTS],
         "representative": {l: _fmt(p) for l, p in PERIOD_LISTS}, "source": _LIST_SRC},
        {"name": "other_section_121a_sale", "kind": "interval", "values": [l for l, _ in OTHER_SALES],
         "representative": {l: ("NoOtherSaleWhereSection121aApplied" if d is None else
                                "MostRecentSaleWhereSection121aApplied, sold " + d) for l, d in OTHER_SALES},
         "source": "us_tax_code/section_121.catala_en:369-383 (b)(3): date_of_sale_or_exchange - other_sale.date_of_sale_or_exchange <= 2 year"},
    ],
    "output": {"name": "requirements_met", "values": ["met", "not_met"],
               "source": "us_tax_code/section_121.catala_en:224-240"},
    "exclusions": [],
    "fixed_inputs": {
        "date_of_sale_or_exchange": {"value": SALE_DATE, "why": "date of every official test (Data, test_section_121.catala_en:19)"},
        "gain_from_sale_or_exchange_of_property": {"value": "$350,000", "why": "official test value (Data, line 21); requirements_met does not read it"},
    },
    "notes": "Every list with a MostRecentSaleWhereSection121aApplied value makes the scope raise a Catala DateError (days compared with years at section_121.catala_en:376), in the interpreter and in Python; those rows are REJECTED although requirements_met itself does not read (b)(3).",
}


def build_inputs(row):
    return (dict(PERIOD_LISTS)[row["property_ownage"]],
            dict(PERIOD_LISTS)[row["property_usage_as_principal_residence"]],
            dict(OTHER_SALES)[row["other_section_121a_sale"]])


def run_encoding(inputs):
    own, use, other = inputs
    return "met" if bool(single_person(own, use, other).requirements_met) else "not_met"


def _official(use):
    return lambda: run_encoding(([FOUR_YEARS_RECENT], use, None))


OFFICIAL_CASES = [
    {"case_id": "test_section_121.catala_en:Test1",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "one_inside_window_over_730d", "other_section_121a_sale": "none"},
     "expected": "met", "original": _official([FOUR_YEARS_RECENT])},
    {"case_id": "test_section_121.catala_en:Test2",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "one_inside_window_under_730d", "other_section_121a_sale": "none"},
     "expected": "not_met", "original": _official([ONE_YEAR_RECENT])},
    {"case_id": "test_section_121.catala_en:Test3",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "one_across_5y_mark_under_730d", "other_section_121a_sale": "none"},
     "expected": "not_met", "original": _official([TWO_YEARS_MIDDLE])},
    {"case_id": "test_section_121.catala_en:Test4",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "two_total_730d_or_more", "other_section_121a_sale": "none"},
     "expected": "met", "original": _official([TWO_YEARS_MIDDLE, ONE_YEAR_RECENT])},
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
