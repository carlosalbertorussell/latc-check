# Public datasets

The files under `data/raw/` are third-party data, kept unchanged as downloaded from the UCI
Machine Learning Repository. They are not covered by the copyright notice in `LICENSE-DATA`;
their own licence and attribution apply. `latc_check/datasets.py` and `latc_check/datasets_more.py`
read them as plain data. Each of the three later directories has a `SOURCE.txt` with the
download URL, date and DOI.
The downloaded `.zip` archives are not kept (`.gitignore` excludes `data/raw/**/*.zip`).

| directory | dataset | source | licence | files |
|---|---|---|---|---|
| `raw/uci_car/` | Car Evaluation (1,728 rows, 6 attributes) | https://archive.ics.uci.edu/dataset/19/car+evaluation | CC BY 4.0 | `car.data`, `car.names`, `car.c45-names` |
| `raw/uci_nursery/` | Nursery (12,960 rows, 8 attributes) | https://archive.ics.uci.edu/dataset/76/nursery | CC BY 4.0 | `nursery.data`, `nursery.names`, `nursery.c45-names` |
| `raw/lenses/` | Lenses (24 rows, 4 attributes) | https://archive.ics.uci.edu/dataset/58/lenses | CC BY 4.0 | `lenses.data`, `lenses.names` |
| `raw/balance-scale/` | Balance Scale (625 rows, 4 attributes) | https://archive.ics.uci.edu/dataset/12/balance+scale | CC BY 4.0 | `balance-scale.data`, `balance-scale.names` |
| `raw/monks/` | MONK's Problems (432 states, 6 attributes, 3 targets) | https://archive.ics.uci.edu/dataset/70/monk+s+problems | CC BY 4.0 | `monks-{1,2,3}.{train,test}`, `monks.names` |

Both were donated by Marko Bohanec and Blaž Zupan (June 1997). Car Evaluation was created by
Marko Bohanec; Nursery by Vladislav Rajkovič et al. (13 experts). Each dataset page on the UCI
site gives the repository's own citation and DOI.

**Citations** (as given in the `.names` files):

* Car Evaluation: M. Bohanec and V. Rajkovič, "Knowledge acquisition and explanation for
  multi-attribute decision making", 8th International Workshop on Expert Systems and their
  Applications, Avignon, France, pp. 59–78, 1988.
* Nursery: M. Olave, V. Rajkovič, M. Bohanec, "An application for admission in public school
  systems", in I. Th. M. Snellen, W. B. H. J. van de Donk and J.-P. Baquiast (eds.), *Expert
  Systems in Public Administration*, pp. 145–160, Elsevier Science Publishers (North Holland),
  1989.
* Both: M. Bohanec and V. Rajkovič, "Expert system for decision making", *Sistemica* 1(1),
  pp. 145–157, 1990 (the DEX shell in which both models were built).

**Notes on the files.**

* The prose `.names` files spell four values differently from the data: `v-high` (data
  `vhigh`), `5-more` (`5more`), class `v-good` (`vgood`) in Car, and `non-prob` (`nonprob`)
  in Nursery. The `.c45-names` files match the data, so the loaders take the domains from
  them and check that the value order is the same as in `.names`.
* `nursery.data` ends with a blank line, which the loader skips.
* Both tables were verified to be the full Cartesian product of their declared domains, with
  no duplicate condition tuples and one class per tuple (`datasets.verify`).

**Lenses, Balance Scale and MONK's** (`datasets_more.py`).

* Repository citations and DOIs: Cendrowska, J. (1987), Lenses, 10.24432/C5K88Z; Siegler, R.
  (1976), Balance Scale, 10.24432/C5488X; Wnek, J. (1993), MONK's Problems, 10.24432/C5R30R.
* Original sources: J. Cendrowska, "PRISM: An algorithm for inducing modular rules",
  *International Journal of Man-Machine Studies* 27(4), pp. 349–370, 1987; R. S. Siegler,
  "Three aspects of cognitive development", *Cognitive Psychology* 8(4), pp. 481–520, 1976;
  S. B. Thrun et al., "The MONK's problems: A performance comparison of different learning
  algorithms", Technical Report CMU-CS-91-197, Carnegie Mellon University, 1991.
* None of the three has a `.c45-names` file, so domains are read from section 7 of the prose
  `.names` files; values are kept exactly as the `.data` files spell them.
* The `monks-N.test` files hold all 432 input states with exact labels, so the MONK's tables
  are read from them. `monks-3.train` has 6 of 122 labels that differ from `.test` (the
  intended noise); the `.train` files are only checked to be subsets of `.test`.
* All five tables were verified to be the full Cartesian product of their declared domains,
  with no duplicate condition tuples and one class per tuple; Balance Scale's classes also
  agree with its weight × distance rule.

## DMN Technology Compatibility Kit

The DMN TCK (https://github.com/dmn-tck/tck, Apache License 2.0) is **not** copied into this
repository. Clone it next to this repository (`../dmn-tck`) or pass `--tck PATH` to
`run_datasets.py`. The results in `results/datasets/` were produced from commit `9402e87` of
the TCK.

## Not used

LendingClub loan data was considered but not used: it is distributed through Kaggle and
needs a login.
