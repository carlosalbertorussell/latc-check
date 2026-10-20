"""Step 4: cell-by-cell comparison of the verifier's runs.csv with the runner's.

Usage: python3.12 paperC/verify/compare.py <verifier runs.csv> <runner runs.csv>
Rows are paired by position (both files follow the run order of PROTOCOL.md section 5);
columns are paired by name. Prints every difference and a one-line verdict.
"""

import csv
import sys


def load(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def main(mine_path, theirs_path):
    mh, mine = load(mine_path)
    th, theirs = load(theirs_path)
    out = []
    only_mine = [c for c in mh if c not in th]
    only_theirs = [c for c in th if c not in mh]
    if only_mine:
        out.append(f"columns only in verifier: {only_mine}")
    if only_theirs:
        out.append(f"columns only in runner: {only_theirs}")
    if [c for c in mh if c in th] != [c for c in th if c in mh]:
        out.append("shared columns are in a different order")
    if len(mine) != len(theirs):
        out.append(f"row count differs: verifier {len(mine)}, runner {len(theirs)}")
    shared = [c for c in mh if c in th]
    mi = {c: mh.index(c) for c in shared}
    ti = {c: th.index(c) for c in shared}
    cells = diffs = 0
    for k, (a, b) in enumerate(zip(mine, theirs)):
        for c in shared:
            cells += 1
            if a[mi[c]] != b[ti[c]]:
                diffs += 1
                if diffs <= 200:
                    out.append(f"row {k + 1} column {c}: verifier {a[mi[c]]!r}, runner {b[ti[c]]!r}")
    out.append(f"VERDICT {'IDENTICAL' if diffs == 0 and not out else 'DIFFERENT'}: "
               f"{cells} shared cells compared, {diffs} differ")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
