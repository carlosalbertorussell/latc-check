import LatcFormal.Prop3

/-!
# The two-attribute pair of the worked example (Sections 5.1 and 6.2)

Sex {M, F} and Activity {D, I}, no constraint, T₀ = {(M, D), (F, I)}. Proposition 4's
proof uses it: the wrong output T₀ itself has the size and frequencies of the right one,
M(T₀) = {(M, I), (F, D)}. All facts below are checked by the kernel with `decide`.
-/

set_option linter.unusedSectionVars false

namespace Latc.Examples

open Finset

inductive Sex | M | F
  deriving DecidableEq, Repr

inductive Activity | D | I
  deriving DecidableEq, Repr

instance : Fintype Sex := ⟨{Sex.M, Sex.F}, fun x => by cases x <;> simp⟩

instance : Fintype Activity := ⟨{Activity.D, Activity.I}, fun x => by cases x <;> simp⟩

/-- Attribute 0 is Sex, attribute 1 is Activity. -/
abbrev Dom : Fin 2 → Type
  | 0 => Sex
  | 1 => Activity

instance : ∀ i, Fintype (Dom i)
  | 0 => inferInstanceAs (Fintype Sex)
  | 1 => inferInstanceAs (Fintype Activity)

instance : ∀ i, DecidableEq (Dom i)
  | 0 => inferInstanceAs (DecidableEq Sex)
  | 1 => inferInstanceAs (DecidableEq Activity)

/-- The condition tuple (s, a). -/
def tup (s : Sex) (a : Activity) : ∀ i, Dom i
  | 0 => s
  | 1 => a

/-- No constraint: 𝒱 = 𝒟. -/
def noConstraint : (∀ i, Dom i) → Prop := fun _ => True

instance : DecidablePred noConstraint := fun _ => isTrue trivial

instance (C : (∀ i, Dom i) → Prop) [DecidablePred C] (out : List (∀ i, Dom i)) (q : ℕ)
    (T : Finset (∀ i, Dom i)) : Decidable (Check C out q T) := by
  unfold Check; infer_instance

instance (C : (∀ i, Dom i) → Prop) [DecidablePred C] (out : List (∀ i, Dom i))
    (T : Finset (∀ i, Dom i)) : Decidable (Correct C out T) := by
  unfold Correct; infer_instance

/-- T₀ = {(M, D), (F, I)}. -/
def T0 : Finset (∀ i, Dom i) := {tup .M .D, tup .F .I}

/-- Its twin T₀′ = {(M, I), (F, D)}. -/
def T0' : Finset (∀ i, Dom i) := {tup .M .I, tup .F .D}

/-- M(T₀) = {(M, I), (F, D)}. -/
theorem missing_T0 : missing noConstraint T0 = T0' := by decide

/-- T₀ and its twin have the same frequency profile and different missing sets
(Section 5.1). -/
theorem twins_same_profile :
    (∀ i (v : Dom i), freq T0 i v = freq T0' i v) ∧
      missing noConstraint T0 ≠ missing noConstraint T0' := by
  decide

/-- **Proposition 4, insufficiency (the paper's concrete counterexample).** The output
listing T₀ itself passes the generalized check for T₀ but is not a correct output. -/
theorem prop4_counterexample :
    Check noConstraint [tup .M .D, tup .F .I] T0.card T0 ∧
      ¬ Correct noConstraint [tup .M .D, tup .F .I] T0 := by
  decide

/-- The lexicographic enumeration of Sex × Activity. -/
def lexEnum : List (∀ i, Dom i) := [tup .M .D, tup .M .I, tup .F .D, tup .F .I]

/-- COMPLETE on the pair, with the identity as key and outcome ⊥ for both examples,
returns (M, I), (F, D) in lexicographic order. -/
theorem complete_pair :
    complete noConstraint lexEnum id
      ({(tup .M .D, none), (tup .F .I, none)} : Finset ((∀ i, Dom i) × Option Bool)) =
        [tup .M .I, tup .F .D] := by
  decide

/-- Reading B is exact here: every declared value is observed and there is no constraint,
so Π = 𝒱 (Proposition 2). -/
theorem readingB_pair : readingB T0 = missing noConstraint T0 := by decide

end Latc.Examples
