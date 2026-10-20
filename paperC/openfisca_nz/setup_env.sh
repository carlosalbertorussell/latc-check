#!/usr/bin/env bash
# Recreate the OpenFisca Aotearoa environment used for paperC/specs/NZ-*.
# Usage: paperC/openfisca_nz/setup_env.sh [WORKDIR]   (default: ./openfisca_nz_work)
# Afterwards: export OPENFISCA_AOTEAROA_DIR=$WORKDIR/openfisca-aotearoa and
# run the oracles with $WORKDIR/venv311/bin/python.
set -euo pipefail
WORK="${1:-./openfisca_nz_work}"
COMMIT=9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$WORK"
cd "$WORK"
[ -d openfisca-aotearoa ] || git clone https://github.com/digitalaotearoa/openfisca-aotearoa
git -C openfisca-aotearoa checkout "$COMMIT"
python3.11 -m venv venv311
venv311/bin/pip install --upgrade pip
grep -v '^-e ' "$HERE/requirements.lock" > constraints.txt
venv311/bin/pip install -c constraints.txt -e ./openfisca-aotearoa
venv311/bin/pip freeze
