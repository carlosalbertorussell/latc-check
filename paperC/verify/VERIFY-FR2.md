# Independent verification: FR-APL-1..5, US-121-1, US-121-2

Branch `paperc-verify-fr2`, created from `origin/paperc-data-fr2` (commit `6566904`).
Protocol: `paperC/verify/PROTOCOL.md` and `paperC/verify/FORMAT.md`, copied verbatim from
`origin/paperc-harness`. Python 3.12.3, standard library only (plus the bundled Catala
1.3.0 runtime for step 2). Catala sources: catala-examples at
`2694b17ddd7c2246e207e8f077d586349ee5abea`, cloned fresh.

Independence: nothing under `paperC/harness/` was read on any branch, `latc_check` is not
imported, the spec folders' `oracle.py` and the converter's helper modules
(`oracle_common.py`, `fr_apl_common.py`, `apl_inputs.py`, `us121_inputs.py`) were neither
imported nor used, and no `paperC/results/` file of a `paperc-run-*` branch was read
before step 1 was committed (commit `Add independent recomputation ...`).

## Verdicts

| Sample | 1 Recompute (controls) | 2 Ground-truth spot-check | 3 Conversion audit | 4 Comparison with runner |
|---|---|---|---|---|
| FR-APL-1 | PASS | PASS (50/50) | PASS (minor items) | PASS (1266 rows identical) |
| FR-APL-2 | PASS | PASS (50/50) | PASS (minor items) | PASS (1266 rows identical) |
| FR-APL-3 | PASS | PASS (50/50) | PASS (minor items) | PASS (1266 rows identical) |
| FR-APL-4 | PASS | PASS (50/50) | PASS (minor items; one exclusion questionable) | PASS (1263 rows identical) |
| FR-APL-5 | PASS | PASS (50/50) | PASS (minor items) | PASS (1263 rows identical) |
| US-121-1 | PASS | PASS (12/12, all rows) | PASS | PASS (1266 rows identical) |
| US-121-2 | PASS | PASS (50/50) | **FAIL** (exclusion on a wrong legal ground for 396 rows) | PASS (1266 rows identical) |

"PASS" for step 1 means the recompute ran to completion with CTRL-HASH, CTRL-GT,
CTRL-EXCL and CTRL-PLANT passing. CTRL-H3 fails, as PROTOCOL.md 7(c) expects, in the five
samples with REJECTED rows (FR-APL-1, -2, -4, US-121-1, -2); that is a result about H3 and
says nothing against the sample.

## Step 1: recompute

Code: `paperC/verify/recompute.py`; readings of open points: `paperC/verify/READINGS.md`.
Outputs: `paperC/verify/<ID>/runs.csv`, `controls.csv`, `summary.md`.

| Sample | \|D\| | \|V\| | \|E\| | \|R\| | runs | CTRL-HASH | CTRL-GT | CTRL-EXCL | CTRL-PLANT | CTRL-H3 (max spurious_rejected) |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-APL-1 | 270 | 175 | 0 | 95 | 1266 | pass | pass | pass (0) | pass 422/422 | fail (95) |
| FR-APL-2 | 69120 | 67140 | 0 | 1980 | 1266 | pass | pass | pass (0) | pass 422/422 | fail (1980) |
| FR-APL-3 | 3600 | 3600 | 0 | 0 | 1266 | pass | pass | pass (0) | pass 422/422 | pass |
| FR-APL-4 | 1440 | 952 | 460 | 28 | 1263 | pass | pass | pass (0) | pass 421/421 | fail (28) |
| FR-APL-5 | 2880 | 2520 | 360 | 0 | 1263 | pass | pass | pass (0) | pass 421/421 | pass |
| US-121-1 | 12 | 4 | 0 | 8 | 1266 | pass | pass | pass (0) | pass 422/422 | fail (8) |
| US-121-2 | 1296 | 72 | 792 | 432 | 1266 | pass | pass | pass (0) | pass 422/422 | fail (432) |

The counts agree with the table of `paperC/specs/README-FR2.md`. FR-APL-4 and FR-APL-5
have no official example, so OFFICIAL is skipped there (421 example sets). Two runs into
separate directories gave byte-identical outputs (CTRL-DET, checked on FR-APL-1, -3,
US-121-2).

Values bearing on the hypotheses (from runs.csv):

| Sample | OFFICIAL unseen_values | OFFICIAL C1 missed_valid | OFFICIAL C1 reported_missing / true_gap | FULL C2 spurious_share |
|---|---|---|---|---|
| FR-APL-1 | 17 | 174 | 0 / 174 | 1.0 |
| FR-APL-2 | 37 | 67139 | 0 / 67139 | 1.0 |
| FR-APL-3 | 16 | 3599 | 0 / 3599 | 0.0 (G empty) |
| FR-APL-4 | - | - | - | 1.0 |
| FR-APL-5 | - | - | - | 1.0 |
| US-121-1 | 3 | 2 | -2 / 2 | 1.0 |
| US-121-2 | 11 | 70 | 0 / 70 | 1.0 |

US-121-1 shows the published missing count going negative: four official rows with two
distinct conditions give Π|observed| − len(rows) = 2 − 4 = −2 (READINGS.md item 3).

## Step 2: ground-truth spot-check

Code and per-row results: `paperC/verify/spotcheck/` (`spotcheck.py`, `<ID>.csv`,
`SPOTCHECK.md`, `summary.json`). Draw: one fresh `random.Random(20261020)` per sample,
`sorted(rng.sample(range(N), 50))` (all 12 rows of US-121-1); indices in SPOTCHECK.md.
The adapter builds the Catala inputs itself from the generated record classes and the
spec's representatives, with the FR-APL household transcribed by hand from Exemple1
(`tests_eligibilite_apl.catala_fr:16-107`). It was first validated on every official test
(US Test1–6 and Exemple1 reproduce their asserted values; every official_examples.csv
row maps to its listed output).

| Sample | Rows | Agree | Drawn outputs | REJECTED confirmation |
|---|---|---|---|---|
| FR-APL-1 | 50 | 50 | 15 eligible, 16 not_eligible, 19 REJECTED | `NoValue` Smic.catala_fr:13 (10), `NoValue` prologue.catala_fr:343 (8), `Conflict` Smic.catala_fr:443/489 (1) |
| FR-APL-2 | 50 | 50 | 5 eligible, 45 not_eligible | none drawn |
| FR-APL-3 | 50 | 50 | 50 not_eligible | none in table |
| FR-APL-4 | 50 | 50 | 20 eligible, 13 not_eligible, 16 EXCLUDED, 1 REJECTED | `Conflict` Smic.catala_fr:443/489 |
| FR-APL-5 | 50 | 50 | 1 eligible, 42 not_eligible, 7 EXCLUDED | none in table |
| US-121-1 | 12 | 12 | 1 met, 3 not met, 8 REJECTED | `DateError` section_121.catala_en:376 (8) |
| US-121-2 | 50 | 50 | 2 no_exclusion, 34 EXCLUDED, 14 REJECTED | `DateError` section_121.catala_en:376 (14) |

Supplementary (outside the verdict): the same adapter run on every row of every table
(78,618 rows) agrees everywhere, including the 32 eligible rows of FR-APL-3 and the
positive amounts of US-121-2 that the draw missed; 956 in-band probes changed no output.
The verifier re-ran `spotcheck.py` and got the same draw results.

EXCLUDED rows drawn: each satisfies an exclusion predicate and no non-excluded drawn row
does. What the encoding itself returns on them:

* FR-APL-4 `drom_convention_outside_drom`: the encoding ignores the flag outside the DROM
  (gives `eligible` on 5 of 13 drawn rows); exclusion justified by L861-5-1.
* FR-APL-4 `fjt_type_without_l353_2_convention`: the encoding gives `eligible` on 1 drawn
  row; see audit item 8.
* FR-APL-5 `loan_signed_after_decision_date`: encoding gives `not_eligible` (7/7);
  justified by L831-1 1°.
* US-121-2 `person2_differs_on_single_return`: encoding gives REJECTED on 24, and a
  normal amount on 10 (no_exclusion 6, entire_gain 3, limited_to_250000 1); see the
  finding below.

## Step 3: conversion audit

Full tables (one row per attribute, output, exclusion and fixed input):
`paperC/verify/audit/AUDIT.md`. All interval cut points were found at the comparisons in
the code (FR-APL-2 floor-area thresholds recomputed independently: 9, 13, 16, 18, 22, 25,
27, 31, 34, 36, 40, 43, 45, 49, 52 m², compared with `>=`); every enumeration lists all of
its constructors; the REJECTED mechanisms are where the notes say.

### Substantive disagreement

1. **US-121-2, exclusion `person2_differs_on_single_return` on `surviving_spouse` returns.**
   The spec's representative for `surviving_spouse` is
   `SingleReturnSurvivingSpouse content DeadSpouseInfo {return: (person 1), …,
   death_spouse_info_at_time_of_death: (person 2)}`, so the person-2 labels describe the
   deceased spouse, a real second person whose facts §121(b)(4) uses. The exclusion's
   stated reason ("there is one taxpayer … describes no return") holds for `single`
   returns; for surviving spouses it describes the behaviour of the scope
   (`section_121.catala_en:101-105` sets person2 to `data_single.return`, confirmed by the
   verifier) and gives no legal impossibility. 396 of the 792 EXCLUDED rows are affected.
   The kept rows' outputs are unaffected. Consequence for Paper C: these 396 rows count as
   "spurious_excluded" under C2, so they inflate the H2 measure for US-121-2; they would
   rather belong to V (the encoding ignores person 2 there) or be removed from D by a
   representative that leaves person 2 unused, with the exclusion described as a table
   design choice.

### Questionable exclusion (minor, stated for the author)

8. **FR-APL-4 `fjt_type_without_l353_2_convention` (180 rows).** R832-20 3° refers to a
   foyer that "a fait l'objet" of a pre-1995 L353-2 convention (past fact); the code reads
   the flag as a convention in force (L831-1 5°). An FJT whose old convention has lapsed is
   possible, and the encoding returns `eligible` on one such drawn row. The assumption
   should be stated in CONVERSION.md, or the rows kept.

### Minor citation and wording items

2. All FR-APL tables: output rule cited `LEG:631-645` ends at 646.
3. FR-APL-1/2 `residence`: CONVERSION.md says "declared order", but `Métropole` is
   declared seventh in the enumeration.
4. FR-APL-1/2 `nationalite_demandeur`: cited 228-247; the relevant text is 228-244.
5. FR-APL-1: the 2021-01-01 cut is attributed to L860-3 I, whose quoted text has no date;
   the date comes from the encoding (`LEG:1337`).
6. FR-APL-1..5: the fixed-input boilerplate repeats Exemple1 values for fields that are
   attributes of the table (and, for FR-APL-4/5, values that contradict that table's own
   fixed inputs).
7. FR-APL-2: `personnes_a_charge` 0..3 and `autres_occupants` 0..1 are restricted ranges
   the spec does not state as a choice.
9. FR-APL-5: exclusion source `LEG:648-657` starts on a blank line; R832-5 is the more
   direct authority.
10. US-121-2: the exclusion cites 26 U.S.C. 121(b)(1), which does not bear on it.
11. US-121-2: person-2 ownership source `S121:50-57` runs past `PersonalData` (50-54).

## Step 4: comparison with the runner

Compared with `origin/paperc-run-fr2` at commit `eb508e7` ("Phase 2 runner: harness
results and REPORT-FR2 ..."), files `paperC/results/<ID>/runs.csv`, read only after
steps 1 to 3 were committed. Script: `paperC/verify/compare.py`, plus a byte comparison of
the files without their header line.

| Sample | Rows | Data rows byte-identical | Shared cells compared | Cells differing |
|---|---|---|---|---|
| FR-APL-1 | 1266 | yes | 29118 | 0 |
| FR-APL-2 | 1266 | yes | 29118 | 0 |
| FR-APL-3 | 1266 | yes | 29118 | 0 |
| FR-APL-4 | 1263 | yes | 29049 | 0 |
| FR-APL-5 | 1263 | yes | 29049 | 0 |
| US-121-1 | 1266 | yes | 29118 | 0 |
| US-121-2 | 1266 | yes | 29118 | 0 |

The only difference is two header names: the runner writes `sample_id` and `size` where
the verifier writes `sample` and `n` (READINGS.md item 1). With those two names
substituted, each header is identical too, so the column order and every value
(including every float `repr`) agree. Two independent implementations of PROTOCOL.md give
the same 8,856 runs.

The runner's `controls.csv` gives the same verdicts per sample: CTRL-HASH, CTRL-GT,
CTRL-EXCL pass; CTRL-PLANT passes on every example set (422, or 421 without OFFICIAL,
plus one aggregate row `ALL`); CTRL-H3 fails in FR-APL-1, -2, -4, US-121-1, -2 and passes
in FR-APL-3 and FR-APL-5. The `summary.md` files were not compared cell by cell (the
layouts are each implementation's own).
