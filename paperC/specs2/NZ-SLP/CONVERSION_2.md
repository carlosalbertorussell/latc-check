# NZ-SLP: conversion record (second coder)

Entry variable `supported_living_payment__entitled` (Person, WEEK), OpenFisca Aotearoa
22.0.0 at commit `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb`, file
`openfisca_aotearoa/variables/acts/social_security/supported_living_payment/supported_living_payment.py`
(cited below as `slp.py`). Social Security Act 2018 (SSA 2018) ss 34-42.

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

## Trace

`supported_living_payment__entitled` (formula_2018_11_26, slp.py:17-38)
= `supported_living_payment__disabled_or_blind` OR `supported_living_payment__carer`.
The comments at slp.py:26-36 (ss 116, 117, 121, 128, 140, 170) are not encoded and add no input.

* `supported_living_payment__disabled_or_blind` (slp.py:48-69, s 34 and s 36):
  (`supported_living_payment__restricted_work_capacity` OR `totally_blind`)
  AND `social_security__residential_requirement` AND `age >= 16` AND NOT
  `supported_living_payment__disability_self_inflicted`.
* `supported_living_payment__carer` (slp.py:79-106, s 40(1)):
  `supported_living_payment__caring_for_another_person` AND
  `social_security__residential_requirement` AND
  ((`age >= 18` AND `social_security__dependent_children == 0`) OR `age >= 20`).

Leaves reached: restricted_work_capacity, totally_blind, disability_self_inflicted,
caring_for_another_person (all plain boolean inputs), `age`, and the two general terms kept
whole under rule 1: `social_security__residential_requirement` and
`social_security__dependent_children`.

## Choices

| # | Choice | Source |
|---|---|---|
| 1 | Attribute `residential_requirement` = `social_security__residential_requirement`, kept whole. Its 2018 formula (resident.py:55-74, s 16(2)) reads `immigration__citizen_or_resident`, `social_security__ordinarily_resident_in_new_zealand`, `social_security__resided_continuously_nz_2_years_citizen_or_resident`, `immigration__recognised_refugee`, `immigration__protected_person`, `social_security__ordinarily_resident_in_country_with_reciprocity_agreement` and `years_resided_continuously_in_new_zealand >= 2`. Expanding it would add about seven attributes, and 12 of the 13 official cases set the requirement directly, so under rule 7(d) they would stop mapping. | rule 1; resident.py:21-74; SSA 2018 s 16 |
| 2 | Attribute `dependent_children` = `social_security__dependent_children` (int, Schedule 2), kept whole. The only comparison is `== 0` (slp.py:87), so it is split into `0` and `1+` (representatives 0 and 1). Negative counts do not occur. | slp.py:87; interpretation/child.py:43-54 |
| 3 | Attribute `age`, split at 16, 18 and 20: `<16`, `16-17`, `18-19`, `20+` (representatives 15, 16, 18, 20). The three thresholds are integer literals in the formula; there is no parameter file for them. 16 is s 34(c); 18 is s 40(1)(c)(i); 20 is s 40(1)(c)(ii). Age is read at `period.start`. | slp.py:56, :87, :90; https://www.legislation.govt.nz/act/public/2018/0032/latest/whole.html#DLM6783175 |
| 4 | Booleans `restricted_work_capacity` (s 34(a), slp.py:109), `totally_blind` (s 34(a), demographics/health.py:26), `disability_self_inflicted` (s 36, slp.py:147), `caring_for_another_person` (s 40(1)(a), slp.py:137). | slp.py |
| 5 | Fixed period `2019-W01` (2018-12-31 to 2019-01-06), the period of every official entitlement test; formula_2018_11_26 applies. `base.yaml` (benefit amounts, period 2024-W15) sets the entry variable as an input and asserts other variables, so it is out of scope. | tests/social_security/supported_living_payment/entitled.yaml |
| 6 | Household: one person P, principal of a one-person family. The formula reads only person-level variables; children enter through `dependent_children`. | slp.py |
| 7 | No exclusions. Each attribute combination is legally possible: for example a person under 16 may care for someone, be blind, or have a dependent child; a person may be both totally blind and of restricted work capacity. | rule 5 |
| 8 | `citizenship__citizen`, which the official tests set, only feeds the residential requirement. When a test leaves the requirement unset (case `#0:0`), the encoding computes it as False because `social_security__ordinarily_resident_in_new_zealand` defaults to False; that computed value is the example's label. | resident.py; rule 7(c) |

Encoding behaviour recorded as found: s 40(1)(c)(ii) is encoded as `age >= 20` with no
condition on dependent children, so a carer of 20 or more qualifies with or without them.

## Result

256 combinations, 0 EXCLUDED, 0 REJECTED; 51 True, 205 False.

## Official cases

`entitled.yaml` has 7 tests with 13 person-cases. All 13 map and all 13 pass through the
encoding and through the oracle. Two cases (`#2:0` and `#3:0`) give the same row, so
there are 12 distinct conditions. Every declared label appears at least once in
`official_examples.csv`.

```
person-cases: 13; original encoding matches expected: 13 (of cases asserting the entry variable at 2019-W01); mapped: 13; oracle pass: 13/13
```
