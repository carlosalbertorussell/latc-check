"""What the random-table generator's redraw does to the cases: run ``latc_check.randomized.generator_profile``.

    python -I run_generator_profile.py [--trials 1000] [--seed 20210101] [--out results/generator_profile.json]

Replays the draws of the three randomized scenarios of ``run_report.py`` and writes the mean
share of the valid space covered by T0 and the mean space sizes per scenario, with the same
means for the generator without its coverage redraw.  Standard library only.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # also works under python -I

from latc_check.randomized import generator_profile  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trials", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20210101)
    ap.add_argument("--out", default=os.path.join(HERE, "results", "generator_profile.json"))
    a = ap.parse_args()
    res = generator_profile(a.trials, a.seed)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    for k, v in res.items():
        print(k, {x: round(y, 3) if isinstance(y, float) else y for x, y in v.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
