#!/usr/bin/env bash
# Run the official OpenFisca YAML tests for the three rules and write logs.
# Usage: run_official_tests.sh OPENFISCA_AOTEAROA_DIR VENV_DIR OUT_DIR
set -uo pipefail
SRC="$1"; VENV="$2"; OUT="$3"
mkdir -p "$OUT"
cd "$SRC"
for r in supported_living_payment accommodation_supplement sole_parent_support; do
  "$VENV/bin/openfisca" test -c openfisca_aotearoa "openfisca_aotearoa/tests/social_security/$r" -v > "$OUT/$r.log" 2>&1
  echo "exit status: $?" >> "$OUT/$r.log"
done
