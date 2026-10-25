# Machine-checked core results of Paper A (Lean 4 + Mathlib)

This folder machine-checks the set-theoretic core of the LATC re-examination
("Where Declared Domains Are Lost"): Theorem 1, Corollaries 1, 3 and 4, Propositions 1,
2, 3, 4, 6 and 7, and the generalized cardinality check of Section 6.2. The Lean kernel
checks every proof. Nothing is assumed (`sorry` and `axiom` appear nowhere), and the
concrete examples use kernel `decide` and never `native_decide`. Proposition 5 (complexity)
and Corollary 2 are not formalized.

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

Verification status of the extension (2026-10-25, Linux cloud machine, x86_64, Linux
6.18, 4 cores): on commit `9f5bf0d` of branch `formal-lean-more`, which adds `Thm1`,
`Prop1`, `Prop6` and `Prop7`, with the same Lean 4.35.0 (commit
`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`, Lake 5.0.0) and Mathlib `v4.35.0` (commit
`56a005855ea17e0b0958f73ec801ae140b0a1679`, from `lake exe cache get`, 9031 cached
files), a full `lake build` from an empty `.lake/build` ended with
`Build completed successfully (9058 jobs)` and exit code 0. All eleven files of this
library built with no errors and no `sorry` warnings. The single warning is the same
`module` advisory for `Basic.lean`. The axiom audit printed
`[propext, Classical.choice, Quot.sound]` for each of the 13 theorems above and for each
of the 27 new ones: `Latc.thm1`, `Latc.thm1_noConstraint`, `Latc.thm1_remark`,
`Latc.validSpace_isProduct_of_noConstraint`, `Latc.cor1`,
`Latc.obsProduct_eq_validSpace_of_all_observed`, `Latc.cor3`, `Latc.cor4`, `Latc.prop1`,
`Latc.prop1_condSets`, `Latc.prop1_exists`, `Latc.prop1_exists_full`,
`Latc.prop1_exists_full_needs_nonempty`, `Latc.prop1_procedure`,
`Latc.evenParity_space`, `Latc.evenParity_profile_determines`,
`Latc.evenParity_no_zeroMarginVector`, `Latc.rankFin_bijective`, `Latc.prop6`,
`Latc.prop6_existsUnique`, `Latc.prop6_empty_domain`, `Latc.prop7_injective`,
`Latc.prop7_not_injective`, `Latc.prop7_not_injective_needs_nonempty`,
`Latc.prop7_shared_injective`, `Latc.prop7_shared_not_injective` and
`Latc.prop7_may_or_may_not`. `sorryAx` appears in none. The search for `sorry`, `axiom`,
`admit` and `native_decide` in the `.lean` files finds no match.

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
| T₀ complete: M(T₀) = ∅ | `Complete C T` (`Thm1.lean`) |
| P = Card₁ × ⋯ × Cardₙ, Cardᵢ = \|Obsᵢ(T₀)\| | `obsCardProd T` (`Thm1.lean`) |
| 𝒱 is the product of its projections | `obsProduct (validSpace C) = validSpace C` |
| frequency profile of T₀ | the function `freq T : (i : ι) → D i → ℕ` |
| order of Dᵢ, idxᵢ(v) | `e i : D i ≃ Fin (Fintype.card (D i))`, idxᵢ(v) = `e i v`; attributes `Fin n` (`Prop6.lean`) |
| prime assignment p(Aᵢ, v), key K(x) | `p : (Σ i, D i) → ℕ`, `primeKey p x = ∏ i, p ⟨i, x i⟩` (`Prop7.lean`) |

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
| **Thm. 1**, cond(T₀) ⊆ 𝒱, 𝒱 the product of its projections, T₀ complete ⟹ q(T₀) = P | `Latc.thm1` | `Thm1.lean` |
| Thm. 1, the case C = ∅ (𝒱 = 𝒟 is a product, for any domains) | `Latc.thm1_noConstraint`, `Latc.validSpace_isProduct_of_noConstraint` | `Thm1.lean` |
| Thm. 1, remark: a constraint excludes a tuple of Π ⟹ q(T₀) = \|𝒱\| < P | `Latc.thm1_remark` | `Thm1.lean` |
| **Cor. 1**, q(T₀) < P ⟹ T₀ incomplete | `Latc.cor1` | `Thm1.lean` |
| Cor. 3, the precondition of [3] (every declared value observed) with C = ∅ gives Π = 𝒱 | `Latc.obsProduct_eq_validSpace_of_all_observed` | `Thm1.lean` |
| **Cor. 3**, Π = 𝒱 ⟹ \|M(T₀)\| = P − q(T₀), with q(T₀) ≤ P | `Latc.cor3` | `Thm1.lean` |
| **Cor. 4**, Π = 𝒱 ⟹ v ∈ Obsᵢ appears P / Cardᵢ times in 𝒱 and d_{i,v} = P / Cardᵢ − f_{i,v}(T₀) | `Latc.cor4` (Cardᵢ divides P: `Latc.freq_obsProduct`) | `Thm1.lean` |
| **Prop. 1**, equal profiles ⟹ equal missing sets, for all tables in 𝒱, ⟺ no non-zero zero-margin z | `Latc.prop1` | `Prop1.lean` |
| Prop. 1, read with condition sets | `Latc.prop1_condSets` | `Prop1.lean` |
| Prop. 1, a 2 × 2 grid of states in 𝒱 gives such a z | `Latc.prop1_exists` | `Prop1.lean` |
| Prop. 1, 𝒱 = 𝒟 and two attributes with ≥ 2 values give such a z (non-empty domains) | `Latc.prop1_exists_full`; the need for non-empty domains: `Latc.prop1_exists_full_needs_nonempty` | `Prop1.lean` |
| Prop. 1, a procedure of (domains, constraints, profile) is incorrect for some T₀ ⊆ 𝒱 | `Latc.prop1_procedure` | `Prop1.lean` |
| App. F, the even-parity space {000, 011, 101, 110} has no non-zero zero-margin z | `Latc.evenParity_no_zeroMarginVector`, from `Latc.evenParity_space` and `Latc.evenParity_profile_determines` (kernel `decide` over all 16 × 16 pairs of subsets of 𝒱) | `Prop1.lean` |
| **Prop. 6**, rank is a bijection from 𝒟 onto {0, …, \|𝒟\| − 1} | `Latc.prop6`, `Latc.prop6_existsUnique` (digit vectors: `Latc.rankFin_bijective`) | `Prop6.lean` |
| Prop. 6, the hypothesis \|Dᵢ\| ≥ 1 is unused | `Latc.prop6_empty_domain` | `Prop6.lean` |
| **Prop. 7**, p prime-valued and one-to-one on attribute-value pairs ⟹ K injective | `Latc.prop7_injective` | `Prop7.lean` |
| Prop. 7, two values of one attribute share a prime ⟹ K not injective (non-empty domains) | `Latc.prop7_not_injective`; the need for non-empty domains: `Latc.prop7_not_injective_needs_nonempty` | `Prop7.lean` |
| Prop. 7, primes 2, 3 and 2, 5: keys 4, 10, 6, 15, K injective | `Latc.prop7_shared_injective` | `Prop7.lean` |
| Prop. 7, primes 2, 3 and 2, 3: (v, b) and (a, w) both get 6 | `Latc.prop7_shared_not_injective` | `Prop7.lean` |
| Prop. 7, sharing across attributes: K may or may not be injective | `Latc.prop7_may_or_may_not` | `Prop7.lean` |

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
5. **Proposition 1, the case 𝒱 = 𝒟, uses non-empty domains.** "When 𝒱 = 𝒟, this holds
   as soon as two attributes have two or more values" needs fixed values for the other
   attributes, so every other domain must be non-empty. With three attributes of sizes
   2, 2 and 0, 𝒟 is empty and no vector on it is non-zero
   (`Latc.prop1_exists_full_needs_nonempty`). Section 3.1 assumes non-empty domains, so
   the statement holds as the paper reads. The Lean statement carries
   `[∀ k, Nonempty (D k)]`. The first form of the criterion ("for some fixed values of
   the other attributes, the four states … lie in 𝒱") supplies these values itself and
   needs nothing more. The equivalence and the procedure clause hold for every n,
   including n = 0.
   *Minimal fix:* none needed. Optionally: "when 𝒱 = 𝒟, and all domains being
   non-empty (Section 3.1), this holds as soon as two attributes have two or more values".
6. **Proposition 6's hypothesis "every |Dᵢ| ≥ 1" is unused.** If some domain is empty,
   𝒟 is empty and {0, 1, …, |𝒟| − 1} is empty too, so rank is the empty bijection.
   `Latc.prop6` has no size hypothesis, and `Latc.prop6_empty_domain` shows the case
   with sizes 2 and 0. The statement is true as written.
   *Minimal fix:* none needed. Optionally: "rank is a bijection from the product space
   onto {0, 1, …, |𝒟| − 1}" with the hypothesis deleted.
7. **Proposition 7, "if two values of the same attribute share a prime, K is not
   injective", uses non-empty domains.** Two rows that differ only in those two values
   exist only if every other domain has a value. With domains of sizes 2 and 0 and the
   prime 2 for every pair, the two values of the first attribute share a prime and K is
   injective, because the product space is empty
   (`Latc.prop7_not_injective_needs_nonempty`). Section 3.1 assumes non-empty domains,
   so the statement holds as the paper reads; the Lean statement carries
   `[∀ j, Nonempty (D j)]`. Part (a) needs every p(Aᵢ, v) to be prime, which the
   paper states.
   *Minimal fix:* none needed. Optionally append "(the domains being non-empty)".

## Scope and modelling choices

- Reading B is modelled by its output set Π ∖ cond(T₀), which is how Appendix F's proof
  characterizes it. The mixed-radix bijection of Proposition 6 is formalized in
  `Prop6.lean`, for any finite domains, so it applies with Dᵢ replaced by Obsᵢ(T₀). The
  step from the odometer loop of the implementation to that rank is not formalized.
- COMPLETE's `key()` is an arbitrary function injective on 𝒱. Proposition 7
  (`Prop7.lean`) shows when a prime-product key is one. The canonical form of
  Appendix D.3 is not formalized.
- Theorem 1 reads "T₀ is complete" as M(T₀) = ∅, and Corollary 4 states
  d_{i,v} = P / Cardᵢ − f_{i,v}(T₀) in ℕ together with f_{i,v}(T₀) ≤ P / Cardᵢ, so the
  subtraction does not truncate. The procedure clause of Proposition 1 takes the domains
  as the finite sets `univ` of the fixed types `D i`, the constraint as a predicate and
  the profile, and returns an output sequence judged by `Correct`.
- The vector z of Proposition 1 is a function 𝒟 → ℤ with values in {−1, 0, 1} that
  vanishes outside 𝒱 (`Latc.ZeroMarginVector`).
- Proposition 5 and Corollary 2 are not formalized.
