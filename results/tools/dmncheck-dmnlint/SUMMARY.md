# dmn-check and dmnlint: no missing-rule check

Tools: red6 dmn-check 1.1.6 (newest release that runs on Java 8; 1.4.0 needs Java 21, and its
sources and GitHub master have the same validator set) and bpmn.io dmnlint 2.0.0. Inputs:
`results/tools/inputs/`; both tools reject the DMN 1.4 namespace (dmn-check: schema error
`cvc-elt.1`; dmnlint: parse error), so they were run on copies in `converted_dmn13/` that
differ only in the namespace (DMN 1.3). `scripts/convert_to_dmn13.sh` recreates them.

## Finding

Running both tools on all pension and Car files (and Nursery for dmnlint) confirms that
neither has a missing-rule check. dmn-check's 21 validators cover ids and names, types, the
requirement graph, and duplicate, conflicting and shadowed rules; dmnlint's two rules cover
empty labels and duplicate requirements. On the DMN 1.3 copies, dmn-check reports only "Output
has no type" for V1, V2 and V4, and for V3b adds a type error on every input entry (a false
positive: it does not resolve the itemDefinition to its base type string). dmnlint reports
nothing. Neither tool reports any gap, whether the input domains are declared through
inputValues, through allowedValues, or not at all, although every file has 17–6,480 missing
states. Positive controls built for each tool's own checks (duplicate, conflicting and shadowed
rules; empty label; duplicate requirement) are reported correctly.

| Tool | Version | Missing-rule check | Pension (12 files) | Car (24 files) | Nursery |
|---|---|---|---|---|---|
| dmn-check | 1.1.6 | none (21 validators) | V1/V2/V4: "Output has no type"; V3b: + type errors | same | not run (~50 min per file) |
| dmnlint | 2.0.0 | none (2 rules) | 0 findings | 0 findings | 0 findings |

Runtime per file: dmn-check 0.06–1.7 s on pension, 56–133 s on Car; dmnlint under 1.2 s, 3.7–5.9
s on Nursery. Downloads: dmn-check 1.1.6 and dependencies about 2.6 MB (Maven Central, into
`~/.m2`), dmnlint 2.0.0 about 1.4 MB (npm, local). Details per file in `results.json` and `raw/`.
