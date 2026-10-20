# NZ-SPS conversion notes

Entry variable `sole_parent_support__entitled` (`sole_parent_support/sole_parent_support.py:23`, formula_2018_11_26 at line 30), week **2019-W05** (Monday 2019-01-28 to Sunday 2019-02-03; `period.first_month` is 2019-01). Line numbers without a file name refer to `openfisca_aotearoa/variables/acts/social_security/sole_parent_support/sole_parent_support.py`.

## Choices specific to this sample

1. **Formula traced.** `entitled = requirement AND split_care AND residential_requirement AND age_threshold` (lines 30-39, SSA 2018 s 29(a)-(d)).
   * `sole_parent_support__requirement` (lines 151-166, s 30): dependent-child requirement (summed over the 7 days of the week) AND (NOT in a relationship OR spouse or partner died OR marriage or civil union dissolved OR living apart and lost support OR lost regular support).
   * `sole_parent_support__dependent_child_requirement` (lines 177-187, WEEKDAY): some member in role child has `(dependent_child * age) < 14` (lines 180-181), AND the applicant is principal caregiver or has role parent.
   * `sole_parent_support__lost_regular_support` (lines 225-229, s 30(e)): partner imprisoned OR partner under supervision.
   * `sole_parent_support__split_care` (lines 259-294, s 32): with fewer than 2 dependent children, True for a principal or parent; with 2 or more, true when s 32(1), s 32(2) or s 32(3) holds.
   * `sole_parent_support__age_threshold` (lines 127-130): age at `period.first_day` >= 20.
2. **Attributes.** Eleven leaf inputs of the applicant, the age band, the composite `children` attribute, and two defined terms set at their own level (C2): `social_security__residential_requirement` (sub-tree as in NZ-SLP note 2) and `social_security__in_a_relationship` (`relationships.py:8-25`: married, civil union, de facto, or a member in role partner; the official cases set it directly). `social_security__principal_caregiver` (`interpretation/relationship.py:28`) is a leaf input of period MONTH and is set for 2019-01.
3. **Children as one composite attribute.** The formulas read the children only through the family members in role child: `social_security__dependent_child` (`interpretation/child.py:34-40`), their ages, and the count `social_security__dependent_children`. With `social_security__financially_independent` fixed to False (note 4), a child's relevant state is its age band. The thresholds are 14 (`parameters/social_security/sole_parent_support/child_age_threshold.yml`, value 14 from 2018-11-26, s 30), 16 and 18 (`interpretation/child.py:18-19`, Schedule 2 "child"). The attribute lists the family's children as an unordered multiset of bands: `none`, one child in one of 4 bands, or two children (10 unordered pairs), 15 labels in all. Representatives: ages 5, 14, 16, 18. Children are listed in band order, so the attribute has no duplicate orderings. Two children suffice to reach every case the formulas distinguish (count of dependent children 0, 1 or >= 2, and whether some child meets the under-14 test); the table covers families with at most two children.
4. **Fixed inputs.**
   * **Household:** the applicant is the family's principal; the family has the children of the `children` attribute and no member in role partner, parent or other. Section 32(1)(b)-(c) and the other-parent factor of s 32(2)(b) look at another parent who is a member of the same family (lines 266-268, 274). Modelling that parent would need a second full applicant profile (their own requirement, residence and age, via `sole_parent_support__entitled_without_split_care_requirement`). Without that member, s 32(1) is 0 and the other-parent factor of s 32(2)(b) is 1. `sole_parent_support__parents_living_apart` is then never read with effect, so it is not an attribute.
   * **Children's financial independence** (`interpretation/financially_independent.py:9`, a defined term with its own formula over full employment, student grants, government schemes and main benefits) is fixed to False. With a per-child flag the space has 294,912 combinations even with unordered children, above the 200,000 limit. False is the value in every official case.
   * **Period:** 22 of the 25 cases use 2019-W05; the other three (benefit amounts) use 2023-W05 and 2023-W15. Both parameters on the path have a single value since 2018 (age threshold 20 in `parameters/entitlements/social_security/sole_parent_support/age_threshold.yaml`, child age 14), so the table holds for every week from 2018-11-26. The repository also has `parameters/social_security/sole_parent_support/age_threshold.yml` (value 20); the formula reads the `entitlements` one (line 129).
5. **Age bands.** One threshold, 20 (s 29(d); the parameter file cites the MSD policy page). Bands `<20` (representative 19) and `>=20` (20). The applicant's age plays no other role on this path.
6. **Exclusion SPS-X1** (23,040 rows together with SPS-X2). The applicant is principal caregiver while the family has no dependent child (`children` is `none`, `1:>=18` or `2:>=18+>=18`). The variable is "Principal Caregiver in relation to a dependent child" (`interpretation/relationship.py:32`, Schedule 2). With financial independence fixed to False, a child is dependent exactly when under 18 (`interpretation/child.py:17-40`).
7. **Exclusion SPS-X2.** One of the s 32 flags that refer to the parents' children (`sole_parent_support__principal_caregiver_before_apart`, `__principal_caregiver_of_youngest`, `__both_primary_caregiver_by_order`; labels at lines 309, 318, 327) is True while the family has no dependent child. Section 32(4), quoted in the encoding at line 289, reads "child" in s 32 as a dependent child of the parents.
8. **Exclusions considered and rejected.** `sole_parent_support__receiving` with no child (an existing grant can outlast a change in circumstances; the Act does not make this impossible); in a relationship together with spouse or partner died, dissolved, or imprisoned (each can refer to a different, earlier partner); partner imprisoned together with partner under supervision (both orders can coexist).

## Encoding behaviour reproduced

* **Operator precedence at lines 180-181.** The code reads `persons.family.members("social_security__dependent_child", ...) * persons.family.members("age", ...) < child_age_threshold`, which Python evaluates as `(dependent_child * age) < 14`. For a child who is not a dependent child the product is 0, and 0 < 14 holds. So a family whose only child is 18 or older meets the "dependent child under 14" requirement, as long as the applicant is principal caregiver. The table reproduces this: for example `children = 1:>=18` with principal caregiver True is excluded by SPS-X1, but `children = 2:<14+>=18` behaves as the encoding computes. Rows where this matters: every valid row whose `children` has a `>=18` child and an under-18 child aged 14-17 and no child under 14 (`2:14-15+>=18`, `2:16-17+>=18`). For these the encoding finds the requirement met where the Act (s 30, a dependent child under 14) does not: 2,016 rows are True (1,008 for each of the two labels) that would be False under s 30.
* **Population-wide sum** in `social_security__dependent_children` (C4).
* **Parent role.** `dependent_child_requirement` accepts an applicant in role parent without the principal-caregiver flag (line 187). The table's applicant is always the principal, so this branch is not exercised.

## Official cases

25 cases (`sole_parent_support__entitled.yaml` 12, `__split_care.yaml` 7, `__benefit.yaml` 6). The 7 split-care cases assert only intermediate variables. The other 18 cases assert eligibility for 38 persons. 14 persons map and all 14 pass. The unmappable ones: 16 persons in role child; in `__entitled.yaml` case 3, five single persons whose `social_security__principal_caregiver` is True with no child in their family (SPS-X1; the case sets `sole_parent_support__requirement` directly, so the tests do not model the children); cases 4 and 5, which set `sole_parent_support__requirement` to True for a person without a child member; case 10, which sets `sole_parent_support__lost_regular_support` to True without either of its leaves.

## Conventions shared by the NZ samples

These points apply to NZ-SLP, NZ-AS and NZ-SPS (and the supplementary NZ-AS-1964). They are repeated in every CONVERSION.md so that each folder can be read on its own.

C1. **Ground truth is the encoding as written.** The output of every row is what OpenFisca Aotearoa at commit `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb` computes for the entry variable in the fixed week. Where the encoding departs from the Act (missing provisions, coding defects), the table follows the encoding, and the departure is listed below under "Encoding behaviour reproduced".

C2. **Level of the attributes.** Every input variable read on the path from the entry variable is traced. Leaf inputs (variables without a formula) become attributes. Some variables that have their own formula are defined terms of the Act, encoded once and shared by many benefits, and the rule's official tests always set them directly as inputs: `social_security__residential_requirement` (SSA 2018 s 16), `social_security__in_a_relationship`, `social_security__dependent_children`, `social_security__financially_independent`, `basic_grant__entitled` (Student Allowances Regulations 1998), `immigration__resident`. These are attributes (or fixed inputs) at the level of the defined term, and their own sub-trees are listed in the sample's notes. Expanding them would have made almost every official case unmappable, because the tests override the defined term without setting its leaves. The variables of the benefit's own provisions (for example `sole_parent_support__requirement`, `accommodation_supplement__accommodation_costs`) are always expanded down to their leaves.

C3. **Numeric inputs** are split at every threshold that the formulas on the path compare against, with the parameter file, its value in the fixed week and its legislative reference cited in `spec.json`. Each band's representative is a value inside the band, usually its lower bound or the boundary value itself (for `<=` comparisons), so that the boundary semantics are exercised.

C4. **One OpenFisca simulation per row.** `social_security__dependent_children` (`interpretation/child.py:52-54`) uses Python's built-in `sum` over the whole population array. In a simulation that holds several households, every household's count becomes the total over all households. The official tests each simulate one household, so the encoding behaves as intended there. `oracle.py --enumerate` therefore simulates each row on its own (in parallel worker processes). `oracle.py --batch-diagnostic` shows the effect: with 300 random rows simulated together, NZ-SPS gets 1 row wrong; the other tables are unaffected because they set the count directly as an input.

C5. **REJECTED rows.** None. No simulation raised an error.

C6. **Official cases: how a case maps onto a row.** `oracle.py --check-official` loads every YAML file of the rule's test folder and, for each case:
1. builds the simulation exactly as `openfisca test` does (`SimulationBuilder.set_default_period(period)`, then `build_from_dict`), and computes the entry variable for every period the case asserts. This is the "directly through OpenFisca" count;
2. skips the case (UNMAPPABLE) when it asserts nothing about the entry variable;
3. otherwise, for each person whose value is asserted: rejects the person when the asserted week lies outside the range where the table's formula version and parameter values apply, or when the household differs from the table's fixed household (role, members);
4. reads every attribute from the case's own simulation, at the period the formula reads it (so an attribute that the case leaves unset takes the encoding's default, or the value its formula computes from what the case does set);
5. builds the oracle row, rejects it if it is EXCLUDED, and simulates it with tracing on. Every variable that the case sets as an input and that the oracle's computation reads (traced) is compared with the oracle's value at each traced period. A difference makes the person UNMAPPABLE (the case overrides an intermediate result with a value the attributes do not produce). Equal values are noted. Inputs that the oracle never reads are listed as such; their effect, if any, reaches the row through the attribute values of step 4;
6. compares the oracle output with the expected value.
Step 5 is what makes the mapping safe: a mapped person's output is determined by the row alone.

C7. **Verification.** `paperC/openfisca_nz/crosscheck.py` restates each formula in plain Python (no OpenFisca) and compares it with every row of `ground_truth.csv`, including the EXCLUDED labels. All rows agree for all four tables.

## Official case log

Output of `oracle.py --check-official --log` (`paperC/openfisca_nz/logs/check_official_NZ-SPS.txt`), paths relative to `openfisca_aotearoa/tests/social_security/`:

```
NZ-SPS: 25 official cases in openfisca_aotearoa/tests/social_security/sole_parent_support/*.yaml
  cases without an assertion of sole_parent_support__entitled: 7
  asserted person-values run directly through OpenFisca: 38/38 passed
  person-values mapped onto the table: 14; through the oracle: 14/14 passed
  person-values unmappable: 24
```

| case (person) | result | detail |
|---|---|---|
| `sole_parent_support/sole_parent_support__benefit.yaml#1[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__benefit.yaml#1[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__benefit.yaml#2[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): social_security__income |
| `sole_parent_support/sole_parent_support__benefit.yaml#2[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__benefit.yaml#3[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): social_security__income, sole_parent_support__weekly_childcare_cost |
| `sole_parent_support/sole_parent_support__benefit.yaml#3[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__benefit.yaml#4[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): social_security__income, sole_parent_support__weekly_childcare_cost |
| `sole_parent_support/sole_parent_support__benefit.yaml#4[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__benefit.yaml#5[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): social_security__income, sole_parent_support__weekly_childcare_cost |
| `sole_parent_support/sole_parent_support__benefit.yaml#5[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__benefit.yaml#6[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): social_security__income, sole_parent_support__weekly_childcare_cost |
| `sole_parent_support/sole_parent_support__benefit.yaml#6[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#1[Koro]` | PASS | oracle=False expected=False sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; sole_parent_support__lost_regular_support@2019-W05 set to False, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#1[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#2[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; sole_parent_support__lost_regular_support@2019-W05 set to False, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#2[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#3[0]` | UNMAPPABLE | maps onto a row excluded by the spec: SPS-X1 |
| `sole_parent_support/sole_parent_support__entitled.yaml#3[1]` | UNMAPPABLE | maps onto a row excluded by the spec: SPS-X1 |
| `sole_parent_support/sole_parent_support__entitled.yaml#3[2]` | UNMAPPABLE | maps onto a row excluded by the spec: SPS-X1 |
| `sole_parent_support/sole_parent_support__entitled.yaml#3[3]` | UNMAPPABLE | maps onto a row excluded by the spec: SPS-X1 |
| `sole_parent_support/sole_parent_support__entitled.yaml#3[4]` | UNMAPPABLE | maps onto a row excluded by the spec: SPS-X1 |
| `sole_parent_support/sole_parent_support__entitled.yaml#4[Koro]` | UNMAPPABLE | sets sole_parent_support__requirement@2019-W05 = True, which the table's attributes compute as False |
| `sole_parent_support/sole_parent_support__entitled.yaml#4[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#5` | UNMAPPABLE | sets sole_parent_support__requirement@2019-W05 = True, which the table's attributes compute as False |
| `sole_parent_support/sole_parent_support__entitled.yaml#6[Koro]` | PASS | oracle=False expected=False sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row; sole_parent_support__lost_regular_support@2019-W05 set to False, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#6[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#7[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#7[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#8[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#8[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#9[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#9[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#10[Koro]` | UNMAPPABLE | sets sole_parent_support__lost_regular_support@2019-W05 = True, which the table's attributes compute as False |
| `sole_parent_support/sole_parent_support__entitled.yaml#10[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#11[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#11[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__entitled.yaml#12[Koro]` | PASS | oracle=True expected=True sole_parent_support__age_threshold@2019-W05 set to True, equal to the value computed from the row |
| `sole_parent_support/sole_parent_support__entitled.yaml#12[Tamaiti]` | UNMAPPABLE | person has role child in the family; the table describes the family's principal |
| `sole_parent_support/sole_parent_support__split_care.yaml` #1 | UNMAPPABLE | does not assert sole_parent_support__entitled (asserts social_security__dependent_children, sole_parent_support__parents_living_apart, sole_parent_support__split_care) |
| `sole_parent_support/sole_parent_support__split_care.yaml` #2-#7 (6 cases) | UNMAPPABLE | does not assert sole_parent_support__entitled (asserts sole_parent_support__split_care) |
