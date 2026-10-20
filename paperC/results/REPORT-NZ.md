# Paper C, Phase 2: runner report for the NZ samples

Samples: `NZ-SLP`, `NZ-AS`, `NZ-SPS` (legal samples in `paperC/specs/`), plus the supplementary
table `NZ-AS-1964` (`paperC/openfisca_nz/supplementary/NZ-AS-1964`), reported separately at the end.
Data from OpenFisca Aotearoa 22.0.0 (AGPL-3.0; see the licence note in `paperC/specs/README-NZ.md`).

Every number below is copied from the harness outputs (`summary.md`, `controls.csv`, `runs.csv`,
`manifest.json`, `determinism.json` in `paperC/results/<ID>/`). Where a figure is a tally of
`runs.csv` rows it says so. No metric was recomputed outside the harness.

## Setup

* Branch `paperc-run-nz`, created from `origin/paperc-data-nz` (7efbb1e) and merged with
  `origin/paperc-harness` (`git merge --no-edit`): no conflict. Merge commit
  `859b82615f676dbe949d8a502583fdce764c8070`, which is the `harness_commit` in every manifest
  below; `tracked_inputs_unmodified` is `true` in all four.
* Protocol `paperC/PROTOCOL.md` at registered commit `ee7c527`; Python 3.12.3 (CPython).
* No file under `paperC/PROTOCOL.md`, `paperC/harness/`, `paperC/specs/`, `paperC/openfisca_nz/`
  or `latc_check/` was modified.
* Harness unit tests: `python3.12 -m unittest discover -s paperC/harness/tests -t .`: 23 tests, OK.
* Repository tests: see Deviation 1. With the repository's documented invocation
  (`python3.12 -I -m unittest discover -s tests -t .`) 157 tests, OK.

Commands, run from the repository root:

```
python3.12 -m paperC.harness.run --spec paperC/specs/<ID> --out paperC/results/<ID>
python3.12 -m paperC.harness.run --spec paperC/openfisca_nz/supplementary/NZ-AS-1964 --out paperC/results/supplementary/NZ-AS-1964
python3.12 -m paperC.harness.determinism --spec <spec folder> --report paperC/results/<...>/determinism.json
```

### Wall time

Measured with `date` around each command on a 4-vCPU container. The four `run` commands were
started together and ran concurrently, and the two large CTRL-DET runs also ran concurrently, so
the times include contention.

| sample | `run` wall time | `determinism` wall time (two clean clones, sequential) |
|---|---:|---:|
| NZ-SLP | 1.3 s | under 10 s (not timed separately) |
| NZ-AS | 281.7 s | 547 s |
| NZ-SPS | 434.5 s | 851 s |
| NZ-AS-1964 (suppl.) | 1.8 s | under 10 s (not timed separately) |

Each run produced 1,266 runs (`runs.csv` has 1,266 data rows): OFFICIAL 3, FULL 3, UNIFORM and ZIPF 2 × 7 × 30 × 3.

## Summary across the three legal samples

| | NZ-SLP | NZ-AS | NZ-SPS |
|---|---:|---:|---:|
| \|D\| | 256 | 86,016 | 122,880 |
| \|V\| | 224 | 48,384 | 99,840 |
| \|E\| | 32 | 37,632 | 23,040 |
| \|R\| | 0 | 0 | 0 |
| attributes | 7 | 14 | 14 |
| OFFICIAL rows (distinct) | 13 (12) | 1 (1) | 14 (7) |
| CTRL-HASH, CTRL-GT | pass | pass | pass |
| CTRL-EXCL (disagreeing rows) | pass (0) | pass (0) | pass (0) |
| CTRL-PLANT | 422/422 | 422/422 | 422/422 |
| CTRL-H3 | 422/422 | 422/422 | 422/422 |
| CTRL-DET | pass | pass | pass |
| **H1** OFFICIAL `unseen_values` > 0 | 0 (False) | 20 (True) | 21 (True) |
| **H1** OFFICIAL C1 `missed_valid` > 0 | 0 (False) | 48,383 (True) | 99,776 (True) |
| H1 context: C1 `reported_missing` vs `true_gap` | 243 vs 212 | 0 vs 48,383 | 50 vs 99,833 |
| **H2** FULL C2 `spurious_share` ≥ 0.10 | 1.0000 (True) | 1.0000 (True) | 1.0000 (True) |
| H2 secondary: OFFICIAL C1 / C2 `spurious_share` | 0.1311 / 0.1311 | 0.0000 / 0.4375 | 0.0000 / 0.1875 |
| H2 secondary: UNIFORM n = 1000 median `spurious_share`, C1 / C2 | 0.9412 / 0.9412 | 0.4426 / 0.4426 | 0.1890 / 0.1890 |
| **H3** CTRL-H3 pass | 1 | 1 | 1 |

CTRL-FULL has a pass criterion only for CTRL-NUR; here it is recorded as `missing_count` =
workload = \|E\| on every sample (32; 37,632; 23,040). H4 applies to CTRL-NUR only and is not
emitted for these samples.

The decision rules of PROTOCOL.md section 8 are evaluated over all legal samples of all data
branches, so this report gives the per-sample indicators and leaves the decisions to the paper.
Within the NZ samples alone: both H1 indicators are True for 2 of 3 samples; the H2 indicator is
True for 3 of 3; H3 holds for 3 of 3 (none has REJECTED rows).

## What the numbers show

* **C3 is complete in every run of every sample** (OFFICIAL, FULL and all 420 random cells:
  CTRL-H3 422/422; COMPLETE 30/30 in every C3 cell, Wilson 95% interval 0.8865 to 1.0000).
* **C1 and C2 are never complete on these tables.** In every UNIFORM and ZIPF cell of every NZ sample, C1 and
  C2 have COMPLETE 0/30 (Wilson 0.0000 to 0.1135); under OFFICIAL and FULL, `complete` = 0 for C1
  and C2 on all three samples. Once the examples show every declared value, C1 generates exactly
  the C2 set, which contains all of E, so `spurious` equals \|E\| (32; 37,632; 23,040). Before that
  point C1 misses valid rows. The per-sample tables show where that crossover falls.
* **OFFICIAL examples barely touch the larger tables.** NZ-AS has one official row: C1 reports
  `missing_count` 0 and generates nothing, while 48,383 valid rows are absent (`valid_coverage`
  0.0000). NZ-SPS has 14 official rows, 7 distinct: C1 generates 57 rows and covers a valid share of
  0.0006 (99,776 valid rows missed). NZ-SLP's 13 official rows use every declared value, so C1 and
  C2 coincide there (`valid_coverage` 1.0, 32 spurious rows, all of E).

* **LATC's own missing count is unreliable as a gap estimate.** `missing_count(T)` is
  `product_of_cards(T) - len(T.rows)`, and `len(T.rows)` counts duplicate example rows. It
  therefore differs from the C1 workload whenever examples repeat (NZ-SLP OFFICIAL: reported 243,
  workload 244; NZ-SPS OFFICIAL: reported 50, workload 57), and it turns negative once the draw
  size exceeds the observed product: on NZ-SLP the C1 `reported_missing` is −244 in all 30 seeds
  at n = 500 and −744 at n = 1000, for both UNIFORM and ZIPF, while the true C1 workload is
  positive (mean 54.1 and 34.3 under UNIFORM). Tallied from `runs.csv`: 120 of 420 random C1 runs
  on NZ-SLP have `reported_missing` < 0 (60 of 420 on NZ-AS-1964; 0 on NZ-AS and NZ-SPS, whose
  declared spaces exceed 1,000).
* **The gap closes with sample size on the larger tables too, while spurious rows grow.** On
  NZ-SPS, mean C1 `valid_coverage` under UNIFORM rises from 0.5036 (n = 10) to 1.0000 (n = 1000),
  and the mean `spurious` count rises from 2,423.5 to 23,040 over the same range. ZIPF is slower:
  at n = 1000 C1 still misses 51.2 valid rows on average (`valid_coverage` 0.9995, 95% range
  0.9949 to 1.0000).
* **ZIPF C1 and C2 differ at n = 1000 on NZ-SPS** (mean `spurious_share` 0.1831 vs 0.1885),
  because some ZIPF seeds still leave declared values unseen there; on the other samples C1 and
  C2 are identical from n = 50 on.
* Tallied from `runs.csv`: C1 has `missed_valid` > 0 in 17 of 420 random runs on NZ-SLP, 71 of 420
  on NZ-AS and 294 of 420 on NZ-SPS.

### NZ-AS class imbalance (28 valid True rows of 48,384)

The protocol's coverage metrics (`valid_coverage`, `missed_valid`, `spurious`, `workload`,
`complete`, `unseen_values`, `reported_missing`, `true_gap`) are defined on condition tuples
only, and LATC's completion step does not read the output labels. The two output-dependent
metrics, `examples_disagree_gt` and `contradictory_pairs`, are 0 in every NZ-AS run, as they must
be when every example is labelled by the ground truth. So the imbalance leaves no trace in any
metric the harness emits: NZ-AS reaches C1 `valid_coverage` 1.0000 in every seed from n = 50 on,
exactly as a balanced table with the same attribute structure would. What the imbalance affects
is the content of the example sets: with 28 True rows among 48,384, a uniform draw of up to 1,000
rows will usually hold few or no True rows (an expectation from those two counts, which the
harness does not report), and the single OFFICIAL row is False. The protocol has no metric for
the share of each output among the examples or for how well the examples identify the
eligibility rule, so the imbalance cannot be quantified from the pre-registered outputs. A
verifier or a later deviation could add an output-share column; this run leaves the protocol as
registered.

## Per-sample results

Columns for UNIFORM and ZIPF are over seeds 0..29: `valid_coverage` mean with its 2.5th and
97.5th percentiles (type 7), mean `missed_valid`, mean `spurious` with its percentiles, mean
labelling workload (`workload` = len(G_list)), and the COMPLETE share with its Wilson 95% interval.

### NZ-SLP

Title: Supported Living Payment: eligibility (Social Security Act 2018 ss 34-40), OpenFisca Aotearoa encoding, week 2019-W01

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 256 | 224 | 32 | 0 | 13 | 7 |

Sizes exceeding |V| (draws stay with replacement): [500, 1000].

#### Controls (from `summary.md`)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 256 | 256 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=32; workload=32 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 422 | 422 | 1 | C3 runs with valid_coverage = 1 and spurious = 0; \|R\| = 0 |
| CTRL-DET | - | identical = true at commit 859b826 | | 1 | two clean clones, byte-identical runs.csv, controls.csv, summary.md, manifest.json |

#### OFFICIAL and FULL

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 13 | 0 | 243 | 212 | 244 | 1.0000 | 0 | 32 | 0.1311 | 0 | 0 | 0 |
| OFFICIAL | C2 | 13 | 0 | 243 | 212 | 244 | 1.0000 | 0 | 32 | 0.1311 | 0 | 0 | 0 |
| OFFICIAL | C3 | 13 | 0 | 211 | 212 | 212 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C1 | 224 | 0 | 32 | 0 | 32 | 1.0000 | 0 | 32 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 224 | 0 | 32 | 0 | 32 | 1.0000 | 0 | 32 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 224 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |

#### Hypothesis indicators emitted by the harness

* H1: OFFICIAL unseen_values = 0 (> 0: False); C1 missed_valid = 0 (> 0: False); C1 reported_missing = 243, true_gap = 212.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 1 (422/422 C3 runs complete; |R| = 0).

#### UNIFORM and ZIPF

| cond | source | n | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---:|---|---:|---|---:|---|
| C1 | UNIFORM | 10 | 0.9524 [0.5518, 1.0000] | 10.6667 | 29.8667 [11.6000, 32.0000] | 233.5000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 246.3000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 214.3000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 236.8667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 236.8667 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 204.8667 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 210.6667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 210.6667 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 178.6667 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 174.6000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 174.6000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 142.6000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 121.9000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 121.9000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 89.9000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 54.1333 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 54.1333 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 22.1333 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 34.2667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 34.2667 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 2.2667 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 10 | 0.8506 [0.4656, 1.0000] | 33.4667 | 26.0000 [0.0000, 32.0000] | 208.3333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 247.8000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 215.8000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 20 | 0.9917 [0.9313, 1.0000] | 1.8667 | 31.7333 [29.8000, 32.0000] | 239.2000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 241.3333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 209.3333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 225.7333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 225.7333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 193.7333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 205.1333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 205.1333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 173.1333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 174.3000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 174.3000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 142.3000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 124.4667 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 124.4667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 92.4667 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 79.7000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 32.0000 [32.0000, 32.0000] | 79.7000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 47.7000 | 30/30 (0.8865–1.0000) |

### NZ-AS

Title: Accommodation Supplement: eligibility (Social Security Act 2018 ss 65-67, Social Security Regulations 2018 reg 15), OpenFisca Aotearoa encoding, week 2022-W01

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 86016 | 48384 | 37632 | 0 | 1 | 14 |

#### Controls (from `summary.md`)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 86016 | 86016 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=37632; workload=37632 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 422 | 422 | 1 | C3 runs with valid_coverage = 1 and spurious = 0; \|R\| = 0 |
| CTRL-DET | - | identical = true at commit 859b826 | | 1 | two clean clones, byte-identical runs.csv, controls.csv, summary.md, manifest.json |

#### OFFICIAL and FULL

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 1 | 20 | 0 | 48383 | 0 | 0.0000 | 48383 | 0 | 0.0000 | 0 | 0 | 0 |
| OFFICIAL | C2 | 1 | 20 | 86015 | 48383 | 86015 | 1.0000 | 0 | 37632 | 0.4375 | 0 | 0 | 0 |
| OFFICIAL | C3 | 1 | 20 | 48383 | 48383 | 48383 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C1 | 48384 | 0 | 37632 | 0 | 37632 | 1.0000 | 0 | 37632 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 48384 | 0 | 37632 | 0 | 37632 | 1.0000 | 0 | 37632 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 48384 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |

#### Hypothesis indicators emitted by the harness

* H1: OFFICIAL unseen_values = 20 (> 0: True); C1 missed_valid = 48383 (> 0: True); C1 reported_missing = 0, true_gap = 48383.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 1 (422/422 C3 runs complete; |R| = 0).

#### UNIFORM and ZIPF

| cond | source | n | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---:|---|---:|---|---:|---|
| C1 | UNIFORM | 10 | 0.7405 [0.3744, 1.0000] | 12556.8000 | 26705.0667 [8793.6000, 37632.0000] | 62522.2667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 86006.0000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48374.0000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 20 | 0.9429 [0.7786, 1.0000] | 2764.8000 | 35072.0000 [25920.0000, 37632.0000] | 80671.2000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85996.0000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48364.0000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85966.0667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85966.0667 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48334.0667 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85916.1667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85916.1667 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48284.1667 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85816.5000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85816.5000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48184.5000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85518.8333 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85518.8333 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 47886.8333 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85027.5333 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85027.5333 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 47395.5333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 10 | 0.7429 [0.4500, 1.0000] | 12441.6000 | 26931.2000 [7257.6000, 37632.0000] | 62863.9667 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 86006.3667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48374.3667 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 20 | 0.9476 [0.8179, 1.0000] | 2534.4000 | 35660.8000 [30777.6000, 37632.0000] | 81492.1333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85997.7333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48365.7333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85973.9667 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85973.9667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48341.9667 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85937.2000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85937.2000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48305.2000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85870.7000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85870.7000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48238.7000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85690.8000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85690.8000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 48058.8000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85426.5667 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 37632.0000 [37632.0000, 37632.0000] | 85426.5667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 47794.5667 | 30/30 (0.8865–1.0000) |

### NZ-SPS

Title: Sole Parent Support: eligibility (Social Security Act 2018 ss 29-32), OpenFisca Aotearoa encoding, week 2019-W05

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 122880 | 99840 | 23040 | 0 | 14 | 14 |

#### Controls (from `summary.md`)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 122880 | 122880 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=23040; workload=23040 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 422 | 422 | 1 | C3 runs with valid_coverage = 1 and spurious = 0; \|R\| = 0 |
| CTRL-DET | - | identical = true at commit 859b826 | | 1 | two clean clones, byte-identical runs.csv, controls.csv, summary.md, manifest.json |

#### OFFICIAL and FULL

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 14 | 21 | 50 | 99833 | 57 | 0.0006 | 99776 | 0 | 0.0000 | 0 | 0 | 0 |
| OFFICIAL | C2 | 14 | 21 | 122866 | 99833 | 122873 | 1.0000 | 0 | 23040 | 0.1875 | 0 | 0 | 0 |
| OFFICIAL | C3 | 14 | 21 | 99826 | 99833 | 99833 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C1 | 99840 | 0 | 23040 | 0 | 23040 | 1.0000 | 0 | 23040 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 99840 | 0 | 23040 | 0 | 23040 | 1.0000 | 0 | 23040 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 99840 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |

#### Hypothesis indicators emitted by the harness

* H1: OFFICIAL unseen_values = 21 (> 0: True); C1 missed_valid = 99776 (> 0: True); C1 reported_missing = 50, true_gap = 99833.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 1 (422/422 C3 runs complete; |R| = 0).

#### UNIFORM and ZIPF

| cond | source | n | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---:|---|---:|---|---:|---|
| C1 | UNIFORM | 10 | 0.5036 [0.3108, 0.6564] | 49561.6000 | 2423.4667 [0.0000, 7680.0000] | 52691.8667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122870.0000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99830.0000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 20 | 0.7964 [0.6601, 0.9897] | 20326.4000 | 4864.0000 [0.0000, 15360.0000] | 84357.6000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122860.0000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99820.0000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 50 | 0.9865 [0.9635, 0.9949] | 1348.2667 | 6912.0000 [0.0000, 15360.0000] | 105353.7667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122830.0333 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99790.0333 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 100 | 0.9916 [0.9846, 1.0000] | 836.2667 | 10496.0000 [0.0000, 23040.0000] | 109399.8333 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122780.1000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99740.1000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 200 | 0.9968 [0.9897, 1.0000] | 324.2667 | 18176.0000 [7680.0000, 23040.0000] | 117492.0000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122680.2667 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99640.2667 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 500 | 0.9988 [0.9949, 1.0000] | 119.4667 | 21248.0000 [15360.0000, 23040.0000] | 120469.9333 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122381.4000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99341.4000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 121885.9000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 121885.9000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 98845.9000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 10 | 0.5783 [0.4140, 0.7610] | 42103.4667 | 1792.0000 [0.0000, 7680.0000] | 59518.9000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122870.3667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99830.3667 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 20 | 0.7757 [0.6376, 0.9288] | 22391.4667 | 2560.0000 [0.0000, 9792.0000] | 79990.0333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122861.5000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99821.5000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 50 | 0.9554 [0.8205, 1.0000] | 4454.4000 | 5376.0000 [0.0000, 23040.0000] | 100718.1667 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122836.5667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99796.5667 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 100 | 0.9908 [0.9846, 1.0000] | 921.6000 | 9216.0000 [0.0000, 23040.0000] | 108053.9333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122799.5333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99759.5333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 200 | 0.9942 [0.9846, 1.0000] | 580.2667 | 14336.0000 [0.0000, 23040.0000] | 113446.8333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122731.1000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99691.1000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 500 | 0.9979 [0.9935, 1.0000] | 204.8000 | 19968.0000 [13248.0000, 23040.0000] | 119265.9667 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122542.7667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99502.7667 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 1000 | 0.9995 [0.9949, 1.0000] | 51.2000 | 22272.0000 [15360.0000, 23040.0000] | 121441.2333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 23040.0000 [23040.0000, 23040.0000] | 122260.4333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 99220.4333 | 30/30 (0.8865–1.0000) |

## Deviations and notes

1. **Repository test command.** The task's command `python3.12 -I -m unittest discover tests`
   fails with 14 import errors (`ModuleNotFoundError: No module named 'latc_check'`): `-I` removes
   the current directory from `sys.path`, and without `-t .` discovery puts only `tests/` on the
   path. This is an invocation issue. The repository README's form,
   `python3.12 -I -m unittest discover -s tests -t .`, runs 157 tests, OK (and so does the same
   command without `-I`).
2. **Supplementary output folder.** NZ-AS-1964 results are in
   `paperC/results/supplementary/NZ-AS-1964/` so that no tool that globs `paperC/results/*`
   counts it as a sample. The harness accepted the folder without complaint (all controls pass).
   `determinism.py` always writes to `paperC/results/<ID>` inside its clones, and the manifest
   records output paths, so the clone manifests hash differently from the committed
   `supplementary/` manifest; `runs.csv`, `controls.csv` and `summary.md` match the clones byte for
   byte. To confirm the manifest difference is only the path, the harness was run once more locally
   with `--out paperC/results/NZ-AS-1964`: all four files then matched the clone hashes in
   `determinism.json`, and that temporary folder was deleted. The committed manifest differs from it
   only in the output path strings.
3. **Interim push.** An interim commit with the NZ-SLP and NZ-AS-1964 results was pushed while
   the large samples ran. It was built without moving local HEAD, so every `run` and `determinism`
   call in this report ran at HEAD = `859b826`, the commit named in all manifests.
4. `determinism.json` sits next to the four outputs, as on CTRL-NUR.

Nothing in the pre-registered design was changed.

## Supplementary: NZ-AS-1964

Not a sample (README-NZ deviation 3); not counted in the indicators above. SSA 1964 formula of
Accommodation Supplement, week 2018-W01. CTRL-DET: pass (see Deviation 2).

Title: Accommodation Supplement: eligibility under the Social Security Act 1964 formula (s 61EA), OpenFisca Aotearoa encoding, week 2018-W01 (supplementary table)

| \|D\| | \|V\| | \|E\| | \|R\| | official rows | attributes |
|---|---|---|---|---|---|
| 512 | 384 | 128 | 0 | 6 | 9 |

Sizes exceeding |V| (draws stay with replacement): [500, 1000].

#### Controls (from `summary.md`)

| control | source | observed | expected | pass | detail |
|---|---|---|---|---|---|
| CTRL-HASH | - | verified | verified | 1 | every file listed in SHA256SUMS and matching |
| CTRL-GT | - | 512 | 512 | 1 | ground_truth.csv header, odometer order and outputs; official labels declared |
| CTRL-EXCL | - | 0 | 0 | 1 | rows where (output = EXCLUDED) differs from (an exclusion predicate holds) |
| CTRL-FULL | FULL | missing_count=128; workload=128 | - | - | recorded without a pass criterion (only CTRL-NUR has one) |
| CTRL-PLANT | ALL | 422 | 422 | 1 | example sets where C2 regenerated every declared row with the removed value |
| CTRL-H3 | ALL | 422 | 422 | 1 | C3 runs with valid_coverage = 1 and spurious = 0; \|R\| = 0 |
| CTRL-DET | - | identical = true at commit 859b826 | | 1 | two clean clones byte-identical to each other; committed manifest differs from them only in output paths (Deviation 2) |

#### OFFICIAL and FULL

| source | condition | n_examples | unseen_values | reported_missing | true_gap | workload | valid_coverage | missed_valid | spurious | spurious_share | contradictory_pairs | examples_disagree_gt | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFFICIAL | C1 | 6 | 3 | 58 | 378 | 58 | 0.1250 | 336 | 16 | 0.2759 | 0 | 0 | 0 |
| OFFICIAL | C2 | 6 | 3 | 506 | 378 | 506 | 1.0000 | 0 | 128 | 0.2530 | 0 | 0 | 0 |
| OFFICIAL | C3 | 6 | 3 | 378 | 378 | 378 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |
| FULL | C1 | 384 | 0 | 128 | 0 | 128 | 1.0000 | 0 | 128 | 1.0000 | 0 | 0 | 0 |
| FULL | C2 | 384 | 0 | 128 | 0 | 128 | 1.0000 | 0 | 128 | 1.0000 | 0 | 0 | 0 |
| FULL | C3 | 384 | 0 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0.0000 | 0 | 0 | 1 |

#### Hypothesis indicators emitted by the harness

* H1: OFFICIAL unseen_values = 3 (> 0: True); C1 missed_valid = 336 (> 0: True); C1 reported_missing = 58, true_gap = 378.
* H2: FULL C2 spurious_share = 1.0000 (>= 0.10: True).
* H3: CTRL-H3 pass = 1 (422/422 C3 runs complete; |R| = 0).

#### UNIFORM and ZIPF

| cond | source | n | valid_coverage mean [p2.5, p97.5] | missed_valid mean | spurious mean [p2.5, p97.5] | workload mean | COMPLETE k/30 (Wilson 95%) |
|---|---|---:|---|---:|---|---:|---|
| C1 | UNIFORM | 10 | 0.9889 [0.9083, 1.0000] | 4.2667 | 123.7333 [92.8000, 128.0000] | 493.6667 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 502.2000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 374.2000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 492.5000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 492.5000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 364.5000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 464.9000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 464.9000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 336.9000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 423.4333 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 423.4333 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 295.4333 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 353.7000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 353.7000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 225.7000 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 230.6333 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 230.6333 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 102.6333 | 30/30 (0.8865–1.0000) |
| C1 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 156.4000 | 0/30 (0.0000–0.1135) |
| C2 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 156.4000 | 0/30 (0.0000–0.1135) |
| C3 | UNIFORM | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 28.4000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 10 | 0.9556 [0.5000, 1.0000] | 17.0667 | 119.4667 [46.4000, 128.0000] | 477.8333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 503.4333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 10 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 375.4333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 496.1333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 496.1333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 20 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 368.1333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 478.0333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 478.0333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 50 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 350.0333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 455.1333 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 455.1333 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 100 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 327.1333 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 419.2000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 419.2000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 200 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 291.2000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 350.0000 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 350.0000 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 500 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 222.0000 | 30/30 (0.8865–1.0000) |
| C1 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 279.0667 | 0/30 (0.0000–0.1135) |
| C2 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 128.0000 [128.0000, 128.0000] | 279.0667 | 0/30 (0.0000–0.1135) |
| C3 | ZIPF | 1000 | 1.0000 [1.0000, 1.0000] | 0.0000 | 0.0000 [0.0000, 0.0000] | 151.0667 | 30/30 (0.8865–1.0000) |
