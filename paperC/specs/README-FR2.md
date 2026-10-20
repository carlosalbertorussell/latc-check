# FR-APL and US-121 samples (Paper C)

This branch (`paperc-data-fr2`) adds two families of samples in the format of
`paperC/specs/FORMAT.md` (branch `paperc-harness`):

* **FR-APL**: eligibility for the French *aide personnalisée au logement* (APL), scope
  `ÉligibilitéAidePersonnaliséeLogement` of the Catala encoding `aides_logement`, the
  decision exercised by `aides_logement/tests/tests_eligibilite_apl.catala_fr`. The
  amount computation is out of scope. Five sub-tables, `paperC/specs/FR-APL/FR-APL-1`
  to `FR-APL-5`.
* **US-121**: exclusion of gain from the sale of a principal residence, 26 U.S.C. 121,
  from the Catala encoding `us_tax_code/section_121.catala_en`, the scopes exercised by
  `us_tax_code/tests/test_section_121.catala_en`. Two sub-tables,
  `paperC/specs/US-121/US-121-1` and `US-121-2`.

Source: https://github.com/CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`, compiled with Catala 1.3.0 to Python
(`paperC/catala_more/`, whose README has the build, the clerk results and the
provenance). Every official test passes under clerk and through the generated Python;
`python oracle.py --check-official` passed in every folder before `--enumerate` was
run.

## Tables

| Sample | Subject | Attributes | \|D\| | valid | EXCLUDED | REJECTED | Output counts | Official examples |
|---|---|---|---|---|---|---|---|---|
| FR-APL-1 | date, territory, nationality | 3 | 270 | 175 | 0 | 95 | eligible 93, not_eligible 82 | 1 |
| FR-APL-2 | household size and floor area | 7 | 69,120 | 67,140 | 0 | 1,980 | eligible 12,864, not_eligible 54,276 | 1 |
| FR-APL-3 | tenants and sub-tenants | 8 | 3,600 | 3,600 | 0 | 0 | eligible 32, not_eligible 3,568 | 1 |
| FR-APL-4 | logement-foyer residents | 6 | 1,440 | 952 | 460 | 28 | eligible 504, not_eligible 448 | 0 |
| FR-APL-5 | home buyers | 8 | 2,880 | 2,520 | 360 | 0 | eligible 80, not_eligible 2,440 | 0 |
| US-121-1 | §121(a) requirements, one taxpayer | 3 | 12 | 4 | 0 | 8 | requirements_met 1, requirements_not_met 3 | 4 |
| US-121-2 | §121 amount excluded, single, joint or surviving-spouse return | 8 | 1,296 | 204 | 396 | 696 | no_exclusion 144, entire_gain 23, limited_to_250000 34, limited_to_500000 3 | 2 |

"valid" = \|D\| − EXCLUDED − REJECTED (PROTOCOL.md section 2). The US-121-2 row gives the
counts after the correction of 2026-10-20 (section "Correction" at the end).

### REJECTED rows

REJECTED rows are run-time errors of the Catala code itself, reproduced by the Catala
interpreter (cross-check below). They are explained in each CONVERSION.md:

* FR-APL-1: `NoValue` for every input before 2019-09-01 (no SMIC before 2019-01-01, no
  definition of the dependants taken into account before 2019-09-01); `Conflict` of two
  Mayotte SMIC definitions from 2024-01-01 to 2024-10-31.
* FR-APL-2: `Conflict` in Mayotte between the Mayotte floor-area rule and R844-4, two
  exceptions to the same base rule.
* FR-APL-4: the Mayotte SMIC `Conflict`.
* US-121-1 and US-121-2: `DateError` whenever another §121(a) sale is given,
  `section_121.catala_en:376` comparing a number of days with "2 year" (§121(b)(3) can
  never be evaluated).

### Official tests

| Test file | Test scope | Asserts | Maps onto |
|---|---|---|---|
| `tests_eligibilite_apl.catala_fr` | Exemple1 | `ÉligibilitéAidePersonnaliséeLogement.éligibilité` = vrai | FR-APL-1, FR-APL-2, FR-APL-3 |
| | Exemple2 | `ÉligibilitéAllocationLogement.éligibilité` = AllocationLogementFamiliale | none (different scope and output: allocation de logement) |
| | Exemple3 | same as Exemple2 | none |
| `test_section_121.catala_en` | Test1–Test4 | `Section121SinglePerson.requirements_met` | US-121-1 |
| | Test5, Test6 | `Section121TwoPersons.income_excluded_from_gross_income` | US-121-2 |

Exemple1 maps onto three FR-APL tables because each of them keeps Exemple1's
household for the inputs it does not vary; the oracles check that the inputs built for
the mapped row equal the test's inputs exactly (structural equality of the Catala
records; for FR-APL-2 with the test's 80 m² in place of the band representative).

### Declared values that the official examples never use

| Sample | Attribute (declared values) | Values never used by an official example |
|---|---|---|
| FR-APL-1 | `date_courante` (6) | `lt_2019-01-01`, `2019-01-01_to_2019-08-31`, `2021-01-01_to_2023-12-31`, `2024-01-01_to_2024-10-31`, `ge_2024-11-01` |
| | `residence` (9) | every value except `Metropole` (8) |
| | `nationalite_demandeur` (5) | every value except `francaise` (4) |
| FR-APL-2 | `residence` (9) | every value except `Metropole` (8) |
| | `nationalite_demandeur` (5) | every value except `francaise` (4) |
| | `situation_familiale` (6) | `Celibataire`, `Pacses`, `Concubins`, `CelibataireSepareDeFait`, `ConcubinageDontSepareDeFait` |
| | `personnes_a_charge` (4) | `0`, `1`, `2` |
| | `autres_occupants` (2) | `0` |
| | `surface_m_carres` (16) | every value except `ge_52` (15) |
| | `personnes_agees_handicapees_r844_4` (2) | `vrai` |
| FR-APL-3 | `mode_occupation` (2) | `SousLocataire` |
| | `bailleur` (5) | every value except `BailleurSocial_conventionne` (4) |
| | `part_propriete_famille` (3) | `famille_moins_de_10pc`, `famille_10pc_ou_plus` |
| | `part_usufruit_famille` (3) | `famille_moins_de_10pc`, `famille_10pc_ou_plus` |
| | `loue_ou_sous_loue_a_des_tiers` (5) | every value except `Non` (4) |
| | `logement_decent_l89_462` (2) | `faux` |
| | `residence_principale` (2) | `faux` |
| | `condition_rattache_foyer_fiscal_parent_ifi` (2) | `vrai` |
| FR-APL-4 | all 6 attributes | every value (no official example) |
| FR-APL-5 | all 8 attributes | every value (no official example) |
| US-121-1 | `ownership_days_in_5_years` (2) | `lt_730_days` |
| | `use_days_in_5_years` (2) | none |
| | `other_section_121a_sale` (3) | `within_2_years`, `more_than_2_years` |
| US-121-2 | `return_type` (3) | `surviving_spouse` |
| | `person1_ownership_days_in_5_years`, `person1_use_days_in_5_years`, `person2_ownership_days_in_5_years`, `person2_use_days_in_5_years` (2 each) | `lt_730_days` |
| | `person1_other_section_121a_sale`, `person2_other_section_121a_sale` (3 each) | `within_2_years`, `more_than_2_years` |
| | `gain` (3) | `gt_0_lt_250000`, `ge_500000` |

## How the ground truth was checked

1. **Official tests first.** In every folder `python oracle.py --check-official`
   re-runs every official test scope of the test file directly through the generated
   Python (3/3 for FR-APL, 6/6 for US-121) and every mapped case through the oracle
   (FR-APL-1/2/3: 1/1 each; US-121-1: 4/4; US-121-2: 2/2).
2. **Band homogeneity.** `python oracle.py --check-bands` evaluates every row again
   with each interval attribute moved to other values inside its label (every day from
   2017 to 2027 for FR-APL-1, every day from 2019-09-01 to 2027 for FR-APL-4, every
   integer from 0 to 120 m² for FR-APL-2, boundary and interior points elsewhere). In
   total 1,735,259 evaluations; every one gave the output of the label's representative
   (the probes are listed in each CONVERSION.md). One label was narrowed after a
   first run of this check: in US-121-1 an earlier §121 sale on the date of sale itself
   gives no error, so `within_2_years` is "1 day to 2 years before".
3. **Interpreter cross-check.** `paperC/catala_more/interpreter_crosscheck.py` wrote
   sampled rows (random.Random(2026), at most 600 per table, all rows when fewer) as
   Catala `#[test]` scopes asserting the ground-truth output and ran them with the
   Catala 1.3.0 interpreter through `clerk test`, with no Python involved. Result:
   3,186 rows run (all of FR-APL-1, US-121-1 and the non-excluded rows of
   US-121-2; 600 of each other table), 0 disagreements. Every label row passed its
   assertion (2,611 rows) and every REJECTED row (575) failed with a run-time error at
   the same source position as in the Python runtime. Details:
   `paperC/catala_more/interpreter_crosscheck_report.txt`.

   | Sample | Rows run | Label rows agreeing | REJECTED rows agreeing | Disagreements |
   |---|---|---|---|---|
   | FR-APL-1 | 270 | 175 | 95 | 0 |
   | FR-APL-2 | 600 | 579 | 21 | 0 |
   | FR-APL-3 | 600 | 600 | 0 | 0 |
   | FR-APL-4 | 600 | 581 | 19 | 0 |
   | FR-APL-5 | 600 | 600 | 0 | 0 |
   | US-121-1 | 12 | 4 | 8 | 0 |
   | US-121-2 (before the correction) | 504 | 72 | 432 | 0 |

   A negative control (one assertion flipped) was reported as a disagreement.
4. **Harness loader.** With the harness of branch `paperc-harness` (commit `89795da`),
   `paperC.harness.spec.load_sample` loads all seven folders (CTRL-HASH and CTRL-GT
   pass), and in every folder a row is EXCLUDED exactly when an exclusion predicate
   holds (CTRL-EXCL, 0 disagreeing rows). A trial run of
   `python -m paperC.harness.run --spec paperC/specs/US-121/US-121-1` (output kept out of
   the repository) completed its 1,266 runs; its only failing control was CTRL-H3,
   which PROTOCOL.md section 7(c) expects for a sample with REJECTED rows (C3 then
   generates rejected rows). Five of the seven samples have REJECTED rows (every one
   except FR-APL-3 and FR-APL-5).
5. **Reproducibility.** The enumeration run with Python 3.13.16 and again with Python
   3.12.3 gave byte-identical `ground_truth.csv` and `official_examples.csv` files.
   `spec.json` is written by `oracle.py --write-spec` from the table definition, and
   `oracle.py` refuses to run when the two differ.

## Deviations

1. **Folder layout.** FORMAT.md and PROTOCOL.md section 2 place each sample, including
   each sub-table, in its own folder `paperC/specs/<ID>/`. This branch was restricted to
   adding `paperC/specs/FR-APL/` and `paperC/specs/US-121/`, so the sub-tables are one
   level deeper: `paperC/specs/FR-APL/FR-APL-1/` … and `paperC/specs/US-121/US-121-1/`
   …. Each such folder holds exactly the files of FORMAT.md, and the harness reads a
   sample from the folder given to `--spec`
   (`python -m paperC.harness.run --spec paperC/specs/FR-APL/FR-APL-1 --out …`). If the
   harness needs `paperC/specs/<ID>/`, the seven folders can be moved up one level
   unchanged: `oracle.py` locates `paperC/catala_more` by a relative path
   (`../../../catala_more`), which would then need one `..` less.
2. **Split by subject.** FR-APL is split into five tables by subject (time and
   territory, floor area, rental tenure, logement-foyer, home buyers). The attributes of
   FR-APL-1, FR-APL-2 and FR-APL-3 alone would cross into 270 × 1,536 × 3,600 ≈ 1.5 × 10^9
   rows. Each table varies its own
   attributes and keeps Exemple1's household for the rest; FR-APL-4 fixes a foreign
   applicant meeting both nationality conditions (stated in its spec.json and
   CONVERSION.md).
3. **US-121 split by scope.** The official tests assert two different outputs of two
   scopes (`requirements_met` of `Section121SinglePerson`, and the excluded amount of
   `Section121TwoPersons`), so US-121 has one table per scope; each test maps onto the
   table of its own scope.
4. **Unmappable official tests.** Exemple2 and Exemple3 of
   `tests_eligibilite_apl.catala_fr` test the allocation de logement scope; they are
   re-run (and pass) and listed as unmappable in every FR-APL CONVERSION.md.
5. **Date domains.** FR-APL-4 and FR-APL-5 start their `date_courante` domain at
   2019-09-01; FR-APL-1 records that every earlier date is REJECTED for every input.
6. **Bands at the changes of output.** Interval attributes are cut at the thresholds
   the code compares against. For `date_courante`, which the code compares against
   many dates, the cuts are those at which this table's output or error status
   changes; the band check covers every day of the range to show that the other dates
   do not change the output for the table's inputs (listed in FR-APL-1 CONVERSION.md).
7. **Gain band.** US-121-2's lowest gain band starts above $0 (a zero gain has nothing
   to exclude).
8. **Helper code outside the folders.** `oracle.py` imports `oracle_common.py` and the
   input builders from `paperC/catala_more/`, so that the seven folders contain only the
   files FORMAT.md lists and the encoding build exists once.
9. **Extra oracle commands.** Besides `--enumerate` and `--check-official`, each
   `oracle.py` has `--check-bands`, `--write-official` and `--write-spec`.
10. **Python version.** The Catala 1.3.0 runtime needs Python 3.12 or later, so the
    oracles do too (the harness uses Python 3.12).
11. **US §121 Python build.** `clerk.toml` gives the `us-tax-code` target the OCaml
    backend only; the Python module was built with the file-level rule `clerk build
    us_tax_code/python/Us_tax_code.py`, and its tests are re-run by
    `paperC/catala_more/run_official_tests_us121.py` (clerk's Python test runner has no
    target to run).

## Correction of 2026-10-20: US-121-2

The independent verification (`paperC/verify/VERIFY-FR2.md`, branch
`paperc-verify-fr2`, "Substantive disagreement", item 1) found that the US-121-2
exclusion `person2_differs_on_single_return` rested on a wrong ground for
surviving-spouse returns. Its reason, "one taxpayer, so the person-2 labels describe no
return", holds for `single` returns. On a `surviving_spouse` row the person-2 labels
describe the deceased spouse (`DeadSpouseInfo.death_spouse_info_at_time_of_death`),
whose ownership, use and earlier sales 26 U.S.C. 121(b)(4) and (d)(2) take into
account; the scope `Section121TwoPersons` ignores that record
(`section_121.catala_en:101-105`), which is behaviour of the encoding and makes no row
legally impossible.

Correction (branch `paperc-data-fr2-fix`, folder `paperC/specs/US-121/US-121-2/` only):
the exclusion now applies to `single` rows; every `surviving_spouse` row is evaluated
through the encoding, with the person-2 labels in the deceased spouse's record; the
fixed date of the spouse's death moved from 2020-06-01 to 2020-12-31 so that the
person-2 periods, which end on the date of sale, end at the death. No other table, no
part of `paperC/PROTOCOL.md` and no part of `paperC/harness/` was changed.
US-121-2 CONVERSION.md section 11 gives the mapping, the statute and code lines, and
the checks.

| US-121-2 | \|D\| | valid | EXCLUDED | REJECTED | no_exclusion | entire_gain | limited_to_250000 | limited_to_500000 |
|---|---|---|---|---|---|---|---|---|
| before | 1,296 | 72 | 792 | 432 | 45 | 12 | 12 | 3 |
| after | 1,296 | 204 | 396 | 696 | 144 | 23 | 34 | 3 |

The 396 rows that left EXCLUDED became 264 REJECTED (person 1 has an earlier §121(a)
sale, the `DateError` of line 376), 99 `no_exclusion`, 11 `entire_gain` and 22
`limited_to_250000`; the other 900 rows keep their outputs. Their outputs never depend
on the person-2 labels (checked on all 432 surviving-spouse rows): the table records
that this scope treats a surviving spouse as a single filer. `--check-official` (6/6
direct, 2/2 mapped), `--enumerate`, `--write-official` (unchanged file) and
`--check-bands` (17,700 evaluations, all agreeing) were rerun and `SHA256SUMS`
regenerated.

Checks of the corrected table outside this folder:

* **Catala interpreter.** All 900 non-excluded rows (the 396 changed rows among them)
  were run as `#[test]` scopes with the Catala 1.3.0 interpreter: 204 label rows pass,
  696 REJECTED rows fail with the run-time error of `section_121.catala_en:376`, 0
  disagreements; a negative control was reported as a disagreement
  (`paperC/results/US-121-2-interpreter/`).
* **Harness.** `python3.12 -m paperC.harness.run --spec paperC/specs/US-121/US-121-2 --out
  paperC/results/US-121-2`: CTRL-HASH, CTRL-GT, CTRL-EXCL, CTRL-PLANT (422/422) pass;
  CTRL-H3 fails as PROTOCOL.md 7(c) expects with REJECTED rows; CTRL-DET passes.
* **Verifier's code** (copied to `paperC/verify-fix/`): recompute with the same controls,
  spot-check of all 1,296 rows (1,296 agree), and 0 differing cells out of 31,650 against
  the harness `runs.csv`.

`paperC/results/REPORT-US-121-2-FIX.md` gives the details and the hypothesis indicators.
