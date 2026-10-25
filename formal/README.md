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
