# Paper C, New Zealand rules: second coder's conversion

Three OpenFisca Aotearoa eligibility rules, converted into finite decision tables by a
second coder working independently of the first. A later comparison of the two conversions
measures inter-coder agreement. Format: `paperC/specs/FORMAT.md` and `paperC/PROTOCOL.md`
as registered on `origin/paperc-harness`.

| Sample | Entry variable | Fixed period | Attributes | Combinations | Valid | EXCLUDED | REJECTED | Official person-cases | Mapped (pass) | Distinct mapped conditions |
|---|---|---|---|---|---|---|---|---|---|---|
| `NZ-SLP` | `supported_living_payment__entitled` | 2019-W01 | 7 | 256 | 256 (51 True, 205 False) | 0 | 0 | 13 | 13 (13/13) | 12 |
| `NZ-AS` | `accommodation_supplement__entitled` | 2018-W01 | 9 | 512 | 384 (5 True, 379 False) | 128 | 0 | 12 | 6 (6/6) | 6 |
| `NZ-SPS` | `sole_parent_support__entitled` | 2019-W05 | 11 | 2,048 | 2,048 (189 True, 1,859 False) | 0 | 0 | 26 | 8 (8/8) | 7 |

All tables are far below the 200,000 limit, so none is split. "Mapped (pass)" counts the
official person-cases that map onto the table, and how many of them give the same output
through the oracle as the official test expects. Every official test of the three rules also
passes under `openfisca test`; the run is recorded in
`paperC/openfisca_code2/openfisca_test_results.txt`.

## Declared values that the official examples never use

* `NZ-SLP`: none. Every declared label appears in `official_examples.csv`.
* `NZ-AS`: `ordinarily_resident_in_nz=False`, `below_income_threshold=False`,
  `below_cash_threshold=False` (3 values).
* `NZ-SPS`: `residential_requirement=False`, `age=<20`, `principal_caregiver=False`,
  `child_dependent=False`, `child_age=14+` (5 values).

## The main choices in brief

Each choice, with its source, is in the sample's `CONVERSION_2.md`. In short:

* Formulas are traced to their leaves within the rule's own sections. General terms that
  the rule reads as one condition stay whole: the s 16 residential requirement, Schedule 2
  dictionary terms (dependent children, dependent child, principal caregiver, in a
  relationship) and immigration status.
* `NZ-AS` is converted at 2018-W01, where the Social Security Act 1964 formula applies. Six
  of its seven official tests sit there. The single 2018-Act test (2022-W01) does not map.
* `NZ-SPS` fixes a family of one principal and one child, the shape every official
  family test uses. With one child, s 32 split care reduces to True for the principal.
* One exclusion in total: in `NZ-AS`, a permanent resident visa holder who is not a resident
  (`PR-IMPLIES-RESIDENT`). The encoding defines `immigration__resident` to include
  permanent residents.

## Files

`paperC/specs2/<ID>/` holds `spec.json`, `ground_truth.csv`, `official_examples.csv`,
`oracle.py`, `ENVIRONMENT.md`, `CONVERSION_2.md` and `SHA256SUMS`. Two departures from the
wording of FORMAT.md, both made on instruction for the second coder:

* the folders sit under `paperC/specs2/` (FORMAT.md names `paperC/specs/`);
* the conversion record is named `CONVERSION_2.md` (FORMAT.md names `CONVERSION.md`).

`oracle.py` takes `--enumerate` and `--check-official` as FORMAT.md requires. It also takes
`--write-official`, which, together with `--check-official`, rewrites
`official_examples.csv`. Environment and versions: each `ENVIRONMENT.md` and
`paperC/openfisca_code2/pip_freeze.txt` (Python 3.11.17, openfisca-core 41.5.7).

Reproduce (virtualenv as in `ENVIRONMENT.md`):

```sh
cd paperC/specs2/NZ-SLP   # likewise NZ-AS, NZ-SPS
python oracle.py --check-official --write-official
python oracle.py --enumerate
sha256sum -c SHA256SUMS
```

## Blinding

The second coder followed these rules throughout and states that they were kept:

* No checkout, diff, `git show`, log or file read of the branches `paperc-data-nz`,
  `paperc-data-fr`, `paperc-data-fr2`, any `paperc-run-*` or `paperc-verify-*` branch, or any
  other `paperc-code2-*` branch. Only `main` and `paperc-harness` were fetched.
* No `paperC/specs/` folder was read on any branch. The only files read from
  `origin/paperc-harness` were `paperC/specs/FORMAT.md` and `paperC/PROTOCOL.md`, through
  `git show origin/paperc-harness:<path>`.
* Every interpretive choice (which inputs, where to cut numeric ranges, which period, which
  combinations to exclude, how to map official cases) was made from the OpenFisca Aotearoa
  source, its parameters and tests, and the legislation they cite.

Branch `paperc-code2-nz` was created from `main` (commit `c6d2802`).

## Licence of the encoding

OpenFisca Aotearoa (https://github.com/digitalaotearoa/openfisca-aotearoa, version 22.0.0,
commit `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb`) is licensed under the GNU Affero
General Public License v3.0. Its source code is not copied into this repository: the
samples reference it by URL and commit, and `oracle.py` imports the separately installed
package at run time. The tables in `ground_truth.csv` and `official_examples.csv` are
outputs computed by running that software. File paths and line numbers cited in
`spec.json` and `CONVERSION_2.md` refer to that commit.
