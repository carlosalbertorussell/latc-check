"""Test inputs that no rule mentions: run ``latc_check.dmn_testinputs`` over the corpus.

    python -I run_dmn_testinputs.py [--corpus ../corpus] [--tck ../dmn-tck] [--out results/corpus]

Uses the sources of ``run_dmn_corpus.py`` (same clones, same commits) and writes
``testinputs.json`` and ``TESTINPUTS.md`` to the output folder; the corpus results
(``results.json``, ``inputs.csv``, ``SUMMARY.md``, ``sources.json``) are left unchanged.
Nothing is downloaded: the other formats are only counted from the local git trees.
When no TCK test file (``*-test-NN.xml``) is found, a warning names the pattern and the TCK
path, nothing is written, and the exit status is 1.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # also works under python -I

import run_dmn_corpus  # noqa: E402
from latc_check import dmn_testinputs  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", default=os.path.join(HERE, "..", "corpus"))
    ap.add_argument("--tck", default=os.path.join(HERE, "..", "dmn-tck"))
    ap.add_argument("--tools", default=os.path.join(HERE, "..", "tools"))
    ap.add_argument("--out", default=os.path.join(HERE, "results", "corpus"))
    a = ap.parse_args()
    sources, missing = run_dmn_corpus.build_sources(a.corpus, a.tck, a.tools)
    recorded = os.path.join(a.out, "sources.json")
    if os.path.isfile(recorded):
        with open(recorded, encoding="utf-8") as fh:
            shas = {s["name"]: s.get("sha") for s in json.load(fh)["sources"]}
        for s in sources:
            if s["name"] in shas and shas[s["name"]] != s["sha"]:
                print(f"warning: {s['name']} is at {s['sha']}, sources.json records {shas[s['name']]}")
    try:
        res = dmn_testinputs.run(sources, a.out)
    except dmn_testinputs.NoTestFiles as e:
        print(e, file=sys.stderr)
        return 1
    for g, v in res["summary"].items():
        print(f"{g:13s} test files={v['test_files']} cases={v['test_cases']} values={v['input_values']} "
              f"resolved={v['input_values_resolved']} links={v['links']} string={v['links_string_value']} "
              f"unmentioned={v['unmentioned']} no-match={v['unmentioned_no_match']} "
              f"(distinct {v['distinct_unmentioned']}/{v['distinct_unmentioned_no_match']})")
    print("other formats (names only):", res["inventory_totals"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
