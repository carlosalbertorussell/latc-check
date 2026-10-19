"""Write SUMMARY.md tables from results.json (run after run_cloud.py).

    python3 -I results/tools/cloud-drools/summarize.py > results/tools/cloud-drools/tables.md
"""

from __future__ import annotations

import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))
runs = res["runs"]


def fmt(x, nd=1):
    return "–" if x is None else f"{x:.{nd}f}"


print("## Runtime on the same machine: Drools 7.74.1 vs KIE 10.2.0 (pension and Car, -Xmx8g)\n")
print("Wall time and peak RSS from `/usr/bin/time -v`, one JVM per file (includes JVM start-up). "
      "Laptop seconds are from results/drools/domains/results.json (7.74.1) and "
      "results/tools/kie10/results.json (10.2.0).\n")
print("| File | 7.74.1 wall s | 10.2.0 wall s | 7.74.1 peak RSS MB | 10.2.0 peak RSS MB "
      "| laptop 7.74.1 s | laptop 10.2.0 s |")
print("|---|---:|---:|---:|---:|---:|---:|")
names = sorted({k.split("/", 1)[1] for k in runs if not k.split("/", 1)[1].startswith("nursery")},
               key=lambda n: (not n.startswith("pension"), n))
agg = {}
for n in names:
    a, b = runs.get(f"d7/{n}"), runs.get(f"kie10/{n}")
    la = (a or {}).get("laptop") or {}
    lb = (b or {}).get("laptop") or {}
    print(f"| {n} | {fmt(a and a['wall_s'], 2)} | {fmt(b and b['wall_s'], 2)} | {fmt(a and a['peak_rss_mb'], 0)} "
          f"| {fmt(b and b['peak_rss_mb'], 0)} | {fmt(la.get('seconds'))} | {fmt(lb.get('seconds'))} |")
    ds = n.split("_")[0]
    for tool, r, lap in (("d7", a, la), ("kie10", b, lb)):
        if r:
            g = agg.setdefault((ds, tool), {"wall": [], "rss": [], "lap": []})
            g["wall"].append(r["wall_s"])
            g["rss"].append(r["peak_rss_mb"])
            if lap.get("seconds") is not None:
                g["lap"].append(lap["seconds"])

print("\nTotals per dataset:\n")
print("| Dataset | Tool | files | total wall s (cloud) | median wall s | max peak RSS MB | total s (laptop) |")
print("|---|---|---:|---:|---:|---:|---:|")
for (ds, tool), g in sorted(agg.items()):
    print(f"| {ds} | {'7.74.1' if tool == 'd7' else '10.2.0'} | {len(g['wall'])} | {sum(g['wall']):.1f} "
          f"| {statistics.median(g['wall']):.2f} | {max(g['rss']):.0f} | {sum(g['lap']):.1f} |")

print("\n## Laptop-vs-cloud outcome agreement\n")
print("Compared fields: outcome, gap_messages, states_covered_by_gaps, missing_covered, covered_not_missing, "
      "removed_value_states_found, gap_skip_columns, message_types, and the first gap messages.\n")
print("| Tool | runs compared | identical | different | no laptop result / not finished |")
print("|---|---:|---:|---:|---:|")
for tool in ("d7", "kie10"):
    rs = [r for k, r in runs.items() if k.startswith(tool + "/")]
    cmp_ = [r["vs_laptop"] for r in rs if r.get("vs_laptop") and r["vs_laptop"]["same"] is not None]
    same = sum(1 for c in cmp_ if c["same"])
    print(f"| {'Drools 7.74.1' if tool == 'd7' else 'KIE 10.2.0'} | {len(cmp_)} | {same} | {len(cmp_) - same} "
          f"| {len(rs) - len(cmp_)} |")
diffs = [(k, r["vs_laptop"]["differences"]) for k, r in runs.items() if r.get("vs_laptop") and r["vs_laptop"]["same"] is False]
if diffs:
    print("\nDifferences:\n")
    for k, d in diffs:
        print(f"- `{k}`: {d}")

print("\n## Outcomes by variant (cloud)\n")
print("| Tool | File | outcome | gap msgs | missing states covered | removed-value states found |")
print("|---|---|---|---:|---:|---:|")
for k in sorted(runs, key=lambda k: (k.split("/")[1].startswith("nursery"), k.split("/")[1].startswith("car"), k)):
    r = runs[k]
    print(f"| {'7.74.1' if k.startswith('d7/') else '10.2.0'} | {r['file']} | {r['outcome']} | {r.get('gap_messages', '–')} "
          f"| {r.get('missing_covered', '–')}/{r['missing_states']} "
          f"| {r.get('removed_value_states_found', '–')}/{r['missing_with_removed_value']} |")

print("\n## Nursery runs\n")
print("| Tool | File | heap | cap s | finished | outcome | wall s | peak RSS MB |")
print("|---|---|---|---:|---|---|---:|---:|")
for k, r in sorted(runs.items()):
    if r["dataset"] == "nursery":
        print(f"| {'7.74.1' if k.startswith('d7/') else '10.2.0'} | {r['file']} | {r['heap']} | {r['cap_s']} "
              f"| {'yes' if r['finished'] else 'no (killed)'} | {r['outcome']} | {r['wall_s']:.1f} "
              f"| {fmt(r['peak_rss_mb'], 0)} |")
