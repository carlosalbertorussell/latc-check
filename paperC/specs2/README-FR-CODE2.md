# French family benefits: second, blinded conversion (Paper C)

Second coder's conversion of the Catala French family-benefits rules into the shared
sample format of `paperC/specs/FORMAT.md` (branch `paperc-harness`), for the
inter-coder comparison of Paper C. Branch `paperc-code2-fr`, created from
`origin/paperc-catala-family-benefits`.

## Blinding statement

This conversion was made without access to the first coder's work. While doing it I:

* did not check out, diff, `git show` or read any file under `paperC/specs/` on any
  branch, with the single permitted exception of `paperC/specs/FORMAT.md`, read with
  `git show origin/paperc-harness:paperC/specs/FORMAT.md`;
* read from `origin/paperc-harness` only that file and `paperC/PROTOCOL.md` (also through
  `git show`);
* did not fetch, check out or read the branches `paperc-data-fr`, `paperc-run-*`,
  `paperc-verify-*`, nor any `paperc-code2-*` branch other than this one (only
  `paperc-harness` and `paperc-catala-family-benefits` were fetched);
* used from `origin/paperc-catala-family-benefits` only `paperC/catala_family_benefits/`
  (the Catala 1.3.0 Python build, its runtime, `run_official_tests.py`, `inputs.md`, and the
  folder's README);
* read the Catala sources in a fresh clone of CatalaLang/catala-examples at commit
  `2694b17ddd7c2246e207e8f077d586349ee5abea`.

Every interpretive choice (attributes, cut points, fixed date, representatives,
exclusions, output labels, splits) was made from those sources and from running the
encoding; each is recorded with its article and `file:line` in the folder's
`CONVERSION_2.md`.

## Samples

| ID | rule | attributes | declared space | valid | EXCLUDED | REJECTED | output labels | official rows |
|---|---|---|---|---|---|---|---|---|
| FR-PF | `PrestationsFamiliales.droit_ouvert`, per child | 5 | 3 x 3 x 3 x 2 x 2 = 108 | 72 | 36 | 0 | 2 | 4 |
| FR-AF-1 | allocations familiales, 1 child | 9 | 3 x 3 x 5 x 2 x 9 x 3 x 3 x 2 x 2 = 29,160 | 19,440 | 9,720 | 0 | 19 | 2 |
| FR-AF-2 | allocations familiales, 2 children | 9 | 3 x 5 x 2 x (9 x 3 x 3)^2 = 196,830 | 196,830 | 0 | 0 | 54 | 4 |
| FR-AF-3 | allocations familiales, 3 children | 9 | 3 x 5 x 2 x (9 x 2)^3 = 174,960 | 174,960 | 0 | 0 | 62 | 1 |

Fixed date for all four: 2020-05-01. The household allowance is split by number of
children (CONVERSION_2.md A1); households with four or more children are not covered,
which leaves the Mayotte fourth-child rate as the one statutory case outside the tables.

Each folder holds `spec.json`, `ground_truth.csv`, `official_examples.csv`, `oracle.py`,
`ENVIRONMENT.md`, `CONVERSION_2.md` and `SHA256SUMS`.

## Official tests

The two official test files hold 15 test scopes: `tests_ouverture_droits.catala_fr`
Test1 (4 assertions on `droit_ouvert`, one per child, counted here as 4 cases) and
`tests_allocations_familiales.catala_fr` Test1 to Test14 (one assertion each on the
amount). `oracle.py --check-official` runs all 18 cases through the encoding in every
folder: 18 of 18 pass. Mapped cases, all of which give the same label through the oracle
at the representatives as through the encoding at the official inputs:

| sample | mapped rows | cases |
|---|---|---|
| FR-PF | 4 | ouverture_droits Test1 enfant1 to enfant4 |
| FR-AF-1 | 2 | Test3, Test5 |
| FR-AF-2 | 4 | Test4, Test6, Test9, Test10 |
| FR-AF-3 | 1 | Test2 |

Unmapped: Test1, Test7, Test12 (four children); Test8, Test11, Test13, Test14 (dates
outside 2020-04-01..2020-12-31, the period on which every parameter equals its value at
the fixed date). Reasons per folder are in each `CONVERSION_2.md`.

## Declared values that the official examples never use

### FR-PF (5 of 13 attribute values)

* `residence`: drom_l751_1, mayotte (2/3)
* `obligation_scolaire`: Avant (1/3)
* `remuneration_mensuelle`: entre_plafonds (1/3)
* `aide_logement_personnelle`: true (1/2)
* output labels: none unused (0 of 2)

### FR-AF-1 (21 of 34 attribute values)

* `residence`: mayotte (1/3)
* `attributaire`: tiers_titre_I, aucun (2/3)
* `ressources`: entre_plafonds_I_II, zone_degressive_II, au_dela_plafond_II (3/5)
* `avant_2012`: true (1/2)
* `e1_age`: moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus (8/9)
* `e1_remuneration`: entre_plafonds, au_dessus_plafonds (2/3)
* `e1_prise_en_charge`: partagee, services_sociaux (2/3)
* `e1_deja_ouvert`: false (1/2)
* `e1_aide_logement`: true (1/2)
* output labels: 17 of 19 unused

### FR-AF-2 (19 of 40 attribute values)

* `residence`: mayotte (1/3)
* `ressources`: zone_degressive_I, zone_degressive_II, au_dela_plafond_II (3/5)
* `avant_2012`: true (1/2)
* `e1_age`: moins_3, 14_16, anniversaire_16, 19_20, 20_23, 23_plus (6/9)
* `e1_remuneration`: entre_plafonds (1/3)
* `e1_prise_en_charge`: partagee (1/3)
* `e2_age`: 14_16, anniversaire_16, 19_20, 20_23, 23_plus (5/9)
* `e2_remuneration`: entre_plafonds (1/3)
* output labels: 51 of 54 unused

### FR-AF-3 (34 of 43 attribute values)

* `residence`: drom_l751_1, mayotte (2/3)
* `ressources`: zone_degressive_I, entre_plafonds_I_II, zone_degressive_II, au_dela_plafond_II (4/5)
* `avant_2012`: true (1/2)
* `e1_age`: moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus (8/9)
* `e1_deja_ouvert`: false (1/2)
* `e2_age`: moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus (8/9)
* `e2_deja_ouvert`: false (1/2)
* `e3_age`: moins_3, 3_11, 11_14, 14_16, anniversaire_16, 16_19, 19_20, 23_plus (8/9)
* `e3_deja_ouvert`: false (1/2)
* output labels: 61 of 62 unused

## Checks run

* `oracle.py --check-official`: 18/18 official cases pass through the encoding in every
  folder; mapped rows 4/4, 2/2, 4/4, 1/1 agree with the oracle. The earnings cut points
  (711,49 EUR and 943,02 EUR) are re-derived from the encoding on each run.
* `oracle.py --check-groups` (each grouped residence and care label replaced by every
  other member): FR-PF all 108 rows, 144 substitutions; FR-AF-1 all 29,160 rows, 51,840
  substitutions; FR-AF-2 every 40th row (4,921 rows, 16,405 substitutions); FR-AF-3 every
  40th row (4,374 rows, 8,748 substitutions). 0 disagreements.
* FR-AF-2 with `déjà ouvert` flipped to faux on 1,500 random rows: 0 differences (the
  input is fixed there, CONVERSION_2.md A1).
* Format checks: header and odometer order of every `ground_truth.csv`, outputs within
  `output.values` plus EXCLUDED and REJECTED, every official row uses declared labels,
  EXCLUDED exactly where an exclusion predicate holds (0 disagreements), LF line endings.
* Resources cells whose `zone_degressive_*` region is empty for that household (no
  allocation to taper) are kept and evaluated at their representative: FR-AF-1 6,624,
  FR-AF-2 30,796, FR-AF-3 720 rows (CONVERSION_2.md A4).
* Reproducibility: `ground_truth.csv` and `official_examples.csv` were written with Python
  3.13.16 and regenerated with Python 3.12.3; see "Python 3.12 re-run" below.

## Python 3.12 re-run

All four folders were regenerated in place with Python 3.12.3 from the committed
`oracle.py` and `spec.json` (`--check-official`, `--write-official`, `--enumerate`) and
compared byte for byte with the Python 3.13.16 files:

| sample | `ground_truth.csv` | `official_examples.csv` |
|---|---|---|
| FR-PF | identical | identical |
| FR-AF-1 | identical | identical |
| FR-AF-2 | identical | identical |
| FR-AF-3 | identical | identical |

## How to rebuild

From `paperC/specs2/`, with Python 3.12 or later:

```sh
python3 build_fr_code2.py spec            # spec.json (output values empty) and oracle.py copies
for s in FR-PF FR-AF-1 FR-AF-2 FR-AF-3; do
  python3 $s/oracle.py --check-official   # must report every case passing
  python3 $s/oracle.py --write-official
  python3 $s/oracle.py --enumerate        # about 6 and 10 minutes for FR-AF-2 and FR-AF-3 on 4 cores
done
python3 build_fr_code2.py outputs         # output.values from the labels that occur
python3 build_fr_code2.py stats           # the counts above
python3 build_fr_code2.py sums            # SHA256SUMS
```

`build_fr_code2.py` sits outside the sample folders so that each folder holds only the
files FORMAT.md lists.

## Departures from the task text and from FORMAT.md

* The conversion notes are named `CONVERSION_2.md`, as the second-coder task asks;
  FORMAT.md calls the file `CONVERSION.md`. The content is the one FORMAT.md describes.
* The samples live under `paperC/specs2/<ID>/`, as the task asks, so that they cannot
  collide with the first coder's `paperC/specs/<ID>/`.
* `oracle.py` has two flags beyond the two FORMAT.md requires: `--write-official` and
  `--check-groups`.
* `oracle.py --enumerate` runs the official check first and stops if any case fails.
