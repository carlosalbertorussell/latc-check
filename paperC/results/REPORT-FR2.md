# Paper C, Phase 2 runner report: FR-APL-1 to FR-APL-5, US-121-1, US-121-2

Branch `paperc-run-fr2`, created from `origin/paperc-data-fr2` (`6566904`) with
`origin/paperc-harness` merged in (merge commit `ac30804`, no conflict). Protocol:
`paperC/PROTOCOL.md`, registered at `ee7c527`. `paperC/PROTOCOL.md`, `paperC/harness/`,
`paperC/specs/` and `latc_check/` were left unchanged; every manifest records
`harness_commit` = `ac308042bd9614c308fa33f447f8a9f626c25d5f` and
`tracked_inputs_unmodified` = true. Python 3.12.3 (CPython), 4 CPUs.

Every number below is copied from the harness outputs (`summary.md`, `controls.csv`,
`runs.csv`, `determinism.json` in `paperC/results/<ID>/`). Statistics tables were
extracted from `summary.md` by a parser that only rearranges its cells (4 decimals, as
`summary.md` prints them); nothing was recomputed.

## Pre-run checks

| check | command | result |
|---|---|---|
| merge | `git merge --no-edit origin/paperc-harness` | clean, paths disjoint |
| harness unit tests | `python3.12 -m unittest discover -s paperC/harness/tests -t .` | 23 of 23 pass |
| repository tests | `python3.12 -I -m unittest discover tests` | 14 import errors (see deviation 1) |
| repository tests | `python3.12 -I -m unittest discover -s tests -t .` | 157 of 157 pass |
| repository tests | `python3.12 -m unittest discover tests` | 157 of 157 pass |

## Runs, wall time and CTRL-DET

Command per sample (FR-APL under `paperC/specs/FR-APL/<ID>`, US-121 under
`paperC/specs/US-121/<ID>`, as README-FR2.md deviation 1 describes):

```
python3.12 -m paperC.harness.run --spec paperC/specs/FR-APL/FR-APL-1 --out paperC/results/FR-APL-1
python3.12 -m paperC.harness.determinism --spec paperC/specs/FR-APL/FR-APL-1 --report paperC/results/FR-APL-1/determinism.json
```

The harness reads the folder given to `--spec` and names the sample by its basename, so
the extra folder level needed no change. Runs were made in two parallel streams
(FR-APL-2 alone; the other six in sequence), and the CTRL-DET runs likewise, so wall
times include contention for 2 of 4 CPUs. Wall time is measured around the whole
command (`date` before and after).

| sample | runs (rows of runs.csv) | exit | run wall time (s) | CTRL-DET | CTRL-DET wall time (s, two clones) | committed outputs = clone outputs |
|---|---|---|---|---|---|---|
| FR-APL-1 | 1266 | 0 | 1.13 | pass | 3.50 | yes |
| FR-APL-2 | 1266 | 0 | 230.61 | pass | 464.75 | yes |
| FR-APL-3 | 1266 | 0 | 10.44 | pass | 24.13 | yes |
| FR-APL-4 | 1263 | 0 | 3.72 | pass | 9.09 | yes |
| FR-APL-5 | 1263 | 0 | 8.46 | pass | 18.97 | yes |
| US-121-1 | 1266 | 0 | 0.84 | pass | 2.46 | yes |
| US-121-2 | 1266 | 0 | 2.47 | pass | 5.71 | yes |

CTRL-DET was run at commit `ac30804`, the same commit at which the committed outputs
were produced (the results were still uncommitted, and `determinism` clones only
committed files). The sha256 of the four local outputs equals `run_a` and `run_b` in
every `determinism.json`. FR-APL-4 and FR-APL-5 have 1,263 runs because OFFICIAL is
skipped there (no official example).

## Controls overview

| sample | \|D\| | \|V\| | \|E\| | \|R\| | official rows | CTRL-HASH | CTRL-GT | CTRL-EXCL | CTRL-PLANT | CTRL-H3 | CTRL-DET |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FR-APL-1 | 270 | 175 | 0 | 95 | 1 | pass | pass | pass (0) | pass 422/422 | **fail** 0/422 | pass |
| FR-APL-2 | 69120 | 67140 | 0 | 1980 | 1 | pass | pass | pass (0) | pass 422/422 | **fail** 0/422 | pass |
| FR-APL-3 | 3600 | 3600 | 0 | 0 | 1 | pass | pass | pass (0) | pass 422/422 | pass 422/422 | pass |
| FR-APL-4 | 1440 | 952 | 460 | 28 | 0 | pass | pass | pass (0) | pass 421/421 | **fail** 0/421 | pass |
| FR-APL-5 | 2880 | 2520 | 360 | 0 | 0 | pass | pass | pass (0) | pass 421/421 | pass 421/421 | pass |
| US-121-1 | 12 | 4 | 0 | 8 | 4 | pass | pass | pass (0) | pass 422/422 | **fail** 0/422 | pass |
| US-121-2 | 1296 | 72 | 792 | 432 | 2 | pass | pass | pass (0) | pass 422/422 | **fail** 0/422 | pass |

CTRL-FULL has a pass criterion only for CTRL-NUR; it is recorded per sample below.
CTRL-H3 fails on exactly the five samples with R non-empty, as PROTOCOL.md 7(c)
anticipates: in every such C3 run the generated set contains all of R (C3 `spurious` =
\|R\| in every UNIFORM and ZIPF cell, p2.5 = p97.5 = \|R\|), so no C3 run on these
samples is COMPLETE. On the two samples with R empty (FR-APL-3, FR-APL-5) every C3 run
is COMPLETE.

## Hypothesis indicators (this branch only)

The decisions of PROTOCOL.md section 8 are taken over all legal samples of every data
branch; the indicators below are this branch's contribution.

| sample | H1: OFFICIAL unseen_values > 0 | H1: OFFICIAL C1 missed_valid > 0 | OFFICIAL C1 reported_missing vs true_gap | H2: FULL C2 spurious_share ≥ 0.10 | H3: CTRL-H3 |
|---|---|---|---|---|---|
| FR-APL-1 | yes (17) | yes (174) | 0 vs 174 | yes (1.0000) | fail, \|R\| = 95 |
| FR-APL-2 | yes (37) | yes (67139) | 0 vs 67139 | yes (1.0000) | fail, \|R\| = 1980 |
| FR-APL-3 | yes (16) | yes (3599) | 0 vs 3599 | no (0.0000) | pass |
| FR-APL-4 | no OFFICIAL rows | no OFFICIAL rows | - | yes (1.0000) | fail, \|R\| = 28 |
| FR-APL-5 | no OFFICIAL rows | no OFFICIAL rows | - | yes (1.0000) | pass, \|R\| = 0 |
| US-121-1 | yes (3) | yes (2) | -2 vs 2 | yes (1.0000) | fail, \|R\| = 8 |
| US-121-2 | yes (11) | yes (70) | 0 vs 70 | yes (1.0000) | fail, \|R\| = 432 |

On this branch: H1 indicators hold on 5 of the 5 samples with official rows (both
indicators); the H2 indicator holds on 6 of 7; H3 holds on 2 of 7 (FR-APL-3, FR-APL-5),
and the 5 samples with R non-empty are the 5 failures.

H2 secondary quantities (reported without decision): OFFICIAL spurious_share C1 / C2 =
FR-APL-1 0.0000 / 0.3532, FR-APL-2 0.0000 / 0.0286, FR-APL-3 0.0000 / 0.0000,
US-121-1 0.0000 / 0.8000, US-121-2 0.0000 / 0.9459. Median spurious_share over seeds at
UNIFORM n = 1000, C1 / C2: FR-APL-1 1.0000 / 1.0000, FR-APL-2 0.0291 / 0.0291,
FR-APL-3 0.0000 / 0.0000, FR-APL-4 0.5951 / 0.5951, FR-APL-5 0.1753 / 0.1753,
US-121-1 0.0000 / 1.0000, US-121-2 1.0000 / 1.0000.

## Observations

1. **The H2 indicator under FULL is binary by construction.** With FULL, X = V, so C2
   generates exactly D \ V = E ∪ R; spurious_share is then 1 whenever E ∪ R is
   non-empty and 0 otherwise. The harness output agrees on all seven samples (C2 FULL
   workload = \|E\| + \|R\|: 95, 1980, 0, 488, 360, 8, 1224). On this branch the
   ≥ 0.10 threshold therefore separates FR-APL-3 (no E, no R) from the rest, and the
   share says nothing about how large the impossible part is relative to the table. The
   UNIFORM n = 1000 medians above (0.0291 on FR-APL-2, 0.5951 on FR-APL-4) carry that
   information.
2. **C1 can beat C2 and C3 when a declared value occurs only in REJECTED or EXCLUDED
   rows.** Such values never appear among valid examples, so the observed domains of C1
   leave them out. On US-121-1 (`other_section_121a_sale` = `within_2_years` and
   `more_than_2_years` are REJECTED in every row) C1 is COMPLETE in 30/30 seeds at every
   UNIFORM size and at every ZIPF size from n = 20 (27/30 at ZIPF n = 10), while C2 and
   C3 add the 8 REJECTED rows in every run and are COMPLETE in 0/30. FULL C1 on US-121-1
   is COMPLETE with workload 0. FULL `unseen_values` counts such values: FR-APL-1 2,
   US-121-1 2, US-121-2 4, the others 0. On FR-APL-1 the same effect lowers C1 spurious
   to 5 rows (the 2024 Mayotte `Conflict` rows, whose values do occur in valid rows)
   against 95 for C2 and C3, though C1 is still never COMPLETE there. On US-121-2 C1
   still generates 72 spurious rows at every n ≥ 50 (FULL C1 workload 72, all spurious).
3. **Negative LATC missing count.** On US-121-1, OFFICIAL has 4 rows over 2 distinct
   conditions (Test1 = Test4, Test2 = Test3), so `missing_count` = product of observed
   cardinalities (2) minus 4 rows = -2, and C2/C3 `reported_missing` = 8 while their
   workload is 10. `missing_count` counts rows, so duplicate examples make it
   under-report even below zero; the harness reports it as defined in section 4.
4. **Labelling workload on FR-APL-2.** C2 and C3 generate essentially the whole table
   at every size (mean workload 69,110.0 at UNIFORM n = 10, 68,127.8 at n = 1000, out
   of \|D\| = 69,120), and C1 reaches the same workload once every declared value has
   been seen (identical C1 and C2 rows from n = 1000 UNIFORM). Valid coverage of 1 is
   reached by enumeration; 1,980 of the generated rows are REJECTED in every C2 and C3
   run.
5. **C1 under random sources.** At n = 10 the mean C1 valid coverage is below 1 on
   every sample except US-121-1 (lowest: FR-APL-2, 0.2400 UNIFORM and 0.1839 ZIPF).
   C1 valid coverage is 1 in every seed (p2.5 = 1) from n = 50 on FR-APL-3, US-121-2
   and FR-APL-5 UNIFORM; from n = 100 on FR-APL-1, FR-APL-4, FR-APL-2 UNIFORM and
   FR-APL-5 ZIPF; from n = 200 on FR-APL-2 ZIPF. Its COMPLETE share is non-zero only on
   FR-APL-3 (UNIFORM 11/30, 28/30, then 30/30 from n = 50; ZIPF 5/30, 21/30, then
   30/30 from n = 50) and US-121-1; on the other five samples it is 0/30 in every cell:
   each such run either misses valid rows or generates E or R rows.
6. **REJECTED rows dominate the H3 failures.** On FR-APL-1, -2 and -4 and on US-121-1/-2,
   CTRL-EXCL passes (spec exclusions match EXCLUDED rows exactly) and every C3 failure
   is `spurious_rejected`: these are run-time errors of the Catala code (README-FR2.md:
   `NoValue`, `Conflict`, `DateError` at `section_121.catala_en:376`). The declared
   domains plus exclusions recover V exactly on every sample where the encoding never
   errors.

## Small valid spaces (US-121-1, |V| = 4; US-121-2, |V| = 72)

The harness marks every run with n > \|V\| in `size_exceeds_valid`; `summary.md` lists
those sizes: US-121-1 all seven sizes (10 to 1000), US-121-2 n ∈ {100, 200, 500, 1000},
FR-APL-1 n ∈ {200, 500, 1000}, FR-APL-4 n = 1000. Draws stay with replacement.

* On US-121-1 the size axis carries almost no information. Mean `true_gap` is 0.2667
  (UNIFORM) and 0.5333 (ZIPF) at n = 10, 0.0333 at n = 20, and 0 from n = 50 on, so
  from n = 50 every seed draws all 4 valid states and every metric is constant across
  seeds and sizes (C1 workload 0; C2 and C3 workload 8, spurious 8). The Wilson
  intervals at 30/30 and 0/30 ([0.8865, 1.0000] and [0.0000, 0.1135]) are the only
  non-degenerate statistics left; the 2.5 to 97.5 % ranges are single points.
* On US-121-2, mean `true_gap` falls to 0 at UNIFORM n = 1000 (0.7667 at ZIPF n = 1000,
  whose 1/k weights leave the tail ranks rarely drawn). From n = 50 on, every C1, C2 and
  C3 cell has valid coverage 1 in every seed and constant spurious counts (72, 1224,
  432), and only the workload falls with n.
* Neither sample breaks the harness: sizes above \|V\| run as specified, and the flag
  makes them identifiable in `runs.csv`. For the paper, the sizes above \|V\| are
  repeated draws from a saturated sample and should be read as such.

## Deviations

1. **Repository test command.** `python3.12 -I -m unittest discover tests`, as given in
   the task, fails with 14 `ModuleNotFoundError: No module named 'latc_check'`: with
   `-I` the current directory is not on `sys.path`, and `discover tests` puts only
   `tests/` there. `python3.12 -I -m unittest discover -s tests -t .` (top-level dir set
   to the repository root) and the same command without `-I` both run 157 of 157 tests
   with no failure. No code was changed; I treated this as an invocation issue and went
   on.
2. **Folder layout.** As stated in README-FR2.md deviation 1, the samples sit one level
   deeper than `paperC/specs/<ID>/`; `--spec` was given that folder, and results were
   written to `paperC/results/<ID>/` as the task specified.
3. **Parallel execution.** Two harness processes ran at once (see the wall-time table).
   The outputs do not depend on this (CTRL-DET passes and the committed outputs equal
   the clone outputs); only the wall times do.
4. **Harness commit.** The outputs record the merge commit `ac30804` as
   `harness_commit`, since the harness code is identical to `paperc-harness` but the
   checkout is the merged branch.

No pre-registered number, procedure or file was changed.

## Per-sample results

### FR-APL-1

Aide personnalisée au logement (APL): eligibility by date, territory and applicant nationality

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 270 | 175 | 0 | 95 | 1 | 3 |

Sizes exceeding |V| (draws stay with replacement): [200, 500, 1000].

**Controls** (`controls.csv` per example set; CTRL-DET pass, see above)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 270 | 270 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=5; workload=5 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 0 | 422 | 0 | C3 runs with valid_coverage = 1 and spurious = 0; |R| = 95 |

**OFFICIAL and FULL**

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 1 | 17 | 0 | 174 | 0 | 0.0057 | 174 | 0 | 0.0000 | 0 | 0 | 0 |
| OFFICIAL | C2 | 1 | 17 | 269 | 174 | 269 | 1.0000 | 0 | 95 | 0.3532 | 0 | 0 | 0 |
| OFFICIAL | C3 | 1 | 17 | 269 | 174 | 269 | 1.0000 | 0 | 95 | 0.3532 | 0 | 0 | 0 |
| FULL | C1 | 175 | 2 | 5 | 0 | 5 | 1.0000 | 0 | 5 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 175 | 2 | 95 | 0 | 95 | 1.0000 | 0 | 95 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 175 | 2 | 95 | 0 | 95 | 1.0000 | 0 | 95 | 1.0000 | 0 | 0 | 0 |

**Hypothesis indicators emitted by the harness**

* H1: OFFICIAL unseen_values = 17 (> 0: True); C1 missed_valid = 174 (> 0: True); C1 reported_missing = 0, true_gap = 174.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 0 (0/422 C3 runs complete; |R| = 95).

**UNIFORM and ZIPF** (30 seeds per cell; valid_coverage with its 2.5 to 97.5 % range; spurious = rows of G in E ∪ R; workload = rows generated; COMPLETE share with Wilson 95% interval)

| source | n | cond | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | true_gap mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---|---|---|---|---|---|---|
| UNIFORM | 10 | C1 | 0.5760 [0.3200, 0.8314] | 74.2000 | 2.5667 [0.0000, 5.0000] | 93.7000 | 165.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 260.3333 | 165.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 260.3333 | 165.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C1 | 0.9067 [0.7714, 1.0000] | 16.3333 | 4.6667 [0.0000, 5.0000] | 144.4000 | 156.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 251.0667 | 156.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 251.0667 | 156.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C1 | 0.9962 [0.9686, 1.0000] | 0.6667 | 5.0000 [5.0000, 5.0000] | 135.6667 | 131.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 226.3333 | 131.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 226.3333 | 131.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 103.3667 | 98.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 193.3667 | 98.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 193.3667 | 98.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 59.4000 | 54.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 149.4000 | 54.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 149.4000 | 54.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 14.8000 | 9.8000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 104.8000 | 9.8000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 104.8000 | 9.8000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 5.4333 | 0.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 95.4333 | 0.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 95.4333 | 0.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C1 | 0.4775 [0.2460, 0.7793] | 91.4333 | 1.5667 [0.0000, 5.0000] | 77.1000 | 166.9667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 261.9667 | 166.9667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 261.9667 | 166.9667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C1 | 0.7562 [0.4860, 0.9379] | 42.6667 | 3.0667 [0.0000, 5.0000] | 121.1000 | 160.7000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 255.7000 | 160.7000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 255.7000 | 160.7000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C1 | 0.9762 [0.8857, 1.0000] | 4.1667 | 4.5000 [0.0000, 5.0000] | 145.5000 | 145.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 240.1667 | 145.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 240.1667 | 145.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 131.3667 | 126.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 221.3667 | 126.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 221.3667 | 126.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 104.2000 | 99.2000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 194.2000 | 99.2000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 194.2000 | 99.2000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 62.2333 | 57.2333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 152.2333 | 57.2333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 152.2333 | 57.2333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 5.0000 [5.0000, 5.0000] | 31.4000 | 26.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 121.4000 | 26.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 95.0000 [95.0000, 95.0000] | 121.4000 | 26.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |


### FR-APL-2

Aide personnalisée au logement (APL): eligibility by household size and floor area

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 69120 | 67140 | 0 | 1980 | 1 | 7 |

**Controls** (`controls.csv` per example set; CTRL-DET pass, see above)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 69120 | 69120 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=1980; workload=1980 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 0 | 422 | 0 | C3 runs with valid_coverage = 1 and spurious = 0; |R| = 1980 |

**OFFICIAL and FULL**

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 1 | 37 | 0 | 67139 | 0 | 0.0000 | 67139 | 0 | 0.0000 | 0 | 0 | 0 |
| OFFICIAL | C2 | 1 | 37 | 69119 | 67139 | 69119 | 1.0000 | 0 | 1980 | 0.0286 | 0 | 0 | 0 |
| OFFICIAL | C3 | 1 | 37 | 69119 | 67139 | 69119 | 1.0000 | 0 | 1980 | 0.0286 | 0 | 0 | 0 |
| FULL | C1 | 67140 | 0 | 1980 | 0 | 1980 | 1.0000 | 0 | 1980 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 67140 | 0 | 1980 | 0 | 1980 | 1.0000 | 0 | 1980 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 67140 | 0 | 1980 | 0 | 1980 | 1.0000 | 0 | 1980 | 1.0000 | 0 | 0 | 0 |

**Hypothesis indicators emitted by the harness**

* H1: OFFICIAL unseen_values = 37 (> 0: True); C1 missed_valid = 67139 (> 0: True); C1 reported_missing = 0, true_gap = 67139.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 0 (0/422 C3 runs complete; |R| = 1980).

**UNIFORM and ZIPF** (30 seeds per cell; valid_coverage with its 2.5 to 97.5 % range; spurious = rows of G in E ∪ R; workload = rows generated; COMPLETE share with Wilson 95% interval)

| source | n | cond | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | true_gap mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---|---|---|---|---|---|---|
| UNIFORM | 10 | C1 | 0.2400 [0.1407, 0.3751] | 51024.7333 | 330.6000 [0.0000, 1034.1250] | 16435.8667 | 67130.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69110.0000 | 67130.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69110.0000 | 67130.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C1 | 0.6323 [0.4435, 0.8106] | 24684.9667 | 1253.7667 [0.0000, 1809.2500] | 43688.8333 | 67120.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69100.0333 | 67120.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69100.0333 | 67120.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C1 | 0.9564 [0.8578, 1.0000] | 2929.6667 | 1885.6667 [1617.0000, 1980.0000] | 66046.1000 | 67090.1000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69070.1000 | 67090.1000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69070.1000 | 67090.1000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69020.1667 | 67040.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69020.1667 | 67040.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69020.1667 | 67040.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68920.3333 | 66940.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68920.3333 | 66940.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68920.3333 | 66940.3333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68622.0667 | 66642.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68622.0667 | 66642.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68622.0667 | 66642.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68127.8333 | 66147.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68127.8333 | 66147.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68127.8333 | 66147.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C1 | 0.1839 [0.0608, 0.3257] | 54792.6333 | 220.6333 [0.0000, 750.6000] | 12558.5667 | 67130.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69110.5667 | 67130.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69110.5667 | 67130.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C1 | 0.5767 [0.3536, 0.7307] | 28418.5667 | 1022.8333 [0.0000, 1662.7500] | 39726.0000 | 67121.7333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69101.7333 | 67121.7333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69101.7333 | 67121.7333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C1 | 0.9134 [0.8024, 1.0000] | 5816.0000 | 1732.0000 [971.5000, 1980.0000] | 63014.1667 | 67098.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69078.1667 | 67098.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69078.1667 | 67098.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C1 | 0.9979 [0.9825, 1.0000] | 142.3333 | 1978.3333 [1966.2500, 1980.0000] | 68897.6000 | 67061.6000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69041.6000 | 67061.6000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 69041.6000 | 67061.6000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68973.6333 | 66993.6333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68973.6333 | 66993.6333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68973.6333 | 66993.6333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68790.6667 | 66810.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68790.6667 | 66810.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68790.6667 | 66810.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68518.5333 | 66538.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68518.5333 | 66538.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1980.0000 [1980.0000, 1980.0000] | 68518.5333 | 66538.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |


### FR-APL-3

Aide personnalisée au logement (APL): eligibility of tenants and sub-tenants

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 3600 | 3600 | 0 | 0 | 1 | 8 |

**Controls** (`controls.csv` per example set; CTRL-DET pass, see above)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 3600 | 3600 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=0; workload=0 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 422 | 422 | 1 | C3 runs with valid_coverage = 1 and spurious = 0; |R| = 0 |

**OFFICIAL and FULL**

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 1 | 16 | 0 | 3599 | 0 | 0.0003 | 3599 | 0 | 0.0000 | 0 | 0 | 0 |
| OFFICIAL | C2 | 1 | 16 | 3599 | 3599 | 3599 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| OFFICIAL | C3 | 1 | 16 | 3599 | 3599 | 3599 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C1 | 3600 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C2 | 3600 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C3 | 3600 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |

**Hypothesis indicators emitted by the harness**

* H1: OFFICIAL unseen_values = 16 (> 0: True); C1 missed_valid = 3599 (> 0: True); C1 reported_missing = 0, true_gap = 3599.
* H2: FULL C2 spurious_share = 0.0000 (>= 0.10: False).
* H3: CTRL-H3 pass = 1 (422/422 C3 runs complete; |R| = 0).

**UNIFORM and ZIPF** (30 seeds per cell; valid_coverage with its 2.5 to 97.5 % range; spurious = rows of G in E ∪ R; workload = rows generated; COMPLETE share with Wilson 95% interval)

| source | n | cond | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | true_gap mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---|---|---|---|---|---|---|
| UNIFORM | 10 | C1 | 0.7716 [0.4193, 1.0000] | 822.4000 | 0.0000 [0.0000, 0.0000] | 2767.6000 | 3590.0000 | 11/30 = 0.3667 [0.2187, 0.5449] |
| UNIFORM | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3590.0000 | 3590.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3590.0000 | 3590.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 20 | C1 | 0.9867 [0.8000, 1.0000] | 48.0000 | 0.0000 [0.0000, 0.0000] | 3532.0667 | 3580.0667 | 28/30 = 0.9333 [0.7868, 0.9815] |
| UNIFORM | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3580.0667 | 3580.0667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3580.0667 | 3580.0667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 50 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3550.3000 | 3550.3000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3550.3000 | 3550.3000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3550.3000 | 3550.3000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3501.2333 | 3501.2333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3501.2333 | 3501.2333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3501.2333 | 3501.2333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3405.1000 | 3405.1000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3405.1000 | 3405.1000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3405.1000 | 3405.1000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3132.5000 | 3132.5000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3132.5000 | 3132.5000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3132.5000 | 3132.5000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2728.0000 | 2728.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2728.0000 | 2728.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2728.0000 | 2728.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 10 | C1 | 0.6841 [0.3876, 1.0000] | 1137.0667 | 0.0000 [0.0000, 0.0000] | 2453.4333 | 3590.5000 | 5/30 = 0.1667 [0.0734, 0.3356] |
| ZIPF | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3590.5000 | 3590.5000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3590.5000 | 3590.5000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 20 | C1 | 0.9213 [0.6107, 1.0000] | 283.2000 | 0.0000 [0.0000, 0.0000] | 3299.2000 | 3582.4000 | 21/30 = 0.7000 [0.5212, 0.8334] |
| ZIPF | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3582.4000 | 3582.4000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3582.4000 | 3582.4000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 50 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3560.5333 | 3560.5333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3560.5333 | 3560.5333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3560.5333 | 3560.5333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3528.8000 | 3528.8000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3528.8000 | 3528.8000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3528.8000 | 3528.8000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3474.4000 | 3474.4000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3474.4000 | 3474.4000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3474.4000 | 3474.4000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3338.8000 | 3338.8000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3338.8000 | 3338.8000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3338.8000 | 3338.8000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3156.3667 | 3156.3667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3156.3667 | 3156.3667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 3156.3667 | 3156.3667 | 30/30 = 1.0000 [0.8865, 1.0000] |


### FR-APL-4

Aide personnalisée au logement (APL): eligibility of residents of a logement-foyer

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 1440 | 952 | 460 | 28 | 0 | 6 |

official_examples.csv has no data rows, so the OFFICIAL source is skipped.

Sizes exceeding |V| (draws stay with replacement): [1000].

**Controls** (`controls.csv` per example set; CTRL-DET pass, see above)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 1440 | 1440 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=488; workload=488 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 421 | 421 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 0 | 421 | 0 | C3 runs with valid_coverage = 1 and spurious = 0; |R| = 28 |

**OFFICIAL and FULL**

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FULL | C1 | 952 | 0 | 488 | 0 | 488 | 1.0000 | 0 | 488 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 952 | 0 | 488 | 0 | 488 | 1.0000 | 0 | 488 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 952 | 0 | 28 | 0 | 28 | 1.0000 | 0 | 28 | 1.0000 | 0 | 0 | 0 |

**Hypothesis indicators emitted by the harness**

* H1: no OFFICIAL rows; this sample does not enter the H1 decision.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 0 (0/421 C3 runs complete; |R| = 28).

**UNIFORM and ZIPF** (30 seeds per cell; valid_coverage with its 2.5 to 97.5 % range; spurious = rows of G in E ∪ R; workload = rows generated; COMPLETE share with Wilson 95% interval)

| source | n | cond | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | true_gap mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---|---|---|---|---|---|---|
| UNIFORM | 10 | C1 | 0.5758 [0.3345, 0.8412] | 403.8000 | 209.4000 [48.0000, 383.5000] | 747.6333 | 942.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1430.0333 | 942.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 970.0333 | 942.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C1 | 0.8946 [0.7059, 1.0000] | 100.3333 | 391.0000 [264.9000, 488.0000] | 1222.8333 | 932.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1420.1667 | 932.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 960.1667 | 932.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C1 | 0.9951 [0.9265, 1.0000] | 4.6667 | 482.0000 [398.0000, 488.0000] | 1380.5000 | 903.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1391.1667 | 903.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 931.1667 | 903.1667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1344.6667 | 856.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1344.6667 | 856.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 884.6667 | 856.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1258.3667 | 770.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1258.3667 | 770.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 798.3667 | 770.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1050.0333 | 562.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1050.0333 | 562.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 590.0333 | 562.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 818.8333 | 330.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 818.8333 | 330.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 358.8333 | 330.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C1 | 0.5027 [0.2148, 0.7646] | 473.4000 | 184.3333 [37.0500, 388.2500] | 654.3000 | 943.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1431.3667 | 943.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 971.3667 | 943.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C1 | 0.8555 [0.5346, 1.0000] | 137.5333 | 375.6667 [168.9000, 488.0000] | 1173.4000 | 935.2667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1423.2667 | 935.2667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 963.2667 | 935.2667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C1 | 0.9814 [0.9143, 1.0000] | 17.7333 | 468.4000 [398.0000, 488.0000] | 1367.4000 | 916.7333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1404.7333 | 916.7333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 944.7333 | 916.7333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1378.4000 | 890.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1378.4000 | 890.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 918.4000 | 890.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1334.1333 | 846.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1334.1333 | 846.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 874.1333 | 846.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1232.6667 | 744.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1232.6667 | 744.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 772.6667 | 744.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1110.3667 | 622.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 488.0000 [488.0000, 488.0000] | 1110.3667 | 622.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 28.0000 [28.0000, 28.0000] | 650.3667 | 622.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |


### FR-APL-5

Aide personnalisée au logement (APL): eligibility of home buyers (accession and location-accession)

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 2880 | 2520 | 360 | 0 | 0 | 8 |

official_examples.csv has no data rows, so the OFFICIAL source is skipped.

**Controls** (`controls.csv` per example set; CTRL-DET pass, see above)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 2880 | 2880 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=360; workload=360 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 421 | 421 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 421 | 421 | 1 | C3 runs with valid_coverage = 1 and spurious = 0; |R| = 0 |

**OFFICIAL and FULL**

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FULL | C1 | 2520 | 0 | 360 | 0 | 360 | 1.0000 | 0 | 360 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 2520 | 0 | 360 | 0 | 360 | 1.0000 | 0 | 360 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 2520 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |

**Hypothesis indicators emitted by the harness**

* H1: no OFFICIAL rows; this sample does not enter the H1 decision.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 1 (421/421 C3 runs complete; |R| = 0).

**UNIFORM and ZIPF** (30 seeds per cell; valid_coverage with its 2.5 to 97.5 % range; spurious = rows of G in E ∪ R; workload = rows generated; COMPLETE share with Wilson 95% interval)

| source | n | cond | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | true_gap mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---|---|---|---|---|---|---|
| UNIFORM | 10 | C1 | 0.8035 [0.5610, 1.0000] | 495.2000 | 220.0000 [0.0000, 360.0000] | 2234.8000 | 2510.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2870.0000 | 2510.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2510.0000 | 2510.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 20 | C1 | 0.9867 [0.8000, 1.0000] | 33.6000 | 355.2000 [288.0000, 360.0000] | 2821.6333 | 2500.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2860.0333 | 2500.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2500.0333 | 2500.0333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 50 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2830.3000 | 2470.3000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2830.3000 | 2470.3000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2470.3000 | 2470.3000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2782.1333 | 2422.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2782.1333 | 2422.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2422.1333 | 2422.1333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2687.6667 | 2327.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2687.6667 | 2327.6667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2327.6667 | 2327.6667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2425.6000 | 2065.6000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2425.6000 | 2065.6000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2065.6000 | 2065.6000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2052.8333 | 1692.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2052.8333 | 1692.8333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 1692.8333 | 1692.8333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 10 | C1 | 0.7568 [0.4207, 1.0000] | 612.8000 | 224.8000 [0.0000, 360.0000] | 2123.1000 | 2511.1000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2871.1000 | 2511.1000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2511.1000 | 2511.1000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 20 | C1 | 0.9641 [0.7633, 1.0000] | 90.4000 | 336.8000 [174.0000, 360.0000] | 2749.5333 | 2503.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2863.1333 | 2503.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2503.1333 | 2503.1333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 50 | C1 | 0.9952 [0.9607, 1.0000] | 12.0000 | 348.0000 [261.0000, 360.0000] | 2818.4333 | 2482.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2842.4333 | 2482.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2482.4333 | 2482.4333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2812.2333 | 2452.2333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2812.2333 | 2452.2333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2452.2333 | 2452.2333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2760.3667 | 2400.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2760.3667 | 2400.3667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2400.3667 | 2400.3667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2634.0667 | 2274.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2634.0667 | 2274.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2274.0667 | 2274.0667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2467.6000 | 2107.6000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 360.0000 [360.0000, 360.0000] | 2467.6000 | 2107.6000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2107.6000 | 2107.6000 | 30/30 = 1.0000 [0.8865, 1.0000] |


### US-121-1

US IRC section 121(a): ownership and use requirements of one taxpayer

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 12 | 4 | 0 | 8 | 4 | 3 |

Sizes exceeding |V| (draws stay with replacement): [10, 20, 50, 100, 200, 500, 1000].

**Controls** (`controls.csv` per example set; CTRL-DET pass, see above)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 12 | 12 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=0; workload=0 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 0 | 422 | 0 | C3 runs with valid_coverage = 1 and spurious = 0; |R| = 8 |

**OFFICIAL and FULL**

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 4 | 3 | -2 | 2 | 0 | 0.5000 | 2 | 0 | 0.0000 | 0 | 0 | 0 |
| OFFICIAL | C2 | 4 | 3 | 8 | 2 | 10 | 1.0000 | 0 | 8 | 0.8000 | 0 | 0 | 0 |
| OFFICIAL | C3 | 4 | 3 | 8 | 2 | 10 | 1.0000 | 0 | 8 | 0.8000 | 0 | 0 | 0 |
| FULL | C1 | 4 | 2 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C2 | 4 | 2 | 8 | 0 | 8 | 1.0000 | 0 | 8 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 4 | 2 | 8 | 0 | 8 | 1.0000 | 0 | 8 | 1.0000 | 0 | 0 | 0 |

**Hypothesis indicators emitted by the harness**

* H1: OFFICIAL unseen_values = 3 (> 0: True); C1 missed_valid = 2 (> 0: True); C1 reported_missing = -2, true_gap = 2.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 0 (0/422 C3 runs complete; |R| = 8).

**UNIFORM and ZIPF** (30 seeds per cell; valid_coverage with its 2.5 to 97.5 % range; spurious = rows of G in E ∪ R; workload = rows generated; COMPLETE share with Wilson 95% interval)

| source | n | cond | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | true_gap mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---|---|---|---|---|---|---|
| UNIFORM | 10 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.2667 | 0.2667 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.2667 | 0.2667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.2667 | 0.2667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0333 | 0.0333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0333 | 0.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0333 | 0.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| UNIFORM | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C1 | 0.9500 [0.5000, 1.0000] | 0.2000 | 0.0000 [0.0000, 0.0000] | 0.3333 | 0.5333 | 27/30 = 0.9000 [0.7438, 0.9654] |
| ZIPF | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.5333 | 0.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.5333 | 0.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0333 | 0.0333 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0333 | 0.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0333 | 0.0333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.0000 | 30/30 = 1.0000 [0.8865, 1.0000] |
| ZIPF | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 8.0000 [8.0000, 8.0000] | 8.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |


### US-121-2

US IRC section 121: amount of gain excluded on a single or joint return

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 1296 | 72 | 792 | 432 | 2 | 8 |

Sizes exceeding |V| (draws stay with replacement): [100, 200, 500, 1000].

**Controls** (`controls.csv` per example set; CTRL-DET pass, see above)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 1296 | 1296 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=72; workload=72 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 0 | 422 | 0 | C3 runs with valid_coverage = 1 and spurious = 0; |R| = 432 |

**OFFICIAL and FULL**

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 2 | 11 | 0 | 70 | 0 | 0.0278 | 70 | 0 | 0.0000 | 0 | 0 | 0 |
| OFFICIAL | C2 | 2 | 11 | 1294 | 70 | 1294 | 1.0000 | 0 | 1224 | 0.9459 | 0 | 0 | 0 |
| OFFICIAL | C3 | 2 | 11 | 502 | 70 | 502 | 1.0000 | 0 | 432 | 0.8606 | 0 | 0 | 0 |
| FULL | C1 | 72 | 4 | 72 | 0 | 72 | 1.0000 | 0 | 72 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 72 | 4 | 1224 | 0 | 1224 | 1.0000 | 0 | 1224 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 72 | 4 | 432 | 0 | 432 | 1.0000 | 0 | 432 | 1.0000 | 0 | 0 | 0 |

**Hypothesis indicators emitted by the harness**

* H1: OFFICIAL unseen_values = 11 (> 0: True); C1 missed_valid = 70 (> 0: True); C1 reported_missing = 0, true_gap = 70.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 0 (0/422 C3 runs complete; |R| = 432).

**UNIFORM and ZIPF** (30 seeds per cell; valid_coverage with its 2.5 to 97.5 % range; spurious = rows of G in E ∪ R; workload = rows generated; COMPLETE share with Wilson 95% interval)

| source | n | cond | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | true_gap mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---|---|---|---|---|---|---|
| UNIFORM | 10 | C1 | 0.9111 [0.6667, 1.0000] | 6.4000 | 56.0000 [26.1000, 72.0000] | 112.3000 | 62.7000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1286.7000 | 62.7000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 494.7000 | 62.7000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C1 | 0.9833 [0.8333, 1.0000] | 1.2000 | 68.4000 [36.0000, 72.0000] | 121.6000 | 54.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1278.4000 | 54.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 486.4000 | 54.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 107.4333 | 35.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1259.4333 | 35.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 467.4333 | 35.4333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 90.2000 | 18.2000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1242.2000 | 18.2000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 450.2000 | 18.2000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 76.5667 | 4.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1228.5667 | 4.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 436.5667 | 4.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 72.1333 | 0.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1224.1333 | 0.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 432.1333 | 0.1333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 72.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1224.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| UNIFORM | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 432.0000 | 0.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C1 | 0.8398 [0.5174, 1.0000] | 11.5333 | 51.0000 [22.3500, 72.0000] | 103.5333 | 64.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1288.0667 | 64.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 10 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 496.0667 | 64.0667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C1 | 0.9778 [0.7875, 1.0000] | 1.6000 | 68.8000 [36.0000, 72.0000] | 125.7333 | 58.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1282.5333 | 58.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 20 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 490.5333 | 58.5333 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 119.9000 | 47.9000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1271.9000 | 47.9000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 50 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 479.9000 | 47.9000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 107.5667 | 35.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1259.5667 | 35.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 100 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 467.5667 | 35.5667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 93.0000 | 21.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1245.0000 | 21.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 200 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 453.0000 | 21.0000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 77.4000 | 5.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1229.4000 | 5.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 500 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 437.4000 | 5.4000 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C1 | 1.0000 [1.0000, 1.0000] | 0.0000 | 72.0000 [72.0000, 72.0000] | 72.7667 | 0.7667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C2 | 1.0000 [1.0000, 1.0000] | 0.0000 | 1224.0000 [1224.0000, 1224.0000] | 1224.7667 | 0.7667 | 0/30 = 0.0000 [0.0000, 0.1135] |
| ZIPF | 1000 | C3 | 1.0000 [1.0000, 1.0000] | 0.0000 | 432.0000 [432.0000, 432.0000] | 432.7667 | 0.7667 | 0/30 = 0.0000 [0.0000, 0.1135] |

