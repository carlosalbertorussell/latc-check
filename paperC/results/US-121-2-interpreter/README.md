# Catala-interpreter cross-check of the corrected US-121-2

Every non-excluded row of `paperC/specs/US-121/US-121-2/ground_truth.csv` after the
correction of 2026-10-20 (900 rows: 204 label rows, 696 REJECTED) was written as a
Catala `#[test]` scope asserting its ground-truth output, plus one negative control
with a wrong expected label, and run with the Catala 1.3.0 **interpreter** (`clerk
test`, catala-examples at `2694b17ddd7c2246e207e8f077d586349ee5abea`, OCaml 4.14.2). No
Python is involved in the evaluation. Driver: `xcheck_us121_2.py` (reuses the writer and
reader of `paperC/catala_more/interpreter_crosscheck.py`, with the corrected date of the
spouse's death, |2020-12-31|).

Result (`result.txt`): 204 label rows pass their assertion, 696 REJECTED rows fail with
the run-time error of `section_121.catala_en:376` ("ambiguous comparison between
durations in different units"), 0 disagreements; the negative control is reported as a
disagreement. The 900 rows include the 396 `surviving_spouse` rows the correction moved
out of EXCLUDED (264 REJECTED, 132 label rows).

Files: `scopes/` (the generated test files), `xcheck_manifest.json` (scope → row and
expected output), `clerk_report.txt` (verbatim clerk output), `result.txt`.
