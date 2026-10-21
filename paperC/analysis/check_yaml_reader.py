"""Check common.load_yaml against PyYAML on the 19 official test files of the NZ rules.

PyYAML is used only by this check (it is not needed by the analyses). Test names, which
are folded block scalars, are compared after collapsing whitespace.
Run from the repository root:  python3.12 -I paperC/analysis/check_yaml_reader.py
"""

import datetime
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML not available: check skipped")


def norm(x):
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, datetime.date):
        return x.isoformat()
    return x


def names(cases):
    return [dict(c, name=" ".join(str(c.get("name", "")).split())) for c in cases]


n = bad = 0
root = common.ext_path("openfisca-aotearoa", "openfisca_aotearoa", "tests", "social_security")
for d in ("supported_living_payment", "accommodation_supplement", "sole_parent_support"):
    for p in sorted(glob.glob(os.path.join(root, d, "**", "*.yaml"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            text = f.read()
        n += 1
        if names(norm(yaml.safe_load(text))) != names(common.load_yaml(text)):
            bad += 1
            print("differs:", os.path.relpath(p, root))
print(f"{n} files, {bad} differ")
