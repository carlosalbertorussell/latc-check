# Verifier cross-check of the corrected NZ-SLP (2026-10-21)

This folder is a copy of `paperC/verify/` from `origin/paperc-verify-nz` (commit `6fc8b7e`).
`recompute.py`, `spotcheck.py`, `compare.py`, `citations.py`, `PROTOCOL.md`, `FORMAT.md` and
`VERIFY-NZ.md` are byte-identical to that commit; `NZ-AS/` and `NZ-SPS/` are the verifier's
original outputs, untouched. The files in `NZ-SLP/` were regenerated on the corrected table
(`paperC/specs/NZ-SLP`, exclusion SLP-X1 removed); the originals remain on
`origin/paperc-verify-nz`. Two scripts were added:

* `compare_renamed.py`: cell-by-cell comparison of two `runs.csv` files after mapping the
  verifier's column `sample` onto the runner's `sample_id`, the one naming difference.
* `m6_slp_fix.py`: row-by-row comparison of the corrected ground truth with the second
  conversion (`origin/paperc-code2-nz`, `paperC/specs2/NZ-SLP`), with the attribute and
  label map of `origin/paperc-analysis:paperC/analysis/m6_nz.py` (`slp_compare`).

Commands (repository root; `V` is the Python 3.11 virtualenv of
`paperC/openfisca_nz/setup_env.sh`):

```
python3.12 paperC/verify-fix/recompute.py paperC/specs/NZ-SLP
V/bin/python -W ignore paperC/verify-fix/spotcheck.py paperC/specs/NZ-SLP
V/bin/python -W ignore paperC/verify-fix/spotcheck.py --full paperC/specs/NZ-SLP
python3.12 paperC/verify-fix/compare.py HEAD NZ-SLP
python3.12 paperC/verify-fix/compare_renamed.py paperC/verify-fix/NZ-SLP/runs.csv paperC/results/NZ-SLP/runs.csv
python3.12 -I paperC/verify-fix/m6_slp_fix.py
```

Results (in `NZ-SLP/`):

| Check | File | Result |
|---|---|---|
| recompute, controls | `controls.csv`, `summary.md` | CTRL-HASH, CTRL-GT, CTRL-EXCL, CTRL-PLANT (422 sets), CTRL-H3 (422 runs) pass; a second run gave a byte-identical `runs.csv` |
| OpenFisca spot check, 50 drawn rows | `spotcheck.csv` | 50 agree |
| OpenFisca check of every row | `fullcheck.txt` | 256 rows: 205 False/False, 51 True/True, 0 disagree |
| `compare.py` against the harness | `compare.txt` | 0 of 30,384 cells in common columns differ; CTRL-PLANT 0 of 422 differ; 462 summary statistics rows, 0 differ |
| `compare_renamed.py` | `compare_renamed.txt` | 31,650 cells (1,266 runs × 25 columns), 0 differ, IDENTICAL |
| second conversion | `m6_second_conversion.txt` | 256 of 256 rows agree |
