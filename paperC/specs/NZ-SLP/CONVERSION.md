# NZ-SLP conversion notes

Entry variable `supported_living_payment__entitled` (`supported_living_payment.py:9`, formula_2018_11_26 at line 17), week **2019-W01** (Monday 2018-12-31 to Sunday 2019-01-06). File paths are relative to `openfisca_aotearoa/variables/acts/social_security/` unless they start with `openfisca_aotearoa/`.

## Choices specific to this sample

1. **Formula traced.** `entitled = disabled_or_blind OR carer` (line 38).
   * `supported_living_payment__disabled_or_blind` (lines 48-69, SSA 2018 ss 34-36): (restricted work capacity OR totally blind) AND residential requirement AND age >= 16 AND NOT self-inflicted.
   * `supported_living_payment__carer` (lines 79-106, SSA 2018 s 40): caring for another person AND residential requirement AND ((age >= 18 AND dependent children = 0) OR age >= 20).
   * The comments at lines 26-36 and 94-104 list provisions the encoding leaves out (ss 116, 117, 121, 128, 140, 170, s 40(2)-(3), s 41, s 42, s 54(5)(d), s 61(5)(d)). The table follows the encoding (C1).
2. **Attributes.** Five leaf inputs (`supported_living_payment__restricted_work_capacity`, `totally_blind`, `supported_living_payment__disability_self_inflicted`, `supported_living_payment__caring_for_another_person`, and `age`) plus two defined terms set at their own level (C2):
   * `social_security__residential_requirement` (`resident.py:21`, SSA 2018 s 16). Its 2018 formula (lines 55-74) reads `immigration__citizen_or_resident`, `social_security__ordinarily_resident_in_new_zealand`, `social_security__resided_continuously_nz_2_years_citizen_or_resident`, `immigration__recognised_refugee`, `immigration__protected_person`, `social_security__ordinarily_resident_in_country_with_reciprocity_agreement` and `years_resided_continuously_in_new_zealand`. All 7 entitlement cases of `entitled.yaml` set it directly.
   * `social_security__dependent_children` (`interpretation/child.py:43`), the number of dependent children, computed from the family's child members. `entitled.yaml` case 6 sets it directly. Only `== 0` is compared (line 87), so the declared values are `0` and `>=1`.
3. **Age bands.** The formulas compare the age at `period.start` (2018-12-31) with the literals 16 (line 56, s 34(c)), 18 (line 87, s 40(1)(c)(i)) and 20 (line 90, s 40(1)(c)(ii)). No parameter file is involved. Bands `<16`, `16-17`, `18-19`, `>=20` with representatives 15, 16, 18, 20. Age is set directly for every day of the week (`set_input_dispatch_by_period`), as the official tests do; `date_of_birth` is not used.
4. **Fixed inputs.** The applicant is alone, as principal of a one-person family. Nothing on the path reads another family member. The period is the period of every entitlement case; the formula reads no parameter, so the table is the same for every week from 2018-11-26.
5. **Exclusion SLP-X1.** `supported_living_payment__disability_self_inflicted` is labelled "The person's restricted capacity for work, or total blindness, was self-inflicted and brought about by the person with a view to qualifying for a benefit" (line 151, SSA 2018 s 36). The flag presupposes restricted work capacity or total blindness; when both are False it describes something impossible by definition. 32 rows. The output of those rows would be False in any case (the s 34 branch already fails), so the exclusion changes labels and never outcomes.
6. **Exclusions considered and rejected.** Age under 16 with dependent children (possible: the Act does not bar a parent under 16 from having a dependent child); caring for another person combined with restricted work capacity (possible; the two grounds are independent).
7. **Official cases.** 50 cases. The 43 cases of `base.yaml` assert the benefit amount with `supported_living_payment__entitled` set as an input, so they assert nothing about eligibility. The 7 cases of `entitled.yaml` assert eligibility for 13 persons; all 13 map onto the table and pass. Every mapped case also sets `citizenship__citizen`, which the table reads only through `social_security__residential_requirement`.

## Encoding behaviour reproduced

* The s 40 carer route with dependent children: an applicant aged 18-19 with dependent children is not eligible (line 87-90), as the Act states.
* No further departures were found on this path.

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

Output of `oracle.py --check-official --log` (`paperC/openfisca_nz/logs/check_official_NZ-SLP.txt`), paths relative to `openfisca_aotearoa/tests/social_security/`:

```
NZ-SLP: 50 official cases in openfisca_aotearoa/tests/social_security/supported_living_payment/*.yaml
  cases without an assertion of supported_living_payment__entitled: 43
  asserted person-values run directly through OpenFisca: 13/13 passed
  person-values mapped onto the table: 13; through the oracle: 13/13 passed
  person-values unmappable: 0
```

| case (person) | result | detail |
|---|---|---|
| `supported_living_payment/entitled.yaml#1` | PASS | oracle=False expected=False inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#2[0]` | PASS | oracle=True expected=True inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#2[1]` | PASS | oracle=False expected=False inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#3[0]` | PASS | oracle=True expected=True inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#3[1]` | PASS | oracle=False expected=False inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#4[0]` | PASS | oracle=True expected=True inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#4[1]` | PASS | oracle=False expected=False inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#5[0]` | PASS | oracle=False expected=False inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#5[1]` | PASS | oracle=True expected=True inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#6[0]` | PASS | oracle=False expected=False inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#6[1]` | PASS | oracle=True expected=True inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#7[0]` | PASS | oracle=True expected=True inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/entitled.yaml#7[1]` | PASS | oracle=False expected=False inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): citizenship__citizen |
| `supported_living_payment/base.yaml` #1-#43 (43 cases) | UNMAPPABLE | does not assert supported_living_payment__entitled (asserts supported_living_payment__base, supported_living_payment__benefit, supported_living_payment__reduction) |
