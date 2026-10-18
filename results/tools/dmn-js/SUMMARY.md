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
