# Readings chosen where PROTOCOL.md leaves room

`recompute.py` implements PROTOCOL.md (copy in this folder) without reading
`paperC/harness/` and without importing `latc_check`. Where the text admits more than
one reading, this is the one implemented.

1. **runs.csv columns.** Section 6 defines the metric columns and Deviation 5 adds
   `size_exceeds_valid`; the identifying columns are not named. Layout used:
   `sample, source, n, seed, condition`, then the 19 metrics in the order of the
   section 6 table, then `size_exceeds_valid`. Step 4 compares by column name, so a
   different order or naming in the harness is reported as a layout difference only.
2. **OFFICIAL and FULL identifiers.** Section 5 says OFFICIAL records seed `-` and the
   row count as size. FULL is given the same treatment: seed `-`, n = |V|.
3. **`len(T.rows)` counts duplicate example rows.** The protocol builds one `Row` per
   example, in example order, with no de-duplication step. So C1 `reported_missing` =
   Π|observed_j| − len(example list), and likewise for C2 and C3; it is negative
   whenever the examples repeat more than the product allows.
4. **Generated sets.** C1: product of the observed labels (first-appearance order)
   minus the distinct example conditions. C2: D minus the example conditions. C3:
   S minus the example conditions (the "valid space" of section 4 is S, the
   spec-valid space defined by the predicates). An example condition is removed from
   G whatever output it carries.
5. **Multiplicities.** `examples_invalid` counts entries of X_list (with repetition);
   `value_coverage`, `unseen_values` and `min_value_coverage` use the distinct set X;
   `examples_disagree_gt` counts example rows.
6. **CTRL-PLANT.** Label counts of A1 are taken over example rows with repetition;
   ties go to the earlier declared label. The C1 count for v is the number of rows
   with A1 = v that C1 generates from the remaining rows. When the remaining list is
   empty, C1 generates nothing.
7. **`complete`.** `valid_coverage == 1` is tested as float equality with 1, which
   holds exactly when covered_valid = |V|.
8. **Predicates.** Parsed with `ast` and accepted only if every node is a boolean
   operator, `not`, a comparison (any operator), a tuple/list/set, an attribute name or
   a string constant (Deviation 1); then `eval(predicate, {"__builtins__": {}}, row)`.
9. **Statistics.** Mean = `sum(x)/N`; percentiles Hyndman–Fan type 7 as written;
   Wilson interval clamped to [0, 1] (Deviation 2). Numbers in summary.md are rounded
   for display (6 significant digits); runs.csv holds the exact values (`repr`).
10. **Sample folder.** The spec folders of this family are one level deeper
    (`paperC/specs/FR-APL/<ID>/`, README-FR2 Deviation 1); the recompute reads the folder
    given on the command line.
11. **CTRL-DET.** Run here as two runs of `recompute.py` into separate directories:
    byte-identical `runs.csv`, `controls.csv`, `summary.md` for FR-APL-1, FR-APL-3 and
    US-121-2. No manifest is written by the verifier.
