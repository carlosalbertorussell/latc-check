# Drools 7.74.1 and the observed-domain trap

T0 = a complete table minus every row with one value of one attribute, written as DMN UNIQUE point rules. *missing* = states of the declared product absent from T0; *found* = missing states inside Drools' reported gaps (`DECISION_TABLE_GAP`), each gap token (including '-') read over the values Drools was given for that input; the last column reads '-' as every declared value (upper bound). Variants: **V1** inputValues = full declared values (all inputs); **V2** no allowed values declared (typeRef string only); **V3a** itemDefinition allowedValues (full) on inputData variable only; inputExpression typeRef string; **V3b** itemDefinition allowedValues (full) on inputData variable and inputExpression typeRef; **V4** inputValues = values observed in T0; **V5** inputValues = full values on all inputs except the removed attribute (none there); **V6** inputValues = observed values; inputExpression typeRef = itemDefinition with full values; **V7** inputValues = full values; inputExpression typeRef = itemDefinition with observed values.

| dataset | variant | cases | Drools outcome (cases) | missing | found | removed-value states | found | found, '-' read as full |
|---|---|---|---|---|---|---|---|---|
| car | V1 | 11 | gaps reported (11) | 5184 | 5184 | 5184 | 5184 | 5184 |
| car | V2 | 11 | gap analysis skipped (11) | 5184 | 0 | 5184 | 0 | 0 |
| car | V3a | 11 | gap analysis skipped (11) | 5184 | 0 | 5184 | 0 | 0 |
| car | V3b | 11 | gaps reported (11) | 5184 | 5184 | 5184 | 5184 | 5184 |
| car | V4 | 11 | no gaps reported (11) | 5184 | 0 | 5184 | 0 | 0 |
| car | V5 | 10 | gap analysis skipped (10) | 4752 | 0 | 4752 | 0 | 0 |
| car | V6 | 6 | no gaps reported (6) | 3024 | 0 | 3024 | 0 | 0 |
| car | V7 | 6 | gaps reported (6) | 3024 | 3024 | 3024 | 3024 | 3024 |
| nursery | V2 | 8 | gap analysis skipped (8) | 32832 | 0 | 32832 | 0 | 0 |
| pension | V1 | 3 | gaps reported (3) | 56 | 56 | 24 | 24 | 56 |
| pension | V2 | 3 | gap analysis skipped (3) | 56 | 0 | 24 | 0 | 0 |
| pension | V3a | 3 | gap analysis skipped (3) | 56 | 0 | 24 | 0 | 0 |
| pension | V3b | 3 | gaps reported (3) | 56 | 56 | 24 | 24 | 56 |
| pension | V4 | 3 | gaps reported (3) | 56 | 32 | 24 | 0 | 42 |
| pension | V5 | 3 | gap analysis skipped (3) | 56 | 0 | 24 | 0 | 0 |
| pension | V6 | 3 | gaps reported (3) | 56 | 32 | 24 | 0 | 42 |
| pension | V7 | 3 | gaps reported (3) | 56 | 56 | 24 | 24 | 56 |

Pension: T0 = Table 1a (8 rows) minus its rows with Age = v, so it also misses states with the other Age values; *missing* counts all of them, *removed-value states* only those with Age = v. Car and Nursery: every missing state has the removed value.

## Finding

Drools does not take string domains from the values the rules mention: when a string input has no enumerated values (V2; also V3a, where the itemDefinition is attached only to the inputData variable; V5, where only the removed attribute lacks them) it emits the WARNING `DECISION_TABLE_GAP` "Columns: [...] relate to FEEL string values which can be enumerated for the inputs; Gap analysis skipped" and reports no gap, in every case, so it neither finds the missing value nor declares the table complete. With the full values declared, either as `inputValues` on the decision-table input (V1) or as `allowedValues` of an `itemDefinition` named by the `inputExpression` typeRef (V3b), Drools reports gaps covering exactly the missing states (no extra states) in every case run. The trap appears when the declaration itself is the observed domain: `inputValues` listing only the values T0 mentions (V4) gives "no gaps" on every Car case (a false complete verdict, 0 of the removed-value states found) and, on the pension example, only the gaps inside the observed product. When both declarations are present, `inputValues` wins over the inputExpression's itemDefinition (V6 behaves as V4, V7 as V1).

## Runs not completed

Nursery: only V2 was run (one case per attribute). A probe of Nursery finance=convenient (6480 rules, the smallest Nursery case) ran V2 and V3a in about 2 min each (both: gap analysis skipped), but V1 (full analysis) had not finished after about 61 min and was killed; V1, V3b, V4, V6 were therefore not run on Nursery. Car: one case per attribute was required; buying=high, buying=med, buying=low, maint=high, maint=med were also run (core variants V1-V5; maint=med lacks V5 because that run was killed when the scope was trimmed, and was not re-run). An earlier Car/pension pass was discarded and re-run with --fresh after the evaluation was changed to read '-' over Drools' own domain.
