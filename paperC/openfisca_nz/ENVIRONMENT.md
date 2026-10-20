# OpenFisca Aotearoa environment for Paper C (NZ rules)

## Source of the encoding

- Repository: https://github.com/digitalaotearoa/openfisca-aotearoa
- Commit: `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb` (short `9d77ea7ce3c4`), committed 2025-05-06 09:40:51 +1200, "Merge pull request #72 from ackama/BM-11/non-residents"
- Package version (pyproject.toml): `openfisca-aotearoa 22.0.0`
- Licence: AGPL-3.0. The OpenFisca source is not copied into this repository; every reference to it names the URL and the commit above.

## Interpreter and packages

- OS: Linux x86_64 (kernel 6.18.44), cloud container
- Python 3.11.17 (`python3.11 -m venv`). pyproject.toml declares `requires-python >=3.9` and lists 3.9, 3.10 and 3.11 as classifiers; 3.11 is the newest listed.
- pip 26.2.2
- OpenFisca-Core 41.5.7 (pyproject.toml pins `openfisca-core[web-api] >=41.4.5, <42`)
- numpy 1.24.4
- Complete list: `requirements.lock` (`pip freeze`; the editable line names the clone at the commit above).

## Reproduce

```
paperC/openfisca_nz/setup_env.sh /path/to/work
paperC/openfisca_nz/run_official_tests.sh /path/to/work/openfisca-aotearoa /path/to/work/venv311 /tmp/logs
```

The oracles in `paperC/specs/NZ-*/oracle.py` locate the clone through the environment variable `OPENFISCA_AOTEAROA_DIR` (needed only for `--check-official`, which reads the YAML test files); they import `openfisca_aotearoa` from the active interpreter.

## Official test results (verbatim logs in `test_logs/`)

Command, run from the clone root:
`openfisca test -c openfisca_aotearoa openfisca_aotearoa/tests/social_security/<rule> -v`

| Rule folder | Test files | Cases | Result |
|---|---|---|---|
| supported_living_payment | base.yaml (43), entitled.yaml (7) | 50 | 50 passed, exit 0 |
| accommodation_supplement | 2018/*.yaml (41), 1964/entitled.yaml (6) | 47 | 47 passed, exit 0 |
| sole_parent_support | sole_parent_support__entitled.yaml (12), __split_care.yaml (7), __benefit.yaml (6) | 25 | 25 passed, exit 0 |

Run date: 2026-10-20.

## Files in this folder

| File | Purpose |
|---|---|
| `requirements.lock` | `pip freeze` of the virtualenv |
| `setup_env.sh` | clone at the commit, create the Python 3.11 virtualenv, install with the lock as constraints |
| `run_official_tests.sh` | run `openfisca test` on the three rule folders, writing `test_logs/` |
| `test_logs/` | verbatim `openfisca test -v` output (50, 47 and 25 passed) |
| `oracle_core.py`, `rules/<ID>.py`, `build_oracles.py` | parts of each `oracle.py` and the script that assembles them (`--check` verifies) |
| `crosscheck.py` | OpenFisca-free re-implementation of every table, compared row by row |
| `summarise.py` | the numbers of `paperC/specs/README-NZ.md` |
| `case_table.py`, `docs/`, `make_docs.py` | CONVERSION.md bodies and the generated official-case tables; ENVIRONMENT.md and SHA256SUMS of each folder |
| `logs/` | `check_official_<ID>.txt` (one line per official case or person) and `summary.txt` |
| `rebuild_all.sh` | rebuild every table, log, doc and checksum from scratch |
| `supplementary/NZ-AS-1964/` | Accommodation Supplement under the SSA 1964 formula, same format, not a sample |
