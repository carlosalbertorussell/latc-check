# CTRL-NUR environment

* Python 3.12.x (built with 3.12; `oracle.py` uses the standard library only: `csv`, `json`, `os`, `sys`, `itertools`).
* No packages to install.
* Input data: `data/raw/uci_nursery/` of this repository, unchanged since commit
  `c6d2802abe667a9a49cbcb3848f12407fdf00ef5`:

| file | sha256 |
|---|---|
| nursery.data | 8e0389c3dd37590248a921c2726d869ee96b817761a35eb8416afa24f31f931d |
| nursery.names | f18db269d8300cb47f9caf01a5e5513e23c8fa6ba647cfecb0e3af04790f5467 |
| nursery.c45-names | 5b66540d9116c3d34b269bdd2205f6e13d18af65a31586c614c751d19c1f730e |

Rebuild and check (from this folder):

```
python3.12 oracle.py --enumerate
python3.12 oracle.py --check-official
```
