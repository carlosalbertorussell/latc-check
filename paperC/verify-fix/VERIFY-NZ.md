# Independent verification of the NZ samples (NZ-SLP, NZ-AS, NZ-SPS)

Branch `paperc-verify-nz`, created from `origin/paperc-data-nz` at `7efbb1e`.
Protocol: `paperC/verify/PROTOCOL.md` and `paperC/verify/FORMAT.md`, copied verbatim from
`origin/paperc-harness` (PROTOCOL.md registered at `ee7c527`).

Independence: nothing under `paperC/harness/` was read, copied or imported on any branch;
`latc_check` was neither imported nor read; `paperC/openfisca_nz/oracle_core.py`, the
`oracle.py` files and `paperC/openfisca_nz/crosscheck.py` were not used; the runner's
`paperC/results/` was first opened at step 4, after steps 1 to 3 had produced their outputs.
All code is in `paperC/verify/` (Python 3.12 standard library for steps 1 and 4; OpenFisca in
a separate Python 3.11 virtualenv for steps 2 and 3).

## Verdicts

| Check | NZ-SLP | NZ-AS | NZ-SPS |
|---|---|---|---|
| 1. Recompute: CTRL-HASH, CTRL-GT | pass | pass | pass |
| 1. Recompute: CTRL-EXCL (disagreeing rows) | pass (0) | pass (0) | pass (0) |
| 1. Recompute: CTRL-PLANT (422 example sets) | pass | pass | pass |
| 1. Recompute: CTRL-H3 (422 C3 runs) | pass | pass | pass |
| 2. OpenFisca spot check, 50 rows (seed 20261020) | pass (50/50) | pass (50/50) | pass (50/50) |
| 2b. Supplementary: every row evaluated in OpenFisca | pass (224/224 valid) | pass (48,384/48,384 valid) | pass (99,840/99,840 valid) |
| 3. Audit: code citations and declared values | pass | pass | pass |
| 3. Audit: thresholds and parameters at the fixed period | pass | pass | pass |
| 3. Audit: legislation references | partial (see 3.3) | partial (see 3.3) | partial (see 3.3) |
| 4. Compare runs.csv with `origin/paperc-run-nz` | **pass**: 0 of 30,384 cells differ | pending | pending |

No disagreement was found between the verifier and the conversion or the runner in any
number. The findings below are observations on the protocol and the samples; none of
them is an error in the data.

## 1. Recompute (`recompute.py`)

`python3.12 paperC/verify/recompute.py paperC/specs/NZ-SLP paperC/specs/NZ-AS paperC/specs/NZ-SPS`
writes `paperC/verify/<ID>/runs.csv` (1,266 rows each: OFFICIAL and FULL × 3 conditions,
then UNIFORM and ZIPF × 7 sizes × 30 seeds × 3 conditions), `controls.csv`, `plant.csv`
(CTRL-PLANT per example set) and `summary.md`. Run time about 1 minute for all three.

| Sample | \|D\| | \|E\| | \|R\| | \|V\| | OFFICIAL rows | OFFICIAL unseen_values | OFFICIAL C1 missed_valid | C1 reported_missing vs true_gap | FULL C2 spurious_share |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| NZ-SLP | 256 | 32 | 0 | 224 | 13 | 0 | 0 | 243 vs 212 | 1.0 |
| NZ-AS | 86,016 | 37,632 | 0 | 48,384 | 1 | 20 | 48,383 | 0 vs 48,383 | 1.0 |
| NZ-SPS | 122,880 | 23,040 | 0 | 99,840 | 14 | 21 | 99,776 | 50 vs 99,833 | 1.0 |

The unseen-value counts agree with the lists in `paperC/specs/README-NZ.md` (NZ-AS 20,
NZ-SPS 21, NZ-SLP none).

### Readings chosen where PROTOCOL.md leaves room

1. **runs.csv layout.** PROTOCOL.md names the metric columns (section 6) and
   `size_exceeds_valid` (clarification 5) but not the identifying columns. I used
   `sample, source, size, seed, condition`, then the section 6 columns in table order, then
   `size_exceeds_valid`. The runner uses the same order with `sample_id` for the first
   column; this header name is the only difference between the two files.
2. **FULL size and seed.** Recorded like OFFICIAL: seed `-`, size = row count = |V|.
3. **size_exceeds_valid** is 1 only for UNIFORM and ZIPF cells with n > |V|; OFFICIAL and
   FULL get 0.
4. **C1 generated list.** Product of the observed label lists (first-appearance order) in
   odometer order, minus every product tuple that occurs among the example conditions; each
   tuple appears once. `reported_missing` for C1 is product of observed cardinalities minus
   the number of example rows counted with repetition, so it can be negative when draws
   repeat (NZ-SLP: -244 at n = 500).
5. **C3 missing count.** `T.valid_space_size()` is read as |S|, the number of declared
   tuples that satisfy no exclusion predicate.
6. **contradictory_pairs** counts index pairs over the example list with repetition;
   `value_coverage`, `min_value_coverage` and `unseen_values` use the distinct conditions X.
7. **CTRL-PLANT.** Label counts of A1 are taken over the example rows with repetition; ties
   go to the earlier declared label; C1 is run on the remaining rows for the "C1 count for v".
8. **Predicates.** Parsed with `ast` and limited to the node whitelist of clarification 1,
   then evaluated exactly as section 2 states. All five NZ predicates pass the whitelist.
9. **Statistics.** Median = `statistics.median`; percentiles Hyndman-Fan type 7 as written;
   Wilson bounds clamped to [0, 1] (clarification 2).
10. **CTRL-HASH.** Every file under the folder (recursively), except `SHA256SUMS`,
    `__pycache__` directories and `*.pyc`, must be listed with the right digest, and every
    listed file must exist.

## 2. Ground-truth spot check in OpenFisca (`spotcheck.py`)

Environment: OpenFisca Aotearoa cloned from GitHub at `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb`
(commit date 2025-05-06), installed editable with `--no-deps` into a fresh Python 3.11
virtualenv together with the pinned versions of `paperC/openfisca_nz/requirements.lock`
(OpenFisca-Core 41.5.7, numpy 1.24.4, pandas 2.3.3, ...). `setup_env.sh` was not used.

Simulation built from spec.json only: one simulation per row; the applicant is principal of
the family (and of a tenancy and an ownership); each attribute is set to its representative.
An input is stored in the periods the formulas read: the spec's week for WEEK variables,
each of the 7 days of the week for DAY variables (`age`), every month the week overlaps for
MONTH variables, `ETERNITY` for eternal ones. NZ-AS: a partner member (cash assets 0,
`accommodation_supplement__receiving` = the attribute) exists only when
`social_security__in_a_relationship` is True. NZ-SPS: one child member per age in the
`children` representative, each with `social_security__financially_independent` False;
no partner or parent member. The entry variable is calculated for the applicant at the
spec's week.

Draw: `random.Random(20261020).sample(range(len(rows)), 50)`, sorted; indices are 0-based
data-row indices (CSV line = index + 2) and are listed row by row in
`paperC/verify/<ID>/spotcheck.csv`, with the ground truth, the OpenFisca value, the
exclusions that hold and the verdict.

| Sample | Valid rows agreeing | EXCLUDED rows whose predicate holds | Disagreements |
|---|---|---|---|
| NZ-SLP | 42/42 (8 True, 34 False) | 8/8 (SLP-X1) | 0 |
| NZ-AS | 25/25 (all False) | 25/25 (AS-X1 15, AS-X2 5, both 5) | 0 |
| NZ-SPS | 43/43 (4 True, 39 False) | 7/7 (SPS-X2 5, both 2) | 0 |

Indices drawn:

* NZ-SLP: 8, 9, 12, 15, 16, 20, 23, 29, 37, 39, 40, 52, 54, 56, 63, 68, 70, 80, 81, 82, 104, 109, 113, 119, 123, 126, 130, 135, 142, 161, 166, 171, 175, 182, 186, 190, 191, 199, 201, 203, 204, 209, 216, 219, 234, 235, 238, 250, 253, 254
* NZ-AS: 4196, 5111, 6465, 6616, 8174, 8584, 10729, 11835, 11878, 12201, 14925, 19401, 20149, 20737, 22279, 26687, 26780, 27038, 27121, 27869, 28006, 28265, 29153, 32266, 35313, 36055, 40843, 41120, 41833, 42039, 42276, 53346, 55974, 58281, 60013, 60256, 61017, 61019, 63094, 64907, 66339, 66631, 69153, 72951, 74563, 76101, 76464, 82553, 85295, 85437
* NZ-SPS: 4196, 5111, 6616, 8174, 8584, 10729, 11835, 11878, 14925, 19401, 20149, 20737, 26687, 27038, 27869, 28006, 29153, 32266, 35313, 36055, 41120, 42276, 53346, 55974, 58281, 60256, 61019, 63094, 64907, 66631, 69153, 72951, 82553, 85295, 85437, 87908, 89875, 93572, 95388, 97324, 97668, 98282, 101481, 101997, 102169, 103232, 104303, 107221, 112632, 120325

Because the NZ-AS draw contained no True row (only 28 of 48,384 valid rows are True), I
also ran **every row** of the three tables through the same simulation builder
(`spotcheck.py --full`, `paperC/verify/<ID>/fullcheck.txt`). Every valid row agrees:

| Sample | GT True / OF True | GT False / OF False | EXCLUDED, OF False | EXCLUDED, OF True | Valid rows disagreeing |
|---|---:|---:|---:|---:|---:|
| NZ-SLP | 48 | 176 | 29 | 3 | 0 |
| NZ-AS | 28 | 48,356 | 37,620 | 12 | 0 |
| NZ-SPS | 6,867 | 92,973 | 21,024 | 2,016 | 0 |

This independently confirms the per-row NZ-SPS count of 6,867 True rows (README-NZ.md
defect 1) and that the operator-precedence behaviour (defect 2) is in the encoding as run.

**EXCLUDED rows against the exclusions' sources.** Every EXCLUDED row drawn satisfies a
declared predicate, and CTRL-EXCL (step 1) shows the converse over the whole table. The
encoding itself would return True on some excluded rows (last-but-one column above):

* NZ-SLP, 3 rows: carer path (s 40) with the self-inflicted flag set and neither restricted
  capacity nor blindness. SLP-X1 rests on the variable's label, which presupposes one of
  the two (`supported_living_payment.py:151`); the exclusion is consistent with that source.
* NZ-AS, 12 rows: AS-X1 rows (no relationship, partner receiving AS). Without a partner
  member the flag has no effect in the simulation, so these rows behave like their
  "partner not receiving" twins. AS-X1 matches its source (`relationships.py:20-24`).
* NZ-SPS, 2,016 rows: principal caregiver of children who are all 18 or over. These are
  True only through the precedence defect (`(dependent_child * age) < 14` is `0 < 14`).
  SPS-X1 removes them because its source (`relationship.py:32`, "Principal Caregiver in
  relation to a dependent child") presupposes a dependent child. **Observation:** the
  exclusion therefore hides part of defect 2 from the valid space; the 2,016 valid rows
  that README-NZ.md attributes to the defect are a separate set (one child 14-17 plus one
  18 or over).

## 3. Audit of the conversion

`citations.py` resolves every `file:line` citation in spec.json against the clone and prints
the cited lines; I read each against the claim. Parameter values were read from the YAML
files of the clone and checked to have a single value covering the fixed week.

### 3.1 Code citations and declared values

All 7 + 14 + 14 attribute citations, all 5 exclusion citations and the 3 entry-point ranges
point to the lines described (reads, input-variable declarations, labels, the reg 8(3)
quotation at `independent_circumstances.py:24-25`, the s 32(4) comment at
`sole_parent_support.py:289`). Variable entities, periods, value types and defaults agree
with the spec text (checked by loading each variable in the tax-benefit system).
The `accommodation_type` labels and their order equal `AccommodationType`
(`housing.py:8-15`). No disagreement.

### 3.2 Thresholds and parameters at the fixed period

| Sample | Item | Encoding | Spec | Agrees |
|---|---|---|---|---|
| NZ-SLP | age bands | literals 16 (`:56`), 18 (`:87`), 20 (`:90`), compared with `>=` | `<16, 16-17, 18-19, >=20` | yes |
| NZ-SLP | dependent children | `== 0` (`:87`) | `0, >=1` | yes |
| NZ-AS | cash assets | `assets.yaml` ssa2018_15_1_a = 16200, ssa2018_15_1_b = 8100 from 2018-11-26, single values; `<=` on an int | `<=8100, 8101-16200, >16200`, representatives 8100, 16200, 16201 (each band's boundary) | yes |
| NZ-AS | accommodation costs | `> 0` | `<=0, >0` | yes |
| NZ-AS | dependent children | `>= 1` | `0, >=1` | yes |
| NZ-SPS | child age 14 | `child_age_threshold.yml` 14 from 2018-11-26, `<` | bands `<14, 14-15, ...` | yes |
| NZ-SPS | child 16 / 18 | `child.py:18-19`, `<` | bands `14-15, 16-17, >=18` | yes |
| NZ-SPS | split care | `dependent_children >= 2` (`:260`) | one or two children | yes |
| NZ-SPS | applicant age | `age_threshold.yaml` 20 from 2018 (01-01), `>=` | `<20, >=20` | yes |

Every band boundary is a threshold of the encoding and every threshold of the formula path
falls on a band boundary.

### 3.3 Legislation references

`legislation.govt.nz` answers this container with an AWS WAF challenge (HTTP 202, empty
body) and NZLII with HTTP 403, so the Act's text could not be read directly here, as was
also the case for the conversion session. What could be checked through web search
summaries of NZLII, MSD and Community Law pages:

* s 29: sole parent support requires age 20 or over: agrees with NZ-SPS `age`.
* s 30 / s 33: sole parent support concerns a dependent child under 14: agrees.
* s 40(1)(c): carer at least 18 without a dependent child, at least 20 otherwise: agrees
  with NZ-SLP `age` and `social_security__dependent_children`.
* s 67: other funding exclusion: (a) spouse or partner receiving AS; (b) receiving a basic
  or independent circumstances grant (i), would be eligible if applying (ii), would be
  eligible but for income (iii): agrees with the NZ-AS attribute citations.
* Social Security Regulations 2018 reg 15: cash assets limit $8,100 single without child,
  $16,200 couple or sole parent (MSD Map): agrees with the parameters and NZ-AS bands.

Not checked against a primary text: s 16, s 34(c) (16 or over), s 36, s 32(2)-(4),
Schedule 2 definitions, Student Allowances Regulations 1998 reg 8(3) (checked only against
the encoding's own quotation). Two sources found note that s 67 was amended in 2022
(para (e)) and in 2025; the encoding omits para (e) (README-NZ.md defect 3) and the
amendments do not touch the paragraphs encoded, so no disagreement follows, but the
statement in spec.json that "every week from then on gives the same table" holds for the
encoding only, and should not be read as a statement about the law.

### 3.4 Disagreements and observations

No disagreement between spec.json and the encoding was found. Observations for the author:

1. **AS-X2 scope.** AS-X2 removes "eligible for an independent circumstances grant while
   receiving a basic grant" (reg 8(3)). On my reading the same regulation also rules out
   `independent_circumstances_grant__would_be_entitled` (eligible but for income) while
   receiving a basic grant; that combination is left in the valid space. This changes no output (any row with
   `basic_grant__receiving` True is False through s 67(b)(i)) but it does change |E| and
   |V|, and so the H2 and coverage figures of NZ-AS.
2. **SPS-X1 masks part of the encoding's precedence defect** (2,016 excluded rows are True in
   the encoding), see section 2.
3. **H2 under FULL is true by construction.** Under FULL the examples are exactly V, so C2
   generates exactly E ∪ R and its spurious_share is 1.0 for every sample with a non-empty
   E ∪ R (all three NZ samples). The H2 decision rule (C2 spurious_share ≥ 0.10 under FULL)
   therefore only tests whether a sample has any exclusion at all. The secondary measures
   (OFFICIAL: NZ-SLP 0.131, NZ-AS 0.438, NZ-SPS 0.188; UNIFORM n = 1000 median: NZ-SLP
   0.941, NZ-AS 0.443, NZ-SPS 0.189) are the informative ones.
4. **C1 reported_missing can be negative** with repeated draws (NZ-SLP n = 500 and 1000),
   since PROTOCOL.md defines it as product of cardinalities minus the number of example
   rows with repetition. Means and percentiles of this metric mix these values in.

## 4. Comparison with the runner (`compare.py`)

`python3.12 paperC/verify/compare.py origin/paperc-run-nz NZ-SLP NZ-AS NZ-SPS`, run at
`origin/paperc-run-nz` = `09c2392`. Output in `paperC/verify/<ID>/compare.txt`.

* **NZ-SLP: identical numbers.** 1,266 rows and 25 columns on both sides; the only
  difference is the first header name (`sample` here, `sample_id` in the runner).
  0 of 30,384 cells in common columns differ. CTRL-PLANT per example set (removed label,
  rows removed, C2 and C1 counts, pass): 0 of 422 differ. Summary statistics (10 metrics ×
  42 cells, plus completion share and Wilson bounds, at the runner's 4 decimals): 0 of 462
  rows differ.
* **NZ-AS, NZ-SPS: pending.** `origin/paperc-run-nz` holds no `paperC/results/NZ-AS/` or
  `paperC/results/NZ-SPS/` yet. Re-run the command above once they are pushed.

## Files

* `PROTOCOL.md`, `FORMAT.md`: verbatim copies from `origin/paperc-harness`.
* `recompute.py`: step 1. `spotcheck.py`: step 2 (and `--full`). `citations.py`: step 3
  helper. `compare.py`: step 4.
* `<ID>/runs.csv`, `controls.csv`, `plant.csv`, `summary.md`: step 1 outputs.
* `<ID>/spotcheck.csv`, `fullcheck.txt`: step 2 outputs. `<ID>/compare.txt`: step 4 output.

## Reproduce

```
python3.12 paperC/verify/recompute.py paperC/specs/NZ-SLP paperC/specs/NZ-AS paperC/specs/NZ-SPS
python3.11 -m venv V && V/bin/pip install -r <requirements.lock without the -e line>
git clone https://github.com/digitalaotearoa/openfisca-aotearoa C && git -C C checkout 9d77ea7ce3c4
V/bin/pip install --no-deps -e C
V/bin/python -W ignore paperC/verify/spotcheck.py paperC/specs/NZ-SLP paperC/specs/NZ-AS paperC/specs/NZ-SPS
V/bin/python -W ignore paperC/verify/spotcheck.py --full paperC/specs/NZ-SLP paperC/specs/NZ-AS paperC/specs/NZ-SPS
python3.12 paperC/verify/citations.py C paperC/specs/NZ-SLP paperC/specs/NZ-AS paperC/specs/NZ-SPS
python3.12 paperC/verify/compare.py origin/paperc-run-nz NZ-SLP NZ-AS NZ-SPS
```
