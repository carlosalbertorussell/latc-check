import Mathlib

/-!
# Formal setting (Paper A, Section 3)

Attributes are indexed by a finite type `ι`; attribute `i` has the declared finite
domain `D i`. A condition tuple is a dependent function `x : ∀ i, D i`, so the
product space 𝒟 = D₁ × ⋯ × Dₙ is the finite type `∀ i, D i`.

The constraint set C is modelled as one decidable predicate `C` on complete tuples:
a tuple satisfies it exactly when it satisfies every constraint of the paper's set C
(the conjunction of finitely many decidable predicates is a decidable predicate).

An initial table is represented by its set of condition tuples `T : Finset (∀ i, D i)`,
which is faithful because Section 3.2 assumes the condition tuples of a table are
distinct. Only COMPLETE (Proposition 3) works on rows `(x, y)`, because its first
`require` is what enforces that assumption; see `LatcFormal.Prop3`.
-/

set_option linter.unusedSectionVars false

namespace Latc

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]
  {D : ι → Type*} [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)]

section Defs

variable (C : (∀ i, D i) → Prop) [DecidablePred C]

/-- The valid space 𝒱 = {x ∈ 𝒟 : c(x) for all c ∈ C} (Section 3.1). -/
def validSpace : Finset (∀ i, D i) := univ.filter C

/-- The missing set M(T₀) = 𝒱 ∖ cond(T₀) (Section 3.2). -/
def missing (T : Finset (∀ i, D i)) : Finset (∀ i, D i) := validSpace C \ T

end Defs

/-- Observed values Obs_i(S) = {xᵢ : x ∈ S} (Section 3.2). -/
def obs (S : Finset (∀ i, D i)) (i : ι) : Finset (D i) := S.image (fun x => x i)

/-- The product of the observed values Π = Obs₁(T₀) × ⋯ × Obsₙ(T₀) (Section 3.2). -/
def obsProduct (S : Finset (∀ i, D i)) : Finset (∀ i, D i) := Fintype.piFinset (obs S)

/-- The output of LATC under Reading B, as a set: the tuples of Π that match no row of
T₀, R = Π ∖ cond(T₀) (Section 4.2; Appendix F, proof of Proposition 2). -/
def readingB (S : Finset (∀ i, D i)) : Finset (∀ i, D i) := obsProduct S \ S

/-- The frequency f_{i,v}(S) = |{x ∈ S : xᵢ = v}| (Section 3.2). -/
def freq (S : Finset (∀ i, D i)) (i : ι) (v : D i) : ℕ := (S.filter (fun x => x i = v)).card

section Check

variable (C : (∀ i, D i) → Prop) [DecidablePred C]

/-- The generalized cardinality check CHECK of Section 6.1 / 6.2, applied to an output
sequence `out` of a completion procedure, for an initial table with `q` rows and
condition set `T`:

* |M| = |𝒱| − |T₀|, and
* f_{i,v}(M) = f_{i,v}(𝒱) − f_{i,v}(T₀) for every attribute i and every v ∈ Dᵢ.

The output is a list, so its length and value counts are taken with multiplicity, as the
implementation does (`latc_check/latc.py`, `deficit_check`). Differences are taken in `ℤ`,
as in the Python code, so that no truncated subtraction can make a check pass. -/
def Check (out : List (∀ i, D i)) (q : ℕ) (T : Finset (∀ i, D i)) : Prop :=
  (out.length : ℤ) = (validSpace C).card - q ∧
    ∀ (i : ι) (v : D i),
      (out.countP (fun x => decide (x i = v)) : ℤ) = freq (validSpace C) i v - freq T i v

/-- A completion procedure's output is correct if it has no repeated tuple and its set
of elements is exactly the missing set (Section 3.2). -/
def Correct (out : List (∀ i, D i)) (T : Finset (∀ i, D i)) : Prop :=
  out.Nodup ∧ out.toFinset = missing C T

end Check

/-! ### Basic lemmas -/

lemma mem_validSpace {C : (∀ i, D i) → Prop} [DecidablePred C] {x : ∀ i, D i} :
    x ∈ validSpace C ↔ C x := by
  simp [validSpace]

lemma mem_obsProduct {S : Finset (∀ i, D i)} {x : ∀ i, D i} :
    x ∈ obsProduct S ↔ ∀ i, x i ∈ obs S i := by
  simp [obsProduct]

/-- Every condition tuple of T₀ lies in the product of the observed values. -/
lemma subset_obsProduct (S : Finset (∀ i, D i)) : S ⊆ obsProduct S := by
  intro x hx
  rw [mem_obsProduct]
  intro i
  exact mem_image.mpr ⟨x, hx, rfl⟩

/-- Frequencies of a set difference subtract when the subtracted set is inside. -/
lemma freq_sdiff {S T : Finset (∀ i, D i)} (h : T ⊆ S) (i : ι) (v : D i) :
    freq (S \ T) i v = freq S i v - freq T i v := by
  unfold freq
  have : (S \ T).filter (fun x => x i = v) =
      S.filter (fun x => x i = v) \ T.filter (fun x => x i = v) := by
    ext x; simp only [mem_filter, mem_sdiff]; tauto
  rw [this, card_sdiff_of_subset (filter_subset_filter _ h)]

/-- On a duplicate-free list, value counts are the frequencies of its set of elements. -/
lemma countP_eq_freq {l : List (∀ i, D i)} (hl : l.Nodup) (i : ι) (v : D i) :
    l.countP (fun x => decide (x i = v)) = freq l.toFinset i v := by
  unfold freq
  rw [List.countP_eq_length_filter, ← List.toFinset_card_of_nodup (hl.filter _),
    List.toFinset_filter]
  simp only [decide_eq_true_eq]

end Latc
