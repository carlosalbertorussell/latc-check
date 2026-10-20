"""Step 4: compare paperC/verify/<ID>/runs.csv with the runner's paperC/results/<ID>/runs.csv.

Usage: python3.12 paperC/verify/compare.py <git ref> NZ-SLP [...]
Reads the runner's file with `git show <ref>:paperC/results/<ID>/runs.csv`. Columns are
matched by name; rows by position (both follow the run order of PROTOCOL.md s 5).
Writes paperC/verify/<ID>/compare.txt.
"""
import csv
import io
import os
import subprocess
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recompute import STAT_METRICS, pct, wilson  # noqa: E402  (own module, not the harness)

HERE = os.path.dirname(os.path.abspath(__file__))


def main(ref, ids):
    for sid in ids:
        try:
            theirs_txt = subprocess.run(["git", "show", f"{ref}:paperC/results/{sid}/runs.csv"],
                                        check=True, capture_output=True, text=True).stdout
        except subprocess.CalledProcessError:
            msg = f"{sid}: {ref} has no paperC/results/{sid}/runs.csv; comparison pending\n"
            open(os.path.join(HERE, sid, "compare.txt"), "w").write(msg)
            print(msg, end="")
            continue
        mine_txt = open(os.path.join(HERE, sid, "runs.csv"), encoding="utf-8").read()
        mine = list(csv.DictReader(io.StringIO(mine_txt)))
        theirs = list(csv.DictReader(io.StringIO(theirs_txt)))
        mcols, tcols = list(mine[0]), list(theirs[0])
        lines = [f"{sid}: verifier columns {len(mcols)}, runner columns {len(tcols)}; "
                 f"verifier rows {len(mine)}, runner rows {len(theirs)}",
                 "columns only in verifier: " + (", ".join(c for c in mcols if c not in tcols) or "none"),
                 "columns only in runner: " + (", ".join(c for c in tcols if c not in mcols) or "none"),
                 f"same column order: {mcols == tcols}; byte-identical file: {mine_txt == theirs_txt}"]
        common = [c for c in mcols if c in tcols]
        diffs = 0
        for i, (a, b) in enumerate(zip(mine, theirs)):
            for c in common:
                if a[c] != b[c]:
                    diffs += 1
                    if diffs <= 200:
                        lines.append(f"row {i + 2} {a['source']} {a.get('size')} {a.get('seed')} {a['condition']} "
                                     f"column {c}: verifier {a[c]!r} runner {b[c]!r}")
        lines.append(f"differing cells in common columns: {diffs} (of {len(common) * min(len(mine), len(theirs))})")
        lines += compare_plant(ref, sid) + compare_stats(ref, sid, mine)
        open(os.path.join(HERE, sid, "compare.txt"), "w").write("\n".join(lines) + "\n")
        print("\n".join(l for l in lines if not l.startswith("row ")))


def show(ref, path):
    return subprocess.run(["git", "show", f"{ref}:{path}"], check=True, capture_output=True, text=True).stdout


def compare_plant(ref, sid):
    """Per example set: removed value, rows removed, C2 and C1 counts, pass flag."""
    mine = list(csv.DictReader(open(os.path.join(HERE, sid, "plant.csv"), encoding="utf-8")))
    theirs = [r for r in csv.DictReader(io.StringIO(show(ref, f"paperC/results/{sid}/controls.csv")))
              if r["control"] == "CTRL-PLANT" and r["source"] != "ALL"]
    diffs = 0
    for a, b in zip(mine, theirs):
        m = re.match(r".*?=(.*); removed (\d+) example rows; C1 generated (\d+)", b["detail"])
        x = (a["source"], a["size"], a["seed"], a["v"], a["removed_rows"], a["c1_generated_with_v"],
             a["c2_generated_with_v"], a["expected"], a["pass"])
        y = (b["source"], b["size"], b["seed"], m.group(1), m.group(2), m.group(3), b["observed"],
             b["expected"], b["pass"])
        diffs += x != y
    return [f"CTRL-PLANT per example set: verifier {len(mine)}, runner {len(theirs)}, differing {diffs}"]


def compare_stats(ref, sid, mine):
    """Compare the runner's summary.md statistics tables (4 decimals) with recomputed values."""
    text = show(ref, f"paperC/results/{sid}/summary.md")
    groups = {}
    for r in mine:
        if r["source"] in ("UNIFORM", "ZIPF"):
            groups.setdefault((r["condition"], r["source"], r["size"]), []).append(r)
    section, checked, diffs, out = None, 0, 0, []
    for line in text.split("\n"):
        if line.startswith("### "):
            section = line[4:].strip()
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0] not in ("C1", "C2", "C3") or cells[1] not in ("UNIFORM", "ZIPF"):
            continue
        g = groups[(cells[0], cells[1], cells[2])]
        if section in STAT_METRICS:
            xs = [float(r[section]) for r in g]
            want = [f"{v:.4f}" for v in (statistics.fmean(xs), statistics.median(xs), pct(xs, 0.025), pct(xs, 0.975))]
            got = cells[4:8]
        elif section and section.startswith("COMPLETE"):
            k = sum(int(r["complete"]) for r in g)
            lo, hi = wilson(k, len(g))
            want = [f"{k}/{len(g)}", f"{k / len(g):.4f}", f"{lo:.4f}", f"{hi:.4f}"]
            got = cells[3:7]
        else:
            continue
        checked += 1
        if want != got:
            diffs += 1
            out.append(f"stats {section} {cells[:3]}: verifier {want} runner {got}")
    return [f"summary statistics rows checked: {checked}, differing: {diffs}"] + out


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
