# Paper C pre-registration: LATC as the completion step of a Rules as Code model

Author: Carlos A. Russell (sole author).
Registered: 2026-10-20, before any code that computes a Paper C result was written.
Status: this text is frozen at the commit that adds it. Later changes go only in the
dated "Deviations" section at the end; the original text is never rewritten.

## 1. Question

Raggio and Russell (2021) propose LATC, which detects and fills the missing rows of a
decision table from example cases by counting attribute cardinalities, as the
completion component of a Rules as Code model. Paper C tests that claim against real
encoded legislation used as ground truth (Catala encodings of French family benefits,
French housing benefits and US tax code section 121; OpenFisca Aotearoa social-security
eligibility rules), with UCI Nursery as a control.

The LATC implementation tested is the reference implementation in `latc_check/`
(module `latc_check.latc`, with `latc_check.model` and `latc_check.reference`) as it
stands on `main` at commit `c6d2802`. Paper C does not modify it.

## 2. Terms

A **sample** is one folder `paperC/specs/<ID>/` in the format of
`paperC/specs/FORMAT.md`. A sub-table (for example `FR-AF-1`) is its own sample.
Samples whose ID starts with `CTRL-` are controls; all others are **legal samples**.

For a sample with attributes A1..Am in spec order, declared label tuples D1..Dm:

* **D** (declared space) = D1 × ... × Dm, enumerated in odometer order (last attribute
  varies fastest), which is the row order of `ground_truth.csv`.
* **GT(c)** = the `output` cell of `ground_truth.csv` for condition tuple c.
* **E** = { c in D : GT(c) = `EXCLUDED` }, **R** = { c in D : GT(c) = `REJECTED` }.
* **V** (valid space) = D \ (E ∪ R). The list **V_list** is V in `ground_truth.csv`
  row order.
* **S** (spec-valid space) = { c in D : no exclusion predicate of spec.json holds at c }.
  A predicate is evaluated with `eval(predicate, {"__builtins__": {}}, row)` where `row`
  maps each attribute name to its label (a Python `str`).
* An **example set** is a list of rows (c, y), with c in D and y a label. Its condition
  list is **X_list** and its set of distinct conditions is **X**.

Every condition tuple is a tuple of label strings. All comparisons are exact string
comparisons.

## 3. Hypotheses

* **H1** With the encoding's own official test cases as examples, most rules miss at
  least one declared value, so LATC under-reports the gaps.
* **H2** Without exclusions, a substantial share of generated rows are legally
  impossible.
* **H3** With declared domains and exclusions, completion equals the ground truth's
  valid space exactly.
* **H4** On the Nursery control the full data set shows no gap, and random samples show
  a gap that shrinks with sample size.

Decision rules are in section 8.

## 4. Conditions

For every example set the harness builds one `latc_check.model.DecisionTable`:

```
attributes = tuple(Attribute(name_j, tuple(D_j)) for j in 1..m)   # spec order
rows       = [Row(c, y) for (c, y) in example set]                # example order
outcomes   = tuple(output.values)
constraint = None            (C1, C2)
constraint = lambda c: c in S (C3)
```

The generated list **G_list** and the generated set **G** are:

* **C1 LATC as published.** `G_list = latc_check.latc.latc_odometer(T)`.
  This uses `observed_domains(T)` (labels seen in the examples, first-appearance
  order) and enumerates their product by `odometer_assembly`, returning the assembled
  rows not present among the example conditions. LATC's own missing count is
  `latc_check.latc.missing_count(T)` (= `product_of_cards(T) - len(T.rows)`).
* **C2 Declared domains.** `G_list = latc_check.reference.exact_complement(T)` with
  `constraint = None`. With no constraint, `valid_space()` is `full_space()`, the
  odometer enumeration of the declared domains, so C2 is the C1 procedure with the
  declared domains in place of the observed ones. Reported missing count for C2:
  `prod(len(D_j)) - len(T.rows)`.
* **C3 Declared domains and exclusions.** `G_list = latc_check.reference.exact_complement(T)`
  with `constraint` = membership in S. Reported missing count for C3:
  `T.valid_space_size() - len(T.rows)`.

The same example set is used by C1, C2 and C3 within one (source, size, seed) cell.

## 5. Example sources

* **OFFICIAL** The rows of `official_examples.csv` in file order (`case_id` dropped).
  One run per condition; seed and size are recorded as `-` and the row count. If the
  file has no data rows, OFFICIAL is skipped for that sample and the summary says so.
* **FULL** (control and context source) V_list with outputs GT(c), in
  `ground_truth.csv` order. One run per condition.
* **UNIFORM**(n, seed): `rng = random.Random(seed)`; then exactly one call
  `rng.choices(V_list, k=n)`. Each drawn condition c becomes the row (c, GT(c)).
* **ZIPF**(n, seed): `rng = random.Random(seed)`; then exactly two calls in this order:
  1. `perm = list(V_list); rng.shuffle(perm)`; rank k (1-based) is `perm[k-1]`;
  2. `rng.choices(perm, weights=[1.0 / (k ** 1.0) for k in range(1, len(perm) + 1)], k=n)`
     (s = 1.0, P(rank k) proportional to 1/k^s).
  Each drawn condition c becomes the row (c, GT(c)).

Sizes n ∈ {10, 20, 50, 100, 200, 500, 1000}; seeds 0..29. A fresh `random.Random(seed)`
is created for every (source, n, seed) cell, so cells are independent of execution
order (for a given seed, UNIFORM draws of size n are the prefix of the draws of a larger
size). Draws are always with replacement and always of exactly n rows; when n > |V|
the summary flags the size as exceeding the valid space and nothing else changes.
RNG is CPython 3.12 `random` (Mersenne Twister); no other source of randomness is used.

Run order (fixed, also the row order of `runs.csv`): source in (OFFICIAL, FULL,
UNIFORM, ZIPF); within UNIFORM and ZIPF, n ascending, then seed ascending; condition
C1, C2, C3 innermost.

## 6. Metrics (per run)

With X, G, D, V, E, R as above and m attributes:

| column | definition |
|---|---|
| `n_examples` | len(X_list) |
| `n_distinct_examples` | \|X\| |
| `examples_invalid` | number of entries of X_list in E ∪ R |
| `examples_disagree_gt` | number of example rows (c, y) with y ≠ GT(c) |
| `contradictory_pairs` | number of unordered index pairs i < j of the example list with c_i = c_j and y_i ≠ y_j |
| `value_coverage` | for each attribute j: \|{c[j] : c in X}\| / \|D_j\|, written `name=seen/declared` joined by `;` |
| `min_value_coverage` | min over j of the ratios above |
| `unseen_values` | Σ_j \|D_j \ {c[j] : c in X}\| |
| `reported_missing` | the condition's missing count from section 4 |
| `true_gap` | \|V \ X\| |
| `workload` | len(G_list) (labelling workload) |
| `covered_valid` | \|V ∩ (X ∪ G)\| |
| `valid_coverage` | covered_valid / \|V\| (1.0 if \|V\| = 0) |
| `missed_valid` | \|V \ (X ∪ G)\| |
| `spurious_excluded` | \|G ∩ E\| |
| `spurious_rejected` | \|G ∩ R\| |
| `spurious` | \|G ∩ (E ∪ R)\| |
| `spurious_share` | spurious / \|G\| (0.0 if G is empty) |
| `complete` | 1 if valid_coverage = 1 and spurious = 0, else 0 |

Floats are written with Python `repr`. Integer columns allow every ratio to be recomputed.

## 7. Controls and pass criteria (written to `controls.csv`)

* **CTRL-HASH** every file of the sample folder (recursively, excluding `SHA256SUMS`,
  `__pycache__` directories and `*.pyc`) is listed in `SHA256SUMS` with a matching
  sha256 and no listed file is absent. Failure aborts the run.
* **CTRL-GT** `ground_truth.csv` has the header of FORMAT.md, exactly |D| rows in
  odometer order, and every output in output.values ∪ {EXCLUDED, REJECTED}; every
  OFFICIAL row uses declared labels. Failure aborts the run.
* **CTRL-EXCL** (spec consistency) for every c in D: GT(c) = EXCLUDED if and only if
  c ∉ S. Recorded as pass/fail with the count of disagreeing rows; the run continues.
* **(a) CTRL-FULL** for sample `CTRL-NUR`, source FULL, condition C1:
  `missing_count(T) = 0` and workload = 0. For other samples FULL is recorded without
  a pass criterion.
* **(b) CTRL-PLANT** (planted defect) for every example set used in section 5
  (OFFICIAL if non-empty, FULL, and every UNIFORM and ZIPF cell): let v be the declared
  label of the first attribute A1 with the smallest count among the example rows
  (count 0 allowed; ties broken by declared order). Remove every example row whose
  A1 label is v. Run C2 on the remaining rows. Pass if every c in D with c[1] = v is in
  G (expected count = Π_{j≥2} \|D_j\|). The count C1 generates for v is recorded too
  (expected 0, since v is then unobserved). The control passes if every example set passes.
* **(c) CTRL-H3** every C3 run has valid_coverage = 1 and spurious = 0. Per run this
  follows by construction when CTRL-EXCL passes and R is empty; when R is non-empty,
  C3 can generate rejected rows, and that is recorded as a failure of H3 for the
  sample, with `spurious_rejected` stating how many.
* **(d) CTRL-DET** (determinism) the harness is run twice from two clean checkouts of
  the same commit, writing to separate directories; `runs.csv`, `controls.csv`,
  `summary.md` and `manifest.json` must be byte-identical. No output contains a
  timestamp, absolute path or host name.

## 8. Statistics and decision rules

For each (sample, condition, source, size) with seeds, and for each metric among
valid_coverage, missed_valid, spurious, spurious_share, workload, contradictory_pairs,
min_value_coverage, unseen_values, reported_missing, true_gap, report over the 30
seeds: mean (arithmetic), median, 2.5th and 97.5th percentiles. Percentile p of sorted
values x_0..x_{N-1}: h = (N-1)·p, lo = floor(h); value = x_lo + (h - lo)·(x_{lo+1} - x_lo)
(x_{lo+1} taken as x_lo when lo = N-1); this is Hyndman and Fan type 7. Also report the
share of seeds with complete = 1 and its Wilson 95% interval with
z = `statistics.NormalDist().inv_cdf(0.975)`:
centre = (p̂ + z²/(2N)) / (1 + z²/N),
half = z·sqrt(p̂(1-p̂)/N + z²/(4N²)) / (1 + z²/N), interval = [centre - half, centre + half].
OFFICIAL and FULL have one run per condition; their values are reported directly.

Decision rules (evaluated over all legal samples once every legal sample has run):

* **H1** supported if, among legal samples with at least one OFFICIAL row, more than
  half have `unseen_values > 0` under OFFICIAL, and more than half have C1
  `missed_valid > 0` under OFFICIAL. Each sample's two indicators and
  `reported_missing` versus `true_gap` are reported.
* **H2** supported if more than half of legal samples have C2 `spurious_share ≥ 0.10`
  under FULL. Secondary, reported without a decision: C2 and C1 spurious_share under
  OFFICIAL, and median over seeds under UNIFORM n = 1000.
* **H3** supported for a sample if CTRL-H3 passes for it; supported overall if it holds
  for every legal sample. Samples with R non-empty are listed separately.
* **H4** (CTRL-NUR only) supported if (i) CTRL-FULL passes; (ii) every UNIFORM and
  ZIPF C1 run has `reported_missing > 0`; (iii) for each of UNIFORM and ZIPF, the mean
  C1 `missed_valid` is non-increasing across n = 10, 20, ..., 1000; (iv) the mean C1
  `missed_valid` at n = 10 under UNIFORM is greater than 0.

## 9. Outputs and provenance

`python -m paperC.harness.run --spec paperC/specs/<ID> --out paperC/results/<ID>`
writes `runs.csv`, `controls.csv`, `summary.md` and `manifest.json`. The manifest holds
the harness git commit, whether the harness, protocol, spec and `latc_check/` are
unmodified relative to that commit, the PROTOCOL.md commit hash, the Python version,
and the sha256 of every input and output file (paths relative to the repository
root). The harness uses Python 3.12 and its standard library plus `latc_check`.

## 10. Independent recomputation

Every number can be recomputed from `ground_truth.csv`, `official_examples.csv`,
`spec.json` and sections 4 to 8: the example sets follow from the stated `random` calls,
the generated sets from the named `latc_check` functions (or their definitions in
section 4), and the metrics from the formulas in section 6.

## Deviations

(none yet)

### 2026-10-20: clarifications made while writing the harness

Recorded after the harness was written and tried once on CTRL-NUR to test it. None
of these changes a number defined above.

1. Exclusion predicates are parsed with `ast` before evaluation and rejected (run
   aborted) unless every node is a boolean operator, `not`, a comparison, a tuple,
   list or set, an attribute name of the sample, or a string constant. Predicates
   that pass are evaluated exactly as section 2 states.
2. Wilson bounds are clamped to [0, 1], which only removes rounding residue at
   k = 0 and k = N.
3. `SHA256SUMS` is read in `sha256sum` output form (64 hex digits, a space, a space or
   `*`, the path relative to the sample folder).
4. The manifest field `tracked_inputs_unmodified` is true when
   `git status --porcelain` reports nothing for `paperC/harness`, `paperC/PROTOCOL.md`,
   the sample folder and `latc_check`.
5. `runs.csv` carries one extra column, `size_exceeds_valid` (1 when n > |V|), which
   implements the flag of section 5.
6. CTRL-DET is run by `python -m paperC.harness.determinism`, which clones the current
   commit twice and compares the four output files byte for byte.
