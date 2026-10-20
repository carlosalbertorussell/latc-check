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
  \|2020-12-31\| (neither is read by this scope).
* **Person 2 by filing status** (section 11 gives the reasons):

  | `return_type` | person 1 | person 2 |
  |---|---|---|
  | `single` | the taxpayer (`SingleReturn` content) | the same taxpayer; rows with different person-2 labels are EXCLUDED (section 4) |
  | `joint` | `JointReturn.person1` | `JointReturn.person2`, the other spouse |
  | `surviving_spouse` | `DeadSpouseInfo.return`, the surviving spouse who sells | `DeadSpouseInfo.death_spouse_info_at_time_of_death`, the deceased spouse |
* **Gain.** A gain of $0 has nothing to exclude and would give `no_exclusion` whatever
  the requirements, so the first band starts above $0.

## 3. Fixed inputs

`date_of_sale_or_exchange` \|2021-01-01\| and `return_date` \|2021-01-01\| (`TESTS:19-20`;
`return_date` is read by no rule), `date_of_spouse_death` \|2020-12-31\| (section 11), and the context
variables `person1`, `person2`, `gain_cap` left to the scope's definitions, as in the
tests.

## 4. Exclusions

| id | Rows | Rule |
|---|---|---|
| `person2_differs_on_single_return` | 396 | `return_type` is `single` and at least one person-2 label differs from the matching person-1 label |

A single return carries the data of one taxpayer (`SingleReturn content PersonalData`,
`S121:65-66`), and the scope reads that one record as both person 1 and person 2
(`S121:95-105`); a single-return row whose person-2 labels differ from the person-1
labels describes no return. The predicate is written out with string constants for
each pair of different labels. Until the correction of 2026-10-20 (section 11) the
exclusion also covered `surviving_spouse` rows (792 rows in all).

## 5. REJECTED rows (696)

Every non-excluded row in which a person whose data the scope reads has
`within_2_years` or `more_than_2_years` raises the `DateError` of `S121:376` described
in US-121-1: 384 `joint` rows (person 1 or person 2), 24 `single` rows and 288
`surviving_spouse` rows (person 1, the surviving spouse; the deceased spouse's
`person2_other_section_121a_sale` is not read, section 11).

## 6. Band check (`python oracle.py --check-bands`)

The period lists and earlier-sale dates of US-121-1 for both persons, and gains of
$0.01, $1,000 and $249,999.99 / $250,000, $250,000.01 and $499,999.99 / $500,000,
$500,000.01 and $10,000,000: 17,700 evaluations after the correction (9,912 before it),
all giving the output of the label's representative. On `surviving_spouse` rows the
person-2 probes go into the deceased spouse's record, which the scope does not read, so
those probes test nothing beyond section 11's independence check.

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
  surviving spouse is treated like a single filer: the deceased spouse's facts (the
  person-2 labels of `surviving_spouse` rows) never change the output (section 11).
* `section121a_requirements_met` (`S121:216-217`, `304-307`) is computed and never used
  for the amount, which comes from each person's own §121(a) test.
* §121(b)(3) cannot be evaluated (section 5).

## 9. Interpreter cross-check

Before the correction, all 504 non-excluded rows were also run through the Catala
interpreter: see `paperC/catala_more/interpreter_crosscheck_report.txt` and
`paperC/specs/README-FR2.md`. Section 11 gives the check of the 396 rows the correction
added.

Result before the correction: 504 rows run through the interpreter, 0 disagreements (72 rows whose label assertion passed, 432 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

1,296 rows: 144 `no_exclusion`, 23 `entire_gain`, 34 `limited_to_250000`, 3
`limited_to_500000`, 396 EXCLUDED, 696 REJECTED (204 valid rows). Two official
examples. Counts before the correction of 2026-10-20: section 11.

## 11. Correction of 2026-10-20: surviving-spouse rows

**What was wrong.** The exclusion `person2_differs_on_single_return` covered
`single` and `surviving_spouse` rows, on the ground that "there is one taxpayer" and
the person-2 labels describe no return. The independent verification
(`paperC/verify/VERIFY-FR2.md` on branch `paperc-verify-fr2`, "Substantive
disagreement", item 1) found that this ground holds for `single` rows only. On a
`surviving_spouse` row the oracle puts the person-2 labels into
`DeadSpouseInfo.death_spouse_info_at_time_of_death` (`S121:60-63`): they describe the
deceased spouse, a real second person whose facts the statute uses. The fact that
`Section121TwoPersons` reads person 2 from `DeadSpouseInfo.return`
(`S121:101-105`) is behaviour of the scope; it makes no such row legally impossible.
The 396 surviving-spouse rows excluded on that ground were therefore wrongly outside
V. The protocol (`paperC/PROTOCOL.md`) and the harness are unchanged; this is a data
correction in this folder only.

**How person-2 labels map onto the deceased spouse's facts.** On a
`surviving_spouse` row:

| Attribute | Field of `death_spouse_info_at_time_of_death` | Meaning |
|---|---|---|
| `person2_ownership_days_in_5_years` | `property_ownage` (`S121:51`) | days the deceased spouse owned the residence, aggregated over the 5 years ending on the date of sale, below or at least 730 |
| `person2_use_days_in_5_years` | `property_usage_as_principal_residence` (`S121:52-53`) | days the deceased spouse used it as principal residence, same window |
| `person2_other_section_121a_sale` | `other_section_121a_sale` (`S121:54`) | whether the deceased spouse had an earlier sale to which §121(a) applied, and when |

The representatives are the same periods and dates as for person 1 (section 2). The
person-2 periods end on \|2021-01-01\|, the date of sale, and Catala counts a period as
`end - begin` days (`S121:179-191`), so a period ending on \|2021-01-01\| covers days up
to \|2020-12-31\|. The fixed `date_of_spouse_death` was therefore moved from
\|2020-06-01\| to \|2020-12-31\|, the day before the sale, so that no representative
gives the deceased spouse ownership or use after death. The earlier-sale dates
(\|2020-01-01\|, \|2018-06-01\|) precede the death. With this date the sale also falls
within the 2-year window of §121(b)(4) and of the encoding's own surviving-spouse rule
(`S121:399-404`: death < sale ≤ death + 2 years). The 5-year window ending at the death
and the one ending at the sale differ by one day; the representatives give 366 and
1,461 days in both.

This mapping is the encoding's own: `Section121TwoPasses` builds, for a surviving
spouse, a `JointReturn` with `person1: single_data.return` and `person2:
single_data.death_spouse_info_at_time_of_death`, evaluated at the date of death
(`S121:406-425`), and grants $500,000 when that first pass meets §121(b)(2)(A)
(`S121:427-430`). The statute uses the same facts:

* 26 U.S.C. 121(b)(4) (`S121:392-396`): "In the case of a sale or exchange of property
  by an unmarried individual whose spouse is deceased on the date of such sale,
  paragraph (1) shall be applied by substituting "$500,000" for "$250,000" if such sale
  occurs not later than 2 years after the date of death of such spouse and the
  requirements of paragraph (2)(A) were met immediately before such date of death."
  Paragraph (2)(A) (`S121:271-280`) asks whether either spouse meets the ownership
  requirement, both meet the use requirement, and neither is ineligible under (b)(3):
  each of the three person-2 attributes enters it.
* 26 U.S.C. 121(d)(2) (not encoded in `S121`): "in the case of an unmarried individual
  whose spouse is deceased on the date of the sale or exchange of property, the period
  such unmarried individual owned and used such property shall include the period such
  deceased spouse owned and used such property before death."

**What the encoding outputs on these rows.** Each `surviving_spouse` row is evaluated
through `oracle.py` with the generated Python (`paperC/catala_more/generated/Us_tax_code.py`,
scope `Section121TwoPersons`), which reads only `DeadSpouseInfo.return` (`S121:99`,
`105`). The output is the one of the same row with the person-2 labels set equal to the
person-1 labels (checked on all 432 `surviving_spouse` rows, 0 differences), and a row
is REJECTED exactly when person 1 has another §121(a) sale (the `DateError` of
`S121:376`); the deceased spouse's earlier sale is never read. The table thus records,
as rows of V, that this scope gives a surviving spouse the single-filer result whatever
the deceased spouse's facts (section 8).

**Design choice considered and set aside.** A representative that leaves person 2
unused for surviving spouses would need an extra label (such as `not_applicable`) on
the three person-2 attributes, plus an exclusion of that label on `joint` rows and of
the other labels on `surviving_spouse` rows. That is again a table-design exclusion
removing 396 legally possible rows from V, and it would change the declared domain of
three attributes. The mapping above keeps the domain unchanged, gives every
surviving-spouse row a possible return, and uses the record the encoding itself treats
as the deceased spouse's data.

**Counts before and after.**

| | \|D\| | valid | EXCLUDED | REJECTED | no_exclusion | entire_gain | limited_to_250000 | limited_to_500000 |
|---|---|---|---|---|---|---|---|---|
| before (commit `6566904`) | 1,296 | 72 | 792 | 432 | 45 | 12 | 12 | 3 |
| after | 1,296 | 204 | 396 | 696 | 144 | 23 | 34 | 3 |

The 396 rows that left EXCLUDED became 264 REJECTED, 99 `no_exclusion`, 11
`entire_gain` and 22 `limited_to_250000`. Every other row (the 432 `single` rows, the
432 `joint` rows, and the 36 `surviving_spouse` rows that were in V before) has the same
output as before, the 72 previously valid rows included. Per filing status after the
correction: `single` 396 EXCLUDED, 24 REJECTED, 12 valid; `joint` 384 REJECTED, 48
valid; `surviving_spouse` 288 REJECTED, 144 valid.

**Checks rerun.** `python3.12 oracle.py --write-spec` (spec.json regenerated from the
table definition), `--check-official` (6/6 direct, 2/2 mapped, both agreeing; the
mapped rows are a `single` and a `joint` row, unchanged), `--enumerate`,
`--write-official` (official_examples.csv byte-identical) and `--check-bands` (17,700
evaluations, all agreeing). `SHA256SUMS` regenerated. The Catala-interpreter check of the changed
rows, the harness run and the verifier's recomputation on the corrected table are
recorded in the "Correction" section of `paperC/specs/README-FR2.md` and in
`paperC/results/REPORT-US-121-2-FIX.md`.

Other changes in this folder made with the correction: the exclusion's source now
cites `S121:65-66` and `95-105` in place of 26 U.S.C. 121(b)(1) (verifier item 10), and
the person-2 ownership source cites `S121:50-54` in place of `50-57` (verifier item 11). The
table title now names surviving-spouse returns, which the table always contained.
