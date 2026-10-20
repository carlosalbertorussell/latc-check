"""Run the DroolsCheck driver on the 39 shared audit files and keep the raw output.

    python -I replication/tool_audit/run_drools.py --driver-dir DIR --java JAVA --out DIR
        [--only SUBSTR ...] [--skip SUBSTR ...] [--timeout SECONDS]

``--driver-dir`` holds ``out/DroolsCheck.class`` and ``lib/*.jar`` (see README.md: one such
folder per Drools version).  Each file of ``results/tools/inputs/manifest.json`` runs in its
own JVM through ``latc_check.drools_domains.run_one``, the call the paper's runs used, and its
standard output is written to ``<out>/<file>.dmn.txt`` (with a final ``# ERROR:`` line if the
JVM failed or timed out), the layout of ``results/tools/cloud-drools/raw/``.  Wall times go to
``<out>/times.json``.  Files that already have output are skipped, so an interrupted run can be
resumed.  Pass JVM options such as a larger heap through the JAVA_TOOL_OPTIONS environment
variable.  Score the folder with ``score.py``.  Standard library only.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from latc_check.drools_domains import run_one  # noqa: E402

INPUTS = os.path.join(REPO, "results", "tools", "inputs")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--driver-dir", required=True, help="folder with out/DroolsCheck.class and lib/*.jar")
    ap.add_argument("--java", default="java", help="java executable")
    ap.add_argument("--out", required=True, help="folder for the raw outputs")
    ap.add_argument("--only", nargs="*", default=None, help="run only files whose name contains one of these")
    ap.add_argument("--skip", nargs="*", default=None, help="skip files whose name contains one of these")
    ap.add_argument("--timeout", type=float, default=7200, help="seconds per file (default 2 h)")
    a = ap.parse_args(argv)

    with open(os.path.join(INPUTS, "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    os.makedirs(a.out, exist_ok=True)
    tpath = os.path.join(a.out, "times.json")
    times = {}
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as fh:
            times = json.load(fh)
    names = [os.path.basename(rel) for c in manifest["cases"] for rel in c["files"].values()]
    missing = [n for n in names if not os.path.exists(os.path.join(INPUTS, n))]
    if missing:
        print(f"{len(missing)} input files are missing; run `python -I run_tool_inputs.py` first", file=sys.stderr)
        return 1
    for name in names:
        if a.only and not any(s in name for s in a.only):
            continue
        if a.skip and any(s in name for s in a.skip):
            continue
        raw = os.path.join(a.out, name + ".txt")
        if os.path.exists(raw):
            continue
        print(f"running {name} ...", flush=True)
        stdout, secs, err = run_one(os.path.join(INPUTS, name), a.driver_dir, a.java, a.timeout)
        with open(raw, "w", encoding="utf-8") as fh:
            fh.write(stdout + ("\n# ERROR: " + err if err else ""))
        times[name] = round(secs, 1)
        with open(tpath, "w", encoding="utf-8") as fh:
            json.dump(times, fh, indent=1)
        print(f"  {secs:.1f} s" + (f"  {err[:200]}" if err else ""), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
