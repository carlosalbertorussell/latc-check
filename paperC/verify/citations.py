"""Step 3 helper: print every file:line citation of spec.json with the cited source line(s).

Usage: python3.12 paperC/verify/citations.py <openfisca-aotearoa clone> paperC/specs/<ID> [...]
"""
import json
import os
import re
import sys

CITE = re.compile(r"([\w/.]+\.(?:py|ya?ml))((?::\d+(?:-\d+)?(?:,\s*\d+)?)?(?:(?:,| and)\s*:\d+(?:-\d+)?)*)")
LINES = re.compile(r":?(\d+)(?:-(\d+))?")


def resolve(root, name):
    hits = []
    for d, _, files in os.walk(os.path.join(root, "openfisca_aotearoa")):
        for f in files:
            full = os.path.join(d, f)
            if full.endswith("/" + name) or f == name:
                hits.append(full)
    return hits


def main(root, folders):
    for folder in folders:
        spec = json.load(open(os.path.join(folder, "spec.json"), encoding="utf-8"))
        items = [(a["name"], a["source"]) for a in spec["attributes"]]
        items += [(e["id"], e["source"]) for e in spec["exclusions"]]
        items.append(("output", spec["output"]["source"]))
        print("=" * 30, spec["id"])
        for name, src in items:
            print(f"\n## {name}: {src}")
            last = None
            for tok in re.finditer(r"([\w/.]+\.(?:py|ya?ml))|(?::|line )(\d+)(?:-(\d+))?", src):
                if tok.group(1):
                    hits = resolve(root, tok.group(1))
                    hits = [h for h in hits if not h.endswith("/tests/" + tok.group(1))] if len(hits) > 1 else hits
                    if len(hits) > 1:
                        hits = [h for h in hits if "/social_security/" in h] or hits
                    last = hits[0] if len(hits) == 1 else None
                    if len(hits) != 1:
                        print(f"   [{tok.group(1)}: {len(hits)} matches]")
                    continue
                if last is None:
                    continue
                a = int(tok.group(2)); b = int(tok.group(3) or a)
                lines = open(last, encoding="utf-8").read().split("\n")
                for k in range(a, min(b, a + 3) + 1):
                    print(f"   {os.path.relpath(last, root)}:{k}: {lines[k - 1].strip()[:150]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
