# Machine-checked core results of Paper A (Lean 4 + Mathlib)

This folder machine-checks the set-theoretic core of the LATC re-examination
("Where Declared Domains Are Lost"): Propositions 2, 3 and 4, and the generalized
cardinality check of Section 6.2. The Lean kernel checks every proof. Nothing is assumed
(`sorry` and `axiom` appear nowhere), and the concrete examples use kernel `decide`, not
`native_decide`. Propositions 1 (frequency profiles and Ryser interchanges) and
5 (complexity) are not formalized.

## Versions

| Component | Version (pinned in) |
|---|---|
| Lean | `leanprover/lean4:v4.35.0` (`lean-toolchain`) |
| Mathlib | tag `v4.35.0`, commit `56a005855ea17e0b0958f73ec801ae140b0a1679` (`lakefile.toml`, `lake-manifest.json`) |

## Build

Install [elan](https://github.com/leanprover/elan), then run from this folder:

```bash
lake exe cache get
```

```bash
lake build
```

`lake exe cache get` downloads the precompiled Mathlib (about 5 GB). Without it, Lake
compiles Mathlib from source, which takes hours. A clean build ends with no errors and no
`sorry` warnings. `LatcFormal/Axioms.lean` runs `#print axioms` on every main theorem;
each should list only `propext`, `Classical.choice` and `Quot.sound`.

Verification status (2026-10-21, Linux cloud machine, x86_64): on the final tree (commit
`caa1514`, where `Axioms.lean` imports `LatcFormal.Prop2`), Lean 4.35.0 (commit
`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`, Lake 5.0.0) and Mathlib `v4.35.0` (commit
`56a005855ea17e0b0958f73ec801ae140b0a1679`, from `lake exe cache get`, 9031 cached files),
the full `lake build` ended with `Build completed successfully (9054 jobs)` and exit
code 0. All seven files of this library (`Basic`, `Prop2`, `Prop3`, `Prop4`, `Examples`,
`Axioms` and the root `LatcFormal`) built with no errors and no `sorry` warnings; the
other 9047 jobs were Mathlib and its dependencies. The single warning was Lake's advisory
that `Basic.lean` imports Mathlib without the `module` keyword, which does not affect the
proofs. The axiom audit printed `[propext, Classical.choice, Quot.sound]` for each of
`Latc.prop2`, `Latc.prop2_missed`, `Latc.prop2_extra`, `Latc.prop2_missed_iff`,
`Latc.prop3`, `Latc.prop4_necessity`, `Latc.prop4_insufficiency`,
`Latc.prop4_insufficiency_needs_an_attribute`, `Latc.check_membership_sufficient`,
`Latc.check_wrong_output_cases`, `Latc.Examples.prop4_counterexample`,
`Latc.Examples.twins_same_profile` and `Latc.Examples.complete_pair`, and `sorryAx` appears
in none. A search of the folder for `sorry`, `axiom`, `admit` and `native_decide` finds
them only in comments, in this README and in the `#print axioms` commands of
`Axioms.lean`. An earlier Windows run built every file except the four `prop2*` audit
lines, which failed because the `Prop2` import was missing at the time.

## Model (Section 3)

| Paper | Lean (`LatcFormal/Basic.lean`) |
|---|---|
| attributes A₁, …, Aₙ; declared finite domains Dᵢ | index type `ι` with `[Fintype ι]`; `D : ι → Type*` with `[∀ i, Fintype (D i)]` |
| product space 𝒟 = D₁ × ⋯ × Dₙ | the finite type `∀ i, D i` |
| constraint set C, each a decidable predicate | one predicate `C` with `[DecidablePred C]`, the conjunction of the constraints |
| valid space 𝒱 | `validSpace C` |
| initial table T₀, condition tuples distinct (Section 3.2) | its condition set `T : Finset (∀ i, D i)`, with q(T₀) = `T.card` |
| missing set M(T₀) = 𝒱 ∖ cond(T₀) | `missing C T` |
| observed values Obsᵢ(S) | `obs S i` |
| Π = Obs₁(T₀) × ⋯ × Obsₙ(T₀) | `obsProduct T` |
| Reading B's output R = Π ∖ cond(T₀) | `readingB T` |
| frequency f_{i,v}(S) | `freq S i v` |
| generalized check CHECK (Sections 6.1–6.2) | `Check C out q T`, on an output sequence `out : List _` with multiplicities; differences in `ℤ` |
| correct output (Section 3.2): no repeats, set = M(T₀) | `Correct C out T` |

COMPLETE (`LatcFormal/Prop3.lean`) takes T₀ as a `Finset` of rows `(x, y)`, because its
second `require` is what makes the condition tuples distinct. The fixed visiting order is
a parameter `enum`, any list that contains every tuple of 𝒟 exactly once. The
lexicographic order is one such list.

## Theorem map

| Paper statement | Lean theorem | File |
|---|---|---|
| Prop. 2, M(T₀) ∖ R = 𝒱 ∖ Π | `Latc.prop2_missed` (holds for every T₀) | `Prop2.lean` |
| Prop. 2, R ∖ M(T₀) = Π ∖ 𝒱 (needs cond(T₀) ⊆ 𝒱) | `Latc.prop2_extra` | `Prop2.lean` |
| Prop. 2, missed states are those with an unobserved declared value | `Latc.prop2_missed_iff` | `Prop2.lean` |
| **Prop. 2**, R = M(T₀) ⟺ Π = 𝒱, given cond(T₀) ⊆ 𝒱 | `Latc.prop2` | `Prop2.lean` |
| Prop. 2, the hypothesis cond(T₀) ⊆ 𝒱 is needed | unnamed `example` after `prop2` | `Prop2.lean` |
| App. F, "If T₀ = ∅, then Π = R = ∅" | `Latc.obsProduct_empty` (n ≥ 1) and the `example` after it (fails for n = 0) | `Prop2.lean` |
| **Prop. 3** (correctness of COMPLETE): returns exactly M(T₀), each tuple once, in the fixed visiting order, and passes CHECK | `Latc.prop3` | `Prop3.lean` |
| **Prop. 4**, necessity | `Latc.prop4_necessity` | `Prop4.lean` |
| **Prop. 4**, insufficiency, general case (App. F) | `Latc.prop4_insufficiency` (with n ≥ 1; see the gap below) | `Prop4.lean` |
| Prop. 4, insufficiency, concrete counterexample T₀ = {(M, D), (F, I)} over Sex × Activity | `Latc.Examples.prop4_counterexample` | `Examples.lean` |
| §6.2, "membership checks close the gap" | `Latc.check_membership_sufficient` | `Prop4.lean` |
| §6.2, "an output that passes the counts is wrong only if it contains a tuple twice, a tuple of cond(T₀) or a tuple outside 𝒱" | `Latc.check_wrong_output_cases` | `Prop4.lean` |
| §5.1, the twins have the same profile and different missing sets | `Latc.Examples.twins_same_profile` | `Examples.lean` |
| COMPLETE and Reading B on the pair | `Latc.Examples.complete_pair`, `Latc.Examples.readingB_pair`, `Latc.Examples.missing_T0` | `Examples.lean` |

## Discrepancies found

None of these changes a result of the paper. Each is recorded here, and the paper now
states the hypotheses involved: n ≥ 1 in Section 3.1, and distinct condition tuples in 𝒱 for the
membership check of Section 6.2.

1. **Proposition 4, insufficiency, needs at least one attribute (n ≥ 1).** The general
   case in Appendix F says that for any non-zero zero-margin vector z, the output
   𝒱 ∖ {x : z_x = −1} passes the generalized check. With n = 0 attributes there are no
   margin equations, so z = 1 on 𝒟 = 𝒱 = {()} qualifies. Then T₀ = {()} and the output
   {()} has one row where |𝒱| − |T₀| = 0, so it fails the check
   (`Latc.prop4_insufficiency_needs_an_attribute`). The size equation is the step that
   breaks: it needs Σ_x z_x = 0, which follows from the margins of any one attribute.
   *Minimal fix:* assume n ≥ 1, which Section 3.1 of the paper now states explicitly ("Let A1, …, An, with n ≥ 1, be attributes") and earlier assumed implicitly.
   The Lean statement carries `[Nonempty ι]`.
2. **Appendix F, proof of Proposition 2, first sentence.** "If T₀ = ∅, then Π = R = ∅"
   holds only for n ≥ 1. For n = 0, Π is the one-element product {()}. The proposition
   itself is unaffected: both identities hold for every T₀ and every n, and the
   case split is not needed (`Latc.prop2_missed` and `Latc.prop2_extra` have no such case).
   *Minimal fix:* none needed. Read with n ≥ 1, as above.
3. **Proposition 2's hypothesis is used only by one identity.** M(T₀) ∖ R = 𝒱 ∖ Π holds
   for every T₀, because cond(T₀) ⊆ Π always holds. R ∖ M(T₀) = Π ∖ 𝒱 and the "only if"
   direction need cond(T₀) ⊆ 𝒱, and the `example` after `prop2` shows the "only if"
   direction fails without it. This agrees with the paper, which states the hypothesis.
   It is recorded only to make the dependency precise.
4. **Section 6.2, "membership checks close the gap"** relies on cond(T₀) ⊆ 𝒱 and
   distinct condition tuples, which the sentence does not repeat. These are the standing
   hypotheses of Proposition 4 and of COMPLETE's `require` lines, and the Lean statement
   assumes them. Without cond(T₀) ⊆ 𝒱, |𝒱 ∖ cond(T₀)| can exceed |𝒱| − |T₀|, and a
   strict subset of the missing set passes.

## Scope and modelling choices

- Reading B is modelled by its output set Π ∖ cond(T₀), which is how Appendix F's proof
  characterizes it. The claim that the odometer enumeration lists every tuple of Π exactly
  once (the mixed-radix bijection, Proposition 6) is not formalized.
- COMPLETE's `key()` is an arbitrary function injective on 𝒱. The canonical form of
  Appendix D.3 is not formalized.
- The vector z of Proposition 1 is a function 𝒟 → ℤ with values in {−1, 0, 1} that
  vanishes outside 𝒱 (`Latc.ZeroMarginVector`).
- Propositions 1, 5, 6 and 7, Theorem 1 and Corollaries 1–4 are not formalized.

## Proposition 5: the reduction

`LatcFormal/Prop5Reduction.lean` machine-checks the combinatorial correspondence on which
the proof of Proposition 5 rests. Variables form an arbitrary finite type `V` (the paper's
n attributes are `V = Fin n`), states are functions `V → Bool` (domains {0, 1}, with
`false` for 0 and `true` for 1), and the clause constraints feed the `validSpace` and
`missing` of `Basic.lean` through the predicate `conPred S`.

### Theorem map

| Paper statement or proof step | Lean theorem (namespace `Latc.Prop5`) |
|---|---|
| CNF over Boolean variables, literals xᵢ and ¬xᵢ, satisfaction | `Lit`, `CNF`, `evalCNF`, `Satisfiable`, `satSet`, `numSat` |
| a constraint is a clause, a disjunction of conditions Aᵢ = v | `Cond`, `ClauseCon`, `ConSet`, `holdsAll`, `conPred` |
| every CNF formula is a set of clause constraints with the same satisfying assignments | `encode_validSpace` (𝒱 = satSet φ), `encode_size` (one constraint per clause, same lengths) |
| every set of clause constraints over {0, 1} is a CNF formula with the same satisfying assignments | `decode_validSpace`, with `decode_encode` and `encode_decode` (mutually inverse) |
| with T₀ = ∅, M(T₀) = 𝒱 = the satisfying assignments | `missing_empty`, `prop5_missing_empty` |
| M(∅) non-empty iff satisfiable (the reduction from SAT) | `prop5_nonempty_iff_satisfiable`, `prop5_decode_nonempty_iff_satisfiable` |
| completeness (M(∅) = ∅) iff unsatisfiable | `prop5_complete_iff_unsatisfiable`, `prop5_decode_complete_iff_unsatisfiable` |
| \|𝒱\| is the number of satisfying assignments (the reduction from #SAT) | `prop5_card_validSpace` |
| \|M(T₀)\| = \|𝒱\| − \|T₀\| for distinct condition tuples inside 𝒱 | `card_missing_of_subset` (any constraint predicate), `prop5_card_missing` |
| monotone two-literal clauses (xᵢ ∨ xⱼ) are the clauses of two conditions Aᵢ = 1 | `encode_isPos2_iff`, `decode_isPos2`; with i ≠ j, `encode_isPos2Distinct_iff` |
| the certificate check of NP membership: x ∉ cond(T₀) and x satisfies every clause | `verify`, `verify_correct`, `nonempty_iff_exists_certificate` |
| #P membership: \|M(T₀)\| is the number of accepted certificates | `card_missing_eq_certificates` |
| one value only: non-emptiness is trivial | `single_value_nonempty_iff` |
| satisfiability reduces to constraint sets whose clauses each use one value | `purify`, `purify_single_valued`, `prop5_pure_clauses` |
| unsatisfiable CNF x₀ ∧ ¬x₀ gives a complete empty table | `Examples.unsat_complete` |
| satisfiable CNF (x₀ ∨ ¬x₁) ∧ x₁ gives M(∅) = {(1, 1)} | `Examples.sat_nonempty` |
| triangle (x₀ ∨ x₁)(x₁ ∨ x₂)(x₀ ∨ x₂): \|𝒱\| = 4; with T₀ = {(1, 1, 1)}, \|M(T₀)\| = 3, and the certificate check on three states | `Examples.triangle_count`, `Examples.triangle_table` |
| repeated condition Aᵢ = 1 ∨ Aᵢ = 1 is a unit clause | `holdsClause_dup`, `Examples.dup_clause` |
| two rows with one condition tuple | `Examples.repeated_condition_tuple` |

All examples are checked by the kernel with `decide`.

### What is machine-checked, and what rests on Cook (1971) and Valiant (1979)

Machine-checked: the translations between CNF formulas and clause constraints over
{0, 1} in both directions, with equal sets of satisfying assignments and linear size;
M(∅) = 𝒱 = the satisfying assignments, hence non-emptiness ⟺ satisfiability, completeness
⟺ unsatisfiability and |𝒱| = #SAT; |M(T₀)| = |𝒱| − |T₀| for distinct condition tuples
inside 𝒱; the exact match between monotone two-literal clauses and clauses of two
conditions Aᵢ = 1; and the correctness of the certificate check used for membership in
NP, coNP and #P.

Unchecked: complexity classes, polynomial time and reductions as such. The statements that
`verify`, `encode`, `decode` and `purify` run in polynomial time are read off their
definitions (one pass over the clauses, one membership test in T₀) and are outside the
formal model. The hardness rests on two cited theorems that are outside the library:
Cook (1971), that CNF satisfiability is NP-complete, which with
`prop5_nonempty_iff_satisfiable` gives the NP-hardness of non-emptiness and the
coNP-hardness of completeness; and Valiant (1979), that counting the satisfying
assignments of monotone two-literal CNF formulas is #P-complete under polynomial-time
Turing reductions, which with `prop5_card_validSpace` and `encode_isPos2_iff` gives the
#P-hardness of computing |𝒱|.

### Discrepancies found

None of these is an error in a result of Proposition 5. Each one makes a phrase of the
statement precise.

1. **"Clauses may mix A_i = 0 and A_i = 1" is stronger than needed within a clause, and
   both values must occur in the constraint set.** If every condition of the constraint
   set uses one value v, M(∅) is non-empty iff no clause is empty, because the constant
   state v satisfies every non-empty clause (`single_value_nonempty_iff`); the question is
   then decided by one scan. Mixing inside a clause is unnecessary: `purify` translates a
   CNF formula over n variables into |φ| + 2n clause constraints over 2n attributes in
   which each clause uses one value only (`purify_single_valued`), with M(∅) non-empty iff
   the formula is satisfiable (`prop5_pure_clauses`). With Cook's theorem, non-emptiness is
   NP-hard already for such constraint sets. The paper's wording is correct as it stands,
   because it states hardness for a class that contains them.
   *Minimal fix:* none needed. Optional precision: "(many-one reductions; both A_i = 0 and
   A_i = 1 must occur, though each clause may use one value)".
2. **"Clauses of two conditions A_i = 1" matches monotone two-literal CNF exactly when
   both sides allow i = j.** As lists, the clauses of two conditions Aᵢ = 1, Aⱼ = 1 are
   exactly the encodings of the clauses xᵢ ∨ xⱼ (`encode_isPos2_iff`, `decode_isPos2`).
   With i = j the clause is the unit clause xᵢ (`holdsClause_dup`, `Examples.dup_clause`).
   Read as two distinct conditions, the class is monotone 2-CNF with i ≠ j
   (`encode_isPos2Distinct_iff`), one clause per edge of a graph, whose count is the
   number of vertex covers. Counting vertex covers of a graph is the standard #P-complete
   form of Valiant's monotone 2-SAT, so the hardness claim holds under either reading.
   *Minimal fix:* none needed. Optional precision: "clauses of two distinct conditions
   A_i = 1 and A_j = 1".
3. **"for distinct rows inside 𝒱" needs distinct condition tuples.** Two rows that share a
   condition tuple and differ in the outcome are distinct rows. In the triangle example,
   two such rows over the state (0, 1, 1) give |M(T₀)| = 3, while |𝒱| minus the number of
   rows is 2 (`Examples.repeated_condition_tuple`). Section 3.2 assumes distinct condition
   tuples, so the statement holds in the paper's setting, and `prop5_card_missing`
   carries that hypothesis (T₀ is a `Finset` of condition tuples).
   *Minimal fix:* "for distinct condition tuples inside 𝒱" in place of "for distinct rows
   inside 𝒱".

### Verification status

2026-10-25, Linux cloud machine, x86_64, Lean 4.35.0 (commit
`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`, Lake 5.0.0), Mathlib `v4.35.0` (commit
`56a005855ea17e0b0958f73ec801ae140b0a1679`, from `lake exe cache get`, 9031 cached files).
After removing `.lake/build`, `lake build` on the final tree ended with
`Build completed successfully (9055 jobs)` and exit code 0. All eight files of the library
(`Basic`, `Prop2`, `Prop3`, `Prop4`, `Prop5Reduction`, `Examples`, `Axioms` and the root
`LatcFormal`) built with no errors and no `sorry` warnings; the single warning was the
advisory about the `module` keyword in `Basic.lean`. The axiom audit printed
`[propext, Classical.choice, Quot.sound]` for every `Latc.Prop5` theorem in `Axioms.lean`,
except `decode_encode`, `encode_decode` and `encode_size`, which printed the smaller
`[propext, Quot.sound]`; `sorryAx` appears in none. A search of the folder for `sorry`,
`axiom`, `admit` and `native_decide` finds them only in comments, in this README and in the
`#print axioms` commands of `Axioms.lean`.
