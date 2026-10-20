# Replication report

Please fill in what applies and send it back with `replication/out/summary.json` and any
`replication/out/*_differences.txt` files. Short answers are fine.

## Who and when

* Name and affiliation:
* Date(s) of the run:
* May the paper name you as the replicator? (yes / no / only as "an independent researcher")
* Any relation to the author or to the original LATC work:

## Environment

* Repository commit (`git rev-parse HEAD`):
* Operating system and version:
* CPU and RAM:
* Python version (`python -VV`):
* Corpus fetched with `python -I fetch_corpus.py`? (yes / no; any source that failed):
* For the tool audit: Java version(s), Maven version, Node version, dmn-js clone commit:

## Core results (`python -I replication/run_all.py`)

| step | MATCH | DIFFERS | FAILED | SKIPPED | notes |
|---|---:|---:|---:|---:|---|
| report | | | | | |
| generator_profile | | | | | |
| datasets | | | | | |
| datasets_more | | | | | |
| trap_frequency | | | | | |
| corpus | | | | | |
| exposed_sample | | | | | |
| tool_inputs | | | | | |

* Test suite (`python -I -m unittest discover -s tests -t .`): tests run, failures, errors:
* Timing claims checked (see REPLICATION.md, "What is compared"): which hold on your machine,
  and which do not:

## Tool audit (`replication/tool_audit/`)

| tool and version | Java / Node | files run | same as the published run | differences |
|---|---|---:|---:|---|
| Drools 7.74.1 | | | | |
| Apache KIE 10.2.0 | | | | |
| dmn-js verifier (2016) | | | | |

* Nursery V1 (6,480 rules): finished? run time and peak memory:
* Do the found missing states agree with the manifest as the paper reports (V1 / V3b find all;
  V2 skips gap analysis; V4 and dmn-js miss the states with the removed value)?

## Discrepancies

For each difference: the file and value, what you expected, what you got, and whether you
think it changes a claim of the paper.

1.

## Time spent

* Setting up (downloads, builds):
* Running and waiting:
* Checking and writing this report:

## Anything else

Problems with the instructions, steps that were unclear, suggestions:
