"""Score raw analyser outputs of the tool audit against the manifest of true missing states.

    python -I replication/tool_audit/score.py [--drools LABEL=DIR ...] [--dmnjs LABEL=RESULTS_JSON ...]
        [--out FILE.md] [--json FILE.json]

``--drools`` takes a folder of DroolsCheck outputs (``<file>.dmn.txt``, as written by
``run_drools.py`` or ``results/tools/cloud-drools/raw/<tool>/``).  LABEL names the version and
picks the published result to compare with: a label starting with ``d7`` is compared with
Drools 7.74.1 (``results/tools/cloud-drools/results.json``, runs ``d7/...``), one starting with
``kie10`` with Apache KIE 10.2.0 (runs ``kie10/...``).  ``--dmnjs`` takes the ``results.json``
written by ``results/tools/dmn-js/run_all.js`` and compares it with the committed
``results/tools/dmn-js/results.json``.

For every file the true missing states are recomputed from the DMN file itself
(``missing_and_observed`` of ``results/tools/kie10/run_kie10.py``) and checked against the
manifest counts.  Drools output is read with ``latc_check.drools_domains.evaluate``, the
evaluation of the paper's runs (gap tokens over the declared values for V1 / V3b, the observed
values for V4, none for V2).  dmn-js gap regions are expanded here over the domain the tool used
(``tool_domains``, with ``any`` = that domain), independently of the harness's own count, and
both counts are reported.  Before scoring, the 39 input files and ``manifest.json`` are checked
against ``replication/expected_sha256.txt``.  Standard library only.
"""
import argparse
import hashlib
import json
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "results", "tools", "kie10"))

from latc_check.drools_domains import evaluate  # noqa: E402
from run_kie10 import missing_and_observed  # noqa: E402  (pure functions; its Windows paths are unused here)

INPUTS = os.path.join(REPO, "results", "tools", "inputs")
SHA = os.path.join(REPO, "replication", "expected_sha256.txt")
REF_DROOLS = os.path.join(REPO, "results", "tools", "cloud-drools", "results.json")
REF_DMNJS = os.path.join(REPO, "results", "tools", "dmn-js", "results.json")
CMP_DROOLS = ("outcome", "gap_messages", "states_covered_by_gaps", "missing_covered", "covered_not_missing",
              "removed_value_states_found", "gap_skip_columns", "message_types")
CMP_DMNJS = ("outcome", "n_gap_regions", "states_covered_by_gaps", "true_missing_found",
             "removed_value_states_found", "tool_domains")


def norm_sha(path):
    """SHA-256 of a file with CRLF line ends read as LF (as in replication/run_all.py)."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def check_inputs():
    """Problems with the shared input files, as a list of strings (empty when all match)."""
    want = {}
    with open(SHA, encoding="utf-8") as fh:
        for ln in fh:
            parts = ln.split()
            if len(parts) >= 2 and parts[1].startswith("results/tools/inputs/"):
                want[parts[1]] = parts[0]
    problems = []
    for rel, h in sorted(want.items()):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            problems.append(f"missing {rel}")
        elif norm_sha(p) != h:
            problems.append(f"differs from the committed hash: {rel}")
    return problems, len(want)


def cases():
    """(case, variant, file name, attrs, missing set, observed domains) for every manifest file."""
    with open(os.path.join(INPUTS, "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    for case in manifest["cases"]:
        attrs = [SimpleNamespace(name=a, domain=tuple(case["declared_domains"][a])) for a in case["attributes"]]
        for variant, rel in case["files"].items():
            name = os.path.basename(rel)
            missing, observed = missing_and_observed(os.path.join(INPUTS, name), attrs)
            ridx = case["attributes"].index(case["attribute"])
            removed = sum(1 for x in missing if x[ridx] == case["removed_value"])
            if (len(missing), removed) != (case["missing_states"], case["missing_with_removed_value"]):
                raise SystemExit(f"{name}: recomputed missing states {len(missing)} / {removed} differ from the "
                                 f"manifest {case['missing_states']} / {case['missing_with_removed_value']}")
            yield case, variant, name, attrs, missing, observed


def compare(new, prev, keys):
    if prev is None:
        return "no reference"
    if str(prev.get("outcome", "")).startswith("not finished"):
        return "reference did not finish"
    diffs = [k for k in keys if prev.get(k) != new.get(k)]
    return "same" if not diffs else "differs: " + ", ".join(diffs)


def score_drools(label, folder):
    with open(REF_DROOLS, encoding="utf-8") as fh:
        ref = json.load(fh)["runs"]
    tool = "d7" if label.startswith("d7") else "kie10" if label.startswith("kie10") else None
    rows = []
    for case, variant, name, attrs, missing, observed in cases():
        ridx = case["attributes"].index(case["attribute"])
        row = {"tool": label, "file": name, "dataset": case["dataset"], "variant": variant,
               "missing_states": case["missing_states"],
               "missing_with_removed_value": case["missing_with_removed_value"]}
        path = os.path.join(folder, name + ".txt")
        if not os.path.exists(path):
            row.update({"outcome": "not run", "vs_reference": "-"})
            rows.append(row)
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        err = next((ln[len("# ERROR: "):] for ln in text.splitlines() if ln.startswith("# ERROR: ")), "")
        stdout = "\n".join(ln for ln in text.splitlines() if not ln.startswith("# ERROR: "))
        if not stdout.strip():
            ev = {"outcome": "not finished (timeout)" if "timeout" in err else "error", "detail": err}
        else:
            domains = {"V1": [a.domain for a in attrs], "V3b": [a.domain for a in attrs],
                       "V2": [None] * len(attrs), "V4": observed}[variant]
            ev = evaluate(stdout, attrs, missing, domains, ridx, case["removed_value"])
            if err:
                ev["detail"] = err
        row.update({k: ev.get(k) for k in CMP_DROOLS})
        if ev.get("detail"):
            row["detail"] = ev["detail"][:300]
        prev = ref.get(f"{tool}/{name}") if tool else None
        row["vs_reference"] = compare(ev, prev, CMP_DROOLS) if not row["outcome"].startswith(("not", "error")) \
            else "-"
        rows.append(row)
    return rows


def expand(region, tool_domains, labels):
    """States covered by one dmn-js gap region, read over the tool's own domains."""
    sets = []
    for cell, lab in zip(region, labels):
        if cell == "any":
            sets.append(tuple(tool_domains[lab]))
        else:
            sets.append(tuple(v.strip().strip('"') for v in str(cell).strip("[]").split(",")))
    out = [()]
    for s in sets:
        out = [x + (v,) for x in out for v in s]
    return set(out)


def score_dmnjs(label, path):
    with open(path, encoding="utf-8") as fh:
        runs = json.load(fh)["runs"]
    with open(REF_DMNJS, encoding="utf-8") as fh:
        ref = {(r["file"], r["variant"]): r for r in json.load(fh)["runs"]}
    by_file = {}
    for r in runs:
        by_file.setdefault(r["file"], []).append(r)
    rows = []
    for case, variant, name, attrs, missing, observed in cases():
        labels = [a.name for a in attrs]
        ridx = labels.index(case["attribute"])
        mine = [r for r in by_file.get(name, []) if r["variant"] == variant or
                (variant == "V3b" and r["variant"] == "V3b+resolvedTypeRef")]
        if not mine:
            rows.append({"tool": label, "file": name, "dataset": case["dataset"], "variant": variant,
                         "missing_states": case["missing_states"],
                         "missing_with_removed_value": case["missing_with_removed_value"],
                         "outcome": "not run", "vs_reference": "-"})
        for r in mine:
            row = {"tool": label, "file": name, "dataset": case["dataset"], "variant": r["variant"],
                   "missing_states": case["missing_states"],
                   "missing_with_removed_value": case["missing_with_removed_value"]}
            row.update({k: r.get(k) for k in CMP_DMNJS})
            if r.get("gap_regions") is not None and r.get("all_inputs_typed_string_for_tool") and r.get("tool_domains"):
                covered = set()
                for g in r["gap_regions"]:
                    covered |= expand(g, r["tool_domains"], labels)
                row["recomputed_found"] = len(covered & missing)
                row["recomputed_removed_found"] = sum(1 for x in covered & missing if x[ridx] == case["removed_value"])
                row["recomputed_extra"] = len(covered - missing)
            elif r.get("n_gap_regions") == 0:
                row.update({"recomputed_found": 0, "recomputed_removed_found": 0, "recomputed_extra": 0})
            row["missing_covered"] = row.get("true_missing_found")
            row["covered_not_missing"] = row.get("recomputed_extra")
            row["vs_reference"] = compare(r, ref.get((name, r["variant"])), CMP_DMNJS)
            rows.append(row)
    return rows


def table(rows):
    L = ["| tool | file | variant | outcome | missing (removed value) | found | removed-value found "
         "| extra states | recomputed found / removed / extra | same as the published run |",
         "|---|---|---|---|---:|---:|---:|---:|---|---|"]
    for r in rows:
        rec = ("-" if "recomputed_found" not in r else
               f"{r['recomputed_found']} / {r['recomputed_removed_found']} / {r['recomputed_extra']}")
        L.append(f"| {r['tool']} | {r['file']} | {r['variant']} | {r['outcome']} | {r['missing_states']} "
                 f"({r['missing_with_removed_value']}) | {r.get('missing_covered', '-')} | "
                 f"{r.get('removed_value_states_found', '-')} | {r.get('covered_not_missing', '-')} | {rec} | "
                 f"{r['vs_reference']} |")
    return L


def summary(rows):
    groups = {}
    for r in rows:
        groups.setdefault((r["tool"], r["dataset"], r["variant"]), []).append(r)
    L = ["| tool | dataset | variant | files | outcomes | missing | found | removed-value states | found "
         "| extra states | same as published |", "|---|---|---|---:|---|---:|---:|---:|---:|---:|---|"]
    for (tool, ds, v), rs in groups.items():
        oc = {}
        for r in rs:
            oc[r["outcome"]] = oc.get(r["outcome"], 0) + 1
        num = lambda k: sum(r.get(k) or 0 for r in rs)  # noqa: E731
        same = sum(1 for r in rs if r["vs_reference"] == "same")
        ran = sum(1 for r in rs if r["outcome"] != "not run")
        L.append(f"| {tool} | {ds} | {v} | {len(rs)} | " + "; ".join(f"{k} ({n})" for k, n in oc.items()) +
                 f" | {num('missing_states')} | {num('missing_covered')} | {num('missing_with_removed_value')} | "
                 f"{num('removed_value_states_found')} | {num('covered_not_missing')} | "
                 f"{f'{same}/{ran}' if ran else '-'} |")
    return L


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drools", nargs="*", default=[], metavar="LABEL=DIR")
    ap.add_argument("--dmnjs", nargs="*", default=[], metavar="LABEL=RESULTS_JSON")
    ap.add_argument("--out", help="write the Markdown report here too")
    ap.add_argument("--json", help="write the per-file rows as JSON here")
    a = ap.parse_args(argv)
    if not a.drools and not a.dmnjs:
        ap.error("give at least one --drools or --dmnjs")

    problems, n = check_inputs()
    L = ["# Tool audit: raw outputs scored against the manifest", ""]
    if problems:
        print("Input files do not match the committed hashes; run `python -I run_tool_inputs.py` first:\n  "
              + "\n  ".join(problems[:10]), file=sys.stderr)
        return 1
    L += [f"Inputs: the {n - 1} DMN files and manifest.json under results/tools/inputs/ match "
          "replication/expected_sha256.txt.", ""]
    rows = []
    for spec in a.drools:
        label, _, folder = spec.partition("=")
        rows += score_drools(label, folder)
    for spec in a.dmnjs:
        label, _, path = spec.partition("=")
        rows += score_dmnjs(label, path)
    L += ["## Summary", ""] + summary(rows) + ["", "## Per file", ""] + table(rows)
    L += ["", "found = true missing states inside a reported gap; extra = reported states that are not missing "
              "(false gaps). For dmn-js, found is the harness's count and the recomputed columns expand the "
              "gap regions here; the two must agree."]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
    bad = [r for r in rows if r["vs_reference"] not in ("same", "-", "reference did not finish", "no reference")]
    mism = [r for r in rows if "recomputed_found" in r and r.get("missing_covered") is not None
            and r["recomputed_found"] != r["missing_covered"]]
    print(f"{len(rows)} rows; {len(bad)} differ from the published runs; "
          f"{len(mism)} dmn-js rows where the recomputed count differs from the harness's.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
