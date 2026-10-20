# US-121-1 conversion record

Table: whether one taxpayer meets the ownership and use requirements of 26 U.S.C.
121(a) ("owned and used ... as the taxpayer's principal residence for periods
aggregating 2 years or more" during the 5 years ending on the date of sale), as the
Catala scope `Section121SinglePerson` decides it. Sub-table 1 of 2 of US-121; US-121-2
covers the amount excluded on a single or joint return.

File references are to CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`; `S121` is
`us_tax_code/section_121.catala_en`, `TESTS` is
`us_tax_code/tests/test_section_121.catala_en`.

## 1. Scope and output

* Entry point: scope `Section121SinglePerson` (`S121:31-48`) of module `Us_tax_code`,
  through `paperC/catala_more/generated/Us_tax_code.py`
  (`section121_single_person`, Catala 1.3.0).
* Output: `requirements_met` (`S121:32`, rule `S121:207-209`: ownership and use
  requirements both met). Labels `requirements_met` / `requirements_not_met`. This is
  what the official tests Test1–Test4 assert (`TESTS:79`, `94`, `109`, `124`).

## 2. Attributes

### `ownership_days_in_5_years` and `use_days_in_5_years` (interval, 2 labels each)

The inputs are lists of periods (`property_ownage`, `property_usage_as_principal_residence`,
`S121:36-39`). The scope sums them with `aggregate_periods_from_last_five_years`
(`S121:179-191`) and compares the sum with 730 days (`S121:196-205`, "Regulation
1.121-1(c)(1): 2 years = 730 days"). The labels are the two sides of that comparison:

| Label | Aggregate as computed by the encoding | Representative |
|---|---|---|
| `lt_730_days` | 0 to 729 days | `[Period {begin: \|2020-01-01\|, end: \|2021-01-01\|}]` (366 days) |
| `ge_730_days` | 730 days or more | `[Period {begin: \|2017-01-01\|, end: \|2021-01-01\|}]` (1,461 days; the tests' `period_four_years_recent`) |

The aggregation (`S121:179-191`): a period whose begin is at most 5 years before the
sale counts in full (end − begin); one that ended 5 years or more before the sale
counts 0; one straddling the 5-year mark counts (end + 5 years) − sale.
`paperC/catala_more/us121_inputs.aggregate_days_last_five_years` recomputes this with
`datetime`; the oracle uses it to place a test's periods in a label and asserts that
the label agrees with the scope's own `requirements_ownership_met` /
`requirements_usage_met`.

### `other_section_121a_sale` (enum, 3 labels)

`OtherSection121aSale` (`S121:26-29`): `NoOtherSaleWhereSection121aApplied`, or
`MostRecentSaleWhereSection121aApplied` carrying the date of that earlier sale; read by
`section_121_b_3_applies` (`S121:371-383`, §121(b)(3): one exclusion every 2 years).

| Label | Meaning | Representative |
|---|---|---|
| `none` | no earlier §121(a) sale | `NoOtherSaleWhereSection121aApplied` |
| `within_2_years` | earlier sale 1 day to 2 years before the date of sale | earlier sale \|2020-01-01\| |
| `more_than_2_years` | earlier sale more than 2 years before | earlier sale \|2018-06-01\| |

An earlier sale **on the date of sale itself** belongs to none of the labels: the band
check found that this single date behaves differently (section 6).

## 3. Fixed inputs

* `date_of_sale_or_exchange` \|2021-01-01\| and `gain_from_sale_or_exchange_of_property`
  $350,000: the `Data` scope of the official tests (`TESTS:19`, `21`).
  `requirements_met` does not read the gain.
* Context variables `gain_cap` and `section_121_b_3_applies` keep the scope's own
  definitions, as in the tests.

## 4. Exclusions

None. Every combination of the three attributes describes a possible taxpayer.

## 5. REJECTED rows (8)

Every row with `within_2_years` or `more_than_2_years` raises a Catala `DateError` at
`S121:376.9-376.81`: `date_of_sale_or_exchange - other_sale.date_of_sale_or_exchange
<= 2 year` subtracts two dates (a number of days) and compares the result with a
number of years, which the Catala runtime refuses ("ambiguous comparison between
durations in different units"). Catala computes every output of the scope, so
`requirements_met` is not returned either. The Catala interpreter gives the same error
(`paperC/catala_more/probes/probe_b3_output.txt`, and the interpreter cross-check).

## 6. Band check (`python oracle.py --check-bands`)

Period lists with aggregates of 0 (empty list, and a period that ended more than 5
years before the sale), 365, 366 and 729 days for `lt_730_days`; 730, 731 (Test4's
two periods), 1,826 and 1,827 days for `ge_730_days`; earlier sales on 2019-01-01,
2019-01-02 and 2020-12-31 for `within_2_years` and on 2018-12-31 and 2010-01-01 for
`more_than_2_years`: 128 evaluations, all giving the output of the label's
representative.

A first version of the check also tried an earlier sale on 2021-01-01, the date of
sale itself. The difference is then 0 days, which Catala can compare with 2 years, so
no error is raised and `requirements_met` is returned: that date was taken out of
`within_2_years` (section 2).

## 7. Official tests

| Test | Mapped | Row | Output |
|---|---|---|---|
| `test_section_121/Test1` | yes | `ge_730_days, ge_730_days, none` | `requirements_met` |
| `test_section_121/Test2` | yes | `ge_730_days, lt_730_days, none` (use 2019-01-01 to 2020-01-01, 365 days) | `requirements_not_met` |
| `test_section_121/Test3` | yes | `ge_730_days, lt_730_days, none` (use 2015-01-01 to 2017-01-02, 366 days counted) | `requirements_not_met` |
| `test_section_121/Test4` | yes | `ge_730_days, ge_730_days, none` (use: the two periods above, 731 days) | `requirements_met` |
| `test_section_121/Test5` | no | tests `Section121TwoPersons` and asserts `income_excluded_from_gross_income` (US-121-2) | |
| `test_section_121/Test6` | no | same as Test5 | |

Test2 and Test3 map onto the same row, and so do Test1 and Test4 (their use periods
differ and fall in the same label). `python oracle.py --check-official`: 6/6 direct,
4/6 mapped, 4/4 agreeing.

## 8. Behaviour of the encoding recorded by this table

* §121(b)(3) cannot be evaluated: any earlier §121(a) sale (other than on the same day)
  stops the scope with a run-time error. No official test gives an earlier sale.
* A period that starts within the 5 years counts in full even when it extends past the
  date of sale (`S121:183-184`); the representatives end on the date of sale, so the
  table does not depend on this.

## 9. Interpreter cross-check

All 12 rows were also run through the Catala interpreter: see
`paperC/catala_more/interpreter_crosscheck_report.txt` and `paperC/specs/README-FR2.md`.

Result: 12 rows run through the interpreter, 0 disagreements (4 rows whose label assertion passed, 8 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

12 rows: 1 `requirements_met`, 3 `requirements_not_met`, 0 EXCLUDED, 8 REJECTED. Four
official examples.
