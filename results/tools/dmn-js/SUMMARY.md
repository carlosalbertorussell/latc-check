# dmn-js verifier (Laurson & Maggi 2016): where it takes input domains from

Tool: https://github.com/ulaurson/dmn-js at commit e0b6417a95ea2685e2cd8b46421634afd08b23ec
(2016-05-19, identical to master), `lib/features/verifier/Verifier.js` loaded unchanged in
Node v24.19.0 through `harness.js` (DOM-free stubs and dmn-moddle 0.2.3; the shims, S1–S6,
are documented in the harness and do not touch the analysis logic). Inputs:
`results/tools/inputs/` (see its `manifest.json` for ground truth).

## Finding

Confirmed by execution. For string inputs the verifier builds each input's value set as the
union of the values in the rule cells (`getRulesAndInputs`, Verifier.js lines 1263–1283) and
never reads `inputValues` or an itemDefinition's `allowedValues`, although the parsed model
exposes both. Its gap output is identical for V1, V2 and V4 in every case. On pension it
reports only gaps among observed values (no false positives) and finds 0 of the 8 states with
the removed Age value; on Car and Nursery, where every missing state has the removed value, it
reports no gaps even with the full domain declared (V1). With V3b, whose inputExpression typeRef
names an itemDefinition, it treats the columns as numeric and reports meaningless `NaN`
intervals.

| Case (removed value) | Rules | Missing (with removed value) | V1 | V2 | V3b raw | V3b typeRef→string | V4 |
|---|---|---|---|---|---|---|---|
| pension Age >=65 | 5 | 19 (8) | 5 regions, 11/19, removed 0/8 | same as V1 | 30 NaN regions | same as V1 | same as V1 |
| pension Age 60-64 | 4 | 20 (8) | 6 regions, 12/20, removed 0/8 | same | 21 NaN regions | same | same |
| pension Age <60 | 7 | 17 (8) | 5 regions, 9/17, removed 0/8 | same | 40 NaN regions | same | same |
| Car buying / maint / doors (one value removed) | 1296 | 432 (432) | no gaps | no gaps | 14,257 NaN regions | no gaps | no gaps |
| Car persons / lug_boot / safety | 1152 | 576 (576) | no gaps | no gaps | 12,673 NaN regions | no gaps | no gaps |
| Nursery finance=convenient | 6480 | 6480 (6480) | no gaps | no gaps | – | – | no gaps |

Counts read each reported region over the tool's own domain. Runtimes: pension ≤ 0.04 s, Car
0.5–1.7 s (raw V3b 25–35 s), Nursery 17–20 s. Downloads: 2.9 MB clone and 3.0 MB of npm
packages, under `C:\Users\crussell\Downloads\repos\tools\dmn-js-verifier`.

Run: `node run_all.js <clone> <clone>/_harness [dataset]`.

## Gap and overlap output against the sweep and the oracle (random tables)

`compare_random.py` (Python driver) exports each table with `dmn.to_dmn_xml` (string inputs,
point entries, UNIQUE), runs `harness.js` unchanged on every file through `run_random.js`, and
compares the result with `dmn.analyse` (the sweep, regions expanded) and `dmn_oracle.oracle`.
`run_random.js` also records the verifier's overlap rows, which `harness.js` only counts, by
wrapping `addOverlappingRuleToTable` (records the rule numbers, then calls the original). Gap
regions are expanded over the domain the verifier uses (the values in the rule cells; `any` =
that domain) and compared with the oracle's uncovered states restricted to that domain, and
with the full declared domain. Overlaps: every pair inside every "Rules a, b, … are
overlapping" row, against the oracle's overlapping pairs; the verifier's maximal groups against
the oracle's maximal overlap sets. Per-table records: `random_tables.json`.

| Tables | Verifier ran | Gaps agree (verifier's domain) | Gaps agree (declared domain) | Overlapping pairs agree | Maximal sets agree |
|---|---|---|---|---|---|
| 1,000 random, all values observed (seed 20210101) | 1,000 | 1,000 | 1,000 | 1,000 (no overlaps in any) | 1,000 |
| Pension V1, three Age values removed | 3 | 3 | 0 (misses 8 of 8 removed-value states each) | 3 (no overlaps) | 3 |
| Car V1, six one-value removals | 6 | 6 (no gaps) | 0 (misses all 432 / 576) | 6 (no overlaps) | 6 |
| Supplementary: the 138 C.2 tables (seed 20210101) with only enumerated inputs and no not(), file as exported | 62 | 62 | 40 | 62 (32 tables with overlaps, 109 pairs) | 62 |
| Same 138, wildcard written as an empty cell (dmn-js 0.5 convention, input shim) | 138 | 138 | 102 | 138 (96 tables with overlaps, 499 pairs) | 138 |

The sweep equals the oracle on every table (gaps and pairs). The verifier never reports a
false gap, and its regions are pairwise disjoint.

- On all-observed tables the verifier's domain equals the declared domain in all 1,000 and its
  expanded gaps equal the sweep's and the oracle's states in all 1,000 (8,952 missing states).
- Every disagreement on the declared domain is the domain finding above: values that no rule
  cell mentions (the removed value in pension and Car; values reachable only through a
  wildcard or never mentioned in the C.2 tables) are absent from the verifier's domain, so the
  states that carry them are not reported. On its own domain the verifier agrees everywhere.
- Region merging differs, the states do not. The verifier merges two regions that differ in
  one column by set union in any value order, greedily, in discovery order; the sweep merges
  contiguous runs in declared value order (D-4). Totals on the 1,000 tables: 4,280 verifier
  regions against 4,945; fewer in 401 tables (up to 6 fewer), equal in 592, and one more in 7,
  where the greedy order leaves a split the sweep's fixed-point merge avoids (r0023: 4 against 3).
- Wildcards: the exported '-' is not a wildcard to the verifier; its string syntax check
  rejects the cell, and it skips the analysis (76 of 138 tables, every one with a '-'). The
  dmn-js 0.5 editor holds "any" as an empty cell, but dmn-moddle 0.2.3 parses `<text></text>`
  as undefined and the verifier then throws; `run_random.js` with WILDCARD_EMPTY=1 sets such
  entries to '' after parsing (input only). With that, the verifier treats '' as matching
  every value and agrees with the oracle on gaps (its domain) and overlaps in all 138.
- Overlap definition: the verifier reports geometric overlaps regardless of hit policy (it
  ignores hitPolicy), so it was compared with the oracle's geometric pairs, not with hit-policy
  violations. Its rows are maximal groups of rules with a common point, plus sub-rows for rules
  with equal outputs; the pairs and the maximal groups both equal the oracle's.

Runtime: 1,285 files (1,000 random, 9 pension/Car, 2 × 138 C.2) in 254 s wall at 4 child
processes (Node start-up and parsing dominate); summed verifier time 10.7 s on the 1,000
random tables (max 0.05 s), 3.0 s on the six Car tables. Whole driver 279 s.

Run (repo root): `python -I results/tools/dmn-js/compare_random.py <clone> [--work DIR]`.
