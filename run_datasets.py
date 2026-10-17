"""Run the public-dataset experiments (UCI Car, UCI Nursery, DMN TCK). See README.md."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # also works under python -I

from latc_check.datasets_report import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
