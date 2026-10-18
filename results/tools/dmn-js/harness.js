'use strict';
/*
 * Node harness for the Laurson & Maggi (2016) DMN verifier
 * (fork of dmn-js, https://github.com/ulaurson/dmn-js, commit e0b6417,
 *  file lib/features/verifier/Verifier.js), run headless on one DMN file.
 *
 * Usage: node harness.js <dmn-js-repo-dir> <harness-deps-dir> <file.dmn> [removedAttr removedValue declaredDomainsJSON]
 * Prints one JSON object on stdout.
 *
 * Verifier.js is loaded UNCHANGED from the repo. Shims (no analysis logic):
 *  S1 min-dom/lib/{classes,domify,remove} and diagram-js/lib/util/IdGenerator
 *     are replaced by DOM-free stubs (the verifier uses them only to colour
 *     cells and render the result table). The domify stub records the HTML
 *     the verifier renders, which is how the gap rows are read back.
 *  S2 The table-js "sheet" and the "elementRegistry" are replaced by plain
 *     objects that expose exactly what the verifier reads: the body-row linked
 *     list (_lastRow.body / .previous / .businessObject), the column linked list
 *     (_lastColumn.previous / .type / .id, with a trailing annotations column as
 *     dmn-js adds one), elementRegistry.get(columnId).businessObject and
 *     elementRegistry._elements[cellId|ruleId].gfx (inert stub elements).
 *  S3 The DMN 1.4 file is parsed with dmn-moddle 0.2.3 (the version dmn-js 0.5
 *     depends on), which only knows the DMN 1.1 namespace. The harness rewrites
 *     the namespace URI in memory, and renames <allowedValues> to <allowedValue>
 *     (the DMN 1.1 name), so that the parsed business objects carry inputValues
 *     and itemDefinition allowed values exactly as dmn-js 0.5 would hold them.
 *  S4 console.log is silenced during verifyTable (the verifier logs the number
 *     of missing string values on every recursion leaf).
 *  S5 Verifier.prototype.getRulesAndInputs is wrapped on the instance to record
 *     (not change) its return value: the per-input allowedValues the verifier
 *     actually uses for the string gap search.
 */
var path = require('path');
var fs = require('fs');
var Module = require('module');

var repo = path.resolve(process.argv[2]);
var depsDir = path.resolve(process.argv[3]);
var file = path.resolve(process.argv[4]);
var removedAttr = process.argv[5] || null;
var removedValue = process.argv[6] || null;
var declared = process.argv[7] ? JSON.parse(process.argv[7]) : null;

// ---------- S1: DOM-free stubs ----------
var rendered = [];
function stubEl(html) {
  var idm = /id="([^"]+)"/.exec(html || '');
  var el = {
    _html: html, childNodes: [], rows: [],
    getAttribute: function (a) { return a === 'id' && idm ? idm[1] : null; },
    appendChild: function (c) { this.childNodes.push(c); this.rows.push(c); },
    addEventListener: function () {},
    style: {}
  };
  return el;
}
var shims = {
  'min-dom/lib/classes': function () { return { add: function () {}, remove: function () {}, contains: function () { return false; } }; },
  'min-dom/lib/domify': function (html) {
    rendered.push(html);
    var el = stubEl(html);
    if (/id="errorTable"/.test(html)) { el.childNodes = [stubEl('<thead>'), stubEl('<tbody>')]; }
    return el;
  },
  'min-dom/lib/remove': function () {},
  'diagram-js/lib/util/IdGenerator': function (p) { var n = 0; this.next = function () { return p + '_' + (++n); }; }
};
var origLoad = Module._load;
Module._load = function (request) {
  if (Object.prototype.hasOwnProperty.call(shims, request)) { return shims[request]; }
  return origLoad.apply(this, arguments);
};

var Verifier = require(path.join(repo, 'lib/features/verifier/Verifier.js'));
var DmnModdle = require(path.join(depsDir, 'node_modules/dmn-moddle'));

// ---------- S3: parse ----------
var xml = fs.readFileSync(file, 'utf8');
var nsMatch = /xmlns="([^"]+)"/.exec(xml);
xml = xml.split(nsMatch[1]).join('http://www.omg.org/spec/DMN/20151101/dmn11.xsd')
  .replace(/<allowedValues(\s|>)/g, '<allowedValue$1').replace(/<\/allowedValues>/g, '</allowedValue>');

var saved = [console.error, console.warn, console.log]; console.error = console.warn = console.log = function () {}; // parse warnings for DMN 1.4-only elements (inputData, informationRequirement, variable) are counted, not printed
new DmnModdle().fromXML(xml, 'dmn:Definitions', function (err, defs, ctx) {
  console.error = saved[0]; console.warn = saved[1]; console.log = saved[2];
  var out = { file: path.basename(file), parse_warnings: ctx && ctx.warnings ? ctx.warnings.length : 0 };
  if (err) { out.outcome = 'error'; out.error = 'parse: ' + err.message; return finish(out); }
  try { run(defs, out); } catch (e) { out.outcome = 'error'; out.error = e.stack.split('\n').slice(0, 4).join(' | '); }
  finish(out);
});

function finish(out) { process.stdout.write(JSON.stringify(out) + '\n'); }

function unq(s) { s = s.trim(); return (s[0] === '"' && s[s.length - 1] === '"') ? s.slice(1, -1) : s; }

function run(defs, out) {
  var decision = (defs.decision || [])[0];
  var table = decision.decisionTable;
  var inputs = table.input, outputs = table.output, rules = table.rule;

  // what the parsed model makes available to the tool (to show it COULD read it)
  var itemDefs = {};
  (defs.itemDefinition || []).forEach(function (d) {
    var av = Array.isArray(d.allowedValue) ? d.allowedValue[0] : d.allowedValue;
    itemDefs[d.name] = av ? av.text : null;
  });
  out.model_exposes = inputs.map(function (ic) {
    return { label: ic.label, typeRef: ic.inputExpression.typeRef,
      inputValues: ic.inputValues ? ic.inputValues.text : null,
      itemDefinition_allowedValues: itemDefs[ic.inputExpression.typeRef] || null };
  });

  // S6 (diagnostic only, env RESOLVE_TYPEREF=1): replace an inputExpression typeRef that names an
  // itemDefinition by that itemDefinition's base typeRef, so the verifier sees "string".
  // This changes only the input handed to the tool; it is reported as a separate pseudo-variant.
  if (process.env.RESOLVE_TYPEREF === '1') {
    var base = {}; (defs.itemDefinition || []).forEach(function (d) { base[d.name] = d.typeRef; });
    inputs.forEach(function (ic) { var t = ic.inputExpression.typeRef; if (base[t]) { ic.inputExpression.typeRef = base[t]; } });
    out.typeRef_resolved_by_harness = true;
  }

  // ---------- S2: sheet + elementRegistry stand-ins ----------
  var elements = {};
  var colList = inputs.concat(outputs);
  var prev = null;
  colList.forEach(function (c) {
    var node = { id: c.id, type: c.$type, businessObject: c, previous: prev };
    elements[c.id] = { businessObject: c, gfx: stubEl() };
    prev = node;
  });
  var lastColumn = { id: 'annotations', isAnnotationsColumn: true, previous: prev };
  var rprev = null;
  rules.forEach(function (r) {
    rprev = { id: r.id, businessObject: r, previous: rprev };
    elements[r.id] = { businessObject: r, gfx: stubEl() };
    colList.forEach(function (c) { elements['cell_' + c.id + '_' + r.id] = { gfx: stubEl() }; });
  });
  var container = stubEl('<div id="container">');
  var sheet = { _lastRow: { body: rprev }, _lastColumn: lastColumn, getContainer: function () { return container; } };
  var elementRegistry = { _elements: elements, get: function (id) { return elements[id]; } };

  var v = new Verifier(elementRegistry, {}, sheet);

  // S5: record the domain the tool uses
  var usedDomains = null;
  var origGRI = v.getRulesAndInputs;
  v.getRulesAndInputs = function () {
    var res = origGRI.apply(this, arguments);
    usedDomains = {};
    Object.keys(res[0]).forEach(function (cid) {
      var ic = elements[cid].businessObject;
      usedDomains[ic.label] = res[0][cid].allowedValues ? res[0][cid].allowedValues.map(unq) : null;
    });
    return res;
  };

  // S4
  var log = console.log; console.log = function () {};
  var t0 = process.hrtime.bigint();
  try { v.verifyTable(); } finally { console.log = log; }
  out.runtime_s = Number(process.hrtime.bigint() - t0) / 1e9;

  out.input_types_seen_by_tool = inputs.map(function (ic) { return ic.inputExpression.typeRef; });
  out.tool_domains = usedDomains;
  var syntaxErr = usedDomains === null;

  // read back rendered gap rows
  var gapRows = rendered.filter(function (h) { return /No rule exists for/.test(h); });
  var gaps = gapRows.map(function (h) {
    var m = /data-missing_rules= '(.*)'value="Add missing rule"/.exec(h);
    return JSON.parse(m[1]).ruleValue;
  });
  out.overlap_rows = rendered.filter(function (h) { return /are overlapping/.test(h); }).length;
  out.gap_regions = gaps;
  out.n_gap_regions = gaps.length;
  out.outcome = syntaxErr ? 'error (verifier flagged syntax errors, analysis skipped)' : (gaps.length ? 'gaps reported' : 'no gaps');

  // ---------- evaluation (outside the tool) ----------
  var labels = inputs.map(function (ic) { return ic.label; });
  var stringTyped = out.input_types_seen_by_tool.every(function (t) { return t === 'string'; });
  out.all_inputs_typed_string_for_tool = stringTyped;
  var ruleKeys = new Set(rules.map(function (r) { return r.inputEntry.map(function (e) { return unq(e.text); }).join('|'); }));

  if (gaps.length && stringTyped && usedDomains) {
    var covered = new Set();
    gaps.forEach(function (g) {
      var sets = g.map(function (cell, i) {
        if (cell === 'any') { return usedDomains[labels[i]]; }
        return String(cell).replace(/[\[\]]/g, '').split(',').map(unq);
      });
      (function rec(i, acc) {
        if (i === sets.length) { covered.add(acc.join('|')); return; }
        sets[i].forEach(function (x) { rec(i + 1, acc.concat([x])); });
      })(0, []);
    });
    out.states_covered_by_gaps = covered.size;
    out.covered_states_that_match_a_rule = Array.from(covered).filter(function (k) { return ruleKeys.has(k); }).length;
    if (declared) {
      var ai = labels.indexOf(removedAttr);
      var trueMissing = [];
      (function rec(i, acc) {
        if (i === labels.length) { var k = acc.join('|'); if (!ruleKeys.has(k)) { trueMissing.push(acc.slice()); } return; }
        declared[labels[i]].forEach(function (x) { rec(i + 1, acc.concat([x])); });
      })(0, []);
      out.true_missing_states = trueMissing.length;
      out.true_missing_with_removed_value = trueMissing.filter(function (s) { return s[ai] === removedValue; }).length;
      out.true_missing_found = trueMissing.filter(function (s) { return covered.has(s.join('|')); }).length;
      out.removed_value_states_found = trueMissing.filter(function (s) { return s[ai] === removedValue && covered.has(s.join('|')); }).length;
      // alternative, generous reading: an 'any' cell read over the DECLARED domain
      var coveredDecl = new Set();
      gaps.forEach(function (g) {
        var sets = g.map(function (cell, i) { return cell === 'any' ? declared[labels[i]] : String(cell).replace(/[\[\]]/g, '').split(',').map(unq); });
        (function rec(i, acc) { if (i === sets.length) { coveredDecl.add(acc.join('|')); return; } sets[i].forEach(function (x) { rec(i + 1, acc.concat([x])); }); })(0, []);
      });
      out.alt_any_over_declared = { states_covered: coveredDecl.size, true_missing_found: trueMissing.filter(function (s) { return coveredDecl.has(s.join('|')); }).length, removed_value_states_found: trueMissing.filter(function (s) { return s[ai] === removedValue && coveredDecl.has(s.join('|')); }).length };
    }
  } else if (gaps.length) {
    out.note = 'gap regions not interpretable as string states (tool did not treat all inputs as string)';
  } else if (declared) {
    out.states_covered_by_gaps = 0; out.true_missing_found = 0; out.removed_value_states_found = 0;
  }
  out.tool_domain_contains_removed_value = usedDomains && usedDomains[removedAttr] ? usedDomains[removedAttr].indexOf(removedValue) > -1 : null;
}
