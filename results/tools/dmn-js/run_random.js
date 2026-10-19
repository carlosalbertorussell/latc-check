'use strict';
// Runs harness.js (unchanged) on a list of DMN files and also records the verifier's
// overlap output, which harness.js only counts. One child process per file.
//
// Usage: node run_random.js <dmn-js-repo-dir> <harness-deps-dir> <list.json> <out.jsonl> [concurrency]
//   list.json: [{"id": "...", "file": "path.dmn", "wildcard_empty": false}, ...]
//   out.jsonl: one line per file: harness.js output + {id, wall_s, overlap_groups}
//
// overlap_groups: one entry per "Rules a, b, ... are overlapping" row the verifier renders,
// read by wrapping Verifier.prototype.addOverlappingRuleToTable (records its arguments and
// calls the original). Rule numbers are the verifier's ruleNR (1-based table order).
// Called by compare_random.py.
var path = require('path');
var fs = require('fs');
var cp = require('child_process');
var Module = require('module');

var harnessPath = path.join(__dirname, 'harness.js');

if (process.argv[2] === '--child') {
  var repo = process.argv[3], deps = process.argv[4], file = process.argv[5];
  var groups = [];
  var realLoad = Module._load;
  Module._load = function (request) {
    var m = realLoad.apply(this, arguments);
    if (/verifier[\\/]Verifier(\.js)?$/.test(request) && m && m.prototype && !m.__recorded) {
      var orig = m.prototype.addOverlappingRuleToTable;
      m.prototype.addOverlappingRuleToTable = function (rules, ruleNRs, range, body, sameString) {
        groups.push({ rules: ruleNRs.slice(), outputs_same: /outputs are same/.test(sameString) });
        return orig.apply(this, arguments);
      };
      m.__recorded = true;
    }
    // Diagnostic input shim, only with env WILDCARD_EMPTY=1: dmn-moddle 0.2.3 parses an empty
    // <text></text> as undefined, while the dmn-js 0.5 editor holds an empty ("any") cell as ''.
    // This sets undefined inputEntry texts to '' after parsing, so a file whose wildcard cells are
    // empty reaches the verifier as the editor would hand it over. No analysis code is touched.
    if (process.env.WILDCARD_EMPTY === '1' && /dmn-moddle$/.test(request) && !m.__wildcard) {
      var fromXML = m.prototype.fromXML;
      m.prototype.fromXML = function (xml, type, cb) {
        return fromXML.call(this, xml, type, function (err, defs, ctx) {
          if (!err && defs) {
            (defs.drgElements || defs.drgElement || defs.decision || []).forEach(function (d) {
              var t = d.decisionTable;
              if (!t) { return; }
              (t.rule || []).forEach(function (r) {
                (r.inputEntry || []).forEach(function (e) { if (e.text === undefined) { e.text = ''; } });
              });
            });
          }
          cb(err, defs, ctx);
        });
      };
      m.__wildcard = true;
    }
    return m;
  };
  var write = process.stdout.write.bind(process.stdout);
  process.stdout.write = function (s) {
    try { var o = JSON.parse(String(s)); o.overlap_groups = groups; s = JSON.stringify(o) + '\n'; } catch (e) { /* not the result line */ }
    return write(s);
  };
  process.argv = [process.argv[0], harnessPath, repo, deps, file];
  require(harnessPath);
} else {
  var repoDir = path.resolve(process.argv[2]);
  var depsDir = path.resolve(process.argv[3]);
  var list = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
  var outFile = process.argv[5];
  var conc = parseInt(process.argv[6] || '4', 10);
  var out = fs.openSync(outFile, 'w');
  var next = 0, running = 0, done = 0, t0 = Date.now();
  var launch = function () {
    while (running < conc && next < list.length) {
      (function (job) {
        running++;
        var start = Date.now();
        var child = cp.spawn(process.execPath, [__filename, '--child', repoDir, depsDir, path.resolve(job.file)],
          { env: Object.assign({}, process.env, { RESOLVE_TYPEREF: '0', WILDCARD_EMPTY: job.wildcard_empty ? '1' : '0' }) });
        var so = '', se = '';
        var timer = setTimeout(function () { child.kill(); }, 15 * 60 * 1000);
        child.stdout.on('data', function (d) { so += d; });
        child.stderr.on('data', function (d) { se += d; });
        child.on('close', function (code) {
          clearTimeout(timer);
          var r;
          try { r = JSON.parse(so.trim().split('\n').pop()); } catch (e) {
            r = { outcome: 'error', error: 'exit ' + code + ': ' + se.slice(0, 2000) };
          }
          r.id = job.id; r.wall_s = (Date.now() - start) / 1000;
          fs.writeSync(out, JSON.stringify(r) + '\n');
          running--; done++;
          if (done % 100 === 0 || done === list.length) {
            console.log(done + '/' + list.length + ' files, ' + ((Date.now() - t0) / 1000).toFixed(1) + ' s');
          }
          if (done === list.length) { fs.closeSync(out); } else { launch(); }
        });
      })(list[next++]);
    }
  };
  if (list.length === 0) { fs.closeSync(out); } else { launch(); }
}
