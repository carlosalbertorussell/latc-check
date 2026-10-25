import LatcFormal.Basic

/-!
# Theorem 1 and Corollaries 1, 3 and 4 (Section 5.2; proof in Appendix F)

Write Card_i = |Obs_i(T₀)|, P = Card_1 × ⋯ × Card_n and q(T₀) = |T₀|.

* **Theorem 1.** Let cond(T₀) ⊆ 𝒱 and let 𝒱 be the product of its projections, in
  particular when C = ∅. If T₀ is complete, then q(T₀) = P.
* **Corollary 1.** Under the hypotheses of Theorem 1, if q(T₀) < P, then T₀ is
  incomplete.
* **Corollary 3.** If Π = 𝒱, the number of rows to add is |M(T₀)| = P − q(T₀).
* **Corollary 4.** If Π = 𝒱, each observed value v of Aᵢ appears P / Card_i times in
  𝒱, and d_{i,v} = P / Card_i − f_{i,v}(T₀) rows of M(T₀) carry v.

A table is complete when it leaves no valid state uncovered, M(T₀) = ∅. The projections
of 𝒱 are `obs (validSpace C)`, so "𝒱 is the product of its projections" reads
`obsProduct (validSpace C) = validSpace C`.
-/

set_option linter.unusedSectionVars false

namespace Latc

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]
  {D : ι → Type*} [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)]
  (C : (∀ i, D i) → Prop) [DecidablePred C]

/-- T₀ is complete when its missing set is empty. -/
def Complete (T : Finset (∀ i, D i)) : Prop := missing C T = ∅

/-- P = Card_1 × ⋯ × Card_n, the product of the numbers of observed values. -/
def obsCardProd (T : Finset (∀ i, D i)) : ℕ := ∏ i, (obs T i).card

/-- |Π| = P. -/
lemma card_obsProduct (T : Finset (∀ i, D i)) : (obsProduct T).card = obsCardProd T := by
  simp [obsProduct, obsCardProd, Fintype.card_piFinset]

/-- With no constraint (C = ∅, here `C x` for every x), 𝒱 = 𝒟 is the product of its
projections. This holds for every family of domains, including empty ones. -/
lemma validSpace_isProduct_of_noConstraint (hC : ∀ x, C x) :
    obsProduct (validSpace C) = validSpace C := by
  have hV : validSpace C = univ := by ext x; simp [mem_validSpace, hC x]
  rw [hV]
  exact subset_antisymm (fun _ _ => mem_univ _) (subset_obsProduct _)

/-- A complete table inside 𝒱 is all of 𝒱. -/
lemma eq_validSpace_of_complete {T : Finset (∀ i, D i)} (hT : T ⊆ validSpace C)
    (hc : Complete C T) : T = validSpace C :=
  subset_antisymm hT (sdiff_eq_empty_iff_subset.mp hc)

/-- **Theorem 1.** If cond(T₀) ⊆ 𝒱, 𝒱 is the product of its projections and T₀ is
complete, then q(T₀) = P. -/
theorem thm1 (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C)
    (hprod : obsProduct (validSpace C) = validSpace C) (hc : Complete C T) :
    T.card = obsCardProd T := by
  have hTV := eq_validSpace_of_complete C hT hc
  rw [← card_obsProduct, hTV, hprod]

/-- Theorem 1 in the case the paper singles out, C = ∅. -/
theorem thm1_noConstraint (hC : ∀ x, C x) (T : Finset (∀ i, D i)) (hc : Complete C T) :
    T.card = obsCardProd T :=
  thm1 C T (fun x _ => mem_validSpace.mpr (hC x)) (validSpace_isProduct_of_noConstraint C hC) hc

/-- The remark after Theorem 1: if a constraint excludes some tuple of Π, a complete
table inside 𝒱 has cond(T₀) = 𝒱 ⊊ Π, so q(T₀) = |𝒱| < P. -/
theorem thm1_remark (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C) (hc : Complete C T)
    (hex : ∃ x ∈ obsProduct T, ¬ C x) :
    T.card = (validSpace C).card ∧ T.card < obsCardProd T := by
  have hTV := eq_validSpace_of_complete C hT hc
  refine ⟨by rw [hTV], ?_⟩
  rw [← card_obsProduct]
  apply card_lt_card
  refine (ssubset_iff_of_subset (subset_obsProduct T)).mpr ?_
  obtain ⟨x, hx, hnC⟩ := hex
  exact ⟨x, hx, fun h => hnC (mem_validSpace.mp (hT h))⟩

/-- **Corollary 1.** Under the hypotheses of Theorem 1, q(T₀) < P implies that T₀ is
incomplete. -/
theorem cor1 (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C)
    (hprod : obsProduct (validSpace C) = validSpace C) (hlt : T.card < obsCardProd T) :
    ¬ Complete C T := fun hc => (thm1 C T hT hprod hc ▸ hlt).false

/-- The precondition of [3] (every declared value is observed) with C = ∅ gives Π = 𝒱,
the hypothesis of Corollaries 3 and 4. -/
lemma obsProduct_eq_validSpace_of_all_observed (hC : ∀ x, C x) (T : Finset (∀ i, D i))
    (hobs : ∀ i, obs T i = univ) : obsProduct T = validSpace C := by
  ext x
  simp [mem_obsProduct, mem_validSpace, hobs, hC x]

/-- **Corollary 3.** If Π = 𝒱, then |M(T₀)| = P − q(T₀) (and q(T₀) ≤ P, so the
subtraction does not truncate). -/
theorem cor3 (T : Finset (∀ i, D i)) (hPi : obsProduct T = validSpace C) :
    (missing C T).card = obsCardProd T - T.card ∧ T.card ≤ obsCardProd T := by
  have hT : T ⊆ validSpace C := hPi ▸ subset_obsProduct T
  rw [← card_obsProduct, hPi, missing, card_sdiff_of_subset hT]
  exact ⟨rfl, card_le_card hT⟩

/-- In Π, an observed value v of Aᵢ appears in P / Card_i tuples, and Card_i divides P. -/
lemma freq_obsProduct (T : Finset (∀ i, D i)) (i : ι) {v : D i} (hv : v ∈ obs T i) :
    freq (obsProduct T) i v = obsCardProd T / (obs T i).card ∧
      (obs T i).card * (obsCardProd T / (obs T i).card) = obsCardProd T := by
  have hfib : freq (obsProduct T) i v = ∏ j ∈ univ.erase i, (obs T j).card :=
    Fintype.card_filter_piFinset_eq_of_mem _ i hv
  have hP : obsCardProd T = (obs T i).card * ∏ j ∈ univ.erase i, (obs T j).card :=
    (mul_prod_erase univ (fun j => (obs T j).card) (mem_univ i)).symm
  have hpos : 0 < (obs T i).card := card_pos.mpr ⟨v, hv⟩
  have hdiv : obsCardProd T / (obs T i).card = ∏ j ∈ univ.erase i, (obs T j).card := by
    rw [hP, Nat.mul_div_cancel_left _ hpos]
  rw [hfib, hdiv, ← hP]
  exact ⟨rfl, rfl⟩

/-- **Corollary 4.** If Π = 𝒱, each observed value v of Aᵢ appears P / Card_i times in
𝒱, and the number of rows of M(T₀) carrying v is d_{i,v} = P / Card_i − f_{i,v}(T₀),
with f_{i,v}(T₀) ≤ P / Card_i. -/
theorem cor4 (T : Finset (∀ i, D i)) (hPi : obsProduct T = validSpace C) (i : ι) {v : D i}
    (hv : v ∈ obs T i) :
    freq (validSpace C) i v = obsCardProd T / (obs T i).card ∧
      freq (missing C T) i v = obsCardProd T / (obs T i).card - freq T i v ∧
      freq T i v ≤ obsCardProd T / (obs T i).card := by
  have hT : T ⊆ validSpace C := hPi ▸ subset_obsProduct T
  have hV : freq (validSpace C) i v = obsCardProd T / (obs T i).card := by
    rw [← hPi]; exact (freq_obsProduct T i hv).1
  refine ⟨hV, ?_, ?_⟩
  · rw [missing, freq_sdiff hT, hV]
  · rw [← hV]; exact card_le_card (filter_subset_filter _ hT)

end Latc
