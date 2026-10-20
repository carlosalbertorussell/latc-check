# US-121-1: conversion choices (second coder)

Sample `US-121-1`: `Section121SinglePerson.requirements_met` (IRC §121(a)). 400
combinations. Source: catala-examples `2694b17`, Catala 1.3.0.

## Source and official tests (common to US-121-1 and US-121-2)

* Module `Us_tax_code` (`us_tax_code/us_tax_code.catala_en`, including `preamble.catala_en`,
  `section_121.catala_en`, `section_132.catala_en`), compiled to Python with
  `catala python` (Catala 1.3.0; see `paperC/catala_code2/README.md`).
* Official tests: `us_tax_code/tests/test_section_121.catala_en`, six `#[test]` scopes.
  `Test1` to `Test4` assert `Section121SinglePerson.requirements_met` (true, false, false,
  true); `Test5` and `Test6` assert `Section121TwoPersons.income_excluded_from_gross_income`
  ($250,000 and $350,000). All use the shared scope `Data` (lines 6-62): sale and return on
  2021-01-01, gain $350,000, periods `period_four_years_recent` 2017-01-01..2021-01-01,
  `period_one_year_recent` 2019-01-01..2020-01-01, `period_two_years_middle`
  2015-01-01..2017-01-02, and `NoOtherSaleWhereSection121aApplied` throughout.
* The task names these two decisions; `Section121TwoPasses` ((b)(2)(B) and (b)(4)) has no
  official test and is outside both tables.
* **How the encoding counts time** (`section_121.catala_en:205-222`): for each period, if
  `sale <= begin + 5 year` the whole period counts (`end - begin`); else if
  `sale >= end + 5 year` it counts 0; else it counts `(end + 5 year) - sale`. The sums for
  ownership and use are each compared with `730 day` (`>=`, lines 224-240), and
  `requirements_met` is their conjunction. With the sale on 2021-01-01 the 5-year mark is
  2016-01-01.
* **(b)(3) raises.** `section_121_b_3_applies` (lines 369-383) compares
  `date_of_sale_or_exchange - other_sale.date_of_sale_or_exchange`, a number of days,
  with `2 year`. Catala 1.3.0 rejects comparisons between durations in different units,
  so every `MostRecentSaleWhereSection121aApplied` input raises `DateError`
  ("ambiguous comparison between durations in different units"), in the Python backend and
  in the interpreter (`clerk run` on a scratch scope, see `paperC/catala_code2/README.md`).
  Because the generated scope function computes all its outputs, the error also stops
  `requirements_met`, which does not read (b)(3). These rows are `REJECTED`. The cut at
  2 years is kept in the declared values (`under_2_years_before` 2020-01-01,
  `exactly_2_years_before` 2019-01-01, `over_2_years_before` 2018-06-01) since it is the
  comparison the code makes, and it would separate outcomes once the unit problem is fixed.


## Attributes

* `property_ownage` and `property_usage_as_principal_residence`: lists of periods,
  represented by ten labelled lists that cover each branch of the aggregation and both
  sides of the 730-day threshold, with the boundary itself (sale on 2021-01-01):

  | Label | Representative list | Days counted |
  |---|---|---|
  | `none` | [] | 0 |
  | `one_inside_window_over_730d` | 2017-01-01..2021-01-01 (official) | 1,461 |
  | `one_inside_window_730d` | 2018-01-02..2020-01-02 | 730 |
  | `one_inside_window_under_730d` | 2019-01-01..2020-01-01 (official) | 365 |
  | `one_across_5y_mark_over_730d` | 2010-01-01..2019-01-01 | 1,095 |
  | `one_across_5y_mark_730d` | 2010-01-01..2018-01-01 | 730 |
  | `one_across_5y_mark_under_730d` | 2015-01-01..2017-01-02 (official) | 366 |
  | `one_ended_before_5y_mark` | 2005-01-01..2015-06-01 | 0 |
  | `two_total_730d_or_more` | 2015-01-01..2017-01-02; 2019-01-01..2020-01-01 (official) | 731 |
  | `two_total_under_730d` | 2015-01-01..2016-06-01; 2019-01-01..2020-01-01 | 516 |

  The 730-day boundaries were checked against the encoding: 2018-01-02..2020-01-02 and
  2010-01-01..2018-01-01 meet the requirement, the same periods shortened by one day do not.
  Periods ending after the sale date, overlapping periods and periods with `end < begin`
  were left out; the scope declares the lists disjoint (lines 26-30).
* `other_section_121a_sale`: `none`, `under_2_years_before`, `exactly_2_years_before`,
  `over_2_years_before` (see above).

## Fixed inputs

* `date_of_sale_or_exchange` 2021-01-01 and `gain_from_sale_or_exchange_of_property`
  $350,000 (the official `Data`); `requirements_met` does not read the gain.
* Context variables `gain_cap` and `section_121_b_3_applies` are left to their
  definitions in the code (Option absent in the generated Python).

## Output

`met` (true) / `not_met` (false).

## Exclusions

None.

## REJECTED rows (300)

Every row with `other_section_121a_sale` other than `none` (3 × 100): `DateError` at
`section_121.catala_en:376`.

## Official examples (4 of 6 map)

| case | ownership | use | output |
|---|---|---|---|
| Test1 | `one_inside_window_over_730d` | `one_inside_window_over_730d` | `met` |
| Test2 | `one_inside_window_over_730d` | `one_inside_window_under_730d` | `not_met` |
| Test3 | `one_inside_window_over_730d` | `one_across_5y_mark_under_730d` | `not_met` |
| Test4 | `one_inside_window_over_730d` | `two_total_730d_or_more` | `met` |

`other_section_121a_sale = none` in all four. Each representative is the test's own list,
so the mapping is exact. `oracle.py --check-official`: 4 of 4 through the encoding and
through the oracle. `Test5` and `Test6` assert an output of `Section121TwoPersons` and are
unmappable here (they map onto US-121-2).

## Reproduction

```sh
cd paperC/specs2/US-121-1
python3.12 oracle.py --enumerate        # rewrites ground_truth.csv
python3.12 oracle.py --check-official   # official tests through the encoding and the oracle
```

`spec.json` and `official_examples.csv` are written by `oracle.py --write-spec --write-official`
from the same definitions. This conversion was made by the second coder without access to
the first coder's work (see `paperC/specs2/README-FR2-CODE2.md`).
