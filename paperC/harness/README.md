# Paper C harness

Protocol: `paperC/PROTOCOL.md`, registered at commit
`ee7c527080e665df70b906f0cbf091098e84ad5f` (the first commit of branch
`paperc-harness`). Sample format: `paperC/specs/FORMAT.md`.

The harness runs the pre-registered design on one sample folder: conditions C1, C2, C3
(PROTOCOL.md section 4) × sources OFFICIAL, FULL, UNIFORM, ZIPF (section 5) × sizes
10..1000 × seeds 0..29, with the metrics of section 6, the controls of section 7 and the
statistics of section 8. It uses Python 3.12, its standard library, and `latc_check`
(`latc.latc_odometer`, `latc.missing_count`, `reference.exact_complement`,
`model.DecisionTable`), which it does not modify.

## Use

From the repository root:

```
python3.12 -m paperC.harness.run --spec paperC/specs/<ID> --out paperC/results/<ID>
python3.12 -m paperC.harness.determinism --spec paperC/specs/<ID> --report paperC/results/<ID>/determinism.json
python3.12 -m unittest discover -s paperC/harness/tests -t .
```

`run` verifies `SHA256SUMS` and the ground truth (aborting with exit code 2 on failure)
and writes:

* `runs.csv`: one row per run, every metric of section 6 (floats in Python `repr`);
* `controls.csv`: CTRL-HASH, CTRL-GT, CTRL-EXCL, CTRL-FULL, one CTRL-PLANT row per
  example set plus its total, CTRL-H3;
* `summary.md`: sample sizes, controls, OFFICIAL and FULL runs, per-metric statistics
  over seeds, COMPLETE shares with Wilson 95% intervals, and this sample's hypothesis
  indicators;
* `manifest.json`: harness commit, whether the tracked inputs were unmodified,
  protocol commit, Python version, sha256 of every input (spec folder, PROTOCOL.md,
  harness sources, the `latc_check` modules used) and of the three outputs above.

`determinism` clones the current commit twice into temporary folders, runs `run` in
each and compares the four output files byte for byte (CTRL-DET). Commit before running it.

## Files

| file | role |
|---|---|
| `spec.py` | loads a sample folder; CTRL-HASH, CTRL-GT, CTRL-EXCL; the sets D, E, R, V, S |
| `experiment.py` | sources, conditions, metrics, planted defect |
| `stats.py` | type 7 percentiles, mean, Wilson interval |
| `run.py` | command line, outputs, manifest, summary and hypothesis indicators |
| `determinism.py` | CTRL-DET |
| `tests/test_harness.py` | 23 unit tests on 3 × 2 tables whose metrics are computed by hand in the comments, including one table with an exclusion and one with a REJECTED row |

## Status (2026-10-20)

* Unit tests: 23 of 23 pass (`python3.12 -m unittest discover -s paperC/harness/tests -t .`).
  The repository's existing test suite also still passes; nothing outside `paperC/` was changed.
* CTRL-NUR was run at harness commit `0269952afddb3d6e0458f1e035de733f8721be96` with
  Python 3.12.3; results are in `paperC/results/CTRL-NUR/`.

Every control passed on CTRL-NUR:

| control | result |
|---|---|
| CTRL-HASH | pass |
| CTRL-GT | pass (12,960 rows in odometer order) |
| CTRL-EXCL | pass (no exclusions, no EXCLUDED rows) |
| (a) CTRL-FULL | pass: C1 on all 12,960 rows reports `missing_count` 0 and generates 0 rows |
| (b) CTRL-PLANT | pass on 421 of 421 example sets (FULL plus 420 UNIFORM and ZIPF cells) |
| (c) CTRL-H3 | pass: 421 of 421 C3 runs reach valid coverage 1 with 0 spurious rows |
| (d) CTRL-DET | pass: two clean clones of commit `0269952` produced byte-identical `runs.csv`, `controls.csv`, `summary.md` and `manifest.json` (`determinism.json`); the committed outputs have the same hashes |

H4 indicators on CTRL-NUR (the decision itself belongs to the paper): all four hold.
C1 on random samples reports missing rows in 420 of 420 runs; the mean number of valid
rows C1 misses falls from 4,260 (UNIFORM, n = 10) and 3,515.4 (ZIPF, n = 10) to 0 from
n = 50 on. C1 completes the table in 5 of 30 UNIFORM seeds at n = 10 (Wilson 95%
interval 0.073 to 0.336) and in 28 of 30 at n = 20. The gap on Nursery closes quickly
because every declared value appears in a few dozen uniform draws, after which the
odometer over observed values equals the declared space.

OFFICIAL is skipped on CTRL-NUR because Nursery has no official test cases.

## Deviations

The implementation clarifications are recorded in the dated "Deviations" section of
`paperC/PROTOCOL.md` (predicate whitelist, Wilson clamping, `SHA256SUMS` line format,
the `tracked_inputs_unmodified` field, the `size_exceeds_valid` column and how CTRL-DET
is run). None changes a pre-registered number. The task asked for the results directory
to be committed; `determinism.json` sits next to the four outputs and is outside the
manifest, since it is produced after them.

Branch note: the work is on `paperc-harness` as the task specified.
