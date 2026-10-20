# NZ-AS: conversion record (second coder)

Entry variable `accommodation_supplement__entitled` (Person, WEEK), OpenFisca Aotearoa
22.0.0 at commit `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb`, file
`openfisca_aotearoa/variables/acts/social_security/accommodation_supplement/entitled.py`
(cited below as `entitled.py`).

## Rules applied to all three NZ samples of the second coder

These rules were set by the second coder before building any table, without access to the
first coder's work (see `paperC/specs2/README-NZ-CODE2.md`, "Blinding").

1. **Depth of the trace.** Every variable that the rule's own sections define is traced
   down to variables without a formula at the fixed period. A variable that implements a
   general definition or a test from outside the rule's own sections, and that the rule
   reads as a single condition, is kept as one attribute and not expanded: the residential
   requirement of SSA 2018 s 16 (`social_security__residential_requirement`), the
   Schedule 2 dictionary terms (`social_security__dependent_children`,
   `social_security__dependent_child`, `social_security__principal_caregiver`,
   `social_security__in_a_relationship`), and the immigration and citizenship status
   variables. Age is an input in whole years (`age`); `date_of_birth` is left unset.
2. **Booleans** are declared `["False", "True"]`.
3. **Numeric inputs** are split at every value the traced formulas compare against. Labels
   name the interval; the lowest interval is open below (so it also holds the encoding's
   default age of -9999, which the formulas treat as a small number). The representative
   of the lowest interval is the threshold minus one; every other representative is the
   interval's lower bound, so each threshold is exercised from both sides.
4. **One fixed period** per rule, taken from the periods the official tests use.
5. **Exclusions** only for combinations that a definition makes impossible.
6. **Every other input** stays at its declared default. The household structure is fixed
   per rule (see `fixed_inputs` in spec.json).
7. **Mapping official cases.** An official case is one person in one official YAML test.
   It maps onto the table when (a) the test asserts the entry variable at the fixed period,
   (b) the person fits the fixed household structure, (c) every attribute has a declared
   label for the value the encoding computes for that person in the test's own simulation
   (attributes may be given directly or computed from inputs below them), and (d) any
   formula variable lying between the attributes and the entry variable that the test sets
   directly is set to the value its formula would give anyway. Check (d) is done by
   rebuilding the test with those inputs removed and comparing every such intermediate
   variable and the output for that person. The expected output of the test is the
   example's output label.
8. **REJECTED.** No cell raised an error, so no cell is REJECTED.

## Period: the decisive choice for this rule

The variable has two formulas. `formula_1964_12_04` (entitled.py:75-138, Social Security
Act 1964 s 61EA) applies to periods before 2018-11-26; `formula_2018_11_26`
(entitled.py:19-73, SSA 2018 ss 65-67) applies from then on. The official tests use two
periods: six tests at `2018-W01` (folder `1964/`) and one test at `2022-W01` (folder
`2018/`).

The second coder fixes the period at **2018-W01**, so the 1964-Act formula is the rule
converted. Reasons:

* Its inputs are all person-level variables, so the trace reaches the leaves in one step.
* Six of the seven official tests sit at that period, and all six map (rule 7).
* The 2018-Act formula reads the tenancy, ownership and family entities (costs.py:20-94;
  regulation/.../accommodation_supplement/assets.py:19-66, cash-asset thresholds of the
  Social Security Regulations 2018 r 15; exclusion.py:33-79, which reaches student
  allowance entitlement). A faithful table would need a fixed multi-entity household and
  several numeric splits. Its single official test sets all five intermediate variables
  (`social_security__residential_requirement`, `accommodation_supplement__accommodation_costs`,
  `accommodation_supplement__assets_requirement`,
  `accommodation_supplement__social_housing_exclusion`,
  `accommodation_supplement__other_funding_exclusion`) directly, so it would not map at
  the leaf level either.

## Trace (formula_1964_12_04)

`age(period.first_day) >= age_threshold`
AND (`immigration__resident` + `immigration__permanent_resident` + `citizenship__citizen`)
AND `social_security__ordinarily_resident_in_new_zealand`
AND `accommodation_supplement__accommodation_costs`
AND (`social_housing__eligible` == 0)
AND `accommodation_supplement__below_income_threshold`
AND `accommodation_supplement__below_cash_threshold`.
Monthly-read inputs are read at `period.first_month` (2018-01).

## Choices

| # | Choice | Source |
|---|---|---|
| 1 | Fixed period `2018-W01` (2018-01-01 to 2018-01-07). | see above; tests/social_security/accommodation_supplement/1964/entitled.yaml |
| 2 | Attribute `age`, split at 16: `<16`, `16+` (representatives 15, 16). Parameter `social_security.accommodation_supplement.age_threshold` = 16 from 1964-12-04, file `parameters/social_security/accommodation_supplement/age_threshold.yaml`, reference SSA 1964 https://www.legislation.govt.nz/act/public/1964/0136/latest/DLM359124.html. Age is read at `period.first_day`. | entitled.py:80-89 |
| 3 | Attributes `immigration_resident`, `immigration_permanent_resident`, `citizen`, kept whole under rule 1. `immigration__resident` has a formula (holds_resident_visa OR permanent_resident, immigration/residence.py:34-42), and the official tests set it directly; it is the variable the rule reads. | entitled.py:106-110 |
| 4 | Exclusion `PR-IMPLIES-RESIDENT`: `immigration_permanent_resident == 'True' and immigration_resident == 'False'`. The encoding defines `immigration__resident` as "Holder of a permanent resident visa or a resident visa" and computes it as a disjunction that includes `immigration__permanent_resident`; Immigration Act 2009 s 4 counts the permanent resident visa among residence class visas. A permanent resident who is not a resident is impossible by that definition. 128 combinations. | immigration/residence.py:26-42 |
| 5 | No exclusion between `citizen` and the visa attributes. Whether a citizen can hold a residence class visa at the same time is a question of fact and law the encoding does not settle by definition, so the second coder leaves those combinations valid. | rule 5 |
| 6 | Attribute `ordinarily_resident_in_nz` = `social_security__ordinarily_resident_in_new_zealand` (ETERNITY, no formula, default False). | resident.py:77 |
| 7 | Attribute `accommodation_costs` = `accommodation_supplement__accommodation_costs`. Its only formula starts 2018-11-26 (costs.py:20), so at 2018-W01 it is a plain boolean input with default False. | costs.py:11-20 |
| 8 | Attribute `social_housing` = `social_housing__eligible` (label "Has social housing?", default True, no formula); the rule requires it to be False. | entitled.py:117-118, :142-148 |
| 9 | Attributes `below_income_threshold` and `below_cash_threshold` (no formula, default True). The encoding gives no amounts, so these stay booleans. | entitled.py:120-128, :151-164 |
| 10 | Household: one person P, principal of a one-person family. | entitled.py:75-138 reads only person-level variables |

## Result

512 combinations, 128 EXCLUDED, 0 REJECTED; 5 True, 379 False. The 5 True rows are
age `16+`, ordinarily resident, accommodation costs, no social housing, below both
thresholds, and one of the five status combinations allowed by the exclusion with at least
one status True.

## Official cases

12 person-cases: 6 from `1964/entitled.yaml` (one person each) and 6 from
`2018/entitled.yaml` (one test with six persons). The six 1964-Act cases map and pass through the
encoding and through the oracle, with 6 distinct conditions. The six 2018-Act cases assert
the entry variable at 2022-W01 only, so they do not map (rule 7(a)); `openfisca test`
passes them (see `paperC/openfisca_code2/openfisca_test_results.txt`).

Declared values never used by the official examples: `ordinarily_resident_in_nz=False`,
`below_income_threshold=False`, `below_cash_threshold=False`.

```
UNMAPPED social_security/accommodation_supplement/2018/entitled.yaml#0:0: entry variable not asserted at the fixed period 2018-W01
UNMAPPED social_security/accommodation_supplement/2018/entitled.yaml#0:1: entry variable not asserted at the fixed period 2018-W01
UNMAPPED social_security/accommodation_supplement/2018/entitled.yaml#0:2: entry variable not asserted at the fixed period 2018-W01
UNMAPPED social_security/accommodation_supplement/2018/entitled.yaml#0:3: entry variable not asserted at the fixed period 2018-W01
UNMAPPED social_security/accommodation_supplement/2018/entitled.yaml#0:4: entry variable not asserted at the fixed period 2018-W01
UNMAPPED social_security/accommodation_supplement/2018/entitled.yaml#0:5: entry variable not asserted at the fixed period 2018-W01
person-cases: 12; original encoding matches expected: 6 (of cases asserting the entry variable at 2018-W01); mapped: 6; oracle pass: 6/6
```
