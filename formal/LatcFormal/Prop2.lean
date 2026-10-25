import LatcFormal.Basic

/-!
# Proposition 2 (Section 5.3; proof in Appendix F)

Let cond(T₀) ⊆ 𝒱, let Π = Obs₁(T₀) × ⋯ × Obsₙ(T₀) and let R = Π ∖ cond(T₀) be the
output of Reading B. Then

* M(T₀) ∖ R = 𝒱 ∖ Π (R misses exactly the valid states that carry a declared value
  no example shows),
* R ∖ M(T₀) = Π ∖ 𝒱 (R adds exactly the tuples of Π that violate a constraint),

so R = M(T₀) if and only if Π = 𝒱.
-/

set_option linter.unusedSectionVars false

namespace Latc

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]
  {D : ι → Type*} [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)]
  (C : (∀ i, D i) → Prop) [DecidablePred C]

/-- Proposition 2, first identity: M(T₀) ∖ R = 𝒱 ∖ Π.
This identity holds for every T₀; it uses only cond(T₀) ⊆ Π. -/
theorem prop2_missed (T : Finset (∀ i, D i)) :
    missing C T \ readingB T = validSpace C \ obsProduct T := by
  ext x
  have hP : x ∈ T → x ∈ obsProduct T := fun h => subset_obsProduct T h
  simp only [missing, readingB, mem_sdiff]
  tauto

/-- Proposition 2, second identity: R ∖ M(T₀) = Π ∖ 𝒱, under cond(T₀) ⊆ 𝒱. -/
theorem prop2_extra (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C) :
    readingB T \ missing C T = obsProduct T \ validSpace C := by
  ext x
  have hV := @hT x
  simp only [missing, readingB, mem_sdiff]
  tauto

/-- Proposition 2, the characterization of the missed states: a valid state lies outside
Π exactly when one of its values is a declared value that no example shows. -/
theorem prop2_missed_iff (T : Finset (∀ i, D i)) (x : ∀ i, D i) :
    x ∈ validSpace C \ obsProduct T ↔ C x ∧ ∃ i, x i ∉ obs T i := by
  simp [mem_validSpace, mem_obsProduct]

/-- **Proposition 2.** If cond(T₀) ⊆ 𝒱, Reading B's output equals the missing set
M(T₀) if and only if the product of the observed values equals the valid space. -/
theorem prop2 (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C) :
    readingB T = missing C T ↔ obsProduct T = validSpace C := by
  constructor
  · intro h
    have h1 := prop2_missed C T
    have h2 := prop2_extra C T hT
    rw [h, sdiff_self] at h1 h2
    exact subset_antisymm (sdiff_eq_bot_iff.mp h2.symm) (sdiff_eq_bot_iff.mp h1.symm)
  · intro h
    simp [readingB, missing, h]

/-- The hypothesis cond(T₀) ⊆ 𝒱 of Proposition 2 cannot be dropped from the "only if"
direction: with one Boolean attribute, the constraint `x = true` and
T₀ = {false, true}, Reading B returns R = ∅ = M(T₀) although Π = 𝒟 ≠ 𝒱. -/
example :
    let C : (Fin 1 → Bool) → Prop := fun x => x 0 = true
    let T : Finset (Fin 1 → Bool) := {fun _ => false, fun _ => true}
    readingB T = missing C T ∧ obsProduct T ≠ validSpace C := by
  decide

/-- Appendix F's proof of Proposition 2 opens with "If T₀ = ∅, then Π = R = ∅". This
holds when there is at least one attribute ... -/
theorem obsProduct_empty [Nonempty ι] : obsProduct (∅ : Finset (∀ i, D i)) = ∅ := by
  obtain ⟨i⟩ := ‹Nonempty ι›
  ext x
  simp only [mem_obsProduct, obs, image_empty, notMem_empty, iff_false, not_forall]
  exact ⟨i, id⟩

/-- ... but not for n = 0 attributes, where Π is the product of no sets, the
one-element set {()}. Proposition 2 itself is unaffected: its two identities hold for
every T₀ and every n. -/
example : obsProduct (∅ : Finset (∀ _ : Fin 0, Bool)) ≠ ∅ := by
  decide

end Latc
