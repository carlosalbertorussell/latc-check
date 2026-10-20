# US-121-2 conversion record

Table: the amount of gain excluded under 26 U.S.C. 121 on a single, joint or
surviving-spouse return, as the Catala scope `Section121TwoPersons` computes it, in
bands named after the cases of the statute. Sub-table 2 of 2 of US-121.

File references are to CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`; `S121` is
`us_tax_code/section_121.catala_en`, `TESTS` is
`us_tax_code/tests/test_section_121.catala_en`.

## 1. Scope and output

* Entry point: scope `Section121TwoPersons` (`S121:70-86`) through
  `paperC/catala_more/generated/Us_tax_code.py` (`section121_two_persons`). It is the
  scope Test5 and Test6 use.
* The scope runs `Section121SinglePerson` for person 1 and person 2
  (`S121:107-129`). `income_excluded_from_gross_income_uncapped` is the larger of the
  two persons' uncapped amounts (`S121:219-224`): the gain when the person meets §121(a)
  and §121(b)(3) does not apply, else $0. `income_excluded_from_gross_income` caps it
  at `gain_cap` (`S121:250-254`): $500,000 when `section_121_b_2_A_condition` holds
  (§121(b)(2)(A), `S121:283-313`), else person 1's cap of $250,000 (§121(b)(1),
  `S121:236`, `248`).
* Output labels, from the statute's cases:

| Label | Encoding output | Statute |
|---|---|---|
| `no_exclusion` | uncapped amount $0 | §121(a) not met, or §121(b)(3) applies |
| `entire_gain` | uncapped amount > $0 and below the applicable cap; excluded = gain | the whole gain is excluded |
| `limited_to_250000` | uncapped ≥ $250,000 and the cap is $250,000; excluded = $250,000 | §121(b)(1) limitation |
| `limited_to_500000` | uncapped ≥ $500,000 and the cap is $500,000; excluded = $500,000 | §121(b)(2)(A) limitation |

The oracle reads `income_excluded_from_gross_income_uncapped`,
`income_excluded_from_gross_income`, `section_121_b_2_A_condition` and
`gain_cap_person_1` from the scope, determines the cap the scope applied, checks that
the excluded amount equals min(uncapped, cap) and returns the label. A gain exactly
equal to the cap is `limited_to_…`, in line with the code's `>=` (`S121:251`).

## 2. Attributes

| Attribute | Kind | Labels | Notes |
|---|---|---|---|
| `return_type` | enum | `single`, `joint`, `surviving_spouse` | `ReturnType` (`S121:65-68`): `SingleReturn`, `JointReturn`, `SingleReturnSurvivingSpouse` |
| `person1_ownership_days_in_5_years` | interval | `lt_730_days`, `ge_730_days` | as in US-121-1 |
| `person1_use_days_in_5_years` | interval | `lt_730_days`, `ge_730_days` | as in US-121-1 |
| `person1_other_section_121a_sale` | enum | `none`, `within_2_years`, `more_than_2_years` | as in US-121-1 |
| `person2_ownership_days_in_5_years` | interval | `lt_730_days`, `ge_730_days` | |
| `person2_use_days_in_5_years` | interval | `lt_730_days`, `ge_730_days` | |
| `person2_other_section_121a_sale` | enum | `none`, `within_2_years`, `more_than_2_years` | |
| `gain` | interval | `gt_0_lt_250000` (rep. $200,000), `250000_to_lt_500000` ($350,000, the tests' gain), `ge_500000` ($600,000) | cut at the two caps the code compares with |

Choices made:

* **Filing status.** The three constructors of `ReturnType`. For `single`, the scope
  takes both person 1 and person 2 from the single `PersonalData` (`S121:95-105`); for
  `surviving_spouse` it takes both from `DeadSpouseInfo.return`. The oracle builds the
  `JointReturn` from the person-1 and person-2 labels, the `SingleReturn` from the
  person-1 labels, and the `SingleReturnSurvivingSpouse` with person 1 as `return`,
  person 2 as `death_spouse_info_at_time_of_death` and `date_of_spouse_death`
  \|2020-06-01\| (neither is read by this scope).
* **Gain.** A gain of $0 has nothing to exclude and would give `no_exclusion` whatever
  the requirements, so the first band starts above $0.

## 3. Fixed inputs

`date_of_sale_or_exchange` \|2021-01-01\| and `return_date` \|2021-01-01\| (`TESTS:19-20`;
`return_date` is read by no rule), `date_of_spouse_death` \|2020-06-01\|, and the context
variables `person1`, `person2`, `gain_cap` left to the scope's definitions, as in the
tests.

## 4. Exclusions

| id | Rows | Rule |
|---|---|---|
| `person2_differs_on_single_return` | 792 | `return_type` is `single` or `surviving_spouse` and at least one person-2 label differs from the matching person-1 label |

On those returns there is one taxpayer, and the scope's person 2 is person 1
(`S121:101-105`); a row whose person-2 labels differ describes no return. The
predicate is written out with string constants for each pair of different labels.

## 5. REJECTED rows (432)

Every non-excluded row in which person 1 or person 2 has `within_2_years` or
`more_than_2_years` raises the `DateError` of `S121:376` described in US-121-1: 384
joint rows and 24 rows each for `single` and `surviving_spouse`.

## 6. Band check (`python oracle.py --check-bands`)

The period lists and earlier-sale dates of US-121-1 for both persons, and gains of
$0.01, $1,000 and $249,999.99 / $250,000, $250,000.01 and $499,999.99 / $500,000,
$500,000.01 and $10,000,000: 9,912 evaluations, all giving the output of the label's
representative.

## 7. Official tests

| Test | Mapped | Row | Output |
|---|---|---|---|
| `test_section_121/Test1`–`Test4` | no | test `Section121SinglePerson.requirements_met` (US-121-1) | |
| `test_section_121/Test5` | yes | `single`, person 1 `ge_730_days, ge_730_days, none`, person 2 the same (the scope's person 2 on a single return), gain `250000_to_lt_500000` | `limited_to_250000` (asserted $250,000) |
| `test_section_121/Test6` | yes | `joint`, person 1 `ge_730_days, ge_730_days, none`, person 2 `ge_730_days, ge_730_days, none` (use 731 days), gain `250000_to_lt_500000` | `entire_gain` (asserted $350,000) |

Test6's person 2 uses the two periods of `person_ok_2` (731 days); the table row uses
the label's representative period (1,461 days), with the same output.
`python oracle.py --check-official`: 6/6 direct, 2/6 mapped, 2/2 agreeing.

## 8. Behaviour of the encoding recorded by this table

* `Section121TwoPersons` has no rule for §121(b)(2)(B) (other joint returns: the sum of
  each spouse's limitation) or §121(b)(4) (surviving spouses): those are in the scope
  `Section121TwoPasses` (`S121:131-160`, `324-361`, `398-431`), whose `PeriodMerge`
  returns `[]` (`S121:13-21`, marked TODO) and which no official test uses. In this
  table a joint return that misses §121(b)(2)(A) gets the $250,000 limitation, and a
  surviving spouse is treated like a single filer.
* `section121a_requirements_met` (`S121:216-217`, `304-307`) is computed and never used
  for the amount, which comes from each person's own §121(a) test.
* §121(b)(3) cannot be evaluated (section 5).

## 9. Interpreter cross-check

All 504 non-excluded rows were also run through the Catala interpreter: see
`paperC/catala_more/interpreter_crosscheck_report.txt` and `paperC/specs/README-FR2.md`.

Result: 504 rows run through the interpreter, 0 disagreements (72 rows whose label assertion passed, 432 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

1,296 rows: 45 `no_exclusion`, 12 `entire_gain`, 12 `limited_to_250000`, 3
`limited_to_500000`, 792 EXCLUDED, 432 REJECTED. Two official examples.
