"""How often do decision-table inputs in public DMN models declare their domain?

Static survey for the observed-domain trap: a string input without a declared
domain gives an analyser nothing to check completeness against (Drools skips
gap analysis) or only the values the rules mention (observed-domain tools), so
a value no rule mentions is never reported missing.

Every ``.dmn`` file under the corpus sources is parsed as data with
``xml.etree.ElementTree`` (DMN 1.1 to 1.5 model namespaces; documents with a
DOCTYPE or ENTITY are refused, nothing is evaluated).  The walk skips every path
with a ``.git``, ``node_modules`` or ``target`` directory component
(``SKIP_DIRS``): installed packages and build output hold copies of models
from other places, and a local checkout may hold them outside the repository.  Files are deduplicated by the SHA-256 of their
bytes, so the checkouts must keep the stored line endings (``fetch_corpus.py``
sets ``core.autocrlf=false``).  For every decision table and every input
clause one row is recorded:

* ``type_ref`` of the inputExpression, and ``base`` = the base type after
  following itemDefinition typeRef chains (``string``, ``number``,
  ``boolean``, ``temporal``, ``structured``, ``unknown``, ``none``).  An input
  without a typeRef is typed from its entries when they are all string
  literals (``string``, ``type_source = "inferred"``) or all numeric tests;
* ``has_input_values``: an ``inputValues`` element with non-empty text;
* ``iv_values``: its values when it is a list of string literals;
* ``av_direct``: allowedValues (or DMN 1.5 typeConstraint) on the
  itemDefinition *named* by the inputExpression typeRef;
* ``av_chain``: allowedValues found anywhere along that typeRef chain;
* ``av_variable``: allowedValues reachable from the variable the expression
  names: the expression text (``A`` or ``A.b.c``) is matched to an inputData
  or decision name, and its variable typeRef is followed, through
  itemComponents for dotted paths;
* ``drools_declared``: what Drools uses for gap analysis = inputValues, else
  allowedValues of the itemDefinition named by the inputExpression typeRef
  (``av_direct``; established by ``drools_domains`` V1/V3b/V3a.  A typeRef
  chain of several itemDefinitions was not tested there; ``av_chain`` is
  reported separately);
* ``declared`` (any of the above) and ``declared_values`` (the first
  enumerable one, in Drools precedence: inputValues, direct, chain, variable);
* ``mentioned``: the string literals the rules' input entries mention
  (``not(...)`` included), ``n_any`` rules with ``-``, ``n_nonliteral``
  entries that are not literal lists (expressions, function calls, ...);
* ``unused_declared``: declared values that no rule mentions (the values an
  observed-domain tool cannot know); ``unmatched_declared``: declared values
  that no rule's entry in this column can match at all (no ``-``, no
  ``not(...)`` admitting it; only when every entry is literal), so every state
  with that value is a gap that an observed-domain tool misses;
* ``outside_declared``: mentioned values that are not declared.

Per table, ``single_hit`` (UNIQUE, ANY, FIRST, PRIORITY; a missing hitPolicy is
UNIQUE) and ``has_catch_all`` (some rule has ``-`` or an empty entry on every
input).  Summary measures added for referees: *exposed* tables (single-hit, no
catch-all rule, and an undeclared string input whose entries mention a string
literal; variant: that column has no ``-`` at all), the hit policies of tables
with string inputs, the declared share within single-hit tables, *copied
declarations* (declared set equal to the set of literals the column
mentions), the no-entry-can-match share with fixture-like paths
(``FIXTURE_PATH_RE``) excluded and on distinct (input, declaration, unmatched
values) combinations, and the number of sources contributing to each kind.

Kinds: ``tck`` (conformance tests), ``analyser`` (fixtures of verifiers /
linters), ``product-test`` (test resources of engines and editors),
``example`` (examples, tutorials, demos), ``other`` (non-test files of
product repositories).  Test fixtures are not representative of business
models; results are reported overall and per kind.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

from .dmn_import import dmn_version, split_top, string_literal, Unsupported

STRING_TYPES = {"string"}
NUMBER_TYPES = {"number", "integer", "int", "long", "double", "decimal", "float", "short"}
BOOLEAN_TYPES = {"boolean", "bool"}
TEMPORAL_TYPES = {"date", "time", "date and time", "datetime", "dateTime", "duration",
                  "days and time duration", "years and months duration",
                  "dayTimeDuration", "yearMonthDuration"}
_NUM = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)$")
_NUMTEST = re.compile(r"^(?:(?:<=|>=|<|>|=)\s*-?[\d.]+|[\[\(\]]\s*-?[\d.]+\s*\.\.\s*-?[\d.]+\s*[\]\)\[]|-?[\d.]+)$")

KINDS = ("example", "product-test", "tck", "analyser", "other")

# single-hit policies (a missing hitPolicy is UNIQUE); every other value is multi-hit or invalid
SINGLE_HIT = {"UNIQUE", "ANY", "FIRST", "PRIORITY"}
MULTI_HIT = ("COLLECT", "RULE ORDER", "OUTPUT ORDER")
# file paths that suggest a deliberately incomplete fixture (gap-analysis tests and the like)
FIXTURE_PATH_RE = re.compile(r"gap|missing|incomplete|dtanalysis|notcomplete|analysis", re.I)


_EXTRA_NS = {"http://www.omg.org/spec/DMN/20151101": "1.1",
             "http://www.omg.org/spec/DMN/20151101/dmn11.xsd": "1.1",
             "http://www.omg.org/spec/DMN/20151101/dmn.xsd": "1.1",
             "http://www.omg.org/spec/DMN/20153011": "1.1 (draft namespace)",
             "http://www.omg.org/spec/DMN/20130901": "1.0 (beta namespace)"}


def model_version(ns):
    """DMN version of a model namespace (1.1 to 1.5, plus 1.1 variants seen in the wild)."""
    v = dmn_version(ns)
    if v == "unknown (20240513)":
        return "1.6"
    return v or _EXTRA_NS.get((ns or "").rstrip("/") if ns not in _EXTRA_NS else ns)


def _local(tag: str) -> tuple[str, str]:
    if tag.startswith("{"):
        ns, local = tag[1:].split("}", 1)
        return ns, local
    return "", tag


def _child(el, name):
    for ch in el:
        if _local(ch.tag)[1] == name:
            return ch
    return None


def _children(el, name):
    return [ch for ch in el if _local(ch.tag)[1] == name]


def _text(el):
    """Text of el/text (unaryTests), or None when absent or blank."""
    if el is None:
        return None
    t = _child(el, "text")
    s = "".join(t.itertext()) if t is not None else None
    return s.strip() if s and s.strip() else None


def _strip_prefix(ref):
    if ref is None:
        return None
    ref = ref.strip()
    if ":" in ref and not ref.startswith("http"):
        ref = ref.split(":", 1)[1]
    return ref


def base_kind(t):
    if t is None:
        return "none"
    s = t.strip()
    low = s.lower()
    if low in STRING_TYPES:
        return "string"
    if low in NUMBER_TYPES:
        return "number"
    if low in BOOLEAN_TYPES:
        return "boolean"
    if s in TEMPORAL_TYPES or low in {x.lower() for x in TEMPORAL_TYPES}:
        return "temporal"
    if low == "any" or low == "context" or low.startswith("list"):
        return "other"
    return "unknown"


def string_values(text):
    """Values of a list of string literals, or None if it is not one."""
    if text is None:
        return None
    try:
        items = split_top(text)
        return [string_literal(i) for i in items]
    except Unsupported:
        return None


def _constraint_text(el):
    """allowedValues, or DMN 1.5 typeConstraint, of an itemDefinition/component."""
    t = _text(_child(el, "allowedValues"))
    if t is None:
        t = _text(_child(el, "typeConstraint"))
    return t


class TypeInfo:
    __slots__ = ("name", "type_ref", "allowed", "components", "is_collection")

    def __init__(self, el):
        self.name = el.get("name")
        tr = _child(el, "typeRef")
        self.type_ref = (tr.text or "").strip() if tr is not None else el.get("typeRef")
        self.allowed = _constraint_text(el)
        self.components = {c.get("name"): TypeInfo(c) for c in _children(el, "itemComponent")}
        self.is_collection = el.get("isCollection") == "true"


def item_definitions(root):
    """name -> TypeInfo for top-level itemDefinitions of any DMN namespace."""
    out = {}
    for el in root:
        ns, local = _local(el.tag)
        if local == "itemDefinition" and model_version(ns) and el.get("name"):
            out[el.get("name")] = TypeInfo(el)
    return out


def resolve(type_ref, items, depth=0):
    """(base type name, first allowedValues text on the chain, info of the named item)."""
    t = _strip_prefix(type_ref)
    if not t:
        return None, None, None
    info = items.get(t)
    if info is None or depth > 10:
        return t, None, None
    if info.components:
        return "<structured>", info.allowed, info
    if info.is_collection:
        return "<collection>", info.allowed, info
    if info.type_ref is None:
        return "<unknown>", info.allowed, info
    b, a, _ = resolve(info.type_ref, items, depth + 1)
    return b, info.allowed if info.allowed is not None else a, info


def _base_class(base):
    if base == "<structured>":
        return "structured"
    if base in ("<collection>", "<unknown>"):
        return "other"
    return base_kind(base)


def _path_allowed(type_ref, path, items):
    """allowedValues reachable from a variable typed ``type_ref`` along ``path``."""
    b, a, info = resolve(type_ref, items)
    if not path:
        return b, a
    node = info
    for seg in path:
        if node is None or seg not in node.components:
            return None, None
        comp = node.components[seg]
        cb, ca, cinfo = resolve(comp.type_ref, items) if comp.type_ref else (None, None, None)
        if comp.components:
            node = comp
            a = comp.allowed
            b = "<structured>"
        else:
            node = cinfo
            a = comp.allowed if comp.allowed is not None else ca
            b = cb
    return b, a


# -- input entries ----------------------------------------------------------------

_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _quoted(text):
    """Every string literal inside an expression (counted as mentioned by the rule)."""
    return [m.group(1).replace('\\"', '"') for m in _QUOTED.finditer(text)]


def entry_info(text):
    """Classify one input entry: ('any'|'lits'|'notlits'|'nonliteral'|'numeric', values)."""
    t = (text or "").strip()
    if t in ("", "-"):
        return "any", []
    neg = False
    if t.startswith("not(") and t.endswith(")"):
        neg, t = True, t[4:-1].strip()
    try:
        items = split_top(t)
    except Unsupported:
        return "nonliteral", _quoted(t)
    vals, numeric = [], 0
    for it in items:
        if it.startswith('"'):
            try:
                vals.append(string_literal(it))
                continue
            except Unsupported:
                return "nonliteral", _quoted(t)
        if _NUMTEST.match(it.replace(" ", "")) or _NUMTEST.match(it):
            numeric += 1
            continue
        return "nonliteral", _quoted(t)
    if numeric and not vals:
        return "numeric", []
    if numeric:
        return "nonliteral", vals
    return ("notlits" if neg else "lits"), vals


# -- one file -----------------------------------------------------------------------

def analyse_bytes(data: bytes, rel: str = "?"):
    """(file record, list of table records, list of input rows)."""
    frec = {"path": rel, "error": None, "version": None, "n_tables": 0}
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        frec["error"] = "doctype"
        return frec, [], []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        frec["error"] = f"xml: {e}"
        return frec, [], []
    ns, local = _local(root.tag)
    frec["version"] = model_version(ns)
    if local != "definitions" or frec["version"] is None:
        frec["error"] = "not a DMN model"
        return frec, [], []
    items = item_definitions(root)
    variables = {}        # inputData / decision name -> variable typeRef
    for el in root:
        _, l = _local(el.tag)
        if l in ("inputData", "decision") and el.get("name"):
            v = _child(el, "variable")
            variables[el.get("name")] = v.get("typeRef") if v is not None else None
    parents = {c: p for p in root.iter() for c in p}
    tables, rows = [], []
    for ti, dt in enumerate(el for el in root.iter() if _local(el.tag)[1] == "decisionTable"):
        owner = parents.get(dt)
        while owner is not None and _local(owner.tag)[1] not in ("decision", "businessKnowledgeModel"):
            owner = parents.get(owner)
        oname = (owner.get("name") or owner.get("id")) if owner is not None else "?"
        inputs = _children(dt, "input")
        rules = _children(dt, "rule")
        trec = {"path": rel, "table": oname, "table_index": ti,
                "hit_policy": dt.get("hitPolicy", "UNIQUE"), "n_rules": len(rules),
                "n_inputs": len(inputs), "n_outputs": len(_children(dt, "output"))}
        cols = [[] for _ in inputs]
        for r in rules:
            for k, ie in enumerate(_children(r, "inputEntry")):
                if k < len(cols):
                    t = _child(ie, "text")
                    cols[k].append("".join(t.itertext()) if t is not None else "")
        # a catch-all rule: "-" (or empty) on every input; a missing inputEntry counts as empty
        any_txt = ("", "-")
        trec["single_hit"] = trec["hit_policy"].strip().upper() in SINGLE_HIT
        # a default output answers a no-match, so an unmentioned value still gets a defined result
        trec["has_default_output"] = any(_child(o, "defaultOutputEntry") is not None
                                         for o in _children(dt, "output"))
        trec["has_catch_all"] = any(
            all(("".join(t.itertext()) if (t := _child(ie, "text")) is not None else "").strip() in any_txt
                for ie in _children(r, "inputEntry")[:len(inputs)])
            for r in rules)
        trows = [_input_row(inp, k, cols[k], items, variables, trec) for k, inp in enumerate(inputs)]
        outs = [["".join(t.itertext()) if (t := _child(oe, "text")) is not None else ""
                 for oe in _children(r, "outputEntry")] for r in rules]
        fp_src = [trec["hit_policy"],
                  [[x["expression"], x["type_ref"], x["input_values"], x["av_direct"], x["av_chain"],
                    x["av_variable"]] for x in trows],
                  [[c[i] if i < len(c) else None for c in cols] for i in range(len(rules))], outs]
        trec["fingerprint"] = hashlib.sha256(json.dumps(fp_src, ensure_ascii=False).encode()).hexdigest()[:16]
        for x in trows:
            x["fingerprint"] = trec["fingerprint"]
        rows.extend(trows)
        tables.append(trec)
    frec["n_tables"] = len(tables)
    return frec, tables, rows


def _input_row(inp, k, col, items, variables, trec):
    ie = _child(inp, "inputExpression")
    expr_text = ""
    type_ref = None
    if ie is not None:
        type_ref = ie.get("typeRef")
        t = _child(ie, "text")
        expr_text = ("".join(t.itertext()) if t is not None else "").strip()
    label = inp.get("label") or expr_text or inp.get("id") or f"#{k}"
    base, av_chain, info = resolve(type_ref, items)
    av_direct = info.allowed if info is not None else None
    base_cls = _base_class(base) if type_ref else "none"
    # the variable the expression names, possibly a dotted path into it
    av_var, var_base = None, None
    if expr_text:
        parts = [p.strip() for p in expr_text.split(".")]
        for cut in range(len(parts), 0, -1):
            name = ".".join(parts[:cut])
            if name in variables:
                var_base, av_var = _path_allowed(variables[name], parts[cut:], items)
                break
    entries = [entry_info(x) for x in col]
    kinds = Counter(e[0] for e in entries)
    mentioned = []
    for _, vals in entries:
        for v in vals:
            if v not in mentioned:
                mentioned.append(v)
    type_source = "typeRef" if type_ref else None
    if base_cls in ("none", "unknown", "other"):
        # untyped (or an unresolvable reference): type from the variable, then from literals
        vb = _base_class(var_base) if var_base else None
        if vb in ("string", "number", "boolean", "temporal"):
            base_cls, type_source = vb, "variable"
        elif base_cls == "none":
            lit = kinds["lits"] + kinds["notlits"]
            if lit and not kinds["nonliteral"] and not kinds["numeric"]:
                base_cls, type_source = "string", "inferred"
            elif kinds["numeric"] and not lit and not kinds["nonliteral"]:
                base_cls, type_source = "number", "inferred"
            elif all(x.strip() in ("true", "false", "-", "") for x in col) and any(x.strip() in ("true", "false") for x in col):
                base_cls, type_source = "boolean", "inferred"
    iv_text = _text(_child(inp, "inputValues"))
    declared_texts = [("inputValues", iv_text), ("av_direct", av_direct),
                      ("av_chain", av_chain), ("av_variable", av_var)]
    declared_values, declared_source = None, None
    for src, txt in declared_texts:
        if txt is not None:
            vals = string_values(txt)
            if vals is not None:
                declared_values, declared_source = vals, src
                break
    row = dict(path=trec["path"], table=trec["table"], table_index=trec["table_index"],
               input_index=k, label=label, expression=expr_text, type_ref=type_ref,
               base=base_cls, type_source=type_source,
               has_input_values=iv_text is not None, input_values=iv_text,
               av_direct=av_direct, av_chain=av_chain, av_variable=av_var,
               drools_declared=iv_text is not None or av_direct is not None,
               declared=any(t is not None for _, t in declared_texts),
               reachable_allowed=(av_chain is not None or av_var is not None),
               declared_values=declared_values, declared_source=declared_source,
               mentioned=mentioned, n_entries=len(col), n_any=kinds["any"],
               n_not=kinds["notlits"], n_nonliteral=kinds["nonliteral"],
               n_numeric=kinds["numeric"])
    row["iv_enumerable"] = iv_text is not None and string_values(iv_text) is not None
    if declared_values is not None:
        dset = set(declared_values)
        mset = set(mentioned)
        row["unused_declared"] = [v for v in declared_values if v not in mset]
        row["outside_declared"] = [v for v in mentioned if v not in dset]
        if kinds["nonliteral"] or kinds["numeric"]:
            row["unmatched_declared"] = None          # cannot tell
        elif kinds["any"]:
            row["unmatched_declared"] = []
        else:
            matchable = set()
            for kind, vals in entries:
                if kind == "lits":
                    matchable |= set(vals)
                elif kind == "notlits":
                    matchable |= dset - set(vals)
            row["unmatched_declared"] = [v for v in declared_values if v not in matchable]
    else:
        row["unused_declared"] = row["outside_declared"] = row["unmatched_declared"] = None
    return row


# -- corpus -------------------------------------------------------------------------

_TEST_SEG = re.compile(r"^(?:src/test|it|spec|specs|__tests__|fixtures?|testdata|test-?resources|.*test-?cases?|"
                       r"(?:.*[._-])?tests?(?:[._-].*)?|integration-?tests?.*)$", re.I)
_EXAMPLE_RE = re.compile(r"example|sample|demo|tutorial|getting-?started|quickstart|showcase|playground|starter", re.I)
_TCK_RE = re.compile(r"(^|/)(tck|dmn-tck|TestCases|compliance-level-\d|compatibility)(/|$)", re.I)
_ANALYSER_RE = re.compile(r"verifier|validation|validator|lint|dmn-check", re.I)


def classify(source, rel):
    """Kind of one file from its source's role and its path inside the source."""
    role = source.get("role", "product")
    if role == "tck" or _TCK_RE.search(rel):
        return "tck"
    if role == "analyser":
        return "analyser"
    if role == "example":
        return "example"
    if any(_TEST_SEG.match(seg) for seg in rel.split("/")[:-1]) or source.get("examples_are_tests"):
        if role == "product" and _ANALYSER_RE.search(rel):
            return "analyser"
        return "product-test"
    if _EXAMPLE_RE.search(rel):
        return "example"
    return "other"


KIND_PRIORITY = {"tck": 0, "example": 1, "product-test": 2, "analyser": 3, "other": 4}


# directories never walked: git data, installed packages, build output
SKIP_DIRS = {".git", "node_modules", "target"}


def collect(sources):
    """[(sha256, source, rel, kind, bytes)] of unique files, plus duplicate count per kind."""
    seen = {}
    dups = Counter()
    for src in sources:
        base = src["path"]
        for dp, dn, fn in os.walk(base):
            dn[:] = sorted(d for d in dn if d not in SKIP_DIRS)
            for f in sorted(fn):
                if not f.lower().endswith(".dmn"):
                    continue
                full = os.path.join(dp, f)
                rel = os.path.relpath(full, base).replace("\\", "/")
                with open(full, "rb") as fh:
                    data = fh.read()
                h = hashlib.sha256(data).hexdigest()
                kind = classify(src, rel)
                cur = seen.get(h)
                if cur is None:
                    seen[h] = dict(sha256=h, source=src["name"], rel=rel, kind=kind, data=data,
                                   copies=1, sources={src["name"]})
                else:
                    cur["copies"] += 1
                    cur["sources"].add(src["name"])
                    dups[kind] += 1
                    if KIND_PRIORITY[kind] < KIND_PRIORITY[cur["kind"]]:
                        cur.update(source=src["name"], rel=rel, kind=kind)
    return list(seen.values()), dups


def _pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def summarise(files, tables, rows):
    """Headline measures; ``rows`` carry ``kind``."""
    out = {}
    groups = {"all": None, **{k: k for k in KINDS}}
    for g, k in groups.items():
        fr = [f for f in files if k is None or f["kind"] == k]
        tr = [t for t in tables if k is None or t["kind"] == k]
        rr = [r for r in rows if k is None or r["kind"] == k]
        if not fr:
            continue
        s = {"files": len(fr), "files_with_tables": sum(1 for f in fr if f["n_tables"]),
             "parse_errors": sum(1 for f in fr if f["error"]), "decision_tables": len(tr),
             "rules": sum(t["n_rules"] for t in tr), "inputs": len(rr),
             "inputs_by_base": dict(Counter(r["base"] for r in rr))}
        for base in ("string", "boolean", "number"):
            br = [r for r in rr if r["base"] == base]
            n = len(br)
            d = {"inputs": n,
                 "typed_by_typeRef": sum(1 for r in br if r["type_source"] == "typeRef"),
                 "input_values": sum(r["has_input_values"] for r in br),
                 "reachable_allowed": sum(1 for r in br if r["reachable_allowed"]),
                 "allowed_only": sum(1 for r in br if r["reachable_allowed"] and not r["has_input_values"]),
                 "declared_any": sum(r["declared"] for r in br),
                 "drools_usable": sum(r["drools_declared"] for r in br),
                 "variable_only": sum(1 for r in br if r["declared"] and not r["drools_declared"]
                                      and r["av_chain"] is None),
                 "none": sum(1 for r in br if not r["declared"])}
            for key in list(d):
                if key != "inputs":
                    d[key + "_pct"] = _pct(d[key], n)
            if base == "string":
                enum = [r for r in br if r["declared_values"] is not None]
                d["declared_enumerable"] = len(enum)
                d["with_unused_value"] = sum(1 for r in enum if r["unused_declared"])
                d["with_unused_value_pct"] = _pct(d["with_unused_value"], len(enum))
                known = [r for r in enum if r["unmatched_declared"] is not None]
                d["unmatched_known"] = len(known)
                d["with_unmatched_value"] = sum(1 for r in known if r["unmatched_declared"])
                d["with_unmatched_value_pct"] = _pct(d["with_unmatched_value"], len(known))
                d["with_outside_value"] = sum(1 for r in enum if r["outside_declared"])
                d["with_outside_value_pct"] = _pct(d["with_outside_value"], len(enum))
                d["declared_values_total"] = sum(len(r["declared_values"]) for r in enum)
                d["unused_values_total"] = sum(len(r["unused_declared"]) for r in enum)
                d["undeclared_no_literals"] = sum(1 for r in br if not r["declared"] and not r["mentioned"])
            s[base] = d
        # tables with at least one string input
        by_table = defaultdict(list)
        for r in rr:
            if r["base"] == "string":
                by_table[(r["source"], r["path"], r["table_index"])].append(r)
        nt = len(by_table)
        s["tables_with_string_inputs"] = nt
        s["tables_all_string_declared"] = sum(1 for v in by_table.values() if all(r["declared"] for r in v))
        s["tables_all_string_drools"] = sum(1 for v in by_table.values() if all(r["drools_declared"] for r in v))
        s["tables_no_string_declared"] = sum(1 for v in by_table.values() if not any(r["declared"] for r in v))
        for key in ("tables_all_string_declared", "tables_all_string_drools", "tables_no_string_declared"):
            s[key + "_pct"] = _pct(s[key], nt)
        s["hit_policies"] = dict(Counter(t["hit_policy"] for t in tr))
        s.update(_extra_measures(fr, tr, rr, by_table))
        out[g] = s
    return out


def is_test_path(path):
    """True when some folder of the path is a test folder (the rule ``classify`` applies inside
    product repositories; files of example repositories keep the example kind)."""
    return any(_TEST_SEG.match(seg) for seg in (path or "").split("/")[:-1])


def is_fixture_path(path):
    """True when a file path suggests a deliberately incomplete fixture."""
    return bool(FIXTURE_PATH_RE.search(path or ""))


def exposed_column(r, table):
    """String column an observed-domain tool cannot complete, in a single-hit table without a catch-all:
    undeclared, its entries mention a string literal, and no all-'-' rule covers it."""
    return (r["base"] == "string" and not r["declared"] and bool(r["mentioned"])
            and table["single_hit"] and not table["has_catch_all"])


def exposed_strict_column(r, table):
    """Exposed column whose entries are all string literals: no '-', no not(...) and no other FEEL
    expression, any of which can match a value the rules never name."""
    return (exposed_column(r, table) and r["n_any"] == 0 and r["n_not"] == 0
            and r["n_nonliteral"] == 0)


def _extra_measures(fr, tr, rr, by_table):
    """Exposure, hit policies, copied declarations, fixture-excluded unmatched share, sources."""
    s = {}
    tkey = {(t["source"], t["path"], t["table_index"]): t for t in tr}
    nt = len(by_table)
    exposed = exposed_dash = exposed_strict = 0
    hp = Counter()
    single = []
    for key, v in by_table.items():
        t = tkey[key]
        p = t["hit_policy"].strip().upper()
        hp[p if t["single_hit"] or p in MULTI_HIT else "other"] += 1
        if t["single_hit"]:
            single.append(v)
        if any(exposed_column(r, t) for r in v):
            exposed += 1
        if any(exposed_column(r, t) and r["n_any"] == 0 for r in v):
            exposed_dash += 1
        if any(exposed_strict_column(r, t) for r in v):
            exposed_strict += 1
    s["exposed_tables"] = exposed
    s["exposed_tables_strict"] = exposed_strict
    s["exposed_tables_strict_pct"] = _pct(exposed_strict, nt)
    s["exposed_tables_pct"] = _pct(exposed, nt)
    # sensitivity of the measures (the headline definitions above are unchanged):
    # exposed tables whose no-match returns a declared default output
    s["exposed_tables_with_default_output"] = sum(
        1 for key, v in by_table.items()
        if tkey[key].get("has_default_output") and any(exposed_column(r, tkey[key]) for r in v))
    # Drools-usable string declarations on an input expression without a typeRef (Drools 7.74.1
    # skips the table's analysis then, even with inputValues)
    sr = [r for r in rr if r["base"] == "string"]
    s["string_drools_declared_no_typeref"] = sum(1 for r in sr if r["drools_declared"] and not r["type_ref"])
    s["string_drools_with_typeref"] = sum(1 for r in sr if r["drools_declared"] and r["type_ref"])
    s["string_drools_with_typeref_pct"] = _pct(s["string_drools_with_typeref"], len(sr))
    # files of the example kind that sit under a test folder of their example repository
    s["tables_under_test_path"] = sum(1 for t in tr if is_test_path(t["path"]))
    s["string_tables_under_test_path"] = sum(1 for key in by_table if is_test_path(key[1]))
    s["exposed_tables_under_test_path"] = sum(
        1 for key, v in by_table.items()
        if is_test_path(key[1]) and any(exposed_column(r, tkey[key]) for r in v))
    nt_rows = [r for r in sr if not is_test_path(r["path"])]
    s["string_inputs_outside_test_path"] = len(nt_rows)
    s["string_declared_outside_test_path_pct"] = _pct(sum(r["declared"] for r in nt_rows), len(nt_rows))
    s["string_drools_outside_test_path_pct"] = _pct(sum(r["drools_declared"] for r in nt_rows), len(nt_rows))
    s["exposed_tables_no_dash"] = exposed_dash
    s["exposed_tables_no_dash_pct"] = _pct(exposed_dash, nt)
    s["string_tables_hit_policy"] = dict(hp)
    s["string_tables_single_hit"] = len(single)
    s["string_tables_single_hit_pct"] = _pct(len(single), nt)
    s["string_tables_with_catch_all"] = sum(1 for k in by_table if tkey[k]["has_catch_all"])
    s["single_hit_tables_with_catch_all"] = sum(1 for k in by_table
                                                if tkey[k]["single_hit"] and tkey[k]["has_catch_all"])
    srows = [r for v in single for r in v]
    s["single_hit_string_inputs"] = len(srows)
    s["single_hit_string_declared"] = sum(r["declared"] for r in srows)
    s["single_hit_string_declared_pct"] = _pct(s["single_hit_string_declared"], len(srows))
    s["single_hit_string_drools"] = sum(r["drools_declared"] for r in srows)
    s["single_hit_string_drools_pct"] = _pct(s["single_hit_string_drools"], len(srows))
    s["single_hit_tables_all_declared"] = sum(1 for v in single if all(r["declared"] for r in v))
    s["single_hit_tables_all_declared_pct"] = _pct(s["single_hit_tables_all_declared"], len(single))
    # copied declarations: the declared set equals the set of literals the column mentions
    enum = [r for r in rr if r["base"] == "string" and r["declared_values"] is not None]
    s["copied_declaration"] = sum(1 for r in enum if set(r["declared_values"]) == set(r["mentioned"]))
    s["copied_declaration_pct"] = _pct(s["copied_declaration"], len(enum))
    s["copied_declaration_of"] = len(enum)
    # no entry can match, with fixture-like paths excluded
    known = [r for r in enum if r["unmatched_declared"] is not None]
    kn = [r for r in known if not is_fixture_path(r["path"])]
    s["unmatched_fixture_path"] = sum(1 for r in known if r["unmatched_declared"] and is_fixture_path(r["path"]))
    s["unmatched_known_nonfixture"] = len(kn)
    s["with_unmatched_value_nonfixture"] = sum(1 for r in kn if r["unmatched_declared"])
    s["with_unmatched_value_nonfixture_pct"] = _pct(s["with_unmatched_value_nonfixture"], len(kn))
    # source repositories
    s["sources_files"] = len({f["source"] for f in fr})
    s["sources_tables"] = len({t["source"] for t in tr})
    s["sources_string_inputs"] = len({r["source"] for r in rr if r["base"] == "string"})
    return s


def unmatched_combinations(rows):
    """Distinct (input, declaration, unmatched values) combinations over string inputs whose
    unmatched set is known: (all, with an unmatched value), also with fixture-like paths excluded."""
    def combos(rs):
        known = {(r["label"], tuple(r["declared_values"]), tuple(r["unmatched_declared"]))
                 for r in rs if r["base"] == "string" and r.get("unmatched_declared") is not None}
        return len(known), sum(1 for k in known if k[2])
    n, m = combos(rows)
    nf, mf = combos([r for r in rows if not is_fixture_path(r["path"])])
    flagged = {(r["label"], tuple(r["declared_values"]), tuple(r["unmatched_declared"]))
               for r in rows if r["base"] == "string" and r.get("unmatched_declared")
               and is_fixture_path(r["path"])}
    return {"combinations_known": n, "combinations_unmatched": m,
            "combinations_unmatched_pct": _pct(m, n),
            "combinations_with_fixture_path": len(flagged),
            "combinations_known_nonfixture": nf, "combinations_unmatched_nonfixture": mf,
            "combinations_unmatched_nonfixture_pct": _pct(mf, nf)}


def run(sources, out_dir):
    files_u, dups = collect(sources)
    files, tables, rows = [], [], []
    for f in sorted(files_u, key=lambda x: (x["source"], x["rel"])):
        frec, trs, rs = analyse_bytes(f["data"], f["rel"])
        frec.update(source=f["source"], kind=f["kind"], sha256=f["sha256"], copies=f["copies"],
                    also_in=sorted(f["sources"] - {f["source"]}))
        for x in trs + rs:
            x["source"], x["kind"] = f["source"], f["kind"]
        files.append(frec)
        tables.extend(trs)
        rows.extend(rs)
    summary = summarise(files, tables, rows)
    # second deduplication: decision tables with identical content (inputs, declarations,
    # entries, outputs) in different files count once, kept in the highest-priority kind
    best = {}
    for t in tables:
        fp = t["fingerprint"]
        if fp not in best or KIND_PRIORITY[t["kind"]] < KIND_PRIORITY[best[fp]["kind"]]:
            best[fp] = t
    keep = {(t["source"], t["path"], t["table_index"]) for t in best.values()}
    ut = [t for t in tables if (t["source"], t["path"], t["table_index"]) in keep]
    ur = [r for r in rows if (r["source"], r["path"], r["table_index"]) in keep]
    ufiles = [dict(f, n_tables=sum(1 for t in ut if t["source"] == f["source"] and t["path"] == f["path"]))
              for f in files]
    summary_unique = summarise([f for f in ufiles if f["n_tables"]], ut, ur)
    per_source = {}
    for s in sources:
        fr = [f for f in files if f["source"] == s["name"]]
        per_source[s["name"]] = {"unique_files": len(fr), "tables": sum(f["n_tables"] for f in fr),
                                 "kinds": dict(Counter(f["kind"] for f in fr))}
    os.makedirs(out_dir, exist_ok=True)
    res = {"summary": summary, "summary_unique_tables": summary_unique,
           "unmatched_combinations": unmatched_combinations(rows),
           "duplicates_dropped_by_kind": dict(dups),
           "per_source": per_source, "files": files, "tables": tables, "inputs": rows}
    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    cols = ["source", "kind", "path", "table", "table_index", "input_index", "label", "type_ref",
            "base", "type_source", "has_input_values", "iv_enumerable", "av_direct", "av_chain",
            "av_variable", "drools_declared", "declared", "declared_source", "declared_values",
            "mentioned", "unused_declared", "unmatched_declared", "outside_declared",
            "n_entries", "n_any", "n_not", "n_nonliteral", "fingerprint"]
    with open(os.path.join(out_dir, "inputs.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([json.dumps(r[c], ensure_ascii=False) if isinstance(r[c], list) else r[c]
                        for c in cols])
    return res


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sources", required=True, help="sources.json (name, path, role, url, sha)")
    ap.add_argument("--out", default=os.path.join("results", "corpus"))
    a = ap.parse_args(argv)
    with open(a.sources, encoding="utf-8") as fh:
        sources = json.load(fh)["sources"]
    res = run(sources, a.out)
    s = res["summary"]
    for g, v in s.items():
        st = v.get("string", {})
        print(f"{g:13s} files={v['files']:5d} tables={v['decision_tables']:5d} "
              f"string={st.get('inputs', 0):5d} iv={st.get('input_values_pct')}% "
              f"reach-av={st.get('reachable_allowed_pct')}% drools={st.get('drools_usable_pct')}% "
              f"tables-all={v.get('tables_all_string_declared_pct')}% unused={st.get('with_unused_value_pct')}%")
    return 0


KIND_LABEL = {"all": "all", "example": "examples / tutorials", "product-test": "product test resources",
              "tck": "conformance (TCK)", "analyser": "analyser fixtures", "other": "product, non-test"}


def _f(x):
    return "-" if x is None else (f"{x:.1f}" if isinstance(x, float) else str(x))


def _headline(summary):
    lines = ["| kind | files | decision tables | string inputs | inputValues % | reachable allowedValues % "
             "| any declaration % | usable by Drools % | tables: every string input declared % "
             "| tables: every string input Drools-usable % | declared enumerable inputs "
             "| ... with a declared value no rule mentions % "
             "| ... with a declared value no entry can match % (n/known) | ... with rule values outside the declaration % |",
             "|" + "---|" * 14]
    for g, v in summary.items():
        st = v["string"]
        lines.append(f"| {KIND_LABEL[g]} | {v['files']} | {v['decision_tables']} | {st['inputs']} "
                     f"| {_f(st['input_values_pct'])} | {_f(st['reachable_allowed_pct'])} "
                     f"| {_f(st['declared_any_pct'])} | {_f(st['drools_usable_pct'])} "
                     f"| {_f(v['tables_all_string_declared_pct'])} | {_f(v['tables_all_string_drools_pct'])} "
                     f"| {st['declared_enumerable']} | {_f(st['with_unused_value_pct'])} "
                     f"| {_f(st['with_unmatched_value_pct'])} ({st['with_unmatched_value']}/{st['unmatched_known']}) "
                     f"| {_f(st['with_outside_value_pct'])} |")
    return lines


def _other_types(summary):
    lines = ["| kind | boolean inputs | declared % (inputValues / allowedValues) | numeric inputs "
             "| declared % (inputValues / allowedValues) | Drools-usable % (numeric) |",
             "|---|---|---|---|---|---|"]
    for g, v in summary.items():
        b, n = v["boolean"], v["number"]
        lines.append(f"| {KIND_LABEL[g]} | {b['inputs']} | {_f(b['declared_any_pct'])} ({_f(b['input_values_pct'])} / "
                     f"{_f(b['reachable_allowed_pct'])}) | {n['inputs']} | {_f(n['declared_any_pct'])} "
                     f"({_f(n['input_values_pct'])} / {_f(n['reachable_allowed_pct'])}) | {_f(n['drools_usable_pct'])} |")
    return lines


def notable(res, limit=25):
    """Declared string inputs with a declared value that no rule entry can match, one per distinct table."""
    order_k = {"example": 0, "other": 1, "product-test": 2, "analyser": 3, "tck": 4}
    fps, seen, out = set(), set(), []
    order = sorted(res["inputs"], key=lambda r: (order_k[r["kind"]], r["source"], r["path"]))
    for r in order:
        if r["base"] != "string" or not r.get("unmatched_declared"):
            continue
        fps.add(r["fingerprint"])
        key = (r["label"], tuple(r["declared_values"]), tuple(r["unmatched_declared"]))
        if key in seen:          # the same column in variants of one test model
            continue
        seen.add(key)
        out.append(r)
    return out[:limit], len(fps), len(seen)


def _by_both(res, header, cells):
    """Rows per kind, first counted by distinct files, then by distinct table contents."""
    lines = ["| count by | kind | " + " | ".join(header) + " |", "|---|---|" + "---|" * len(header)]
    for label, summ in (("files", res["summary"]), ("contents", res["summary_unique_tables"])):
        for g, v in summ.items():
            lines.append(f"| {label} | {KIND_LABEL[g]} | " + " | ".join(cells(v)) + " |")
    return lines


def _np(n, d, pct):
    return f"{n}/{d} ({_f(pct)}%)"


def _referee_sections(res):
    a, au = res["summary"]["all"], res["summary_unique_tables"]["all"]
    st, stu = a["string"], au["string"]
    C = res["unmatched_combinations"]
    L = ["## Exposure: single-hit tables an observed-domain tool cannot complete", "",
         "A table is *exposed* when its hit policy is single-hit (UNIQUE, ANY, FIRST, PRIORITY; a missing "
         "hitPolicy is UNIQUE), it has a string input with no declaration (as above) whose entries mention at "
         "least one string literal, and no catch-all rule covers that column: no rule has `-` (or an empty "
         "entry) in that column and in every other input. A value no rule mentions then reaches no rule, and "
         "an observed-domain tool cannot report it. *Variant*: no rule has `-` in that column at all (a subset "
         "of the exposed tables). *Strict*: the exposed column's entries are all string literals, with no `-`, "
         "`not(...)` or other FEEL expression that could match a value the rules never name. Multi-hit tables (COLLECT, RULE ORDER, OUTPUT ORDER) are never exposed: an "
         "empty result is a legitimate answer for them. Denominator: tables with at least one string input.", ""]
    L += _by_both(res, ["tables with string inputs", "single-hit", "with a catch-all rule",
                        "exposed", "variant: no `-` in the column", "strict: literal entries only"],
                  lambda v: [str(v["tables_with_string_inputs"]),
                             _np(v["string_tables_single_hit"], v["tables_with_string_inputs"],
                                 v["string_tables_single_hit_pct"]),
                             str(v["string_tables_with_catch_all"]),
                             _np(v["exposed_tables"], v["tables_with_string_inputs"], v["exposed_tables_pct"]),
                             _np(v["exposed_tables_no_dash"], v["tables_with_string_inputs"],
                                 v["exposed_tables_no_dash_pct"]),
                             _np(v["exposed_tables_strict"], v["tables_with_string_inputs"],
                                 v["exposed_tables_strict_pct"])])
    e = res["summary"].get("example", {})
    L += ["", "### Sensitivity of the measures", "",
          f"* Default output: {a['exposed_tables_with_default_output']} of the {a['exposed_tables']} exposed "
          f"tables (distinct contents: {au['exposed_tables_with_default_output']} of {au['exposed_tables']}) "
          "have a defaultOutputEntry, so a value no rule mentions still gets a defined result; the exposure "
          "count does not read default outputs.",
          f"* Drools and typeRef: {a['string_drools_declared_no_typeref']} of the "
          f"{a['string']['drools_usable']} string inputs counted as usable by Drools have no inputExpression "
          "typeRef; Drools 7.74.1 then skips the table's gap analysis even with inputValues. Requiring a "
          f"typeRef gives {_np(a['string_drools_with_typeref'], a['string']['inputs'], a['string_drools_with_typeref_pct'])} "
          "usable by Drools.",
          f"* Examples under test folders: files of example repositories keep the example kind even under "
          f"a test folder. {e.get('tables_under_test_path', 0)} of the {e.get('decision_tables', 0)} example "
          f"tables sit under one ({e.get('exposed_tables_under_test_path', 0)} of the "
          f"{e.get('exposed_tables', 0)} exposed ones); without them, the "
          f"{e.get('string_inputs_outside_test_path', 0)} example string inputs declare a domain in "
          f"{e.get('string_declared_outside_test_path_pct')}% and in a form Drools uses in "
          f"{e.get('string_drools_outside_test_path_pct')}%."]
    L += ["", "### Hit policies of tables with string inputs", ""]
    pols = ["UNIQUE", "ANY", "FIRST", "PRIORITY", "COLLECT", "RULE ORDER", "OUTPUT ORDER", "other"]
    L += _by_both(res, ["tables with string inputs"] + pols,
                  lambda v: [str(v["tables_with_string_inputs"])]
                  + [str(v["string_tables_hit_policy"].get(p, 0)) for p in pols])
    L += ["", "*other* = values outside the DMN hit policies (e.g. `LAST`, misspelt values).", "",
          "### Declarations in single-hit tables", "",
          "The declared share of string inputs, restricted to single-hit tables (multi-hit tables excluded).", ""]
    L += _by_both(res, ["single-hit tables with string inputs", "their string inputs", "any declaration",
                        "usable by Drools", "tables: every string input declared"],
                  lambda v: [str(v["string_tables_single_hit"]), str(v["single_hit_string_inputs"]),
                             _np(v["single_hit_string_declared"], v["single_hit_string_inputs"],
                                 v["single_hit_string_declared_pct"]),
                             _np(v["single_hit_string_drools"], v["single_hit_string_inputs"],
                                 v["single_hit_string_drools_pct"]),
                             _np(v["single_hit_tables_all_declared"], v["string_tables_single_hit"],
                                 v["single_hit_tables_all_declared_pct"])])
    L += ["", "## Declared values that no rule mentions", "",
          f"**{st['with_unused_value']} of {st['declared_enumerable']} string inputs whose declaration is a "
          f"list of string literals ({_f(st['with_unused_value_pct'])}%) declare a value that no input entry of "
          f"the column mentions** (distinct files); by distinct table contents {stu['with_unused_value']} of "
          f"{stu['declared_enumerable']} ({_f(stu['with_unused_value_pct'])}%). These are values an "
          f"observed-domain tool cannot know. Declared values in total: {st['declared_values_total']}, of which "
          f"{st['unused_values_total']} are mentioned by no rule (distinct contents: {stu['declared_values_total']}"
          f" and {stu['unused_values_total']}).", ""]
    L += _by_both(res, ["declared enumerable string inputs", "with a declared value no rule mentions"],
                  lambda v: [str(v["string"]["declared_enumerable"]),
                             _np(v["string"]["with_unused_value"], v["string"]["declared_enumerable"],
                                 v["string"]["with_unused_value_pct"])])
    L += ["", "## Copied declarations", "",
          "Among string inputs whose declaration is a list of string literals, the share whose declared set "
          "**equals** the set of string literals the column's entries mention (`not(...)` and literals inside "
          "expressions included): a declaration that adds nothing beyond the rules, as if copied from them. "
          f"Overall {_np(a['copied_declaration'], a['copied_declaration_of'], a['copied_declaration_pct'])} "
          f"(distinct files), {_np(au['copied_declaration'], au['copied_declaration_of'], au['copied_declaration_pct'])}"
          " (distinct contents).", ""]
    L += _by_both(res, ["declared enumerable string inputs", "declared set = mentioned set"],
                  lambda v: [str(v["copied_declaration_of"]),
                             _np(v["copied_declaration"], v["copied_declaration_of"], v["copied_declaration_pct"])])
    L += ["", "## No entry can match: distinct combinations and fixture-like paths", "",
          f"Inputs (distinct files): {_np(st['with_unmatched_value'], st['unmatched_known'], st['with_unmatched_value_pct'])}"
          f"; distinct table contents: {_np(stu['with_unmatched_value'], stu['unmatched_known'], stu['with_unmatched_value_pct'])}. "
          f"Distinct (input, declaration, unmatched values) combinations, over all string inputs whose unmatched "
          f"set is known: {_np(C['combinations_unmatched'], C['combinations_known'], C['combinations_unmatched_pct'])}"
          f". *Fixture-like path*: the file path or name contains `gap`, `missing`, `incomplete`, `dtanalysis`, "
          f"`notcomplete` or `analysis` (case-insensitive), suggesting a deliberately incomplete test model. "
          f"{C['combinations_with_fixture_path']} of the {C['combinations_unmatched']} combinations occur in such "
          f"a file; with those files excluded: "
          f"{_np(C['combinations_unmatched_nonfixture'], C['combinations_known_nonfixture'], C['combinations_unmatched_nonfixture_pct'])}"
          " combinations.", ""]
    L += _by_both(res, ["inputs with a declared value no entry can match (n/known)", "... of them in fixture-like paths",
                        "fixture-like paths excluded (n/known)"],
                  lambda v: [_np(v["string"]["with_unmatched_value"], v["string"]["unmatched_known"],
                                 v["string"]["with_unmatched_value_pct"]),
                             str(v["unmatched_fixture_path"]),
                             _np(v["with_unmatched_value_nonfixture"], v["unmatched_known_nonfixture"],
                                 v["with_unmatched_value_nonfixture_pct"])])
    L += ["", "## Source repositories per kind", "",
          "Distinct sources (repositories, plus the two local analyser fixture sets) contributing to each kind. "
          "A file found in several sources is credited to the one it was kept in. Forks count separately "
          "(Camunda 7 / Operaton, dmn-js / its verifier fork).", ""]
    L += _by_both(res, ["sources with files", "with decision tables", "with string inputs"],
                  lambda v: [str(v["sources_files"]), str(v["sources_tables"]), str(v["sources_string_inputs"])])
    L += [""]
    return L


def summary_md(res, sources, missing):
    S, U = res["summary"], res["summary_unique_tables"]
    a, au = S["all"], U["all"]
    L = ["# Domain declarations of decision-table inputs in public DMN models", "",
         "Generated by `run_dmn_corpus.py` (`latc_check/dmn_corpus.py`). Question: when a decision table's "
         "string inputs do not declare their allowed values, Drools skips gap analysis and observed-domain "
         "tools (dmn-js verifier) build the domain from the values the rules mention, so a value no rule "
         "mentions is never reported missing. How often do real, public DMN models declare those domains?", "",
         "## Corpus", "",
         f"{len(sources)} sources (shallow, sparse clones of public repositories, `.dmn` files only, at the "
         "commits listed under Sources; plus two analyser fixture sets from the earlier tool audit). "
         f"{sum(s['dmn_files_in_checkout'] for s in sources)} `.dmn` files were found, "
         f"{a['files']} distinct by SHA-256 of their bytes "
         f"(duplicates dropped, by kind: {json.dumps(res['duplicates_dropped_by_kind'])}; a file present in "
         "several places is kept once, in the kind of highest priority TCK > example > product test > "
         f"analyser > other). {a['parse_errors']} distinct files are not analysed (malformed XML, or not in a DMN "
         "model namespace; mostly deliberate negative test fixtures). "
         f"{a['decision_tables']} decision tables were found in {a['files_with_tables']} files.", "",
         "Many tables recur in several files with different bytes (versions of the same TCK case, the same "
         "example copied into several example projects, Camunda 7 and its fork Operaton). The second set of "
         "numbers counts each distinct table content (hit policy, input expressions and typeRefs, every "
         "declaration text, every input and output entry) once: "
         f"{au['decision_tables']} distinct tables.", "",
         "Kinds: *examples / tutorials* = example, tutorial, demo and showcase repositories, and example "
         "folders of product repositories outside test folders; *product test resources* = test resources of "
         "engines, editors and libraries (Drools, Kogito, Camunda 7/8, Operaton, Flowable, dmn-js, jDMN, dsntk, "
         "...); *conformance (TCK)* = the DMN TCK and TCK copies inside other repositories (`tck`, `TestCases`, "
         "`compliance-level-N`, `compatibility` folders); *analyser fixtures* = fixtures of verifiers / "
         "validators / linters (red6/dmn-check, Drools `kie-dmn-validation` tests, the dmn-js verifier fork, "
         "the Corea/Blatt/Delfmann verifier); *product, non-test* = remaining files of product repositories.", "",
         "## Measures", "",
         "Per decision-table input clause. *String input*: the inputExpression typeRef resolves, through "
         "itemDefinition chains, to `string`; inputs without a usable typeRef are typed from the variable they "
         "name, else from their entries (all string literals). *inputValues*: the input has a non-empty "
         "`inputValues`. *Reachable allowedValues*: an itemDefinition reachable from the inputExpression typeRef "
         "(directly or through a typeRef chain) or from the inputData / decision variable the expression names "
         "(also through itemComponents for `A.b` paths) has `allowedValues` (DMN 1.5 `typeConstraint` counts). "
         "*Usable by Drools*: `inputValues`, or `allowedValues` on the itemDefinition named by the "
         "inputExpression typeRef (the declarations Drools used for gap analysis in `results/drools/domains`; "
         "allowedValues reachable only through the inputData variable were ignored by Drools there, and a "
         "chain of several itemDefinitions was not tested, so neither is counted). *Declared value no rule "
         "mentions*: among inputs whose declaration is a list of string literals, some declared value appears in "
         "no input entry of the column (`not(...)` included): exactly a value an observed-domain tool "
         "cannot know. *No entry can match*: stronger; every entry of the column is a literal list or `not` of "
         "one, none is `-`, and none admits the value, so every state with that value is a gap, and an "
         "observed-domain tool misses all of them (columns with non-literal entries are left out of this ratio; "
         "counts in brackets).", "",
         "## String inputs, by kind (distinct files)", ""] + _headline(S) + [
         "", "## String inputs, by kind (distinct table contents)", ""] + _headline(U) + [
         "", "## Boolean and numeric inputs (distinct files)", ""] + _other_types(S) + [
         "", "Booleans have a fixed domain (true, false), so a missing declaration hides no value; a numeric "
         "input without a declaration is an unbounded interval. Both are listed for comparison only.", ""]
    st = a["string"]
    L += ["## Where the declaration sits (string inputs, distinct files)", "",
          f"With inputValues: {st['input_values']}; allowedValues reachable but no inputValues: "
          f"{st['allowed_only']}; declared only through the inputData / decision variable (not usable by "
          f"Drools): {st['variable_only']} ({_f(st['variable_only_pct'])}% of string inputs); no declaration: "
          f"{st['none']} ({_f(st['none_pct'])}%). Undeclared string inputs whose column mentions no string "
          f"literal at all (only `-` or expressions): {st['undeclared_no_literals']}.", "",
          "## Tables with no declaration", "",
          f"{a['tables_no_string_declared']} of {a['tables_with_string_inputs']} tables with string inputs "
          f"({_f(a['tables_no_string_declared_pct'])}%; distinct contents: {au['tables_no_string_declared']} of "
          f"{au['tables_with_string_inputs']}, {_f(au['tables_no_string_declared_pct'])}%) declare no string "
          "domain at all. How many states a declared domain would add to them is **not computable**: the "
          "allowed values missing from the rules are, by construction, written nowhere in the model.", ""]
    ex, nfp, ncol = notable(res)
    L += ["## Declared values that no rule entry can match", "",
          f"{nfp} distinct tables have a string input with a declared value that no entry of its column can "
          f"match (no `-`, no admitting `not(...)`); {ncol} distinct (input, declaration, unmatched values) "
          "combinations. Up to 25, examples first, one per combination:", "",
          "| kind | source | file | table | input | declared values no entry matches | declared (where) "
          "| rule values outside the declaration |",
          "|---|---|---|---|---|---|---|---|"]
    for r in ex:
        L.append(f"| {r['kind']} | {r['source']} | `{r['path']}` | {r['table']} | {r['label']} "
                 f"| {', '.join(r['unmatched_declared'])} | {len(r['declared_values'])} ({r['declared_source']}) "
                 f"| {', '.join(r['outside_declared']) or '-'} |")
    L += [""] + _referee_sections(res)
    L += ["## Hit policies (distinct files)", "", json.dumps(a["hit_policies"]), "",
          "## Sources", "", "| source | role | commit | .dmn files in checkout | distinct files kept | tables |",
          "|---|---|---|---|---|---|"]
    for s in sources:
        ps = res["per_source"].get(s["name"], {})
        L.append(f"| [{s['name']}]({s['url']}) | {s['role']} | `{(s.get('sha') or '?')[:12]}` "
                 f"| {s['dmn_files_in_checkout']} | {ps.get('unique_files', 0)} | {ps.get('tables', 0)} |")
    if missing:
        L += ["", "Not found locally: " + ", ".join(missing)]
    L += ["", "## Caveats", "",
          "* Selection bias: public repositories are dominated by engine test suites, conformance tests and "
          "small demos; production business models are rarely public. Test resources exercise features "
          "(often the declaration features themselves), so their declaration rates say little about business "
          "practice. The examples / tutorials row is the closest proxy, and it is small "
          f"({S.get('example', {}).get('files', 0)} files, "
          f"{S.get('example', {}).get('string', {}).get('inputs', 0)} string inputs) and concentrated in a few "
          "repositories.",
          "* Repositories were found from the candidate list, the `dmn` GitHub topic (repository search, not "
          "code search) and the repositories' READMEs; only each default branch's HEAD was taken.",
          "* Duplicates are removed by bytes and, in the second table, by table content; near-duplicates with "
          "small edits remain.",
          "* Typing is static: typeRefs naming imported models' types are not resolved (counted as `unknown`), "
          "and FEEL is not evaluated. A declaration that is not a list of string literals counts as declared "
          "but is left out of the unused-value measures.",
          "* *Usable by Drools* follows the variants tested in `results/drools/domains`; other tools differ "
          "(the dmn-js verifier reads only the rules' values in any case).",
          ""]
    return "\n".join(L)
