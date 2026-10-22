# Corpus results: old and new figures

The corpus results in this folder were regenerated on Linux from a clean fetch
(`python -I fetch_corpus.py`, then `run_dmn_corpus.py --corpus ../corpus --tck ../dmn-tck`,
`run_dmn_exposed_sample.py` and `run_dmn_testinputs.py`, all under `python -I`). Every
source was fetched at the commit recorded in `sources.json`: 50 of 50 sources ready, none
failed. *Old* is the version committed at 7603ea2; *new* is the version in this folder.

## Why the figures changed

* **Line endings.** The original corpus was checked out on Windows with
  `core.autocrlf=true`. Git converted LF files to CRLF on checkout; repositories that force LF
  stayed LF (`apache/incubator-kie-drools` sets `* text eol=lf` and `apache/incubator-kie-tools`
  sets `* text=auto eol=lf` in `.gitattributes`), and the 14 files stored with CRLF stayed CRLF. The
  survey deduplicates files by the SHA-256 of their bytes, so two copies of one model in
  repositories with different settings got different hashes and were counted twice.
  Matching the old hashes against the fresh checkout confirms this: of the 3,766 old
  distinct files, 2,518 have the hash of a current file converted to CRLF, 1,246 have the
  hash of a current file as stored, and 2 match nothing (the two `node_modules` files below).
  Of the 1,246, 1,194 are kie-drools and kie-tools files; the other 52 are files stored with
  CRLF, files with no LF line break, the Corea file and 37 `CodeForPhilly/benefit-decision-toolkit`
  files, whose old checkout already held the stored LF bytes.
  The largest effect is `apache/incubator-kie-kogito-runtimes`: its 42 old distinct files
  (40 tables) are byte-identical copies of `apache/incubator-kie-drools` models once both
  keep their stored LF bytes, so the new run keeps none of them.
  `fetch_corpus.py` now runs every git command with `-c core.autocrlf=false -c core.eol=lf`
  and sets both in each clone's local config.
* **dmn-js verifier fixtures.** The local `../tools/dmn-js-verifier` held
  `_harness/node_modules/dmn-moddle/test/fixtures/dmn/{decision.part,example}.dmn`,
  2 files outside the repository (7 `.dmn` files found, 5 in the pinned checkout).
  `dmn_corpus.collect` now skips every path with a `node_modules` or `target` directory
  component; no fresh checkout holds such a path, so the rule changes no new figure.
* **Corea verifier.** The local Corea copy lacked the 4 `dmnverifierfrontend` models
  (`dmn/BaselineModel.dmn`, `dmn/emptyDMN.dmn`, `bpmn-verifier/BaselineModel.dmn`,
  `bpmn-verifier/diagram.dmn`). The pinned checkout has all 5 models; the old run kept 1
  distinct Corea file with 2 tables, the new run keeps 5 with 14 tables.

Per source, only five rows of the Sources table in `SUMMARY.md` change (distinct files
kept, tables): kie-kogito-runtimes 42, 40 → 0, 0; kie-drools 1,100, 594 → 1,098, 591;
Common.DMN.Engine 88, 104 → 89, 112; dmn-js verifier 7, 5 → 5, 4; Corea 1, 2 → 5, 14. The net
change is −41 files and −24 tables. The examples / tutorials and TCK figures are unchanged.

**Line-ending check of the fresh fetch.** 4,191 `.dmn` files are on disk; 14 contain a CR
byte, and all 14 are stored with CRLF in their repository (`git ls-files --eol`: `i/crlf` or
`i/mixed`). No file holds a CR byte that its repository does not store.

**Outside audit.** A Linux re-run at 7603ea2 by an outside auditor got 3,725 files, 2,882
tables, 2,088 string inputs, 1,548 tables with string inputs, 363 exposed (23.4%), 252
strict (16.3%) and 28 exposed tables with a default output. The new figures match all seven
exactly. Git on Linux leaves line endings as stored unless configured otherwise, and a fetch
of the pinned commits holds neither the `node_modules` fixtures nor an incomplete Corea copy,
so the auditor's run avoided all three causes above; no difference remains to explain. With
the new settings, a fetch on Windows gives the same bytes.

## Survey figures (distinct files)

| figure | old (7603ea2) | new | |
|---|---|---|---|
| distinct files | 3,766 | 3,725 | changed |
| files with decision tables | 1,738 | 1,716 | changed |
| decision tables | 2,906 | 2,882 | changed |
| rules | 13,353 | 13,303 | changed |
| inputs | 5,326 | 5,283 | changed |
| string inputs | 2,092 | 2,088 | changed |
| string inputs declaring a domain, % | 50.3% | 50.5% | changed |
| string inputs usable by Drools, % | 43.6% | 44.2% | changed |
| examples and tutorials: declaring a domain, % | 40.0% | 40.0% | same |
| examples and tutorials: usable by Drools, % | 33.8% | 33.8% | same |
| tables with string inputs | 1,559 | 1,548 | changed |
| tables with no string domain | 724 (46.4%) | 720 (46.5%) | changed |
| exposed tables | 369 (23.7%) | 363 (23.4%) | changed |
| exposed tables in examples | 34 of 112 (30.4%) | 34 of 112 (30.4%) | same |
| exposed, no `-` in the column | 338 (21.7%) | 332 (21.4%) | changed |
| strict exposed tables | 258 (16.5%) | 252 (16.3%) | changed |
| exposed tables with a default output | 31 | 28 | changed |
| distinct exposed contents | 190 of 675 (28.1%) | 190 of 676 (28.1%) | changed |
| distinct exposed contents with a default output | 23 | 23 | same |
| declared lists equal to the rule values | 724/1045 (69.3%) | 726/1046 (69.4%) | changed |
| lists with an unmatched declared value | 68/974 (7.0%) | 67/975 (6.9%) | changed |
| unmatched combinations (distinct) | 10/160 (6.2%) | 10/164 (6.1%) | changed |
| unmatched combinations, fixture paths excluded | 8/140 (5.7%) | 8/144 (5.6%) | changed |
| lists with an unused declared value | 308/1045 (29.5%) | 307/1046 (29.3%) | changed |
| single-hit tables: string inputs declaring a domain | 850/1718 (49.5%) | 849/1712 (49.6%) | changed |
| single-hit tables: string inputs usable by Drools | 718/1718 (41.8%) | 725/1712 (42.3%) | changed |
| Drools-usable string inputs with a typeRef | 898/2092 (42.9%) | 907/2088 (43.4%) | changed |
| sources contributing files / tables / string inputs | 44 / 43 / 40 | 43 / 42 / 39 | changed |

## Distinct table contents (`SUMMARY.md`)

| figure | old (7603ea2) | new | |
|---|---|---|---|
| distinct table contents | 1,288 | 1,297 | changed |
| files holding them | 896 | 898 | changed |
| string inputs | 943 | 947 | changed |
| declared share of string inputs | 378/943 (40.1%) | 382/947 (40.3%) | changed |
| usable by Drools | 327/943 (34.7%) | 331/947 (35.0%) | changed |
| tables with string inputs | 675 | 676 | changed |
| tables with no string domain | 386 (57.2%) | 386 (57.1%) | changed |
| exposed | 190 (28.1%) | 190 (28.1%) | same |
| strict exposed | 114 (16.9%) | 114 (16.9%) | same |
| declared lists equal to the rule values | 213/371 (57.4%) | 217/375 (57.9%) | changed |
| lists with an unmatched declared value | 41/315 (13.0%) | 41/319 (12.9%) | changed |
| lists with an unused declared value | 152/371 (41.0%) | 152/375 (40.5%) | changed |

## Appendix C.7: by kind of model (distinct files)

*Declared %* = string inputs with any declaration; *Usable by Drools %* as in `SUMMARY.md`;
*every string input declared* = tables with every string input declared, as k of n tables
with a string input; *no entry can match* = string inputs with a declared value no entry
can match, k of the inputs whose unmatched set is known.

| kind | run | files | tables | string inputs | Declared % | Usable by Drools % | Tables with every string input declared (share of tables with a string input) | Declared value no entry can match |
|---|---|---|---|---|---|---|---|---|
| all | old | 3766 | 2906 | 2092 | 50.3 | 43.6 | 777 of 1559 (49.8%) | 68 of 974 |
| all | new | 3725 | 2882 | 2088 | 50.5 | 44.2 | 770 of 1548 (49.7%) | 67 of 975 |
| examples / tutorials | old | 171 | 190 | 145 | 40.0 | 33.8 | 48 of 112 (42.9%) | 5 of 53 |
| examples / tutorials | new | 171 | 190 | 145 | 40.0 | 33.8 | 48 of 112 (42.9%) | 5 of 53 |
| product test resources | old | 2197 | 2009 | 1490 | 45.4 | 39.3 | 486 of 1105 (44.0%) | 43 of 610 |
| product test resources | new | 2158 | 1977 | 1478 | 45.5 | 39.9 | 479 of 1092 (43.9%) | 42 of 605 |
| conformance (TCK) | old | 1022 | 471 | 304 | 77.3 | 67.4 | 185 of 232 (79.7%) | 14 of 234 |
| conformance (TCK) | new | 1022 | 471 | 304 | 77.3 | 67.4 | 185 of 232 (79.7%) | 14 of 234 |
| analyser fixtures | old | 329 | 184 | 102 | 55.9 | 50.0 | 39 of 74 (52.7%) | 4 of 51 |
| analyser fixtures | new | 329 | 194 | 111 | 57.7 | 52.3 | 40 of 77 (51.9%) | 4 of 58 |
| product, non-test | old | 47 | 52 | 51 | 51.0 | 43.1 | 19 of 36 (52.8%) | 2 of 26 |
| product, non-test | new | 45 | 50 | 50 | 50.0 | 42.0 | 18 of 35 (51.4%) | 2 of 25 |

## Exposed sample (`EXPOSED_SAMPLE.md`)

| figure | old (7603ea2) | new | |
|---|---|---|---|
| exposed tables over distinct files | 369 | 363 | changed |
| sampling frame (distinct exposed contents) | 190 | 190 | same |
| frame by kind (tck / example / product-test / analyser / other) | 1 / 26 / 151 / 9 / 3 | 1 / 26 / 151 / 9 / 3 | same |
| sample drawn (seed 20210101, n = 50) | 50 contents | the same 50 contents | same |
| `copies` of 8a58c338a00bb359 (kie-drools `Using Imported.dmn`, PARTIAL) | 3 | 2 | changed |
| `copies` of bd91f8e0f9f02d8f (kogito-examples `vacationDays.dmn`, OPEN) | 7 | 4 | changed |
| copies over the sample | 79 | 75 | changed |
| first coder: OPEN / CLOSED / PARTIAL / UNCLEAR | 1 / 2 / 46 / 1 | 1 / 2 / 46 / 1 | same |
| OPEN share (Wilson 95%) | 2% (0% to 10%) | 2% (0% to 10%) | same |
| OPEN over 190 distinct exposed tables | about 4 (1 to 20) | about 4 (1 to 20) | same |
| OPEN over the exposed tables of distinct files, same share | about 7 of 369 (1 to 39) | about 7 of 363 (1 to 38) | changed |
| copy-weighted OPEN estimate | 7 of 79 copies, 9%, about 33 of 369 tables | 4 of 75 copies, 5%, about 19 of 363 tables | changed |
| second judgement (domain): OPEN / CLOSED / COVERED / SYNTHETIC / UNCLEAR | 7 / 10 / 5 / 24 / 4 | 7 / 10 / 5 / 24 / 4 | same |
| second judgement OPEN (Wilson 95%) | 7 of 50 (7% to 26%) | 7 of 50 (7% to 26%) | same |
| partial protection (`-` in the column) | 5 of 50 | 5 of 50 | same |
| second coder: OPEN / CLOSED / PARTIAL | 2 / 9 / 39 | 2 / 9 / 39 | same |
| class: agreement, κ, PABAK, AC1 | 84%, 0.42, 0.79, 0.82 | 84%, 0.42, 0.79, 0.82 | same |
| class, OPEN against the rest: agreement, κ, PABAK, AC1 | 98%, 0.66, 0.96, 0.98 | 98%, 0.66, 0.96, 0.98 | same |
| domain: agreement, κ, PABAK, AC1 | 70%, 0.60, 0.62, 0.63 | 70%, 0.60, 0.62, 0.63 | same |
| domain, OPEN against the rest: agreement, κ, PABAK, AC1 | 78%, 0.45, 0.56, 0.65 | 78%, 0.45, 0.56, 0.65 | same |
| second coder's OPEN share (Wilson 95%) | 2/50, 4% (1% to 13%) | 2/50, 4% (1% to 13%) | same |

The frame keeps its 190 fingerprints, so the seeded draw selects the same 50 contents and
both coders' labels apply unchanged. Only the copy counts move: the OPEN table's content
appeared in 7 distinct files when CRLF and LF copies were counted apart, and in 4 now.
`coding/blind_sheet.csv` carries no copy counts and is unchanged.

## TCK test inputs (`TESTINPUTS.md`)

| figure | old (7603ea2) | new | |
|---|---|---|---|
| TCK test files (distinct) | 158 | 158 | same |
| test cases | 3,456 | 3,456 | same |
| input values | 442 | 442 | same |
| resolved to a column | 198 | 198 | same |
| links | 268 | 268 | same |
| string links (string value into a string column with literals) | 58 | 58 | same |
| unmentioned values | 2 | 2 | same |
| unmentioned and no rule can match | 0 | 0 | same |
| other formats counted (scesim / TCK-style XML / JSON or YAML) | 58 / 1,055 / 75 | 58 / 1,055 / 75 | same |

`testinputs.json` changes in the SHA-256 of the test and model files (the TCK XML is now
LF) and in the inventory row of the Corea verifier, which is now a git checkout (an empty
inventory in place of `?`). The fetch now adds `*-test-*.xml` to the TCK sparse checkout;
without it `run_dmn_testinputs.py` finds no test file, prints a warning naming the pattern
and the TCK path, and exits with status 1.

**Run-to-run stability.** `dmn_testinputs.bkm_bindings` iterated a set of decision names, whose
order depends on Python's per-process hash seed, so the order of the links in
`testinputs.json` (and, when two decisions bind the same BKM parameter, the binding kept)
could change from one run to the next; the summary figures above did not move. It now
iterates the names sorted. Two further runs of all three scripts give byte-identical files in
this folder.
