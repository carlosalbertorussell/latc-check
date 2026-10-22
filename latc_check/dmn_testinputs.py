"""Do the test cases shipped with public DMN models feed a string value that no rule mentions?

Follow-up to ``dmn_corpus``: the observed-domain trap needs a value
that no rule of an undeclared string column mentions.  This module looks for
such values in the test inputs that ship with the models.

Formats
-------
* **DMN TCK test cases** (``*-test-*.xml`` with ``<testCases>`` / ``<testCase>``
  / ``<inputNode name=...><value>``, namespace
  ``http://www.omg.org/spec/DMN/20160719/testcase``).  The model is the
  ``<modelName>`` file in the same folder.  Implemented.
* Other formats (Drools / KIE ``.scesim`` scenarios, Camunda / Operaton /
  jDMN JSON or YAML fixtures, Java or JavaScript unit tests building
  variable maps in code) are **not parsed**: the corpus clones are sparse,
  blob-less clones holding ``.dmn`` files only, so their contents are not on
  disk, and reading them would mean downloading.  ``inventory`` counts them
  from the local git trees (names only) so the size of what is skipped is
  known.  Unit tests in code are skipped in any case: the link from a value
  to a model and input would need the host language evaluated.

Resolution
----------
For one test case, the decisions evaluated are the result nodes (decisions,
or a decision service's output and encapsulated decisions) and every decision
they require, transitively (``informationRequirement/requiredDecision``).
When no result node names a decision of the model, every decision counts
(``closure = "all"``).  A decision table owned by one of these decisions has
its input expressions (``A`` or ``A.b.c``) matched to the test case's input
nodes (longest dotted prefix naming an input node, the rest followed through
``<component>`` values).  A table owned by a business knowledge model is
reached when the test invokes the BKM directly (``type="bkm"``), or when an
evaluated decision invokes it with a parameter bound to a plain input name
(``<invocation>`` bindings, or a FEEL call ``BKM name(a, b)`` whose
arguments are plain names); other tables and expressions are not resolved.

Checks
------
For every (test value, table column) link where the column is a string input
of ``dmn_corpus`` (``base == "string"``) whose entries mention at least one
string literal, the value is *unmentioned* when it is a string and no entry
of the column mentions it (exact match against the decoded literals of
``dmn_corpus.entry_info``; ``not(...)`` lists and literals quoted inside
expressions count as mentions, as in ``dmn_corpus``).  For an unmentioned
value the column says whether a rule can still match it:

* ``wildcard``: some entry is ``-`` or empty;
* ``not``: no wildcard, a ``not(...)`` entry admits it;
* ``unknown``: no wildcard or ``not``, some entry is a FEEL expression;
* ``no_match``: every entry is a literal list and none admits it, so no rule
  of the table matches (no result; the default output when one is declared).

Instances are flagged *deliberate-looking* when the test file name, test case
id / name / description contain ``no match``, ``missing``, ``default``,
``null``, ``invalid`` and similar words, and separately when a result node of
the test case expects null.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

from . import dmn_corpus as dc
from .dmn_import import split_top, Unsupported

TC_NS = "http://www.omg.org/spec/DMN/20160719/testcase"
XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
TCK_TEST_RE = re.compile(r"-test-\d+\.xml$", re.I)
DELIBERATE_RE = re.compile(r"no[\s_-]?match|missing|default|null|invalid|unknown|not[\s_-]?found|"
                           r"no[\s_-]?rule|unmatched|unexpected|illegal|wrong", re.I)
KINDS = dc.KINDS


# -- TCK test files -----------------------------------------------------------------

def _value_tree(el):
    """Value of an inputNode / component / item: a small tree.

    {"t": xsd type (local part) | "untyped" | "null", "v": text} for a leaf,
    {"t": "struct", "c": {name: tree}} or {"t": "list", "items": [tree]}."""
    comps = dc._children(el, "component")
    if comps:
        return {"t": "struct", "c": {c.get("name"): _value_tree(c) for c in comps}}
    lst = dc._child(el, "list")
    if lst is not None:
        return {"t": "list", "items": [_value_tree(i) for i in dc._children(lst, "item")]}
    v = dc._child(el, "value")
    if v is None:
        if el.get(XSI + "nil") == "true":
            return {"t": "null"}
        if dc._local(el.tag)[1] == "value":
            v = el
        else:
            return {"t": "null"}
    if v.get(XSI + "nil") == "true":
        return {"t": "null"}
    if dc._children(v, "component") or dc._child(v, "list") is not None:
        return _value_tree(v)
    xt = v.get(XSI + "type")
    t = xt.split(":", 1)[-1] if xt else "untyped"
    return {"t": t, "v": v.text if v.text is not None else ""}


def parse_tck_tests(data: bytes):
    """Parse a TCK test file.  None when it is not one."""
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        return None
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return None
    ns, local = dc._local(root.tag)
    if local != "testCases":
        return None
    mn = dc._child(root, "modelName")
    labels = dc._child(root, "labels")
    out = {"model_name": (mn.text or "").strip() if mn is not None else None,
           "labels": [(x.text or "").strip() for x in dc._children(labels, "label")] if labels is not None else [],
           "cases": []}
    for tc in dc._children(root, "testCase"):
        desc = dc._child(tc, "description")
        case = {"id": tc.get("id"), "name": tc.get("name"), "type": tc.get("type") or "decision",
                "invocable": tc.get("invocableName"),
                "description": (desc.text or "").strip() if desc is not None else None,
                "inputs": [], "results": []}
        for inp in dc._children(tc, "inputNode"):
            case["inputs"].append({"name": (inp.get("name") or "").strip(), "value": _value_tree(inp)})
        for rn in dc._children(tc, "resultNode"):
            exp = dc._child(rn, "expected")
            ev = _value_tree(exp) if exp is not None else None
            case["results"].append({"name": (rn.get("name") or "").strip(), "type": rn.get("type"),
                                    "expected": ev})
        out["cases"].append(case)
    return out


def is_null_tree(t):
    return t is None or t.get("t") == "null"


# -- model graph ----------------------------------------------------------------------

def _href_id(el):
    h = (el.get("href") or "").strip()
    if "#" in h:
        pre, _, i = h.partition("#")
        return i, bool(pre)
    return h, False


def model_graph(data: bytes):
    """Decisions, BKMs, decision services and tables of one model, for resolution.

    Tables are numbered as in ``dc.analyse_bytes`` (document order)."""
    root = ET.fromstring(data)
    parents = {c: p for p in root.iter() for c in p}
    g = {"decisions": {}, "bkms": {}, "services": {}, "ids": {}, "tables": [], "imports": 0}
    for el in root:
        _, l = dc._local(el.tag)
        name, eid = (el.get("name") or "").strip(), el.get("id")
        if l == "import":
            g["imports"] += 1
        if l == "decision":
            req, kreq = [], []
            for ir in dc._children(el, "informationRequirement"):
                rd = dc._child(ir, "requiredDecision")
                if rd is not None:
                    i, ext = _href_id(rd)
                    if not ext:
                        req.append(i)
            for kr in dc._children(el, "knowledgeRequirement"):
                rk = dc._child(kr, "requiredKnowledge")
                if rk is not None:
                    i, ext = _href_id(rk)
                    if not ext:
                        kreq.append(i)
            g["decisions"][name] = {"id": eid, "el": el, "requires": req, "knowledge": kreq}
            g["ids"][eid] = ("decision", name)
        elif l == "businessKnowledgeModel":
            params = []
            enc = dc._child(el, "encapsulatedLogic")
            if enc is not None:
                params = [(p.get("name") or "").strip() for p in dc._children(enc, "formalParameter")]
            g["bkms"][name] = {"id": eid, "params": params}
            g["ids"][eid] = ("bkm", name)
        elif l == "decisionService":
            refs = []
            for part in ("outputDecision", "encapsulatedDecision"):
                for r in dc._children(el, part):
                    i, ext = _href_id(r)
                    if not ext:
                        refs.append(i)
            g["services"][name] = {"id": eid, "decisions": refs}
    for ti, dt in enumerate(el for el in root.iter() if dc._local(el.tag)[1] == "decisionTable"):
        owner = parents.get(dt)
        while owner is not None and dc._local(owner.tag)[1] not in ("decision", "businessKnowledgeModel"):
            owner = parents.get(owner)
        okind = "none" if owner is None else ("decision" if dc._local(owner.tag)[1] == "decision" else "bkm")
        oname = (owner.get("name") or "").strip() if owner is not None else None
        inputs = dc._children(dt, "input")
        cols = [[] for _ in inputs]
        for r in dc._children(dt, "rule"):
            for k, ie in enumerate(dc._children(r, "inputEntry")):
                if k < len(cols):
                    t = dc._child(ie, "text")
                    cols[k].append("".join(t.itertext()) if t is not None else "")
        exprs = []
        for inp in inputs:
            ie = dc._child(inp, "inputExpression")
            t = dc._child(ie, "text") if ie is not None else None
            exprs.append(("".join(t.itertext()) if t is not None else "").strip())
        default = any(dc._child(o, "defaultOutputEntry") is not None for o in dc._children(dt, "output"))
        g["tables"].append({"index": ti, "owner_kind": okind, "owner": oname, "exprs": exprs,
                            "entries": [[dc.entry_info(x) for x in c] for c in cols],
                            "default_output": default})
    return g


def decision_closure(g, case):
    """Names of the decisions a test case evaluates, and how the set was found."""
    start = []
    names = [r["name"] for r in case["results"]]
    if case.get("invocable"):
        names.append(case["invocable"])
    for n in names:
        if n in g["decisions"]:
            start.append(n)
        elif n in g["services"]:
            start += [g["ids"][i][1] for i in g["services"][n]["decisions"]
                      if g["ids"].get(i, ("", ""))[0] == "decision"]
    if not start:
        return set(g["decisions"]), "all"
    seen, todo = set(), list(start)
    while todo:
        n = todo.pop()
        if n in seen or n not in g["decisions"]:
            continue
        seen.add(n)
        for i in g["decisions"][n]["requires"]:
            k = g["ids"].get(i)
            if k and k[0] == "decision":
                todo.append(k[1])
    return seen, "requirements"


def _split_path(expr):
    return [p.strip() for p in expr.split(".")]


def lookup(expr, scope):
    """Follow ``expr`` (``A`` or ``A.b.c``) into ``scope`` {name: value tree}.

    Returns (input name, path, tree) or None when no prefix names a scope entry.
    The tree is None when the path leaves the value (absent component)."""
    if not expr:
        return None
    parts = _split_path(expr)
    for cut in range(len(parts), 0, -1):
        name = ".".join(parts[:cut])
        if name in scope:
            node = scope[name]
            for seg in parts[cut:]:
                if node is None or node.get("t") != "struct":
                    node = None
                    break
                node = node["c"].get(seg)
            return name, parts[cut:], node
    return None


_NAME_RE = re.compile(r"^[^\s\"(),\[\]{}+*/<>=!-][^\"(),\[\]{}+*/<>=!]*$")


def bkm_bindings(g, closure, scope):
    """{bkm name: {param: lookup result (input name, path, tree)}} for BKMs invoked by the closure's decisions with
    parameters bound to plain input names (or paths into them)."""
    out = defaultdict(dict)
    for dname in closure:
        del_ = g["decisions"][dname]["el"]
        for inv in (e for e in del_.iter() if dc._local(e.tag)[1] == "invocation"):
            callee = dc._child(inv, "literalExpression")
            cname = "".join(dc._child(callee, "text").itertext()).strip() \
                if callee is not None and dc._child(callee, "text") is not None else ""
            if cname not in g["bkms"]:
                continue
            for b in dc._children(inv, "binding"):
                p = dc._child(b, "parameter")
                le = dc._child(b, "literalExpression")
                t = dc._child(le, "text") if le is not None else None
                if p is None or t is None:
                    continue
                hit = lookup("".join(t.itertext()).strip(), scope)
                if hit:
                    out[cname][(p.get("name") or "").strip()] = hit
        texts = ["".join(t.itertext()) for le in del_.iter() if dc._local(le.tag)[1] == "literalExpression"
                 for t in [dc._child(le, "text")] if t is not None]
        for bname, b in g["bkms"].items():
            pat = re.compile(re.escape(bname) + r"\s*\(")
            for txt in texts:
                for m in pat.finditer(txt):
                    depth, k = 1, m.end()
                    while k < len(txt) and depth:
                        depth += {"(": 1, ")": -1}.get(txt[k], 0)
                        k += 1
                    if depth:
                        continue
                    args = txt[m.end():k - 1]
                    try:
                        items = split_top(args) if args.strip() else []
                    except Unsupported:
                        continue
                    for pos, it in enumerate(items):
                        it = it.strip()
                        pname = None
                        if ":" in it:
                            pname, it = (s.strip() for s in it.split(":", 1))
                        elif pos < len(b["params"]):
                            pname = b["params"][pos]
                        if pname is None or not _NAME_RE.match(it):
                            continue
                        hit = lookup(it, scope)
                        if hit:
                            out[bname][pname] = hit
    return out


def column_admits(entries, value):
    """How a column's entries treat a string ``value`` no entry mentions:
    'wildcard' | 'not' | 'unknown' | 'no_match'."""
    kinds = {k for k, _ in entries}
    if "any" in kinds:
        return "wildcard"
    if any(k == "notlits" and value not in vals for k, vals in entries):
        return "not"
    if kinds & {"nonliteral", "numeric"}:
        return "unknown"
    return "no_match"


# -- one test file -------------------------------------------------------------------

def analyse_test_file(test_data: bytes, model_data: bytes, rel="?", model_rel="?"):
    """Links and instances for one TCK test file against its model.

    Returns a dict with counts, ``links`` (one per test value and table column) and
    ``unresolved`` input nodes."""
    tf = parse_tck_tests(test_data)
    res = {"path": rel, "model": model_rel, "error": None, "cases": 0, "input_values": 0,
           "links": [], "unresolved": Counter(), "closure_all": 0}
    if tf is None:
        res["error"] = "not a TCK test file"
        return res
    frec, tables, rows = dc.analyse_bytes(model_data, model_rel)
    if frec["error"]:
        res["error"] = f"model: {frec['error']}"
        return res
    g = model_graph(model_data)
    res["imports"] = g["imports"]
    tmap = {t["table_index"]: t for t in tables}
    rmap = defaultdict(dict)
    for r in rows:
        rmap[r["table_index"]][r["input_index"]] = r
    exposed = {ti: any(dc.exposed_column(r, tmap[ti]) for r in cols.values()) for ti, cols in rmap.items()}
    res["cases"] = len(tf["cases"])
    for case in tf["cases"]:
        scope = {i["name"]: i["value"] for i in case["inputs"]}
        res["input_values"] += len(case["inputs"])
        targets = []                       # (table, scope, origin {param: (input, path)} or None)
        if case["type"] == "bkm" and case.get("invocable") in g["bkms"]:
            targets += [(t, scope, None) for t in g["tables"]
                        if t["owner_kind"] == "bkm" and t["owner"] == case["invocable"]]
        else:
            closure, how = decision_closure(g, case)
            if how == "all":
                res["closure_all"] += 1
            targets += [(t, scope, None) for t in g["tables"]
                        if t["owner_kind"] == "decision" and t["owner"] in closure]
            for bname, bind in bkm_bindings(g, closure, scope).items():
                bscope = {p: h[2] for p, h in bind.items()}
                origin = {p: (h[0], h[1]) for p, h in bind.items()}
                targets += [(t, bscope, origin) for t in g["tables"]
                            if t["owner_kind"] == "bkm" and t["owner"] == bname]
        used = set()
        for t, sc, origin in targets:
            ti = t["index"]
            for k, expr in enumerate(t["exprs"]):
                hit = lookup(expr, sc)
                if not hit:
                    continue
                name, path, tree = hit
                via = None
                if origin is not None:
                    via = f"{t['owner']}({name})"
                    name, path = origin[name][0], origin[name][1] + path
                used.add(name)
                r = rmap[ti].get(k)
                tab = tmap[ti]
                link = {"case": case["id"], "case_name": case.get("name"), "description": case.get("description"),
                        "input": name, "path": path, "via_bkm": via,
                        "table": tab["table"], "table_index": ti, "input_index": k, "column": r["label"],
                        "fingerprint": tab["fingerprint"], "base": r["base"],
                        "string_literal_column": r["base"] == "string" and bool(r["mentioned"]),
                        "declared": r["declared"], "declared_values": r["declared_values"],
                        "single_hit": tab["single_hit"], "hit_policy": tab["hit_policy"],
                        "has_catch_all": tab["has_catch_all"], "exposed_table": exposed.get(ti, False),
                        "exposed_column": dc.exposed_column(r, tab), "default_output": t["default_output"],
                        "value_type": "absent" if tree is None else tree["t"],
                        "value": None if tree is None else tree.get("v"),
                        "expected_null": any(is_null_tree(x["expected"]) for x in case["results"]),
                        "expected": [_short(x["expected"]) for x in case["results"]]}
                link["unmentioned"] = False
                if link["string_literal_column"] and link["value_type"] in ("string", "untyped"):
                    v = link["value"]
                    if v not in r["mentioned"]:
                        link["unmentioned"] = True
                        link["admits"] = column_admits(t["entries"][k], v)
                        low = {m.strip().lower() for m in r["mentioned"]}
                        link["near_mention"] = v.strip().lower() in low
                        if r["declared_values"] is not None:
                            link["in_declared"] = v in r["declared_values"]
                        words = " ".join(x for x in (rel, case["id"], case.get("name"), case.get("description"))
                                         if x)
                        link["deliberate_words"] = sorted({m.group(0).lower() for m in DELIBERATE_RE.finditer(words)})
                res["links"].append(link)
        for i in case["inputs"]:
            if i["name"] not in used:
                res["unresolved"][_why_unresolved(i["name"], g, tables, rows)] += 1
    res["unresolved"] = dict(res["unresolved"])
    return res


def _short(tree):
    if tree is None or tree["t"] == "null":
        return None
    if tree["t"] == "struct":
        return "{" + ", ".join(tree["c"]) + "}"
    if tree["t"] == "list":
        return f"[{len(tree['items'])} items]"
    return tree.get("v")


def _why_unresolved(name, g, tables, rows):
    exprs = {r["expression"] for r in rows}
    if any(lookup(e, {name: None}) for e in exprs):
        return "column outside the evaluated decisions or an unbound BKM"
    if name in g["decisions"]:
        return "decision value supplied as input"
    return "no decision-table column reads it directly"


# -- corpus ---------------------------------------------------------------------------

def find_tck_tests(sources):
    """[(source, rel test path, full test path, full model path or None)] for TCK test files."""
    out = []
    for src in sources:
        base = src["path"]
        for dp, dn, fn in os.walk(base):
            dn[:] = sorted(d for d in dn if d not in (".git", "node_modules"))
            for f in sorted(fn):
                if not TCK_TEST_RE.search(f):
                    continue
                full = os.path.join(dp, f)
                with open(full, "rb") as fh:
                    head = fh.read(4096)
                if b"testCases" not in head:
                    continue
                out.append((src, os.path.relpath(full, base).replace("\\", "/"), full))
    return out


class NoTestFiles(RuntimeError):
    """No TCK test file was found: the results would be empty."""


def no_tests_warning(sources):
    """Message for a run that found no TCK test file (expected pattern and TCK path)."""
    tck = [s["path"] for s in sources if s.get("role") == "tck"]
    where = ", ".join(tck) if tck else "no TCK source (expected ../dmn-tck)"
    return (f"warning: no DMN TCK test files found (expected *-test-NN.xml files holding <testCases>) "
            f"under {where}; the TCK checkout needs the sparse pattern *-test-*.xml "
            f"(python -I fetch_corpus.py adds it). No results written.")


INVENTORY_SKIP = {"package.json", "package-lock.json", "tsconfig.json", "pom.xml", "kmodule.xml",
                  "kie-deployment-descriptor.xml"}


def inventory(path):
    """Counts of candidate test-input files in a clone's git tree (names only; no blob is read).

    ``scesim``: Drools / KIE scenarios; ``tck_xml``: ``*-test-NN.xml``; ``json_yaml_next_to_dmn``:
    JSON / YAML files in a folder that also holds a ``.dmn`` file; ``on_disk``: how many of all
    these are present in the working tree."""
    env = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    try:
        p = subprocess.run(["git", "-C", path, "ls-tree", "-r", "--name-only", "HEAD"], capture_output=True,
                           text=True, timeout=120, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    names = p.stdout.splitlines()
    dmn_dirs = {os.path.dirname(n) for n in names if n.lower().endswith(".dmn")}
    c = Counter()
    for n in names:
        b = os.path.basename(n)
        low = b.lower()
        key = None
        if low.endswith(".scesim"):
            key = "scesim"
        elif TCK_TEST_RE.search(b):
            key = "tck_xml"
        elif low.endswith((".json", ".yaml", ".yml")) and b not in INVENTORY_SKIP \
                and os.path.dirname(n) in dmn_dirs:
            key = "json_yaml_next_to_dmn"
        if key:
            c[key] += 1
            if os.path.exists(os.path.join(path, n)):
                c["on_disk"] += 1
    return dict(c)


def _pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def summarise(links, files):
    """Counts per kind, by test files (every link) and by distinct table contents
    ((table fingerprint, column, value) once)."""
    out = {}
    for g in ("all",) + KINDS:
        L = [x for x in links if g == "all" or x["kind"] == g]
        F = [f for f in files if g == "all" or f["kind"] == g]
        if not F:
            continue
        s = {"test_files": len(F), "test_cases": sum(f["cases"] for f in F),
             "input_values": sum(f["input_values"] for f in F)}
        res_vals = {(x["test_file"], x["case"], x["input"], tuple(x["path"])) for x in L}
        s["input_values_resolved"] = len({(a, b, c) for a, b, c, _ in res_vals})
        s["links"] = len(L)
        sl = [x for x in L if x["string_literal_column"]]
        s["links_string_literal_column"] = len(sl)
        s["links_string_value"] = sum(1 for x in sl if x["value_type"] in ("string", "untyped"))
        um = [x for x in sl if x["unmentioned"]]
        s["unmentioned"] = len(um)
        s["unmentioned_by_admits"] = dict(Counter(x["admits"] for x in um))
        s["unmentioned_no_match"] = sum(1 for x in um if x["admits"] == "no_match")
        s["unmentioned_no_match_single_hit"] = sum(1 for x in um if x["admits"] == "no_match" and x["single_hit"])
        s["unmentioned_undeclared"] = sum(1 for x in um if not x["declared"])
        s["unmentioned_exposed_column"] = sum(1 for x in um if x["exposed_column"])
        s["links_exposed_column"] = sum(1 for x in L if x["exposed_column"])
        s["cases_expecting_null"] = len({(x["test_file"], x["case"]) for x in L if x["expected_null"]})
        s["null_into_string_column"] = sum(1 for x in sl if x["value_type"] in ("null", "absent"))
        # distinct contents
        key = lambda x: (x["fingerprint"], x["input_index"], x["value_type"], x["value"])  # noqa: E731
        s["distinct_links"] = len({key(x) for x in L})
        s["distinct_links_string_value"] = len({key(x) for x in sl if x["value_type"] in ("string", "untyped")})
        s["distinct_unmentioned"] = len({key(x) for x in um})
        s["distinct_unmentioned_no_match"] = len({key(x) for x in um if x["admits"] == "no_match"})
        s["distinct_tables_linked"] = len({x["fingerprint"] for x in L})
        s["distinct_tables_string_value"] = len({x["fingerprint"] for x in sl
                                                 if x["value_type"] in ("string", "untyped")})
        s["distinct_tables_unmentioned"] = len({x["fingerprint"] for x in um})
        s["distinct_tables_no_match"] = len({x["fingerprint"] for x in um if x["admits"] == "no_match"})
        s["unmentioned_pct_of_string_values"] = _pct(s["unmentioned"], s["links_string_value"])
        s["distinct_unmentioned_pct"] = _pct(s["distinct_unmentioned"], s["distinct_links_string_value"])
        out[g] = s
    return out


def run(sources, out_dir):
    tests = find_tck_tests(sources)
    if not tests:
        raise NoTestFiles(no_tests_warning(sources))
    files, links, seen = [], [], {}
    for src, rel, full in tests:
        with open(full, "rb") as fh:
            data = fh.read()
        h = hashlib.sha256(data).hexdigest()
        if h in seen:
            seen[h]["copies"] += 1
            continue
        tf = parse_tck_tests(data)
        model_rel = None
        mpath = None
        if tf and tf["model_name"]:
            mpath = os.path.join(os.path.dirname(full), tf["model_name"])
            model_rel = os.path.relpath(mpath, src["path"]).replace("\\", "/")
        kind = dc.classify(src, rel)
        if mpath is None or not os.path.isfile(mpath):
            rec = {"source": src["name"], "path": rel, "model": model_rel, "kind": kind, "sha256": h,
                   "copies": 1, "error": "model file not found", "cases": len(tf["cases"]) if tf else 0,
                   "input_values": sum(len(c["inputs"]) for c in tf["cases"]) if tf else 0,
                   "unresolved": {}, "links": 0}
            files.append(rec)
            seen[h] = rec
            continue
        with open(mpath, "rb") as fh:
            mdata = fh.read()
        r = analyse_test_file(data, mdata, rel, model_rel)
        rec = {"source": src["name"], "path": rel, "model": model_rel, "kind": kind, "sha256": h, "copies": 1,
               "model_sha256": hashlib.sha256(mdata).hexdigest(), "error": r["error"], "cases": r["cases"],
               "input_values": r["input_values"], "unresolved": r["unresolved"], "links": len(r["links"]),
               "closure_all": r["closure_all"], "imports": r.get("imports", 0)}
        files.append(rec)
        seen[h] = rec
        for x in r["links"]:
            x.update(source=src["name"], kind=kind, test_file=rel, model=model_rel)
            links.append(x)
    inv = {}
    for src in sources:
        if src.get("role") == "tck":
            continue
        inv[src["name"]] = inventory(src["path"])
    instances = [x for x in links if x["unmentioned"]]
    res = {"summary": summarise(links, files),
           "unresolved_input_values": dict(sum((Counter(f["unresolved"]) for f in files), Counter())),
           "inventory_other_formats": inv,
           "inventory_totals": dict(sum((Counter(v) for v in inv.values() if v), Counter())),
           "files": files, "instances": instances, "links": links}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "testinputs.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(out_dir, "TESTINPUTS.md"), "w", encoding="utf-8") as fh:
        fh.write(summary_md(res, sources))
    return res


# -- report ---------------------------------------------------------------------------

def _row(label, kind, v):
    return (f"| {label} | {dc.KIND_LABEL[kind]} | {v['test_files']} | {v['test_cases']} | {v['input_values']} "
            f"| {v['input_values_resolved']} | {v['links']} | {v['links_string_value']} "
            f"| {v['unmentioned']} | {v['unmentioned_no_match']} |")


def summary_md(res, sources):
    S = res["summary"]
    a = S.get("all", {})
    L = ["# Test inputs that no rule mentions", "",
         "Generated by `run_dmn_testinputs.py` (`latc_check/dmn_testinputs.py`). Question: do the test cases "
         "shipped with public DMN models feed a decision table a string value that no rule entry of the column "
         "mentions (the value an observed-domain analyser never reports missing)? The corpus and the table "
         "and column measures are those of `SUMMARY.md` (`dmn_corpus.py`), which this survey leaves unchanged.", "",
         "## Formats", "",
         "* **DMN TCK test cases** (`*-test-NN.xml`, `<testCase>` / `<inputNode>`), parsed, with the model named "
         "by `<modelName>` in the same folder. Only the DMN TCK clone holds them on disk.",
         "* **Not parsed**: Drools / KIE `.scesim` scenarios, JSON / YAML fixtures and unit tests written in "
         "code. The other 49 sources are blob-less sparse clones with `.dmn` files only, so these files are "
         "not on disk; reading them would require downloading. Their number, counted from the local git trees "
         "(file names only), is under *Skipped formats*. Unit tests in Java, JavaScript or Scala are skipped in "
         "any case: linking a value to a model input would need the host code evaluated.", "",
         "## Resolution", "",
         "A test case evaluates its result decisions and every decision they require (transitively), or the "
         "output and encapsulated decisions of a tested decision service; when no result node names a decision, "
         "every decision of the model counts. A decision table owned by one of them has each input expression "
         "(`A` or `A.b.c`) matched to the test case's input nodes, components followed for dotted paths. A table "
         "of a business knowledge model is reached when the test invokes the BKM, or an evaluated decision "
         "invokes it with parameters bound to plain input names. A *link* is one (test value, table column) "
         "pair; a *resolved input value* is an input node that feeds at least one column.", "",
         "## Checks", "",
         "For links into a string column whose entries mention at least one string literal (as in `SUMMARY.md`), "
         "a string test value is *unmentioned* when no entry of the column mentions it (exact match against the "
         "decoded literals; `not(...)` lists and literals inside expressions count as mentions). Whether a rule "
         "can still match it: *wildcard* (some entry is `-` or empty), *not* (a `not(...)` entry admits it), "
         "*unknown* (an entry is a FEEL expression), *no match* (every entry is a literal list and none admits "
         "it: no rule of the table matches, the table returns no result or its default output).", "",
         "## Counts by kind", "",
         "Counted by distinct test files (each link once per test case):", "",
         "| count by | kind | test files | test cases | input values | resolved input values | links "
         "| links: string value into a string column with literals | unmentioned | ... no rule can match |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for g, v in S.items():
        L.append(_row("test files", g, v))
    L += ["", "Counted by distinct table contents (each (table content, column, value) once):", "",
          "| kind | distinct tables linked | distinct links | distinct string-value links into string columns "
          "| distinct unmentioned | distinct no-match | tables with an unmentioned value | tables with a no-match value |",
          "|---|---|---|---|---|---|---|---|"]
    for g, v in S.items():
        L.append(f"| {dc.KIND_LABEL[g]} | {v['distinct_tables_linked']} | {v['distinct_links']} "
                 f"| {v['distinct_links_string_value']} | {v['distinct_unmentioned']} "
                 f"| {v['distinct_unmentioned_no_match']} | {v['distinct_tables_unmentioned']} "
                 f"| {v['distinct_tables_no_match']} |")
    kinds_missing = [dc.KIND_LABEL[k] for k in KINDS if k not in S]
    if kinds_missing:
        L += ["", "No test-input files on disk for: " + ", ".join(kinds_missing) + "."]
    if a:
        L += ["", f"Unmentioned values by what the column admits: {json.dumps(a['unmentioned_by_admits'])}. "
              f"Of the {a['unmentioned']} unmentioned links: in undeclared columns {a['unmentioned_undeclared']}, "
              f"in exposed columns (single-hit, undeclared, no "
              f"catch-all rule) {a['unmentioned_exposed_column']}. Null or absent values fed to string columns with literals: "
              f"{a['null_into_string_column']} links (counted separately). Links into an exposed column, any "
              f"value: {a['links_exposed_column']}. Test cases with a resolved link that expect a null result: "
              f"{a['cases_expecting_null']}."]
    L += ["", "## Instances", "",
          "Every link with an unmentioned value (one row per test file, column and value; the test cases are "
          "listed). *Deliberate-looking*: words such as no match, missing, default, null, invalid in the test file "
          "name, test case id, name or description; *expects null*: a result node of the test case expects null.",
          "", "| test file | table | column | value | declared | exposed table | hit policy | rule can match "
          "| default output | test cases | deliberate-looking | expects null |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    groups = defaultdict(list)
    for x in res["instances"]:
        groups[(x["test_file"], x["table"], x["column"], x["value"])].append(x)
    for (tfile, table, col, val), xs in sorted(groups.items()):
        x = xs[0]
        words = sorted({w for y in xs for w in y["deliberate_words"]})
        L.append(f"| `{tfile}` | {table} | {col} | `{val}` | {'yes' if x['declared'] else 'no'} "
                 f"| {'yes' if x['exposed_table'] else 'no'} | {x['hit_policy']} | {x['admits']} "
                 f"| {'yes' if x['default_output'] else 'no'} | {', '.join(sorted({y['case'] for y in xs}))} "
                 f"| {', '.join(words) or '-'} | {'yes' if any(y['expected_null'] for y in xs) else 'no'} |")
    if not res["instances"]:
        L.append("| (none) |||||||||||| ")
    L += ["", "## Unresolved input values", "",
          "Input nodes that feed no decision-table column under the resolution above, by reason: "
          + json.dumps(res["unresolved_input_values"]) + ".", ""]
    errs = [f for f in res["files"] if f["error"]]
    if errs:
        L += ["Test files not analysed: " + "; ".join(f"`{f['path']}` ({f['error']})" for f in errs) + ".", ""]
    nall = sum(f.get("closure_all", 0) for f in res["files"])
    L += [f"Test cases whose result nodes name no decision of the model (every decision counted): {nall}.", ""]
    L += ["## Skipped formats", "",
          "Candidate test-input files in the git trees of the other sources (names only, from `git ls-tree`; "
          "`on disk` = present in the sparse working tree). *TCK-style XML* = `*-test-NN.xml`, mostly TCK copies "
          "inside engine repositories; *JSON / YAML next to a model* = JSON or YAML files in a folder that holds a "
          "`.dmn` file (fixtures, but also configuration).", "",
          "| source | .scesim | TCK-style XML | JSON / YAML next to a model | on disk |", "|---|---|---|---|---|"]
    for name, v in sorted(res["inventory_other_formats"].items()):
        if not v:
            if v is None:
                L.append(f"| {name} | ? | ? | ? | ? |")
            continue
        L.append(f"| {name} | {v.get('scesim', 0)} | {v.get('tck_xml', 0)} | {v.get('json_yaml_next_to_dmn', 0)} "
                 f"| {v.get('on_disk', 0)} |")
    t = res["inventory_totals"]
    L.append(f"| **total** | {t.get('scesim', 0)} | {t.get('tck_xml', 0)} | {t.get('json_yaml_next_to_dmn', 0)} "
             f"| {t.get('on_disk', 0)} |")
    L += ["", "Sources with no candidate file are omitted.", "",
          "## Caveats", "",
          "* Only TCK test cases are measured; the TCK exercises engine conformance, so its test values are "
          "chosen to hit rules, and its numbers say little about business test suites.",
          "* Resolution is static: input expressions that are FEEL expressions other than a name or a path, "
          "tables inside contexts whose variables shadow inputs, BKMs invoked through other BKMs or with "
          "computed arguments, and imported models are not followed (counted under *Unresolved*).",
          "* Matching is exact on the decoded string; *near* matches (case or surrounding blanks) are recorded "
          "in `testinputs.json` (`near_mention`).",
          "* *No match* is decided on the column alone. A *wildcard* column can still leave the test value "
          "without a matching rule when the other columns exclude it; that would need evaluation.", ""]
    return "\n".join(L)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sources", required=True, help="JSON list of sources with name, path, role")
    ap.add_argument("--out", default=os.path.join("results", "corpus"))
    a = ap.parse_args(argv)
    with open(a.sources, encoding="utf-8") as fh:
        sources = json.load(fh)["sources"]
    try:
        run(sources, a.out)
    except NoTestFiles as e:
        print(e, file=sys.stderr)
        return 1
    return 0
