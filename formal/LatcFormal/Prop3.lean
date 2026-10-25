import LatcFormal.Prop4

/-!
# Proposition 3: correctness of COMPLETE (Section 6.1)

```
COMPLETE(D1..Dn, C, T0):
  K0 ← { key(x) : (x, y) ∈ T0 }
  require |K0| = |T0|                 # T0 has no duplicate conditions
  require every x in T0 lies in V     # else report out-of-domain rows
  M ← ∅
  for x in D1 × … × Dn in lexicographic order:
      if every c ∈ C holds for x and key(x) ∉ K0:
          M ← M ∪ { (x, ⊥) }
  CHECK(M)
  return M
```

Assumptions: domains finite and declared; each constraint a decidable predicate; rows
are exact conjunctions; key() injective on the valid space.

Here T₀ is a finite set of rows `(x, y)` with outcomes in an arbitrary type `Y`, so that
the second `require` is meaningful. The loop's fixed visiting order is a parameter
`enum : List (∀ i, D i)` that lists every tuple of 𝒟 exactly once; the lexicographic
order is one such list. The output is the list of added condition tuples, in visiting
order (the outcome ⊥ carries no information and is left out).
-/

set_option linter.unusedSectionVars false

namespace Latc

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]
  {D : ι → Type*} [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)]
  (C : (∀ i, D i) → Prop) [DecidablePred C]
  {K : Type*} [DecidableEq K] {Y : Type*} [DecidableEq Y]

/-- cond(T): the set of condition tuples of a table of rows. -/
def cond (T₀ : Finset ((∀ i, D i) × Y)) : Finset (∀ i, D i) := T₀.image Prod.fst

/-- K₀ = {key(x) : (x, y) ∈ T₀}. -/
def keys (key : (∀ i, D i) → K) (T₀ : Finset ((∀ i, D i) × Y)) : Finset K :=
  T₀.image (fun r => key r.1)

/-- The loop of COMPLETE: visit `enum` in order and keep each x that satisfies the
constraints and whose key is not in K₀. -/
def complete (enum : List (∀ i, D i)) (key : (∀ i, D i) → K)
    (T₀ : Finset ((∀ i, D i) × Y)) : List (∀ i, D i) :=
  enum.filter (fun x => decide (C x ∧ key x ∉ keys key T₀))

/-- **Proposition 3 (correctness of COMPLETE).** If `enum` visits every tuple of 𝒟
exactly once, key() is injective on 𝒱, and T₀ meets the two `require` conditions, then
COMPLETE returns exactly M(T₀), each tuple once, in the visiting order of `enum`, and
its output passes CHECK with |T₀| the number of rows. -/
theorem prop3 (enum : List (∀ i, D i)) (henum : enum.Nodup) (hall : ∀ x, x ∈ enum)
    (key : (∀ i, D i) → K) (hkey : Set.InjOn key (validSpace C))
    (T₀ : Finset ((∀ i, D i) × Y))
    (hreq1 : (keys key T₀).card = T₀.card)
    (hreq2 : ∀ r ∈ T₀, C r.1) :
    Correct C (complete C enum key T₀) (cond T₀) ∧
      (complete C enum key T₀).Sublist enum ∧
      Check C (complete C enum key T₀) T₀.card (cond T₀) := by
  have hcondV : cond T₀ ⊆ validSpace C := by
    intro x hx
    obtain ⟨r, hr, rfl⟩ := mem_image.mp hx
    exact mem_validSpace.mpr (hreq2 r hr)
  have hcorrect : Correct C (complete C enum key T₀) (cond T₀) := by
    refine ⟨henum.filter _, ?_⟩
    ext x
    simp only [complete, List.mem_toFinset, List.mem_filter, hall, true_and,
      decide_eq_true_eq, missing, mem_sdiff, mem_validSpace]
    constructor
    · rintro ⟨hC, hk⟩
      refine ⟨hC, fun hx => hk ?_⟩
      obtain ⟨r, hr, rfl⟩ := mem_image.mp hx
      exact mem_image.mpr ⟨r, hr, rfl⟩
    · rintro ⟨hC, hx⟩
      refine ⟨hC, fun hk => hx ?_⟩
      obtain ⟨r, hr, hkr⟩ := mem_image.mp hk
      have : r.1 = x := hkey (mem_validSpace.mpr (hreq2 r hr)) (mem_validSpace.mpr hC) hkr
      rw [← this]
      exact mem_image.mpr ⟨r, hr, rfl⟩
  -- the second `require` makes the condition tuples of T₀ distinct, so |cond(T₀)| = |T₀|
  have hcard : (cond T₀).card = T₀.card := by
    rw [cond, card_image_iff]
    have hinj := card_image_iff.mp hreq1
    intro r hr s hs h
    exact hinj hr hs (show key r.1 = key s.1 by rw [h])
  refine ⟨hcorrect, List.filter_sublist, ?_⟩
  have := prop4_necessity C (cond T₀) hcondV _ hcorrect
  rwa [hcard] at this

end Latc
