"""How often the observed-domain trap occurs: run ``latc_check.trap_frequency``.

    python -I run_trap_frequency.py [--draws 20000] [--seed 20210101]

Writes ``results/trap_frequency/results.json``, ``trap_frequency.csv`` and
``SUMMARY.md``.  Standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # also works under python -I

from latc_check.trap_frequency import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
