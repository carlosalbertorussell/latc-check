"""Import decision tables from DMN XML (DMN 1.1 to 1.5) into ``dmn.DMNTable``.

Only the FEEL subset that ``dmn`` models is accepted; everything else is
*skipped with a reason*, never guessed.  The files are parsed as data with
``xml.etree.ElementTree``; documents with a DOCTYPE are refused (no entity
expansion), and nothing in them is evaluated.

Accepted
--------
* hit policies UNIQUE (the default), ANY, FIRST, PRIORITY; one output column;
* input types ``string`` and ``number`` (also through an ``itemDefinition``
  whose base type is one of them, and ``feel:`` prefixes).  An input without a
  ``typeRef`` is typed from its literals when they are all strings or all
  numeric tests;
* input entries: ``-``; string literals and lists of them (``"a","b"``);
  number literals; comparisons ``< <= > >= =`` with a number; intervals
  ``[a..b]``, ``(a..b)``, ``[a..b)``, ``(a..b]`` and the DMN 1.1 forms
  ``]a..b[`` etc.; ``not(...)`` of any of these.

Domains (I-D1 .. I-D3)
----------------------
I-D1  A string input's domain is its ``inputValues``, else the
      ``allowedValues`` of its item definition.  With neither, the domain is
      open: the values the rules mention plus one sentinel ``OTHER`` that
      stands for every other string, so a table without a ``-`` row for that
      input shows a gap there (the string analogue of an unbounded number).
I-D2  A numeric input's domain is the interval of its ``inputValues`` (or
      item-definition ``allowedValues``), else unbounded (-inf, inf).
I-D3  Booleans are not in the modelled subset and are skipped by default.
      ``booleans="enum"`` treats them as the enumeration (true, false); that
      variant is reported separately as a sensitivity count.

Skip reasons (first one found, in this order): ``doctype``, ``hit policy
<X>``, ``multiple outputs``, ``input type <t>`` (non-string/number),
``unsupported FEEL: ...`` (in inputValues, entries or PRIORITY outputs).
"""

from __future__ import annotations

import math
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .dmn import ANY, INF, DMNTable, Input, Interval, Not, OneOf, Point, Rule

# DMN model namespaces by specification date.  DC, DI, DMNDI and FEEL share
# the date prefix but are not model namespaces.
DMN_VERSIONS = {"20151101": "1.1", "20180521": "1.2", "20191111": "1.3",
                "20211108": "1.4", "20230324": "1.5"}
_MODEL_NS = re.compile(r"^https?://www\.omg\.org/spec/DMN/(\d{8})/(MODEL/?|dmn\.xsd|DMN\d*\.xsd)$")

OTHER = "<other>"     # I-D1 sentinel: any string the rules do not mention
SUPPORTED_POLICIES = ("UNIQUE", "ANY", "FIRST", "PRIORITY")


class Unsupported(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(reason)
        self.reason, self.detail = reason, detail


def dmn_version(ns: str) -> str | None:
    m = _MODEL_NS.match(ns or "")
    return DMN_VERSIONS.get(m.group(1), f"unknown ({m.group(1)})") if m else None


def _split(tag: str) -> tuple[str, str]:
    if tag.startswith("{"):
        ns, local = tag[1:].split("}", 1)
        return ns, local
    return "", tag


# -- FEEL subset ------------------------------------------------------------------------

_NUM = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
_NUM_RE = re.compile(rf"^{_NUM}$")
_CMP_RE = re.compile(rf"^(<=|>=|<|>|=)\s*({_NUM})$")
_IVL_RE = re.compile(rf"^([\[\(\]])\s*({_NUM})\s*\.\.\s*({_NUM})\s*([\]\)\[])$")
_IVL_SCAN = re.compile(r"[\[\(\]][^,\"\[\]()]*\.\.[^,\"\[\]()]*[\]\)\[]")


def number(text: str):
    if not _NUM_RE.match(text):
        raise Unsupported("unsupported FEEL: non-literal expression", text)
    x = float(text)
    return int(x) if x.is_integer() and "." not in text else x


def split_top(text: str) -> list[str]:
    """Split at commas outside string literals, intervals and parentheses."""
    out, cur, depth, inside, esc = [], [], 0, False, False
    k = 0
    while k < len(text):
        ch = text[k]
        k += 1
        if not inside and ch in "[(]":
            m = _IVL_SCAN.match(text, k - 1)
            if m:                      # an interval: brackets need not pair up
                cur.append(m.group(0))
                k = m.end()
                continue
        if inside:
            cur.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                inside = False
            continue
        if ch == '"':
            inside = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    if inside or depth:
        raise Unsupported("unsupported FEEL: unbalanced quotes or parentheses", text)
    out.append("".join(cur).strip())
    return out


def string_literal(text: str) -> str:
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        raise Unsupported("unsupported FEEL: non-literal expression", text)
    body, out, k = text[1:-1], [], 0
    while k < len(body):
        ch = body[k]
        if ch == "\\" and k + 1 < len(body):
            out.append({"n": "\n", "t": "\t", "r": "\r"}.get(body[k + 1], body[k + 1]))
            k += 2
            continue
        if ch == '"':
            raise Unsupported("unsupported FEEL: non-literal expression", text)
        out.append(ch)
        k += 1
    return "".join(out)


def _negated(text: str) -> str | None:
    t = text.strip()
    if t.startswith("not(") and t.endswith(")"):
        inner = t[4:-1]
        try:
            split_top(inner)          # balanced inside
            return inner
        except Unsupported:
            return None
    return None


def numeric_test(text: str):
    """One numeric unary test -> Point or Interval."""
    t = text.strip()
    m = _CMP_RE.match(t)
    if m:
        op, x = m.group(1), number(m.group(2))
        return {"<": Interval(-INF, x, True, False), "<=": Interval(-INF, x, True, True),
                ">": Interval(x, INF, False, True), ">=": Interval(x, INF, True, True),
                "=": Point(x)}[op]
    m = _IVL_RE.match(t)
    if m:
        lo, hi = number(m.group(2)), number(m.group(3))
        return Interval(lo, hi, m.group(1) == "[", m.group(4) == "]")
    if _NUM_RE.match(t):
        return Point(number(t))
    if t == "null" or t.startswith("null"):
        raise Unsupported("unsupported FEEL: null", t)
    raise Unsupported("unsupported FEEL: non-literal expression", t)


def parse_entry(text: str, kind: str):
    """An input entry for an input of ``kind`` 'string', 'number' or 'boolean'."""
    t = (text or "").strip()
    if t == "-":
        return ANY
    if not t:
        raise Unsupported("unsupported FEEL: empty entry", t)
    inner = _negated(t)
    if inner is not None:
        e = parse_entry(inner, kind)
        if e is ANY:
            raise Unsupported("unsupported FEEL: not(-)", t)
        return Not(e)
    items = split_top(t)
    if kind == "number":
        if len(items) > 1:
            raise Unsupported("unsupported FEEL: numeric disjunction", t)
        return numeric_test(items[0])
    if kind == "boolean":
        vals = []
        for it in items:
            if it not in ("true", "false"):
                raise Unsupported("unsupported FEEL: non-literal expression", it)
            vals.append(it)
    else:
        vals = [string_literal(it) for it in items]
    return Point(vals[0]) if len(vals) == 1 else OneOf(frozenset(vals))


def _literal_kind(text: str) -> str | None:
    """'string' or 'number' when every item of an entry is of that kind."""
    t = (text or "").strip()
    if t == "-":
        return None
    inner = _negated(t)
    if inner is not None:
        t = inner
    try:
        items = split_top(t)
    except Unsupported:
        return "?"
    if all(len(i) >= 2 and i[0] == '"' == i[-1] for i in items):
        return "string"
    if all(_CMP_RE.match(i) or _IVL_RE.match(i) or _NUM_RE.match(i) for i in items):
        return "number"
    if all(i in ("true", "false") for i in items):
        return "boolean"
    return "?"


# -- import --------------------------------------------------------------------------

@dataclass
class ImportedTable:
    file: str
    name: str
    table_id: str
    version: str | None
    hit_policy: str
    n_inputs: int
    n_rules: int
    status: str = "parsed"            # parsed | skipped
    reason: str = ""
    reasons: list = field(default_factory=list)
    detail: str = ""
    dmn: DMNTable | None = None
    domains: list = field(default_factory=list)   # per input: (name, kind, source)

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "dmn"}
        return d


def _text(el) -> str | None:
    if el is None:
        return None
    for ch in el:
        if _split(ch.tag)[1] == "text":
            return "".join(ch.itertext())
    return None


def _child(el, local: str):
    for ch in el:
        if _split(ch.tag)[1] == local:
            return ch
    return None


def _children(el, local: str) -> list:
    return [ch for ch in el if _split(ch.tag)[1] == local]


def _item_definitions(root, ns: str) -> dict:
    """name -> (base typeRef, allowedValues text) for simple item definitions."""
    out = {}
    for el in root.iter(f"{{{ns}}}itemDefinition"):
        name = el.get("name")
        tr = _child(el, "typeRef")
        av = _child(el, "allowedValues")
        out[name] = ((tr.text or "").strip() if tr is not None else None, _text(av))
    return out


def _resolve(type_ref: str | None, items: dict, depth: int = 0) -> tuple[str | None, str | None]:
    if type_ref is None:
        return None, None
    t = type_ref.split(":", 1)[1] if type_ref.startswith("feel:") else type_ref
    if t in items and depth < 10:
        base, allowed = items[t]
        rb, ra = _resolve(base, items, depth + 1)
        return rb, allowed if allowed is not None else ra
    return t, None


def _owner_name(parents: dict, el) -> str:
    p = parents.get(el)
    while p is not None:
        if _split(p.tag)[1] in ("decision", "businessKnowledgeModel", "decisionService"):
            return p.get("name") or p.get("id") or "?"
        p = parents.get(p)
    return "?"


def _import_table(el, ns: str, version: str, items: dict, parents: dict, rel: str,
                  booleans: str) -> ImportedTable:
    hp = (el.get("hitPolicy") or "UNIQUE").strip().upper()
    in_els = _children(el, "input")
    out_els = _children(el, "output")
    rule_els = _children(el, "rule")
    it = ImportedTable(rel, _owner_name(parents, el), el.get("id") or "", version,
                       hp + (f" {el.get('aggregation')}" if el.get("aggregation") else ""),
                       len(in_els), len(rule_els))

    def fail(reason: str, detail: str = "") -> None:
        it.reasons.append(reason)
        if it.status == "parsed":
            it.status, it.reason, it.detail = "skipped", reason, detail

    if hp not in SUPPORTED_POLICIES:
        fail(f"hit policy {hp}")
    if len(out_els) != 1:
        fail("multiple outputs" if len(out_els) > 1 else "no output")

    entries = [[_text(e) for e in _children(r, "inputEntry")] for r in rule_els]
    outputs = [[_text(e) for e in _children(r, "outputEntry")] for r in rule_els]
    if any(len(e) != len(in_els) for e in entries):
        fail("rule width does not match inputs")

    kinds, doms = [], []
    for k, ie in enumerate(in_els):
        expr = _child(ie, "inputExpression")
        raw_type = expr.get("typeRef") if expr is not None else None
        base, allowed = _resolve(raw_type, items)
        iv = _text(_child(ie, "inputValues"))
        src = "inputValues" if iv is not None else ("itemDefinition" if allowed is not None else None)
        dom_text = iv if iv is not None else allowed
        if base is None:
            seen = {_literal_kind(row[k]) for row in entries if k < len(row)} - {None}
            if dom_text is not None:
                seen.add(_literal_kind(dom_text))
            if not seen:
                base = "string"     # every entry is "-": the input never constrains a rule
            else:
                base = seen.pop() if len(seen) == 1 and "?" not in seen else None
            inferred = True
        else:
            inferred = False
        if base == "boolean" and booleans == "enum":
            kinds.append("boolean")
        elif base in ("string", "number"):
            kinds.append(base)
        else:
            kinds.append(None)
            fail(f"input type {base or 'untyped'}",
                 f"input {k + 1} ({_label(ie)}): typeRef {raw_type!r}")
        doms.append((dom_text, src, inferred))

    inputs = []
    if it.status == "parsed":
        try:
            parsed = [[parse_entry(t, kinds[k]) for k, t in enumerate(row)] for row in entries]
        except Unsupported as u:
            fail(u.reason, u.detail)
    if it.status == "parsed":
        for k, ie in enumerate(in_els):
            dom_text, src, inferred = doms[k]
            name = _label(ie)
            try:
                inputs.append(_input(name, kinds[k], dom_text, [row[k] for row in parsed]))
            except Unsupported as u:
                fail(u.reason, f"inputValues of {name}: {u.detail}")
                break
            it.domains.append({"input": name, "type": kinds[k] + (" (inferred)" if inferred else ""),
                               "domain": src or ("unbounded" if kinds[k] == "number" else
                                                 "booleans" if kinds[k] == "boolean" else
                                                 "mentioned+OTHER")})
    if it.status == "parsed":
        out_el = out_els[0]
        ov_text = _text(_child(out_el, "outputValues"))
        out_texts = [(o[0] or "").strip() if o else "" for o in outputs]
        out_vals = ()
        try:
            if ov_text is not None:
                out_vals = tuple(_output_literal(x) for x in split_top(ov_text.strip()))
            labels = [_output_literal(t) if hp == "PRIORITY" else t for t in out_texts]
            if hp == "PRIORITY":
                if not out_vals:
                    raise Unsupported("unsupported FEEL: PRIORITY without outputValues")
                missing = [l for l in labels if l not in out_vals]
                if missing:
                    raise Unsupported("unsupported FEEL: PRIORITY output not in outputValues",
                                      repr(missing[0]))
        except Unsupported as u:
            fail(u.reason, u.detail)
    if it.status == "parsed":
        rules = [Rule(tuple(p), lab) for p, lab in zip(parsed, labels)]
        it.dmn = DMNTable(tuple(inputs), rules, hp, output_name=out_els[0].get("name") or "output",
                          output_values=out_vals)
    return it


def _output_literal(t: str) -> str:
    t = t.strip()
    if t.startswith('"'):
        return string_literal(t)
    if _NUM_RE.match(t):
        return t
    raise Unsupported("unsupported FEEL: non-literal output", t)


def _label(ie) -> str:
    if ie.get("label"):
        return ie.get("label")
    t = _text(_child(ie, "inputExpression"))
    return (t or ie.get("id") or "?").strip()


def _input(name: str, kind: str, dom_text: str | None, col: list) -> Input:
    if kind == "number":
        if dom_text is None:
            return Input(name, domain=Interval(-INF, INF))
        items = split_top(dom_text.strip())
        if len(items) != 1:
            raise Unsupported("unsupported FEEL: numeric disjunction", dom_text.strip())
        d = numeric_test(items[0])
        if isinstance(d, Point):
            d = Interval(d.value, d.value)
        return Input(name, domain=d)
    if kind == "boolean":
        return Input(name, values=("true", "false"))
    if dom_text is not None:
        vals = tuple(dict.fromkeys(string_literal(x) for x in split_top(dom_text.strip())))
        return Input(name, values=vals)
    mentioned = {}
    for e in col:
        e = e.entry if isinstance(e, Not) else e
        if isinstance(e, Point):
            mentioned.setdefault(e.value, None)
        elif isinstance(e, OneOf):
            for v in sorted(e.values):
                mentioned.setdefault(v, None)
    return Input(name, values=tuple(mentioned) + (OTHER,))


def import_file(path: str, root_dir: str | None = None, booleans: str = "skip") -> tuple[list, str | None]:
    """(list of ImportedTable, file-level error or None)."""
    rel = os.path.relpath(path, root_dir) if root_dir else os.path.basename(path)
    rel = rel.replace("\\", "/")
    with open(path, "rb") as f:
        data = f.read()
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        return [], "doctype"
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return [], f"XML parse error: {e}"
    ns, _ = _split(root.tag)
    parents = {c: p for p in root.iter() for c in p}
    out = []
    items_by_ns: dict = {}
    for el in root.iter():
        ens, local = _split(el.tag)
        if local != "decisionTable":
            continue
        version = dmn_version(ens)
        if version is None:
            continue
        if ens not in items_by_ns:
            items_by_ns[ens] = _item_definitions(root, ens)
        out.append(_import_table(el, ens, version, items_by_ns[ens], parents, rel, booleans))
    return out, None


def import_tree(root_dir: str, booleans: str = "skip") -> dict:
    """Every .dmn file under ``root_dir``: tables found, parsed or skipped."""
    files, tables, file_errors = [], [], {}
    for dp, dn, fn in os.walk(root_dir):
        dn[:] = sorted(d for d in dn if d != ".git")
        for f in sorted(fn):
            if f.lower().endswith(".dmn"):
                files.append(os.path.join(dp, f))
    for p in files:
        ts, err = import_file(p, root_dir, booleans)
        if err:
            file_errors[os.path.relpath(p, root_dir).replace("\\", "/")] = err
        tables.extend(ts)
    return {"files": len(files), "files_with_tables": len({t.file for t in tables}),
            "file_errors": file_errors, "tables": tables}


# -- finiteness for the oracle ---------------------------------------------------------

def finite_for_oracle(table: DMNTable, max_points: int = 200_000) -> tuple[bool, str]:
    """Can ``dmn_oracle`` analyse this table exhaustively?"""
    size = 1
    for d, inp in enumerate(table.inputs):
        if inp.numeric:
            dom = inp.domain
            if not (math.isfinite(dom.lo) and math.isfinite(dom.hi) and dom.lo_closed and dom.hi_closed
                    and float(dom.lo).is_integer() and float(dom.hi).is_integer()):
                return False, f"{inp.name}: domain not a closed integer range"
            for r in table.rules:
                e = r.entries[d]
                e = e.entry if isinstance(e, Not) else e
                bounds = ([e.value] if isinstance(e, Point) else
                          [e.lo, e.hi] if isinstance(e, Interval) else [])
                if any(math.isfinite(b) and not float(b).is_integer() for b in bounds):
                    return False, f"{inp.name}: non-integer entry bound"
            size *= int(2 * (dom.hi - dom.lo)) + 1
        else:
            size *= len(inp.values)
    if size > max_points:
        return False, f"grid of {size} points exceeds {max_points}"
    return True, f"grid of {size} points"
