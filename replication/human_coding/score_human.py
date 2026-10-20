"""Agreement of the human coders with each other and with the two LLM coders.

    python -I replication/human_coding/score_human.py SHEET_A.csv [SHEET_B.csv] [--out FILE.md]

Each sheet is a filled copy of ``coding_sheet_blank.csv``.  The LLM labels are read from
``results/corpus/exposed_sample_classes.json`` (first coder) and
``results/corpus/exposed_sample_rater2.json`` (second, blinded coder), matched by
``sample_no``.  For every pair of coders the script reports, on ``class`` and on ``domain``,
and on OPEN against the rest for each, the observed agreement, Cohen's kappa, PABAK and
Gwet's AC1, computed with the functions of ``latc_check/dmn_exposed_sample.py`` exactly as in
``EXPOSED_SAMPLE.md``.  The LLM 1 / LLM 2 row reproduces the published figures and serves as a
check.  Standard library only.
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from latc_check.dmn_exposed_sample import (CLASSES, DOMAINS, cohen_kappa, gwet_ac1,  # noqa: E402
                                           pabak, wilson)

LLM1 = os.path.join(REPO, "results", "corpus", "exposed_sample_classes.json")
LLM2 = os.path.join(REPO, "results", "corpus", "exposed_sample_rater2.json")
BLANK = os.path.join(HERE, "coding_sheet_blank.csv")
FIELDS = {"class": CLASSES, "domain": DOMAINS}


def read_llm(path):
    with open(path, encoding="utf-8") as fh:
        return {int(e["sample_no"]): {f: e[f] for f in FIELDS} for e in json.load(fh).values()}


def read_sheet(path, blank):
    """Labels by sample_no; raises ValueError on a missing row, a changed row or an unknown label."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out, problems = {}, []
    for r in rows:
        try:
            n = int(r["sample_no"])
        except (KeyError, ValueError):
            problems.append(f"row without a valid sample_no: {r}")
            continue
        ref = blank.get(n)
        if ref is None:
            problems.append(f"sample_no {n} is not in the blank sheet")
            continue
        if (r.get("table"), r.get("table_index")) != (ref["table"], ref["table_index"]):
            problems.append(f"sample_no {n}: table differs from the blank sheet")
        lab = {}
        for f, cats in FIELDS.items():
            v = (r.get(f) or "").strip().upper()
            if v not in cats:
                problems.append(f"sample_no {n}: {f} {v!r} is not one of {', '.join(cats)}")
            lab[f] = v
        out[n] = lab
    missing = sorted(set(blank) - set(out))
    if missing:
        problems.append(f"missing sample_no: {missing}")
    if problems:
        raise ValueError(f"{path}:\n  " + "\n  ".join(problems))
    return out


def minutes(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        vals = [r.get("minutes", "").strip() for r in csv.DictReader(fh)]
    nums = []
    for v in vals:
        try:
            nums.append(float(v.replace(",", ".")))
        except ValueError:
            pass
    return sum(nums), len(nums)


def agreement_rows(name_a, a, name_b, b):
    keys = sorted(set(a) & set(b))
    rows = []
    for f, cats in FIELDS.items():
        x, y = [a[k][f] for k in keys], [b[k][f] for k in keys]
        po, k = cohen_kappa(x, y)
        rows.append((name_a, name_b, f, len(keys), po, k, pabak(x, y, len(cats)), gwet_ac1(x, y, list(cats))))
        xo, yo = [v == "OPEN" for v in x], [v == "OPEN" for v in y]
        po, k = cohen_kappa(xo, yo)
        rows.append((name_a, name_b, f"{f}: OPEN against the rest", len(keys), po, k, pabak(xo, yo, 2),
                     gwet_ac1(xo, yo, [True, False])))
    return rows


def confusion(name_a, a, name_b, b):
    keys = sorted(set(a) & set(b))
    L = [f"Classes, {name_a} (rows) against {name_b} (columns):", "",
         "| | " + " | ".join(CLASSES) + " |", "|---|" + "---:|" * len(CLASSES)]
    for c in CLASSES:
        L.append(f"| {c} | " + " | ".join(str(sum(1 for k in keys if a[k]["class"] == c and b[k]["class"] == d))
                                         for d in CLASSES) + " |")
    return L + [""]


def report(coders, sheets):
    L = ["# Human coding of the exposed-table sample: agreement", "",
         "| coder | " + " | ".join(CLASSES) + " | OPEN share (Wilson 95%) |",
         "|---|" + "---:|" * (len(CLASSES) + 1)]
    for name, lab in coders.items():
        n = len(lab)
        cnt = [sum(1 for v in lab.values() if v["class"] == c) for c in CLASSES]
        lo, hi = wilson(cnt[0], n)
        L.append(f"| {name} | " + " | ".join(map(str, cnt)) +
                 f" | {cnt[0]}/{n} = {100 * cnt[0] / n:.0f}% ({100 * lo:.0f}% to {100 * hi:.0f}%) |")
    L += ["", "| coder A | coder B | judgement | tables | observed agreement | Cohen's kappa | PABAK | Gwet's AC1 |",
          "|---|---|---|---:|---:|---:|---:|---:|"]
    humans = [n for n in coders if n.startswith("Human")]
    pairs = [(a, b) for i, a in enumerate(humans) for b in humans[i + 1:]]
    pairs += [(h, m) for h in humans for m in ("LLM 1", "LLM 2")] + [("LLM 1", "LLM 2")]
    for a, b in pairs:
        for r in agreement_rows(a, coders[a], b, coders[b]):
            L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {100 * r[4]:.0f}% | {r[5]:.2f} | {r[6]:.2f} | {r[7]:.2f} |")
    L += ["", "The LLM 1 / LLM 2 rows should equal the agreement table of `results/corpus/EXPOSED_SAMPLE.md`.", ""]
    if len(humans) == 2:
        L += confusion(humans[0], coders[humans[0]], humans[1], coders[humans[1]])
    for h in humans:
        L += confusion(h, coders[h], "LLM 1", coders["LLM 1"])
    for h, path in zip(humans, sheets):
        total, n = minutes(path)
        L.append(f"{h} ({os.path.basename(path)}): {total:.0f} minutes recorded over {n} tables.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheets", nargs="+", help="one or two filled coding sheets (CSV)")
    ap.add_argument("--out", help="also write the report to this Markdown file")
    a = ap.parse_args(argv)
    if len(a.sheets) > 2:
        ap.error("give one or two sheets")
    with open(BLANK, encoding="utf-8", newline="") as fh:
        blank = {int(r["sample_no"]): r for r in csv.DictReader(fh)}
    coders = {}
    try:
        for i, path in enumerate(a.sheets, 1):
            coders[f"Human {i}"] = read_sheet(path, blank)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    coders["LLM 1"] = read_llm(LLM1)
    coders["LLM 2"] = read_llm(LLM2)
    text = report(coders, a.sheets)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
