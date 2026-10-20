"""Summary numbers for paperC/specs/README-NZ.md.  Standard library only.

For each NZ table: size of the declared space, EXCLUDED / REJECTED / valid counts,
output counts, official example rows, and the declared labels that the official
examples never use (per attribute).  Usage: python summarise.py
"""
import csv
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(os.path.dirname(HERE), "specs")
FOLDERS = [os.path.join(SPECS, s) for s in ("NZ-SLP", "NZ-AS", "NZ-SPS")] + [os.path.join(HERE, "supplementary", "NZ-AS-1964")]


def main():
    for folder in FOLDERS:
        spec = json.load(open(os.path.join(folder, "spec.json"), encoding="utf-8"))
        with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
            gt = list(csv.DictReader(f))
        with open(os.path.join(folder, "official_examples.csv"), encoding="utf-8", newline="") as f:
            off = list(csv.DictReader(f))
        out = Counter(r["output"] for r in gt)
        excl, rej = out.pop("EXCLUDED", 0), out.pop("REJECTED", 0)
        print(f"## {spec['id']}")
        print(f"declared space {len(gt)}; EXCLUDED {excl}; REJECTED {rej}; valid {len(gt) - excl - rej}; "
              f"valid outputs {dict(sorted(out.items()))}")
        print(f"official example rows {len(off)}; outputs {dict(sorted(Counter(r['output'] for r in off).items()))}; "
              f"distinct conditions {len({tuple(r[a['name']] for a in spec['attributes']) for r in off})}")
        for a in spec["attributes"]:
            used = {r[a["name"]] for r in off}
            unseen = [v for v in a["values"] if v not in used]
            if unseen:
                print(f"  unseen {a['name']}: {', '.join(unseen)}")
        print()


if __name__ == "__main__":
    main()
