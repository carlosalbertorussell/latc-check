"""Cell-by-cell comparison of two runs.csv files after mapping the verifier's column
name `sample` onto the runner's `sample_id` (the only naming difference).

Usage: python3.12 paperC/verify-fix/compare_renamed.py <verifier runs.csv> <runner runs.csv>
Rows are matched by position, columns by name (runner's order).
"""
import csv
import sys

RENAME = {"sample": "sample_id"}


def load(path, rename):
    with open(path, encoding="utf-8", newline="") as f:
        return [{rename.get(k, k): v for k, v in r.items()} for r in csv.DictReader(f)]


def main(a_path, b_path):
    a, b = load(a_path, RENAME), load(b_path, {})
    cols = list(b[0])
    missing = [c for c in cols if c not in a[0]] + [c for c in a[0] if c not in b[0]]
    diffs = sum(x[c] != y[c] for x, y in zip(a, b) for c in cols if c in x)
    cells = len(cols) * min(len(a), len(b))
    print(f"rows {len(a)} / {len(b)}; columns {len(cols)}; unmatched columns: {missing or 'none'}")
    print(f"cells compared {cells}; differing {diffs}; verdict {'IDENTICAL' if not diffs and not missing and len(a) == len(b) else 'DIFFERENT'}")
    return 1 if diffs or missing or len(a) != len(b) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
