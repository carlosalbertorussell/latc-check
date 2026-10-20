# NZ-SPS: conversion record (second coder)

Entry variable `sole_parent_support__entitled` (Person, WEEK), OpenFisca Aotearoa 22.0.0 at
commit `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb`, file
`openfisca_aotearoa/variables/acts/social_security/sole_parent_support/sole_parent_support.py`
(cited below as `sps.py`). Social Security Act 2018 (SSA 2018) ss 29-32.

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

`sole_parent_support__entitled` (formula_2018_11_26, sps.py:30-39) =
`sole_parent_support__requirement` (s 29(a)) AND `sole_parent_support__split_care` (s 29(b))
AND `social_security__residential_requirement` (s 29(c)) AND
`sole_parent_support__age_threshold` (s 29(d)).

* `sole_parent_support__age_threshold` (sps.py:118-130): `age(period.first_day) >= 20`.
  It belongs to the rule's own s 29(d), so it is expanded to `age` (rule 1).
* `sole_parent_support__requirement` (sps.py:151-166, s 30):
  `dependent_child_requirement` summed over the seven days of the week (option `"add"`)
  AND (NOT `social_security__in_a_relationship` OR `spouse_or_partner_died` OR
  `marriage_or_civil_union_dissolved` OR `living_apart_and_lost_support` OR
  `lost_regular_support`).
* `sole_parent_support__lost_regular_support` (sps.py:225-229, s 30(e)):
  `partner_imprisoned` OR `partner_supervision`. Expanded to its two leaves (rule 1).
* `sole_parent_support__dependent_child_requirement` (WEEKDAY, sps.py:177-187, s 30): for
  each family member, `social_security__dependent_child * age < 14`, then ANY over members
  in the child role, AND (`social_security__principal_caregiver` read at the first month of
  the day OR the person has the parent role).
* `sole_parent_support__split_care` (sps.py:259-294, s 32): it applies only when
  `social_security__dependent_children >= 2`; otherwise it equals "the person has the
  parent or principal role". With the fixed household (one child), P's dependent children
  number 0 or 1, so split care is True for P and its other inputs (parents living apart,
  principal caregiver before living apart, of the youngest, care orders, receiving SPS)
  have no effect. They are left at their defaults.

## Choices

| # | Choice | Source |
|---|---|---|
| 1 | Household fixed: family F with principal P (the subject) and one member C in the child role. The official tests that build a family use exactly this shape (Koro and Tamaiti). Two or more children would bring in s 32 split care and a second parent, which the official tests never exercise. | sps.py:259-294; official test file |
| 2 | Attribute `residential_requirement`, kept whole (rule 1; s 16). Every official test sets it directly. | sps.py:35; resident.py:21 |
| 3 | Attribute `age` of P, split at 20: `<20`, `20+` (representatives 19, 20). Parameter `entitlements.social_security.sole_parent_support.age_threshold` = 20 from 2018, file `parameters/entitlements/social_security/sole_parent_support/age_threshold.yaml` (reference: MSD policy page; SSA 2018 s 29(d)). P's age enters no other comparison: the child-age test is filtered to the child role. | sps.py:118-130 |
| 4 | Attribute `in_a_relationship` = `social_security__in_a_relationship`, kept whole (Schedule 2 term, rule 1). With no partner in the family and no marriage inputs its formula gives False; the tests either set it or let it compute. | sps.py:156; relationships.py:8-25 |
| 5 | Booleans `spouse_or_partner_died` (s 30(b)), `marriage_or_civil_union_dissolved` (s 30(c)), `living_apart_and_lost_support` (s 30(d)), `partner_imprisoned` (s 30(e)(i)), `partner_supervision` (s 30(e)(ii)). | sps.py:190-248 |
| 6 | Attribute `principal_caregiver` = P's `social_security__principal_caregiver` (Schedule 2, MONTH). The week 2019-W05 runs from 2019-01-28 to 2019-02-03 and each day reads its own month, so the oracle sets it for `month:2019-01:2`, as the official tests do. | sps.py:183; interpretation/relationship.py:28 |
| 7 | Attribute `child_dependent` = C's `social_security__dependent_child` (Schedule 2), kept whole (rule 1). Its own formula (age under 16, or under 18 and not financially independent, in the child role) is not expanded. | sps.py:180; interpretation/child.py:26-40 |
| 8 | Attribute `child_age` = C's age, split at 14: `<14`, `14+` (representatives 13, 14). Parameter `social_security.sole_parent_support.child_age_threshold` = 14 from 2018-11-26, file `parameters/social_security/sole_parent_support/child_age_threshold.yml`, reference SSA 2018 s 30 (https://www.legislation.govt.nz/act/public/2018/0032/latest/whole.html#DLM6783167). The other file `parameters/entitlements/.../youngest_child_age_threshold.yaml` (also 14) is read only by `sole_parent_support__family_has_child_under_age_limit`, which the entry variable does not reach. | sps.py:178-181 |
| 9 | Fixed period `2019-W05`, the period of every official test. | official test file |
| 10 | No exclusions. In particular a child aged 14 or more may still be a dependent child (up to 18), and a person who is in a relationship may still have had a former spouse die or a former marriage dissolved. | rule 5 |

Encoding behaviour recorded as found:

* Operator precedence in sps.py:180-181 makes the child test
  `(dependent_child * age) < 14`. For a child who is not dependent the product is 0, so the
  test holds whatever the child's age. The table records that behaviour: a non-dependent
  child satisfies the requirement at both ages.
* In six official tests (`#6` to `#11`) the child's age is written `age: 5` without a period
  while the principal's age carries an explicit period; the simulation builder then leaves
  the child's age at the default -9999. The child test still holds (-9999 < 14), and under
  rule 3 that value falls in `<14`. These cases are mapped with `child_age=<14`.

## Result

2,048 combinations, 0 EXCLUDED, 0 REJECTED; 189 True, 1,859 False.
(True needs residential requirement, P aged 20+, P principal caregiver, a child that is
non-dependent or under 14 (3 of 4 child combinations), and one of 63 of the 64 relationship
combinations: all except "in a relationship" with every s 30(b)-(e) ground False.)

## Official cases

`sole_parent_support__entitled.yaml` has 12 tests with 26 person-cases. 8 map, and all 8
pass through the encoding and through the oracle. Two of them (`#0:Koro` and `#5:Koro`) give
the same row, so there are 7 distinct conditions. 18 do not map:

* 10 child persons (Tamaiti) are outside the table, which is about the principal (rule 7(b)).
* 6 persons of tests `#2` and `#4` have no family with a child (rule 7(b)); these tests set
  `sole_parent_support__requirement` and `sole_parent_support__split_care` directly.
* `#3:Koro` sets `sole_parent_support__requirement` to True, while its formula gives False
  (no principal caregiver input, and Koro holds the principal role, so the parent-role
  alternative does not apply) (rule 7(d)).
* `#9:Koro` sets `sole_parent_support__lost_regular_support` to True with neither
  `partner_imprisoned` nor `partner_supervision` set, so its formula gives False (rule 7(d)).

Declared values never used by the official examples: `residential_requirement=False`,
`age=<20`, `principal_caregiver=False`, `child_dependent=False`, `child_age=14+`.

```
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#0:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#1:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#2:0: family is not exactly one principal and one child (the table fixes that composition)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#2:1: family is not exactly one principal and one child (the table fixes that composition)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#2:2: family is not exactly one principal and one child (the table fixes that composition)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#2:3: family is not exactly one principal and one child (the table fixes that composition)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#2:4: family is not exactly one principal and one child (the table fixes that composition)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#3:Koro: sets intermediate variable(s) to values their formulas do not give for this case: sole_parent_support__entitled_without_split_care_requirement, sole_parent_support__requirement
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#3:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#4:0: family is not exactly one principal and one child (the table fixes that composition)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#5:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#6:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#7:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#8:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#9:Koro: sets intermediate variable(s) to values their formulas do not give for this case: sole_parent_support__lost_regular_support
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#9:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#10:Tamaiti: person is not the principal of its family (the table is about the principal P)
UNMAPPED social_security/sole_parent_support/sole_parent_support__entitled.yaml#11:Tamaiti: person is not the principal of its family (the table is about the principal P)
person-cases: 26; original encoding matches expected: 26 (of cases asserting the entry variable at 2019-W05); mapped: 8; oracle pass: 8/8
```
