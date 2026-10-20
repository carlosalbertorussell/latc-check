# Verifier code applied to the corrected US-121-2

`recompute.py`, `compare.py`, `spotcheck/spotcheck.py`, `PROTOCOL.md`, `FORMAT.md` and
`READINGS.md` are byte-identical copies of `paperC/verify/` on branch
`paperc-verify-fr2` (commit `4d4d51e`); that branch was left untouched. The verifier's
earlier outputs (its per-sample folders and spot-check CSVs) were not copied. Two
drivers were added; neither changes the copied code:

* `spotcheck_us121_2_all.py` runs the spot-check's official-test validation and then
  `spotcheck.spot` on every row of `paperC/specs/US-121/US-121-2/ground_truth.csv`,
  in-band probes included.
* `compare_renamed.py` runs `compare.main` after renaming the verifier's columns
  `sample` and `n` to the harness names `sample_id` and `size`, so that these two
  columns are compared as well.

Commands (repository root, Python 3.12.3):

```
python3.12 paperC/verify-fix/recompute.py paperC/specs/US-121/US-121-2 paperC/verify-fix/US-121-2
python3.12 paperC/verify-fix/spotcheck_us121_2_all.py > paperC/verify-fix/US-121-2/spotcheck_all.log
python3.12 paperC/verify-fix/compare.py paperC/verify-fix/US-121-2/runs.csv paperC/results/US-121-2/runs.csv
python3.12 paperC/verify-fix/compare_renamed.py paperC/verify-fix/US-121-2/runs.csv paperC/results/US-121-2/runs.csv
```

Results (`US-121-2/`):

* recompute: CTRL-HASH, CTRL-GT, CTRL-EXCL pass; CTRL-PLANT 422/422; CTRL-H3 fails
  (0/422 C3 runs complete, max spurious_rejected 696), as PROTOCOL.md 7(c) expects with
  REJECTED rows. A second run into another folder gave byte-identical files.
* spot-check: official-test validation PASS; 1,296 of 1,296 rows agree with the ground
  truth; 9,072 in-band probes, no row with a difference (`spotcheck_all.csv`,
  `spotcheck_all.log`). The spot-check builds the surviving-spouse return with the
  date of death 2020-06-01 hard-coded (`spotcheck.py`, `us_return_type`), while the
  corrected spec fixes 2020-12-31; `Section121TwoPersons` reads neither, and the rows
  agree.
* compare (`compare.txt`): `compare.py` as copied reports 29,118 shared cells and 0
  differing, with the verdict DIFFERENT only because two columns have different names;
  after renaming, 31,650 cells (1,266 runs × 25 columns) and 0 differing, verdict
  IDENTICAL.
