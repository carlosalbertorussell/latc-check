// Builds positive-control DMN files (DMN 1.3 namespace) from a converted pension file,
// to show that each tool's checks actually fire when their target defect is present.
//  ctrl_duplicate_rule.dmn     : rule_0 copied verbatim            -> dmn-check DuplicateRuleValidator
//  ctrl_conflicting_rule.dmn   : rule_0 inputs, different output   -> dmn-check ConflictingRuleValidator
//  ctrl_shadowed_rule.dmn      : rule "-" ,"-","-","-" first        -> dmn-check ShadowedRuleValidator (FIRST hit policy)
//  ctrl_dmnlint.dmn            : empty decision name + duplicated informationRequirement -> dmnlint rules
const fs = require('fs');
const base = 'C:/Users/crussell/Downloads/repos/LATC/results/tools/dmncheck-dmnlint/';
const src = fs.readFileSync(base + 'converted_dmn13/pension_Age_lt60_V1.dmn', 'utf-8');
const rule0 = src.match(/<rule id="rule_0">[\s\S]*?<\/rule>/)[0];
const reid = (s, n) => s.replace(/rule_0/g, n);
const out = {};
out.ctrl_duplicate_rule = src.replace('</decisionTable>', reid(rule0, 'rule_dup') + '\n    </decisionTable>');
out.ctrl_conflicting_rule = src.replace('</decisionTable>',
  reid(rule0, 'rule_conf').replace(/(<outputEntry[^>]*>\s*<text>)"[^"]*"/, '$1"NO"') + '\n    </decisionTable>');
const anyRule = reid(rule0, 'rule_any').replace(/(<inputEntry[^>]*>\s*<text>)[^<]*/g, '$1-');
out.ctrl_shadowed_rule = src.replace('hitPolicy="UNIQUE"', 'hitPolicy="FIRST"').replace(rule0, anyRule + '\n      ' + rule0);
out.ctrl_dmnlint = src
  .replace(/(<decision id="[^"]*" name=")[^"]*"/, '$1"')
  .replace(/(<informationRequirement id="[^"]*_req_0">[\s\S]*?<\/informationRequirement>)/,
    m => m + '\n    ' + m.replace(/_req_0"/, '_req_0_dup"'));
fs.mkdirSync(base + 'controls', { recursive: true });
for (const [k, v] of Object.entries(out)) fs.writeFileSync(base + 'controls/' + k + '.dmn', v);
console.log(Object.keys(out).join('\n'));
