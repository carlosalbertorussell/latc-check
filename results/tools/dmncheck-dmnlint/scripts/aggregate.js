// Aggregates raw outputs into results.json.
const fs = require('fs');
const path = require('path');
const R = 'C:/Users/crussell/Downloads/repos/LATC/results/tools/dmncheck-dmnlint/';
const manifest = require('C:/Users/crussell/Downloads/repos/LATC/results/tools/inputs/manifest.json');

const fileInfo = {};
for (const c of manifest.cases) for (const [v, f] of Object.entries(c.files)) {
  fileInfo[path.basename(f)] = { dataset: c.dataset, attribute: c.attribute, removed_value: c.removed_value,
    variant: v, rules: c.rules, missing_states: c.missing_states };
}
const readJsonl = f => fs.existsSync(f) ? fs.readFileSync(f, 'utf-8').split(/\r?\n/).filter(Boolean).map(JSON.parse) : [];
const GAP_RE = /missing|gap|incomplete|complete|coverage|uncovered|not covered|unused|undeclared|not used/i;

function summarise(findings, key) {
  const c = {};
  for (const f of findings) { const k = `${f[key]} | ${f.severity || f.category} | ${f.message}`; c[k] = (c[k] || 0) + 1; }
  return c;
}

function dmncheck(rawFile) {
  return readJsonl(R + rawFile).map(r => ({
    file: path.basename(r.file), ...fileInfo[path.basename(r.file)],
    parsed: r.parsed, error: r.error,
    finding_counts: summarise(r.findings, 'validator'),
    gap_or_domain_related_findings: r.findings.filter(f => GAP_RE.test(f.message)).length,
    duplicate_conflict_shadow_findings: r.findings.filter(f => /Duplicate|Conflicting|Shadowed/.test(f.validator)).length,
    runtime_ms: r.parsed ? Math.round(r.parse_ms + r.validate_ms) : Math.round(r.total_ms)
  }));
}
function dmnlint(rawFile) {
  const d = JSON.parse(fs.readFileSync(R + rawFile, 'utf-8'));
  return d.results.map(r => ({
    file: path.basename(r.file), ...fileInfo[path.basename(r.file)],
    parsed: !r.parse_error, error: r.parse_error,
    finding_counts: summarise(r.findings, 'rule'),
    gap_or_domain_related_findings: r.findings.filter(f => GAP_RE.test(f.message) && !/^Parse error/.test(f.message)).length,
    runtime_ms: Math.round(r.ms)
  }));
}

const out = {
  generated: new Date().toISOString(),
  inputs: 'results/tools/inputs (39 DMN 1.4 files, manifest.json)',
  tools: {
    'dmn-check': {
      version_run: '1.1.6 (de.redsix:dmn-check-validators 1.1.6, camunda-dmn-model 7.14.0) on Temurin JDK 8u504',
      latest_version: '1.4.0 (requires Java 21; not run, no JDK >= 11 available and none downloaded)',
      how_run: 'scripts/RunDmnCheck.java: loads every validator via de.redsix.dmncheck.util.ValidatorLoader.getValidators() (same default set as the maven plugin/CLI) and applies each to every file',
      validators_installed_1_1_6: ['AggregationOutputTypeValidator', 'AggregationValidator', 'ConflictingRuleValidator', 'ConnectedRequirementGraphValidator', 'DecisionIdAndNameValidator', 'DefinitionsIdAndNameValidator', 'DuplicateColumnLabelValidator', 'DuplicateRuleValidator', 'InputDataValidator', 'InputEntryTypeValidator', 'InputTypeDeclarationValidator', 'InputValuesTypeValidator', 'ItemDefinitionAllowedValuesTypeValidator', 'ItemDefinitionIdAndNameValidator', 'KnowledgeSourceIdAndNameValidator', 'NoDecisionPresentValidator', 'OutputEntryTypeValidator', 'OutputTypeDeclarationValidator', 'OutputValuesTypeValidator', 'RequirementGraphLeafValidator', 'ShadowedRuleValidator'],
      validators_1_4_0_sources: ['AggregationOutputTypeValidator', 'AggregationValidator', 'ConflictingRuleValidator', 'ConnectedRequirementGraphValidator', 'DecisionIdAndNameValidator', 'DefinitionsIdAndNameValidator', 'DuplicateColumnLabelValidator', 'DuplicateRuleValidator', 'InputDataIdAndNameValidator', 'InputEntryTypeValidator', 'InputTypeDeclarationValidator', 'InputValuesTypeValidator', 'ItemDefinitionAllowedValuesTypeValidator', 'ItemDefinitionIdAndNameValidator', 'KnowledgeSourceIdAndNameValidator', 'NoDecisionPresentValidator', 'OutputEntryTypeValidator', 'OutputTypeDeclarationValidator', 'OutputValuesTypeValidator', 'RequirementGraphLeafValidator', 'ShadowedRuleValidator'],
      validators_github_master_2026_09_14: 'same 21 concrete validators as 1.4.0',
      has_missing_rule_check: false,
      results_original_dmn14: dmncheck('raw/dmncheck_original_dmn14.jsonl'),
      results_converted_dmn13: dmncheck('raw/dmncheck_converted_dmn13.jsonl'),
      positive_controls: dmncheck('raw/dmncheck_controls.jsonl')
    },
    dmnlint: {
      version_run: '2.0.0 (npm, released 2026-10-16; dmn-moddle 12.2.1, @bpmn-io/lint-core) on Node v24.19.0',
      how_run: 'scripts/run_dmnlint.js: same steps as the dmnlint CLI (dmn-moddle fromXML + import warnings + Linter with extends "dmnlint:all"); CLI also spot-checked',
      rules_installed_2_0_0: ['label-required', 'no-duplicate-requirements'],
      rules_0_2_0_and_1_0_0: ['label-required', 'no-duplicate-requirements'],
      has_missing_rule_check: false,
      results_original_dmn14: dmnlint('raw/dmnlint_original_dmn14.json'),
      results_converted_dmn13: dmnlint('raw/dmnlint_converted_dmn13.json'),
      positive_controls: dmnlint('raw/dmnlint_controls.json')
    }
  }
};
fs.writeFileSync(R + 'results.json', JSON.stringify(out, null, 1));
// compact per-variant table on stdout
for (const [tool, t] of Object.entries(out.tools)) for (const k of ['results_original_dmn14', 'results_converted_dmn13']) {
  const g = {};
  for (const r of t[k]) {
    const key = `${r.dataset}/${r.variant}`;
    g[key] = g[key] || { files: 0, parsed: 0, findings: {}, gap: 0, ms: [] };
    g[key].files++; if (r.parsed) g[key].parsed++; g[key].gap += r.gap_or_domain_related_findings; g[key].ms.push(r.runtime_ms);
    for (const [f, n] of Object.entries(r.finding_counts)) g[key].findings[f] = (g[key].findings[f] || 0) + n;
  }
  console.log(`\n### ${tool} ${k}`);
  for (const [key, v] of Object.entries(g)) console.log(key, `files=${v.files} parsed=${v.parsed} gap=${v.gap} ms=${Math.min(...v.ms)}-${Math.max(...v.ms)}`, JSON.stringify(v.findings));
}
