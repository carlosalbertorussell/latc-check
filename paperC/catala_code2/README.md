# Catala build used by the second coder (FR2: APL eligibility and US section 121)

This folder holds the Python that Catala 1.3.0 generates from catala-examples,
the Catala Python runtime, the official `clerk test` results, and the parts
from which the oracles of `paperC/specs2/FR-APL-*` and `paperC/specs2/US-121-*`
are assembled. It was built independently of the first coder (see
`paperC/specs2/README-FR2-CODE2.md`, "Blinding").

## Provenance

| Item | Value |
|---|---|
| Rules | https://github.com/CatalaLang/catala-examples, commit `2694b17ddd7c2246e207e8f077d586349ee5abea` |
| Compiler | Catala `1.3.0` (opam package `catala.1.3.0`); `catala --version` and `clerk --version` print `1.3.0` |
| Python runtime | `catala_runtime.py`, `dates.py` from the opam install (`$(opam var lib)/catala/runtime/python/src/catala`), byte-identical to the copy clerk writes to `_targets/python/libcatala` |
| OCaml / opam | 4.14.2 (switch `catala`) / 2.1.5 (Ubuntu package) |
| Host | Ubuntu 24.04, x86_64, Claude Code cloud container, 2026-10-20 |
| Python used for the tables | 3.12.3 (`python3.12`); 3.13.16 gives byte-identical `ground_truth.csv` files |

## Commands (as run)

```sh
# Toolchain (as in paperC/catala_family_benefits/README.md of branch paperc-catala-family-benefits)
apt-get update && apt-get install -y opam ninja-build libgmp-dev pkg-config
export OPAMYES=1
opam init --disable-sandboxing --bare -n
opam switch create catala 4.14.2
eval $(opam env --switch=catala)
opam install catala.1.3.0

# Sources
git clone https://github.com/CatalaLang/catala-examples
cd catala-examples
git checkout 2694b17ddd7c2246e207e8f077d586349ee5abea

# Official tests (full output in clerk_test_results.txt)
clerk test aides_logement/tests/tests_eligibilite_apl.catala_fr                  # interpreter
clerk test aides_logement/tests/tests_eligibilite_apl.catala_fr --backend=python
clerk test us_tax_code/tests/test_section_121.catala_en                          # interpreter
clerk test us_tax_code/tests/test_section_121.catala_en --backend=python         # runs nothing, see below

# Python for the housing aids (clerk target "aides-logement" of clerk.toml)
clerk build aides-logement
cp _targets/python/aides-logement/Aides_logement.py \
   _targets/python/allocations-familiales/{Allocations_familiales,Bmaf,Prestations_familiales}.py \
   _targets/python/smic/{France,Smic}.py \
   _targets/python/libcatala/*_fr.py _targets/python/libcatala/*_en.py _targets/python/libcatala/*_internal.py \
   <this folder>/generated/
cp _targets/python/libcatala/{catala_runtime,dates}.py <this folder>/runtime/

# Python for US section 121: the clerk target "us-tax-code" declares only the
# OCaml backend, so the module was compiled with the Catala compiler directly.
catala python us_tax_code/us_tax_code.catala_en -o <this folder>/generated/Us_tax_code.py
```

`catala python` on `us_tax_code.catala_en` prints one warning (sub-scope
`period_merge` of `Section121TwoPersons` is declared and never used,
`section_121.catala_en:86`) and produces the module.

`generated/__init__.py` is a one-line package marker written for this
repository: the modules import each other with `from . import X`, and clerk's
own `__init__.py` files (`__all__ = [Aides_logement]`) raise `NameError` on
import. Every other file in `generated/` and `runtime/` is unedited compiler
or runtime output.

## Official test results (Catala 1.3.0)

| File | Interpreter | Python backend |
|---|---|---|
| `aides_logement/tests/tests_eligibilite_apl.catala_fr` | 7 of 7 passed (1 typecheck + 3 `test-scope` CLI blocks + 3 `#[test]` scopes) | 3 of 3 `#[test]` scopes passed |
| `us_tax_code/tests/test_section_121.catala_en` | 12 of 12 passed (6 CLI blocks + 6 `#[test]` scopes) | no test run: clerk.toml gives target `us-tax-code` the OCaml backend only |

`clerk_test_results.txt` holds the verbose output of these four runs and the
JUnit XML report (19 test cases, 0 failures). The Python re-runs of the
mappable official tests are part of each oracle (`oracle.py --check-official`):
APL `Exemple1` passes through the generated Python, and the six section 121
tests `Test1` to `Test6` pass through the generated `Us_tax_code.py`
(4 in US-121-1, 2 in US-121-2).

## Behaviour of the encodings found while enumerating

* **Section 121 (b)(3) cannot be evaluated.** `section_121.catala_en:376`
  compares `date_of_sale_or_exchange - other_sale.date_of_sale_or_exchange`
  (a duration in days) with `2 year`. Catala 1.3.0 rejects this comparison at
  run time ("ambiguous comparison between durations in different units"), so
  every input with `MostRecentSaleWhereSection121aApplied` raises a `DateError`.
  The interpreter does the same: `clerk run` on a scratch test scope with
  ownership and use 2017-01-01..2021-01-01 and a previous sale on 2018-06-01
  stopped with that error at `section_121.catala_en:376.9-81`. The official
  tests only use `NoOtherSaleWhereSection121aApplied`.
* **APL in Mayotte, 2024-01-01 to 2024-10-31.** `smic/Smic.catala_fr`
  defines the Mayotte hourly SMIC twice for that period (8,80 € and 8,98 €),
  and the eligibility scope evaluates it through the family-benefits sub-scope,
  so these inputs raise a Catala `Conflict`.
* **APL in Mayotte with R844-4.** The Mayotte surface rule
  (`code_construction_reglementaire.catala_fr:5613`) and the R844-4 rule
  (`:5530`) are both exceptions to the label `base` of
  `condition_logement_surface`; when both apply the scope raises a `Conflict`.
* **APL, French applicant in Mayotte.** The Mayotte version of
  `condition_nationalité` (`code_construction_legislatif.catala_fr:1389-1402`)
  maps `Française` to `faux`, so a French applicant residing in Mayotte is
  never eligible.
* **APL, location-accession.** `caractéristiques_prêt_l831_1_6`
  (`prologue.catala_fr:387`) has no definition, so its default `faux` makes
  `LocationAccession` ineligible for every loan.
* **APL, dates before 2019-09-01.** `personnes_à_charge_prises_en_compte` is
  defined from 2019-09-01 (`archives.catala_fr:10`) and the SMIC from
  2019-01-01, so earlier dates raise `NoValue`. The tables start at 2019-09-01.

## Files

| Path | What it is |
|---|---|
| `generated/` | Python generated by Catala 1.3.0: `Aides_logement`, `Allocations_familiales`, `Bmaf`, `Prestations_familiales`, `France`, `Smic`, `Us_tax_code`, and the standard-library modules (`*_fr.py`, `*_en.py`, `*_internal.py`) |
| `runtime/` | `catala_runtime.py`, `dates.py` (Catala 1.3.0 Python runtime; needs Python 3.12 or later) |
| `oracle_parts/` | Sources of the oracles: `apl_common.py`, `fr_dates.py`, `fr_apl_1.py` .. `fr_apl_5.py`, `us_common.py`, `us_121_1.py`, `us_121_2.py` |
| `oracle_template.py` | Generic part (exclusions, REJECTED handling, enumeration, CSV writers, official check) appended to every oracle |
| `make_oracles.py` | Writes `paperC/specs2/<ID>/oracle.py` from the parts, so each oracle file is self-contained apart from `generated/` and `runtime/` |
| `clerk_test_results.txt` | Output of the official `clerk test` runs |
| `LICENSE-catala-examples.txt` | Apache License 2.0 of catala-examples |

To rebuild a table: `python3 make_oracles.py`, then in `paperC/specs2/<ID>/`
run `python3.12 oracle.py --write-spec --write-official --enumerate --check-official`.

## Licence and attribution

The Catala sources (CatalaLang/catala-examples) and the Catala compiler and
runtime (CatalaLang/catala) are licensed under the Apache License 2.0; the
files in `generated/` and `runtime/` derive from them and are redistributed
under that licence (text in `LICENSE-catala-examples.txt`). The encodings are
the work of the Catala authors (https://github.com/CatalaLang/catala-examples).
