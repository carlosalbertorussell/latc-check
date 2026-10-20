# Rerunning the DMN analyser audit

This is the outside replication of the analyser audit (Section 9.2, Appendix C.6): three DMN
gap analysers run on the same 39 DMN files, each a decision table with one value of one input
removed from every rule, written in four ways that differ only in how the input domains are
declared. The question is which declaration makes each analyser find the missing states.

| variant | how the domains are declared |
|---|---|
| V1 | `inputValues` with the full declared values, on every input |
| V2 | nothing (typeRef `string` only) |
| V3b | an `itemDefinition` with the full `allowedValues`, named by the `inputData` variable and by the `inputExpression` typeRef |
| V4 | `inputValues` listing only the values the rules mention |

The cases are pension with each Age value removed (3 cases, 12 files), Car with one value of each
attribute removed (6 cases, 24 files), and Nursery with finance = convenient removed (V1, V2, V4;
3 files). `results/tools/inputs/manifest.json` gives, per case, the declared domains, the number
of truly missing states and how many of them carry the removed value.

The harnesses are the ones the paper used, unchanged:

* Drools 7.74.1.Final and Apache KIE 10.2.0: the driver `DroolsCheck.java` (the same file in
  `tools/drools/` and `results/tools/kie10/`), which runs `DMNValidator` with schema and model
  validation and decision-table analysis and prints one line per message. `run_drools.py` here
  calls it once per file through `latc_check.drools_domains.run_one`.
* The 2016 dmn-js verifier (Laurson and Maggi): `results/tools/dmn-js/harness.js`, which loads
  `lib/features/verifier/Verifier.js` of the fork unchanged under Node, driven by
  `results/tools/dmn-js/run_all.js`.

`score.py` reads the raw outputs, recomputes the true missing states of every file from the DMN
file itself, checks them against the manifest, and reports for each file how many missing states
the analyser found, how many of those carry the removed value, and how many reported states are
not missing; it also says whether each result equals the published one.

## 0. Get the repository and the inputs

```bash
python -I run_tool_inputs.py
```

Run from the repository root (Python 3.10 or later). It writes the 39 `.dmn` files to
`results/tools/inputs/` (they are gitignored) and rewrites `manifest.json`, which should come out
byte-identical (`git status` shows no change). `score.py` checks every input file against
`replication/expected_sha256.txt` before scoring.

## 1. Drools 7.74.1 and Apache KIE 10.2.0

Downloads: a JDK (8 or later for 7.74.1, 17 or later for 10.2.0; the paper's cloud re-run used
OpenJDK 21 for both), Maven 3.9 (only to fetch the libraries), 39 jars (about 17 MB) for 7.74.1
and 59 jars (about 27 MB) for 10.2.0.

Build one driver folder per version (any location; `d7/` and `kie10/` below):

```bash
mkdir d7 kie10
cp tools/drools/pom.xml tools/drools/DroolsCheck.java d7/
cp results/tools/kie10/pom.xml results/tools/kie10/DroolsCheck.java kie10/
```

In each folder:

```bash
mvn -B dependency:copy-dependencies -DoutputDirectory=lib
```

```bash
javac -cp "lib/*" -d out DroolsCheck.java
```

Then run every file, from the repository root (on Windows use `java.exe` paths as needed):

```bash
python -I replication/tool_audit/run_drools.py --driver-dir d7 --java java --out replication/tool_audit/raw/d7
```

```bash
python -I replication/tool_audit/run_drools.py --driver-dir kie10 --java java --out replication/tool_audit/raw/kie10
```

Each file runs in its own JVM, and its output goes to `raw/<version>/<file>.dmn.txt`. Pension and
Car take 5 to 10 seconds per file. **Nursery V1 (6,480 rules) takes 35 to 40 minutes per version**
on one core and about 1.3 GB (7.74.1) and 2.3 GB (10.2.0) of memory; give the JVM room with
`JAVA_TOOL_OPTIONS=-Xmx8g`. To leave it for last, run once with `--skip nursery_finance_convenient_V1`
and once with `--only nursery_finance_convenient_V1`. Interrupted runs resume where they stopped
(files with output are skipped). The default per-file timeout is 2 hours (`--timeout`).

Drools 7.74.1 also runs on Java 8, which the laptop runs used. The cloud re-run
(`results/tools/cloud-drools/SUMMARY.md`) got the same results on Java 21 as the laptop on Java 8
(7.74.1) and 17 (10.2.0).

## 2. The dmn-js verifier (2016)

Downloads: Node (the paper used v24.19.0), a clone of the fork (2.9 MB) and dmn-moddle 0.2.3
(3.0 MB of npm packages).

```bash
git clone https://github.com/ulaurson/dmn-js dmn-js-verifier
```

```bash
git -C dmn-js-verifier checkout e0b6417a95ea2685e2cd8b46421634afd08b23ec
```

```bash
mkdir harness-deps && cp results/tools/dmn-js/package.json harness-deps/ && npm install --prefix harness-deps
```

Then, from the repository root:

```bash
node results/tools/dmn-js/run_all.js dmn-js-verifier harness-deps
```

It runs `harness.js` on all 39 files (V3b twice: as written, and with the typeRef resolved to
`string`), about 5 minutes in all, and **writes `results/tools/dmn-js/results.json` over the
committed file**. Move the new file aside and restore the committed one:

```bash
mkdir -p replication/tool_audit/raw/dmn-js && mv results/tools/dmn-js/results.json replication/tool_audit/raw/dmn-js/results.json && git checkout -- results/tools/dmn-js/results.json
```

## 3. Scoring

```bash
python -I replication/tool_audit/score.py --drools d7=replication/tool_audit/raw/d7 kie10=replication/tool_audit/raw/kie10 --dmnjs dmnjs=replication/tool_audit/raw/dmn-js/results.json --out replication/tool_audit/score.md --json replication/tool_audit/score.json
```

The labels before `=` are free text, but a Drools label must start with `d7` or `kie10`: it picks
the published run to compare with (`results/tools/cloud-drools/results.json`). The dmn-js output
is compared with the committed `results/tools/dmn-js/results.json`.

The report has one summary row per tool, dataset and variant and one row per file:

* **missing (removed value)**: the true missing states of the file, from the manifest and
  recomputed from the DMN file (the script stops if the two disagree);
* **found**: missing states inside a gap the analyser reported. For Drools the gap messages are
  read with `latc_check.drools_domains.evaluate`, the evaluation of the paper's runs: a `-` or a
  range in a gap is read over the values Drools had for that input (the declared values for V1
  and V3b, the values in the rules for V4; Drools skips gap analysis in V2). For dmn-js it is the
  harness's own count, and the "recomputed" column expands the reported regions again in
  `score.py`; the two must agree;
* **removed-value found**: how many of the found states carry the removed value;
* **extra states**: reported states that are not missing (false gaps);
* **same as the published run**: `same`, or the fields that differ.

The last line counts the rows that differ from the published runs. Files that were not run are
listed as `not run`. The published cloud runs did not include Nursery V4 for Drools.

What the paper reports, for comparison: Drools and KIE find every missing state and nothing else
with V1 and V3b; they skip gap analysis with V2 ("Gap analysis skipped"); with V4 they find no
state that carries the removed value, and on Car they report "no gaps". The dmn-js verifier gives
the same gaps for V1, V2 and V4: on pension only gaps among the values the rules mention, none
with the removed value; on Car and Nursery no gaps at all; raw V3b gives numeric `NaN` regions.

## What to send back

`score.md`, `score.json`, the `raw/` folders (zipped), the tool versions and JDK / Node versions,
and the "Tool audit" part of `replication/REPORT_TEMPLATE.md`.

## Tested

`run_drools.py` and `score.py` were run on the reference machine on the 12 pension files with the
local Drools 7.74.1 build (Temurin 8) and on 4 with KIE 10.2.0 (Temurin 17), and `run_all.js` on
the 15 pension runs; all equal the published runs. `score.py` also reproduces the published result
for all 38 committed raw outputs in `results/tools/cloud-drools/raw/` of each version and for the
48 runs in the committed `results/tools/dmn-js/results.json`.
