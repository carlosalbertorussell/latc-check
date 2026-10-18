# Corea, Blatt & Delfmann DMN verifier: where gap analysis gets its input domains

Tool: https://gitlab.uni-koblenz.de/jonasblatt/ma-jonasblatt-dmn-verifier (link from Appendix A
of Blatt's thesis), branch `develop`, commit 5b307e8481170d37b63a9b256a45c3c38c7fa50c
(2023-07-10). Java 17, Quarkus 3.1.2, camunda-dmn-model 7.19.0. Built with Maven and run
headlessly through its REST backend
(`/api/dmn/verification/types?typeName=MissingRulesVerification&typeName=MissingPredefinedValueVerification&typeName=UnusedPredefinedValueVerification`).

Inputs: `results/tools/inputs/`. The tool rejects all 39 original files (HTTP 400: its
camunda-dmn-model 7.19 has no DMN 1.4 schema), so it was run on copies in `adapted/` with two
format-only changes: namespace DMN 1.3, and `typeRef="string"` on `<output>`. Inputs,
inputValues, itemDefinitions and rules are unchanged. With V3b (inputExpression typeRef naming an
itemDefinition) the parser throws a NullPointerException and the file is rejected.

## Finding

The Missing Rules verifier never reads declared domains: it starts from an all-wildcard rule and
subtracts each rule, so every string column is an open universe, and gaps are reported as
`not(...)` complements of the values used in the rules (`MissingRuleVerifier` never calls
`getPredefinedValues()`). V1, V2 and V4 therefore give the same missing-rule list in every case.
The removed value is never named; it appears only inside a `not(...)` region that also covers
arbitrary undeclared strings, and every table gets 3–7 entries that contain no declared state at
all. Declared values (`inputValues` only) are read by the two predefined-value checks: Unused
Predefined Value names the removed value, but only in V1; with no declaration (V2) Missing
Predefined Value flags every rule cell. The verifier also has a completeness defect: on pension
with Age 60-64 removed, its regions miss 2 of the 20 missing states, (M, I, <30, 60-64) and
(M, I, <30, <60), in V1, V2 and V4 (checked by hand against the eight reported entries).

| Case | Variant | Rules | Missing-rule entries (of which outside the declared domain) | Missing states covered | Removed-value states covered | Unused value names removed value |
|---|---|---|---|---|---|---|
| pension Age >=65 | V1 / V2 / V4 | 5 | 9 (3) | 19/19 | 8/8 | V1 only |
| pension Age 60-64 | V1 / V2 / V4 | 4 | 8 (3) | **18/20** | **7/8** | V1 only |
| pension Age <60 | V1 / V2 / V4 | 7 | 10 (4) | 17/17 | 8/8 | V1 only |
| Car, 6 cases | V1 / V2 / V4 | 1,152–1,296 | 6 (5) | all | all | V1 only |
| Nursery finance=convenient | V1 / V2 / V4 | 6,480 | 8 (7) | 6480/6480 | 6480/6480 | V1 only |
| any | V3b | – | error (NullPointerException) | – | – | – |

"Covered" means inside some reported region read over the declared domain; the regions are
`not(...)` complements, so covering a missing state does not mean the tool named its value.
Runtime per file: pension under 1 s, Car 3–19 s, Nursery 194–287 s. Downloads: Temurin 17
(191 MB), source archives (16.5 MB), Maven dependencies (121 MB), about 330 MB in total, under
`C:\Users\crussell\Downloads\repos\tools\corea-verifier`. Per-run details in `results.json`.
