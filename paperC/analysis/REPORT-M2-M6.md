# Paper C: analyses M2 (slicing and the official examples) and M6 (agreement of the two conversions)

Status: computed on branch `paperc-analysis` (cut from `main`) for review by the author. No
wording here has been approved for the paper. Every number comes from a script in
`paperC/analysis/` and is stored in `paperC/analysis/out/*.json`.

## Reproduce

```sh
paperC/analysis/fetch_sources.sh                 # catala-examples 2694b17, openfisca-aotearoa 9d77ea7ce3c4 into _ext/
git fetch origin                                 # the scripts read origin/<branch> with git show
python3.12 -I paperC/analysis/check_yaml_reader.py   # optional; needs PyYAML, checks the stdlib YAML reader
python3.12 -I paperC/analysis/m2_fr_af.py        # FR-PF, FR-AF   (about 10 s)
python3.12 -I paperC/analysis/m6_fr_af.py        # FR-PF, FR-AF   (about 4 min; runs the Catala 1.3.0 Python build)
python3.12 -I paperC/analysis/m2_fr2.py          # FR-APL, US-121
python3.12 -I paperC/analysis/m6_fr2.py
python3.12 -I paperC/analysis/m2_nz.py           # NZ-SLP, NZ-AS, NZ-SPS
python3.12 -I paperC/analysis/m6_nz.py
python3.12 -I paperC/analysis/build_report.py    # writes this file from fragments/
```

Standard library only. `m6_fr_af.py` and the FR-PF variant of `m2_fr_af.py` evaluate inputs
through the Catala 1.3.0 Python build of the branches (extracted with `git archive` into
`_ext/branches/`), because the second coder's resource bands depend on the computed
allocation. No OpenFisca evaluation was needed: every NZ label used is set by the tests or
follows from a variable's default or a simple formula in the cloned source.

Branches read: first conversion `paperc-data-fr`, `paperc-data-fr2`, `paperc-data-fr2-fix`
(corrected US-121-2), `paperc-data-nz`; second conversion `paperc-code2-fr`,
`paperc-code2-fr2`, `paperc-code2-nz`. No other branch was modified.

## Definitions used throughout

* **Suite of a rule**: every official test of that rule in the pinned test files.
  FR-PF: the 4 `droit_ouvert` assertions of `tests_ouverture_droits.catala_fr` Test1 (a
  variant adds the 33 children of the 14 household tests). FR-AF: the 14 scopes of
  `tests_allocations_familiales.catala_fr`. FR-APL: the 3 scopes of
  `tests_eligibilite_apl.catala_fr`. US-121: the 6 scopes of `test_section_121.catala_en`.
  NZ: every case of the rule's YAML folder (SLP 50, AS 47, SPS 25), counted per person.
* **Mapped**: the rows of the table's `official_examples.csv`.
* **Whole suite placement** (M2(b)): every test placed on the table's attributes with the
  table's own labels and cut points, ignoring the table's fixed inputs, period and
  household shape and ignoring which output the test asserts. A test with no value for an
  attribute counts as **unknown** on that attribute. Where the encoding gives an unset
  input a default, a secondary count with the default is reported beside it (NZ).
* **H1 indicators** (PROTOCOL.md section 8): (1) unused declared values > 0; (2) C1
  `missed_valid` > 0, the number of valid rows outside the product of the observed
  values (`common.usage`).

## Summary

### M2: declared values unused by the mapped tests and by the whole suite

| Rule | Table | First conversion: declared / unused mapped / unused whole suite | Second conversion: declared / unused mapped / unused whole suite |
|---|---|---|---|
| FR-PF | FR-PF | 26 / 16 / 16 (variant 8) | 13 / 5 / 5 (variant 2) |
| FR-AF | FR-AF-1 | 44 / 32 / 18 | 32 / 21 / 13 |
| FR-AF | FR-AF-2 | 40 / 20 / 14 | 40 / 19 / 13 |
| FR-AF | FR-AF-3 | 39 / 27 / 14 | 43 / 34 / 18 |
| FR-APL | FR-APL-1 | 20 / 17 / 15 | 24 / 20 / 17 |
| FR-APL | FR-APL-2 | 44 / 37 / 32 | 27 / 27 / 23 |
| FR-APL | FR-APL-3 | 24 / 16 / 15 | 36 / 36 / 30 |
| FR-APL | FR-APL-4 | 24 / 24 / 20 | 33 / 22 / 21 |
| FR-APL | FR-APL-5 | 23 / 23 / 19 | 45 / 38 / 32 |
| US-121 | US-121-1 | 7 / 3 / 3 | 24 / 18 / 18 |
| US-121 | US-121-2 | 20 / 11 / 10 | 25 / 13 / 12 |
| NZ-SLP | NZ-SLP | 16 / 0 / 0 | 16 / 0 / 0 |
| NZ-AS | NZ-AS (first: SSA 2018 formula; second: SSA 1964 formula) | 34 / 20 / 0 | 18 / 3 / 3 (default reading 2) |
| NZ-AS | NZ-AS-1964 (first, supplementary) | 18 / 3 / 3 (default reading 2) | - |
| NZ-SPS | NZ-SPS | 41 / 21 / 14 (default reading 12) | 22 / 5 / 3 (default reading 2) |

Table names with the same number do not cover the same inputs in the two conversions
(sections M6(a)); the rows pair tables only by name. The mapped-only counts reproduce the
"declared values never used" lists of every data README, with one stated exception in the
second conversion's FR-AF-1 README total (FR-AF section).

### M2 verdict on H1

With the whole suite, both H1 indicators still hold in every table except two:

* **NZ-SLP** (both conversions): 0 unused values and 0 missed valid rows with the mapped
  tests already, so the slice changes nothing.
* **First conversion's NZ-AS (SSA 2018 formula)**: with the one mapped row, 20 of 34 values
  are unused and 48,383 of 48,384 valid rows are missed; with the whole suite every
  declared value occurs and the product covers the valid space (0 and 0). All 20 values
  come from 2018-folder cases that assert other variables, plus five persons the first
  coder could not map because a case overrides an intermediate variable. This is the one
  table where the slice decides both indicators.

Every other table keeps unused values > 0 and missed valid rows > 0 (FR, US and NZ-SPS by
the margins in the tables of each section). The decision rule over samples (more than
half of the legal samples with at least one official row) therefore holds for each
conversion with the whole suite as it does with the mapped tests: first conversion 12 of
the 14 sample tables keep both indicators (all but NZ-SLP and NZ-AS); second conversion
13 of 14 (all but NZ-SLP). The supplementary NZ-AS-1964 keeps both. The drop in unused
values is largest where the dropped tests had other periods or other household shapes
(FR-AF: 6 to 16 values) and small where the dropped tests repeat the mapped household
(FR-APL: 1 to 6; US-121: 0 or 1). The values that stay unused are values that no official
test sets at all (for example any earlier §121 sale, any non-parent person in charge,
residences outside Métropole and La Réunion for FR-APL).

### M6: agreement of the two conversions

| Rule | Row-level comparison | Result |
|---|---|---|
| FR-PF | common refinement (1,080 cells) and both directions | 0 output disagreements; 540 cells EXCLUDED by the first coder only |
| FR-AF | 5 overlapping slices, both directions | 0 disagreements in 4 slices; FR-AF-2 pair: 336 (A) and 160 (B), one cause (same-band birth order) |
| FR-APL | 7 pairs of tables | complete agreement in 6; logement-foyer pair: 736 rows excluded by the first coder only, 114 Mayotte rows differ by the fixed applicant nationality |
| US-121 | 2 pairs | complete agreement (400 and 864 rows) |
| NZ-SLP | all 256 rows | 224 agree; the 32 rows the first coder excluded are 29 False and 3 True in the second |
| NZ-AS (SSA 1964) | all 512 rows (first coder's supplementary table) | complete agreement, exclusions included |
| NZ-SPS | 2,048 comparable one-child rows | 1,792 agree; 256 excluded by the first coder only (63 True in the second, by the encoding's precedence defect) |

No pair shows two valid rows with different outputs except where a stated difference in
fixed inputs or input representation explains it. The differences between the two ground
truths are differences of valid space (which rows each coder excluded) and of fixed
inputs.

### Findings for the author (affect the existing records)

1. NZ-SLP first conversion, `paperc-data-nz:paperC/specs/NZ-SLP/CONVERSION.md:16`: the
   claim that the 32 SLP-X1 rows "would be False in any case" is wrong for 3 rows, which the
   s 40 carer route makes True.
2. US-121-2 second conversion: the exclusion predicate leaves 2,688 single and
   surviving-spouse rows with a partly filled person 2 in the valid space (its description
   at `paperc-code2-fr2:paperC/specs2/US-121-2/CONVERSION_2.md:81-84` says they are removed).
   Of its 744 labelled valid rows, 72 describe a well-formed return.
3. NZ-SPS second conversion: its oracle reads only `sole_parent_support__entitled.yaml`
   (`paperc-code2-nz:paperC/specs2/NZ-SPS/oracle.py:22`) and skips
   `sole_parent_support__benefit.yaml`, whose 6 cases (12 person-values) assert the entry
   variable, 3 at the table's own week.
4. FR-AF second conversion: `README-FR-CODE2.md:77` gives FR-AF-1 34 declared values; its
   spec declares 32.
5. US-121 second conversion: the line references to `section_121.catala_en` (aggregation
   at 205-222, comparisons at 224-240) do not match commit `2694b17` (179-191, 196-205); the
   quoted content matches.

## French family benefits: FR-PF and FR-AF (both conversions)

Scripts: `paperC/analysis/m2_fr_af.py` (writes `out/m2_fr_af.json`) and
`paperC/analysis/m6_fr_af.py` (writes `out/m6_fr_af.json`), both run with `python3.12 -I`
from the repository root after `paperC/analysis/fetch_sources.sh`. Branch commits read:
`origin/paperc-data-fr` 0aee62d (first conversion), `origin/paperc-code2-fr` c957417
(second conversion). Official tests: catala-examples 2694b17,
`allocations_familiales/tests/tests_ouverture_droits.catala_fr` (scope Test1, lines 61-67,
four `droit_ouvert` assertions) and `tests_allocations_familiales.catala_fr` (Test1-Test14,
one amount assertion each). The test files are parsed by `m2_fr_af.py` (`pf_children`,
`af_tests`); the parsed inputs equal the hand copies in the second coder's `oracle.py`.

### M2. Official tests and declared values

#### Suites and mapped tests

| Rule | Suite | Cases |
|---|---|---:|
| FR-PF (`PrestationsFamiliales.droit_ouvert`) | tests_ouverture_droits Test1, one case per asserted child | 4 |
| FR-AF (`InterfaceAllocationsFamiliales.i_montant_versé`) | tests_allocations_familiales Test1-Test14 | 14 |

Both conversions map all 4 FR-PF cases. The FR-AF tests mapped are: first conversion
FR-AF-1 Test2, Test3, Test5; FR-AF-2 Test4, Test6, Test9, Test10; FR-AF-3 Test2. Second
conversion FR-AF-1 Test3, Test5; FR-AF-2 Test4, Test6, Test9, Test10; FR-AF-3 Test2. No FR-AF
test is mapped onto any table by either conversion when its date lies outside
2020-04-01..2020-12-31, which removes six tests (Test7, 8, 11, 12, 13, 14) from every table.

Unmapped household tests. Each cell gives every reason category that applies (computed by
`categories()` in `m2_fr_af.py`) and the line of the conversion record that states the
conversion's own reason. "period" = other period; "shape" = other household shape (number of
children outside the table's range); "fixed input" = an input that the table fixes lies outside
the fixed value's band (classified as "other" in the task's terms). No FR-AF test is of another
output or scope.

First conversion (stated lines in `paperc-data-fr:paperC/specs/<table>/CONVERSION.md`):

| Test (line) | date | children | FR-AF-1 | FR-AF-2 | FR-AF-3 |
|---|---|---:|---|---|---|
| Test1 (:66) | 2020-05-01 | 4 | shape; fixed input (stated: line 62) | shape (stated: line 73) | shape; fixed input (stated: line 73) |
| Test2 (:80) | 2020-05-01 | 3 | mapped | shape (stated: line 74) | mapped |
| Test3 (:94) | 2020-05-01 | 1 | mapped | shape (stated: line 75) | shape; fixed input (stated: line 74) |
| Test4 (:107) | 2020-05-01 | 2 | fixed input (stated: line 63) | mapped | shape; fixed input (stated: line 75) |
| Test5 (:120) | 2020-05-01 | 1 | mapped | shape (stated: line 76) | shape (stated: line 76) |
| Test6 (:132) | 2020-05-01 | 2 | fixed input (stated: line 64) | mapped | shape; fixed input (stated: line 77) |
| Test7 (:163) | 2021-02-01 | 4 | period; shape; fixed input (stated: line 65) | period; shape (stated: line 77) | period; shape; fixed input (stated: line 78) |
| Test8 (:176) | 2021-01-01 | 2 | period (stated: line 66) | period (stated: line 78) | period; shape; fixed input (stated: line 79) |
| Test9 (:206) | 2020-05-01 | 2 | fixed input (stated: line 67) | mapped | shape; fixed input (stated: line 80) |
| Test10 (:236) | 2020-04-20 | 2 | fixed input (stated: line 68) | mapped | shape; fixed input (stated: line 81) |
| Test11 (:266) | 2021-12-31 | 3 | period (stated: line 69) | period; shape (stated: line 79) | period (stated: line 82) |
| Test12 (:304) | 2019-08-26 | 4 | period; shape (stated: line 70) | period; shape; fixed input (stated: line 80) | period; shape; fixed input (stated: line 83) |
| Test13 (:351) | 2019-08-26 | 1 | period (stated: line 71) | period; shape (stated: line 81) | period; shape; fixed input (stated: line 84) |
| Test14 (:373) | 2022-05-01 | 2 | period; fixed input (stated: line 72) | period (stated: line 82) | period; shape; fixed input (stated: line 85) |

Second conversion (stated lines in `paperc-code2-fr:paperC/specs2/<table>/CONVERSION_2.md`):

| Test (line) | date | children | FR-AF-1 | FR-AF-2 | FR-AF-3 |
|---|---|---:|---|---|---|
| Test1 (:66) | 2020-05-01 | 4 | shape (stated: line 295) | shape (stated: line 301) | shape; fixed input (stated: line 292) |
| Test2 (:80) | 2020-05-01 | 3 | shape (stated: line 296) | shape (stated: line 302) | mapped |
| Test3 (:94) | 2020-05-01 | 1 | mapped | shape (stated: line 303) | shape (stated: line 293) |
| Test4 (:107) | 2020-05-01 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test5 (:120) | 2020-05-01 | 1 | mapped | shape (stated: line 303) | shape (stated: line 293) |
| Test6 (:132) | 2020-05-01 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test7 (:163) | 2021-02-01 | 4 | period; shape (stated: line 295) | period; shape (stated: line 301) | period; shape; fixed input (stated: line 292) |
| Test8 (:176) | 2021-01-01 | 2 | period; shape (stated: line 297) | period (stated: line 304) | period; shape (stated: line 293) |
| Test9 (:206) | 2020-05-01 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test10 (:236) | 2020-04-20 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test11 (:266) | 2021-12-31 | 3 | period; shape (stated: line 296) | period; shape (stated: line 302) | period (stated: line 294) |
| Test12 (:304) | 2019-08-26 | 4 | period; shape (stated: line 295) | period; shape (stated: line 301) | period; shape (stated: line 292) |
| Test13 (:351) | 2019-08-26 | 1 | period (stated: line 298) | period; shape (stated: line 303) | period; shape (stated: line 293) |
| Test14 (:373) | 2022-05-01 | 2 | period; shape (stated: line 297) | period (stated: line 305) | period; shape; fixed input (stated: line 293) |

Tests that the period alone keeps out (every other condition of the table holds): first
conversion FR-AF-1 Test8, Test11, Test13; FR-AF-2 Test8, Test14; FR-AF-3 Test11. Second
conversion FR-AF-1 Test13; FR-AF-2 Test8, Test14; FR-AF-3 Test11. Where several reasons
apply, the conversions state one: the first names the period first (for example Test7,
FR-AF-1 line 65), the second names the number of children first (Test7, Test12).

The second coder's README counts 18 cases for the French rules (the 4 FR-PF children plus
the 14 household tests, `paperc-code2-fr:paperC/specs2/README-FR-CODE2.md:52`); here each
rule's suite holds only the tests of its own scope, so FR-PF has 4 and FR-AF has 14.

#### Declared-value usage, mapped tests against the whole suite

"Whole suite" places every test of the rule on the table's attributes with the table's own
labels and 2020-05-01 cut points, whatever its date, household shape or fixed inputs
(placement rules in Judgements 2-7). `missed_valid` is the number of valid rows outside the
product of the values observed (protocol C1).

| Conversion | Table | Suite | Mapped | Declared values | Unused (mapped) | Unused (whole suite) | missed_valid, mapped | missed_valid, whole suite | valid rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| first | FR-PF | 4 | 4 | 26 | 16 | 16 | 1 074 | 1 074 | 1 080 |
| first | FR-AF-1 | 14 | 3 | 44 | 32 | 18 | 138 224 | 136 000 | 138 240 |
| first | FR-AF-2 | 14 | 4 | 40 | 20 | 14 | 131 148 | 126 156 | 132 300 |
| first | FR-AF-3 | 14 | 1 | 39 | 27 | 14 | 175 615 | 175 232 | 175 616 |
| second | FR-PF | 4 | 4 | 13 | 5 | 5 | 66 | 66 | 72 |
| second | FR-AF-1 | 14 | 2 | 32 | 21 | 13 | 19 436 | 19 152 | 19 440 |
| second | FR-AF-2 | 14 | 4 | 40 | 19 | 13 | 195 678 | 186 462 | 196 830 |
| second | FR-AF-3 | 14 | 1 | 43 | 34 | 18 | 174 959 | 173 232 | 174 960 |

FR-PF variant (stated as a variant: the 14 household tests compute `droit_ouvert` for each
of their children inside the household amount and never assert it). Adding the 33 children
of the 14 household tests, with `obligation_scolaire` derived as the wrapper derives it
(catala-examples `allocations_familiales/epilogue.catala_fr:121-131`):

| Conversion | Declared | Unused (4 asserted children) | Unused (with the 33 household children) | missed_valid | valid rows |
|---|---:|---:|---:|---:|---:|
| first | 26 | 16 | 8 | 952 | 1 080 |
| second | 13 | 5 | 2 | 48 | 72 |

Values still unused in the variant: first FR-PF residence Martinique, LaReunion,
SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon; prise_en_charge
ServicesSociauxAllocationVerseeALaFamille; remuneration eq_plafond; apl true. Second FR-PF
remuneration_mensuelle entre_plafonds; aide_logement_personnelle true.

Per attribute (UNKNOWN = number of suite tests that cannot be placed on the attribute; in
every case the cause is a table slot with no child in the test, since every test sets every
input of its children and household):

**First FR-PF** (whole suite equals the mapped set): unused residence Guadeloupe, Guyane,
Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte;
obligation_scolaire Avant; prise_en_charge GardeAlterneePartageAllocations,
GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille,
ServicesSociauxAllocationVerseeAuxServicesSociaux; age a00_03; remuneration eq_plafond; apl true.

**First FR-AF-1**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 9 | Guadeloupe, Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte | Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon | 0 |
| ressources | 5 | eq_plafond_I, eq_plafond_II, gt_plafond_II | eq_plafond_I, eq_plafond_II, gt_plafond_II | 0 |
| avait_enfant_avant_2012 | 2 | true | none | 0 |
| est_parent | 2 | false | false | 0 |
| titre_I | 2 | true | true | 0 |
| enfant1_age | 8 | absent, a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | absent, a00_03, a19_20, a20_plus | 0 |
| enfant2_age | 8 | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | a19_20 | 0 |
| enfant3_age | 8 | a00_03, a03_11, a11_14, a14_16, a16_19, a19_20 | a00_03, a03_11, a19_20 | 0 |

**First FR-AF-2**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 9 | Guyane, Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte | Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon | 0 |
| ressources | 3 | gt_plafond_II | gt_plafond_II | 0 |
| enfant1_age | 7 | a00_03, a14_16, a19_20, a20_plus | a00_03, a19_20, a20_plus | 0 |
| enfant1_remuneration | 2 | none | none | 0 |
| enfant1_prise_en_charge | 5 | GardeAlterneePartageAllocations, GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille | the same three | 0 |
| enfant2_age | 7 | a14_16, a19_20, a20_plus | a19_20 | 3 |
| enfant2_remuneration | 2 | none | none | 3 |
| enfant2_prise_en_charge | 5 | GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille | ServicesSociauxAllocationVerseeALaFamille | 3 |

**First FR-AF-3** (residence and resources are fixed and not counted)

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| enfant1_age | 7 | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | a00_03, a19_20, a20_plus | 0 |
| enfant1_remuneration | 2 | gt_plafond | none | 0 |
| enfant1_deja_ouvert | 2 | false | false | 0 |
| enfant1_apl | 2 | true | true | 0 |
| enfant2_age | 7 | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | a19_20 | 3 |
| enfant2_remuneration | 2 | gt_plafond | none | 3 |
| enfant2_deja_ouvert | 2 | false | false | 3 |
| enfant2_apl | 2 | true | true | 3 |
| enfant3_age | 7 | a00_03, a03_11, a11_14, a14_16, a16_19, a19_20 | a00_03, a03_11, a19_20 | 9 |
| enfant3_remuneration | 2 | gt_plafond | gt_plafond | 9 |
| enfant3_deja_ouvert | 2 | false | false | 9 |
| enfant3_apl | 2 | true | true | 9 |

**Second FR-PF** (whole suite equals the mapped set): unused residence drom_l751_1, mayotte;
obligation_scolaire Avant; remuneration_mensuelle entre_plafonds; aide_logement_personnelle true.

**Second FR-AF-1**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 3 | mayotte | none | 0 |
| attributaire | 3 | tiers_titre_I, aucun | tiers_titre_I, aucun | 0 |
| ressources | 5 | entre_plafonds_I_II, zone_degressive_II, au_dela_plafond_II | zone_degressive_II, au_dela_plafond_II | 0 |
| avant_2012 | 2 | true | none | 0 |
| e1_age | 9 | moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus | moins_3, anniversaire_16, 19_20, 20_23, 23_plus | 0 |
| e1_remuneration | 3 | entre_plafonds, au_dessus_plafonds | entre_plafonds | 0 |
| e1_prise_en_charge | 3 | partagee, services_sociaux | partagee | 0 |
| e1_deja_ouvert | 2 | false | false | 0 |
| e1_aide_logement | 2 | true | true | 0 |

**Second FR-AF-2**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 3 | mayotte | none | 0 |
| ressources | 5 | zone_degressive_I, zone_degressive_II, au_dela_plafond_II | zone_degressive_II, au_dela_plafond_II | 0 |
| avant_2012 | 2 | true | none | 0 |
| e1_age | 9 | moins_3, 14_16, anniversaire_16, 19_20, 20_23, 23_plus | moins_3, anniversaire_16, 19_20, 20_23, 23_plus | 0 |
| e1_remuneration | 3 | entre_plafonds | entre_plafonds | 0 |
| e1_prise_en_charge | 3 | partagee | partagee | 0 |
| e2_age | 9 | 14_16, anniversaire_16, 19_20, 20_23, 23_plus | 14_16, 19_20, 23_plus | 3 |
| e2_remuneration | 3 | entre_plafonds | entre_plafonds | 3 |
| e2_prise_en_charge | 3 | none | none | 3 |

**Second FR-AF-3**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 3 | drom_l751_1, mayotte | none | 0 |
| ressources | 5 | zone_degressive_I, entre_plafonds_I_II, zone_degressive_II, au_dela_plafond_II | zone_degressive_II, au_dela_plafond_II | 0 |
| avant_2012 | 2 | true | none | 0 |
| e1_age | 9 | moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus | moins_3, anniversaire_16, 19_20, 20_23, 23_plus | 0 |
| e1_deja_ouvert | 2 | false | false | 0 |
| e2_age | 9 | moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus | 14_16, 19_20, 23_plus | 3 |
| e2_deja_ouvert | 2 | false | false | 3 |
| e3_age | 9 | moins_3, 3_11, 11_14, 14_16, anniversaire_16, 16_19, 19_20, 23_plus | moins_3, 3_11, anniversaire_16, 19_20, 23_plus | 9 |
| e3_deja_ouvert | 2 | false | false | 9 |

Values that no official test reaches under any placement, in both conversions: a child aged
19 to 20 (`a19_20` / `19_20`, the forfaitaire window), a child under 3 in the first slot,
earnings exactly at the ceiling (first FR-PF), personal housing aid true, `déjà ouvert` false,
a person in charge who is not a parent (first `est_parent` false, `titre_I` true; second
`tiers_titre_I`), and resources above plafond II (in the second conversion both bands above plafond II,
`zone_degressive_II` and `au_dela_plafond_II`). Every test sets `déjà ouvert` vrai and housing aid faux.

Checks:
* Placing the mapped tests with the placement code reproduces every row of each
  `official_examples.csv` (12 first-conversion rows, 11 second-conversion rows; flag
  `placement_equals_mapped` in the JSON).
* The number of children with `droit_ouvert` computed by the three rules agrees with the
  encoding's own count for all 14 household tests.
* Shifting each test's children to 2020-05-01 at equal ages (Judgement 4) changes no age band
  of either conversion (0 mismatches over the 33 children).
* The mapped-only unused values equal, attribute by attribute, the lists in
  `paperc-data-fr:paperC/specs/README-FR.md:66` and
  `paperc-code2-fr:paperC/specs2/README-FR-CODE2.md` (sections from line 69). One discrepancy
  in the second README: its heading `FR-AF-1 (21 of 34 attribute values)`
  (`README-FR-CODE2.md:77`) gives 34 declared values; the spec declares 3+3+5+2+9+3+3+2+2 = 32,
  and the 21 listed values are right.

#### H1 with the whole suite

H1's indicators per table: (1) unused declared values > 0; (2) `missed_valid` > 0.

| Conversion | Table | (1) mapped | (1) whole suite | (2) mapped | (2) whole suite |
|---|---|---|---|---|---|
| first | FR-PF | yes (16) | yes (16; variant 8) | yes | yes (variant yes, 952) |
| first | FR-AF-1 | yes (32) | yes (18) | yes | yes |
| first | FR-AF-2 | yes (20) | yes (14) | yes | yes |
| first | FR-AF-3 | yes (27) | yes (14) | yes | yes |
| second | FR-PF | yes (5) | yes (5; variant 2) | yes | yes (variant yes, 48) |
| second | FR-AF-1 | yes (21) | yes (13) | yes | yes |
| second | FR-AF-2 | yes (19) | yes (13) | yes | yes |
| second | FR-AF-3 | yes (34) | yes (18) | yes | yes |

Both indicators hold for every French family-benefit table of both conversions when the whole
suite is used. Using the whole suite lowers the unused count of an FR-AF table by 6 to 16 values (first
FR-AF-1 by 14, FR-AF-2 by 6, FR-AF-3 by 13; second FR-AF-1 by 8, FR-AF-2 by 6, FR-AF-3 by 16)
and leaves the FR-PF counts unchanged; the values that remain unused are values that no
official test sets (list above). The share of valid rows outside the product of observed
values falls from 99.1-100 % to 94.7-99.8 % for the FR-AF tables (lowest: second FR-AF-2,
186 462 of 196 830; first FR-AF-2, 126 156 of 132 300) and stays at 99.4 % (first) and
91.7 % (second) for FR-PF.

### M6. Agreement between the two conversions

#### M6 (a) Attribute-level alignment

Tables are paired by household shape: first FR-AF-1 (0-3 children) contains the shapes of all
three second tables; first FR-AF-2 and second FR-AF-2 both have exactly 2 children; first
FR-AF-3 (exactly 3 children, Métropole, 30 000 EUR) is a slice of second FR-AF-3.

FR-PF:

| Encoding input | First conversion | Second conversion | Nesting | Sources |
|---|---|---|---|---|
| date_courante | fixed 2020-05-01 | fixed 2020-05-01 | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:101; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:113 |
| résidence | attribute, 9 collectivités | attribute, 3 classes: metropole = Métropole + SaintPierreEtMiquelon; drom_l751_1 = the 6 L751-1 territories; mayotte | first refines second | paperc-data-fr:paperC/specs/FR-PF/spec.json:21; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:50 |
| obligation_scolaire | attribute Avant / Pendant / Apres | attribute Avant / Pendant / Apres | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:28; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:40 |
| date_de_naissance | attribute `age`, cuts at 3, 16 and 20 years | attribute `age_20_ans`, cut at 20 years | first refines second (same strict comparison at 20) | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:59; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:110 |
| rémuneration_mensuelle | attribute, 3 bands relative to the residence's ceiling: below, equal to, above 943,02 EUR (Mayotte 711,49 EUR) | attribute, 3 absolute bands: [0; 711,49], (711,49; 943,02], above 943,02 EUR | cross: the first isolates the ceiling point of each residence; the second cuts at both ceilings for every residence | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:83; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:57 |
| prise_en_charge | attribute, 5 values (read by no rule of droit_ouvert) | fixed EffectiveEtPermanente | first varies, second fixes | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:52; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:97 |
| a_déjà_ouvert_droit_aux_allocations_familiales | fixed vrai | fixed vrai | coincide | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:98; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:121 |
| bénéficie_titre_personnel_aide_personnelle_logement | attribute `apl` | attribute `aide_logement_personnelle` | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:68; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:83 |
| identifiant | fixed 1 | fixed 1 | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:102; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:125 |
| exclusions | X1-X3, obligation_scolaire against the 3-, 16- and 20-year bands (2 160 of 3 240 rows) | X-PF-SCOL, Avant or Pendant at 20 or more (36 of 108 rows) | the first's exclusions contain the second's; the first also excludes Avant from age 3, Pendant under 3 or from 16, Apres under 16, which a single cut at 20 cannot express | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:103; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:119 |

FR-AF (the source line of each row, in each conversion's spec.json or conversion record, is in `out/m6_fr_af.json`, key `alignment`):

| Encoding input | First conversion | Second conversion | Nesting |
|---|---|---|---|
| date_courante | fixed 2020-05-01 | fixed 2020-05-01 | coincide |
| number of children | FR-AF-1: 0-3 (`absent` slots); FR-AF-2: 2; FR-AF-3: 3 | FR-AF-1: 1; FR-AF-2: 2; FR-AF-3: 3 | first FR-AF-1 covers the 1-, 2- and 3-child shapes; 0 children only in the first |
| i_résidence | 9 values (FR-AF-1, FR-AF-2); fixed Métropole (FR-AF-3) | 3 classes (all tables) | first refines second where both vary |
| i_ressources_ménage | FR-AF-1: below pI, = pI, between, = pII, above pII; FR-AF-2: <= pI, (pI; pII], > pII; FR-AF-3: fixed 30 000 EUR. pI = 57 759 + 5 775 n EUR, pII = 80 831 + 5 775 n EUR, n = children with droit_ouvert | 5 bands in all tables: <= pI, (pI; pI + 12a], (pI + 12a; pII], (pII; pII + 12a], > pII + 12a, a = the allocation the encoding computes | cross: both cut at pI and pII; the second adds the complément dégressif cuts pI + 12a and pII + 12a; the first FR-AF-1 isolates the points pI and pII. The second's 5 bands refine the first FR-AF-2's 3 |
| est_parent, remplit_titre_I | two attributes in FR-AF-1 (both false = REJECTED); fixed (vrai, faux) elsewhere | one attribute `attributaire` in FR-AF-1: parent (vrai, faux), tiers_titre_I (faux, vrai), aucun (EXCLUDED); (vrai, vrai) has no label of its own; fixed parent elsewhere | first refines second ((vrai, vrai) is its own cell in the first) |
| avait_enfant_à_charge_avant_1er_janvier_2012 | attribute (FR-AF-1); fixed faux (FR-AF-2, FR-AF-3) | attribute (all tables) | coincide where both vary |
| per-child date_de_naissance | 7 bands: a00_03, a03_11, a11_14, a14_16 (from the 14th birthday to the 16th birthday inclusive), a16_19, a19_20, a20_plus; slot k is k - 1 days younger than slot 1 | 9 bands: moins_3, 3_11, 11_14, 14_16 (16th birthday excluded), anniversaire_16 (the 16th birthday itself), 16_19, 19_20, 20_23, 23_plus (born on or before 1997-04-30); every slot uses the band's single representative | second refines first: a14_16 = 14_16 + anniversaire_16, a20_plus = 20_23 + 23_plus, the other bands coincide |
| per-child rémuneration | fixed 0 EUR (FR-AF-1); <= the residence's ceiling / above (FR-AF-2, FR-AF-3) | [0; 711,49], (711,49; 943,02], above (FR-AF-1, FR-AF-2); fixed 0 EUR (FR-AF-3) | second refines first (the first's cut is 711,49 in Mayotte and 943,02 elsewhere, both cuts of the second) |
| per-child prise_en_charge | fixed EffectiveEtPermanente (FR-AF-1, FR-AF-3); 5 values (FR-AF-2) | 3 classes complete / partagee / services_sociaux (FR-AF-1, FR-AF-2); fixed EffectiveEtPermanente (FR-AF-3) | first refines second where both vary |
| per-child a_déjà_ouvert | fixed vrai (FR-AF-1, FR-AF-2); attribute (FR-AF-3) | attribute (FR-AF-1, FR-AF-3); fixed vrai (FR-AF-2) | coincide where both vary |
| per-child housing aid | fixed faux (FR-AF-1, FR-AF-2); attribute (FR-AF-3) | attribute (FR-AF-1); fixed faux (FR-AF-2, FR-AF-3) | never varied by both in tables of the same shape |
| d_identifiant | fixed 0, 1, 2 in list order | fixed 1, 2, 3 in list order | coincide in effect |
| output | FR-AF-1, FR-AF-2: zero, general_t1-3, outre_mer_1_enfant, mayotte; FR-AF-3: zero, base, base_majoration, base_forfaitaire, base_majoration_forfaitaire | sans_droit or bareme/tier/parts (19, 54, 62 labels) | second refines first: each second label maps onto one first label (`coarsen` in m6_fr_af.py) |

#### M6 (b, c) Row-level agreement

Method (`m6_fr_af.py`): direction A takes every row of the first table's slice, builds its
concrete inputs from the first coder's representatives, labels those inputs with the second
coder's cut points (the second's resource band through the encoding, since it depends on the
computed allocation), and compares the first ground truth with the second ground truth of that
row after coarsening the second label. Direction B does the same from the second table. Inputs
that one table fixes are restricted to the fixed value on the other side. The first coder's
representatives, run through the encoding, reproduce the first ground truth on every compared
row (0 failures).

Output coarsening (exact, since both labels are read from the same encoding result):
sans_droit and every `.../nul` -> zero; mayotte and mayotte_avant_2012 -> mayotte;
outre_mer_un_enfant -> outre_mer_1_enfant; general/Tk -> general_tk. For first FR-AF-3:
general/T1/B -> base, B+M -> base_majoration, B+F -> base_forfaitaire, B+M+F ->
base_majoration_forfaitaire.

| Pair | First slice | Second slice | Direction A rows: agree / disagree / invalid on a side | Direction B rows: agree / disagree / invalid on a side |
|---|---|---|---|---|
| FR-PF | prise_en_charge EffectiveEtPermanente (648 of 3 240 rows) | all 108 rows | 216 / 0 / 432 (first EXCLUDED: 324 with the second valid, 108 with the second EXCLUDED) | 36 / 0 / 72 (36 second valid with the first EXCLUDED, 36 both EXCLUDED) |
| P1 | FR-AF-1, one child in slot 1 | FR-AF-1, child earnings jusqu_plafond_mayotte, care complete, déjà ouvert true, housing aid false | 1 890 / 0 / 630 (first REJECTED, second EXCLUDED) | 540 / 0 / 270 (second EXCLUDED, first REJECTED) |
| P2 | FR-AF-1, two children in slots 1-2, parent | FR-AF-2, both children earnings jusqu_plafond_mayotte, care complete | 4 410 / 0 / 0 | 2 430 / 0 / 0 |
| P3 | FR-AF-1, three children, parent | FR-AF-3, déjà ouvert true for all | 30 870 / 0 / 0 | 21 870 / 0 / 0 |
| P4 | FR-AF-2, all rows | FR-AF-2, avant_2012 false | 131 964 / 336 / 0 | 98 255 / 160 / 0 |
| P5 | FR-AF-3, earnings le_plafond and housing aid false for all | FR-AF-3, metropole, jusqu_plafond_I, avant_2012 false | 2 744 / 0 / 0 | 5 832 / 0 / 0 |

FR-PF on the common refinement (residence 9 x obligation 3 x birth date on each side of 3,
16, 20 years x earnings 0 / 711,49 / 800 / 943,02 / 1 000 EUR x housing aid 2, care
EffectiveEtPermanente; 1 080 cells, each labelled into both tables): 360 agree, 0 disagree,
540 first EXCLUDED with the second valid, 180 EXCLUDED in both.

Explanation of every non-agreement:

1. **FR-PF, invalid on one side (direction A 324 rows, direction B 36 rows, common refinement
   540 cells).** All come from the exclusions. The first coder's X1-X3 use the 3- and 16-year
   cuts; the second coder has no such cut and excludes only Avant or Pendant at 20 or more.
   A second-coder row such as (Avant, moins_20) covers children under 3 (valid in the first)
   and children aged 3 to 19 (X1 in the first). In direction B, the second's representative of
   `moins_20` is born 2005-01-01 (aged 15), so its 36 (Avant, moins_20) and (Apres, moins_20)
   rows fall into the first's X1 and X3. On the outputs where both sides are valid there is no
   disagreement.
2. **FR-AF P1, invalid on both sides (630 and 270 rows).** The household where the person in
   charge is neither a parent nor meets Title I: REJECTED by the first coder (the encoding's
   L521-2 assertion fails, `paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:139`) and EXCLUDED
   by the second (`attributaire = aucun`, X-AF-ATTRIB, `paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:142`). Both sides keep the row out of the valid
   space; the conversions differ only in the status they give it.
3. **FR-AF P4, 336 (direction A) and 160 (direction B) disagreements, one cause.** In every
   disagreeing row the two children lie in the same first-coder age band (`a16_19` or `a19_20`),
   one child has `droit_ouvert` with its share paid to the services sociaux, and the other has
   earnings above the ceiling (no `droit_ouvert`). Re-evaluating the encoding with one input
   group swapped at a time, the only input whose swap flips the label is a child's birth date.
   The first coder makes slot 1 one day older than slot 2
   (`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:181`); the second gives both children
   the band's single representative date, and with equal dates the encoding treats the last
   child in list order as the eldest
   (`paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:171`). The eldest child is left out
   of the L521-3 al. 1 majoration, so which child is the eldest decides whether the
   non-entitled child adds a majoration: the amount is positive (outre_mer_1_enfant or mayotte)
   on one side and zero on the other. The first coder recorded the same effect in its own
   robustness check (`paperc-data-fr:paperC/specs/FR-AF-2/CONVERSION.md:39`). Groups:

   | Direction | Count | Residence | First output | Second output (coarsened) | Example (first row) |
   |---|---:|---|---|---|---|
   | A | 144 | L751-1 | outre_mer_1_enfant | zero | Guadeloupe, le_plafond_I, child 1 a16_19 le_plafond ServicesSociauxAllocationVerseeAuxServicesSociaux, child 2 a16_19 gt_plafond GardeAlterneePartageAllocations -> second outre_mer_un_enfant/nul |
   | A | 144 | L751-1 | zero | outre_mer_1_enfant | the same with the two children swapped -> second outre_mer_un_enfant/M |
   | A | 24 | Mayotte | mayotte | zero | Mayotte, the same children as the first example -> mayotte/T1/nul |
   | A | 24 | Mayotte | zero | mayotte | swapped -> mayotte/T1/M |
   | B | 40 | L751-1 | outre_mer_1_enfant | zero | second drom_l751_1, jusqu_plafond_I, 16_19 jusqu services_sociaux + 16_19 au_dessus complete (outre_mer_un_enfant/nul) -> first outre_mer_1_enfant |
   | B | 40 | L751-1 | zero | outre_mer_1_enfant | swapped (outre_mer_un_enfant/M) -> first zero |
   | B | 40 | Mayotte | mayotte | zero | mayotte, the same children (mayotte/T1/nul) -> first mayotte |
   | B | 40 | Mayotte | zero | mayotte | swapped (mayotte/T1/M) -> first zero |

   Each line of this table joins two groups of equal size, one with both children in
   `a16_19` and one with both in `a19_20` (72 + 72, 12 + 12, 20 + 20); the JSON lists every
   group with its row shapes (`shapes`) and one example. In every disagreeing row the entitled
   child has earnings `le_plafond` and care ServicesSociauxAllocationVerseeAuxServicesSociaux,
   and the other child has earnings `gt_plafond` with any other care arrangement. This is a property of the representatives: the age bands of
   both conversions leave the birth order of two same-band children open, and each coder closed
   it differently.

No other disagreement occurs: 0 in P1, P2, P3 and P5 in either direction, and 0 output
disagreements in FR-PF.

Where no row comparison was made, and why: the first FR-AF-1 rows with an `absent` slot
before a present one (they repeat a household of the canonical rows,
`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:25`); the first FR-AF-1 rows with no
child (no second-coder table); the first FR-AF-1 rows with est_parent and titre_I both true in
P2 and P3 (the second fixes (vrai, faux) there); first FR-PF rows with a prise_en_charge other
than EffectiveEtPermanente and first FR-AF-2 rows against second FR-AF-2 rows with avant_2012
true (each fixed on the other side); first FR-AF-3 rows with child earnings above the ceiling
or housing aid (fixed in the second FR-AF-3); and second-coder rows outside each slice.

### Judgements

1. **Suites.** FR-PF: the four asserted children of `tests_ouverture_droits.catala_fr` Test1
   (lines 61-67). FR-AF: the 14 household tests. The second README's count of 18 cases mixes
   both scopes (`paperc-code2-fr:paperC/specs2/README-FR-CODE2.md:52`).
2. **Ages at the test's own date.** Every age band is evaluated against the test's own
   `date_courante`, as both conversions do for Test10
   (`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:109`;
   `paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:36`).
3. **2020-05-01 cut points for every test.** Child earnings are cut at 943,02 / 711,49 EUR and
   household resources at the 2020 D521-3 ceilings (formula in
   `paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:148`) whatever the test's date; n
   (children with droit_ouvert) is computed by the three rules of droit_ouvert with
   obligation_scolaire derived as `epilogue.catala_fr:121-131` does, and checked against the
   encoding.
4. **Second coder's resource bands.** They depend on the computed allocation a
   (`paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:221`), so each test household is
   run through the unmodified Catala build (the second coder's `call_interface`) at 2020-05-01
   with its children's birth dates moved by (2020-05-01 - test date) days; this moves no child
   to another age band.
5. **Child slots in list order.** Both conversions place the test's children in list order
   (`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:198`; the second's mapped rows, for
   example Test9). When a test has more children than slots, the first k children fill the
   slots, the household attributes (resources band) use the whole household, and the extra
   children are recorded as not placed (`children_not_placed` in the JSON). When it has fewer,
   the empty slots are UNKNOWN, except in the first FR-AF-1, whose declared value `absent` is
   the label of an empty slot (`CONVERSION.md:25`).
6. **Fixed inputs are not counted.** A table's fixed inputs (for example first FR-AF-3's
   residence and resources) add no declared value; a test whose value differs from the fixed one
   is still placed on the attributes.
7. **Second coder's `attributaire`.** Every test sets est_parent and leaves titre_I faux, which
   is `parent` (`paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:137`).
8. **Reason categories.** Each unmapped test gets every category that applies (period outside
   2020-04-01..2020-12-31, number of children outside the table's range, fixed input outside
   its band), next to the single reason the conversion record states.
9. **FR-PF variant.** The 33 household children are a variant only: their `droit_ouvert` is
   computed inside the household tests and never asserted
   (`paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:121`).
10. **M6 restrictions.** Rows are compared only where the fixed inputs coincide. First
    est_parent = titre_I = true is mapped to the second's `parent`, which the second coder
    states behaves the same (`CONVERSION_2.md:137`); this pair occurs only in P1, where all its
    rows agree.
11. **M6 label mapping.** Residence by the second coder's three classes; care arrangement by
    its three classes; ages and earnings through each side's representative values; outputs by
    `coarsen`.

## FR-APL and US-121

Sources. First conversion: `origin/paperc-data-fr2` (FR-APL-1 to -5, US-121-1) and
`origin/paperc-data-fr2-fix` (US-121-2 as corrected on 2026-10-20). Second conversion:
`origin/paperc-code2-fr2`. Official tests: catala-examples `2694b17`,
`aides_logement/tests/tests_eligibilite_apl.catala_fr` (3 test scopes) and
`us_tax_code/tests/test_section_121.catala_en` (6 test scopes). Scripts:
`tests_fr2.py` (reads the tests, with the line of every value), `m2_fr2.py`,
`m6_fr2.py`; output `out/m2_fr2.json`, `out/m6_fr2.json`.

### M2. Official tests and declared values

Unit: one test scope (one taxpayer per placement in US-121-1, see J-US1). Both
conversions map whole test scopes, so the counts below are in the conversions' own unit.

| Rule | Conv. | Table | Suite tests | Mapped | Declared values | Unused, mapped tests | Unused, whole suite | Unknown placements | missed_valid, mapped | missed_valid, whole suite | Valid rows |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FR-APL | 1 | FR-APL-1 | 3 | 1 | 20 | 17 | 15 | 0 | 174 | 171 | 175 |
| FR-APL | 1 | FR-APL-2 | 3 | 1 | 44 | 37 | 32 | 0 | 67,139 | 67,116 | 67,140 |
| FR-APL | 1 | FR-APL-3 | 3 | 1 | 24 | 16 | 15 | 0 | 3,599 | 3,598 | 3,600 |
| FR-APL | 1 | FR-APL-4 | 3 | 0 | 24 | 24 | 20 | 12 | 952 | 952 | 952 |
| FR-APL | 1 | FR-APL-5 | 3 | 0 | 23 | 23 | 19 | 15 | 2,520 | 2,520 | 2,520 |
| FR-APL | 2 | FR-APL-1 | 3 | 1 | 24 | 20 | 17 | 0 | 709 | 702 | 710 |
| FR-APL | 2 | FR-APL-2 | 3 | 0 | 27 | 27 | 23 | 12 | 2,272 | 2,272 | 2,272 |
| FR-APL | 2 | FR-APL-3 | 3 | 0 | 36 | 36 | 30 | 15 | 49,500 | 49,500 | 49,500 |
| FR-APL | 2 | FR-APL-4 | 3 | 1 | 33 | 22 | 21 | 0 | 26,879 | 26,878 | 26,880 |
| FR-APL | 2 | FR-APL-5 | 3 | 1 | 45 | 38 | 32 | 0 | 30,471 | 30,424 | 30,472 |
| US-121 | 1 | US-121-1 | 6 | 4 | 7 | 3 | 3 | 0 | 2 | 2 | 4 |
| US-121 | 1 | US-121-2 | 6 | 2 | 20 | 11 | 10 | 16 | 202 | 201 | 204 |
| US-121 | 2 | US-121-1 | 6 | 4 | 24 | 18 | 18 | 0 | 96 | 96 | 100 |
| US-121 | 2 | US-121-2 | 6 | 2 | 25 | 13 | 12 | 16 | 736 | 728 | 744 |

"Unknown placements" counts (test, attribute) pairs where a test has no value for the
attribute. The mapped-only columns reproduce every list of "declared values that the
official examples never use" in `paperc-data-fr2:paperC/specs/README-FR2.md:67-97` (first conversion; the corrected US-121-2 list is unchanged in `paperc-data-fr2-fix`) and
`README-FR2-CODE2.md:80-90` (second conversion), table by table.

**Unmapped tests and reasons.**

| Conv. | Tables | Test | Category | Detail | Conversion's own statement |
|---|---|---|---|---|---|
| 1, 2 | every FR-APL table | Exemple2, Exemple3 | other output or scope | assert `ÉligibilitéAllocationLogement.éligibilité` (`tests_eligibilite_apl.catala_fr:116`, `:202`), the allocation de logement | first: `paperc-data-fr2:paperC/specs/README-FR2.md:57-58`; second: `paperc-code2-fr2:paperC/specs2/FR-APL-1/CONVERSION_2.md:59-63` |
| 1 | FR-APL-4, FR-APL-5 | Exemple1 | other: housing tenure fixed by the table | Exemple1 is a tenancy (`Locataire`, `tests_eligibilite_apl.catala_fr:71`); FR-APL-4 fixes a logement-foyer, FR-APL-5 home ownership | `paperc-data-fr2:paperC/specs/FR-APL/FR-APL-4/CONVERSION.md:83-85`, `FR-APL-5/CONVERSION.md:81-83` |
| 2 | FR-APL-2, FR-APL-3 | Exemple1 | other: housing tenure fixed by the table | as above (FR-APL-2 logement-foyer, FR-APL-3 home ownership) | `paperc-code2-fr2:paperC/specs2/README-FR2-CODE2.md:68-69` |
| 1, 2 | US-121-1 | Test5, Test6 | other output or scope | assert `Section121TwoPersons.income_excluded_from_gross_income` (`test_section_121.catala_en:139`, `:158`) | first: `paperc-data-fr2:paperC/specs/US-121/US-121-1/CONVERSION.md:104-105`; second: `paperc-code2-fr2:paperC/specs2/US-121-1/CONVERSION_2.md:95-97` |
| 1, 2 | US-121-2 | Test1-Test4 | other output or scope | assert `Section121SinglePerson.requirements_met` (`test_section_121.catala_en:79`, `:94`, `:109`, `:124`) | first: `paperc-data-fr2-fix:paperC/specs/US-121/US-121-2/CONVERSION.md:112`; second: `paperc-code2-fr2:paperC/specs2/US-121-2/CONVERSION_2.md:100-101` |

No test of these rules is unmapped for its period or household shape: every fixed date
of these tables is the date of a test, and Exemple2 and Exemple3 fall in declared date
bands where a table has a date attribute.

**What the whole suite adds** (declared values used by some unmapped test and by no
mapped test):

| Conv. | Table | Values newly used | Attributes with unknown placements |
|---|---|---|---|
| 1 | FR-APL-1 | date `2021-01-01_to_2023-12-31`; residence `LaReunion` | none |
| 1 | FR-APL-2 | residence `LaReunion`; situation `Concubins`; dependants `1`, `2`; other occupants `0` | none |
| 1 | FR-APL-3 | bailleur `BailleurPrive` | none |
| 1 | FR-APL-4 | residence `Metropole`, `LaReunion`; dates `2019-09-01_to_2020-12-31`, `2021-01-01_to_2023-04-04` | the four foyer attributes (3 tests each) |
| 1 | FR-APL-5 | zone `Zone1`, `Zone2`; date `ge_2019-10-01`; residence_principale `vrai` | mode, loan type, holder, signature date, age of dwelling (3 tests each) |
| 2 | FR-APL-1 | date `2021-05-01_to_2023-04-04`; residence `LaReunion`; bailleur `prive` | none |
| 2 | FR-APL-2 | dates `2019-10-01_to_2020-12-31`, `2021-05-01_to_2023-04-04`; residence `Metropole`, `LaReunion` | the four foyer attributes (3 tests each) |
| 2 | FR-APL-3 | the same two dates and two residences; zone `Zone1`, `Zone2` | mode, loan type, holder, signature date, age of dwelling (3 tests each) |
| 2 | FR-APL-4 | residence `LaReunion` | none |
| 2 | FR-APL-5 | residence `LaReunion`; situation `Concubins`; occupants `0`; dependants `1`, `2`; surface `58_to_60` | none |
| 1 | US-121-1 | none (Test5's and Test6's taxpayers fall in labels Test1-Test4 already use) | none |
| 1 | US-121-2 | person 1 use `lt_730_days` (Test2, Test3) | return type and the three person-2 attributes (Test1-Test4) |
| 2 | US-121-1 | none | none |
| 2 | US-121-2 | person 1 use `under_730d` (Test2, Test3) | as for the first conversion |

Read as single returns (J-US2), Test1-Test4 would lower the first conversion's
US-121-2 count to 9 unused values (missed_valid 198) and leave the second conversion's at
12 (missed_valid 728).

**H1 indicators with the whole suite.** In all 14 tables both indicators stay positive:
the whole suite leaves between 3 (first US-121-1) and 32 (first FR-APL-2, second
FR-APL-5) declared values unused, and the product of the observed values still misses
valid rows in every table (smallest case: 2 of 4 valid rows in the first US-121-1).
The largest drop in unused values is 6 (second FR-APL-3, 36 to 30; second FR-APL-5,
38 to 32). For FR-APL the reason is that the three tests share one household type (a
tenant, French applicant, Locataire of a social or private landlord, decent main
residence, no family ownership, no letting), so the slice dropped only two of them and
the two it dropped repeat most of Exemple1's values. For US-121 every test uses
`NoOtherSaleWhereSection121aApplied` (`test_section_121.catala_en:41`, `:48`, `:54`,
`:61`, `:78`, `:93`, `:108`, `:123`), so every earlier-sale label stays unused whatever
the slice.

### M6(a). Attribute-level alignment

The two coders split FR-APL differently: the first by subject with five tables (1 date,
territory and nationality; 2 floor area and household; 3 tenancy conditions;
4 logement-foyer; 5 home buyers), the second by the part of the law (1 tenancy landlord;
2 logement-foyer; 3 home ownership; 4 common conditions; 5 floor area). Every other
input is held at Exemple1's value in both conversions (first: `FR-APL-1/CONVERSION.md:82-92`;
second: `FR-APL-1/CONVERSION_2.md:42-55`), except where stated.

| Encoding input | First conversion | Second conversion | Nesting |
|---|---|---|---|
| `date_courante` | attribute in 1 (6 bands, cuts 2019-01-01, 2019-09-01, 2021-01-01, 2024-01-01, 2024-11-01; `FR-APL-1/CONVERSION.md:40-47`), 4 (5 bands from 2019-09-01, cuts 2021-01-01, 2023-04-05, 2024-01-01, 2024-11-01; `FR-APL-4/CONVERSION.md:33`), 5 (2 bands, cut 2019-10-01; `FR-APL-5/CONVERSION.md:44`); fixed 2020-03-10 in 2, 3 | attribute in 1, 2, 3 (8 bands from 2019-09-01, cuts 2019-10-01, 2021-01-01, 2021-05-01, 2023-04-05, 2023-09-01, 2024-01-01, 2024-11-01; `FR-APL-1/CONVERSION_2.md:74-84`); fixed 2020-03-10 in 4, 5 | from 2019-09-01 the second refines each first-conversion date attribute; the first adds two bands before 2019-09-01 (all REJECTED), which the second leaves outside its domain (`CONVERSION_2.md:76`) |
| `ménage.résidence` | 9 values in 1, 2, 4; fixed Métropole in 3, 5 | 9 values in 1, 2, 3; 3 values (Métropole, La Réunion, Mayotte) in 4, 5 (`FR-APL-4/CONVERSION_2.md:73-76`) | coincide where both declare 9; the second's 3 are a subset |
| `demandeur.nationalité` | 5 values (Française and the four flag pairs) in 1, 2; fixed Étrangère {vrai, vrai} in 4 (`FR-APL-4/CONVERSION.md:45-48`); fixed Française in 3, 5 | 5 values in 4; 2 values (Française, Étrangère T_T) in 5; fixed Française in 1, 2, 3 | the five labels coincide; the second's FR-APL-5 pair is a subset |
| `situation_familiale` | 6 values in 2 | 6 values in 5 | coincide |
| number of dependants | `0`-`3` in 2 (first k children of Exemple1) | `0`-`4` in 5 (first k of Exemple1, then children born 2012-01-01) | the second extends the range; equal households for k <= 3 |
| `nombre_autres_occupants_logement` | `0`, `1` in 2 | `0`-`3` in 5 | the second extends |
| `surface_m_carrés` | 16 bands, cuts 9, 13, 16, 18, 22, 25, 27, 31, 34, 36, 40, 43, 45, 49, 52 (`FR-APL-2/CONVERSION.md:52-56`) | 23 bands, the same cuts plus 54, 58, 61, 63, 67, 70, 72 (`FR-APL-5/CONVERSION_2.md:87-93`) | the second refines (its extra cuts serve households of 7 to 9 persons, which the first does not declare) |
| `personnes_âgées_handicapées_foyer_r844_4` | bool in 2 | bool in 5 | coincide |
| `logement.mode_occupation` | Locataire/SousLocataire in 3; RésidentLogementFoyer fixed in 4; AccessionPropriété/LocationAccession in 5; Locataire fixed in 1, 2 | Locataire/SousLocataire in 1; RésidentLogementFoyer fixed in 2; AccessionPropriété/LocationAccession in 3; Locataire/AccessionPropriété in 4; Locataire fixed in 5 | the same constructors, assigned to different tables |
| landlord (`TypeBailleur` with its flag) | 5 values in 3 | 5 values in 1 | coincide |
| `propriétaire`, `usufruit` (family share) | 3 values: Autre, < 10 %, >= 10 % (`FR-APL-3/CONVERSION.md:35-40`) | 4 values: autre, < 10 %, = 10 %, > 10 % (`FR-APL-4/CONVERSION_2.md:91-94`) | the second refines |
| `loué_ou_sous_loué_à_des_tiers` | one attribute, 5 values: Non; under 30 / 30 or more × L442-1 yes/no (`FR-APL-3/CONVERSION.md:41-48`) | three attributes (sublet yes/no; age sans_objet / under 30 / 30th birthday on the date / over 30; L442-1 sans_objet / yes / no) with an exclusion that removes the combinations describing no input (`FR-APL-4/CONVERSION_2.md:83-90`, `:107-109`) | the second refines (it splits "30 or more" at the 30th birthday) |
| `logement_decent_l89_462`, `condition_rattaché_foyer_fiscal_parent_ifi` | bool in 3 | bool in 4 | coincide |
| `résidence_principale` | bool in 3 and 5 | bool in 4; fixed vrai in 3 | coincide |
| foyer type and three conventions | attributes in 4 | attributes in 2 | coincide; the first declares two exclusions (`FR-APL-4/CONVERSION.md:60-65`), the second none |
| loan type, holder, signature date, age of dwelling, zone | attributes in 5; signature cuts 2017-12-31, 2018-01-01, 2020-01-01 | attributes in 3, the same cuts (`FR-APL-3/CONVERSION_2.md:105-109`) | coincide (representatives differ inside the bands) |
| loan record amounts and entry date | 500 €, entry 2010-01-01 | 700 €, entry = earlier of the signature and decision dates | fixed differently; both record them as unread by eligibility |
| foyer `date_conventionnement` | 2000-01-01 | 2010-01-01 | fixed differently; both record it as unread |
| benefits received, children's details, rent, applicant's birth date and flags | fixed at Exemple1 | fixed at Exemple1 | same fixed values |

US-121:

| Encoding input | First conversion | Second conversion | Nesting |
|---|---|---|---|
| `date_of_sale_or_exchange`, `return_date` | fixed 2021-01-01 | fixed 2021-01-01 | coincide |
| `property_ownage`, `property_usage_as_principal_residence` | 2 bands of the five-year aggregate, < 730 and >= 730 days, in both tables (`US-121-1/CONVERSION.md:25-43`) | US-121-1: 10 list shapes (`CONVERSION_2.md:41-61`); US-121-2: the two bands of the first conversion (`CONVERSION_2.md:52-56`) | US-121-1: the second refines (each shape lies on one side of 730 days); US-121-2: coincide |
| `other_section_121a_sale` | 3 values: none, 1 day to 2 years before, more than 2 years (`US-121-1/CONVERSION.md:45-57`; the same-day sale is in no label) | 4 values: none, under 2 years (2020-01-01), exactly 2 years (2019-01-01), over 2 years (`CONVERSION_2.md:34-36`) | the second's two inner values lie in the first's `within_2_years`; whether the second's `under_2_years_before` holds the same-day sale is not stated, so the two cross at that single date |
| `gain_from_sale_or_exchange_of_property` | fixed $350,000 in US-121-1; in US-121-2 3 bands (0, 250,000), [250,000, 500,000), [500,000, ∞) (`US-121-2/CONVERSION.md:50`, `:68-69`) | fixed $350,000 in US-121-1; in US-121-2 3 bands under 250,000 / 250,000 to 500,000 / over 500,000 (`CONVERSION_2.md:60-64`) | coincide apart from $0, which the first leaves out, and the boundary points, which the second does not assign |
| `return_type` | single, joint, surviving spouse | the same three | coincide |
| person 2 on a one-person return | single: the same taxpayer, other person-2 values EXCLUDED; surviving spouse: the deceased spouse's record, varied (correction, `US-121-2/CONVERSION.md:148-221`) | `not_applicable`; the deceased spouse's record fixed to `person_ok_1` (`CONVERSION_2.md:73-77`) | different representations; the scope reads neither record (`US-121-2/CONVERSION.md:204-212`) |
| `date_of_spouse_death` | fixed 2020-12-31 | fixed 2020-06-01 | fixed differently; unread by `Section121TwoPersons` |

Observation on the second conversion's US-121-2 exclusion. Its description says it removes
non-joint rows "when ... some person-2 attribute has a value"
(`paperc-code2-fr2:paperC/specs2/US-121-2/CONVERSION_2.md:81-84`), and the predicate
`(return_type == 'joint_return') == (p2_own == 'not_applicable' or p2_use == 'not_applicable' or p2_other == 'not_applicable')`
removes non-joint rows only when no person-2 attribute is `not_applicable`. The 2,688
single and surviving-spouse rows with a partly filled person 2 therefore stay in V
(672 labelled, 2,016 REJECTED; `m6_fr2.py`, pair US-121-2, "B rows without
counterpart"). They describe no return. Of the 744 labelled valid rows of that table, 72
describe a well-formed return.

Observation on line references. The second conversion cites the five-year aggregation
of `section_121.catala_en` at lines 205-222 and the 730-day comparisons at 224-240
(`US-121-1/CONVERSION_2.md:20-24`); at commit `2694b17` they are at lines 179-191 and
196-205, which the first conversion cites. The content quoted matches the code.

### M6(b-c). Row-level agreement

A pair compares a first-coder table A with a second-coder table B. Each side is
restricted to the values equal to the other side's fixed inputs, and each B row is mapped
onto the A row whose labels contain B's values (B refines A on every shared attribute
used). The output labels map one to one (`eligible`/`eligible`,
`ineligible`/`not_eligible`; `met`/`requirements_met`; `zero`/`no_exclusion`,
`full_gain`/`entire_gain`, `capped_at_250000`/`limited_to_250000`,
`capped_at_500000`/`limited_to_500000`). EXCLUDED and REJECTED are compared as labels.

| Pair | A (first) | B (second) | Restriction | B rows compared | Agree | Both valid (agree) | A rows of the slice reached |
|---|---|---|---|---|---|---|---|
| tenancy, date × territory | FR-APL-1 | FR-APL-1 | A: Française; B: Locataire, social conventionné | 72 | 72 | 71 (71) | 36 of 54 |
| nationality | FR-APL-1 | FR-APL-4 | A: date band of 2020-03-10, 3 territories; B: other attributes at Exemple1 | 15 | 15 | 15 (15) | 15 of 15 |
| floor area | FR-APL-2 | FR-APL-5 | A: 3 territories, 2 nationalities; B: occupants 0-1, dependants 0-3 | 13,248 | 13,248 | 11,784 (11,784) | 9,216 of 9,216 |
| common conditions | FR-APL-3 | FR-APL-4 | A: Locataire, social conventionné; B: Métropole, Française, Locataire | 896 | 896 | 896 (896) | 360 of 360 |
| landlord | FR-APL-3 | FR-APL-1 | A: other attributes at Exemple1; B: band of 2020-03-10, Métropole | 10 | 10 | 10 (10) | 10 of 10 |
| logement-foyer | FR-APL-4 | FR-APL-2 | none | 2,304 | 1,454 | 1,540 (1,426) | 1,440 of 1,440 |
| home buyers | FR-APL-5 | FR-APL-3 | A: main residence; B: Métropole | 5,760 | 5,760 | 5,580 (5,580) | 1,440 of 1,440 |
| §121(a) | US-121-1 | US-121-1 | none | 400 | 400 | 100 (100) | 12 of 12 |
| §121 amount | US-121-2 | US-121-2 | B rows with a well-formed person 2 | 864 | 864 | 72 (72) | 504 of 1,296 |

Agreement is complete in eight of the nine pairs, REJECTED rows included (1,464 in the
floor-area pair, 300 and 792 in the US pairs) and EXCLUDED rows included (the 180
home-buyer rows with a loan signed after the decision date, which both coders exclude by
the same rule: first `FR-APL-5/CONVERSION.md:59`, second `FR-APL-3/CONVERSION_2.md:128-132`).

Rows without a counterpart, explained:

* tenancy pair: 18 A rows (dates before 2019-09-01, all REJECTED) lie outside B's date
  domain.
* common-conditions pair: 2,176 B rows of the slice are EXCLUDED by
  `sublet_details_iff_sublet`. They are combinations of B's three sublet attributes
  that encode no input; A's single sublet attribute has no such combinations.
* §121 amount pair: B's 2,928 EXCLUDED rows and its 2,688 rows with a partly filled person
  2 on a one-person return (observation above) have no A counterpart. A's 396 single rows
  with person-2 labels different from person 1 (EXCLUDED in A) and A's 396 surviving-spouse
  rows whose deceased spouse differs from `person_ok_1` (B fixes that record) have no B
  counterpart; on these 396 surviving-spouse rows A's outputs do not depend on the
  person-2 labels (`US-121-2/CONVERSION.md:204-212`).

**Disagreements: the logement-foyer pair (850 rows).**

1. *A excludes, B evaluates: 736 rows.* A declares two exclusions and B none.
   `drom_convention_outside_drom` (a DROM convention outside the five DROM): 448 B rows
   (208 eligible, 240 ineligible). `fjt_type_without_l353_2_convention` (a young-workers
   foyer type without the livre III convention that defines it): 224 B rows (74 eligible,
   146 ineligible, 4 REJECTED). Both exclusions hold: 64 B rows (26 eligible, 38
   ineligible). A's sources: `paperc-data-fr2:paperC/specs/FR-APL/FR-APL-4/CONVERSION.md:60-65`.
   B states every combination possible (`FR-APL-2/CONVERSION_2.md:115-117`). The
   disagreement is about the valid space; the encoding returns a value for these rows.
2. *A eligible, B ineligible: 114 rows, all in Mayotte.* The fixed applicant differs:
   A fixes an Étrangère meeting both nationality conditions
   (`FR-APL-4/CONVERSION.md:45-48`), B keeps Exemple1's Française. The Mayotte rule of
   `condition_nationalité` returns faux for a Française
   (`code_construction_legislatif.catala_fr:1389-1402`, recorded by both coders: first
   `FR-APL-1/CONVERSION.md:135-140`, second `FR-APL-2/CONVERSION_2.md:126`). Outside
   Mayotte all 1,426 rows valid on both sides agree, which also confirms that the other
   difference in fixed inputs (`date_conventionnement`) has no effect on eligibility.

No sound mapping is needed for the rest of FR-APL: every first-coder table is covered by
at least one pair above (FR-APL-1 by two, FR-APL-3 by two).

### Judgements

* J-APL1. Exemple2 and Exemple3 are placed on the APL tables through their `ménage`,
  `demandeur` and `date_courante`, which have the same types as the APL scope's inputs
  (`tests_eligibilite_apl.catala_fr:117-192`, `:203-260`). They assert another scope's
  output (`:116`, `:202`), which M2(b) ignores.
* J-APL2. The dependants label is the number of `EnfantÀCharge` in the test's list
  (Exemple2: 2, `tests_eligibilite_apl.catala_fr:126-148`; Exemple3: 1, `:212-223`). The
  first coder's label k is "the first k children of Exemple1" and the rule counts the list
  (`paperc-data-fr2:paperC/specs/FR-APL/FR-APL-2/CONVERSION.md:31-34`); the second
  coder's likewise (`paperc-code2-fr2:paperC/specs2/FR-APL-5/CONVERSION_2.md:82-86`).
* J-APL3. A tenancy has no foyer type, foyer conventions, loan, loan holder, signature
  date or age-of-dwelling field, so these attributes are unknown for all three tests;
  `mode_occupation` is unknown in the home-buyer tables because `Locataire` is not one of
  their labels. `zone` and `résidence_principale` are set by every test
  (`tests_eligibilite_apl.catala_fr:68-69`, `:153-154`, `:227-228`) and are placed.
* J-APL4. Floor area 60 m² (Exemple2 `:178`, Exemple3 `:246`) is `ge_52` (first) and
  `58_to_60` (second); 80 m² (Exemple1 `:93`) is `ge_52` and `from_72`, as both
  conversions mapped it.
* J-US1. US-121-1 describes one taxpayer; each person of a test is one placement, so
  Test5 gives `person_ok_1` and Test6 gives `person_ok_1` and `person_ok_2`
  (`test_section_121.catala_en:138`, `:154-155`). The five-year aggregate is computed
  with `section_121.catala_en:179-191` (`tests_fr2.aggregate_days`): `person_ok_2`'s use
  counts 366 + 365 = 731 days.
* J-US2. Test1-Test4 run `Section121SinglePerson`, which has no return type, so in
  US-121-2 their return type and person 2 are unknown. Reading them as single returns
  (the first coder's convention for one taxpayer, `US-121-2/CONVERSION.md:63-65`) is the
  variant reported above.
* J-US3. The gain of every test is $350,000 (`test_section_121.catala_en:21`), in the
  middle band of both conversions.
* J-M6. Row mappings use each label's definition (cut points), and the representatives
  of B fall inside the mapped A label in every case: dates (A
  `FR-APL-1/CONVERSION.md:40-47`, `FR-APL-4/CONVERSION.md:33`, `FR-APL-5/CONVERSION.md:44`;
  B `FR-APL-1/CONVERSION_2.md:74-84`), surfaces (A `FR-APL-2/CONVERSION.md:52-56`; B
  `FR-APL-5/CONVERSION_2.md:87-93`), shares and third-party ages (A
  `FR-APL-3/CONVERSION.md:35-48` and band check `:71-75`; B `FR-APL-4/CONVERSION_2.md:83-94`),
  §121 lists and earlier sales (A `US-121-1/CONVERSION.md:32-57`; B
  `US-121-1/CONVERSION_2.md:45-56`, `:34-36`). For the nationality pair, B's fixed
  date 2020-03-10 is A's representative of `2019-09-01_to_2020-12-31`
  (`FR-APL-1/CONVERSION.md:44`).

## New Zealand rules (OpenFisca Aotearoa, commit 9d77ea7ce3c4)

Scripts: `paperC/analysis/m2_nz.py` (writes `out/m2_nz.json`) and `paperC/analysis/m6_nz.py`
(writes `out/m6_nz.json`), run from the repository root with `python3.12 -I`. Both read the
branches through `git show` and the official YAML tests from `paperC/analysis/_ext/`
(`fetch_sources.sh`). Every number below is printed by, or stored in the JSON of, one of
these scripts. Case identifiers are `file#case[person]` with paths relative to
`openfisca_aotearoa/tests/social_security/`, the case counted from 1 in file order and the
person given by name or by 0-based vector position. The first coder numbers cases the same
way; the second coder counts cases from 0 (`#0:0` there is `#1[0]` here).

Tables covered. First conversion (`origin/paperc-data-nz`): `NZ-SLP`, `NZ-AS` (SSA 2018
formula, 2022-W01), `NZ-SPS`, and the supplementary `NZ-AS-1964` (SSA 1964 formula,
2018-W01, kept outside `paperC/specs`). Second conversion (`origin/paperc-code2-nz`):
`NZ-SLP`, `NZ-AS` (SSA 1964 formula, 2018-W01), `NZ-SPS` (one child).

### M2 (a): official cases, mapped and unmapped

The suite of a rule is every YAML case in its test folder. The first coder counts
"person-values" (one per person whose entry variable a case asserts, README-NZ table,
`paperc-data-nz:paperC/specs/README-NZ.md:39-42`); the second coder counts "person-cases",
one per person of a test it reads (`paperc-code2-nz:paperC/specs2/NZ-SLP/CONVERSION_2.md:32`).
Both units are the same where both coders read the file; the second coder reads fewer files
(below).

| Rule | YAML cases | cases asserting the entry variable | persons in all cases | person-values asserting it | first: table, mapped | second: table, mapped |
|---|---:|---:|---:|---:|---|---|
| SLP | 50 | 7 | 105 | 13 | NZ-SLP 13 | NZ-SLP 13 |
| AS | 47 | 7 | 157 | 12 | NZ-AS 1; NZ-AS-1964 6 | NZ-AS 6 |
| SPS | 25 | 18 | 65 | 38 | NZ-SPS 14 | NZ-SPS 8 |

Unmapped cases by reason (reason category, then the conversion's own wording and line):

**NZ-SLP, both conversions.** Other output or scope: `supported_living_payment/base.yaml`
#1-#43 (assert the amount, with the entry variable set as an input;
`paperc-data-nz:paperC/specs/NZ-SLP/CONVERSION.md:77`,
`paperc-code2-nz:paperC/specs2/NZ-SLP/CONVERSION_2.md:72`). All 13 asserting person-values map
in both conversions.

**NZ-AS, first conversion (2018 formula).**
* Other period (6): `accommodation_supplement/1964/entitled.yaml#1`-`#6`, asserted for 2018-W01, before the 2018 formula applies (`paperc-data-nz:paperC/specs/NZ-AS/CONVERSION.md:76-81`).
* Other, case overrides an intermediate variable (5): `2018/entitled.yaml#1[0]`, `[1]`, `[3]`, `[4]`, `[5]` set `accommodation_supplement__accommodation_costs` = True with no type or costs, which the attributes compute as False (`CONVERSION.md:70-75`).
* Other output or scope (40 YAML cases): `2018/_benefit_me.yaml` #1-#3, `accommodation_supplement.yaml` #1, `area.yaml` #1, `assets.yaml` #1-#4, `base.yaml` #1-#10, `beneficiary.yaml` #1, `costs.yaml` #1-#6, `cutout.yaml` #1, `exclusion.yaml` #1-#7, `rate.yaml` #1, `rebate.yaml` #1, `situation.yaml` #1-#4 (`CONVERSION.md:82-94`).

**NZ-AS-1964, first conversion (supplementary).** Other period (6): `2018/entitled.yaml#1[0]`-`[5]`,
asserted for 2022-W01 (`paperc-data-nz:paperC/openfisca_nz/supplementary/NZ-AS-1964/CONVERSION.md:55-60`).
Other output or scope: the same 40 cases (`CONVERSION.md:67-79`).

**NZ-AS, second conversion (1964 formula).** Other period (6): `2018/entitled.yaml#1[0]`-`[5]`,
"entry variable not asserted at the fixed period 2018-W01"
(`paperc-code2-nz:paperC/specs2/NZ-AS/CONVERSION_2.md:113-118`). Other output or scope: the
same 40 cases; the oracle reads only the two `entitled.yaml` files
(`paperc-code2-nz:paperC/specs2/NZ-AS/oracle.py:21-24`).

The two coders thus put opposite halves of the AS suite on their main tables: the first
coder's main table takes the one 2018 case, the second coder's takes the six 1964 cases.

**NZ-SPS, first conversion.**
* Other household shape (16): the child Tamaiti of `sole_parent_support__benefit.yaml#1`-`#6` and of `sole_parent_support__entitled.yaml#1`, `#2`, `#4`, `#6`-`#12` (`paperc-data-nz:paperC/specs/NZ-SPS/CONVERSION.md:74-110`, "person has role child").
* Other, row excluded by the table's own exclusion SPS-X1 (5): `__entitled.yaml#3[0]`-`[4]` (`CONVERSION.md:89-93`).
* Other, case overrides an intermediate variable (3): `__entitled.yaml#4[Koro]` and `#5[0]` set `sole_parent_support__requirement` = True (`CONVERSION.md:94`, `:96`); `#10[Koro]` sets `sole_parent_support__lost_regular_support` = True without its leaves (`CONVERSION.md:105`).
* Other output or scope (7 YAML cases): `sole_parent_support__split_care.yaml` #1-#7 (`CONVERSION.md:111-112`).

**NZ-SPS, second conversion.**
* Other household shape (16): Tamaiti of `__entitled.yaml#1`, `#2`, `#4`, `#6`-`#12` (10, "person is not the principal"), and the persons of `#3[0]`-`[4]` and `#5[0]` (6, "family is not exactly one principal and one child") (`paperc-code2-nz:paperC/specs2/NZ-SPS/CONVERSION_2.md:123-140`).
* Other, case overrides an intermediate variable (2): `#4[Koro]` (`CONVERSION_2.md:130`), `#10[Koro]` (`CONVERSION_2.md:137`).
* Other, file outside the second coder's list of official tests (12): Koro and Tamaiti of `sole_parent_support__benefit.yaml#1`-`#6`. These cases assert `sole_parent_support__entitled`, and three of them are at 2019-W05, the table's own week; the oracle reads only `sole_parent_support__entitled.yaml` (`paperc-code2-nz:paperC/specs2/NZ-SPS/oracle.py:22`), and the conversion record states that 2019-W05 is "the period of every official test" (`CONVERSION_2.md:83`). The first coder maps the six Koro persons.
* Other output or scope (7 YAML cases): `__split_care.yaml` #1-#7.

### M2 (b): declared values used by the whole suite

Every person of every case is placed on each table's attributes, whatever the case asserts
and whatever its week or household, at every week the case asserts an output (883 person-weeks
for AS, 105 for SLP, 65 for SPS; 89 placement rows for the second coder's SPS, where a family
with two children gives one row per child). Two readings:

* **primary**: an attribute takes a value only when the case sets that input, or sets the
  leaves of a defined term whose formula is a plain function of them (see Judgements);
  otherwise it is UNKNOWN, as the task requires;
* **secondary**: UNKNOWN is replaced by the encoding's default or by what the formula
  computes from the inputs the case sets (sources in `DEFAULTS` of `m2_nz.py` and in the
  Judgements). This reading is reported for information only.

The mapped column is the table's `official_examples.csv`. The suite columns include the
mapped rows.

| Table | declared values | unused, mapped tests | unused, whole suite (primary) | unused, whole suite (secondary) |
|---|---:|---:|---:|---:|
| first NZ-SLP | 16 | 0 | 0 | 0 |
| second NZ-SLP | 16 | 0 | 0 | 0 |
| first NZ-AS (2018) | 34 | 20 | 0 | 0 |
| first NZ-AS-1964 (suppl.) | 18 | 3 | 3 | 2 |
| second NZ-AS (1964) | 18 | 3 | 3 | 2 |
| first NZ-SPS | 41 | 21 | 14 | 12 |
| second NZ-SPS | 22 | 5 | 3 | 2 |

Values still unused by the whole suite:
* NZ-AS-1964 and second NZ-AS: `ordinarily_resident_in_nz` False (primary only; in the secondary reading it comes from the default, `resident.py:77`, in 151 placements), `below_income_threshold` False and `below_cash_threshold` False (both readings: no case sets them False, and their default is True, `entitled.py:153`, `:161`).
* First NZ-SPS: `children` none, 1:14-15, 1:16-17, 1:>=18 and nine of the ten two-child labels (primary; `none` appears in the secondary reading from the single-person vector cases `__entitled.yaml#3` and `#5`, which describe no family); `social_security__principal_caregiver` False (primary). The only two-child label any case reaches is `2:<14+<14` (`__split_care.yaml`, children aged 5 and 3).
* Second NZ-SPS: `principal_caregiver` False (primary), `child_dependent` False and `child_age` 14+ (both readings: every child in the suite is aged 3 or 5, or has no age).

Where the values left unused by the mapped tests come from in the whole suite (first case
found; full lists in `out/m2_nz.json`, key `provenance`):
* First NZ-AS: all 20 come from 2018-folder cases that assert other variables, plus the five `2018/entitled.yaml` persons the first coder could not map: `residential_requirement` False from `2018/entitled.yaml#1[1]`; the six accommodation types and costs > 0 from `_benefit_me.yaml`, `accommodation_supplement.yaml`, `exclusion.yaml#1`, `#6`, `rate.yaml`, `rebate.yaml`; relationship True, dependent children >= 1 and both higher cash-asset bands from `assets.yaml` (families with partner and children); the seven s 67 flags from `exclusion.yaml#2`-`#7`.
* First NZ-SPS: `2:<14+<14`, `receiving` True, the three s 32 flags True from `__split_care.yaml#1`-`#6`; `residential_requirement` False from `__entitled.yaml#3[3]`; `age` <20 from the child persons Tamaiti (29 placements).
* Second NZ-SPS: `residential_requirement` False from `__entitled.yaml#3[3]`; `age` <20 from the child persons.

Restricted to applicants (persons in role principal, or with no family role), the primary
reading leaves one more value unused in each SPS table (`age` <20; first 15, second 4); the
other tables do not change.

UNKNOWN counts per attribute (primary), out of the placement rows: SLP 101 of 105 for
restricted work capacity, 103 blind, 93 residential requirement, 0 age, 103 self-inflicted,
99 caring, 11 dependent children. First NZ-AS (883): from 203 (relationship) to 881
(disability); accommodation type 672, costs 785, cash assets 837. AS-1964 tables (883): age
779, accommodation costs 650, each other attribute 877 to 882. First NZ-SPS (65): children 6,
age 6, relationship 6, principal caregiver 31, residential requirement 36, the s 30 and s 32
flags 55 to 64. Second NZ-SPS (89): child attributes 6, age 6, principal caregiver 43, flags
79 to 88. Ten placements in AS have an `accommodation_type` outside the enum (`under_the_sun`,
`under_the_moon` in `costs.yaml#1`-`#4` and `exclusion.yaml#1`, `#6`); they stay UNKNOWN in
both readings.

Cross-check: the mapped-only counts (0, 20, 3, 21; 0, 3, 5) equal the lists in
`paperc-data-nz:paperC/specs/README-NZ.md:54-72` and
`paperc-code2-nz:paperC/specs2/README-NZ-CODE2.md:22-26`. No discrepancy.

### M2 (c): H1 indicators per table

`missed valid` is the number of valid ground-truth rows outside the product of the observed
values (C1 `missed_valid`).

| Table | valid rows | mapped: unused > 0 / missed valid | whole suite, primary | whole suite, secondary |
|---|---:|---|---|---|
| first NZ-SLP | 224 | no / 0 | no / 0 | no / 0 |
| second NZ-SLP | 256 | no / 0 | no / 0 | no / 0 |
| first NZ-AS (2018) | 48,384 | yes / 48,383 | no / 0 | no / 0 |
| first NZ-AS-1964 | 384 | yes / 336 | yes / 336 | yes / 288 |
| second NZ-AS (1964) | 384 | yes / 336 | yes / 336 | yes / 288 |
| first NZ-SPS | 99,840 | yes / 99,776 | yes / 91,648 | yes / 82,944 |
| second NZ-SPS | 2,048 | yes / 1,984 | yes / 1,792 | yes / 1,536 |

With the whole suite, both indicators still hold for the AS-1964 and SPS tables of both
conversions and stay false for both NZ-SLP tables. They change for one table: the first
coder's NZ-AS (2018 formula), where every declared value occurs somewhere in the 2018 test
folder, so the product of the observed values covers all 48,384 valid rows. The slice
(other output, and the intermediate override in `2018/entitled.yaml`) accounts for all 20
unused values of that table.

### M6 (a): attribute-level alignment

**SLP.** Both conversions make the same seven inputs attributes, with the same cut points:
restricted work capacity, totally blind, residential requirement (kept whole), age (16, 18,
20), self-inflicted, caring for another person, dependent children (0 / 1 or more). Labels
differ only in spelling (`>=20` / `20+`, `>=1` / `1+`); every attribute coincides. Both fix
2019-W01 and a one-person household, and both keep the residential requirement and the
dependent-children count at the level of the defined term. The one difference is the
exclusion: the first coder declares SLP-X1 (self-inflicted without restricted capacity or
blindness, `paperc-data-nz:paperC/specs/NZ-SLP/spec.json:37`); the second declares none
(`paperc-code2-nz:paperC/specs2/NZ-SLP/CONVERSION_2.md:74`).

**AS, SSA 1964 formula (first coder's supplementary table, second coder's main table).**
Both make the same nine inputs attributes: age (16), `immigration__resident` (kept whole),
permanent resident, citizen, ordinarily resident, `accommodation_supplement__accommodation_costs`
(a plain input at 2018-W01), social housing, below the income threshold, below the cash
threshold. All nine coincide (`>=16` / `16+`). Both fix 2018-W01 and a lone applicant, and
both declare the same exclusion (AS64-X1, `paperc-data-nz:paperC/openfisca_nz/supplementary/NZ-AS-1964/CONVERSION.md:12`;
PR-IMPLIES-RESIDENT, `paperc-code2-nz:paperC/specs2/NZ-AS/CONVERSION_2.md:86`).

**AS, SSA 2018 formula.** Only the first coder converts it (main NZ-AS, 2022-W01,
`paperc-data-nz:paperC/specs/NZ-AS/CONVERSION.md:7`). Its 14 attributes (residential
requirement, accommodation type, accommodation costs > 0, relationship, dependent children,
cash assets at 8,100 and 16,200, the partner's AS, and the seven s 67 grant and disability
flags) are inputs the second coder's table never reads, because the second coder fixed
2018-W01, where the 1964 formula applies
(`paperc-code2-nz:paperC/specs2/README-NZ-CODE2.md:36`). No row-level comparison is possible
for this formula: the second conversion has no table for it. Conversely, the first coder's
main NZ-AS reads none of the 1964 inputs (age, the three status flags, the threshold flags).

**SPS.**

| Encoding input | first coder | second coder | relation |
|---|---|---|---|
| residential requirement | attribute | attribute | coincide |
| age (20) | attribute `<20`, `>=20` | attribute `<20`, `20+` | coincide |
| in a relationship | attribute | attribute | coincide |
| s 30(b)-(d): spouse died, dissolved, living apart | attributes | attributes | coincide |
| s 30(e): partner imprisoned, under supervision | attributes | attributes | coincide |
| principal caregiver (month 2019-01) | attribute | attribute | coincide |
| receiving SPS; principal caregiver before living apart; of youngest; by order (s 32) | attributes | fixed at default False: with one child, s 32 split care is True for the principal (`CONVERSION_2.md:63-69`) | first only |
| children (members in role child) | composite `children`: none, one child in bands <14, 14-15, 16-17, >=18, or two children (15 labels), children's financial independence fixed False (`paperc-data-nz:paperC/specs/NZ-SPS/CONVERSION.md:14`, `:17`) | exactly one child, `child_dependent` (kept whole) x `child_age` <14 / 14+ (`paperc-code2-nz:paperC/specs2/NZ-SPS/CONVERSION_2.md:75`, `:81-82`) | on one-child households the first refines the second on age (14-15 and 16-17 both fall in True/14+, 1:>=18 is False/14+); the second's cell False/<14 (a financially independent child under 14) has no first-coder label; the first's `none` and two-child labels have no second-coder counterpart |
| parents living apart | not set (no other parent) | default | both leave it without effect |
| period | 2019-W05 | 2019-W05 | same |

Exclusions: the first coder declares SPS-X1 and SPS-X2 (no dependent child,
`paperc-data-nz:paperC/specs/NZ-SPS/spec.json:281`); the second declares none.

### M6 (b): NZ-SLP row by row

Attribute names are mapped in spec order and the labels `>=20` -> `20+`, `>=1` -> `1+`; the
mapping is a bijection, so all 256 combinations are compared one to one.

* 224 rows agree: every row valid for the first coder has the same output in both tables.
* 32 rows are EXCLUDED by the first coder (SLP-X1) and evaluated by the second: 29 False, 3 True.

The three True rows are self-inflicted = True, restricted capacity = False, blind = False,
caring for another person = True, residential requirement = True, and (age 18-19,
dependent children 0), (age >=20, 0) or (age >=20, >=1). They are True through the s 40
carer route (`supported_living_payment.py:79-106`), which reads neither the s 34 grounds nor
the self-inflicted flag. The first coder's record states that the output of the excluded
rows "would be False in any case (the s 34 branch already fails), so the exclusion changes
labels and never outcomes" (`paperc-data-nz:paperC/specs/NZ-SLP/CONVERSION.md:16`). That
statement holds for 29 of the 32 rows and fails for these 3. The two conversions'
evaluations agree everywhere: the difference lies in the exclusion, and the second
coder's table shows that the excluded combinations are evaluable (their True count, 51,
equals the first coder's 48 plus these 3).

### M6 (c): other row-level comparisons

**NZ-AS-1964 (first) against NZ-AS (second), SSA 1964 formula.** Names mapped in spec order,
`>=16` -> `16+`; all 512 combinations compared one to one. 512 agree, including the 128
EXCLUDED rows, which both coders exclude with the same predicate. No disagreement.

**NZ-SPS.** Common refinement: the first coder's rows with one child and the four s 32
inputs at False (the second coder's defaults), 4 x 2^9 = 2,048 rows; each maps to one
second-coder row through `1:<14` -> (True, <14), `1:14-15` and `1:16-17` -> (True, 14+),
`1:>=18` -> (False, 14+), the other nine attributes by name. These 2,048 rows cover 1,536 of
the second coder's 2,048 rows; the 512 rows with `child_dependent` False and `child_age` <14
have no first-coder counterpart (63 of them are True).

* 1,792 rows agree: every comparable row valid for the first coder.
* 256 rows are EXCLUDED by the first coder (SPS-X1: principal caregiver with `children` = `1:>=18`) and evaluated by the second: 193 False, 63 True.

The 63 True rows are the second coder's (False, 14+) child with principal caregiver True, a
residential requirement, age 20+, and one of the 63 relationship combinations that satisfy
s 30. They are True because of the operator precedence at `sole_parent_support.py:180-181`
(`(dependent_child * age) < 14` holds for a non-dependent child), which both coders record
(`paperc-data-nz:paperC/specs/NZ-SPS/CONVERSION.md:26`,
`paperc-code2-nz:paperC/specs2/NZ-SPS/CONVERSION_2.md:88`). The first coder's SPS-X1 treats
"principal caregiver of a family whose only child is 18 or over" as impossible by definition
(`CONVERSION.md:20`), so those rows never reach the encoding there; the second coder
evaluates them. On rows both coders evaluate, the two ground truths agree completely.

### Judgements (NZ)

1. **Unit of an official case.** One person of one YAML case, as both coders do; for M2 (b) one placement per person and per week at which the case asserts an output (README rule in `m2_nz.py`, docstring). Weeks come from the period keys of the outputs; unkeyed outputs use the case's `period`.
2. **Value at a week.** An input keyed by periods takes the value whose period contains the Monday of the week (`period.start`, `period.first_day`, the first month of the first day: the days the formulas read, e.g. `sole_parent_support.py:130`, `:183`); `ETERNITY` covers every week; an unkeyed input applies to every week of the case. For principal caregiver only the month of the Monday is read; every case sets two months (`month:2019-01:2`), covering the whole week.
3. **Every person is placed, including partners and children.** The task asks to ignore household shape; the results restricted to applicants are reported beside (one extra unused value in each SPS table).
4. **Defined terms derived in the primary reading** when the case sets the leaves and the formula is a plain function of them: `age` from `date_of_birth` (`demographics/ages.py:45-53`); `social_security__dependent_children` from the family's members in role child (`interpretation/child.py:43-54`), each child dependent if `social_security__dependent_child` is set True, or if its age is under 18 and the case sets none of the inputs of financial independence (`interpretation/child.py:17-40`, `financially_independent.py:23-29`); `social_security__in_a_relationship` from an explicit family (principal with a member in role partner, `relationships.py:16-25`); the partner's AS receipt from the partner's own input. A case with no family (vector cases) leaves these UNKNOWN.
5. **First coder's cash assets** are the applicant's plus the partners' (`paperc-data-nz:paperC/specs/NZ-AS/CONVERSION.md:14`); unset members count 0.
6. **`accommodation_supplement__accommodation_costs` on the AS-1964 tables** (an input before 2018-11-26, a formula after): set by the case, or in the secondary reading computed by the 2018 formula (`costs.py:20-94`) from type, costs and tenancy/ownership roles for weeks from 2018-11-26, and default False (`costs.py:17`) before. The primary reading counts it known when the case sets the type or the costs.
7. **First coder's `children` label**: bands <14, 14-15, 16-17, >=18 of the family's child members; a child whose explicit `dependent_child` contradicts its band, or a family with three or more children, gets no label (UNKNOWN). **Second coder's child attributes**: a family with two children gives one placement per child (6 cases of `__split_care.yaml`).
8. **Values outside a declared enum** (`under_the_sun`, `under_the_moon` as accommodation type) stay UNKNOWN.
9. **Second coder's `age: 5` without period** (`CONVERSION_2.md:92-95`): this analysis applies an unkeyed value at the case's weeks (judgement 2), so the child is placed at age 5; the second coder reports that the simulation leaves it at -9999. Both fall in `<14`, so no count changes.
10. **Reason categories** follow each coder's own log text: "does not assert" -> other output or scope; "asserted for ... outside" and "not asserted at the fixed period" -> other period; "role child", "not the principal", "not exactly one principal and one child" -> other household shape; override of an intermediate variable and rows under the table's own exclusion -> other; cases in files the second coder's oracle does not read -> other.
11. **M6 label maps**: attributes paired in spec order for SLP and AS-1964 (same encoding variables in the same order, checked by name); SPS children mapped as above with financial independence False on the first side, which makes a child dependent exactly when under 18.

Problems found: (i) the first coder's claim that SLP-X1 never changes an outcome is wrong for
3 rows (`paperc-data-nz:paperC/specs/NZ-SLP/CONVERSION.md:16`); (ii) the second coder's SPS
oracle skips `sole_parent_support__benefit.yaml`, whose cases assert the entry variable,
three of them at the table's own week (`paperc-code2-nz:paperC/specs2/NZ-SPS/oracle.py:22`),
while its record says 2019-W05 is the period of every official test.
