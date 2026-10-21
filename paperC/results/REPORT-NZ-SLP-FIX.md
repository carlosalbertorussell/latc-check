# NZ-SLP correction: report (2026-10-21)

Branch `paperc-data-nz-fix`, created from `origin/paperc-data-nz` (commit `7efbb1e`),
with `origin/paperc-harness` merged in (`git merge --no-edit`, merge commit `d399359`).
The protocol (`paperC/PROTOCOL.md`, registered at `ee7c527`) and `paperC/harness/` are
identical to `origin/paperc-harness`. Only `paperC/specs/NZ-SLP/` and the Correction
section of `paperC/specs/README-NZ.md` changed among the data; NZ-AS, NZ-SPS and
`paperC/openfisca_nz/` are untouched (`git diff origin/paperc-data-nz --
paperC/specs/NZ-AS paperC/specs/NZ-SPS paperC/openfisca_nz` is empty).

Environment for the oracle: OpenFisca Aotearoa 22.0.0 at commit
`9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb`, recreated with
`paperC/openfisca_nz/setup_env.sh`; the resulting `pip freeze` equals
`paperC/openfisca_nz/requirements.lock` line for line (Python 3.11.17, OpenFisca-Core
41.5.7, numpy 1.24.4). Harness and verifier: Python 3.12.3.

## 1. The finding

`origin/paperc-analysis:paperC/analysis/REPORT-M2-M6.md`, "Findings for the author"
item 1 and the NZ-SLP row of M6. Exclusion SLP-X1 (`spec.json`, first version) removed
the 32 rows where `supported_living_payment__disability_self_inflicted` is True and both
`supported_living_payment__restricted_work_capacity` and `totally_blind` are False.
CONVERSION.md item 5 justified it in two ways: the flag "presupposes restricted work
capacity or total blindness", and the output of those rows "would be False in any
case". Evaluated through the encoding, 29 of the rows are False and 3 are True through
the s 40 carer route (`supported_living_payment.py:79-106`). The second, blinded
conversion declared no exclusion and agreed with the first on all 224 shared valid rows.
The verifier's own full OpenFisca check on `paperc-verify-nz`
(`paperC/verify/NZ-SLP/fullcheck.txt`) had already recorded the same split
(EXCLUDED/False 29, EXCLUDED/True 3).

## 2. Legal reasoning

The rule applied: an exclusion must rest on a legal or definitional impossibility; a
statement about the output is no ground for one.

The provisions the encoding cites are SSA 2018 s 34 (requirements on the ground of
restricted work capacity or total blindness: (a) restricted work capacity or total
blindness, (b) the residential requirement, (c) age 16 or over), s 35 (meaning of
restricted work capacity), s 36 (no entitlement on that ground when the restricted
capacity or blindness was self-inflicted with a view to qualifying for a benefit) and
s 40 (the separate ground of caring for another person).

1. **Section 36 is a disqualification scoped to the s 34 ground.** It takes away
   entitlement on the ground of restricted work capacity or total blindness. Where
   s 34(a) fails, s 36 has nothing to act on. Inapplicability of a disqualification
   leaves the person's facts possible; it makes the s 36 question idle for that person.
2. **The facts s 36 refers to are historical.** They concern a past act of the person
   and its purpose. The encoding stores the flag that way:
   `supported_living_payment__disability_self_inflicted` has
   `definition_period = ETERNITY` (`supported_living_payment.py:147-152`), while
   `supported_living_payment__restricted_work_capacity` is a weekly input
   (`:109-116`), read at `period.first_week` (`:50`). A person whose capacity for work
   was once restricted by a self-inflicted act, and who in week 2019-W01 no longer
   meets s 35 (for example after a reassessment under s 37), has the flag True and both
   s 34(a) inputs False. The same holds for every combination of the other five
   attributes, so no part of the 32 rows is impossible: neither the totally-blind half
   nor the restricted-capacity half, at any age, residence, caring status or number of
   dependent children.
3. **The output claim is no ground, and it is also false for 3 rows.** Section 40 is a
   separate ground in the Act, and the encoding's carer branch reads neither the s 34
   inputs nor the self-inflicted flag. A carer who meets the residential requirement and
   the s 40(1)(c) age test is eligible whatever their s 36 history.

Decision: no part of SLP-X1 rests on a legal or definitional impossibility. The
exclusion was removed and all 32 rows are evaluated through the encoding.

Limit: the text of the Act could not be fetched from the build environment
(legislation.govt.nz and NZLII return HTTP 403, as recorded for the first conversion in
README-NZ.md deviation 6). The reasoning rests on the sections the encoding cites, its
variable labels, references and period declarations. The author may wish to confirm it
against ss 34-36 and 40 of the Act.

## 3. The correction

Changes (all in `paperC/specs/NZ-SLP/`, plus `paperC/specs/README-NZ.md`):

1. `spec.json`: `"exclusions": []`; `notes` records the removal.
2. `ground_truth.csv` regenerated with `oracle.py --enumerate`.
3. `CONVERSION.md`: item 5 rewritten ("No exclusion"), item 6 lists the former SLP-X1
   among the exclusions considered and rejected, new section "Correction (2026-10-21)".
4. `SHA256SUMS` rewritten (same file list and format as `make_docs.py`).
5. `README-NZ.md`: table row, deviation 6, new section "Correction (2026-10-21)".

`oracle.py`, `official_examples.csv` and `ENVIRONMENT.md` are byte-identical to before.

| NZ-SLP | \|D\| | valid | EXCLUDED | REJECTED | valid True | valid False |
|---|---:|---:|---:|---:|---:|---:|
| before (`7efbb1e`) | 256 | 224 | 32 | 0 | 48 | 176 |
| after | 256 | 256 | 0 | 0 | 51 | 205 |

The 32 former EXCLUDED rows are 29 False and 3 True. The 3 True rows (restricted work
capacity False, totally blind False, self-inflicted True, residential requirement True,
caring for another person True):

| age | dependent children | output |
|---|---|---|
| 18-19 | 0 | True |
| >=20 | 0 | True |
| >=20 | >=1 | True |

The other 224 rows keep their output; the attribute columns of all 256 rows are
unchanged.

## 4. Controls

| Check | Result |
|---|---|
| `oracle.py --enumerate` on the uncorrected spec (baseline) | reproduced the committed `ground_truth.csv` byte for byte; `SHA256SUMS` verified |
| `oracle.py --check-official --write --log` | 50 cases, 43 without an assertion of eligibility; 13/13 asserted person-values pass directly; 13 mapped, 13/13 pass through the oracle; 0 unmappable. Log identical to `paperC/openfisca_nz/logs/check_official_NZ-SLP.txt`; `official_examples.csv` byte-identical |
| `oracle.py --enumerate` (corrected) | counts above; a second run gave a byte-identical file (sha256 `26020ee8…93c7`) |
| `oracle.py --batch-diagnostic` | 256/256 rows agree |
| `paperC/openfisca_nz/crosscheck.py` (OpenFisca-free) | NZ-SLP 256/256; NZ-SPS, NZ-AS, NZ-AS-1964 unchanged and all rows agree |
| Harness CTRL-HASH, CTRL-GT, CTRL-EXCL | pass |
| Harness CTRL-FULL | recorded without a pass criterion: missing_count 0, workload 0 (before: 32 and 32) |
| Harness CTRL-PLANT | pass, 422/422 example sets |
| Harness CTRL-H3 | pass, 422/422 C3 runs complete (\|R\| = 0) |
| Harness CTRL-DET | pass: two clean clones of `d399359` gave byte-identical `runs.csv`, `controls.csv`, `summary.md`, `manifest.json` (`paperC/results/NZ-SLP/determinism.json`), with the same hashes as the committed outputs |
| Harness unit tests | 23/23 pass |
| `manifest.json` | harness commit `d399359`, `tracked_inputs_unmodified` true |

## 5. Hypothesis indicators emitted by the harness

From `paperC/results/NZ-SLP/summary.md`, beside the run on the uncorrected data
(`origin/paperc-run-nz`, harness commit `859b826`, `paperC/results/NZ-SLP/summary.md`):

| Indicator | before | after |
|---|---|---|
| H1: OFFICIAL unseen_values | 0 (> 0: False) | 0 (> 0: False) |
| H1: OFFICIAL C1 missed_valid | 0 (> 0: False) | 0 (> 0: False) |
| H1: OFFICIAL C1 reported_missing / true_gap | 243 / 212 | 243 / 244 |
| H2: FULL C2 spurious_share | 1.0000 (≥ 0.10: **True**) | 0.0000 (≥ 0.10: **False**) |
| H2 secondary: OFFICIAL spurious_share C1 / C2 | 0.1311 / 0.1311 | 0.0000 / 0.0000 |
| H2 secondary: UNIFORM n = 1000 median spurious_share C1 / C2 | 0.9412 / 0.9412 | 0.0000 / 0.0000 |
| H3: CTRL-H3 | pass, 422/422 (\|R\| = 0) | pass, 422/422 (\|R\| = 0) |
| H4 | not emitted (CTRL-NUR only, PROTOCOL.md section 8) | not emitted |

**H2 changes direction on this sample.** Before, every spurious row in NZ-SLP was one of
the 32 SLP-X1 rows. With no exclusion and no REJECTED row, the valid space equals the
declared space, so no generated row can be spurious in any condition. NZ-SLP now
counts against H2 in the PROTOCOL.md section 8 majority rule (more than half of legal
samples with FULL C2 spurious_share ≥ 0.10). The H1 and H3 indicators keep their
values. The paper-level decisions are for the author once every legal sample's
indicators are in.

### OFFICIAL figures (13 example rows, 12 distinct conditions)

| condition | reported_missing | true_gap | valid_coverage | spurious_share |
|---|---|---|---|---|
| C1 before | 243 | 212 | 1.0000 | 0.1311 |
| C1 after | 243 | 244 | 1.0000 | 0.0000 |
| C2 before | 243 | 212 | 1.0000 | 0.1311 |
| C2 after | 243 | 244 | 1.0000 | 0.0000 |
| C3 before | 211 | 212 | 1.0000 | 0.0000 |
| C3 after | 243 | 244 | 1.0000 | 0.0000 |

`true_gap` is \|V \ X\| (PROTOCOL.md section 6) and grows by the 32 rows now in V
(212 → 244). `reported_missing` is each condition's own missing count (section 4): C1 and
C2 report 243 before and after, and C3, which subtracted the 32 excluded rows before
(211), now reports the same 243 as the other two. C1 and C2 generated 32 spurious rows before (spurious_share 0.1311) and none
after; OFFICIAL C1 and C2 now complete the table (complete 0 → 1).

### Other effects on the seeded runs

| Measure | before | after |
|---|---|---|
| C1 COMPLETE share, UNIFORM n = 10 | 0/30 | 23/30 (Wilson 0.591 to 0.882) |
| C1 COMPLETE share, ZIPF n = 10 / n = 20 | 0/30 / 0/30 | 20/30 / 28/30 |
| C2 COMPLETE share, every size and source | 0/30 | 30/30 |
| C1 COMPLETE share, UNIFORM n ≥ 20 and ZIPF n ≥ 50 | 0/30 | 30/30 |
| C1 mean missed_valid, UNIFORM n = 10 | 10.67 | 14.93 |
| C1 mean missed_valid, ZIPF n = 10 / n = 20 | 33.47 / 1.87 | 23.47 / 4.27 |
| C1 mean valid_coverage, UNIFORM n = 10 / ZIPF n = 10 | 0.9524 / 0.8506 | 0.9417 / 0.9083 |
| C2, C3 missed_valid (all sizes) | 0 | 0 |

Before, C1 and C2 never completed the table: they always generated the 32 excluded
rows once the self-inflicted value had been seen. After, completeness depends only on
whether the examples reach every declared value. The changes in C1 missed_valid follow
from the larger V and from the new draws (the seeded samples are drawn from V, which
changed).

Cells of `runs.csv` that differ between the run on the uncorrected data and this run:
8,782 of 31,650 (every column that depends on V or on spurious rows; `size` and
`n_examples` differ only in the 3 FULL rows, 224 → 256).

## 6. Comparison with the verifier's independent code

`paperC/verify/` was copied from `origin/paperc-verify-nz` (commit `6fc8b7e`) into
`paperC/verify-fix/`; the scripts are byte-identical to that commit and only the
`NZ-SLP/` outputs were regenerated. `paperC/verify-fix/README.md` lists the commands.

* **Recompute** on the corrected folder: \|D\| 256, \|V\| 256, \|E\| 0, \|R\| 0;
  CTRL-HASH, CTRL-GT, CTRL-EXCL pass, CTRL-PLANT 422 sets with 0 failures, CTRL-H3 422
  runs with 0 failures. Its indicators match the harness: H1 0 / 0 (243 against 244),
  H2 FULL C2 spurious_share 0.0, H3 pass. A second run gave a byte-identical `runs.csv`.
* **OpenFisca spot check** (built from `spec.json` alone, without the conversion's
  oracle): the standard 50 drawn rows all agree; with `--full`, all 256 rows evaluated
  directly: 205 False/False, 51 True/True, **0 disagree**.
* **`compare.py` against the harness `runs.csv`**: 0 of 30,384 cells in common columns
  differ; CTRL-PLANT per example set 0 of 422 differ; 462 summary statistics rows, 0
  differ. The only column mismatch is the name `sample` (verifier) against `sample_id`
  (runner). With that one name mapped (`compare_renamed.py`): 31,650 cells (1,266 runs ×
  25 columns), **0 differing cells**, verdict IDENTICAL
  (`paperC/verify-fix/NZ-SLP/compare_renamed.txt`).

For reference, the same `compare_renamed.py` finds 0 differing cells between the
verifier's original recompute (`paperc-verify-nz`) and the uncorrected runner output
(`paperc-run-nz`).

## 7. Agreement with the second conversion

`paperC/verify-fix/m6_slp_fix.py` applies the attribute and label map of
`origin/paperc-analysis:paperC/analysis/m6_nz.py` (`slp_compare`: attributes paired by
position, age `>=20` → `20+`, dependent children `>=1` → `1+`) to the corrected
`ground_truth.csv` and `origin/paperc-code2-nz:paperC/specs2/NZ-SLP/ground_truth.csv`.

| First conversion | rows compared | agree | disagree |
|---|---:|---:|---:|
| before (`origin/paperc-data-nz`) | 256 | 224 | 32 (29 EXCLUDED/False, 3 EXCLUDED/True) |
| after | 256 | **256** | 0 |

The "before" line reproduces the analysis's M6 result. The two conversions now give the
same table: the same 256 rows, the same outputs, no exclusions on either side.

## 8. Left for the author

* `paperC/openfisca_nz/docs/NZ-SLP.md` (the body from which `make_docs.py` writes
  `CONVERSION.md`) and `paperC/openfisca_nz/logs/summary.txt` still carry the first
  version's item 5 and counts. They were left as they are, because the task limits
  changes in `paperC/openfisca_nz/` to the oracle build script, which needed none. A run
  of `rebuild_all.sh` would therefore rewrite `NZ-SLP/CONVERSION.md` without its
  Correction section; the table, `spec.json`-driven oracle outputs and official
  examples would rebuild unchanged. README-NZ.md says so in its Correction section.
* Confirm the reading of ss 34-36 and 40 against the Act's text (section 2, Limit).
* H2 on NZ-SLP now reads False (section 5); the majority decision over all samples is
  the paper's.

## 9. Reproduce

```
git checkout paperc-data-nz-fix
paperC/openfisca_nz/setup_env.sh /path/to/work
export OPENFISCA_AOTEAROA_DIR=/path/to/work/openfisca-aotearoa
cd paperC/specs/NZ-SLP
/path/to/work/venv311/bin/python oracle.py --check-official
/path/to/work/venv311/bin/python oracle.py --enumerate
python3 ../../openfisca_nz/crosscheck.py
cd ../../..
python3.12 -m paperC.harness.run --spec paperC/specs/NZ-SLP --out paperC/results/NZ-SLP
python3.12 -m paperC.harness.determinism --spec paperC/specs/NZ-SLP --report paperC/results/NZ-SLP/determinism.json
python3.12 paperC/verify-fix/recompute.py paperC/specs/NZ-SLP
/path/to/work/venv311/bin/python -W ignore paperC/verify-fix/spotcheck.py --full paperC/specs/NZ-SLP
python3.12 paperC/verify-fix/compare_renamed.py paperC/verify-fix/NZ-SLP/runs.csv paperC/results/NZ-SLP/runs.csv
python3.12 -I paperC/verify-fix/m6_slp_fix.py
```
