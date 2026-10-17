"""Compare the DMN analysis with an external engine: Drools (KIE) DMN validator.

Drools' decision-table analysis (``Validation.ANALYZE_DECISION_TABLE``) reports
gaps, overlaps under UNIQUE / ANY, masked rules under PRIORITY / FIRST, and
other findings (subsumption, contraction, normal-form violations) as text
messages.  This module exports tables as DMN 1.4 XML, runs the Java driver in
``tools/drools`` on them, parses the messages, and compares them with the
exhaustive oracle of ``dmn_oracle`` on the oracle's grid.

Interpretive choices (X-1 .. X-4):

X-1  Drools orders string values lexicographically and may report a string gap
     or overlap as a range [ "b" .. "d" ]; a range is read as every declared
     value v with lo <= v <= hi (closedness from the brackets).
X-2  Overlap messages list a set of rules and one witness box.  We compare the
     set of overlapping rule *pairs*: every pair inside a reported set.
X-3  Masking messages "Rule a is masked by rule: b" are compared with
     ``violations``' masked pairs.  When Drools skips the PRIORITY / FIRST
     analysis (it does for rules with multi-valued entries), the table is
     counted as "skipped by Drools", not as a disagreement.
X-4  Rules are numbered from 1 in Drools and from 0 here.
"""

from __future__ import annotations

import os
import random
import re
import subprocess
from itertools import combinations, product

from . import dmn_oracle
from .dmn import DMNTable, Not, analyse, to_dmn_xml, violations

GAP_RE = re.compile(r"Gap detected: \[(.*)\] \(DMN id")
OVERLAP_RE = re.compile(r"Overlap detected: Overlap values: \[(.*)\] for rules: \[([0-9, ]+)\]")
MASK_RE = re.compile(r"Rule (\d+) is masked by rule: (\d+)")
SKIP_RE = re.compile(r"Skipped Decision Table Analysis")


def split_top(s: str) -> list:
    """Split a Drools value list on commas that are outside brackets and quotes."""
    out, depth, quote, cur = [], 0, False, ""
    for ch in s:
        if ch == '"':
            quote = not quote
        elif not quote and ch in "[(":
            depth += 1
        elif not quote and ch in "])":
            depth -= 1
        if ch == "," and depth == 0 and not quote:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _atom(tok: str):
    tok = tok.strip()
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1]
    return float(tok)


def predicate(tok: str):
    """A Drools value expression -> function value -> bool."""
    tok = tok.strip()
    if tok == "-":
        return lambda x: True
    m = re.fullmatch(r"([\[(])\s*(.+?)\s*\.\.\s*(.+?)\s*([\])])", tok)
    if m:
        lo, hi = _atom(m.group(2)), _atom(m.group(3))
        lc, hc = m.group(1) == "[", m.group(4) == "]"
        return lambda x: (x > lo or (lc and x == lo)) and (x < hi or (hc and x == hi))
    m = re.fullmatch(r"(<=|>=|<|>|=)\s*(.+)", tok)
    if m:
        op, v = m.group(1), _atom(m.group(2))
        return {"<": lambda x: x < v, "<=": lambda x: x <= v, ">": lambda x: x > v,
                ">=": lambda x: x >= v, "=": lambda x: x == v}[op]
    v = _atom(tok)
    return lambda x: x == v


def parse_messages(text: str) -> dict:
    """Driver output -> {path: {"gaps": [...], "overlaps": [...], "masked": [...], "skipped": bool, "raw": [...]}}."""
    res, cur = {}, None
    for line in text.splitlines():
        if line.startswith("=== "):
            path = line[4:].rsplit(" : ", 1)[0]
            cur = res.setdefault(path, {"gaps": [], "overlaps": [], "masked": [], "skipped": False,
                                        "errors": [], "raw": []})
            continue
        if cur is None or "\t" not in line:
            continue
        level, kind, msg = (line.split("\t", 2) + ["", ""])[:3]
        cur["raw"].append((level, kind))
        if level == "ERROR" and not kind.startswith("DECISION_TABLE"):
            cur["errors"].append(msg)
        if (m := GAP_RE.search(msg)):
            cur["gaps"].append([predicate(t) for t in split_top(m.group(1))])
        elif (m := OVERLAP_RE.search(msg)):
            rules = sorted(int(r) - 1 for r in m.group(2).split(","))
            cur["overlaps"].append(rules)
        elif (m := MASK_RE.search(msg)):
            cur["masked"].append((int(m.group(1)) - 1, int(m.group(2)) - 1))
        elif SKIP_RE.search(msg):
            cur["skipped"] = True
    return res


def run_drools(paths: list, driver_dir: str, java: str) -> str:
    """Run the Java driver on DMN files; returns its stdout."""
    cp = os.pathsep.join([os.path.join(driver_dir, "out"), os.path.join(driver_dir, "lib", "*")])
    out = []
    for i in range(0, len(paths), 100):  # keep the Windows command line short
        done = subprocess.run([java, "-cp", cp, "DroolsCheck", *paths[i:i + 100]], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", check=True)
        out.append(done.stdout)
    return "\n".join(out)


def compare(table: DMNTable, found: dict) -> dict:
    """Drools' findings against the exhaustive oracle on the oracle's grid."""
    o = dmn_oracle.oracle(table)
    points = list(product(*(dmn_oracle.grid(i) for i in table.inputs)))
    in_gaps = sorted(x for x in points if any(all(p(v) for p, v in zip(g, x)) for g in found["gaps"]))
    res = {"gaps": in_gaps == o["uncovered"]}
    if table.hit_policy == "UNIQUE":
        pairs = sorted({p for s in found["overlaps"] for p in combinations(s, 2)})
        res["overlap_pairs"] = pairs == o["pairs"]
    elif table.hit_policy == "PRIORITY" and not found["skipped"]:
        res["masked"] = sorted(set(found["masked"])) == o["masked"]
    return res


def has_negation(table: DMNTable) -> bool:
    return any(isinstance(e, Not) for r in table.rules for e in r.entries)


def batch(n: int, seed: int, work_dir: str, driver_dir: str, java: str) -> dict:
    """Export n random oracle tables, run Drools once, compare each."""
    rng = random.Random(seed)
    os.makedirs(work_dir, exist_ok=True)
    tables, paths = [], []
    for k in range(n):
        t = dmn_oracle.random_table(rng)
        p = os.path.join(work_dir, f"t{k:04d}.dmn")
        with open(p, "w", encoding="utf-8") as f:
            f.write(to_dmn_xml(t, f"t{k:04d}"))
        tables.append(t)
        paths.append(p)
    found = parse_messages(run_drools(paths, driver_dir, java))
    by_path = {os.path.normcase(os.path.abspath(k)): v for k, v in found.items()}
    groups = {"without negation": {}, "with negation": {}}
    disagreements, skipped, errors = [], 0, 0
    for k, (t, p) in enumerate(zip(tables, paths)):
        f = by_path.get(os.path.normcase(os.path.abspath(p)))
        if f is None:
            errors += 1
            continue
        errors += bool(f["errors"])
        skipped += f["skipped"]
        res = compare(t, f)
        g = groups["with negation" if has_negation(t) else "without negation"]
        g["tables"] = g.get("tables", 0) + 1
        for key, ok in res.items():
            g.setdefault(key, [0, 0])
            g[key][0] += ok
            g[key][1] += 1
        if not all(res.values()) and len(disagreements) < 10:
            ours = violations(t, analyse(t))
            disagreements.append({"table": k, "policy": t.hit_policy, "negation": has_negation(t),
                                  "result": res, "drools_overlaps": f["overlaps"],
                                  "drools_masked": f["masked"], "ours_masked": ours["masked_pairs"]})
    return {"tables": n, "seed": seed, "agree_of_total": groups,
            "drools_skipped_priority_analysis": skipped, "tables_with_errors": errors,
            "disagreements": disagreements}
