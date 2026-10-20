# Replicating the core results

This folder lets an outside researcher regenerate the core computational results of
*Completeness Needs Declared Domains: LATC, DMN Analysers and Public DMN Models* with one
command and check them against the committed result files. It covers:

| step | script | paper | what it regenerates | about |
|---|---|---|---|---|
| `report` | `run_report.py` | worked example; Sections 5.4, 8.1; Appendix D.1 | the worked example (Table 1a, the frequency table, the deficits, the published complement), the source errata it relies on (the Table 1 to Table 1a outcome changes), the two-attribute counterexample, the random-table runs (1,000 tables per scenario, seed 20210101), the structural and keying checks, the DMN baseline B4 | 9 min |
| `generator_profile` | `run_generator_profile.py` | Appendix D.1 | the profile of the random-table generator | < 1 min |
| `datasets` | `run_datasets.py` | Section 8.2, Appendix D.10 | UCI Car and Nursery, the baselines, the DMN TCK tables | 4 min |
| `datasets_more` | `run_datasets_more.py` | Section 8.2, Appendix D.10 | UCI Lenses, Balance Scale and the three MONK's problems; the five-dataset table | 1 min |
| `trap_frequency` | `run_trap_frequency.py` | Section 9.1 | the trap-frequency table and the Zipf simulations | 3 min |
| `corpus` | `run_dmn_corpus.py` | Section 9.3, Appendix C.7 | the survey of domain declarations in 50 public DMN sources | 5 min |
| `exposed_sample` | `run_dmn_exposed_sample.py` | Section 9.3, Appendix C.7 | the 50-table sample of exposed tables and the agreement of its two coders | < 1 min |
| `tool_inputs` | `run_tool_inputs.py` | Section 9.2, Appendix C.6 | the 39 shared DMN files of the analyser audit and their manifest | < 1 min |

Times are from the reference machine (Intel Core i7-1165G7, Windows 11, CPython 3.15.0); a full
run takes about 25 minutes. The module and output file behind each number are listed in the
paper's Appendix E and in the repository's README.

The DMN analyser audit itself (Drools, Apache KIE, the 2016 dmn-js verifier) needs Java and
Node and has its own instructions in [`tool_audit/README.md`](tool_audit/README.md). A blinded
human check of the 50-table sample is prepared in [`human_coding/`](human_coding/README.md).

## Requirements

* Python 3.10 or later, standard library only. The manifest was made and checked with
  **CPython 3.15.0** (64-bit, Windows 11). Other versions have not been checked; if a seeded
  result differs on another version, please report the version.
* For the `corpus` step (and the TCK part of `datasets`): the public DMN sources at their
  recorded commits, next to the repository. `python -I fetch_corpus.py` fetches them (git 2.25
  or later and network access; `--dry-run` prints the git commands). It fills
  `<parent>/corpus/`, `<parent>/dmn-tck/` and `<parent>/tools/`, where `<parent>` is the folder
  that holds the repository. Without them these steps are reported as `SKIPPED` and the others
  still run.

## Running

```bash
python -I fetch_corpus.py
```

```bash
python -I replication/run_all.py
```

Run both from the repository root. Useful options:

* `--only report datasets` runs some steps only (`--list` shows them);
* `--root DIR` points to the folder holding `corpus/`, `dmn-tck/` and `tools/` (default: the
  repository's parent folder);
* `--work DIR` keeps the regenerated files in `DIR` (by default they go to a temporary folder,
  which is removed at the end unless `--keep` is given).

The runner copies the code, the data and the committed results to the working folder, so
**nothing in the repository is changed**. In that copy each step deletes its own output files,
runs its script with the same interpreter in isolated mode (`python -I`), and hashes the files the
script wrote. The hashes are compared with [`expected_sha256.txt`](expected_sha256.txt), which
holds the hashes of the committed result files. Each file is reported as `MATCH`, `DIFFERS`,
`FAILED` (the script failed or did not write it) or `SKIPPED`. The exit status is 0 when nothing
differs or failed.

Logs go to `replication/out/` (ignored by git): one `<step>.log` per step with the script's
printed output, `summary.json` with every comparison, `report_stdout.txt` (the printed report in
comparable form), and a `<step>_differences.txt` listing, value by value or line by line, where
any file that `DIFFERS` departs from the committed one.

## What is compared, and what is not byte-reproducible

Every result is fully determined by the seeds except run times, memory figures and the
interpreter and platform names. Files that hold none of these are compared byte for byte; the
others are compared with those fields taken out. Each line of `expected_sha256.txt` gives the
mode:

| mode | files | what is hashed |
|---|---|---|
| `sha256` | the DMN files, `generator_profile.json`, `trap_frequency.csv`, `inputs.csv`, `exposed_sample.csv`, the 39 audit inputs and their `manifest.json` | the file's bytes, with CRLF line ends read as LF (git may convert line ends on checkout) |
| `json-stable` | `results.json`, `uci_car.json`, `uci_nursery.json`, `baselines.json`, `dmn_tck.json`, `datasets_more/results.json`, `trap_frequency/results.json`, `corpus/results.json`, `sources.json` | the JSON without every key whose name ends in `_s`, `_ms`, `_ns`, `_us`, `_mib`, `_kib`, `_gib` or `seconds`, or is `s`, `ms`, `python` or `platform`; re-serialised with sorted keys |
| `csv-stable` | `benchmark.csv`, `dmn_benchmark.csv`, `datasets/summary.csv` | the CSV without the columns named in the same way (build times, lookup times, traced peak memory) |
| `md-stable` | the `SUMMARY.md` files and `EXPOSED_SAMPLE.md` | the Markdown with table columns headed in a time unit (`time (ms)`, `ms`, `lookup median / p99 (µs)`, ...) and numbers followed by a time unit in running text replaced by `#`, and the Python version and platform masked |
| `stdout-stable` | the report `run_report.py` prints | the printed report without its two timing sections (RQ4.4 scaling benchmark, B4.5 analysis time), the version header and the lines naming output paths; compared with [`expected/report_stdout.txt`](expected/report_stdout.txt), which was made by the same command on the reference machine and agrees with the committed `results.json` |

Results that cannot be reproduced byte for byte, and how to check each:

* **Timings and memory** (`*_s`, `*_ms`, `*_ns`, `*_us`, `peak_mib`, the RQ4.4 and B4.5 tables,
  the `time (ms)` columns). They depend on the machine and its load; on the reference machine
  they varied by a factor of 2 to 5 between runs. Check the claims the paper makes from them,
  which are relative: in `results/dmn_benchmark.csv` (and B4.5 in `report.log`) COMPLETE is
  faster than the DMN sweep in all 25 configurations; in RQ4.4 the per-lookup cost of
  canonicalisation is larger than that of SHA-512 and of the verified probe; in
  `datasets/SUMMARY.md` DMN takes longer than COMPLETE on Car and Nursery; the traced peak
  memory of the largest benchmark table is about 114 MiB (`peak_mib`; it was the same in repeated
  runs on the reference machine and may change with the Python version).
* **The `large` section of `results/results.json`** (the large-scale test of the README, up to
  67 million rows) is not regenerated: it needs `--large`, takes many minutes and much memory,
  and is mostly timings. The runner leaves it out of the comparison. To check it, run
  `python -I run_report.py --large-only --out <copy of results>` and compare the row counts,
  prime-key bit lengths and lookup agreements with the README's tables; the times will differ.
* **`results_report.txt`** is the printed report of an earlier run with `--large`, kept for
  reference; later code changes added lines to it, so it is not compared. The runner compares
  the printed report with `expected/report_stdout.txt` instead.
* **Tie order in one table.** In `results/datasets/SUMMARY.md` the table of TCK skip reasons is
  sorted by count only (`latc_check/datasets_report.py`, line 650), so reasons with equal
  counts follow Python's per-process string hashing and can swap places between runs. The
  comparison sorts that table's rows; the counts themselves are compared exactly, and
  `dmn_tck.json` holds them by name.
* **Python and platform fields** (`meta.python`, `meta.platform`, the "Generated by" lines) name
  the machine that ran the script.

Not covered by the runner: `run_sensitivity.py` (about 1 minute; run it the same
way and compare `results/sensitivity/` by hand), `run_dmn_testinputs.py` (the DMN TCK test
inputs), `run_drools_domains.py` and the other analyser runs (see `tool_audit/`), and the
large-scale test.

## The test suite

```bash
python -I -m unittest discover -s tests -t .
```

The `-t .` matters under `-I`: isolated mode leaves the current folder off the import path, and
`-t .` puts the repository root back so that the tests can import `latc_check`.

## Reporting

Please fill in [`REPORT_TEMPLATE.md`](REPORT_TEMPLATE.md) and attach `replication/out/summary.json`
and any `*_differences.txt` files.

## For the maintainer

`python -I replication/run_all.py --write-manifest` rewrites `expected_sha256.txt` from the
committed result files (run `python -I run_tool_inputs.py` first, since the 39 audit inputs are
gitignored). `--save-stdout` copies the comparable printed report of a run to `expected/`.
