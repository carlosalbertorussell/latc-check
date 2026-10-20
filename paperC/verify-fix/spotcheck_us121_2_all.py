"""Run the verifier's spot-check (paperC/verify-fix/spotcheck/spotcheck.py, copied unchanged
from branch paperc-verify-fr2) on every row of the corrected US-121-2.

Usage (repository root): python3.12 paperC/verify-fix/spotcheck_us121_2_all.py
Writes paperC/verify-fix/US-121-2/spotcheck_all.csv and prints a summary.
"""

import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "spotcheck"))
import spotcheck as S  # noqa: E402

ok, lines = S.validate_official()
print("official-test validation:", "PASS" if ok else "FAIL")
for ln in lines:
    print("  ", ln)
os.makedirs(os.path.join(HERE, "US-121-2"), exist_ok=True)
spec, gt, res, probes = S.spot("US-121-2", "US-121", range(len(S.load("US-121-2", "US-121")[1])),
                               os.path.join(HERE, "US-121-2", "spotcheck_all.csv"))
agree = sum(1 for _, row, mine, _ in res if mine == row["output"])
print(f"US-121-2: checked={len(res)} agree={agree} disagree={len(res) - agree}")
print("ground truth outputs:", dict(collections.Counter(row["output"] for _, row, _, _ in res)))
print("verifier outputs:", dict(collections.Counter(mine for _, _, mine, _ in res)))
pbad = [p for p in probes if p and "differ" in p]
print(f"in-band probes: {sum(int(p.split('/')[1].split()[0]) for p in probes if p)} on "
      f"{sum(1 for p in probes if p)} rows; rows with a difference: {len(pbad)}")
for i, row, mine, detail in res:
    if mine != row["output"]:
        print("DISAGREE", i, dict(row), mine, detail)
