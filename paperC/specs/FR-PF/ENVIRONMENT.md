# Environment

| Item | Value |
|---|---|
| Encoding | CatalaLang/catala-examples commit `2694b17ddd7c2246e207e8f077d586349ee5abea`, compiled with Catala 1.3.0 |
| Executable build | `paperC/catala_family_benefits/` (branch `paperc-catala-family-benefits`, commit `2046eb8`), used unmodified: `generated/` and `runtime/catala/` |
| sha256 `generated/Allocations_familiales.py` | `53948f3a4cf35eb0e6108e180c08c84f9af9044d06cea56cde0d106ce5f6ad89` |
| sha256 `runtime/catala/catala_runtime.py` | `6d0188c5d3640a3d1cf529eaa01d74a6ba943b8413be6295e258496cd1b9c82e` |
| sha256 `run_official_tests.py` | `b41d3657ccf07703faa5ed87e10aa6bb31397bb17848158fc8a15c5165e8a42c` |
| Python | 3.13.16 and 3.12.3 (byte-identical `ground_truth.csv`); 3.12 or later is required by the Catala 1.3.0 runtime |
| Dependencies | standard library only, plus the bundled runtime |
| Host | Ubuntu 24.04.5 LTS, x86_64, 4 cores, Claude Code cloud container |
| Date of the run | 2026-10-20 |

The oracle finds the build through the relative path `../../catala_family_benefits`,
so the folder must stay at `paperC/specs/<ID>/` in this repository.
`frcatala.py` is a shared helper; the same file (same sha256) sits in every
FR-* spec folder.

## Commands

```sh
cd paperC/specs/<ID>
python3 oracle.py --check-official   # 15 official scopes directly + mapped examples; writes official_examples.csv
python3 oracle.py --self-check       # bands, ceilings and representatives checked against the encoding
python3 oracle.py --enumerate        # writes ground_truth.csv (multiprocessing, one worker per core)
python3 oracle.py --sha256           # writes SHA256SUMS
sha256sum -c SHA256SUMS
```
