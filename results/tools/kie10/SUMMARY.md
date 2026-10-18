# Apache KIE (Drools) DMN validator 10.2.0 vs 7.74.1: input domains for gap analysis

**Tool tested:** org.kie:kie-dmn-validation and kie-dmn-core **10.2.0**, the latest 10.x release on Maven Central (maven-metadata latest/release = 10.2.0, checked 2026-10-18). Run on Eclipse Temurin **17.0.20.1+1** (Windows x64) with -Xmx1200m. The driver is `DroolsCheck.java`, copied unchanged from tools/drools: the 7.74.1 API (`DMNValidatorFactory.newValidator()`, `validate(File, VALIDATE_SCHEMA, VALIDATE_MODEL, ANALYZE_DECISION_TABLE)`) compiles and runs as-is on 10.2.0. Each file ran in its own JVM.

**Baseline:** Drools 7.74.1.Final on Java 8, from results/drools/domains/results.json, matched on the same case (dataset, attribute, removed value) and variant.

**Inputs:** results/tools/inputs/ (shared, read-only); ground truth from manifest.json. Missing states were recomputed from each file's rules and checked against the manifest counts.

**Evaluation:** the 7.74.1 code is reused through `latc_check.drools_domains.evaluate` and `gap_tokens`. Each gap token is read over the values Drools had for that input: full values in V1 and V3b, the values observed in the rules in V4. A file counts as "same as 7.74.1" when all of the following are identical:
- outcome
- number of gap messages
- states covered
- missing states covered
- covered-but-not-missing states
- removed-value states found
- skip columns
- message types
- the first five gap strings

## Comparison (per dataset and variant, summed over files)

| dataset | variant | files | 7.74.1 outcome | 10.2.0 outcome | missing | found 7.74.1 / 10.2.0 | removed-value states | found 7.74.1 / 10.2.0 | extra states (10.2.0) | 10.2.0 s (median) | same as 7.74.1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pension | V1 | 3 | gaps reported (3) | gaps reported (3) | 56 | 56 / 56 | 24 | 24 / 24 | 0 | 9.7 | yes |
| pension | V2 | 3 | gap analysis skipped (3) | gap analysis skipped (3) | 56 | 0 / 0 | 24 | 0 / 0 | 0 | 7.6 | yes |
| pension | V3b | 3 | gaps reported (3) | gaps reported (3) | 56 | 56 / 56 | 24 | 24 / 24 | 0 | 7.3 | yes |
| pension | V4 | 3 | gaps reported (3) | gaps reported (3) | 56 | 32 / 32 | 24 | 0 / 0 | 0 | 8.7 | yes |
| car | V1 | 6 | gaps reported (6) | gaps reported (6) | 3024 | 3024 / 3024 | 3024 | 3024 / 3024 | 0 | 63.9 | yes |
| car | V2 | 6 | gap analysis skipped (6) | gap analysis skipped (6) | 3024 | 0 / 0 | 3024 | 0 / 0 | 0 | 16.7 | yes |
| car | V3b | 6 | gaps reported (6) | gaps reported (6) | 3024 | 3024 / 3024 | 3024 | 3024 / 3024 | 0 | 63.2 | yes |
| car | V4 | 6 | no gaps reported (6) | no gaps reported (6) | 3024 | 0 / 0 | 3024 | 0 / 0 | 0 | 60.8 | yes |
| nursery | V1 | 1 | not run (1) | not finished (timeout) (1) | 6480 | - / - | 6480 | - / - | - | 901.2 | n/a (7.74.1 not run) |
| nursery | V2 | 1 | gap analysis skipped (1) | gap analysis skipped (1) | 6480 | 0 / 0 | 6480 | 0 / 0 | 0 | 102.5 | yes |

message types 10.2.0: DECISION_TABLE_2NDNFVIOLATION, DECISION_TABLE_CONTRACTION_RULE, DECISION_TABLE_GAP
message types 7.74.1 (same files): DECISION_TABLE_2NDNFVIOLATION, DECISION_TABLE_CONTRACTION_RULE, DECISION_TABLE_GAP

"found" = missing states inside the reported `DECISION_TABLE_GAP` boxes. "extra states" = states inside reported gaps that are not missing (always 0).

## Finding

**10.2.0 behaves exactly as 7.74.1 on every file both versions ran (37 of 37).**

| variant | 10.2.0 vs 7.74.1 | result |
|---|---|---|
| V1 | same | gaps cover exactly the missing states, including all removed-value states |
| V3b | same | gaps cover exactly the missing states, including all removed-value states |
| V2 | same | the same WARNING `DECISION_TABLE_GAP` "Columns: [...] relate to FEEL string values which can be enumerated for the inputs; Gap analysis skipped", and no gaps |
| V4 | same | observed domain: "no gaps" on all 6 Car files (a false complete verdict, 0 of 3,024 removed-value states found); on pension, only the gaps inside the observed product (32 of 56 missing, 0 of 24 removed-value states) |

- **Message types:** no new ones. Both versions emit `DECISION_TABLE_GAP`, `DECISION_TABLE_CONTRACTION_RULE` and `DECISION_TABLE_2NDNFVIOLATION`.
- **Log output:** 10.2.0 also logs two slf4j WARN lines about an eval expression in the validator's own rule base, on stderr/stdout before the results. These are engine log lines, not validation messages.
- **Runtime:** roughly 1.5-2 times longer than 7.74.1 on this machine. Car V1 median is 64 s against about 38 s; Nursery V2 is 102 s against 104 s. Other agents were running Java at the same time and RAM was low, so these times are only indicative.

## Not run / not finished

- **Nursery V1** (finance=convenient, 6,480 rules) was killed at the 15-minute cap (901 s) with no output. 7.74.1 had not finished this file after about 61 minutes either, so neither version has a result for it.
- **Nursery V4** was not run (out of scope).
- **V3a, V5, V6, V7** are not in the shared inputs and were not run.
- **Car** coverage was one case per attribute (6 files per variant), as in the shared inputs.

## Files

- `pom.xml`: dependencies; libraries copied with `mvn dependency:copy-dependencies` into tools/kie10/lib.
- `DroolsCheck.java`: the driver, unchanged from tools/drools.
- `run_kie10.py`: the wrapper. It runs each file, evaluates it and compares it with 7.74.1. Run with `python -I`; it resumes from results.json.
- `summarize.py`: prints the table above.
- `results.json`: per-file results.
- `raw/`: the driver output for each file.
- `PROGRESS.md`: the progress log.

Downloads: Temurin JDK 17 zip, 190.8 MB (sha256 matches Adoptium's published checksum); 59 jars, 27 MB in lib; local Maven repo tools/kie10/m2, 50 MB including Maven plugins. Nothing was installed globally, and PATH and system settings were not changed.
