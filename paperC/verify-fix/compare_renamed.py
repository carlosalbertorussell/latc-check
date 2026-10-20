"""Run compare.py (copied unchanged) after renaming the verifier's columns `sample` and `n`
to the harness names `sample_id` and `size`, so that those two columns are compared too.

Usage (repository root): python3.12 paperC/verify-fix/compare_renamed.py <verifier runs.csv> <harness runs.csv>
"""

import csv
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare  # noqa: E402

RENAME = {"sample": "sample_id", "n": "size"}

with open(sys.argv[1], encoding="utf-8", newline="") as f:
    rows = list(csv.reader(f))
rows[0] = [RENAME.get(c, c) for c in rows[0]]
buf = io.StringIO()
csv.writer(buf, lineterminator="\n").writerows(rows)
with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="") as tmp:
    tmp.write(buf.getvalue())
try:
    compare.main(tmp.name, sys.argv[2])
finally:
    os.unlink(tmp.name)
