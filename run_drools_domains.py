"""Drools and the observed-domain trap: run ``latc_check.drools_domains``.

    python -I run_drools_domains.py --driver-dir ../drools-check --java <jdk8>/bin/java.exe

Writes ``results/drools/domains/results.json`` (updated after every file, so
an interrupted run resumes) and ``SUMMARY.md``.  The DMN files go to
``--work-dir`` (default: a temp directory); the pension files are also kept
under ``results/drools/domains/dmn``.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # also works under python -I

from latc_check import datasets, drools_domains as dd  # noqa: E402
from latc_check import examples as ex  # noqa: E402

REPO = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(REPO, "results", "drools", "domains")


def cases(which: list, per_attribute: int | None):
    """(dataset, attribute, value, T0) for the requested datasets."""
    for name in filter(None, which):
        if name == "pension":
            full = ex.pension_table()
            for a, v, t0 in dd.removal_cases(full, ["Age"]):
                yield name, a, v, t0
            continue
        full = datasets.car() if name == "car" else datasets.nursery()
        seen = {}
        for a, v, t0 in dd.removal_cases(full):
            seen[a] = seen.get(a, 0) + 1
            if per_attribute is None or seen[a] <= per_attribute:
                yield name, a, v, t0


def variants_for(name: str, first_of_attr: bool, requested: list) -> list:
    """Core variants everywhere; precedence variants V6/V7 on pension and one case per attribute."""
    out = [v for v in requested if v in dd.CORE_VARIANTS]
    if name == "pension" or first_of_attr:
        out += [v for v in requested if v not in dd.CORE_VARIANTS]
    return out


FINDING = (
    "Drools does not take string domains from the values the rules mention: when a string input has no "
    "enumerated values (V2; also V3a, where the itemDefinition is attached only to the inputData variable; "
    "V5, where only the removed attribute lacks them) it emits the WARNING `DECISION_TABLE_GAP` "
    "\"Columns: [...] relate to FEEL string values which can be enumerated for the inputs; Gap analysis "
    "skipped\" and reports no gap, in every case, so it neither finds the missing value nor declares the "
    "table complete. With the full values declared, either as `inputValues` on the decision-table input (V1) "
    "or as `allowedValues` of an `itemDefinition` named by the `inputExpression` typeRef (V3b), Drools "
    "reports gaps covering exactly the missing states (no extra states) in every case run. The trap appears "
    "when the declaration itself is the observed domain: `inputValues` listing only the values T0 mentions "
    "(V4) gives \"no gaps\" on every Car case (a false complete verdict, 0 of the removed-value states found) "
    "and, on the pension example, only the gaps inside the observed product. When both declarations are "
    "present, `inputValues` wins over the inputExpression's itemDefinition (V6 behaves as V4, V7 as V1).")
NOT_RUN = (
    "Nursery: only V2 was run (one case per attribute). A probe of Nursery finance=convenient (6480 rules, "
    "the smallest Nursery case) ran V2 and V3a in about 2 min each (both: gap analysis skipped), but V1 "
    "(full analysis) had not finished after about 61 min and was killed; V1, V3b, V4, V6 were therefore not "
    "run on Nursery. Car: one case per attribute was required; buying=high, buying=med, buying=low, "
    "maint=high, maint=med were also run (core variants V1-V5; maint=med lacks V5 because that run was "
    "killed when the scope was trimmed, and was not re-run). An earlier Car/pension pass was discarded and "
    "re-run with --fresh after the evaluation was changed to read '-' over Drools' own domain.")


def summary_md(res: dict) -> str:
    rows = res["cases"]
    lines = ["# Drools 7.74.1 and the observed-domain trap", "",
             "T0 = a complete table minus every row with one value of one attribute, written as DMN "
             "UNIQUE point rules. *missing* = states of the declared product absent from T0; "
             "*found* = missing states inside Drools' reported gaps (`DECISION_TABLE_GAP`), each gap token "
             "(including '-') read over the values Drools was given for that input; the last column reads '-' "
             "as every declared value (upper bound). "
             "Variants: " + "; ".join(f"**{k}** {v}" for k, v in dd.VARIANTS.items()) + ".", "",
             "| dataset | variant | cases | Drools outcome (cases) | missing | found | removed-value states | found | found, '-' read as full |",
             "|---|---|---|---|---|---|---|---|---|"]
    groups = {}
    for c in rows:
        for var, r in c["drools"].items():
            groups.setdefault((c["dataset"], var), []).append((c, r))
    for (ds, var), lst in sorted(groups.items()):
        outs = {}
        for _, r in lst:
            outs[r["outcome"]] = outs.get(r["outcome"], 0) + 1
        tot = lambda key: sum(r.get(key) or 0 for _, r in lst)
        lines.append(f"| {ds} | {var} | {len(lst)} | "
                     + ", ".join(f"{k} ({n})" for k, n in sorted(outs.items()))
                     + f" | {sum(c['missing'] for c, _ in lst)} | {tot('missing_covered')}"
                     + f" | {sum(c['missing_with_removed_value'] for c, _ in lst)} | {tot('removed_value_states_found')}"
                     + f" | {tot('missing_covered_full_wildcard')} |")
    lines += ["", "Pension: T0 = Table 1a (8 rows) minus its rows with Age = v, so it also misses states "
              "with the other Age values; *missing* counts all of them, *removed-value states* only those with "
              "Age = v. Car and Nursery: every missing state has the removed value.",
              "", "## Finding", "", FINDING, "", "## Runs not completed", "", NOT_RUN, ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--driver-dir", required=True, help="directory with out/DroolsCheck.class and lib/*.jar")
    ap.add_argument("--java", required=True, help="java executable (JDK 8)")
    ap.add_argument("--datasets", default="pension,car,nursery")
    ap.add_argument("--variants", default=",".join(dd.VARIANTS))
    ap.add_argument("--per-attribute", type=int, default=None,
                    help="at most this many removed values per attribute (default: all)")
    ap.add_argument("--timeout", type=float, default=3600.0, help="seconds per Drools run")
    ap.add_argument("--work-dir", default=os.path.join(tempfile.gettempdir(), "latc_drools_domains"))
    ap.add_argument("--fresh", action="store_true", help="ignore an existing results.json")
    args = ap.parse_args(argv)

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(args.work_dir, exist_ok=True)
    os.makedirs(os.path.join(OUT, "dmn"), exist_ok=True)
    rpath = os.path.join(OUT, "results.json")
    res = {"cases": []}
    if os.path.exists(rpath) and not args.fresh:
        with open(rpath, encoding="utf-8") as f:
            res = json.load(f)
    res.update({"drools": "7.74.1.Final (tools/drools/DroolsCheck.java: VALIDATE_SCHEMA, VALIDATE_MODEL, "
                          "ANALYZE_DECISION_TABLE)",
                "python": platform.python_version(), "variants": dd.VARIANTS})
    by_key = {(c["dataset"], c["attribute"], c["value"]): c for c in res["cases"]}
    requested = args.variants.split(",")
    first = set()
    for ds, a, v, t0 in cases(args.datasets.split(","), args.per_attribute):
        first_of_attr = (ds, a) not in first
        first.add((ds, a))
        miss = dd.missing_states(t0)
        j = [x.name for x in t0.attributes].index(a)
        c = by_key.setdefault((ds, a, v), {"dataset": ds, "attribute": a, "value": v, "drools": {}})
        if c not in res["cases"]:
            res["cases"].append(c)
        c.update({"rules": len(t0.rows), "missing": len(miss),
                  "missing_with_removed_value": sum(1 for m in miss if m[j] == v)})
        d = dd.dmn_of(t0)
        obs = dd.observed_values(t0)
        for var in variants_for(ds, first_of_attr, requested):
            if var in c["drools"] and not args.fresh:
                continue
            stem = f"{ds}_{a}_{v}_{var}".replace(">", "gt").replace("<", "lt").replace("=", "e")
            p = os.path.join(args.work_dir, stem + ".dmn")
            with open(p, "w", encoding="utf-8") as f:
                f.write(dd.export_variant(d, stem.replace("-", "_"), var, a, obs))
            if ds == "pension":
                shutil.copy(p, os.path.join(OUT, "dmn", stem + ".dmn"))
            out, secs, err = dd.run_one(p, args.driver_dir, args.java, args.timeout)
            doms = dd.effective_domains(d, var, a, obs)
            r = (dd.evaluate(out, t0.attributes, miss, doms, j, v) if not err
                 else {"outcome": "error", "detail": err})
            r["seconds"] = round(secs, 1)
            c["drools"][var] = r
            print(f"{ds} {a}={v} {var}: {r['outcome']} found {r.get('missing_covered')}/{len(miss)} "
                  f"removed-value {r.get('removed_value_states_found')}/{c['missing_with_removed_value']} ({r['seconds']} s)", flush=True)
            with open(rpath, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=1)
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write(summary_md(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
