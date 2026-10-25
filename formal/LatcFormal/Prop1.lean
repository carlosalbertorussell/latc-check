import LatcFormal.Prop4

/-!
# Proposition 1 (Section 5.1; proof in Appendix F)

Over a fixed valid space 𝒱, any two initial tables whose distinct condition tuples lie in
𝒱 and have the same frequency profile have the same missing set if and only if no
non-zero vector z ∈ {−1, 0, 1}^𝒱 has all its margins zero. Such a vector exists whenever
two attributes Aᵢ, Aⱼ have values a ≠ a′ and b ≠ b′ such that, for some fixed values of
the other attributes, the four states with these values on Aᵢ and Aⱼ lie in 𝒱; when
𝒱 = 𝒟, this holds as soon as two attributes have two or more values. Where such a vector
exists, any procedure whose output depends on T₀ only through the domains, the
constraints and the frequency profile is incorrect for some T₀.

The frequency profile of T is `freq T : (i : ι) → D i → ℕ`, and z is a
`ZeroMarginVector` (`LatcFormal.Prop4`).
-/

set_option linter.unusedSectionVars false

namespace Latc

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]
  {D : ι → Type*} [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)]
  (C : (∀ i, D i) → Prop) [DecidablePred C]

/-- Every two tables inside 𝒱 with equal profiles have equal condition sets. -/
def ProfileDetermines : Prop :=
  ∀ T T' : Finset (∀ i, D i), T ⊆ validSpace C → T' ⊆ validSpace C →
    freq T = freq T' → T = T'

/-- A non-zero zero-margin vector exists. -/
def HasZeroMarginVector : Prop :=
  ∃ z : (∀ i, D i) → ℤ, ZeroMarginVector C z ∧ ∃ x, z x ≠ 0

/-- Inside 𝒱, equal missing sets and equal condition sets are the same thing. -/
lemma missing_eq_iff {T T' : Finset (∀ i, D i)} (hT : T ⊆ validSpace C)
    (hT' : T' ⊆ validSpace C) : missing C T = missing C T' ↔ T = T' := by
  refine ⟨fun h => ?_, fun h => h ▸ rfl⟩
  have := congrArg (validSpace C \ ·) h
  rwa [missing, missing, Finset.sdiff_sdiff_eq_self hT, Finset.sdiff_sdiff_eq_self hT'] at this

/-- The margin of z = 1_T − 1_{T'} at (i, v) is f_{i,v}(T) − f_{i,v}(T′). -/
lemma margin_indicator_sub {T T' : Finset (∀ i, D i)} (hT : T ⊆ validSpace C)
    (hT' : T' ⊆ validSpace C) (i : ι) (v : D i) :
    ∑ x ∈ (validSpace C).filter (fun x => x i = v),
        ((if x ∈ T then 1 else 0) - (if x ∈ T' then 1 else 0) : ℤ) =
      (freq T i v : ℤ) - freq T' i v := by
  rw [sum_sub_distrib, sum_boole, sum_boole, freq, freq]
  congr 2
  · congr 1; ext x; simp only [mem_filter]; have := @hT x; tauto
  · congr 1; ext x; simp only [mem_filter]; have := @hT' x; tauto

/-- **Proposition 1**, the equivalence: the profile determines the missing set of every
table inside 𝒱 if and only if no non-zero zero-margin vector exists. -/
theorem prop1 :
    (∀ T T' : Finset (∀ i, D i), T ⊆ validSpace C → T' ⊆ validSpace C →
        freq T = freq T' → missing C T = missing C T') ↔
      ¬ HasZeroMarginVector C := by
  constructor
  · -- a non-zero z gives two tables {z = 1} and {z = −1} with equal profiles
    rintro h ⟨z, hz, x, hx⟩
    let T := (validSpace C).filter (fun x => z x = 1)
    let T' := (validSpace C).filter (fun x => z x = -1)
    have hT : T ⊆ validSpace C := filter_subset _ _
    have hT' : T' ⊆ validSpace C := filter_subset _ _
    have hprof : freq T = freq T' := by
      funext i v
      have hm := hz.margin i v
      rw [sum_eq_card_sub_card z hz.values] at hm
      have e1 : ((validSpace C).filter (fun x => x i = v)).filter (fun x => z x = 1) =
          T.filter (fun x => x i = v) := by
        ext y; simp only [T, mem_filter]; tauto
      have e2 : ((validSpace C).filter (fun x => x i = v)).filter (fun x => z x = -1) =
          T'.filter (fun x => x i = v) := by
        ext y; simp only [T', mem_filter]; tauto
      rw [e1, e2] at hm
      unfold freq
      omega
    have heq := (missing_eq_iff C hT hT').mp (h T T' hT hT' hprof)
    have hC := mem_validSpace.mpr (hz.support x hx)
    rcases hz.values x with h1 | h1 | h1
    · have : x ∈ T' := mem_filter.mpr ⟨hC, h1⟩
      rw [← heq] at this
      have := (mem_filter.mp this).2; omega
    · exact hx h1
    · have : x ∈ T := mem_filter.mpr ⟨hC, h1⟩
      rw [heq] at this
      have := (mem_filter.mp this).2; omega
  · -- two different tables with equal profiles give z = 1_T − 1_{T'}
    intro hno T T' hT hT' hprof
    rw [missing_eq_iff C hT hT']
    by_contra hne
    apply hno
    refine ⟨fun x => (if x ∈ T then 1 else 0) - (if x ∈ T' then 1 else 0), ⟨?_, ?_, ?_⟩, ?_⟩
    · intro x; by_cases a : x ∈ T <;> by_cases b : x ∈ T' <;> simp [a, b]
    · intro x hx
      by_cases a : x ∈ T
      · exact mem_validSpace.mp (hT a)
      · by_cases b : x ∈ T'
        · exact mem_validSpace.mp (hT' b)
        · simp [a, b] at hx
    · intro i v
      rw [margin_indicator_sub C hT hT', hprof, sub_self]
    · obtain ⟨x, hx⟩ : ∃ x, ¬ (x ∈ T ↔ x ∈ T') := by
        by_contra h; push Not at h; exact hne (ext h)
      exact ⟨x, by by_cases a : x ∈ T <;> by_cases b : x ∈ T' <;> simp_all⟩

/-- Proposition 1 read with condition sets: `ProfileDetermines` is the same statement. -/
theorem prop1_condSets : ProfileDetermines C ↔ ¬ HasZeroMarginVector C := by
  rw [← prop1]
  refine forall_congr' fun T => forall_congr' fun T' => forall_congr' fun hT =>
    forall_congr' fun hT' => forall_congr' fun _ => (missing_eq_iff C hT hT').symm

/-! ### Existence of a vector from a 2 × 2 sub-grid -/

/-- The state equal to w except for value α on attribute i and β on attribute j. -/
def grid (w : ∀ k, D k) (i j : ι) (α : D i) (β : D j) : ∀ k, D k :=
  Function.update (Function.update w i α) j β

lemma grid_i {w : ∀ k, D k} {i j : ι} (hij : i ≠ j) (α : D i) (β : D j) :
    grid w i j α β i = α := by
  simp [grid, Function.update_of_ne hij]

lemma grid_j (w : ∀ k, D k) (i j : ι) (α : D i) (β : D j) : grid w i j α β j = β := by
  simp [grid]

lemma grid_other (w : ∀ k, D k) {i j k : ι} (hi : k ≠ i) (hj : k ≠ j) (α : D i)
    (β : D j) : grid w i j α β k = w k := by
  simp [grid, Function.update_of_ne hi, Function.update_of_ne hj]

/-- The indicator of one state, as an integer vector. -/
def ind (p x : ∀ k, D k) : ℤ := if x = p then 1 else 0

lemma sum_ind_filter (S : Finset (∀ k, D k)) (p : ∀ k, D k) (hp : p ∈ S) (i : ι) (v : D i) :
    ∑ x ∈ S.filter (fun x => x i = v), ind p x = if p i = v then 1 else 0 := by
  unfold ind
  rw [sum_ite_eq']
  simp [mem_filter, hp]

/-- **Proposition 1**, existence: if a 2 × 2 grid of states, with values a ≠ a′ on Aᵢ,
b ≠ b′ on Aⱼ and fixed values w on the other attributes, lies in 𝒱, then the vector
z = +1 at (a, b), (a′, b′), −1 at (a, b′), (a′, b) and 0 elsewhere is a non-zero
zero-margin vector. -/
theorem prop1_exists (w : ∀ k, D k) {i j : ι} (hij : i ≠ j) {a a' : D i} (ha : a ≠ a')
    {b b' : D j} (hb : b ≠ b')
    (hV : ∀ α ∈ ({a, a'} : Finset (D i)), ∀ β ∈ ({b, b'} : Finset (D j)),
      C (grid w i j α β)) :
    HasZeroMarginVector C := by
  set p1 := grid w i j a b
  set p2 := grid w i j a' b'
  set p3 := grid w i j a b'
  set p4 := grid w i j a' b
  have gi := fun (α : D i) (β : D j) => grid_i (w := w) hij α β
  have gj := grid_j w i j
  -- the four states are distinct
  have ne_i : ∀ {β β' : D j}, grid w i j a β ≠ grid w i j a' β' := fun h =>
    ha (by simpa [gi] using congrFun h i)
  have ne_j : ∀ {α α' : D i}, grid w i j α b ≠ grid w i j α' b' := fun h =>
    hb (by simpa [gj] using congrFun h j)
  have h12 : p1 ≠ p2 := ne_i
  have h13 : p1 ≠ p3 := ne_j
  have h14 : p1 ≠ p4 := ne_i
  have h23 : p2 ≠ p3 := fun h => ne_i h.symm
  have h24 : p2 ≠ p4 := fun h => ne_j h.symm
  have h34 : p3 ≠ p4 := ne_i
  have mem : ∀ α ∈ ({a, a'} : Finset (D i)), ∀ β ∈ ({b, b'} : Finset (D j)),
      grid w i j α β ∈ validSpace C := fun α hα β hβ => mem_validSpace.mpr (hV α hα β hβ)
  refine ⟨fun x => ind p1 x + ind p2 x - ind p3 x - ind p4 x, ⟨?_, ?_, ?_⟩, ⟨p1, ?_⟩⟩
  · intro x
    by_cases e1 : x = p1
    · subst e1; simp [ind, h12, h13, h14]
    by_cases e2 : x = p2
    · subst e2; simp [ind, h12.symm, h23, h24]
    by_cases e3 : x = p3
    · subst e3; simp [ind, h13.symm, h23.symm, h34]
    by_cases e4 : x = p4
    · subst e4; simp [ind, h14.symm, h24.symm, h34.symm]
    simp [ind, e1, e2, e3, e4]
  · intro x hx
    by_cases e1 : x = p1
    · subst e1; exact hV a (by simp) b (by simp)
    by_cases e2 : x = p2
    · subst e2; exact hV a' (by simp) b' (by simp)
    by_cases e3 : x = p3
    · subst e3; exact hV a (by simp) b' (by simp)
    by_cases e4 : x = p4
    · subst e4; exact hV a' (by simp) b (by simp)
    simp [ind, e1, e2, e3, e4] at hx
  · intro k v
    rw [sum_sub_distrib, sum_sub_distrib, sum_add_distrib,
      sum_ind_filter _ p1 (mem a (by simp) b (by simp)),
      sum_ind_filter _ p2 (mem a' (by simp) b' (by simp)),
      sum_ind_filter _ p3 (mem a (by simp) b' (by simp)),
      sum_ind_filter _ p4 (mem a' (by simp) b (by simp))]
    by_cases hki : k = i
    · subst hki
      simp only [p1, p2, p3, p4, gi]
      ring
    by_cases hkj : k = j
    · subst hkj
      simp only [p1, p2, p3, p4, gj]
      ring
    simp only [p1, p2, p3, p4, grid_other w hki hkj]
    ring
  · simp [ind, h12, h13, h14]

/-- **Proposition 1**, the case 𝒱 = 𝒟: two attributes with two or more values each give a
non-zero zero-margin vector. The fixed values of the other attributes exist because every
domain is non-empty (the standing assumption of Section 3.1, here `Nonempty (D k)`). -/
theorem prop1_exists_full [∀ k, Nonempty (D k)] (hC : ∀ x, C x) {i j : ι} (hij : i ≠ j)
    (hi : 2 ≤ Fintype.card (D i)) (hj : 2 ≤ Fintype.card (D j)) :
    HasZeroMarginVector C := by
  obtain ⟨a, a', ha⟩ := Fintype.exists_pair_of_one_lt_card hi
  obtain ⟨b, b', hb⟩ := Fintype.exists_pair_of_one_lt_card hj
  exact prop1_exists C (fun k => Classical.arbitrary (D k)) hij ha hb
    (fun _ _ _ _ => hC _)

/-- The non-emptiness of the other domains is needed for the case 𝒱 = 𝒟: with three
attributes of sizes 2, 2 and 0, the product space is empty, so no vector on it is
non-zero. -/
theorem prop1_exists_full_needs_nonempty :
    let m : Fin 3 → ℕ := ![2, 2, 0]
    ¬ HasZeroMarginVector (fun _ : (∀ k, Fin (m k)) => True) := by
  rintro m ⟨z, -, x, -⟩
  exact (x 2).elim0

/-! ### Procedures that see only the profile -/

/-- **Proposition 1**, the procedure clause. A procedure `F` takes the domains (as the
finite sets `univ`), the constraint and the frequency profile, and returns an output
sequence. If a non-zero zero-margin vector exists, some table T₀ inside 𝒱 gets an
incorrect output. -/
theorem prop1_procedure
    (F : (∀ k, Finset (D k)) → ((∀ k, D k) → Prop) → ((k : ι) → D k → ℕ) →
      List (∀ k, D k))
    (hz : HasZeroMarginVector C) :
    ∃ T : Finset (∀ k, D k), T ⊆ validSpace C ∧
      ¬ Correct C (F (fun _ => univ) C (freq T)) T := by
  obtain ⟨T, T', hT, hT', hprof, hne⟩ : ∃ T T' : Finset (∀ k, D k), T ⊆ validSpace C ∧
      T' ⊆ validSpace C ∧ freq T = freq T' ∧ missing C T ≠ missing C T' := by
    by_contra h
    push Not at h
    exact (prop1 C).mp (fun T T' hT hT' hp => h T T' hT hT' hp) hz
  by_contra h
  push Not at h
  have c1 := (h T hT).2
  have c2 := (h T' hT').2
  rw [hprof] at c1
  exact hne (c1.symm.trans c2)

/-! ### The even-parity space of Appendix F -/

/-- The even-parity constraint on three Boolean attributes. -/
def evenParity : (Fin 3 → Bool) → Prop := fun x => (x 0 ^^ x 1 ^^ x 2) = false

instance : DecidablePred evenParity := fun x => by unfold evenParity; infer_instance

/-- The state (a, b, c). -/
def bits (a b c : Bool) : Fin 3 → Bool := ![a, b, c]

/-- 𝒱 = {000, 011, 101, 110}. -/
theorem evenParity_space :
    validSpace evenParity =
      {bits false false false, bits false true true, bits true false true,
        bits true true false} := by
  decide

set_option maxRecDepth 100000 in
/-- On the even-parity space, the profile determines every table: the kernel checks all
16 × 16 pairs of subsets of 𝒱. -/
theorem evenParity_profile_determines :
    ∀ T ∈ (validSpace evenParity).powerset, ∀ T' ∈ (validSpace evenParity).powerset,
      (∀ i v, freq T i v = freq T' i v) → T = T' := by
  decide

/-- **Appendix F, proof of Proposition 1**: the even-parity space
{000, 011, 101, 110} ⊆ {0, 1}³ admits no non-zero zero-margin vector. -/
theorem evenParity_no_zeroMarginVector : ¬ HasZeroMarginVector evenParity := by
  rw [← prop1_condSets]
  intro T T' hT hT' hprof
  exact evenParity_profile_determines T (mem_powerset.mpr hT) T' (mem_powerset.mpr hT')
    (fun i v => congrFun (congrFun hprof i) v)

end Latc
