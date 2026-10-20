# US-121-1 environment

## To use this folder

* Python 3.12 or later, standard library only (tested with CPython 3.13.16 and
  3.12.3 on Ubuntu 24.04.5 LTS, x86_64). Python 3.11 and earlier cannot import the
  Catala 1.3.0 runtime (PEP 695 generics, `typing.override`).
* The Python build of the Catala encoding in `paperC/catala_more/` of this repository
  (`generated/`, `runtime/catala/`, and the helper modules `oracle_common.py`,
  `us121_inputs.py`,
  `run_official_tests_us121.py`). `oracle.py` finds it at `../../../catala_more` relative to this folder.
  No package needs installing.

```sh
cd paperC/specs/US-121/US-121-1
python3 oracle.py --check-official   # official tests, directly and through the oracle
python3 oracle.py --enumerate        # rewrites ground_truth.csv (same bytes)
python3 oracle.py --write-official   # rewrites official_examples.csv (same bytes)
python3 oracle.py --check-bands      # extra points inside every interval label
```

`oracle.py` stops with an error if `spec.json` differs from the table definition it
holds (`--write-spec` rewrites it). The enumeration was run with Python 3.13.16 and
re-run with Python 3.12.3; both runs wrote byte-identical files.

## Encoding and how it was built

| Item | Value |
|---|---|
| Rules | https://github.com/CatalaLang/catala-examples at commit `2694b17ddd7c2246e207e8f077d586349ee5abea` |
| Official tests | `us_tax_code/tests/test_section_121.catala_en` |
| Compiler | Catala 1.3.0 (opam package `catala.1.3.0`), OCaml 4.14.2, opam 2.1.5 |
| Python runtime | CatalaLang/catala tag `1.3.0`, `runtimes/python/src/catala` |

Install and build commands (Ubuntu 24.04, as root):

```sh
apt-get update && apt-get install -y opam ninja-build libgmp-dev pkg-config
export OPAMYES=1
opam init --disable-sandboxing --bare -n
opam switch create catala 4.14.2
eval $(opam env --switch=catala)
opam install catala.1.3.0
git clone https://github.com/CatalaLang/catala-examples
cd catala-examples && git checkout 2694b17ddd7c2246e207e8f077d586349ee5abea
clerk test us_tax_code/tests/test_section_121.catala_en
clerk build us_tax_code/python/Us_tax_code.py
```

`paperC/catala_more/README.md` gives the full procedure, the clerk results and the
provenance of every generated file.
