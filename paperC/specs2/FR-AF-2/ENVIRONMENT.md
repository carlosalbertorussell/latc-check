# Environment

| Item | Value |
|---|---|
| Python | 3.13.16 (CPython) used to write `ground_truth.csv` and `official_examples.csv`; 3.12.3 checked to give byte-identical files. Python 3.12 or later is required (the Catala 1.3.0 runtime uses PEP 695 generics). |
| Packages | none outside the standard library |
| Encoding | `paperC/catala_family_benefits/generated/` (Catala 1.3.0 Python build of CatalaLang/catala-examples commit `2694b17ddd7c2246e207e8f077d586349ee5abea`), unedited |
| Runtime | `paperC/catala_family_benefits/runtime/catala/` (Catala 1.3.0 Python runtime), unedited |
| Catala sources read | catala-examples at the same commit, cloned with `git clone https://github.com/CatalaLang/catala-examples && git -C catala-examples checkout 2694b17ddd7c2246e207e8f077d586349ee5abea` |
| OS | Ubuntu 24.04, x86_64 (Claude Code cloud container), 4 cores |

`oracle.py` finds the encoding at `../../catala_family_benefits` relative to its own
folder, so it runs from a checkout of branch `paperc-code2-fr` with no install step:

```sh
python3 oracle.py --check-official   # every official test through the encoding and the oracle
python3 oracle.py --write-official   # official_examples.csv
python3 oracle.py --enumerate        # ground_truth.csv (refuses to run if an official test fails)
python3 oracle.py --check-groups N   # grouped enum labels, every N-th row
```

`--enumerate` uses a process pool (one worker per core) for tables above 2,000 rows; the
row order and content do not depend on the number of workers.

The oracle reads internal values of the scope `AllocationsFamiliales` (the components
of `montant_versé` and the ceilings `plafond_I_d521_3`, `plafond_II_d521_3`) through
`sys.setprofile`, which observes the generated function's local variables when it
returns; the generated code and the runtime are not modified.
