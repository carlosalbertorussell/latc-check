# Environment (second coder)

* Python 3.11.17 (CPython) in a virtualenv. openfisca-aotearoa 22.0.0 declares
  `requires-python >=3.9` and lists Python 3.9 to 3.11 in its classifiers.
* openfisca-core 41.5.7, numpy 1.24.4, pandas 2.3.3, PyYAML (pulled in by openfisca-core).
  The full `pip freeze` is in `paperC/openfisca_code2/pip_freeze.txt`.
* Encoding: OpenFisca Aotearoa, https://github.com/digitalaotearoa/openfisca-aotearoa,
  commit `9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb` (version 22.0.0, AGPL-3.0).
  Its source is not copied into this repository.

Install:

```sh
python3.11 -m venv venv311
. venv311/bin/activate
pip install --upgrade pip
git clone https://github.com/digitalaotearoa/openfisca-aotearoa
git -C openfisca-aotearoa checkout 9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb
pip install -e openfisca-aotearoa      # resolves openfisca-core[web-api] >=41.4.5,<42
```

Run (from this folder, with the virtualenv active):

```sh
python oracle.py --check-official --write-official   # rewrites official_examples.csv
python oracle.py --enumerate                          # rewrites ground_truth.csv
```

`--check-official` locates the official YAML tests inside the installed
`openfisca_aotearoa` package (`openfisca_aotearoa/tests/...`), so the package must be
installed from a full clone (the editable install above does that).
