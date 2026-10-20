# NZ-AS-1964 environment

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
/path/to/work/venv311/bin/python oracle.py --enumerate        # 512 rows, one simulation per row
/path/to/work/venv311/bin/python oracle.py --check-official   # official YAML cases, directly and via the oracle
python3 ../../openfisca_nz/crosscheck.py                      # OpenFisca-free re-implementation (path from paperC/specs/<ID>)
```

`oracle.py` is assembled from `paperC/openfisca_nz/rules/NZ-AS-1964.py` and
`paperC/openfisca_nz/oracle_core.py` by `paperC/openfisca_nz/build_oracles.py`
(`--check` verifies the copy).
