"""Does the Drools DMN validator fall into the observed-domain trap?

The experiment of ``run_drools_domains.py``.  A table T0 drops every row
with one value v of one attribute A (the "unobserved declared value" case), so
the missing states are exactly the states with A = v.  T0 is written as DMN
point rules in several variants that differ only in where, if anywhere, the
string inputs' allowed values are declared:

V1  ``inputValues`` on every decision-table input, with the full declared
    values (what ``dmn.to_dmn_xml`` writes).
V2  no declaration at all: plain ``typeRef="string"``, no ``inputValues``, no
    ``itemDefinition``.
V3a an ``itemDefinition`` per input with the full values as ``allowedValues``,
    referenced only by the ``inputData`` variable; the decision table's
    ``inputExpression`` keeps ``typeRef="string"``; no ``inputValues``.
V3b the same ``itemDefinition``s, referenced by the ``inputData`` variable
    and by the ``inputExpression``; no ``inputValues``.
V4  ``inputValues`` with only the values T0 mentions (a declaration derived
    from the data, i.e. the observed domain written down).
V5  ``inputValues`` with the full values on every input except A, which has
    no declaration.
V6  precedence: ``inputValues`` with the observed values, ``inputExpression``
    typed by an ``itemDefinition`` with the full values.
V7  precedence: ``inputValues`` with the full values, ``inputExpression``
    typed by an ``itemDefinition`` with the observed values.

Drools' gap messages are parsed with ``drools_compare.parse_messages`` and
evaluated on the full declared product (X-1 of ``drools_compare``: a string
range is read over the declared values).  The message Drools emits when it
skips gap analysis for string columns without enumerated values is parsed by
``gap_skip_columns``.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from itertools import product

from .dmn import DMN14_NS, DMNTable, from_exact, to_dmn_xml
from .drools_compare import GAP_RE, parse_messages, predicate, split_top
from .model import DecisionTable

VARIANTS = {
    "V1": "inputValues = full declared values (all inputs)",
    "V2": "no allowed values declared (typeRef string only)",
    "V3a": "itemDefinition allowedValues (full) on inputData variable only; inputExpression typeRef string",
    "V3b": "itemDefinition allowedValues (full) on inputData variable and inputExpression typeRef",
    "V4": "inputValues = values observed in T0",
    "V5": "inputValues = full values on all inputs except the removed attribute (none there)",
    "V6": "inputValues = observed values; inputExpression typeRef = itemDefinition with full values",
    "V7": "inputValues = full values; inputExpression typeRef = itemDefinition with observed values",
}
CORE_VARIANTS = ("V1", "V2", "V3a", "V3b", "V4", "V5")

SKIP_COLUMNS_RE = re.compile(
    r"Columns: \[(.*?)\] relate to FEEL string values which can be enumerated for the inputs; "
    r"Gap analysis skipped")


def gap_skip_columns(msg: str):
    """Columns named in Drools' 'string values ... Gap analysis skipped' message, else None."""
    m = SKIP_COLUMNS_RE.search(msg)
    if not m:
        return None
    return [c.strip() for c in m.group(1).split(",") if c.strip()]


# -- cases ------------------------------------------------------------------------

def removal_cases(full: DecisionTable, attributes=None):
    """[(attribute, value, T0)]: T0 = full minus every row with attribute = value."""
    out = []
    for j, a in enumerate(full.attributes):
        if attributes is not None and a.name not in attributes:
            continue
        for v in a.domain:
            out.append((a.name, v, full.with_rows([r for r in full.rows if r.condition[j] != v])))
    return out


def missing_states(t0: DecisionTable) -> set:
    have = {r.condition for r in t0.rows}
    return {c for c in product(*(a.domain for a in t0.attributes)) if c not in have}


# -- export -----------------------------------------------------------------------

def _q(tag: str) -> str:
    return f"{{{DMN14_NS}}}{tag}"


def _feel_list(values) -> str:
    return ",".join('"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"' for v in values)


def _type_name(k: int, kind: str) -> str:
    return f"t_input_{k}_{kind}"


def export_variant(table: DMNTable, name: str, variant: str, removed: str | None = None,
                   observed: dict | None = None) -> str:
    """DMN 1.4 XML of ``table`` (enumerated string inputs) in one of ``VARIANTS``.

    ``table`` carries the full declared values; ``observed`` maps input name to
    the values T0 mentions (V4, V6, V7); ``removed`` names attribute A (V5).
    """
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    if any(i.numeric for i in table.inputs):
        raise ValueError("only enumerated (string) inputs are supported")
    observed = observed or {}
    ET.register_namespace("", DMN14_NS)
    defs = ET.fromstring(to_dmn_xml(table, name))
    dt = defs.find(f".//{_q('decisionTable')}")
    items = []  # (type name, values)

    def item(k: int, kind: str, values) -> str:
        tn = _type_name(k, kind)
        items.append((tn, values))
        return tn

    for k, inp in enumerate(table.inputs):
        el = dt.find(f"{_q('input')}[@id='input_{k}']")
        expr = el.find(_q("inputExpression"))
        iv = el.find(_q("inputValues"))
        var = defs.find(f".//{_q('variable')}[@id='input_data_{k}_variable']")
        obs = tuple(v for v in inp.values if v in set(observed.get(inp.name, inp.values)))
        if variant in ("V2", "V3a", "V3b") or (variant == "V5" and inp.name == removed):
            el.remove(iv)
        elif variant in ("V4", "V6"):
            iv.find(_q("text")).text = _feel_list(obs)
        if variant in ("V3a", "V3b"):
            tn = item(k, "full", inp.values)
            var.set("typeRef", tn)
            if variant == "V3b":
                expr.set("typeRef", tn)
        elif variant == "V6":
            expr.set("typeRef", item(k, "full", inp.values))
        elif variant == "V7":
            expr.set("typeRef", item(k, "observed", obs))
    # itemDefinition precedes the DRG elements in the schema.
    for pos, (tn, values) in enumerate(items):
        it = ET.Element(_q("itemDefinition"), id=tn, name=tn)
        ET.SubElement(it, _q("typeRef")).text = "string"
        av = ET.SubElement(it, _q("allowedValues"), id=f"{tn}_av")
        ET.SubElement(av, _q("text")).text = _feel_list(values)
        defs.insert(pos, it)
    ET.indent(defs)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(defs, encoding="unicode")


def observed_values(t0: DecisionTable) -> dict:
    return {a.name: tuple(dict.fromkeys(r.condition[j] for r in t0.rows))
            for j, a in enumerate(t0.attributes)}


# -- Drools -----------------------------------------------------------------------

def run_one(path: str, driver_dir: str, java: str, timeout: float | None = None) -> tuple[str, float, str]:
    """Run the driver on one file in its own JVM: (stdout, seconds, error text)."""
    cp = os.pathsep.join([os.path.join(driver_dir, "out"), os.path.join(driver_dir, "lib", "*")])
    t0 = time.perf_counter()
    try:
        done = subprocess.run([java, "-cp", cp, "DroolsCheck", path], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return "", time.perf_counter() - t0, f"timeout after {timeout} s"
    err = "" if done.returncode == 0 else f"exit {done.returncode}: {done.stderr[-500:]}"
    return done.stdout, time.perf_counter() - t0, err


def effective_domains(table: DMNTable, variant: str, removed: str | None = None,
                      observed: dict | None = None) -> list:
    """Per input, the values Drools has for gap analysis in ``variant`` (None: no declaration).

    Read from the probes and from V6 / V7: Drools uses ``inputValues`` when present, else the
    ``allowedValues`` of the ``itemDefinition`` named by the ``inputExpression`` typeRef; the
    ``inputData`` variable's type is not used.  A wildcard "-" in a gap message and a string
    range are read over these values (X-1 of ``drools_compare``), not over the full declaration.
    """
    observed = observed or {}
    out = []
    for inp in table.inputs:
        obs = tuple(v for v in inp.values if v in set(observed.get(inp.name, inp.values)))
        if variant in ("V2", "V3a") or (variant == "V5" and inp.name == removed):
            out.append(None)
        elif variant in ("V4", "V6"):
            out.append(obs)
        else:
            out.append(tuple(inp.values))
    return out


def gap_tokens(stdout: str) -> list:
    """The value tokens of every 'Gap detected' message, in order."""
    return [split_top(m.group(1)) for m in map(GAP_RE.search, stdout.splitlines()) if m]


def evaluate(stdout: str, attrs, missing: set, domains: list | None = None,
             removed_index: int | None = None, removed_value=None) -> dict:
    """Drools' messages for one file against the expected missing states.

    ``domains`` (from ``effective_domains``) restricts each gap to the values Drools
    analysed; without it (or for a None entry) a token is read over the full declared values.
    ``missing_covered_full_wildcard`` reads "-" as every declared value instead, an upper
    bound that credits a gap with values Drools never saw.
    """
    parsed = parse_messages(stdout)
    if not parsed:
        return {"outcome": "error", "detail": "no output block"}
    f = next(iter(parsed.values()))
    msgs = [ln.split("	", 2)[2] for ln in stdout.splitlines() if ln.count("	") >= 2]
    skip_cols = next((c for c in map(gap_skip_columns, msgs) if c is not None), None)
    toks = gap_tokens(stdout)
    doms = [set(d) if d is not None else set(a.domain)
            for a, d in zip(attrs, domains or [None] * len(attrs))]
    grid = list(product(*(a.domain for a in attrs)))

    def cover(full_wildcard: bool) -> set:
        gaps = [[(t.strip() == "-", predicate(t)) for t in g] for g in toks]
        return {x for x in grid if any(all((wild and full_wildcard) or (v in dom and p(v))
                                           for (wild, p), v, dom in zip(g, x, doms)) for g in gaps)}

    covered, covered_full = cover(False), cover(True)
    if f["errors"]:
        outcome = "error"
    elif skip_cols is not None:
        outcome = "gap analysis skipped"
    elif f["skipped"]:
        outcome = "analysis skipped"
    elif toks:
        outcome = "gaps reported"
    else:
        outcome = "no gaps reported"
    res = {"outcome": outcome, "gap_messages": len(toks),
           "states_covered_by_gaps": len(covered), "missing_covered": len(covered & missing),
           "covered_not_missing": len(covered - missing),
           "missing_covered_full_wildcard": len(covered_full & missing),
           "gap_skip_columns": skip_cols, "message_types": sorted({k for _, k in f["raw"]}),
           "messages": len(f["raw"]), "errors": f["errors"][:3],
           "skip_message": next((m.split(" (DMN id")[0] for m in msgs
                                 if gap_skip_columns(m) is not None), None),
           "gaps_first": [", ".join(g) for g in toks[:5]]}
    if removed_index is not None:
        res["removed_value_states_found"] = sum(1 for x in covered & missing
                                                if x[removed_index] == removed_value)
    return res


def dmn_of(t0: DecisionTable) -> DMNTable:
    """T0 as UNIQUE point rules over the full declared values."""
    return from_exact(t0, values="declared")
