// Adds diagnosed error causes (from ParseCheck.java, see parsecheck.log) and per-case comparisons to results.json.
import fs from 'node:fs';
const P = new URL('./results.json', import.meta.url);
const r = JSON.parse(fs.readFileSync(P, 'utf8'));
for (const x of r.runs) {
  if (x.outcome !== 'error') continue;
  x.error = x.mode === 'original'
    ? 'HTTP 400 "The dmn syntax is not correct". Cause (ParseCheck.java): camunda-dmn-model 7.19 schema validation, cvc-elt.1.a no declaration for element definitions; the DMN 1.4 namespace (20211108) is not supported'
    : 'HTTP 400. Cause (ParseCheck.java): NullPointerException in VDmnInputValueImpl.Builder: VDmnColumn.getTypeRef() is null, because the inputExpression typeRef names an itemDefinition, and the parser only maps built-in type names';
}
r.adaptation = 'adapted/ = input file with namespace https://www.omg.org/spec/DMN/20211108/MODEL/ replaced by the DMN 1.3 namespace https://www.omg.org/spec/DMN/20191111/MODEL/ and typeRef="string" added to <output> (the parser rejects an output column without typeRef). Inputs, inputValues, itemDefinitions and rules are unchanged.';
const groups = {};
for (const x of r.runs.filter(x => x.mode === 'adapted' && x.http_status === 202)) {
  const k = x.file.replace(/_V\w+\.dmn$/, '');
  (groups[k] ??= {})[x.variant] = x;
}
r.variant_comparison = Object.fromEntries(Object.entries(groups).map(([k, v]) => {
  const key = x => x && x.missing_rules_all_sorted ? JSON.stringify(x.missing_rules_all_sorted.map(m => m.replace(/(pension|car|nursery)_\S+/g, ''))) : (x ? `${x.missing_rules_reported} rules` : null);
  return [k, { missing_rules_identical_V1_V2: key(v.V1) === key(v.V2), missing_rules_identical_V1_V4: key(v.V1) === key(v.V4),
    note: v.V1 && !v.V1.missing_rules_all_sorted ? 'nursery: compared by count only (full lists not stored)' : undefined }];
}));
fs.writeFileSync(P, JSON.stringify(r, null, 1));
console.log(JSON.stringify(r.variant_comparison, null, 1));
