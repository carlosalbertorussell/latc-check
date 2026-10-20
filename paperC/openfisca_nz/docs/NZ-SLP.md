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
