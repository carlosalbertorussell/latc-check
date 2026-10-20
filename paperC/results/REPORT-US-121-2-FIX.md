# US-121-2 correction: report (2026-10-20)

Branch `paperc-data-fr2-fix`, created from `origin/paperc-data-fr2` (commit `6566904`),
with `origin/paperc-harness` merged in (`git merge --no-edit`). Python 3.12.3. The
protocol (`paperC/PROTOCOL.md`, registered at `ee7c527`) and `paperC/harness/` are
identical to `origin/paperc-harness`. No table other than US-121-2 was changed
(`git diff origin/paperc-data-fr2 -- paperC/specs/FR-APL paperC/specs/US-121/US-121-1
paperC/catala_more` is empty).

Path note: the sample folder is `paperC/specs/US-121/US-121-2` (README-FR2.md,
deviation 1). The task gave `--spec paperC/specs/US-121-2`, which does not exist; the
harness was run on the real folder with `--out paperC/results/US-121-2` as given.

## 1. The correction

**Finding** (`paperC/verify/VERIFY-FR2.md` on `paperc-verify-fr2`, "Substantive
disagreement", item 1). The exclusion `person2_differs_on_single_return` covered
`single` and `surviving_spouse` rows on the ground that one taxpayer leaves the
person-2 labels describing no return. That ground holds for `single` rows. On
`surviving_spouse` rows the person-2 labels fill
`DeadSpouseInfo.death_spouse_info_at_time_of_death`: they describe the deceased spouse,
a real person whose ownership, use and earlier sales 26 U.S.C. 121(b)(4) (through the
(b)(2)(A) test "immediately before such date of death") and 121(d)(2) take into
account. `Section121TwoPersons` reads person 2 from `DeadSpouseInfo.return`
(`section_121.catala_en:101-105`); that is a property of the scope, and it makes no
such row legally impossible. 396 of the 792 EXCLUDED rows were affected.

**Change** (only `paperC/specs/US-121/US-121-2/`, plus the Correction section of
`paperC/specs/README-FR2.md`):

1. The exclusion predicate is now `return_type == 'single' and (…)`; its description
   and source cite `section_121.catala_en:65-66` and `95-105` (the old citation of
   §121(b)(1) was verifier item 10).
2. Every `surviving_spouse` row is evaluated through `oracle.py` with the generated
   Catala Python (`paperC/catala_more/generated/Us_tax_code.py`). The person-2 labels map
   onto the deceased spouse's `PersonalData`: ownership periods, use periods and earlier
   §121(a) sale, with the same representatives as for person 1. This is the mapping the
   encoding itself uses in `Section121TwoPasses` (`section_121.catala_en:406-425`:
   `person2: single_data.death_spouse_info_at_time_of_death`).
3. The fixed `date_of_spouse_death` moved from 2020-06-01 to 2020-12-31. The person-2
   periods end on 2021-01-01, the date of sale, and Catala counts `end - begin` days, so
   with a death on 2020-12-31 no representative gives the deceased spouse ownership or
   use after death. `Section121TwoPersons` does not read this date; every row outside
   the 396 has the same output as before.
4. Smaller fixes made with it: the person-2 ownership source cites lines 50-54
   (verifier item 11); the table title names surviving-spouse returns.

US-121-2 `CONVERSION.md` section 11 states the mapping attribute by attribute, quotes
§121(b)(4) and §121(d)(2), and explains why a representative that leaves person 2
unused was set aside (it would need a new label on three attributes and two new
design exclusions, and would again remove 396 legally possible rows from V).

**Counts**

| | \|D\| | valid | EXCLUDED | REJECTED | no_exclusion | entire_gain | limited_to_250000 | limited_to_500000 |
|---|---|---|---|---|---|---|---|---|
| before (`6566904`) | 1,296 | 72 | 792 | 432 | 45 | 12 | 12 | 3 |
| after | 1,296 | 204 | 396 | 696 | 144 | 23 | 34 | 3 |

The 396 rows moved to 264 REJECTED (person 1 has an earlier §121(a) sale: the
`DateError` of line 376), 99 `no_exclusion`, 11 `entire_gain` and 22
`limited_to_250000`. On every `surviving_spouse` row the output equals that of the same
row with person 2 set equal to person 1 (432 rows checked, 0 differences): the table now
records in V that this scope gives a surviving spouse the single-filer result whatever
the deceased spouse's facts.

## 2. Controls

| Check | Result |
|---|---|
| `oracle.py --check-official` | 6/6 official tests pass directly; 2/2 mapped rows (Test5 `single`, Test6 `joint`) agree |
| `oracle.py --enumerate` | counts above; `official_examples.csv` byte-identical to before |
| `oracle.py --check-bands` | 17,700 evaluations at non-representative values, all giving the representative's output |
| Rows outside the 396 | 900 of 900 keep their previous output |
| Catala interpreter (`paperC/results/US-121-2-interpreter/`) | all 900 non-excluded rows run with `clerk test`: 204 label rows pass, 696 REJECTED rows fail with the error of line 376, 0 disagreements; negative control reported |
| Harness CTRL-HASH, CTRL-GT, CTRL-EXCL | pass |
| Harness CTRL-PLANT | pass, 422/422 example sets |
| Harness CTRL-FULL | recorded without a pass criterion (missing_count 228, workload 228) |
| Harness CTRL-H3 | fail, 0/422 C3 runs complete (\|R\| = 696), as PROTOCOL.md 7(c) expects when there are REJECTED rows |
| Harness CTRL-DET | pass: two clean clones of commit `cfacf7f` gave byte-identical `runs.csv`, `controls.csv`, `summary.md`, `manifest.json` (`determinism.json`), with the same hashes as the committed outputs |
| Harness unit tests | 23/23 pass |
| `manifest.json` | harness commit `cfacf7f`, `tracked_inputs_unmodified` true |

## 3. Hypothesis indicators emitted by the harness

From `paperC/results/US-121-2/summary.md`, beside the run on the uncorrected data
(`origin/paperc-run-fr2`, commit `eb508e7`, `paperC/results/US-121-2/summary.md`):

| Indicator | before | after |
|---|---|---|
| H1: OFFICIAL unseen_values | 11 (> 0) | 11 (> 0) |
| H1: OFFICIAL C1 missed_valid | 70 (> 0) | 202 (> 0) |
| H1: OFFICIAL C1 reported_missing / true_gap | 0 / 70 | 0 / 202 |
| H2: FULL C2 spurious_share | 1.0000 (≥ 0.10) | 1.0000 (≥ 0.10) |
| H3: CTRL-H3 | fail, 0/422 (\|R\| = 432) | fail, 0/422 (\|R\| = 696) |
| H4 | not emitted (CTRL-NUR only, PROTOCOL.md section 8) | not emitted |

The direction of every indicator is unchanged. The size of the H2 measure changes:

| Run | before: spurious (excluded + rejected) | after: spurious (excluded + rejected) | spurious_share before → after |
|---|---|---|---|
| OFFICIAL C2 | 1,224 (792 + 432) | 1,092 (396 + 696) | 0.9459 → 0.8439 |
| OFFICIAL C3 | 432 (0 + 432) | 696 (0 + 696) | 0.8606 → 0.7751 |
| FULL C1 | 72 (72 + 0) | 228 (132 + 96) | 1.0 → 1.0 |
| FULL C2 | 1,224 (792 + 432) | 1,092 (396 + 696) | 1.0 → 1.0 |
| FULL C3 | 432 (0 + 432) | 696 (0 + 696) | 1.0 → 1.0 |
| UNIFORM n = 10, C2 (mean of 30 seeds) | 1,224 | 1,092 | 0.9513 → 0.8490 |
| ZIPF n = 10, C2 (mean of 30 seeds) | 1,224 | 1,092 | 0.9503 → 0.8481 |

In C2 the spurious rows no longer include the 396 surviving-spouse rows, which are now
in V; the REJECTED part grows by the 264 of them that raise the line-376 error. FULL C1
generates more rows than before (228 against 72) because V now holds `surviving_spouse`
rows with every person-2 value, so the odometer over observed values reaches more
declared rows; FULL `unseen_values` falls from 4 to 2 (only person 1's two earlier-sale
values never occur in V).

## 4. Comparison with the verifier's independent code

The verifier's `recompute.py`, `compare.py` and `spotcheck/spotcheck.py` were copied
unchanged from `origin/paperc-verify-fr2` (commit `4d4d51e`) to `paperC/verify-fix/`
(the original branch was not touched); `paperC/verify-fix/README.md` lists the commands.

* **Recompute** on the corrected folder: \|D\| 1,296, \|V\| 204, \|E\| 396, \|R\| 696;
  CTRL-HASH, CTRL-GT, CTRL-EXCL pass, CTRL-PLANT 422/422, CTRL-H3 fails (max
  spurious_rejected 696). A second run gave byte-identical files.
* **Spot-check of all 1,296 rows:** official-test validation PASS; 1,296 agree, 0
  disagree; 9,072 in-band probes, none differing. (The spot-check hard-codes the old
  date of death, 2020-06-01; the scope reads neither date.)
* **compare.py against the harness `runs.csv`:** 29,118 shared cells compared, **0
  differ**. `compare.py` prints the verdict DIFFERENT only because two columns are named
  differently (`sample`/`sample_id`, `n`/`size`); after renaming these two
  (`compare_renamed.py`), 31,650 cells (1,266 runs × 25 columns), **0 differ**, verdict
  IDENTICAL (`paperC/verify-fix/US-121-2/compare.txt`).

For reference, the same `compare.py` finds 0 differing cells between the verifier's
original recompute and the uncorrected runner output (`paperc-run-fr2`), and 13,410
differing cells out of 31,650 between that uncorrected output and the corrected one:
those are the effect of the correction.

## 5. For the paper

Report US-121-2 with the corrected counts (valid 204, EXCLUDED 396, REJECTED 696) and
state the change: one exclusion was restricted to single returns after the independent
verification showed that its legal ground did not cover surviving spouses; the 396
surviving-spouse rows are evaluated by the encoding, which ignores the deceased
spouse's facts. The H1, H2 and H3 indicators keep their direction; the H2 measure on
US-121-2 falls (OFFICIAL C2 spurious_share 0.946 → 0.844) and the REJECTED part of it
rises.

## 6. Reproduce

```
git checkout paperc-data-fr2-fix
cd paperC/specs/US-121/US-121-2
python3.12 oracle.py --check-official && python3.12 oracle.py --enumerate && python3.12 oracle.py --check-bands
cd ../../../..
python3.12 -m paperC.harness.run --spec paperC/specs/US-121/US-121-2 --out paperC/results/US-121-2
python3.12 -m paperC.harness.determinism --spec paperC/specs/US-121/US-121-2 --report paperC/results/US-121-2/determinism.json
python3.12 paperC/verify-fix/recompute.py paperC/specs/US-121/US-121-2 paperC/verify-fix/US-121-2
python3.12 paperC/verify-fix/spotcheck_us121_2_all.py
python3.12 paperC/verify-fix/compare_renamed.py paperC/verify-fix/US-121-2/runs.csv paperC/results/US-121-2/runs.csv
```

The interpreter check needs Catala 1.3.0 and a catala-examples checkout;
`paperC/results/US-121-2-interpreter/README.md` gives the commands.
