import LatcFormal.Basic

/-!
# Proposition 7 (Section 7; prime-product keys, Appendix D)

Assign each attribute-value pair (Aᵢ, v) a prime p(Aᵢ, v) and key a row by
K(x) = p(A₁, x₁) × ⋯ × p(Aₙ, xₙ).

* If p is one-to-one on attribute-value pairs and every row holds exactly one value per
  attribute, then K is injective on the product space.
* If two values of the same attribute share a prime, K is not injective.
* If p is one-to-one within each attribute but values of different attributes share a
  prime, K may or may not be injective.

Attribute-value pairs are the sigma type `Σ i, D i`. A row holds exactly one value per
attribute because it is a function `x : ∀ i, D i`.
-/

set_option linter.unusedSectionVars false

namespace Latc

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι] {D : ι → Type*}

/-- The prime-product key K(x) = ∏ᵢ p(Aᵢ, xᵢ). -/
def primeKey (p : (Σ i, D i) → ℕ) (x : ∀ i, D i) : ℕ := ∏ i, p ⟨i, x i⟩

/-- **Proposition 7 (a).** If every p(Aᵢ, v) is prime and p is one-to-one on
attribute-value pairs, K is injective on the product space. -/
theorem prop7_injective (p : (Σ i, D i) → ℕ) (hp : ∀ s, (p s).Prime)
    (hinj : Function.Injective p) : Function.Injective (primeKey p) := by
  intro x y h
  funext i
  have hdvd : p ⟨i, x i⟩ ∣ primeKey p y :=
    h ▸ dvd_prod_of_mem (fun j => p ⟨j, x j⟩) (mem_univ i)
  obtain ⟨j, -, hj⟩ := ((hp ⟨i, x i⟩).prime.dvd_finsetProd_iff _).mp hdvd
  have heq := hinj ((Nat.prime_dvd_prime_iff_eq (hp _) (hp _)).mp hj)
  obtain ⟨rfl, hxy⟩ := Sigma.mk.inj_iff.mp heq
  exact eq_of_heq hxy

/-- **Proposition 7 (b).** If two values v ≠ w of one attribute share a prime, K is not
injective. The other domains must be non-empty (the standing assumption of Section 3.1,
here `Nonempty (D j)`), so that a row through v exists. -/
theorem prop7_not_injective [∀ j, Nonempty (D j)] (p : (Σ i, D i) → ℕ) {i : ι}
    {v w : D i} (hvw : v ≠ w) (hshare : p ⟨i, v⟩ = p ⟨i, w⟩) :
    ¬ Function.Injective (primeKey p) := by
  intro hK
  let r : ∀ j, D j := fun j => Classical.arbitrary (D j)
  have hxy : Function.update r i v = Function.update r i w :=
    hK <| prod_congr rfl fun j _ => by
      by_cases hj : j = i
      · subst hj; simpa using hshare
      · simp [Function.update_of_ne hj]
  exact hvw (by simpa using congrFun hxy i)

/-- The non-emptiness in (b) is needed: with domains of sizes 2 and 0 and every pair
mapped to the prime 2, the two values of the first attribute share a prime, yet K is
injective because the product space is empty. -/
theorem prop7_not_injective_needs_nonempty :
    let m : Fin 2 → ℕ := ![2, 0]
    let p : (Σ i, Fin (m i)) → ℕ := fun _ => 2
    p ⟨0, (0 : Fin 2)⟩ = p ⟨0, (1 : Fin 2)⟩ ∧ (∀ s, (p s).Prime) ∧ Function.Injective (primeKey p) := by
  intro m p
  exact ⟨rfl, fun _ => Nat.prime_two, fun x _ _ => (x 1).elim0⟩

/-! ### Proposition 7 (c): the two examples of the paper -/

/-- Two attributes Aᵢ = attribute 0 and Aⱼ = attribute 1, with two values each. -/
abbrev Row2 := ∀ _ : Fin 2, Fin 2

/-- Primes 2, 3 for Aᵢ and 2, 5 for Aⱼ. -/
def pDistinct : (Σ _ : Fin 2, Fin 2) → ℕ := fun s => ![![2, 3], ![2, 5]] s.1 s.2

/-- Primes 2, 3 for Aᵢ and 2, 3 for Aⱼ. -/
def pShared : (Σ _ : Fin 2, Fin 2) → ℕ := fun s => ![![2, 3], ![2, 3]] s.1 s.2

/-- The row (α, β). -/
def row (α β : Fin 2) : Row2 := ![α, β]

lemma pDistinct_prime : ∀ s, (pDistinct s).Prime := by
  rintro ⟨i, v⟩; fin_cases i <;> fin_cases v <;> norm_num [pDistinct]

lemma pShared_prime : ∀ s, (pShared s).Prime := by
  rintro ⟨i, v⟩; fin_cases i <;> fin_cases v <;> norm_num [pShared]

/-- With primes 2, 3 and 2, 5, p is one-to-one within each attribute, the prime 2 is
shared across attributes, the four keys are 4, 10, 6, 15, and K is injective. -/
theorem prop7_shared_injective :
    (∀ i, Function.Injective (fun v => pDistinct ⟨i, v⟩)) ∧
      pDistinct ⟨0, 0⟩ = pDistinct ⟨1, 0⟩ ∧
      [primeKey pDistinct (row 0 0), primeKey pDistinct (row 0 1),
        primeKey pDistinct (row 1 0), primeKey pDistinct (row 1 1)] = [4, 10, 6, 15] ∧
      Function.Injective (primeKey pDistinct) := by
  decide

/-- With primes 2, 3 and 2, 3, p is one-to-one within each attribute, and the rows
(v, b) = (0, 1) and (a, w) = (1, 0) both get the key 6, so K is not injective. -/
theorem prop7_shared_not_injective :
    (∀ i, Function.Injective (fun v => pShared ⟨i, v⟩)) ∧
      primeKey pShared (row 0 1) = 6 ∧ primeKey pShared (row 1 0) = 6 ∧
      ¬ Function.Injective (primeKey pShared) := by
  decide

/-- **Proposition 7 (c).** When p is prime-valued and one-to-one within each attribute,
and values of different attributes share a prime, K may be injective and may fail to
be. -/
theorem prop7_may_or_may_not :
    (∃ p : (Σ _ : Fin 2, Fin 2) → ℕ, (∀ s, (p s).Prime) ∧
        (∀ i, Function.Injective (fun v => p ⟨i, v⟩)) ∧
        (∃ s t, s.1 ≠ t.1 ∧ p s = p t) ∧ Function.Injective (primeKey p)) ∧
      (∃ p : (Σ _ : Fin 2, Fin 2) → ℕ, (∀ s, (p s).Prime) ∧
        (∀ i, Function.Injective (fun v => p ⟨i, v⟩)) ∧
        (∃ s t, s.1 ≠ t.1 ∧ p s = p t) ∧ ¬ Function.Injective (primeKey p)) := by
  obtain ⟨h1, h2, -, h4⟩ := prop7_shared_injective
  obtain ⟨g1, -, -, g4⟩ := prop7_shared_not_injective
  exact ⟨⟨pDistinct, pDistinct_prime, h1, ⟨⟨0, 0⟩, ⟨1, 0⟩, by decide, h2⟩, h4⟩,
    ⟨pShared, pShared_prime, g1, ⟨⟨0, 0⟩, ⟨1, 0⟩, by decide, by decide⟩, g4⟩⟩

end Latc
