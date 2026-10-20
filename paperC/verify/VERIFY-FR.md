# VERIFY-FR: independent verification of samples FR-PF, FR-AF-1, FR-AF-2, FR-AF-3

Verifier branch `paperc-verify-fr`, created from `origin/paperc-data-fr` (commit `0aee62d`).
Protocol: `paperC/PROTOCOL.md` and `paperC/specs/FORMAT.md` from `origin/paperc-harness`,
copied here as `PROTOCOL.md` and `FORMAT.md` for reference.
Date: 2026-10-20. Python 3.12.3 (CPython), standard library only, plus the bundled
Catala 1.3.0 runtime for step 2.

Independence: no file under `paperC/harness/` (any branch) was read, copied or
imported; `latc_check` was neither read nor imported; `paperC/results/` on
`paperc-run-*` was first opened at step 4, after steps 1 and 2 had been run and their
outputs written. The spec folders' `oracle.py` and `frcatala.py` were not read or
run.

## Verdicts

| check | FR-PF | FR-AF-1 | FR-AF-2 | FR-AF-3 |
|---|---|---|---|---|
| 1. Recompute: controls CTRL-HASH, CTRL-GT, CTRL-EXCL, CTRL-PLANT | PASS | PASS | PASS | PASS |
| 1. Recompute: CTRL-H3 (a protocol outcome) | pass | **fail** (R non-empty: C3 generates REJECTED rows in all 422 runs) | pass | pass |
| 1. Recompute: fast path = literal set algebra (`selftest.py`) | PASS (1 266 runs) | PASS (123 runs) | PASS (123 runs) | PASS (123 runs) |
| 2. Ground-truth spot-check, 50 rows | PASS 50/50 | PASS 50/50 | PASS 50/50 | PASS 50/50 |
| 2. Supplementary (beyond the task) | PASS, all 3 240 rows | PASS 5 000/5 000 | PASS 5 000/5 000 | PASS 5 000/5 000 |
| 3. Conversion audit: values, thresholds, operators, exclusions, labels | PASS | PASS | PASS | PASS |
| 3. Conversion audit: citations (documentation only, no label affected) | 1 disagreement (item 1), 1 minor offset (4) | 2 disagreements (2, 3), 2 minor offsets (4 via A2, 5) | 1 disagreement (3), 2 minor offsets (4 via A2, 5) | 1 minor offset (4 via A2) |
| 4. Comparison with `origin/paperc-run-fr` runs.csv | **PASS: 0 of 31 650 cells differ** | **PASS: 0 of 31 650 cells differ** | **PASS: 0 of 31 650 cells differ** | **PASS: 0 of 31 650 cells differ** |

CTRL-H3 is one of the protocol's measured outcomes (H3), so its failure on FR-AF-1
is a result of the experiment that the verifier reproduces. It does not indicate a
defect in the data or in either implementation.

## 1. Recompute

Code: `recompute.py` (protocol implementation), `selftest.py` (cross-check).
Command: `python3.12 paperC/verify/recompute.py paperC/specs/<ID> paperC/verify/<ID>`.
Outputs per sample: `runs.csv` (1 266 runs = (OFFICIAL + FULL + 2 × 7 × 30) × 3
conditions), `controls.csv`, `plant.csv` (CTRL-PLANT per example set), `summary.md`.

Implementation summary. Each condition tuple is held as its odometer index in D
(its row number in `ground_truth.csv`). C1 enumerates the product of the observed
values (as index offsets) and removes the example conditions; C2 is D minus the
example conditions; C3 is S minus the example conditions, with S from the exclusion
predicates evaluated by `eval(predicate, {"__builtins__": {}}, row)` after an `ast`
whitelist check. The sources use exactly the prescribed calls: UNIFORM
`random.Random(seed).choices(V_list, k=n)`; ZIPF `rng.shuffle(perm)` followed by
`rng.choices(perm, weights=[1.0 / (k ** 1.0) ...], k=n)`. `selftest.py` recomputes
the set metrics with label tuples, `itertools.product` over the observed values in
first-appearance order and literal set algebra (`naive_metrics`) and compares: every
FR-PF run and 41 example sets × 3 conditions per AF sample (OFFICIAL, FULL and an
even spread of seeded cells), 0 differences. The outputs are byte-identical under
Python 3.12.3 and 3.13.16 and across two runs (checked on FR-PF).

| sample | \|D\| | \|V\| | \|E\| | \|R\| | \|S\| | OFFICIAL rows |
|---|---|---|---|---|---|---|
| FR-PF | 3 240 | 1 080 | 2 160 | 0 | 1 080 | 4 |
| FR-AF-1 | 184 320 | 138 240 | 0 | 46 080 | 184 320 | 3 |
| FR-AF-2 | 132 300 | 132 300 | 0 | 0 | 132 300 | 4 |
| FR-AF-3 | 175 616 | 175 616 | 0 | 0 | 175 616 | 1 |

Hypothesis indicators recomputed (decision rules of section 8 are evaluated over all
legal samples, so only the per-sample indicators are given):

| sample | H1 unseen_values > 0 | H1 C1 missed_valid > 0 | C1 reported_missing vs true_gap | H2 FULL C2 spurious_share | H3 (CTRL-H3) |
|---|---|---|---|---|---|
| FR-PF | 16 (yes) | 1 074 (yes) | 8 vs 1 076 | 1.0 | pass |
| FR-AF-1 | 32 (yes) | 138 224 (yes) | 13 vs 138 237 | 1.0 (all REJECTED) | fail, up to 46 080 spurious_rejected |
| FR-AF-2 | 20 (yes) | 131 148 (yes) | 1 148 vs 132 296 | 0.0 | pass |
| FR-AF-3 | 27 (yes) | 175 615 (yes) | 0 vs 175 615 | 0.0 | pass |

Observation for the paper: FR-AF-2 and FR-AF-3 declare no exclusions and have no
REJECTED rows, so E ∪ R is empty, spurious is 0 by construction in every condition,
and C1 = C2 = C3 apart from C1's restriction to observed values. H2 can only be
supported on these samples through exclusions, and the conversion declared none
(CONVERSION.md T4 of each). FR-AF-1's FULL C2 spurious_share of 1.0 consists only of
REJECTED rows (rows the encoding does not model, CONVERSION.md A4), which the
protocol counts as spurious.

### Readings chosen where PROTOCOL.md is ambiguous (each is a finding)

1. **runs.csv identifier columns.** Section 6 defines the metric columns, and
   clarification 5 adds `size_exceeds_valid`, but no section names the identifier
   columns or their order. The verifier wrote `sample, source, n, seed, condition`;
   the runner wrote `sample_id, source, size, seed, condition`. Every other column
   name and the column order coincide. The comparison maps `sample`→`sample_id`,
   `n`→`size`.
2. **FULL's seed and size.** Section 5 says how to record OFFICIAL (seed `-`, size =
   row count) and is silent for FULL. Reading chosen: seed `-`, size = |V|. The
   runner chose the same.
3. **controls.csv layout** is not defined. The verifier writes
   `control,result,detail` plus a separate `plant.csv`; the runner writes
   `control,source,size,seed,observed,expected,pass,detail` with one CTRL-PLANT row
   per example set and an `ALL` row. Content was compared field by field (step 4).
4. **"mean (arithmetic)"** leaves the floating-point procedure open
   (`sum(xs)/N`, `math.fsum(xs)/N` or `statistics.mean`, which can differ in the
   last bit). The verifier uses `statistics.mean`. The runner prints 4 decimals, so
   the difference cannot be observed; a byte-level comparison of summaries would
   need the procedure fixed.
5. **C1 `reported_missing` with repeated examples.** `product_of_cards(T) -
   len(T.rows)` counts duplicate example rows, so it can fall below the workload
   or become negative when n exceeds the observed product. Taken literally (as the
   runner did; the cells agree).
6. **CTRL-PLANT wording** "the declared label of the first attribute A1 with the
   smallest count" was read as: v = argmin over A1's declared labels of their row
   count in the example list (duplicates counted, count 0 allowed, ties by declared
   order). The runner's v agrees on all 422 example sets.
7. **`size_exceeds_valid` for OFFICIAL and FULL** is written 0 (the flag concerns the
   drawn sizes of section 5). The runner agrees.
8. **"every OFFICIAL row uses declared labels" (CTRL-GT)** was also applied to the
   output column (output in `output.values`).
9. **CTRL-H3 when R is non-empty**: recorded as fail for the sample with the maximum
   `spurious_rejected`, as section 7 (c) describes. The runner records the same
   outcome for FR-AF-1 (0 of 422 C3 runs complete).

## 2. Ground-truth spot-check through the Catala encoding

Code: `spotcheck.py` (own adapter; neither `oracle.py` nor `frcatala.py` is used).
Outputs: `spotcheck/spotcheck_<ID>.csv` (row by row: index, condition, ground truth,
verifier label, verdict, the encoding's intermediate values), `spotcheck/spotcheck_indices.txt`.
Draw: `random.Random(20261020).sample(range(|D|), 50)` per sample, 0-based data-row
indices (file line = index + 2), listed in `spotcheck_indices.txt`.

Adapter. Each label becomes the representative of spec.json (FR-PF `eq_plafond`
through `representative_by_residence`; FR-AF resources `plafond_I(n)`, `plafond_II(n)`
and the midpoint rounded down to the euro). The encoding is called directly:
`prestations_familiales(...).droit_ouvert(enfant)` for FR-PF and
`interface_allocations_familiales(...)` for FR-AF. The FR-AF labels are derived
from values read inside the encoding: a profiler hook captures the locals of the
generated `allocations_familiales` at return (`enfants_a_charge_droit_ouvert_prestation_familiale`,
`plafond_i_d521_3`, `plafond_i_i_d521_3`, `montant_verse_base`, `_majoration`,
`_forfaitaire`, both compléments). FR-AF-3 labels come from those components
directly, which bypasses the converter's arithmetic decomposition of the amount
(CONVERSION.md T5). The captured ceilings equal the statute formula
57 759 € + 5 775 € × n and 80 831 € + 5 775 € × n in every evaluated row.
EXCLUDED rows of FR-PF are checked against the exclusions' stated source: the
obligation_scolaire that the encoding's own interface derives from the
representative birth date (epilogue.catala_fr:121-131) must differ from the row's
label.

| sample | rows | agree | ground-truth labels in the draw |
|---|---|---|---|
| FR-PF | 50 | 50 | EXCLUDED 37 (all confirmed by the epilogue derivation), not_entitled 11, entitled 2 |
| FR-AF-1 | 50 | 50 | general_t2 15, REJECTED 10 (AssertionFailed raised), general_t1 10, general_t3 6, mayotte 5, outre_mer_1_enfant 3, zero 1 |
| FR-AF-2 | 50 | 50 | outre_mer_1_enfant 14, zero 12, general_t3 11, general_t1 5, mayotte 4, general_t2 4 |
| FR-AF-3 | 50 | 50 | zero 36, base_majoration 6, base 6, base_forfaitaire 2 |

Supplementary, beyond the prescribed 50 rows: all 3 240 FR-PF rows
(`spotcheck/full_FR-PF.txt`, 0 disagreements) and a second draw of 5 000 rows per AF
table with seed 20261021 (`spotcheck/extended_<ID>.txt`, 0 disagreements each;
FR-AF-3's draw contains 168 `base_majoration_forfaitaire` rows, the one label absent
from its 50-row draw).

## 3. Conversion audit

Detail: `AUDIT-FR.md` (one table per sample, every attribute, output, exclusion and
fixed input, with quoted Catala lines). The citations were checked against a clone of
CatalaLang/catala-examples at `2694b17ddd7c2246e207e8f077d586349ee5abea` and against
the generated Python; behaviours were confirmed by calling the generated Python
(`audit/probe.py`, `audit/feb29_mayotte_probe.py`). The audit was carried out by a
helper agent under the same independence rules; the verifier re-checked items 2, 3,
4, 5, E6, E7 and the 29 February ambiguity directly.

**Verdict: no disagreement changes a ground-truth label.** Every enum is complete
with no extras (ASCII renaming checked against the generated code); every threshold
(3, 11, 14, 16, 20 an; 365 jour; 55 % × SMIC × 169; SMIC 10,15 €, Mayotte 7,66 €;
ceilings 57 759 / 80 831 / 5 775 €; BMAF 414,4 €; majoration 16 %; forfaitaire
20,234 %) and every boundary operator in the interval predicates is the one the
Catala code uses; every band's birth_from/birth_to recomputes; X1-X3 equal the
epilogue derivation (epilogue.catala_fr:121-131).

Disagreements (documentation only):

1. FR-PF `fixed_inputs.date_courante.why` calls 2020-05-01 the date "of most AF
   tests"; 7 of the 14 household tests use it (Test1-6, Test9). CONVERSION.md C2
   states seven correctly.
2. FR-AF-1 `avait_enfant_avant_2012` source names "Décret n°2002-423 art. 7 and
   Annexe"; the article 7 code (decrets_divers.catala_fr:180-239) never reads the
   flag; only the Annexe does (decrets_divers.catala_fr:295-394, e.g. line 394).
3. FR-AF-1/2 output label `mayotte` cites decrets_divers.catala_fr:170-215; the
   rates in force on 2020-05-01 sit in the Annexe (7,17 % at line 397, 30,68 % at
   486, 14,30 % at 567).
4. Minor offset: Smic.catala_fr:80-110 ends two lines before the Mayotte value
   7,66 € (line 112); FR-PF `remuneration`, FR-PF fixed input, CONVERSION C2 and A2.
5. Minor offset: L755-12 cited as securite_sociale_L.catala_fr:436-466; the file has
   465 lines.

Encoding against statute (the tables reproduce the encoding, as the protocol asks;
these bear on what the ground truth means legally and belong in the paper's
threats-to-validity):

* E1. `(b + 20 an) - dc < 365 jour` pays the allocation forfaitaire in the year
  before the 20th birthday as well, while the child still counts for the base
  (probe: a16_19 → a19_20 child changes 368,81 € to 452,66 €). CONVERSION.md A11
  records only the "past 20, no time limit" half (E2).
* E3. The eldest child is chosen among all children and the majoration ignores the
  child's own entitlement: an older non-entitled child makes the eldest entitled
  child eligible (282,76 € against 132,61 €), and a child with personal housing aid
  still receives the majoration and forfaitaire and still counts, although the
  quoted L821-3 removes it from the enfants à charge. Not stated in A11.
* E4. The D755-5 single-child majorations reach only households with a non-entitled
  elder sibling; a genuinely single child never receives them.
* E5. L755-12 al. 2 disapplies "the last four paragraphs" of L521-1 (paragraphs
  3-6); the encoding also disapplies the forfaitaire (paragraph 2), and CONVERSION
  A3 presents this as statutory.
* E6. Mayotte: the encoding adds the first-child rate to the two-child rate where
  the Annexe gives household totals; two children at 2020-05-01 receive 156,85 € in
  the encoding (verifier probe reproduces 156,85 €) against 127,14 € by the Annexe.
* E7. The runtime rounds SMIC × 55 % to the cent before × 169: ceiling 943,02 €
  against the statutory 943,44 € (10,15 × 0,55 × 169 = 943,4425); Mayotte 711,49 €
  against 712,00 €. Children earning between the two values are labelled by the
  encoding's ceiling. CONVERSION C6 records the rounding; the statutory value is
  worth stating beside it.
* E8. L131-1 "dès l'âge de trois ans": the encoding keeps a child `Avant` on the third
  birthday (one-day edge, `>=`).

Ambiguity found by the audit (verified): in the FR-AF tables a child born on
29 February makes the encoding raise `DateError` (date + 3 an rounding under
`AbortOnRound`, epilogue.catala_fr:123); the verifier's probe reproduces it for
births 2016-02-29, 2008-02-29 and 2004-02-29. Bands a00_03, a03_11, a11_14, a16_19 and
a20_plus contain such dates, so for real households these bands are partly
unevaluable by the encoding. The labels are computed at representatives (none a
29 February), so the tables are internally consistent, but the band definitions
silently assume no 29 February birth. FR-PF's PrestationsFamiliales path adds 20 an
to the birth date and is exposed to the same rounding rule for 29 February births
in a16_20/a20_plus (not probed).

## 4. Comparison with the runner

`origin/paperc-run-fr` at commit `2034114` ("FR-AF-3 harness outputs (interim)") holds
`paperC/results/` for all four samples; all four were compared at that commit. Code:
`compare.py`; reports: `<ID>/compare.txt`.

| sample | runs.csv cells compared | differing | CTRL-PLANT sets compared | differing | summary.md statistics (4 decimals) | differing |
|---|---|---|---|---|---|---|
| FR-PF | 31 650 | **0** | 422 | 0 | 2 268 | 0 |
| FR-AF-1 | 31 650 | **0** | 422 | 0 | 2 268 | 0 |
| FR-AF-2 | 31 650 | **0** | 422 | 0 | 2 268 | 0 |
| FR-AF-3 | 31 650 | **0** | 422 | 0 | 2 268 | 0 |

* runs.csv: 1 266 rows × 25 columns per sample, compared as strings, after the
  two identifier columns were renamed (reading 1 above).
* CTRL-PLANT, per example set: v, expected count, C2 count, C1 count and pass.
* summary.md: every statistic the runner prints (mean, median, p2.5, p97.5 of the ten
  metrics; complete share and Wilson bounds) against the verifier's value formatted
  to 4 decimals.
* Controls agree: CTRL-HASH, CTRL-GT, CTRL-EXCL (0 rows each) and CTRL-PLANT (422/422)
  in all four; CTRL-H3 422/422 for FR-PF, FR-AF-2 and FR-AF-3, 0/422 for FR-AF-1 (|R| = 46 080)
  in both implementations; CTRL-FULL (recorded only) missing_count = workload = 2 160
  (FR-PF), 46 080 (FR-AF-1), 0 (FR-AF-2) in both.
* FR-AF-3 controls agree too: CTRL-HASH, CTRL-GT, CTRL-EXCL (0 rows), CTRL-PLANT
  (422/422), CTRL-H3 (422/422), CTRL-FULL missing_count = workload = 0.

## Files

| file | role |
|---|---|
| `PROTOCOL.md`, `FORMAT.md` | reference copies from `origin/paperc-harness` |
| `recompute.py`, `selftest.py` | step 1 |
| `<ID>/runs.csv`, `controls.csv`, `plant.csv`, `summary.md` | step 1 outputs |
| `spotcheck.py`, `spotcheck/` | step 2 |
| `AUDIT-FR.md`, `audit/` | step 3 detail and probes |
| `compare.py`, `<ID>/compare.txt` | step 4 |
