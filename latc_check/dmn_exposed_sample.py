"""A random sample of the *exposed* decision tables of the DMN corpus survey.

``dmn_corpus`` counts a table as exposed when it is single-hit, has no
catch-all rule, and has a string input with no declared domain whose entries
mention a string literal (``dmn_corpus.exposed_column``).  Whether such a table
is a real risk depends on the input's real-world domain, which only a reader of
the model can judge.  This module lists the exposed tables from
``results/corpus/results.json``, one per distinct table content (the
``fingerprint`` of ``dmn_corpus``; the representative is the copy of highest
kind priority, as in ``dmn_corpus.run``), so that copies of the same table are
not over-sampled, and draws a simple random sample with a fixed seed.

Each sampled table is then classified by hand (``CLASSES``) in a JSON file of
``{fingerprint: {"class": ..., "domain": ..., "justification": ..., "partial_protection": ...}}``;
``write_outputs`` merges it into ``exposed_sample.csv`` and
``EXPOSED_SAMPLE.md`` with Wilson 95% intervals.  Standard library only.
"""
import csv
import json
import math
import os
import random

from latc_check.dmn_corpus import KIND_PRIORITY, exposed_column

SEED = 20210101
SAMPLE_SIZE = 50
CLASSES = ("OPEN", "CLOSED", "PARTIAL", "UNCLEAR")
CLASS_TEXT = {
    "OPEN": "the input's real-world domain is open or larger than the values the rules mention, "
            "so an unmentioned value can plausibly arrive and reach no rule",
    "CLOSED": "the domain is closed by convention or by the upstream model (yes/no, a fixed status "
              "set the rules enumerate, an enumeration fixed elsewhere), so the risk is low",
    "PARTIAL": "the table is deliberately partial or a test fixture (a no-match test, a tutorial "
               "fragment, an analyser fixture with intentional gaps)",
    "UNCLEAR": "cannot be judged from the model",
}
# secondary judgement of the column's domain, recorded for every table (fixtures included)
DOMAINS = ("OPEN", "CLOSED", "COVERED", "SYNTHETIC", "UNCLEAR")
DOMAIN_TEXT = {
    "OPEN": "open or larger than the mentioned values in the real world",
    "CLOSED": "closed by convention or by the upstream model",
    "COVERED": "the column's entries already match every value through `not(...)` or expressions, so nothing is missed",
    "SYNTHETIC": "placeholder values with no real-world domain, as in syntax and engine tests",
    "UNCLEAR": "cannot be judged from the model",
}


def exposed_frame(res):
    """Exposed tables, one per distinct fingerprint, sorted by fingerprint.

    Each entry: source, kind, path, table, table_index, hit_policy, n_rules,
    columns (one dict per exposed input: input_index, label, mentioned, has_dash)
    and copies (how many distinct files hold an exposed copy of this content)."""
    inputs = {}
    for r in res["inputs"]:
        inputs.setdefault((r["source"], r["path"], r["table_index"]), []).append(r)
    best, copies = {}, {}
    for t in res["tables"]:
        key = (t["source"], t["path"], t["table_index"])
        cols = [r for r in inputs.get(key, []) if exposed_column(r, t)]
        if not cols:
            continue
        fp = t["fingerprint"]
        copies[fp] = copies.get(fp, 0) + 1
        if fp not in best or KIND_PRIORITY[t["kind"]] < KIND_PRIORITY[best[fp][0]["kind"]]:
            best[fp] = (t, cols)
    out = []
    for fp in sorted(best):
        t, cols = best[fp]
        out.append({"fingerprint": fp, "source": t["source"], "kind": t["kind"], "path": t["path"],
                    "table": t["table"], "table_index": t["table_index"],
                    "hit_policy": t["hit_policy"], "n_rules": t["n_rules"],
                    "columns": [{"input_index": r["input_index"], "label": r["label"],
                                 "mentioned": list(r["mentioned"]), "has_dash": r["n_any"] > 0}
                                for r in sorted(cols, key=lambda r: r["input_index"])],
                    "copies": copies[fp]})
    return out


def draw(frame, n=SAMPLE_SIZE, seed=SEED):
    """Simple random sample without replacement of ``n`` frame entries (all when fewer),
    in the frame's (fingerprint) order."""
    if len(frame) <= n:
        return list(frame)
    idx = sorted(random.Random(seed).sample(range(len(frame)), n))
    return [frame[i] for i in idx]


def wilson(k, n, z=1.959963984540054):
    """Wilson score interval for k successes in n trials, as (low, high)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def cohen_kappa(a, b):
    """Observed agreement and Cohen's kappa of two equal-length label lists, as (po, kappa).

    Kappa is 1.0 when chance agreement is already 1 (both coders use one label throughout)."""
    n = len(a)
    if n == 0 or n != len(b):
        raise ValueError("label lists must be non-empty and of equal length")
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return po, (1.0 if pe == 1 else (po - pe) / (1 - pe))


LIST_COLS = ["sample_no", "fingerprint", "source", "kind", "path", "table", "table_index",
             "hit_policy", "n_rules", "copies", "exposed_inputs", "mentioned_literals",
             "dash_in_column"]


def list_rows(sample):
    """Flat rows for CSV: one row per sampled table, columns joined with ' | '."""
    rows = []
    for i, e in enumerate(sample, 1):
        rows.append({"sample_no": i, "fingerprint": e["fingerprint"], "source": e["source"],
                     "kind": e["kind"], "path": e["path"], "table": e["table"],
                     "table_index": e["table_index"], "hit_policy": e["hit_policy"],
                     "n_rules": e["n_rules"], "copies": e["copies"],
                     "exposed_inputs": " | ".join(c["label"] for c in e["columns"]),
                     "mentioned_literals": " | ".join(json.dumps(c["mentioned"], ensure_ascii=False)
                                                      for c in e["columns"]),
                     "dash_in_column": " | ".join("yes" if c["has_dash"] else "no"
                                                  for c in e["columns"])})
    return rows


def _write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def tally(sample, classes):
    """Counts per class over the sample (unclassified tables count as missing)."""
    counts = {c: 0 for c in CLASSES}
    missing = 0
    for e in sample:
        c = classes.get(e["fingerprint"], {}).get("class")
        if c in counts:
            counts[c] += 1
        else:
            missing += 1
    return counts, missing


def summary_md(frame, sample, classes, n_exposed_files, rater2=None):
    counts, missing = tally(sample, classes)
    n = len(sample) - missing
    k = counts["OPEN"]
    lo, hi = wilson(k, n)
    N = len(frame)
    # copy-weighted estimate over the distinct-file count: (N / n) * sum of copies of OPEN tables
    open_copies = sum(e["copies"] for e in sample if classes.get(e["fingerprint"], {}).get("class") == "OPEN")
    all_copies = sum(e["copies"] for e in sample if e["fingerprint"] in classes)
    L = ["# Exposed decision tables: how many are real risks?", "",
         "Generated by `run_dmn_exposed_sample.py` (`latc_check/dmn_exposed_sample.py`) from "
         "`results/corpus/results.json` and the hand classification in "
         "`results/corpus/exposed_sample_classes.json`.", "",
         "## Frame and sample", "",
         f"`SUMMARY.md` counts {n_exposed_files} exposed tables over distinct files (single-hit, no "
         "catch-all rule, an undeclared string input whose entries mention a string literal). Many are "
         f"copies of one table content; the sampling frame has one entry per distinct table content "
         f"(the `fingerprint` of `dmn_corpus`): {N} tables. A simple random sample of {len(sample)} was "
         f"drawn with `random.Random({SEED}).sample` over the frame sorted by fingerprint. "
         "`exposed_sample.csv` lists the sample with the exposed input column(s), the literals the rules "
         "mention there, the hit policy, the number of rules, and whether some rule has `-` in the column.",
         "", "## Classes", ""]
    for c in CLASSES:
        L.append(f"* **{c}**: {CLASS_TEXT[c]}.")
    L += ["", "Each table was read in its model file (column label, literals, outputs, names and "
          "documentation nearby). When the choice between OPEN and CLOSED was doubtful, the table was "
          "recorded as UNCLEAR.", "", "## Counts", "",
          "| class | tables | share | Wilson 95% |", "|---|---:|---:|---|"]
    for c in CLASSES:
        a, b = wilson(counts[c], n)
        L.append(f"| {c} | {counts[c]} | {100 * counts[c] / n:.0f}% | {100 * a:.0f}% to {100 * b:.0f}% |"
                 if n else f"| {c} | 0 | | |")
    L.append(f"| total | {n} | | |")
    if missing:
        L.append(f"\n{missing} sampled tables have no classification yet.")
    prot = sum(1 for e in sample if classes.get(e["fingerprint"], {}).get("partial_protection"))
    prot_open = sum(1 for e in sample if classes.get(e["fingerprint"], {}).get("class") == "OPEN"
                    and classes[e["fingerprint"]].get("partial_protection"))
    L += ["", f"Partial protection (some rule has `-` in the exposed column, so an unmentioned value "
          f"still reaches that rule in the states where the other inputs match it): {prot} of {n} "
          f"sampled tables, {prot_open} of the {k} OPEN ones.", "",
          "## By kind", "",
          "Most of the frame is test resources of engines and editors; the OPEN, CLOSED and UNCLEAR "
          "tables of the sample all come from example repositories.", "",
          "| kind | frame | sample | " + " | ".join(CLASSES) + " |",
          "|---|---:|---:|" + "---:|" * len(CLASSES)]
    kinds = sorted({e["kind"] for e in frame}, key=lambda x: KIND_PRIORITY[x])
    for kd in kinds:
        ss = [e for e in sample if e["kind"] == kd]
        cc = [sum(1 for e in ss if classes.get(e["fingerprint"], {}).get("class") == c) for c in CLASSES]
        L.append(f"| {kd} | {sum(1 for e in frame if e['kind'] == kd)} | {len(ss)} | "
                 + " | ".join(map(str, cc)) + " |")
    dcount = {d: sum(1 for e in sample if classes.get(e["fingerprint"], {}).get("domain") == d)
              for d in DOMAINS}
    L += ["", "## Domain of the column, fixtures included", "",
          "A second judgement records, for every sampled table, what the exposed column's domain would be "
          "if the table were used for real, fixtures included:", ""]
    for d in DOMAINS:
        a, b = wilson(dcount[d], n)
        L.append(f"* **{d}**: {DOMAIN_TEXT[d]}; {dcount[d]} of {n} "
                 f"(Wilson 95%: {100 * a:.0f}% to {100 * b:.0f}%).")
    L += ["", f"The {dcount['COVERED']} COVERED tables are counted as exposed by the measure although "
          "every value reaches some rule: the literal count includes values inside `not(...)` and expressions.",
          ""]
    L += [          "## Estimate", "",
          f"OPEN share: {k}/{n} = {100 * k / n:.0f}% (Wilson 95%: {100 * lo:.0f}% to {100 * hi:.0f}%).",
          "",
          f"* Over the {N} distinct exposed tables: about {round(k / n * N)} at real risk "
          f"(Wilson range {round(lo * N)} to {round(hi * N)}).",
          f"* Over the {n_exposed_files} exposed tables counted over distinct files, applying the same share: "
          f"about {round(k / n * n_exposed_files)} (range {round(lo * n_exposed_files)} to "
          f"{round(hi * n_exposed_files)}). Weighting each sampled table by its number of distinct-file "
          f"copies instead gives an OPEN share of {open_copies}/{all_copies} copies = "
          f"{100 * open_copies / all_copies:.0f}%, about {round(open_copies / all_copies * n_exposed_files)} "
          "tables (a ratio estimate; copies are unevenly spread, so its interval is wider than the "
          "Wilson interval above, and one table with many copies can drive it).", "",
          "This is an estimate from one rater, reading each model without its authors' context. The "
          "sampling unit is the distinct table content; the classes were assigned to that content, and "
          "copies in other files inherit them.", ""]
    if rater2:
        L += agreement_md(sample, classes, rater2)
    return "\n".join(L)


def agreement_md(sample, classes, rater2):
    """Markdown lines comparing the classification with a second, blinded coder."""
    both = [e for e in sample if e["fingerprint"] in classes and e["fingerprint"] in rater2]
    n = len(both)
    L = ["## Agreement with a second coder", "",
         "A second coder classified the same tables blind, from a sheet without the first coder's labels "
         "(`exposed_sample_rater2.json`), with the same class definitions. Both coders are instances of "
         "the Claude language model (Anthropic) reading the model files, so their errors may be "
         "correlated; the agreement below measures the consistency of the coding and is no substitute "
         "for a check by an independent human expert.", "",
         "| judgement | tables | observed agreement | Cohen's kappa |", "|---|---:|---:|---:|"]
    pairs = {}
    for field in ("class", "domain"):
        a = [classes[e["fingerprint"]][field] for e in both]
        b = [rater2[e["fingerprint"]][field] for e in both]
        pairs[field] = (a, b)
        po, k = cohen_kappa(a, b)
        L.append(f"| {field} | {n} | {100 * po:.0f}% | {k:.2f} |")
        po, k = cohen_kappa([x == "OPEN" for x in a], [y == "OPEN" for y in b])
        L.append(f"| {field}: OPEN against the rest | {n} | {100 * po:.0f}% | {k:.2f} |")
    a, b = pairs["class"]
    L += ["", "Classes, first coder (rows) against second coder (columns):", "",
          "| | " + " | ".join(CLASSES) + " |", "|---|" + "---:|" * len(CLASSES)]
    for c in CLASSES:
        L.append(f"| {c} | " + " | ".join(str(sum(1 for x, y in zip(a, b) if x == c and y == d))
                                         for d in CLASSES) + " |")
    k2 = sum(1 for y in b if y == "OPEN")
    lo, hi = wilson(k2, n)
    L += ["", f"Second coder's OPEN share: {k2}/{n} = {100 * k2 / n:.0f}% "
          f"(Wilson 95%: {100 * lo:.0f}% to {100 * hi:.0f}%).", ""]
    return L


OUT_COLS = LIST_COLS + ["class", "domain", "partial_protection", "justification"]


def write_outputs(res, out_dir, classes_path=None, n=SAMPLE_SIZE, seed=SEED, rater2_path=None):
    """Write exposed_sample.csv (and EXPOSED_SAMPLE.md when classifications exist); return the sample.

    ``rater2_path`` names an optional second coder's classification in the same format; when it
    exists, EXPOSED_SAMPLE.md gains an agreement section."""
    frame = exposed_frame(res)
    sample = draw(frame, n, seed)
    classes = {}
    if classes_path and os.path.exists(classes_path):
        with open(classes_path, encoding="utf-8") as fh:
            classes = json.load(fh)
    rows = list_rows(sample)
    for r in rows:
        c = classes.get(r["fingerprint"], {})
        r["class"] = c.get("class", "")
        r["domain"] = c.get("domain", "")
        r["partial_protection"] = {True: "yes", False: "no"}.get(c.get("partial_protection"), "")
        r["justification"] = c.get("justification", "")
    _write_csv(os.path.join(out_dir, "exposed_sample.csv"), OUT_COLS, rows)
    if classes:
        with open(os.path.join(out_dir, "EXPOSED_SAMPLE.md"), "w", encoding="utf-8") as fh:
            rater2 = None
            if rater2_path and os.path.exists(rater2_path):
                with open(rater2_path, encoding="utf-8") as r2:
                    rater2 = json.load(r2)
            fh.write(summary_md(frame, sample, classes, res["summary"]["all"]["exposed_tables"], rater2))
    return sample
