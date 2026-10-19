"""Run the public-dataset experiments on UCI Lenses, Balance Scale and the MONK's problems."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # also works under python -I

from latc_check.datasets_more import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
