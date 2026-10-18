"""Run the Drools 7.74.1 and Apache KIE 10.2.0 DMN validators on results/tools/inputs/*.dmn (Linux).

Linux copy of results/tools/kie10/run_kie10.py: same parsing and evaluation
(latc_check.drools_domains: gap_tokens, evaluate), but each JVM is wrapped in
``/usr/bin/time -v`` (wall time, peak RSS) and ``timeout -s KILL`` (cap), and each result is
compared with both laptop results (results/tools/kie10/results.json for 10.2.0 and
results/drools/domains/results.json for 7.74.1).

    python3 -I results/tools/cloud-drools/run_cloud.py --tool kie10 --xmx 8g --only pension_ car_
    python3 -I results/tools/cloud-drools/run_cloud.py --tool d7 --xmx 12g --cap 7200 --only nursery_finance_convenient_V1

Environment: CLOUD_WORK (default /home/user/work) holding kie10/ and d7/, each with lib/
(mvn dependency:copy-dependencies of the pom) and out/ (compiled DroolsCheck); JAVA (default java).
Writes results.json and raw/<tool>/<file>.{txt,time} next to this script; skips runs already in
results.json unless --rerun.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results", "tools", "kie10"))

from latc_check.drools_domains import evaluate  # noqa: E402
from run_kie10 import missing_and_observed  # noqa: E402  (pure functions, no Windows paths used)

WORK = os.environ.get("CLOUD_WORK", "/home/user/work")
JAVA = os.environ.get("JAVA", "java")
INPUTS = os.path.join(ROOT, "results", "tools", "inputs")
LAPTOP_D7 = os.path.join(ROOT, "results", "drools", "domains", "results.json")
LAPTOP_KIE10 = os.path.join(ROOT, "results", "tools", "kie10", "results.json")
OUT = os.path.join(HERE, "results.json")
RAW = os.path.join(HERE, "raw")
TOOLS = {"kie10": "Apache KIE (Drools) DMN validator 10.2.0", "d7": "Drools DMN validator 7.74.1.Final"}
CMP_KEYS = ("outcome", "gap_messages", "states_covered_by_gaps", "missing_covered", "covered_not_missing",
            "removed_value_states_found", "gap_skip_columns", "message_types")


def java_version() -> str:
    p = subprocess.run([JAVA, "-version"], capture_output=True, text=True)
    lines = [ln for ln in p.stderr.splitlines() if not ln.startswith("Picked up")]
    return " / ".join(lines[:2])


def parse_time(path: str) -> dict:
    out = {}
    txt = open(path, encoding="utf-8", errors="replace").read() if os.path.exists(path) else ""
    m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (\S+)", txt)
    if m:
        parts = [float(x) for x in m.group(1).split(":")]
        out["wall_s"] = round(sum(p * 60 ** i for i, p in enumerate(reversed(parts))), 2)
    m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", txt)
    if m:
        out["peak_rss_mb"] = round(int(m.group(1)) / 1024, 1)
    m = re.search(r"Exit status: (\d+)", txt)
    if m:
        out["exit_status"] = int(m.group(1))
    m = re.search(r"Command terminated by signal (\d+)", txt)
    if m:
        out["signal"] = int(m.group(1))
    return out


def run(tool: str, path: str, xmx: str, cap: float, raw_base: str):
    d = os.path.join(WORK, tool)
    cp = os.pathsep.join([os.path.join(d, "out"), os.path.join(d, "lib", "*")])
    cmd = ["/usr/bin/time", "-v", "-o", raw_base + ".time", "timeout", "-s", "KILL", str(int(cap)),
           JAVA, f"-Xmx{xmx}", "-cp", cp, "DroolsCheck", path]
    t0 = time.perf_counter()
    done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    secs = time.perf_counter() - t0
    tm = parse_time(raw_base + ".time")
    killed = done.returncode == 137 or tm.get("exit_status") == 137 or tm.get("signal") == 9
    err = ""
    if killed:
        err = f"killed at cap {int(cap)} s"
    elif done.returncode != 0:
        err = f"exit {done.returncode}: " + "\n".join(
            ln for ln in done.stderr.splitlines() if not ln.startswith("Picked up"))[-800:]
    return done.stdout, secs, tm, killed, err


def laptop(tool: str, case: dict, variant: str, name: str, d7: dict, kie10: dict):
    if tool == "kie10":
        return kie10["runs"].get(name)
    for c in d7["cases"]:
        if (c["dataset"], c["attribute"], c["value"]) == (case["dataset"], case["attribute"],
                                                          case["removed_value"]):
            return c["drools"].get(variant)
    return None


def compare(new: dict, prev: dict | None):
    if prev is None:
        return None
    diffs = {k: [prev.get(k), new.get(k)] for k in CMP_KEYS if prev.get(k) != new.get(k)}
    if prev.get("gaps_first") is not None and prev.get("gaps_first") != new.get("gaps_first"):
        diffs["gaps_first"] = "differs"
    return {"same": not diffs, "differences": diffs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", choices=sorted(TOOLS), required=True)
    ap.add_argument("--xmx", default="8g")
    ap.add_argument("--cap", type=float, default=1800, help="kill the JVM after this many seconds")
    ap.add_argument("--only", nargs="*", default=None, help="substrings of file names to run")
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()

    manifest = json.load(open(os.path.join(INPUTS, "manifest.json"), encoding="utf-8"))
    d7 = json.load(open(LAPTOP_D7, encoding="utf-8"))
    kie10 = json.load(open(LAPTOP_KIE10, encoding="utf-8"))
    res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    res.setdefault("driver", "DroolsCheck.java (VALIDATE_SCHEMA, VALIDATE_MODEL, ANALYZE_DECISION_TABLE)")
    res.setdefault("variants", manifest["variants"])
    res.setdefault("runs", {})
    jdk = java_version()
    os.makedirs(os.path.join(RAW, args.tool), exist_ok=True)

    for case in manifest["cases"]:
        for variant, rel in case["files"].items():
            name = os.path.basename(rel)
            key = f"{args.tool}/{name}"
            if args.only and not any(s in name for s in args.only):
                continue
            if key in res["runs"] and not args.rerun:
                continue
            path = os.path.join(INPUTS, name)
            attrs = [SimpleNamespace(name=a, domain=tuple(case["declared_domains"][a])) for a in case["attributes"]]
            missing, observed = missing_and_observed(path, attrs)
            assert len(missing) == case["missing_states"], (name, len(missing), case["missing_states"])
            domains = {"V1": [a.domain for a in attrs], "V3b": [a.domain for a in attrs],
                       "V2": [None] * len(attrs), "V4": observed}[variant]
            print(f"{time.strftime('%H:%M:%S', time.gmtime())} running {args.tool} {name} ...", flush=True)
            raw_base = os.path.join(RAW, args.tool, name)
            stdout, secs, tm, killed, err = run(args.tool, path, args.xmx, args.cap, raw_base)
            with open(raw_base + ".txt", "w", encoding="utf-8") as fh:
                fh.write(stdout + ("\n# ERROR: " + err if err else ""))
            ridx = case["attributes"].index(case["attribute"])
            if killed:
                ev = {"outcome": "not finished (killed at cap)"}
            elif err and not stdout.strip():
                ev = {"outcome": "error"}
            else:
                ev = evaluate(stdout, attrs, missing, domains, ridx, case["removed_value"])
            if err:
                ev["detail"] = err
            ev.pop("seconds", None)
            ev.update({"tool": TOOLS[args.tool], "jdk": jdk, "heap": f"-Xmx{args.xmx}", "cap_s": int(args.cap),
                       "file": name, "dataset": case["dataset"], "attribute": case["attribute"],
                       "removed_value": case["removed_value"], "variant": variant, "rules": case["rules"],
                       "missing_states": len(missing),
                       "missing_with_removed_value": sum(1 for x in missing if x[ridx] == case["removed_value"]),
                       "finished": not killed, "killed": killed,
                       "wall_s": tm.get("wall_s", round(secs, 2)), "peak_rss_mb": tm.get("peak_rss_mb"),
                       "exit_status": tm.get("exit_status")})
            prev = laptop(args.tool, case, variant, name, d7, kie10)
            ev["laptop"] = None if prev is None else {k: prev.get(k) for k in CMP_KEYS + ("seconds",)}
            ev["vs_laptop"] = None if killed else compare(ev, prev)
            res["runs"][key] = ev
            with open(OUT, "w", encoding="utf-8") as fh:
                json.dump(res, fh, indent=1)
            v = ev["vs_laptop"]
            print(f"  {ev['outcome']}  gaps {ev.get('gap_messages')}  covered {ev.get('missing_covered')}/"
                  f"{len(missing)}  removed-value {ev.get('removed_value_states_found')}  {ev['wall_s']} s  "
                  f"{ev['peak_rss_mb']} MB  same-as-laptop={None if v is None else v['same']}"
                  + ("" if not v or v["same"] else f"  DIFF {v['differences']}"), flush=True)


if __name__ == "__main__":
    main()
