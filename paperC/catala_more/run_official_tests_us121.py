#!/usr/bin/env python3
"""Re-run the official Catala tests of us_tax_code/tests/test_section_121.catala_en through the generated Python.

Source of the tests (CatalaLang/catala-examples, commit 2694b17):
  us_tax_code/tests/test_section_121.catala_en
    Test1..Test4  scope T.Section121SinglePerson, assertion on requirements_met
    Test5, Test6  scope T.Section121TwoPersons, assertion on income_excluded_from_gross_income

The data of scope `Data` (lines 18-62) is reproduced in DATA below. Each test is a
field-by-field translation of the Catala test scope (same inputs, same assertion).
Only the standard library and the bundled runtime are used.

us_tax_code/tests/test_section_132.catala_en tests section 132, which is outside
the scope of this folder and is not re-run here (clerk runs it; see README.md).

Run:  python3 run_official_tests_us121.py     (exit status 0 when every assertion holds)
"""

import sys

import us121_inputs as U
from catala_runtime import Money

# champ `Data`, test_section_121.catala_en lines 18-62
DATA = {
    "date_of_sale_or_exchange": "2021-01-01",
    "return_date": "2021-01-01",
    "gain": "350000",
    "period_four_years_recent": ("2017-01-01", "2021-01-01"),
    "period_one_year_recent": ("2019-01-01", "2020-01-01"),
    "period_two_years_middle": ("2015-01-01", "2017-01-02"),
}
P4, P1, P2 = DATA["period_four_years_recent"], DATA["period_one_year_recent"], DATA["period_two_years_middle"]
PERSON_OK_1 = dict(ownage=[P4], usage=[P4])
PERSON_OK_2 = dict(ownage=[P4], usage=[P2, P1])

# (scope name, ownage, usage, expected requirements_met)
SINGLE_PERSON_TESTS = [
    ("Test1", [P4], [P4], True),
    ("Test2", [P4], [P1], False),
    ("Test3", [P4], [P2], False),
    ("Test4", [P4], [P2, P1], True),
]


def make_single_person_test(ownage, usage, expected):
    def run():
        out = U.single_person(DATA["date_of_sale_or_exchange"], ownage, usage, DATA["gain"])
        label = ("" if expected else "not ") + f"scope121a.requirements_met (got {out.requirements_met})"
        return [(label, bool(out.requirements_met) is expected)]
    return run


def test5():
    rt = U.single_return(U.personal_data(**PERSON_OK_1))
    out = U.two_persons(rt, DATA["date_of_sale_or_exchange"], DATA["return_date"], DATA["gain"])
    got = out.income_excluded_from_gross_income
    return [(f"scope121.income_excluded_from_gross_income = $250,000 (got {got})", bool(got == Money("250000")))]


def test6():
    rt = U.joint_return(U.personal_data(**PERSON_OK_1), U.personal_data(**PERSON_OK_2))
    out = U.two_persons(rt, DATA["date_of_sale_or_exchange"], DATA["return_date"], DATA["gain"])
    got = out.income_excluded_from_gross_income
    return [(f"scope121.income_excluded_from_gross_income = $350,000 (got {got})", bool(got == Money("350000")))]


TESTS = [("test_section_121.catala_en", name, make_single_person_test(o, u, e))
         for name, o, u, e in SINGLE_PERSON_TESTS]
TESTS += [("test_section_121.catala_en", "Test5", test5), ("test_section_121.catala_en", "Test6", test6)]


def main():
    print(f"Python {sys.version.split()[0]}")
    n_pass = n_fail = n_assert = 0
    for fname, scope, fn in TESTS:
        try:
            results, error = fn(), None
        except Exception as exc:  # a Catala runtime error counts as a failure
            results, error = [], f"{type(exc).__name__}: {exc}"
        failed = [label for label, ok in results if not ok]
        n_assert += len(results)
        if error is None and not failed:
            n_pass += 1
            print(f"PASS  {fname}  {scope}  ({len(results)} assertion(s)): {results[0][0]}")
        else:
            n_fail += 1
            print(f"FAIL  {fname}  {scope}")
            if error:
                print(f"      error: {error}")
            for label in failed:
                print(f"      assertion failed: {label}")
    print(f"\n{n_pass} passed, {n_fail} failed, {len(TESTS)} test scopes, {n_assert} assertions checked")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
