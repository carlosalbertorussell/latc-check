'use strict';
// Runs harness.js on every file in results/tools/inputs/manifest.json (one child
// process per file, 15-minute timeout) and writes results.json next to this script.
// Usage: node run_all.js <dmn-js-repo-dir> <harness-deps-dir> [datasetFilter]
var path = require('path');
var fs = require('fs');
var cp = require('child_process');

var here = __dirname;
var latc = path.resolve(here, '../../..');
var repo = path.resolve(process.argv[2]);
var deps = path.resolve(process.argv[3]);
var filter = process.argv[4] || null;
var manifest = JSON.parse(fs.readFileSync(path.join(latc, 'results/tools/inputs/manifest.json'), 'utf8'));
var outFile = path.join(here, 'results.json');
var prev = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, 'utf8')) : { runs: [] };
var commit = cp.execSync('git -C "' + repo + '" rev-parse HEAD').toString().trim();

var runs = prev.runs.filter(function (r) { return filter && r.dataset !== filter; });
manifest.cases.forEach(function (c) {
  if (filter && c.dataset !== filter) { return; }
  var jobs = [];
  Object.keys(c.files).forEach(function (v) { jobs.push([v, v]); if (v === 'V3b') { jobs.push(['V3b+resolvedTypeRef', v]); } });
  jobs.forEach(function (job) {
    var variant = job[0];
    var f = path.join(latc, c.files[job[1]]);
    var t0 = Date.now();
    var res = cp.spawnSync(process.execPath, [path.join(here, 'harness.js'), repo, deps, f, c.attribute, c.removed_value,
      JSON.stringify(c.declared_domains)], { env: Object.assign({}, process.env, { RESOLVE_TYPEREF: variant === 'V3b+resolvedTypeRef' ? '1' : '0' }), encoding: 'utf8', timeout: 15 * 60 * 1000, maxBuffer: 1 << 28 });
    var r;
    if (res.error || res.status !== 0) {
      r = { file: path.basename(f), outcome: res.error && res.error.code === 'ETIMEDOUT' ? 'timeout (>15 min)' : 'error',
        error: res.error ? String(res.error) : (res.stderr || '').slice(0, 2000) };
    } else {
      r = JSON.parse(res.stdout.trim().split('\n').pop());
    }
    r.dataset = c.dataset; r.case = c.attribute + '=' + c.removed_value; r.variant = variant;
    r.rules = c.rules; r.manifest_missing_states = c.missing_states;
    r.manifest_missing_with_removed_value = c.missing_with_removed_value;
    r.wall_s = (Date.now() - t0) / 1000;
    console.log([r.file, variant, r.outcome, 'regions=' + r.n_gap_regions, 'covered=' + r.states_covered_by_gaps,
      'found=' + r.true_missing_found + '/' + c.missing_states, 'removed=' + r.removed_value_states_found + '/' + c.missing_with_removed_value,
      'wall=' + r.wall_s + 's'].join('  '));
    runs.push(r);
  });
});
fs.writeFileSync(outFile, JSON.stringify({
  tool: 'Laurson & Maggi DMN verifier (ulaurson/dmn-js fork), lib/features/verifier/Verifier.js',
  repo: 'https://github.com/ulaurson/dmn-js', commit: commit,
  node: process.version, harness: 'results/tools/dmn-js/harness.js', runs: runs
}, null, 1));
