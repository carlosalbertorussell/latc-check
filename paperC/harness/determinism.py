"""CTRL-DET: run the harness twice from two clean checkouts and compare bytes.

    python -m paperC.harness.determinism --spec paperC/specs/<ID> --report <file.json>

Clones the current HEAD commit into two fresh temporary directories, runs
``python -m paperC.harness.run`` in each (writing to paperC/results/<ID> inside
the clone), and compares runs.csv, controls.csv, summary.md and manifest.json.
Only committed files take part, so commit the harness and spec first.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

from .run import REPO
from .spec import sha256_file

OUTPUTS = ("runs.csv", "controls.csv", "summary.md", "manifest.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, help="spec folder, relative to the repository root")
    ap.add_argument("--report", required=True)
    args = ap.parse_args(argv)
    spec_rel = os.path.relpath(os.path.abspath(args.spec), REPO)
    sample_id = os.path.basename(spec_rel.rstrip("/"))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                            text=True, check=True).stdout.strip()
    hashes = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in ("a", "b"):
            clone = os.path.join(tmp, k)
            subprocess.run(["git", "clone", "-q", "--no-hardlinks", REPO, clone], check=True)
            subprocess.run(["git", "checkout", "-q", commit], cwd=clone, check=True)
            out = os.path.join("paperC", "results", sample_id)
            subprocess.run([sys.executable, "-m", "paperC.harness.run", "--spec", spec_rel,
                            "--out", out, "--quiet"], cwd=clone, check=True)
            hashes.append({n: sha256_file(os.path.join(clone, out, n)) for n in OUTPUTS})
    identical = hashes[0] == hashes[1]
    report = {"control": "CTRL-DET", "sample_id": sample_id, "commit": commit,
              "python": sys.version.split()[0], "identical": identical,
              "run_a": hashes[0], "run_b": hashes[1]}
    with open(args.report, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(f"CTRL-DET {'PASS' if identical else 'FAIL'}: outputs {'are' if identical else 'are NOT'} byte-identical")
    return 0 if identical else 1


if __name__ == "__main__":
    sys.exit(main())
