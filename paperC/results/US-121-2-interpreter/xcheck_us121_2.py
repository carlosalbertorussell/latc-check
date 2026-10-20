"""Catala-interpreter cross-check of every non-excluded row of the corrected US-121-2.

Reuses the scope writer and the report reader of paperC/catala_more/interpreter_crosscheck.py
(imported, unchanged). That writer fixes the date of the spouse's death at |2020-06-01|;
here every surviving-spouse scope gets the date of the corrected spec (oracle.DEATH,
|2020-12-31|). All rows are written (no sampling), followed by one negative control: the
first label row with its expected output replaced by another label, which must be
reported as a disagreement.

Usage (repository root; a catala-examples checkout at 2694b17 and Catala 1.3.0 on PATH):

  python3.12 paperC/results/US-121-2-interpreter/xcheck_us121_2.py write <catala-examples dir>
  (cd <catala-examples dir> && clerk test $(cat xcheck_files.txt) --verbose --color=never > report.txt 2>&1)
  python3.12 paperC/results/US-121-2-interpreter/xcheck_us121_2.py read <catala-examples dir>/report.txt
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAPERC = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(PAPERC, "catala_more"))
import interpreter_crosscheck as X  # noqa: E402

CHUNK = 100
OTHER = {"no_exclusion": "entire_gain", "entire_gain": "no_exclusion",
         "limited_to_250000": "no_exclusion", "limited_to_500000": "no_exclusion"}


def write(examples_dir):
    mod = X.load_oracle("US-121", "US-121-2")
    with open(os.path.join(X.SPECS, "US-121", "US-121-2", "ground_truth.csv"), encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["output"] != "EXCLUDED"]
    scopes, manifest = [], []
    for i, row in enumerate(rows):
        row = dict(row)
        expected = row.pop("output")
        text = X.us2_scope(f"XUS1212_{i:04d}", mod.ORACLE.raw_of(row), expected)
        if row["return_type"] == "surviving_spouse":
            assert text.count("|2020-06-01|") == 1
            text = text.replace("|2020-06-01|", f"|{mod.DEATH}|")
        scopes.append(text)
        manifest.append({"scope": f"XUS1212_{i:04d}", "table": "US-121-2", "row": row, "expected": expected})
    neg = next(m for m in manifest if m["expected"] != "REJECTED")
    text = X.us2_scope("XUS1212_NEG", mod.ORACLE.raw_of(neg["row"]), OTHER[neg["expected"]])
    scopes.append(text.replace("|2020-06-01|", f"|{mod.DEATH}|"))
    manifest.append({"scope": "XUS1212_NEG", "table": "NEGATIVE-CONTROL", "row": neg["row"],
                     "expected": OTHER[neg["expected"]]})
    header = "> Using Us_tax_code as T\n\n```catala\n"
    names = []
    for k in range(0, len(scopes), CHUNK):
        rel = os.path.join("us_tax_code", "tests", f"xcheck_fix_us121_2_{k // CHUNK:02d}.catala_en")
        with open(os.path.join(examples_dir, rel), "w", encoding="utf-8") as f:
            f.write(header + "".join(scopes[k:k + CHUNK]) + "```\n")
        names.append(rel)
    with open(os.path.join(examples_dir, "xcheck_files.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(names) + "\n")
    with open(os.path.join(examples_dir, "xcheck_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=0)
    print(f"wrote {len(manifest)} test scopes ({len(manifest) - 1} rows and 1 negative control) in {len(names)} files")


if __name__ == "__main__":
    if sys.argv[1] == "write":
        write(sys.argv[2])
    elif sys.argv[1] == "read":
        sys.exit(X.read(sys.argv[2]))
