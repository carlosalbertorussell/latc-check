# US-121-2: conversion choices (second coder)

Sample `US-121-2`: `Section121TwoPersons.income_excluded_from_gross_income`
(IRC §121(a), (b)(1), (b)(2)(A), (b)(3)). 6,480 combinations. Source: catala-examples
`2694b17`, Catala 1.3.0.

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


## How the scope computes the output (`section_121.catala_en:96-128, 241-282, 300-323`)

Each person's excluded amount is the gain when that person meets ownership and use,
otherwise $0 ($0 under (b)(3)); the scope takes the larger of the two and caps it at
`gain_cap`: $250,000 (person 1's cap) unless (b)(2)(A) holds (joint return, either spouse
owns, both use, neither under (b)(3)), which gives $500,000. For a single or
surviving-spouse return `person1` and `person2` are the same `PersonalData`.

## Attributes

* `return_type`: `single_return`, `joint_return`, `surviving_spouse_return` (the three
  constructors of `ReturnType`).
* Per person: `<p>_property_ownage` and `<p>_property_usage_as_principal_residence` with
  two classes, `under_730d` (representative 2019-01-01..2020-01-01) and `730d_or_more`
  (2017-01-01..2021-01-01). Section121TwoPersons reads the lists only through the
  single-person requirements, which compare the aggregate with 730 days, so two classes
  suffice here; US-121-1 holds the finer description of the lists. `<p>_other_section_121a_sale`
  takes the four values of US-121-1.
* Person 2 attributes have a further value `not_applicable`: only `JointReturn`
  carries a second `PersonalData`.
* `gain_from_sale_or_exchange_of_property`: cut at the caps the code compares with
  (`>=` $250,000 and $500,000): `under_250000` ($100,000), `250000_to_500000` ($350,000,
  the official gain), `over_500000` ($600,000). At a gain of exactly $250,000 or $500,000
  the full gain and the cap are the same amount, so representatives inside the intervals
  keep the output labels distinct.

## Output labels

From the amount returned, with the row's representative gain: `zero` ($0), `full_gain`
(= gain), `capped_at_250000`, `capped_at_500000`. No other amount occurs.

## Fixed inputs

`date_of_sale_or_exchange` and `return_date` 2021-01-01 (official `Data`); for
`surviving_spouse_return`, `date_of_spouse_death` 2020-06-01 and
`death_spouse_info_at_time_of_death` = `person_ok_1` of `Data` (both required by the
constructor and unread by Section121TwoPersons). Context variables `person1`, `person2`,
`gain_cap` are left to their definitions in the code.

## Exclusions

* `person2_iff_joint_return`: the three person-2 attributes are `not_applicable` exactly
  when the return is not a joint return; the predicate holds when the return is joint and
  some person-2 attribute is `not_applicable`, or when the return is not joint and some
  person-2 attribute has a value. 2,928 rows.

## REJECTED rows (2,808)

Every valid row in which some `PersonalData` carries `MostRecentSaleWhereSection121aApplied`:
`DateError` at `section_121.catala_en:376`.

## Official examples (2 of 6 map)

* `Test5`: single return, person 1 = `person_ok_1` (ownership and use 2017-01-01..2021-01-01,
  both `730d_or_more`), gain $350,000 → $250,000 = `capped_at_250000`.
* `Test6`: joint return, person 1 = `person_ok_1`, person 2 = `person_ok_2` (ownership
  1,461 days; use 2015-01-01..2017-01-02 and 2019-01-01..2020-01-01 = 731 days, class
  `730d_or_more`), gain $350,000 → $350,000 = `full_gain`.

`oracle.py --check-official` runs each test with its own lists and with the class
representatives: 2 of 2 pass both ways. `Test1` to `Test4` assert an output of
`Section121SinglePerson` and are unmappable here (they map onto US-121-1).

## Reproduction

```sh
cd paperC/specs2/US-121-2
python3.12 oracle.py --enumerate        # rewrites ground_truth.csv
python3.12 oracle.py --check-official   # official tests through the encoding and the oracle
```

`spec.json` and `official_examples.csv` are written by `oracle.py --write-spec --write-official`
from the same definitions. This conversion was made by the second coder without access to
the first coder's work (see `paperC/specs2/README-FR2-CODE2.md`).
