"""Row-by-row comparison of the corrected NZ-SLP ground truth with the second conversion.

Uses the attribute and label map of paperc-analysis:paperC/analysis/m6_nz.py (slp_compare):
attributes paired by position; labels equal except age '>=20' -> '20+' and
social_security__dependent_children '>=1' -> '1+'.
Usage (repository root): python3.12 -I paperC/verify-fix/m6_slp_fix.py [second-conversion ref]
Reads paperC/specs/NZ-SLP from the working tree and the second conversion's
paperC/specs2/NZ-SLP from git (default ref origin/paperc-code2-nz).
"""
import collections
import csv
import io
import json
import subprocess
import sys

REF2 = sys.argv[1] if len(sys.argv) > 1 else "origin/paperc-code2-nz"
F1, F2 = "paperC/specs/NZ-SLP", "paperC/specs2/NZ-SLP"


def show(path):
    return subprocess.run(["git", "show", f"{REF2}:{path}"], check=True, capture_output=True, text=True).stdout


def table(text, names):
    return {tuple(r[n] for n in names): r["output"] for r in csv.DictReader(io.StringIO(text))}


s1 = json.load(open(f"{F1}/spec.json", encoding="utf-8"))
s2 = json.loads(show(f"{F2}/spec.json"))
n1 = [a["name"] for a in s1["attributes"]]
n2 = [a["name"] for a in s2["attributes"]]
ren = dict(zip(n1, n2))
vals = {("age", ">=20"): "20+", ("social_security__dependent_children", ">=1"): "1+"}
g1 = table(open(f"{F1}/ground_truth.csv", encoding="utf-8").read(), n1)
g2 = table(show(f"{F2}/ground_truth.csv"), n2)
tally = collections.Counter()
dis = []
for c1, o1 in g1.items():
    c2 = tuple(vals.get((a, v), v) for a, v in zip(n1, c1))
    o2 = g2[c2]
    tally["agree" if o1 == o2 else f"first={o1} second={o2}"] += 1
    if o1 != o2:
        dis.append((c1, o1, o2))
print(f"attribute map: {ren}")
print(f"rows first {len(g1)}, second {len(g2)}, compared {sum(tally.values())}, "
      f"distinct second rows reached {len({tuple(vals.get((a, v), v) for a, v in zip(n1, c)) for c in g1})}")
print(f"tally: {dict(tally)}")
for d in dis:
    print("disagreement:", d)
sys.exit(1 if dis else 0)
