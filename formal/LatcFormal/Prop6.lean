import LatcFormal.Basic

/-!
# Proposition 6 (Section 7; the mixed-radix rank, Appendix D)

Fix an order for each domain, write idxᵢ(v) for the position of v in Dᵢ, starting at 0,
and let rank(x) = ∑_{i=1..n} idxᵢ(xᵢ) · ∏_{j>i} |Dⱼ|. If every |Dᵢ| ≥ 1, rank is a
bijection from the product space onto {0, 1, …, |𝒟| − 1}.

Attributes are `Fin n`, so "j > i" is the order of `Fin n`. The order on Dᵢ is an
equivalence `e i : D i ≃ Fin |Dᵢ|`, and idxᵢ(v) = `e i v`. The core statement is about
digit vectors `f : ∀ i, Fin (m i)` with radices `m : Fin n → ℕ`; the first attribute is
the most significant digit.

The hypothesis |Dᵢ| ≥ 1 is not used: if some domain is empty, 𝒟 is empty and
{0, …, |𝒟| − 1} is empty too, so rank is the empty bijection.
-/

namespace Latc

open Finset

/-- rank(f) = ∑ᵢ fᵢ · ∏_{j>i} mⱼ, on digit vectors. -/
def rankFin {n : ℕ} (m : Fin n → ℕ) (f : ∀ i, Fin (m i)) : ℕ :=
  ∑ i, (f i : ℕ) * ∏ j ∈ univ.filter (fun j => i < j), m j

/-- Peeling off the first digit: rank(f) = f₀ · ∏_{j>0} mⱼ + rank(tail f). -/
lemma rankFin_succ {n : ℕ} (m : Fin (n + 1) → ℕ) (f : ∀ i, Fin (m i)) :
    rankFin m f = (f 0 : ℕ) * ∏ j : Fin n, m j.succ +
      rankFin (fun j => m j.succ) (fun j => f j.succ) := by
  unfold rankFin
  rw [Fin.sum_univ_succ]
  congr 1
  · congr 1
    rw [prod_filter, Fin.prod_univ_succ]
    simp [Fin.succ_pos]
  · refine sum_congr rfl fun i _ => ?_
    congr 1
    rw [prod_filter, prod_filter, Fin.prod_univ_succ]
    simp [Fin.succ_lt_succ_iff]

/-- rank(f) < ∏ᵢ mᵢ. -/
lemma rankFin_lt {n : ℕ} (m : Fin n → ℕ) (f : ∀ i, Fin (m i)) :
    rankFin m f < ∏ i, m i := by
  induction n with
  | zero => simp [rankFin]
  | succ n ih =>
    rw [rankFin_succ, Fin.prod_univ_succ]
    have h1 := ih (fun j => m j.succ) (fun j => f j.succ)
    have h2 : (f 0 : ℕ) + 1 ≤ m 0 := (f 0).isLt
    calc (f 0 : ℕ) * ∏ j : Fin n, m j.succ + rankFin (fun j => m j.succ) (fun j => f j.succ)
        < (f 0 : ℕ) * ∏ j : Fin n, m j.succ + ∏ j : Fin n, m j.succ := by omega
      _ = ((f 0 : ℕ) + 1) * ∏ j : Fin n, m j.succ := by ring
      _ ≤ m 0 * ∏ j : Fin n, m j.succ := Nat.mul_le_mul_right _ h2

/-- rank is injective on digit vectors. -/
lemma rankFin_injective {n : ℕ} (m : Fin n → ℕ) : Function.Injective (rankFin m) := by
  induction n with
  | zero => intro f g _; funext i; exact i.elim0
  | succ n ih =>
    intro f g h
    rw [rankFin_succ, rankFin_succ] at h
    set Q := ∏ j : Fin n, m j.succ
    have hf := rankFin_lt (fun j => m j.succ) (fun j => f j.succ)
    have hg := rankFin_lt (fun j => m j.succ) (fun j => g j.succ)
    have hQ : 0 < Q := by omega
    have hdiv : (f 0 : ℕ) = g 0 := by
      have e : ∀ (a r : ℕ), r < Q → (a * Q + r) / Q = a := fun a r hr => by
        rw [Nat.add_comm, Nat.add_mul_div_right _ _ hQ, Nat.div_eq_of_lt hr, Nat.zero_add]
      rw [← e (f 0) _ hf, ← e (g 0) _ hg, h]
    have hmod : rankFin (fun j => m j.succ) (fun j => f j.succ) =
        rankFin (fun j => m j.succ) (fun j => g j.succ) := by
      rw [hdiv] at h; omega
    have htail := ih (fun j => m j.succ) hmod
    funext i
    refine Fin.cases ?_ (fun j => ?_) i
    · exact Fin.ext hdiv
    · exact congrFun htail j

/-- On digit vectors, rank is a bijection onto Fin (∏ᵢ mᵢ) = {0, …, ∏ᵢ mᵢ − 1}. -/
theorem rankFin_bijective {n : ℕ} (m : Fin n → ℕ) :
    Function.Bijective (fun f : ∀ i, Fin (m i) => (⟨rankFin m f, rankFin_lt m f⟩ :
      Fin (∏ i, m i))) := by
  rw [Fintype.bijective_iff_injective_and_card]
  refine ⟨fun f g h => rankFin_injective m (Fin.mk.inj_iff.mp h), ?_⟩
  simp

variable {n : ℕ} {D : Fin n → Type*} [∀ i, Fintype (D i)]

/-- rank(x) = ∑ᵢ idxᵢ(xᵢ) · ∏_{j>i} |Dⱼ|, for the orders `e i : D i ≃ Fin |Dᵢ|`. -/
def rank (e : ∀ i, D i ≃ Fin (Fintype.card (D i))) (x : ∀ i, D i) : ℕ :=
  ∑ i, (e i (x i) : ℕ) * ∏ j ∈ univ.filter (fun j => i < j), Fintype.card (D j)

lemma rank_eq_rankFin (e : ∀ i, D i ≃ Fin (Fintype.card (D i))) (x : ∀ i, D i) :
    rank e x = rankFin (fun i => Fintype.card (D i)) (fun i => e i (x i)) := rfl

lemma rank_lt (e : ∀ i, D i ≃ Fin (Fintype.card (D i))) (x : ∀ i, D i) :
    rank e x < Fintype.card (∀ i, D i) := by
  rw [Fintype.card_pi]
  exact rankFin_lt _ _

/-- **Proposition 6.** rank is a bijection from the product space 𝒟 onto
{0, 1, …, |𝒟| − 1}, here `Fin |𝒟|`. No hypothesis |Dᵢ| ≥ 1 is needed. -/
theorem prop6 (e : ∀ i, D i ≃ Fin (Fintype.card (D i))) :
    Function.Bijective (fun x : ∀ i, D i =>
      (⟨rank e x, rank_lt e x⟩ : Fin (Fintype.card (∀ i, D i)))) := by
  rw [Fintype.bijective_iff_injective_and_card]
  refine ⟨fun x y h => ?_, by simp⟩
  have h' : rank e x = rank e y := Fin.mk.inj_iff.mp h
  rw [rank_eq_rankFin, rank_eq_rankFin] at h'
  have := rankFin_injective _ h'
  funext i
  exact (e i).injective (congrFun this i)

/-- Proposition 6, stated with natural numbers: every r < |𝒟| is the rank of exactly one
tuple. -/
theorem prop6_existsUnique (e : ∀ i, D i ≃ Fin (Fintype.card (D i))) (r : ℕ)
    (hr : r < Fintype.card (∀ i, D i)) : ∃! x : ∀ i, D i, rank e x = r := by
  obtain ⟨x, hx⟩ := (prop6 e).2 ⟨r, hr⟩
  refine ⟨x, Fin.mk.inj_iff.mp hx, fun y hy => (prop6 e).1 ?_⟩
  exact Fin.ext (hy.trans (Fin.mk.inj_iff.mp hx).symm)

/-- A check of the formula: with radices 2, 3, 4, the digits (1, 2, 3) have rank
1 · 12 + 2 · 4 + 3 = 23 = 2 · 3 · 4 − 1, the last position. -/
example : rankFin ![2, 3, 4] (fun i => match i with
    | 0 => (1 : Fin 2) | 1 => (2 : Fin 3) | 2 => (3 : Fin 4)) = 23 := by
  decide

/-- The hypothesis |Dᵢ| ≥ 1 can be dropped: with radices 2 and 0 the product space has no
tuple and {0, …, |𝒟| − 1} has no element, and `prop6` still applies. -/
theorem prop6_empty_domain : Fintype.card (∀ i : Fin 2, Fin (![2, 0] i)) = 0 := by decide

end Latc
