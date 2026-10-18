#!/bin/sh
# Copies the DMN 1.4 test inputs to converted_dmn13/, changing ONLY the DMN namespace URI
# (https://www.omg.org/spec/DMN/20211108/MODEL/ -> https://www.omg.org/spec/DMN/20191111/MODEL/),
# because dmn-check 1.1.6 (camunda-dmn-model 7.14.0) only recognises DMN 1.1-1.3 namespaces.
IN=C:/Users/crussell/Downloads/repos/LATC/results/tools/inputs
OUT=C:/Users/crussell/Downloads/repos/LATC/results/tools/dmncheck-dmnlint/converted_dmn13
mkdir -p "$OUT"
for f in "$IN"/*.dmn; do
  sed 's#https://www.omg.org/spec/DMN/20211108/MODEL/#https://www.omg.org/spec/DMN/20191111/MODEL/#' "$f" > "$OUT/$(basename "$f")"
done
