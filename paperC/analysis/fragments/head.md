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
