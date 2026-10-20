# CTRL-NUR conversion notes

1. **Attributes and declared values** are the 8 input attributes of `nursery.names`
   section 7, in the order listed there, with each attribute's values in the listed order.
2. **Spelling of `nonprob`.** `nursery.names` section 7 spells the first value of
   `social` as `non-prob`; `nursery.data` and `nursery.c45-names` spell it `nonprob`.
   The label is `nonprob` so that it matches the data. The value order is unchanged.
3. **Output.** The 5 classes of `nursery.names` section 9, in the order of
   `nursery.c45-names` (`not_recom, recommend, very_recom, priority, spec_prior`), which
   is also the order of the table in section 9. Output name `NURSERY` is the target
   concept of section 4.
4. **Ground truth.** The class of each of the 12,960 rows of `nursery.data`.
   `nursery.names` section 5 states that the instances completely cover the attribute
   space; `oracle.py` checks that no condition repeats, and `--enumerate` would raise a
   `KeyError` on any combination absent from the data. The enumerated
   `ground_truth.csv` lists the rows in the same order as `nursery.data`.
5. **Exclusions:** none. **REJECTED rows:** none (every combination has a class).
6. **Official examples:** Nursery has no official test cases. `official_examples.csv`
   contains only its header, and the harness skips the OFFICIAL source for this sample.
7. **No `representative` values** are needed: every label is itself the value in the data.
