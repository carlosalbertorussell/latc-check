"""Export the shared DMN inputs for the cross-tool audit (results/tools/inputs/).

Cases: pension with each Age value removed, Car with one value of each attribute removed,
Nursery with finance=convenient removed; variants V1, V2, V3b, V4 of drools_domains. Writes
manifest.json with the ground truth. Run: python -I run_tool_inputs.py
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
from latc_check import datasets, drools_domains as dd  # noqa: E402
from latc_check import examples as ex  # noqa: E402

OUT = os.path.join(REPO, "results", "tools", "inputs")
os.makedirs(OUT, exist_ok=True)
VARS = ["V1", "V2", "V3b", "V4"]
manifest = {"variants": {v: dd.VARIANTS[v] for v in VARS}, "cases": []}


def emit(dataset, attr, value, t0, variants):
    miss = dd.missing_states(t0)
    removed = sum(1 for c in miss if c[[a.name for a in t0.attributes].index(attr)] == value)
    tbl = dd.dmn_of(t0)
    obs = dd.observed_values(t0)
    files = {}
    for v in variants:
        name = f"{dataset}_{attr}_{value}_{v}".replace(" ", "_").replace("<", "lt").replace(">", "gt").replace("=", "").replace("≥", "ge")
        path = os.path.join(OUT, name + ".dmn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(dd.export_variant(tbl, name, v, removed=attr, observed=obs))
        files[v] = os.path.relpath(path, REPO).replace("\\", "/")
    manifest["cases"].append({"dataset": dataset, "attribute": attr, "removed_value": value,
                              "rules": len(t0.rows), "attributes": [a.name for a in t0.attributes],
                              "declared_domains": {a.name: list(a.domain) for a in t0.attributes},
                              "missing_states": len(miss), "missing_with_removed_value": removed,
                              "files": files})


for a, v, t0 in dd.removal_cases(ex.pension_table(), ["Age"]):
    emit("pension", a, v, t0, VARS)
car = datasets.car()
seen = set()
for a, v, t0 in dd.removal_cases(car):
    if a not in seen:
        seen.add(a)
        emit("car", a, v, t0, VARS)
nur = datasets.nursery()
for a, v, t0 in dd.removal_cases(nur, ["finance"]):
    emit("nursery", a, v, t0, ["V1", "V2", "V4"])
    break
with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)
print(len(manifest["cases"]), "cases;", sum(len(c["files"]) for c in manifest["cases"]), "files")
for c in manifest["cases"]:
    print(c["dataset"], c["attribute"], c["removed_value"], c["rules"], "rules,", c["missing_states"], "missing")
