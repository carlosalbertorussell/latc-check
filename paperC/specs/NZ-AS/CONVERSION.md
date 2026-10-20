# NZ-AS conversion notes

Entry variable `accommodation_supplement__entitled` (`accommodation_supplement/entitled.py:10`, formula_2018_11_26 at line 19), week **2022-W01** (Monday 2022-01-03 to Sunday 2022-01-09; `period.first_month` is 2022-01). File paths are relative to `openfisca_aotearoa/variables/` unless they start with `openfisca_aotearoa/`.

## Choices specific to this sample

1. **Formula version.** The variable has two formulas: `formula_1964_12_04` (lines 75-138, SSA 1964 s 61EA, for weeks up to 2018-11-25) and `formula_2018_11_26` (lines 19-73, SSA 2018 ss 65-67). This sample uses the 2018 formula, the law in force. The six official cases of `1964/entitled.yaml` assert the 1964 formula at 2018-W01 and so cannot map onto this table; the same encoding at that week is kept as the supplementary table `paperC/openfisca_nz/supplementary/NZ-AS-1964/`, outside `paperC/specs`, where all six map (see README-NZ.md).
2. **Formula traced.** `entitled = residential_requirement AND accommodation_costs AND assets_requirement AND NOT social_housing_exclusion AND NOT other_funding_exclusion` (lines 67-73).
   * `accommodation_supplement__accommodation_costs` (`acts/social_security/accommodation_supplement/costs.py:20-94`, s 65(2)): costs > 0 AND type rent (applicant not a non-principal tenant), mortgage (not a non-principal owner), board or lodging; or (d) principal of a tenancy or ownership whose summed costs are > 0 with type rent or mortgage.
   * `accommodation_supplement__assets_requirement` (`regulation/social_security_regulation/accommodation_supplement/assets.py:19-66`, Social Security Regulations 2018 reg 15): total cash assets of principal and partners <= 16,200 for a principal in a relationship or a single principal with dependent children; <= 8,100 for a single principal without.
   * `accommodation_supplement__social_housing_exclusion` (`acts/social_security/accommodation_supplement/exclusion.py:18-21`, s 66): type social housing.
   * `accommodation_supplement__other_funding_exclusion` (`exclusion.py:33-79`, s 67): principal whose partner receives Accommodation Supplement; receiving, entitled to, or would be entitled to a basic grant or independent circumstances grant; type residential care; `accommodation_supplement__disability`. Section 67(e) is a TODO in the encoding (line 70).
3. **Attributes.** Leaf inputs: `accommodation_type` (7 values in the declared order of `demographics/housing.py:8-15`, including `unknown`, the default), `accommodation_costs` (float), `accommodation_supplement__cash_assets` (int), the partner's `accommodation_supplement__receiving`, `basic_grant__receiving`, `independent_circumstances_grant__receiving`, `independent_circumstances_grant__entitled` (no formula), `basic_grant__would_be_entitled`, `independent_circumstances_grant__would_be_entitled`, `accommodation_supplement__disability`. Defined terms set at their own level (C2): `social_security__residential_requirement` (sub-tree as in NZ-SLP note 2), `social_security__in_a_relationship` (`acts/social_security/relationships.py:8-25`), `social_security__dependent_children` (`acts/social_security/interpretation/child.py:43`; the `_benefit_me.yaml` cases set it directly), and `basic_grant__entitled` (`regulation/student_allowance/basic_grant.py:10-39`, Student Allowances Regulations 1998 reg 4, which reads student status, age 16/18, partner, supported child and two further allowance variables; `2018/exclusion.yaml` and `2018/accommodation_supplement.yaml` set it directly).
4. **Household and the partner.** The applicant is the principal of a family, of a tenancy and of an ownership; the tenancy and ownership have no other member. With a sole principal, s 65(2)(d) gives the same result as (a) and (b), and the roles tenant, owner and other never apply; distinguishing them would need co-tenants and co-owners with costs of their own. When `social_security__in_a_relationship` is True the family also has one member in role partner, with cash assets 0 and `accommodation_supplement__receiving` taken from the attribute `partner_accommodation_supplement__receiving` (s 67(a)). The attribute `accommodation_supplement__cash_assets` is the total of applicant and partner that reg 15 compares, so the partner's share is folded into it; when mapping an official case, the oracle adds the partner's cash assets to the applicant's. The applicant's own `accommodation_supplement__receiving` is read but summed over partners only, so it has no effect.
5. **Numeric splits.** `accommodation_costs`: the formula compares `> 0` (`costs.py:57, 64, 69, 79, 84`); bands `<=0` (representative 0.0) and `>0` (100.0). `accommodation_supplement__cash_assets`: thresholds `ssa2018_15_1_b` = 8,100 and `ssa2018_15_1_a` = 16,200 in `openfisca_aotearoa/parameters/social_security/accommodation_supplement/assets.yaml` (single values from 2018-11-26, Social Security Regulations 2018 reg 15), compared with `<=`; bands `<=8100`, `8101-16200`, `>16200` with representatives 8,100, 16,200 and 16,201 (the boundary values). `social_security__dependent_children`: compared `>= 1` (`assets.py:24`); bands `0` and `>=1`.
6. **Period.** 2022-W01 is the week asserted by `2018/entitled.yaml`, the only SSA 2018 eligibility case. The formula applies from 2018-11-26 and both thresholds have a single value, so the table holds for every week from then on.
7. **Exclusion AS-X1** (21,504 rows). Not in a relationship, yet a partner receives Accommodation Supplement. The partner exists only as a family member in role partner, and the encoding defines such a member as a relationship (`relationships.py:20-24`); s 67(a) speaks of P's spouse or partner.
8. **Exclusion AS-X2** (21,504 rows; 5,376 rows meet both, 37,632 EXCLUDED in all). Eligible for an independent circumstances grant while receiving a basic grant. Student Allowances Regulations 1998 reg 8(3), quoted in `regulation/student_allowance/independent_circumstances.py:24-25`: "no student is eligible for an independent circumstances grant if the student receives a basic grant".
9. **Exclusions considered and rejected.** "Entitled" together with "would be entitled but for income" for the same grant: the encoding's labels ("Would be eligible for basic grant if less income") suggest the two exclude each other, but the Act's text for s 67(b)(iii) could not be checked from this environment (legislation.govt.nz was unreachable), so no exclusion was declared. Receiving a basic grant while not entitled to it (possible during an overpayment). Accommodation costs > 0 with type `unknown`, `social_housing` or `residential_care` (possible: such costs exist; the formula ignores them).
10. **Few True rows.** Only 28 of the 48,384 valid rows are True: the seven s 67 flags must all be False, the residential requirement True, the type one of four, costs > 0, and the assets band compatible with the household.

## Encoding behaviour reproduced

* Section 67(e) is not encoded (`exclusion.py:70`, TODO).
* The 2018 formula does not test age; the 1964 formula did (age 16).

## Official cases

47 cases. 40 assert only other variables (amounts, areas, rates, intermediate tests). The 7 that assert eligibility cover 12 persons: the 6 persons of `2018/entitled.yaml` case 1 and the 6 single-person cases of `1964/entitled.yaml`. The 1964 cases fall outside the table's period range (note 1). `2018/entitled.yaml` sets the five conjuncts of the formula directly; for 5 of its 6 persons, `accommodation_supplement__accommodation_costs` is set to True, which no leaf values of the case produce (the case sets no type and no costs), so only person 2 maps (it passes). `2018/accommodation_supplement.yaml` asserts the amount `accommodation_supplement`; a positive amount implies eligibility, but the case asserts no eligibility value, so it is not mapped.

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

Output of `oracle.py --check-official --log` (`paperC/openfisca_nz/logs/check_official_NZ-AS.txt`), paths relative to `openfisca_aotearoa/tests/social_security/`:

```
NZ-AS: 47 official cases in openfisca_aotearoa/tests/social_security/accommodation_supplement/2018/*.yaml, openfisca_aotearoa/tests/social_security/accommodation_supplement/1964/*.yaml
  cases without an assertion of accommodation_supplement__entitled: 40
  asserted person-values run directly through OpenFisca: 12/12 passed
  person-values mapped onto the table: 1; through the oracle: 1/1 passed
  person-values unmappable: 11
```

| case (person) | result | detail |
|---|---|---|
| `accommodation_supplement/2018/entitled.yaml#1[0]` | UNMAPPABLE | sets accommodation_supplement__accommodation_costs@2022-W01 = True, which the table's attributes compute as False |
| `accommodation_supplement/2018/entitled.yaml#1[1]` | UNMAPPABLE | sets accommodation_supplement__accommodation_costs@2022-W01 = True, which the table's attributes compute as False |
| `accommodation_supplement/2018/entitled.yaml#1[2]` | PASS | oracle=False expected=False accommodation_supplement__accommodation_costs@2022-W01 set to False, equal to the value computed from the row; accommodation_supplement__assets_requirement@2022-W01 set to True, equal to the value computed from the row; accommodation_supplement__other_funding_exclusion@2022-W01 set to False, equal to the value computed from the row; accommodation_supplement__social_housing_exclusion@2022-W01 set to False, equal to the value computed from the row |
| `accommodation_supplement/2018/entitled.yaml#1[3]` | UNMAPPABLE | sets accommodation_supplement__accommodation_costs@2022-W01 = True, which the table's attributes compute as False |
| `accommodation_supplement/2018/entitled.yaml#1[4]` | UNMAPPABLE | sets accommodation_supplement__accommodation_costs@2022-W01 = True, which the table's attributes compute as False |
| `accommodation_supplement/2018/entitled.yaml#1[5]` | UNMAPPABLE | sets accommodation_supplement__accommodation_costs@2022-W01 = True, which the table's attributes compute as False |
| `accommodation_supplement/1964/entitled.yaml#1` | UNMAPPABLE | asserted for 2018-W01, outside 2018-11-26 to ..., where the table's formula version and parameter values apply |
| `accommodation_supplement/1964/entitled.yaml#2` | UNMAPPABLE | asserted for 2018-W01, outside 2018-11-26 to ..., where the table's formula version and parameter values apply |
| `accommodation_supplement/1964/entitled.yaml#3` | UNMAPPABLE | asserted for 2018-W01, outside 2018-11-26 to ..., where the table's formula version and parameter values apply |
| `accommodation_supplement/1964/entitled.yaml#4` | UNMAPPABLE | asserted for 2018-W01, outside 2018-11-26 to ..., where the table's formula version and parameter values apply |
| `accommodation_supplement/1964/entitled.yaml#5` | UNMAPPABLE | asserted for 2018-W01, outside 2018-11-26 to ..., where the table's formula version and parameter values apply |
| `accommodation_supplement/1964/entitled.yaml#6` | UNMAPPABLE | asserted for 2018-W01, outside 2018-11-26 to ..., where the table's formula version and parameter values apply |
| `accommodation_supplement/2018/_benefit_me.yaml` #1-#3 (3 cases) | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement, family_tax_credit, jobseeker_support__benefit) |
| `accommodation_supplement/2018/accommodation_supplement.yaml` #1 | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement) |
| `accommodation_supplement/2018/area.yaml` #1 | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__area_of_residence) |
| `accommodation_supplement/2018/assets.yaml` #1-#4 (4 cases) | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__assets_requirement) |
| `accommodation_supplement/2018/base.yaml` #1-#10 (10 cases) | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__base) |
| `accommodation_supplement/2018/beneficiary.yaml` #1 | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__beneficiary, accommodation_supplement__non_beneficiary) |
| `accommodation_supplement/2018/costs.yaml` #1-#6 (6 cases) | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__accommodation_costs) |
| `accommodation_supplement/2018/cutout.yaml` #1 | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__cutout) |
| `accommodation_supplement/2018/exclusion.yaml` #1 | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__social_housing_exclusion) |
| `accommodation_supplement/2018/exclusion.yaml` #2-#7 (6 cases) | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__other_funding_exclusion) |
| `accommodation_supplement/2018/rate.yaml` #1 | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__rate) |
| `accommodation_supplement/2018/rebate.yaml` #1 | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts accommodation_supplement__rebate) |
| `accommodation_supplement/2018/situation.yaml` #1-#4 (4 cases) | UNMAPPABLE | does not assert accommodation_supplement__entitled (asserts persons) |
