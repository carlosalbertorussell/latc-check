// Harness: runs the Corea/Blatt DMN verifier (Quarkus REST backend, commit 5b307e84)
// on the shared LATC inputs and scores its Missing Rules / Missing Predefined Value /
// Unused Predefined Value output against ground truth computed from the declared domains.
//
// Usage: node run.mjs [--port 18091] [--only <substring>] [--timeout-s 900]
// The backend must already be running (see SUMMARY.md). Inputs are read, never modified;
// adapted copies (DMN 1.3 namespace + output typeRef="string") are written to ./adapted/.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..', '..', '..');
const INPUTS = path.join(REPO, 'results', 'tools', 'inputs');
const ADAPTED = path.join(HERE, 'adapted');
const RESULTS = path.join(HERE, 'results.json');

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const PORT = opt('--port', '18091');
const ONLY = opt('--only', '');
const TIMEOUT_S = Number(opt('--timeout-s', '900'));
const VERIFIERS = ['MissingRulesVerification', 'MissingPredefinedValueVerification', 'UnusedPredefinedValueVerification'];
const URL_ = `http://localhost:${PORT}/api/dmn/verification/types?` + VERIFIERS.map(v => 'typeName=' + v).join('&');

const unesc = s => s.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
const quoted = s => [...s.matchAll(/"([^"]*)"/g)].map(m => m[1]);

function parseDmn(xml) {
  const inputs = [...xml.matchAll(/<input\s[^>]*?label="([^"]*)"[^>]*>([\s\S]*?)<\/input>/g)].map(m => {
    const body = m[2];
    const typeRef = (body.match(/<inputExpression[^>]*typeRef="([^"]*)"/) || [])[1] || null;
    const iv = body.match(/<inputValues[^>]*>\s*<text>([\s\S]*?)<\/text>/);
    return { label: unesc(m[1]), typeRef, inputValues: iv ? quoted(unesc(iv[1])) : null };
  });
  const rules = [...xml.matchAll(/<rule\s[^>]*>([\s\S]*?)<\/rule>/g)].map(m =>
    [...m[1].matchAll(/<inputEntry[^>]*>\s*<text>([\s\S]*?)<\/text>/g)].map(e => unesc(e[1]).trim()));
  const itemDefs = [...xml.matchAll(/<itemDefinition\s[^>]*name="([^"]*)"/g)].map(m => m[1]);
  return { inputs, rules, itemDefs };
}

function adapt(xml) {
  return xml
    .replace('https://www.omg.org/spec/DMN/20211108/MODEL/', 'https://www.omg.org/spec/DMN/20191111/MODEL/')
    .replace(/<output\s(?![^>]*typeRef)([^>]*?)(\/?)>/g, '<output $1 typeRef="string"$2>');
}

// Reported missing rule "{ "F" / not("D","I") / - / - }" -> list of matchers per column
function parseMissing(msg) {
  const m = msg.match(/\{ (.*) \}$/);
  if (!m) return null;
  return m[1].split(' / ').map(c => {
    c = c.trim();
    if (c === '-') return { any: true };
    if (/^not\(/i.test(c)) return { not: new Set(quoted(c)) };
    return { in: new Set(quoted(c)) };
  });
}
const matches = (mr, st) => mr.every((c, i) => c.any || (c.not ? !c.not.has(st[i]) : c.in.has(st[i])));

function product(doms) {
  let out = [[]];
  for (const d of doms) out = out.flatMap(p => d.map(v => [...p, v]));
  return out;
}

async function post(file, xml) {
  const t0 = Date.now();
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_S * 1000);
  try {
    const r = await fetch(URL_, { method: 'POST', headers: { 'Content-Type': 'text/xml' }, body: xml, signal: ctl.signal });
    const text = await r.text();
    return { status: r.status, text, ms: Date.now() - t0 };
  } catch (e) {
    return { status: null, error: String(e.name === 'AbortError' ? `timeout after ${TIMEOUT_S}s` : e), ms: Date.now() - t0 };
  } finally { clearTimeout(timer); }
}

const manifest = JSON.parse(fs.readFileSync(path.join(INPUTS, 'manifest.json'), 'utf8'));
fs.mkdirSync(ADAPTED, { recursive: true });
const results = fs.existsSync(RESULTS) ? JSON.parse(fs.readFileSync(RESULTS, 'utf8')) : { runs: [] };
const keep = r => !results.runs.some(x => x.file === r.file && x.mode === r.mode);

for (const c of manifest.cases) {
  const attrs = c.attributes;
  const doms = attrs.map(a => c.declared_domains[a]);
  const ri = attrs.indexOf(c.attribute);
  for (const [variant, rel] of Object.entries(c.files)) {
    const file = path.basename(rel);
    if (ONLY && !file.includes(ONLY)) continue;
    const orig = fs.readFileSync(path.join(REPO, rel), 'utf8');
    const dmn = parseDmn(orig);
    // ground truth on the declared product
    const covered = new Set(dmn.rules.map(r => quoted(r.join(',')).length === r.length ? r.map(x => quoted(x)[0]).join('\u0001') : null));
    const states = product(doms);
    const missing = states.filter(s => !covered.has(s.join('\u0001')));
    const missingRemoved = missing.filter(s => s[ri] === c.removed_value);
    const declaration = dmn.inputs.every(i => i.typeRef === 'string') ? (dmn.inputs.some(i => i.inputValues) ? 'inputValues' : 'none') : `itemDefinition typeRef (${dmn.itemDefs.length} itemDefinitions)`;

    for (const mode of ['original', 'adapted']) {
      const xml = mode === 'original' ? orig : adapt(orig);
      if (mode === 'adapted') fs.writeFileSync(path.join(ADAPTED, file), xml);
      process.stdout.write(`${file} [${mode}] ... `);
      const res = await post(file, xml);
      const run = { file, mode, dataset: c.dataset, variant, removed_value: c.removed_value, attribute: c.attribute,
        rules: dmn.rules.length, declaration_in_file: declaration,
        gt_missing_states: missing.length, gt_missing_with_removed_value: missingRemoved.length,
        manifest_missing_states: c.missing_states, manifest_missing_with_removed_value: c.missing_with_removed_value,
        http_status: res.status, wall_ms: res.ms };
      if (res.status !== 202) {
        run.outcome = 'error';
        run.error = res.error || (res.text || '').slice(0, 300);
      } else {
        const body = JSON.parse(res.text);
        const byName = Object.fromEntries(body.verifier.map(v => [v.type.name, v]));
        const mr = byName.MissingRulesVerification;
        const mpv = byName.MissingPredefinedValueVerification;
        const upv = byName.UnusedPredefinedValueVerification;
        const msgs = mr ? mr.entries.map(e => e.message) : [];
        const parsed = msgs.map(parseMissing).filter(Boolean);
        const coversState = s => parsed.some(p => matches(p, s));
        const missCovered = missing.filter(coversState);
        const nonMissingCovered = states.filter(s => covered.has(s.join('\u0001')) && coversState(s)).length;
        const outOfDomainOnly = parsed.filter(p => !states.some(s => matches(p, s))).length;
        const withNot = parsed.filter(p => p.some(x => x.not)).length;
        const inputLabels = new Set(dmn.inputs.map(i => i.label));
        const upvMsgs = upv ? upv.entries.map(e => e.message) : [];
        const upvInput = upvMsgs.filter(m => [...inputLabels].some(l => m.includes(`Column "${l}"`)));
        const mpvMsgs = mpv ? mpv.entries.map(e => e.message) : [];
        const mpvInput = mpvMsgs.filter(m => [...inputLabels].some(l => m.includes(`Column "${l}"`)));
        Object.assign(run, {
          outcome: msgs.length ? 'missing rules reported' : 'none',
          missing_rules_reported: msgs.length,
          missing_rules_with_not: withNot,
          missing_rules_out_of_domain_only: outOfDomainOnly,
          missing_states_covered: missCovered.length,
          removed_value_states_covered: missingRemoved.filter(coversState).length,
          declared_nonmissing_states_covered: nonMissingCovered,
          missing_rules_sample: msgs.slice(0, 6).map(m => m.replace(/^Decision "[^"]*": /, '')),
          missing_rules_all_sorted: msgs.length <= 300 ? msgs.map(m => m.replace(/^Decision "[^"]*": /, '')).sort() : undefined,
          missing_predefined_value_warnings: mpvMsgs.length,
          missing_predefined_value_input_warnings: mpvInput.length,
          missing_predefined_value_sample: mpvMsgs.slice(0, 3),
          unused_predefined_value_warnings: upvMsgs.length,
          unused_predefined_value_input_messages: upvInput,
          unused_pv_names_removed_value: upvInput.some(m => m.includes(`Column "${c.attribute}"`) && m.includes(`"${c.removed_value}"`)),
          verifier_execution_time: Object.fromEntries(body.verifier.map(v => [v.type.name, v.executionTime])),
        });
      }
      console.log(run.outcome, run.wall_ms + 'ms', run.missing_rules_reported ?? '', run.error ? run.error.slice(0, 80) : '');
      results.runs = results.runs.filter(x => !(x.file === file && x.mode === mode));
      results.runs.push(run);
      results.tool = { name: 'DMN verification tool (Corea, Blatt, Delfmann; Blatt MSc thesis)',
        source: 'https://gitlab.uni-koblenz.de/jonasblatt/ma-jonasblatt-dmn-verifier', commit: '5b307e8481170d37b63a9b256a45c3c38c7fa50c',
        endpoint: URL_.replace(PORT, '<port>'), verifiers: VERIFIERS };
      fs.writeFileSync(RESULTS, JSON.stringify(results, null, 1));
    }
  }
}
