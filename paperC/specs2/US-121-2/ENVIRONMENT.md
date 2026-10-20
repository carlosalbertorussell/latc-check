# Environment

| Component | Version |
|---|---|
| Python | 3.12.3 (`python3.12`, Ubuntu 24.04 package); the tables were generated with it. 3.13.16 produces byte-identical `ground_truth.csv`. Python 3.11 and older cannot import the Catala 1.3.0 runtime (PEP 695 syntax). |
| Python packages | none beyond the standard library |
| Catala | 1.3.0 (opam `catala.1.3.0`, OCaml 4.14.2, opam 2.1.5) |
| Catala Python runtime | `paperC/catala_code2/runtime/catala_runtime.py`, `dates.py` (Catala 1.3.0) |
| Generated encoding | `paperC/catala_code2/generated/` (Catala 1.3.0 output for catala-examples `2694b17ddd7c2246e207e8f077d586349ee5abea`) |

`oracle.py` adds `paperC/catala_code2` and `paperC/catala_code2/runtime` to `sys.path`
(paths relative to its own location) and imports `generated.Us_tax_code`.

To rebuild the generated Python from source (about 15 minutes):

```sh
apt-get install -y opam ninja-build libgmp-dev pkg-config
export OPAMYES=1
opam init --disable-sandboxing --bare -n
opam switch create catala 4.14.2 && eval $(opam env --switch=catala)
opam install catala.1.3.0
git clone https://github.com/CatalaLang/catala-examples && cd catala-examples
git checkout 2694b17ddd7c2246e207e8f077d586349ee5abea
catala python us_tax_code/us_tax_code.catala_en -o Us_tax_code.py
```

Full build notes and official `clerk test` results: `paperC/catala_code2/README.md`.
