"""Run the Apache KIE (Drools) 10.x DMN validator on the shared domain-test inputs.

Reuses the 7.74.1 parser and evaluation (latc_check.drools_compare / drools_domains:
gap_tokens, evaluate) on results/tools/inputs/*.dmn, and compares each file with the
Drools 7.74.1 result for the same case and variant (results/drools/domains/results.json).

Run from anywhere with the isolated interpreter:
    python -I results/tools/kie10/run_kie10.py [--only SUBSTR ...] [--timeout-nursery-v1 900]

Environment: KIE10_HOME (default C:/Users/crussell/Downloads/repos/tools/kie10) holding
jdk17/, lib/ (mvn dependency:copy-dependencies of pom.xml) and out/ (compiled DroolsCheck).
Writes results.json and raw/<file>.txt next to this script; resumes from results.json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from itertools import product
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

from latc_check.drools_compare import split_top  # noqa: E402
from latc_check.drools_domains import evaluate, gap_tokens  # noqa: E402,F401

KIE10 = os.environ.get("KIE10_HOME", r"C:\Users\crussell\Downloads\repos\tools\kie10")
JAVA = os.path.join(KIE10, "jdk17", "bin", "java.exe")
CP = os.pathsep.join([os.path.join(KIE10, "out"), os.path.join(KIE10, "lib", "*")])
NS = "{https://www.omg.org/spec/DMN/20211108/MODEL/}"
INPUTS = os.path.join(ROOT, "results", "tools", "inputs")
OLD = os.path.join(ROOT, "results", "drools", "domains", "results.json")
OUT = os.path.join(HERE, "results.json")
RAW = os.path.join(HERE, "raw")


def unq(s: str) -> str:
    s = s.strip()
    return s[1:-1] if s.startswith('"') and s.endswith('"') else s


def read_rules(path: str, attrs: list) -> list:
    """Each rule as a tuple of value sets (None = '-'), in input order."""
    root = ET.parse(path).getroot()
    dt = root.find(f".//{NS}decisionTable")
    rules = []
    for r in dt.findall(f"{NS}rule"):
        cells = []
        for e in r.findall(f"{NS}inputEntry"):
            t = (e.findtext(f"{NS}text") or "").strip()
            cells.append(None if t in ("-", "") else {unq(x) for x in split_top(t)})
        rules.append(cells)
    return rules


def missing_and_observed(path: str, attrs: list):
    rules = read_rules(path, attrs)
    covered = set()
    for cells in rules:
        covered.update(product(*[(a.domain if c is None else [v for v in a.domain if v in c])
                                 for a, c in zip(attrs, cells)]))
    grid = set(product(*(a.domain for a in attrs)))
    observed = []
    for j, a in enumerate(attrs):
        seen = set()
        for cells in rules:
            seen |= set(a.domain) if cells[j] is None else cells[j]
        observed.append(tuple(v for v in a.domain if v in seen))
    return grid - covered, observed


def run(path: str, timeout: float | None):
    t0 = time.perf_counter()
    try:
        done = subprocess.run([JAVA, "-Xmx1200m", "-cp", CP, "DroolsCheck", path], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return "", time.perf_counter() - t0, f"timeout after {timeout} s (killed)"
    err = "" if done.returncode == 0 else f"exit {done.returncode}: {done.stderr[-800:]}"
    return done.stdout, time.perf_counter() - t0, err


def old_result(old: dict, case: dict, variant: str):
    for c in old["cases"]:
        if (c["dataset"], c["attribute"], c["value"]) == (case["dataset"], case["attribute"],
                                                          case["removed_value"]):
            return c["drools"].get(variant)
    return None


def same_as_old(new: dict, prev: dict | None):
    if prev is None:
        return None
    keys = ("outcome", "gap_messages", "states_covered_by_gaps", "missing_covered", "covered_not_missing",
            "removed_value_states_found", "gap_skip_columns", "message_types")
    diffs = {k: (prev.get(k), new.get(k)) for k in keys if prev.get(k) != new.get(k)}
    if prev.get("gaps_first") != new.get("gaps_first"):
        diffs["gaps_first"] = "differs"
    return {"same": not diffs, "differences": diffs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="substrings of file names to run")
    ap.add_argument("--timeout", type=float, default=1800)
    ap.add_argument("--timeout-nursery-v1", type=float, default=900)
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()

    manifest = json.load(open(os.path.join(INPUTS, "manifest.json"), encoding="utf-8"))
    old = json.load(open(OLD, encoding="utf-8"))
    res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    res.setdefault("tool", "Apache KIE (Drools) DMN validator 10.2.0 (org.kie:kie-dmn-validation, "
                           "kie-dmn-core), Eclipse Temurin 17.0.20.1+1, -Xmx1200m; driver DroolsCheck.java "
                           "(VALIDATE_SCHEMA, VALIDATE_MODEL, ANALYZE_DECISION_TABLE)")
    res.setdefault("compared_with", "Drools 7.74.1.Final on Java 8, results/drools/domains/results.json")
    res.setdefault("variants", manifest["variants"])
    res.setdefault("runs", {})
    os.makedirs(RAW, exist_ok=True)

    plan = []
    for case in manifest["cases"]:
        for variant, rel in case["files"].items():
            name = os.path.basename(rel)
            if case["dataset"] == "nursery" and variant not in ("V2", "V1"):
                continue
            plan.append((case, variant, name))
    # nursery V1 last
    plan.sort(key=lambda p: (p[0]["dataset"] == "nursery", p[1] == "V1" and p[0]["dataset"] == "nursery"))

    for case, variant, name in plan:
        if args.only and not any(s in name for s in args.only):
            continue
        if name in res["runs"] and not args.rerun:
            continue
        path = os.path.join(INPUTS, name)
        attrs = [SimpleNamespace(name=a, domain=tuple(case["declared_domains"][a])) for a in case["attributes"]]
        missing, observed = missing_and_observed(path, attrs)
        domains = {"V1": [a.domain for a in attrs], "V3b": [a.domain for a in attrs],
                   "V2": [None] * len(attrs), "V4": observed}[variant]
        timeout = args.timeout_nursery_v1 if (case["dataset"] == "nursery" and variant == "V1") else args.timeout
        print(f"running {name} ...", flush=True)
        stdout, secs, err = run(path, timeout)
        with open(os.path.join(RAW, name + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(stdout + ("\n# ERROR: " + err if err else ""))
        ridx = case["attributes"].index(case["attribute"])
        if err and not stdout.strip():
            ev = {"outcome": "error" if "timeout" not in err else "not finished (timeout)", "detail": err}
        else:
            ev = evaluate(stdout, attrs, missing, domains, ridx, case["removed_value"])
            if err:
                ev["detail"] = err
        ev["seconds"] = round(secs, 1)
        ev["missing_states"] = len(missing)
        ev["missing_with_removed_value"] = sum(1 for x in missing if x[ridx] == case["removed_value"])
        prev = old_result(old, case, variant)
        ev["drools_7_74_1"] = None if prev is None else {k: prev.get(k) for k in (
            "outcome", "gap_messages", "states_covered_by_gaps", "missing_covered", "covered_not_missing",
            "removed_value_states_found", "message_types", "seconds")}
        ev["vs_7_74_1"] = same_as_old(ev, prev)
        ev.update({"dataset": case["dataset"], "attribute": case["attribute"],
                   "removed_value": case["removed_value"], "variant": variant, "rules": case["rules"]})
        assert ev["missing_states"] == case["missing_states"], (name, ev["missing_states"])
        res["runs"][name] = ev
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
        print(f"  {ev['outcome']}  covered {ev.get('missing_covered')}/{len(missing)}  "
              f"removed-value {ev.get('removed_value_states_found')}  {ev['seconds']} s  "
              f"same-as-7.74.1={None if ev['vs_7_74_1'] is None else ev['vs_7_74_1']['same']}", flush=True)


if __name__ == "__main__":
    main()
