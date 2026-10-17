"""Run the sensitivity and policy-change experiments (Section 9.6). See README.md."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # also works under python -I

from latc_check.sensitivity import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
