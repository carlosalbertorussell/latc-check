# NZ-AS-1964 conversion notes (supplementary table)

This table is kept outside `paperC/specs`, so it is not a Paper C sample. It is the SSA 1964 formula of the same variable as NZ-AS; promote it to `paperC/specs/` only by a decision of the author.

Entry variable `accommodation_supplement__entitled` (`openfisca_aotearoa/variables/acts/social_security/accommodation_supplement/entitled.py:10`, formula_1964_12_04 at line 75, applies to weeks up to 2018-11-25), week **2018-W01** (Monday 2018-01-01 to Sunday 2018-01-07; `this_month` is 2018-01).

## Choices specific to this table

1. **Formula traced** (lines 75-138, based on MSD's web page and SSA 1964): age at `period.first_day` >= 16 AND (resident OR permanent resident OR citizen) AND ordinarily resident in New Zealand AND accommodation costs AND NOT social housing AND below the income threshold AND below the cash threshold.
2. **Attributes.** All inputs read by the formula. `accommodation_supplement__accommodation_costs` has only a formula from 2018-11-26 (`costs.py:20`), so in 2018-W01 it is a plain input (default False). `social_housing__eligible` ("Has social housing?", default True), `accommodation_supplement__below_income_threshold` and `__below_cash_threshold` (default True) are plain inputs (`entitled.py:142-164`). `immigration__resident` (`acts/immigration/residence.py:34-42`, "Holder of a permanent resident visa or a resident visa") has a formula (holds a resident visa OR permanent resident); the official cases set it directly, so it is an attribute at its own level (C2). `citizenship__citizen`, `immigration__permanent_resident` and `social_security__ordinarily_resident_in_new_zealand` are inputs of period ETERNITY.
3. **Age.** Threshold 16 from `openfisca_aotearoa/parameters/social_security/accommodation_supplement/age_threshold.yaml` (single value from 1964-12-04). Bands `<16` (15) and `>=16` (16).
4. **Exclusion AS64-X1** (128 rows). Permanent resident True with resident False: the encoding defines `immigration__resident` as the disjunction that includes permanent residence (`residence.py:38`, `:41-42`).
5. **Exclusions considered and rejected.** Citizen together with a resident or permanent resident visa: under the Immigration Act 2009 visas are granted to non-citizens, but the text could not be checked from this environment, so no exclusion was declared.
6. **Official cases.** All 6 cases of `1964/entitled.yaml` map and pass (2018-W01, inside the range up to 2018-11-25). The other 41 cases of the folder assert other variables or (2018/entitled.yaml) lie in 2022, outside this table's range.

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

Output of `oracle.py --check-official --log` (`paperC/openfisca_nz/logs/check_official_NZ-AS-1964.txt`), paths relative to `openfisca_aotearoa/tests/social_security/`:

```
NZ-AS-1964: 47 official cases in openfisca_aotearoa/tests/social_security/accommodation_supplement/2018/*.yaml, openfisca_aotearoa/tests/social_security/accommodation_supplement/1964/*.yaml
  cases without an assertion of accommodation_supplement__entitled: 40
  asserted person-values run directly through OpenFisca: 12/12 passed
  person-values mapped onto the table: 6; through the oracle: 6/6 passed
  person-values unmappable: 6
```

| case (person) | result | detail |
|---|---|---|
| `accommodation_supplement/2018/entitled.yaml#1[0]` | UNMAPPABLE | asserted for 2022-W01, outside 1964-12-04 to 2018-11-25, where the table's formula version and parameter values apply |
| `accommodation_supplement/2018/entitled.yaml#1[1]` | UNMAPPABLE | asserted for 2022-W01, outside 1964-12-04 to 2018-11-25, where the table's formula version and parameter values apply |
| `accommodation_supplement/2018/entitled.yaml#1[2]` | UNMAPPABLE | asserted for 2022-W01, outside 1964-12-04 to 2018-11-25, where the table's formula version and parameter values apply |
| `accommodation_supplement/2018/entitled.yaml#1[3]` | UNMAPPABLE | asserted for 2022-W01, outside 1964-12-04 to 2018-11-25, where the table's formula version and parameter values apply |
| `accommodation_supplement/2018/entitled.yaml#1[4]` | UNMAPPABLE | asserted for 2022-W01, outside 1964-12-04 to 2018-11-25, where the table's formula version and parameter values apply |
| `accommodation_supplement/2018/entitled.yaml#1[5]` | UNMAPPABLE | asserted for 2022-W01, outside 1964-12-04 to 2018-11-25, where the table's formula version and parameter values apply |
| `accommodation_supplement/1964/entitled.yaml#1` | PASS | oracle=True expected=True |
| `accommodation_supplement/1964/entitled.yaml#2` | PASS | oracle=True expected=True |
| `accommodation_supplement/1964/entitled.yaml#3` | PASS | oracle=True expected=True |
| `accommodation_supplement/1964/entitled.yaml#4` | PASS | oracle=False expected=False |
| `accommodation_supplement/1964/entitled.yaml#5` | PASS | oracle=False expected=False |
| `accommodation_supplement/1964/entitled.yaml#6` | PASS | oracle=False expected=False |
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
