"""Random sample of the exposed decision tables of the DMN corpus: run ``latc_check.dmn_exposed_sample``.

    python -I run_dmn_exposed_sample.py [--results results/corpus/results.json] [--out results/corpus]

Reads ``results.json`` (from ``run_dmn_corpus.py``) and the hand classification
``exposed_sample_classes.json`` in the output folder, and writes
``exposed_sample.csv`` and ``EXPOSED_SAMPLE.md`` there.  Standard library only.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # also works under python -I

from latc_check import dmn_exposed_sample as des  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", default=os.path.join(HERE, "results", "corpus", "results.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "results", "corpus"))
    a = ap.parse_args()
    with open(a.results, encoding="utf-8") as fh:
        res = json.load(fh)
    sample = des.write_outputs(res, a.out, os.path.join(a.out, "exposed_sample_classes.json"))
    print(f"frame={len(des.exposed_frame(res))} sample={len(sample)}")


if __name__ == "__main__":
    main()
