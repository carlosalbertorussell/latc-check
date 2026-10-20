"""Write CONVERSION.md, ENVIRONMENT.md and SHA256SUMS into each NZ folder.

CONVERSION.md = docs/<ID>.md + docs/common.md + the official-case log as a table
(case_table.py over logs/check_official_<ID>.txt).  Run after the oracles.
Usage: python make_docs.py
"""
import hashlib
import io
import os
import subprocess
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_oracles  # noqa: E402
import case_table  # noqa: E402

ENV = """# {id} environment

* Encoding: https://github.com/digitalaotearoa/openfisca-aotearoa at commit
  `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb` (openfisca-aotearoa 22.0.0, 6 May 2025, AGPL-3.0).
  Not copied into this repository.
* Python 3.11.17; OpenFisca-Core 41.5.7; numpy 1.24.4; PyYAML 6.0.3. Full list:
  `paperC/openfisca_nz/requirements.lock` (`pip freeze`); notes in `paperC/openfisca_nz/ENVIRONMENT.md`.
* `oracle.py` needs `openfisca_aotearoa` importable; `--check-official` also reads the
  YAML tests of the clone (environment variable `OPENFISCA_AOTEAROA_DIR`, defaulting to
  the source tree of the installed package, which is the clone for an editable install).

Install (from the repository root):

```
paperC/openfisca_nz/setup_env.sh /path/to/work
export OPENFISCA_AOTEAROA_DIR=/path/to/work/openfisca-aotearoa
```

Rebuild and check (from this folder):

```
/path/to/work/venv311/bin/python oracle.py --enumerate        # {rows} rows, one simulation per row
/path/to/work/venv311/bin/python oracle.py --check-official   # official YAML cases, directly and via the oracle
python3 ../../openfisca_nz/crosscheck.py                      # OpenFisca-free re-implementation (path from paperC/specs/<ID>)
```

`oracle.py` is assembled from `paperC/openfisca_nz/rules/{id}.py` and
`paperC/openfisca_nz/oracle_core.py` by `paperC/openfisca_nz/build_oracles.py`
(`--check` verifies the copy).
"""


def sha_file(folder):
    names = sorted(n for n in os.listdir(folder) if n != "SHA256SUMS" and os.path.isfile(os.path.join(folder, n)))
    with open(os.path.join(folder, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
        for n in names:
            with open(os.path.join(folder, n), "rb") as g:
                f.write(f"{hashlib.sha256(g.read()).hexdigest()}  {n}\n")


def main():
    common = open(os.path.join(HERE, "docs", "common.md"), encoding="utf-8").read().strip()
    for rule_id, folder in build_oracles.TARGETS.items():
        head = open(os.path.join(HERE, "docs", rule_id + ".md"), encoding="utf-8").read().strip()
        buf = io.StringIO()
        with redirect_stdout(buf):
            case_table.main(os.path.join(HERE, "logs", f"check_official_{rule_id}.txt"))
        summary = open(os.path.join(HERE, "logs", f"check_official_{rule_id}.txt"), encoding="utf-8").read().split("\n\n", 1)[0]
        text = (head + "\n\n" + common + "\n\n## Official case log\n\n"
                + f"Output of `oracle.py --check-official --log` (`paperC/openfisca_nz/logs/check_official_{rule_id}.txt`), "
                + "paths relative to `openfisca_aotearoa/tests/social_security/`:\n\n```\n" + summary + "\n```\n\n"
                + buf.getvalue())
        with open(os.path.join(folder, "CONVERSION.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8") as f:
            rows = sum(1 for _ in f) - 1
        with open(os.path.join(folder, "ENVIRONMENT.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(ENV.format(id=rule_id, rows=f"{rows:,}"))
        sha_file(folder)
        print(f"{rule_id}: docs and SHA256SUMS written")


if __name__ == "__main__":
    main()
