"""Print the 7.74.1 vs 10.x comparison table (markdown) from results.json next to this script."""

import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))

groups = defaultdict(list)
for name, r in res["runs"].items():
    groups[(r["dataset"], r["variant"])].append(r)


def outcomes(rs, key):
    c = defaultdict(int)
    for r in rs:
        o = r["outcome"] if key is None else (r[key] or {}).get("outcome", "not run")
        c[o] += 1
    return "; ".join(f"{k} ({v})" for k, v in sorted(c.items()))


def s(rs, k, old=False):
    return sum(((r["drools_7_74_1"] or {}).get(k) or 0) if old else (r.get(k) or 0) for r in rs)


print("| dataset | variant | files | 7.74.1 outcome | 10.2.0 outcome | missing | found 7.74.1 / 10.2.0 "
      "| removed-value states | found 7.74.1 / 10.2.0 | extra states (10.2.0) | 10.2.0 s (median) "
      "| same as 7.74.1 |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
order = {"pension": 0, "car": 1, "nursery": 2}
for (ds, v), rs in sorted(groups.items(), key=lambda x: (order[x[0][0]], x[0][1])):
    secs = sorted(r["seconds"] for r in rs)
    unfinished = any(r["outcome"].startswith("not finished") for r in rs)
    same = [r["vs_7_74_1"]["same"] if r["vs_7_74_1"] else None for r in rs]
    same_txt = ("yes" if all(same) else "no") if None not in same else "n/a (7.74.1 not run)"
    found_old = s(rs, "missing_covered", True) if all(r["drools_7_74_1"] for r in rs) else "-"
    rv_old = s(rs, "removed_value_states_found", True) if all(r["drools_7_74_1"] for r in rs) else "-"
    print(f"| {ds} | {v} | {len(rs)} | {outcomes(rs, 'drools_7_74_1')} | {outcomes(rs, None)} | "
          f"{s(rs, 'missing_states')} | {found_old} / {"-" if unfinished else s(rs, "missing_covered")} | "
          f"{s(rs, 'missing_with_removed_value')} | {rv_old} / {"-" if unfinished else s(rs, "removed_value_states_found")} | "
          f"{"-" if unfinished else s(rs, "covered_not_missing")} | {secs[len(secs) // 2]} | {same_txt} |")

types = sorted({t for r in res["runs"].values() for t in r.get("message_types", [])})
old_types = sorted({t for r in res["runs"].values() for t in ((r["drools_7_74_1"] or {}).get("message_types") or [])})
print()
print("message types 10.2.0:", ", ".join(types))
print("message types 7.74.1 (same files):", ", ".join(old_types))
