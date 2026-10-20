"""Cell-by-cell comparison of the verifier's runs.csv with the runner's (task step 4),
plus the per-example-set CTRL-PLANT values.

Usage: python3.12 compare.py <verifier dir> <runner runs.csv> <runner controls.csv> <report path>
The two runs.csv files differ in two column names only (verifier `sample`, `n`;
runner `sample_id`, `size`); columns are matched by position after checking that
every other name agrees.
"""

import csv
import sys

RENAME = {"sample": "sample_id", "n": "size"}


def compare_summary(mine, summary_path):
    """Compare the runner's summary.md statistics (printed to 4 decimals) with the
    verifier's own statistics computed from the verifier's runs.csv."""
    import statistics
    import recompute as rc
    head = mine[0]
    rows = [dict(zip(head, r)) for r in mine[1:]]
    out = []
    with open(summary_path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    section = None
    checked = bad = 0
    for ln in lines:
        if ln.startswith("### "):
            section = ln[4:].strip()
            continue
        if not ln.startswith("| C") or section is None:
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        cond, src, n = cells[0], cells[1], cells[2]
        sel = [r for r in rows if r["condition"] == cond and r["source"] == src and r["n"] == n]
        if section.startswith("COMPLETE"):
            k = sum(int(r["complete"]) for r in sel)
            lo, hi = rc.wilson(k, len(sel))
            mine_vals = ["%d/%d" % (k, len(sel)), "%.4f" % (k / len(sel)), "%.4f" % lo, "%.4f" % hi]
            theirs_vals = cells[3:7]
        else:
            xs = [float(r[section]) for r in sel]
            mine_vals = [str(len(sel))] + ["%.4f" % v for v in (statistics.mean(xs), statistics.median(xs),
                                                                 rc.pct(xs, 0.025), rc.pct(xs, 0.975))]
            theirs_vals = cells[3:8]
        for a, b in zip(mine_vals, theirs_vals):
            checked += 1
            if a != b:
                bad += 1
                out.append("summary %s %s %s %s: verifier %s runner %s" % (section, cond, src, n, a, b))
    out.append("summary.md statistics cells compared (4 decimals): %d; differing: %d" % (checked, bad))
    return out


def main(vdir, runner_runs, runner_controls, report, summary_path=None):
    with open(vdir + "/runs.csv", encoding="utf-8", newline="") as f:
        mine = list(csv.reader(f))
    with open(runner_runs, encoding="utf-8", newline="") as f:
        theirs = list(csv.reader(f))
    out = []
    hm = [RENAME.get(h, h) for h in mine[0]]
    if hm != theirs[0]:
        out.append("HEADER DIFFERS: verifier %r runner %r" % (mine[0], theirs[0]))
    out.append("rows: verifier %d, runner %d" % (len(mine) - 1, len(theirs) - 1))
    diffs = 0
    cells = 0
    for r, (a, b) in enumerate(zip(mine[1:], theirs[1:]), start=2):
        for c, (x, y) in enumerate(zip(a, b)):
            cells += 1
            if x != y:
                diffs += 1
                out.append("line %d column %s: verifier %r runner %r (key %s)" % (r, theirs[0][c], x, y, ",".join(a[1:5])))
    out.append("cells compared: %d; differing cells: %d" % (cells, diffs))

    # CTRL-PLANT per example set
    with open(vdir + "/plant.csv", encoding="utf-8", newline="") as f:
        vp = list(csv.DictReader(f))
    with open(runner_controls, encoding="utf-8", newline="") as f:
        rc = [r for r in csv.DictReader(f) if r["control"] == "CTRL-PLANT"]
    pd = 0
    for a, b in zip(vp, rc):
        key_ok = (a["source"], a["n"], a["seed"]) == (b["source"], b["size"], b["seed"])
        detail = b["detail"]
        v_runner = detail.split(";")[0].split("=", 1)[1]
        c1_runner = detail.split("C1 generated ")[1].split(" ")[0]
        same = (key_ok and a["v"] == v_runner and a["c2_generated_v"] == b["observed"]
                and a["expected"] == b["expected"] and a["pass"] == b["pass"] and a["c1_generated_v"] == c1_runner)
        if not same:
            pd += 1
            out.append("CTRL-PLANT differs: verifier %r runner %r" % (dict(a), dict(b)))
    out.append("CTRL-PLANT example sets: verifier %d, runner %d; differing: %d" % (len(vp), len(rc), pd))
    if summary_path:
        out.extend(compare_summary(mine, summary_path))
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out[-4:]) if diffs + pd < 20 else "\n".join(out[:20]))


if __name__ == "__main__":
    main(*sys.argv[1:6])
