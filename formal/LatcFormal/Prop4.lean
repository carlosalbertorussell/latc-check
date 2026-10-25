import LatcFormal.Basic

/-!
# Proposition 4 and the generalized cardinality check (Section 6.2; Appendix F)

Proposition 4. If the condition tuples of T₀ are distinct and lie in 𝒱, every correct
output passes the generalized check. If a non-zero zero-margin vector z of Proposition 1
exists, then for T₀ = {x : z_x = 1} the incorrect output 𝒱 ∖ {x : z_x = −1} also
passes it.

Section 6.2 also states that membership checks close the gap: if every output tuple lies
in 𝒱, is absent from cond(T₀) and occurs once, then |M| = |𝒱| − |T₀| forces
M = 𝒱 ∖ cond(T₀).

Condition tuples are distinct by construction here: T₀ is the `Finset` T of its condition
tuples and q(T₀) = |T|.
-/

set_option linter.unusedSectionVars false

namespace Latc

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]
  {D : ι → Type*} [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)]
  (C : (∀ i, D i) → Prop) [DecidablePred C]

/-- **Proposition 4, necessity.** If cond(T₀) ⊆ 𝒱, every correct output passes the
generalized check. -/
theorem prop4_necessity (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C)
    (out : List (∀ i, D i)) (hout : Correct C out T) :
    Check C out T.card T := by
  obtain ⟨hnd, hset⟩ := hout
  constructor
  · rw [← List.toFinset_card_of_nodup hnd, hset, missing, card_sdiff_of_subset hT,
      Nat.cast_sub (card_le_card hT)]
  · intro i v
    have hle : freq T i v ≤ freq (validSpace C) i v :=
      card_le_card (filter_subset_filter _ hT)
    rw [countP_eq_freq hnd, hset, missing, freq_sdiff hT, Nat.cast_sub hle]

/-- Section 6.2, membership checks close the gap: an output with no repeated tuple, every
tuple in 𝒱 and none in cond(T₀), and of size |𝒱| − |T₀|, is exactly the missing set.
(The hypothesis cond(T₀) ⊆ 𝒱 is the standing one of Proposition 4 and of COMPLETE's
second `require`.) -/
theorem check_membership_sufficient (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C)
    (out : List (∀ i, D i)) (hnd : out.Nodup)
    (hmem : ∀ x ∈ out, C x ∧ x ∉ T)
    (hlen : (out.length : ℤ) = (validSpace C).card - T.card) :
    Correct C out T := by
  refine ⟨hnd, ?_⟩
  have hsub : out.toFinset ⊆ missing C T := by
    intro x hx
    have := hmem x (List.mem_toFinset.mp hx)
    simp [missing, mem_validSpace, this]
  apply eq_of_subset_of_card_le hsub
  rw [List.toFinset_card_of_nodup hnd, missing, card_sdiff_of_subset hT]
  have : (out.length : ℤ) = ((validSpace C).card - T.card : ℕ) := by
    rw [hlen, Nat.cast_sub (card_le_card hT)]
  omega

/-- Section 6.2, contrapositive form: an output that passes the size count but is not
correct contains a tuple twice, a tuple of cond(T₀) or a tuple outside 𝒱. -/
theorem check_wrong_output_cases (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C)
    (out : List (∀ i, D i)) (hcheck : Check C out T.card T) (hwrong : ¬ Correct C out T) :
    ¬ out.Nodup ∨ ∃ x ∈ out, x ∈ T ∨ ¬ C x := by
  by_contra h
  push Not at h
  obtain ⟨hnd, hmem⟩ := h
  exact hwrong (check_membership_sufficient C T hT out hnd
    (fun x hx => ⟨(hmem x hx).2, (hmem x hx).1⟩) hcheck.1)

/-! ### Insufficiency -/

/-- A vector z ∈ {−1, 0, 1}^𝒱 with all margins zero, as in Proposition 1: z vanishes
outside 𝒱, and Σ_{x ∈ 𝒱, xᵢ = v} z_x = 0 for every attribute i and every v ∈ Dᵢ. -/
structure ZeroMarginVector (z : (∀ i, D i) → ℤ) : Prop where
  values : ∀ x, z x = -1 ∨ z x = 0 ∨ z x = 1
  support : ∀ x, z x ≠ 0 → C x
  margin : ∀ (i : ι) (v : D i), ∑ x ∈ (validSpace C).filter (fun x => x i = v), z x = 0

/-- For z with values in {−1, 0, 1}, Σ_S z = |{z = 1} ∩ S| − |{z = −1} ∩ S|. -/
lemma sum_eq_card_sub_card (z : (∀ i, D i) → ℤ) (hz : ∀ x, z x = -1 ∨ z x = 0 ∨ z x = 1)
    (S : Finset (∀ i, D i)) :
    ∑ x ∈ S, z x = ((S.filter (fun x => z x = 1)).card : ℤ) -
      (S.filter (fun x => z x = -1)).card := by
  rw [card_filter, card_filter, Nat.cast_sum, Nat.cast_sum, ← sum_sub_distrib]
  refine sum_congr rfl fun x _ => ?_
  rcases hz x with h | h | h <;> simp [h]

/-- **Proposition 4, insufficiency (general case, Appendix F)**, with the extra
hypothesis that there is at least one attribute (`Nonempty ι`); see
`prop4_insufficiency_needs_an_attribute` and formal/README.md.

For a non-zero zero-margin vector z and T₀ = {x : z_x = 1}, the output
𝒱 ∖ {x : z_x = −1} is not the missing set, yet it passes the generalized check. -/
theorem prop4_insufficiency [Nonempty ι] (z : (∀ i, D i) → ℤ) (hz : ZeroMarginVector C z)
    (hne : ∃ x, z x ≠ 0) :
    let T := (validSpace C).filter (fun x => z x = 1)
    let O := (validSpace C).filter (fun x => z x ≠ -1)
    T ⊆ validSpace C ∧ O ≠ missing C T ∧ Check C O.toList T.card T := by
  intro T O
  refine ⟨filter_subset _ _, ?_, ?_⟩
  · -- O and M(T₀) differ at any x with z_x ≠ 0
    obtain ⟨x, hx⟩ := hne
    have hC := mem_validSpace.mpr (hz.support x hx)
    intro h
    have hiff : x ∈ O ↔ x ∈ missing C T := by rw [h]
    simp only [O, T, missing, mem_filter, mem_sdiff, hC, true_and] at hiff
    rcases hz.values x with h1 | h1 | h1 <;> simp [h1] at hiff hx
  · -- the sizes and frequencies agree
    have key : ∀ S : Finset (∀ i, D i), S ⊆ validSpace C → ∑ x ∈ S, z x = 0 →
        (S.filter (fun x => z x ≠ -1)).card = (S.card : ℤ) - (S.filter fun x => z x = 1).card := by
      intro S _ hS
      rw [sum_eq_card_sub_card z hz.values] at hS
      have hs : S.filter (fun x => z x ≠ -1) = S \ S.filter (fun x => z x = -1) := by
        ext x; simp only [mem_filter, mem_sdiff]; tauto
      rw [hs, card_sdiff_of_subset (filter_subset _ _),
        Nat.cast_sub (card_le_card (filter_subset _ _))]
      omega
    have hO_eq : ∀ i (v : D i),
        O.filter (fun x => x i = v) =
          ((validSpace C).filter (fun x => x i = v)).filter (fun x => z x ≠ -1) := by
      intro i v; ext x; simp only [O, mem_filter]; tauto
    have hT_eq : ∀ i (v : D i),
        T.filter (fun x => x i = v) =
          ((validSpace C).filter (fun x => x i = v)).filter (fun x => z x = 1) := by
      intro i v; ext x; simp only [T, mem_filter]; tauto
    constructor
    · rw [length_toList]
      obtain ⟨i⟩ := ‹Nonempty ι›
      have htotal : ∑ x ∈ validSpace C, z x = 0 := by
        rw [← sum_fiberwise (validSpace C) (fun x => x i) z]
        exact sum_eq_zero fun v _ => hz.margin i v
      exact key _ subset_rfl htotal
    · intro i v
      rw [countP_eq_freq (nodup_toList O), toList_toFinset]
      unfold freq
      rw [hO_eq, hT_eq]
      exact key _ (filter_subset _ _) (hz.margin i v)

/-- The extra hypothesis `Nonempty ι` is needed: with no attributes, 𝒟 = 𝒱 = {()} has
no margin equations, so z = 1 is a non-zero zero-margin vector, but the output
𝒱 ∖ {z = −1} = {()} has one row where |𝒱| − |T₀| = 1 − 1 = 0, and fails the check. -/
theorem prop4_insufficiency_needs_an_attribute :
    let C : (∀ _ : Fin 0, Bool) → Prop := fun _ => True
    let z : (∀ _ : Fin 0, Bool) → ℤ := fun _ => 1
    ZeroMarginVector C z ∧ (∃ x, z x ≠ 0) ∧
      ¬ Check C ((validSpace C).filter (fun x => z x ≠ -1)).toList
        ((validSpace C).filter (fun x => z x = 1)).card
        ((validSpace C).filter (fun x => z x = 1)) := by
  intro C z
  refine ⟨⟨fun _ => by simp [z], fun _ _ => trivial, fun i => i.elim0⟩,
    ⟨fun i => i.elim0, by simp [z]⟩, ?_⟩
  rintro ⟨h, -⟩
  have hV : validSpace C = univ := by ext x; simp [validSpace, C]
  simp [hV, z] at h

end Latc
