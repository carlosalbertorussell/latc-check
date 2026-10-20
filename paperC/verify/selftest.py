"""Cross-check of recompute.py's index arithmetic against literal set algebra
over label tuples (naive_metrics). Usage: python3.12 selftest.py <spec folder> <max cells>"""
import sys
import recompute as rc

s = rc.Sample(sys.argv[1])
s.load()
limit = int(sys.argv[2])
sets = []
if s.official:
    sets.append(("OFFICIAL", "-", "-", rc.source_official(s)))
sets.append(("FULL", "-", "-", rc.source_full(s)))
for src, fn in (("UNIFORM", rc.source_uniform), ("ZIPF", rc.source_zipf)):
    for n in rc.SIZES:
        for seed in rc.SEEDS:
            sets.append((src, n, seed, fn(s, n, seed)))
if limit < len(sets):
    # keep OFFICIAL/FULL, then an even spread of seeded cells
    head = [x for x in sets if x[0] in ("OFFICIAL", "FULL")]
    rest = [x for x in sets if x[0] not in ("OFFICIAL", "FULL")]
    step = max(1, len(rest) // (limit - len(head)))
    sets = head + rest[::step]
bad = 0
for src, n, seed, ex in sets:
    for cond in rc.CONDITIONS:
        a = rc.run_metrics(s, ex, cond)
        b = rc.naive_metrics(s, ex, cond)
        for k, v in b.items():
            if a[k] != v:
                bad += 1
                print("DIFF", src, n, seed, cond, k, a[k], v)
print(s.id, "cells checked:", len(sets), "x 3 conditions; differences:", bad)
