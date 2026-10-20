#!/usr/bin/env bash
# Rebuild every NZ table, official-example file, log, doc and checksum from scratch.
# Usage: OPENFISCA_AOTEAROA_DIR=/path/to/clone PY=/path/to/venv311/bin/python paperC/openfisca_nz/rebuild_all.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${OPENFISCA_AOTEAROA_DIR:?set to the openfisca-aotearoa clone at commit 9d77ea7ce3c4}"
PY="${PY:-python3.11}"
export OPENFISCA_AOTEAROA_DIR
python3 "$HERE/build_oracles.py"
for d in "$HERE/../specs/NZ-SLP" "$HERE/../specs/NZ-AS" "$HERE/../specs/NZ-SPS" "$HERE/supplementary/NZ-AS-1964"; do
  id="$(basename "$d")"
  (cd "$d" && "$PY" oracle.py --check-official --write --log "$HERE/logs/check_official_$id.txt" 2>/dev/null \
            && "$PY" oracle.py --enumerate)
done
python3 "$HERE/crosscheck.py"
python3 "$HERE/summarise.py" > "$HERE/logs/summary.txt"
python3 "$HERE/make_docs.py"
python3 "$HERE/build_oracles.py" --check
