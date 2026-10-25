import LatcFormal.Basic

/-!
# Proposition 5: the reduction between clause constraints and CNF

Proposition 5 of Paper A states that, when every constraint is a clause (a disjunction of
conditions Aᵢ = v), deciding whether M(T₀) is non-empty is NP-complete, deciding
completeness is coNP-complete, and computing |𝒱| is #P-complete. Its hardness rests on
Cook's theorem (SAT is NP-complete, 1971) and Valiant's theorem (#SAT is #P-complete even
for monotone two-literal clauses, 1979). Complexity classes, polynomial time and those two
theorems are outside this library. This file machine-checks the combinatorial
correspondence the proof rests on:

1. CNF formulas over Boolean variables and clause constraints over domains {0, 1}
   (`Bool`) translate into each other with the same satisfying assignments
   (`encode_validSpace`, `decode_validSpace`), and the translations are size-preserving
   (`encode_size`) and mutually inverse (`decode_encode`, `encode_decode`).
2. With T₀ = ∅, M(T₀) = 𝒱 = the set of satisfying assignments, so M(∅) is non-empty iff
   the formula is satisfiable, and M(∅) = ∅ iff it is unsatisfiable
   (`prop5_missing_empty`, `prop5_nonempty_iff_satisfiable`,
   `prop5_complete_iff_unsatisfiable`, and the converse direction `prop5_decode_*`).
3. |𝒱| is the number of satisfying assignments, and |M(T₀)| = |𝒱| − |T₀| for distinct
   condition tuples inside 𝒱 (`prop5_card_validSpace`, `card_missing_of_subset`,
   `prop5_card_missing`).
4. Monotone two-literal clauses (xᵢ ∨ xⱼ) are exactly the clauses of two conditions
   Aᵢ = 1, Aⱼ = 1 (`encode_isPos2_iff`, `decode_isPos2`, and the distinct-variable
   variants).
5. The certificate check of the NP membership argument (`verify`, `verify_correct`).
6. Two precision checks on the wording: a constraint set whose conditions all use one
   value v has a trivial non-emptiness question (`single_value_nonempty_iff`), and
   satisfiability reduces to constraint sets whose clauses each use one value
   (`prop5_pure_clauses`), so within-clause mixing is not needed for NP-hardness.

The variables are an arbitrary finite type `V`; the paper's n attributes are `V = Fin n`.
States are functions `V → Bool`, the condition tuples of Basic with `D i = Bool`.
-/

set_option linter.unusedSectionVars false

namespace Latc.Prop5

open Finset

/-! ### CNF formulas -/

/-- A literal: xᵢ (`pos i`) or ¬xᵢ (`neg i`). -/
inductive Lit (V : Type*) where
  | pos (i : V)
  | neg (i : V)
  deriving DecidableEq

/-- A clause of a CNF formula: a disjunction of literals. -/
abbrev Clause (V : Type*) := List (Lit V)

/-- A formula in conjunctive normal form: a conjunction of clauses. -/
abbrev CNF (V : Type*) := List (Clause V)

variable {V : Type*}

/-- The value of a literal under an assignment. -/
def Lit.eval : Lit V → (V → Bool) → Bool
  | .pos i, x => x i
  | .neg i, x => !x i

/-- A clause is satisfied when one of its literals is. -/
def evalClause (c : Clause V) (x : V → Bool) : Bool := c.any (fun l => l.eval x)

/-- A CNF formula is satisfied when each of its clauses is. -/
def evalCNF (φ : CNF V) (x : V → Bool) : Bool := φ.all (fun c => evalClause c x)

/-- Satisfiability. -/
def Satisfiable (φ : CNF V) : Prop := ∃ x, evalCNF φ x = true

/-! ### Clause constraints -/

/-- A condition Aᵢ = v over the domain {0, 1}, with `false` for 0 and `true` for 1. -/
structure Cond (V : Type*) where
  attr : V
  val : Bool
  deriving DecidableEq

/-- A clause constraint: a disjunction of conditions Aᵢ = v. -/
abbrev ClauseCon (V : Type*) := List (Cond V)

/-- A constraint set whose constraints are all clauses. -/
abbrev ConSet (V : Type*) := List (ClauseCon V)

/-- A state satisfies the condition Aᵢ = v when its i-th value is v. -/
def Cond.holds (a : Cond V) (x : V → Bool) : Bool := x a.attr == a.val

/-- A state satisfies a clause constraint when it satisfies one of its conditions. -/
def holdsClause (c : ClauseCon V) (x : V → Bool) : Bool := c.any (fun a => a.holds x)

/-- A state satisfies a constraint set when it satisfies each clause. -/
def holdsAll (S : ConSet V) (x : V → Bool) : Bool := S.all (fun c => holdsClause c x)

/-- The constraint set as the single decidable predicate `C` of `Basic.lean`. -/
def conPred (S : ConSet V) (x : V → Bool) : Prop := holdsAll S x = true

instance (S : ConSet V) : DecidablePred (conPred S) :=
  fun x => inferInstanceAs (Decidable (holdsAll S x = true))

/-! ### The translations -/

/-- xᵢ becomes Aᵢ = 1 and ¬xᵢ becomes Aᵢ = 0. -/
def Lit.toCond : Lit V → Cond V
  | .pos i => ⟨i, true⟩
  | .neg i => ⟨i, false⟩

/-- Aᵢ = 1 becomes xᵢ and Aᵢ = 0 becomes ¬xᵢ. -/
def Cond.toLit : Cond V → Lit V
  | ⟨i, true⟩ => .pos i
  | ⟨i, false⟩ => .neg i

/-- The clause constraints encoding a CNF formula, one per clause. -/
def encode (φ : CNF V) : ConSet V := φ.map (List.map Lit.toCond)

/-- The CNF formula of a clause constraint set, one clause per constraint. -/
def decode (S : ConSet V) : CNF V := S.map (List.map Cond.toLit)

@[simp] lemma Lit.holds_toCond (l : Lit V) (x : V → Bool) : l.toCond.holds x = l.eval x := by
  cases l <;> simp [Lit.toCond, Cond.holds, Lit.eval]

@[simp] lemma Cond.eval_toLit (a : Cond V) (x : V → Bool) : a.toLit.eval x = a.holds x := by
  rcases a with ⟨i, _ | _⟩ <;> simp [Cond.toLit, Cond.holds, Lit.eval]

@[simp] lemma Cond.toLit_toCond (l : Lit V) : l.toCond.toLit = l := by
  cases l <;> rfl

@[simp] lemma Lit.toCond_toLit (a : Cond V) : a.toLit.toCond = a := by
  rcases a with ⟨i, _ | _⟩ <;> rfl

theorem decode_encode (φ : CNF V) : decode (encode φ) = φ := by
  simp [decode, encode, Function.comp_def]

theorem encode_decode (S : ConSet V) : encode (decode S) = S := by
  simp [decode, encode, Function.comp_def]

/-- The encoding keeps the number of clauses and the length of every clause, so it is a
linear-size translation. -/
theorem encode_size (φ : CNF V) : (encode φ).map List.length = φ.map List.length := by
  simp [encode, Function.comp_def]

/-- Same satisfying assignments, CNF to constraints. -/
@[simp] theorem holdsAll_encode (φ : CNF V) (x : V → Bool) :
    holdsAll (encode φ) x = evalCNF φ x := by
  simp [holdsAll, encode, holdsClause, evalCNF, evalClause, List.all_map, List.any_map,
    Function.comp_def]

/-- Same satisfying assignments, constraints to CNF. -/
@[simp] theorem evalCNF_decode (S : ConSet V) (x : V → Bool) :
    evalCNF (decode S) x = holdsAll S x := by
  rw [← holdsAll_encode, encode_decode]

/-! ### The valid space and the missing set (Fintype variables) -/

variable [Fintype V] [DecidableEq V]

/-- The set of satisfying assignments of a CNF formula. -/
def satSet (φ : CNF V) : Finset (V → Bool) := univ.filter (fun x => evalCNF φ x = true)

/-- The number of satisfying assignments, the quantity of #SAT. -/
def numSat (φ : CNF V) : ℕ := (satSet φ).card

/-- **Item 1, CNF to constraints.** Every CNF formula is encoded by a set of clause
constraints whose valid space 𝒱 is its set of satisfying assignments. -/
theorem encode_validSpace (φ : CNF V) :
    validSpace (D := fun _ => Bool) (conPred (encode φ)) = satSet φ := by
  ext x; simp [validSpace, satSet, conPred]

/-- **Item 1, constraints to CNF.** Every set of clause constraints over domains {0, 1}
has the same valid space as the CNF formula `decode S`. -/
theorem decode_validSpace (S : ConSet V) :
    validSpace (D := fun _ => Bool) (conPred S) = satSet (decode S) := by
  ext x; simp [validSpace, satSet, conPred]

lemma mem_validSpace_conPred (S : ConSet V) (x : V → Bool) :
    x ∈ validSpace (D := fun _ => Bool) (conPred S) ↔ ∀ c ∈ S, holdsClause c x = true := by
  simp [validSpace, conPred, holdsAll]

/-- With T₀ = ∅, M(T₀) = 𝒱 for every constraint predicate. -/
theorem missing_empty {ι : Type*} [Fintype ι] [DecidableEq ι] {D : ι → Type*}
    [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)] (C : (∀ i, D i) → Prop)
    [DecidablePred C] : missing C ∅ = validSpace C := by
  simp [missing]

/-- **Item 2.** With T₀ = ∅, M(T₀) = 𝒱 = the set of satisfying assignments. -/
theorem prop5_missing_empty (φ : CNF V) :
    missing (D := fun _ => Bool) (conPred (encode φ)) ∅ = satSet φ := by
  rw [missing_empty, encode_validSpace]

/-- **Item 2, non-emptiness is satisfiability.** -/
theorem prop5_nonempty_iff_satisfiable (φ : CNF V) :
    (missing (D := fun _ => Bool) (conPred (encode φ)) ∅).Nonempty ↔ Satisfiable φ := by
  rw [prop5_missing_empty]
  simp [Finset.Nonempty, satSet, Satisfiable]

/-- **Item 2, completeness is unsatisfiability.** The empty table is complete
(M(∅) = ∅) iff the formula is unsatisfiable. -/
theorem prop5_complete_iff_unsatisfiable (φ : CNF V) :
    missing (D := fun _ => Bool) (conPred (encode φ)) ∅ = ∅ ↔ ¬ Satisfiable φ := by
  rw [← prop5_nonempty_iff_satisfiable, Finset.not_nonempty_iff_eq_empty]

/-- **Item 2, converse direction.** For a set of clause constraints, M(∅) is non-empty
iff its CNF formula is satisfiable. -/
theorem prop5_decode_nonempty_iff_satisfiable (S : ConSet V) :
    (missing (D := fun _ => Bool) (conPred S) ∅).Nonempty ↔ Satisfiable (decode S) := by
  rw [← prop5_nonempty_iff_satisfiable, encode_decode]

/-- **Item 2, converse direction.** The empty table is complete iff the CNF formula of
the constraint set is unsatisfiable. -/
theorem prop5_decode_complete_iff_unsatisfiable (S : ConSet V) :
    missing (D := fun _ => Bool) (conPred S) ∅ = ∅ ↔ ¬ Satisfiable (decode S) := by
  rw [← prop5_complete_iff_unsatisfiable, encode_decode]

/-- **Item 3.** |𝒱| is the number of satisfying assignments. -/
theorem prop5_card_validSpace (φ : CNF V) :
    (validSpace (D := fun _ => Bool) (conPred (encode φ))).card = numSat φ := by
  rw [encode_validSpace, numSat]

/-- |M(T₀)| = |𝒱| − |T₀| when the condition tuples of T₀ are distinct (T₀ is a `Finset`)
and lie inside 𝒱. This holds for every constraint predicate. -/
theorem card_missing_of_subset {ι : Type*} [Fintype ι] [DecidableEq ι] {D : ι → Type*}
    [∀ i, Fintype (D i)] [∀ i, DecidableEq (D i)] (C : (∀ i, D i) → Prop)
    [DecidablePred C] (T : Finset (∀ i, D i)) (hT : T ⊆ validSpace C) :
    (missing C T).card = (validSpace C).card - T.card := by
  rw [missing, card_sdiff_of_subset hT]

/-- **Item 3.** For a CNF formula and a table T₀ with distinct condition tuples inside 𝒱,
|M(T₀)| is the number of satisfying assignments minus |T₀|. -/
theorem prop5_card_missing (φ : CNF V) (T : Finset (V → Bool))
    (hT : T ⊆ validSpace (D := fun _ => Bool) (conPred (encode φ))) :
    (missing (D := fun _ => Bool) (conPred (encode φ)) T).card = numSat φ - T.card := by
  rw [card_missing_of_subset _ T hT, prop5_card_validSpace]

/-! ### Monotone two-literal clauses -/

/-- Every clause is a monotone two-literal clause xᵢ ∨ xⱼ. -/
def IsMonotone2 (φ : CNF V) : Prop := ∀ c ∈ φ, ∃ i j, c = [.pos i, .pos j]

/-- Every clause constraint is a disjunction of two conditions Aᵢ = 1, Aⱼ = 1. -/
def IsPos2 (S : ConSet V) : Prop := ∀ c ∈ S, ∃ i j, c = [⟨i, true⟩, ⟨j, true⟩]

/-- As `IsMonotone2`, with two distinct variables in every clause (the edges of a graph). -/
def IsMonotone2Distinct (φ : CNF V) : Prop := ∀ c ∈ φ, ∃ i j, i ≠ j ∧ c = [.pos i, .pos j]

/-- As `IsPos2`, with two distinct conditions in every clause. -/
def IsPos2Distinct (S : ConSet V) : Prop :=
  ∀ c ∈ S, ∃ i j, i ≠ j ∧ c = [⟨i, true⟩, ⟨j, true⟩]

lemma map_toCond_eq_pos2 (c : Clause V) (i j : V) :
    c.map Lit.toCond = [⟨i, true⟩, ⟨j, true⟩] ↔ c = [.pos i, .pos j] := by
  constructor
  · intro h
    have := congrArg (List.map Cond.toLit) h
    simp only [List.map_map, Function.comp_def, Cond.toLit_toCond, List.map_id'] at this
    exact this
  · rintro rfl; rfl

/-- **Item 4.** A CNF formula is monotone two-literal iff its encoding consists of
clauses of two conditions Aᵢ = 1. -/
theorem encode_isPos2_iff (φ : CNF V) : IsPos2 (encode φ) ↔ IsMonotone2 φ := by
  simp [IsPos2, IsMonotone2, encode, map_toCond_eq_pos2]

/-- **Item 4, converse direction.** The CNF formula of a set of clauses of two conditions
Aᵢ = 1 is monotone two-literal. -/
theorem decode_isPos2 (S : ConSet V) : IsMonotone2 (decode S) ↔ IsPos2 S := by
  rw [← encode_isPos2_iff, encode_decode]

/-- **Item 4, distinct variables.** -/
theorem encode_isPos2Distinct_iff (φ : CNF V) :
    IsPos2Distinct (encode φ) ↔ IsMonotone2Distinct φ := by
  simp [IsPos2Distinct, IsMonotone2Distinct, encode, map_toCond_eq_pos2]

/-- A clause A_i = 1 ∨ A_i = 1 written with the same condition twice is the one-condition
clause A_i = 1. -/
theorem holdsClause_dup (i : V) (x : V → Bool) :
    holdsClause [⟨i, true⟩, ⟨i, true⟩] x = holdsClause [⟨i, true⟩] x := by
  simp [holdsClause]

/-! ### The certificate check (NP and #P membership) -/

/-- The certificate check of Proposition 5's NP membership argument: a state x is a
certificate when it lies outside cond(T₀) and satisfies every clause. This is the
polynomial-time verifier of that argument (one membership test in T₀ and one pass over the
clauses); polynomial time itself is not formalized here. -/
def verify (S : ConSet V) (T : Finset (V → Bool)) (x : V → Bool) : Bool :=
  !decide (x ∈ T) && holdsAll S x

/-- **Item 5.** The certificate check is correct: it accepts x iff x ∈ M(T₀). -/
theorem verify_correct (S : ConSet V) (T : Finset (V → Bool)) (x : V → Bool) :
    verify S T x = true ↔ x ∈ missing (D := fun _ => Bool) (conPred S) T := by
  simp [verify, missing, validSpace, conPred, and_comm]

/-- M(T₀) is non-empty iff some certificate is accepted (NP membership). -/
theorem nonempty_iff_exists_certificate (S : ConSet V) (T : Finset (V → Bool)) :
    (missing (D := fun _ => Bool) (conPred S) T).Nonempty ↔ ∃ x, verify S T x = true := by
  simp only [verify_correct, Finset.Nonempty]

/-- |M(T₀)| is the number of accepted certificates (#P membership). -/
theorem card_missing_eq_certificates (S : ConSet V) (T : Finset (V → Bool)) :
    (missing (D := fun _ => Bool) (conPred S) T).card =
      (univ.filter (fun x => verify S T x = true)).card := by
  congr 1; ext x; simp [verify_correct]

/-! ### Precision checks on "clauses may mix A_i = 0 and A_i = 1" -/

/-- If every condition of the constraint set uses one value v, M(∅) is non-empty iff no
clause is empty: the constant state v satisfies every non-empty clause. The question is
then decided by a scan of the clauses, so NP-hardness needs both values to occur in the
constraint set. -/
theorem single_value_nonempty_iff (S : ConSet V) (v : Bool)
    (hv : ∀ c ∈ S, ∀ a ∈ c, a.val = v) :
    (missing (D := fun _ => Bool) (conPred S) ∅).Nonempty ↔ [] ∉ S := by
  rw [missing_empty]
  constructor
  · rintro ⟨x, hx⟩ hnil
    rw [mem_validSpace_conPred] at hx
    simpa [holdsClause] using hx [] hnil
  · intro hnil
    refine ⟨fun _ => v, ?_⟩
    simp only [mem_validSpace_conPred, holdsClause, List.any_eq_true]
    intro c hc
    obtain ⟨a, ha⟩ := List.exists_mem_of_ne_nil c (fun h => hnil (h ▸ hc))
    exact ⟨a, ha, by simp [Cond.holds, hv c hc a ha]⟩

/-- Each literal becomes a condition with value 1: xᵢ ↦ A_{(i,0)} = 1 and
¬xᵢ ↦ A_{(i,1)} = 1, where A_{(i,1)} stands for ¬xᵢ. -/
def Lit.toPosCond : Lit V → Cond (V ⊕ V)
  | .pos i => ⟨.inl i, true⟩
  | .neg i => ⟨.inr i, true⟩

/-- The two clauses that force A_{(i,1)} = ¬A_{(i,0)}: one with value 1 only, one with
value 0 only. -/
def linkClauses (i : V) : ConSet (V ⊕ V) :=
  [[⟨.inl i, true⟩, ⟨.inr i, true⟩], [⟨.inl i, false⟩, ⟨.inr i, false⟩]]

/-- The standard translation of a CNF formula over V into clause constraints over 2|V|
attributes in which every clause uses one value only. `vars` lists the variables; for
V = Fin n it is `List.finRange n`. The output has |φ| + 2|vars| clauses. -/
def purify (vars : List V) (φ : CNF V) : ConSet (V ⊕ V) :=
  φ.map (List.map Lit.toPosCond) ++ vars.flatMap linkClauses

theorem purify_single_valued (vars : List V) (φ : CNF V) :
    ∀ c ∈ purify vars φ, ∃ v, ∀ a ∈ c, a.val = v := by
  intro c hc
  simp only [purify, List.mem_append, List.mem_map, List.mem_flatMap, linkClauses,
    List.mem_cons, List.not_mem_nil, or_false] at hc
  rcases hc with ⟨d, -, rfl⟩ | ⟨i, -, rfl | rfl⟩
  · refine ⟨true, ?_⟩
    simp only [List.mem_map]
    rintro _ ⟨l, -, rfl⟩
    cases l <;> rfl
  · exact ⟨true, by simp⟩
  · exact ⟨false, by simp⟩

lemma holds_toPosCond (l : Lit V) (x : V → Bool) :
    l.toPosCond.holds (Sum.elim x (fun i => !x i)) = l.eval x := by
  cases l <;> simp [Lit.toPosCond, Cond.holds, Lit.eval]

/-- **Within-clause mixing is not needed.** A CNF formula is satisfiable iff M(∅) is
non-empty for its translation `purify`, whose clauses each use one value
(`purify_single_valued`). With Cook's theorem this makes non-emptiness NP-hard already for
such constraint sets. -/
theorem prop5_pure_clauses (vars : List V) (hvars : ∀ i, i ∈ vars) (φ : CNF V) :
    (missing (D := fun _ => Bool) (conPred (purify vars φ)) ∅).Nonempty ↔ Satisfiable φ := by
  rw [missing_empty]
  have hmem : ∀ c, c ∈ purify vars φ ↔
      (∃ d ∈ φ, d.map Lit.toPosCond = c) ∨ ∃ i ∈ vars, c ∈ linkClauses i := by
    intro c; simp [purify]
  constructor
  · rintro ⟨z, hz⟩
    rw [mem_validSpace_conPred] at hz
    -- the link clauses force z (inr i) = !z (inl i)
    have hlink : ∀ i, z (.inr i) = !z (.inl i) := by
      intro i
      have h1 := hz [⟨.inl i, true⟩, ⟨.inr i, true⟩]
        ((hmem _).2 (Or.inr ⟨i, hvars i, by simp [linkClauses]⟩))
      have h2 := hz [⟨.inl i, false⟩, ⟨.inr i, false⟩]
        ((hmem _).2 (Or.inr ⟨i, hvars i, by simp [linkClauses]⟩))
      simp [holdsClause, Cond.holds] at h1 h2
      cases hl : z (.inl i) <;> cases hr : z (.inr i) <;> simp_all
    refine ⟨fun i => z (.inl i), ?_⟩
    simp only [evalCNF, List.all_eq_true, evalClause, List.any_eq_true]
    intro c hc
    have := hz _ ((hmem _).2 (Or.inl ⟨c, hc, rfl⟩))
    simp only [holdsClause, List.any_map, List.any_eq_true, Function.comp_apply] at this
    obtain ⟨l, hl, h⟩ := this
    refine ⟨l, hl, ?_⟩
    cases l <;> simp_all [Lit.toPosCond, Cond.holds, Lit.eval]
  · rintro ⟨x, hx⟩
    refine ⟨Sum.elim x (fun i => !x i), ?_⟩
    rw [mem_validSpace_conPred]
    simp only [evalCNF, List.all_eq_true] at hx
    intro c hc
    rcases (hmem c).1 hc with ⟨d, hd, rfl⟩ | ⟨i, -, hi⟩
    · have := hx d hd
      simp only [holdsClause, List.any_map, Function.comp_def, holds_toPosCond]
      exact this
    · simp only [linkClauses, List.mem_cons, List.not_mem_nil, or_false] at hi
      rcases hi with rfl | rfl <;> cases x i <;> simp [holdsClause, Cond.holds]

/-! ### Concrete examples, checked by the kernel with `decide` -/

namespace Examples

/-- x₀ ∧ ¬x₀, unsatisfiable. -/
def φUnsat : CNF (Fin 1) := [[.pos 0], [.neg 0]]

/-- (x₀ ∨ ¬x₁) ∧ x₁, satisfied only by x₀ = x₁ = 1. -/
def φSat : CNF (Fin 2) := [[.pos 0, .neg 1], [.pos 1]]

/-- The triangle (x₀ ∨ x₁) ∧ (x₁ ∨ x₂) ∧ (x₀ ∨ x₂), a monotone two-literal formula. -/
def φTriangle : CNF (Fin 3) := [[.pos 0, .pos 1], [.pos 1, .pos 2], [.pos 0, .pos 2]]

/-- An unsatisfiable CNF gives a complete empty table: M(∅) = ∅. -/
theorem unsat_complete :
    missing (D := fun _ => Bool) (conPred (encode φUnsat)) ∅ = ∅ := by decide

/-- A satisfiable CNF gives a non-empty M(∅), here the single state (1, 1). -/
theorem sat_nonempty :
    missing (D := fun _ => Bool) (conPred (encode φSat)) ∅ = {![true, true]} := by decide

/-- The triangle is encoded by clauses of two conditions Aᵢ = 1, and |𝒱| = 4 (the states
with at most one 0). -/
theorem triangle_count :
    IsPos2Distinct (encode φTriangle) ∧
      (validSpace (D := fun _ => Bool) (conPred (encode φTriangle))).card = 4 := by
  unfold IsPos2Distinct; decide

/-- With T₀ = {(1, 1, 1)} ⊆ 𝒱, |M(T₀)| = 4 − 1 = 3, and the certificate check accepts
(0, 1, 1) and rejects the row (1, 1, 1) of T₀ and the invalid state (0, 0, 1). -/
theorem triangle_table :
    (missing (D := fun _ => Bool) (conPred (encode φTriangle)) {![true, true, true]}).card = 3 ∧
      verify (encode φTriangle) {![true, true, true]} ![false, true, true] = true ∧
      verify (encode φTriangle) {![true, true, true]} ![true, true, true] = false ∧
      verify (encode φTriangle) {![true, true, true]} ![false, false, true] = false := by
  decide

/-- The repeated condition: [A₀ = 1, A₀ = 1] counts as `IsPos2` but holds exactly when the
one condition A₀ = 1 holds, i.e. it is the unit clause x₀. -/
theorem dup_clause :
    IsPos2 ([[⟨0, true⟩, ⟨0, true⟩]] : ConSet (Fin 1)) ∧
      ¬ IsPos2Distinct ([[⟨0, true⟩, ⟨0, true⟩]] : ConSet (Fin 1)) ∧
      (validSpace (D := fun _ => Bool) (conPred ([[⟨0, true⟩, ⟨0, true⟩]] : ConSet (Fin 1)))) =
        {![true]} := by
  unfold IsPos2 IsPos2Distinct; decide

/-- Two distinct rows can share one condition tuple when their outcomes differ. Their
condition tuples, listed with repetition, are [(0, 1, 1), (0, 1, 1)]: the list has length
2, cond(T₀) has one element, and |M(T₀)| = 4 − 1 = 3 differs from |𝒱| minus the number of
rows, 4 − 2 = 2. The count |𝒱| − |T₀| needs distinct condition tuples. -/
theorem repeated_condition_tuple :
    let rows : List (Fin 3 → Bool) := [![false, true, true], ![false, true, true]]
    (missing (D := fun _ => Bool) (conPred (encode φTriangle)) rows.toFinset).card = 3 ∧
      (validSpace (D := fun _ => Bool) (conPred (encode φTriangle))).card - rows.length = 2 := by
  decide

end Examples

end Latc.Prop5
