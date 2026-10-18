// Runs bpmn.io dmnlint (installed in TOOLS dir) on DMN files, mirroring what the
// dmnlint CLI does (@bpmn-io/lint-core/lib/cli.js lintDiagram): parse with dmn-moddle,
// report moddle import warnings, then run the linter with the "dmnlint:all" config
// (every bundled rule, severity error). Prints a JSON array to stdout.
// Usage: node run_dmnlint.js <file.dmn> [...]
const { createRequire } = require('module');
const fs = require('fs');
const path = require('path');

const TOOLS = 'C:/Users/crussell/Downloads/repos/tools/dmncheck-dmnlint/dmnlint/';
const req = createRequire(TOOLS + 'package.json');
const { DmnModdle } = req('dmn-moddle');
const Linter = req('dmnlint/lib/linter');
const NodeResolver = req('dmnlint/lib/resolver/node-resolver');
const dmnlintVersion = req('dmnlint/package.json').version;
const moddleVersion = req('dmn-moddle/package.json').version;
const allConfig = req('dmnlint/config/all');

async function lintFile(file) {
  const xml = fs.readFileSync(file, 'utf-8');
  const t0 = process.hrtime.bigint();
  const moddle = new DmnModdle();
  const out = { file, findings: [] };
  let root, warnings = [];
  try {
    const r = await moddle.fromXML(xml);
    root = r.rootElement;
    warnings = r.warnings || [];
  } catch (e) {
    out.parse_error = String(e.message || e);
    out.findings.push({ rule: '', category: 'error', message: 'Parse error: ' + out.parse_error });
    out.ms = Number(process.hrtime.bigint() - t0) / 1e6;
    return out;
  }
  out.root_type = root && root.$type;
  out.import_warning_count = warnings.length;
  for (const w of warnings) {
    out.findings.push({
      rule: '(import)', category: 'error', id: w.element && w.element.id,
      message: 'Import warning: ' + String(w.message).split(/\n/)[0]
    });
  }
  const linter = new Linter({ config: { extends: 'dmnlint:all' }, resolver: new NodeResolver() });
  const reports = await linter.lint(root);
  for (const [rule, list] of Object.entries(reports)) {
    for (const r of list) out.findings.push({ rule, category: r.category, id: r.id, message: r.message });
  }
  out.ms = Number(process.hrtime.bigint() - t0) / 1e6;
  return out;
}

(async () => {
  const results = [];
  for (const f of process.argv.slice(2)) results.push(await lintFile(path.resolve(f)));
  console.log(JSON.stringify({
    tool: 'dmnlint', version: dmnlintVersion, dmn_moddle: moddleVersion,
    rules_in_all_config: Object.keys(allConfig.rules), results
  }, null, 1));
})();
