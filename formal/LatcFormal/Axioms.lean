import LatcFormal.Prop2
import LatcFormal.Examples
import LatcFormal.Thm1
import LatcFormal.Prop1
import LatcFormal.Prop6
import LatcFormal.Prop7

/-!
# Axiom audit

Building this file prints the axioms each main theorem depends on. Each list should be a
subset of `propext`, `Classical.choice` and `Quot.sound` (Lean's standard axioms), with
no `sorryAx`.
-/

#print axioms Latc.prop2
#print axioms Latc.prop2_missed
#print axioms Latc.prop2_extra
#print axioms Latc.prop2_missed_iff
#print axioms Latc.prop3
#print axioms Latc.prop4_necessity
#print axioms Latc.prop4_insufficiency
#print axioms Latc.prop4_insufficiency_needs_an_attribute
#print axioms Latc.check_membership_sufficient
#print axioms Latc.check_wrong_output_cases
#print axioms Latc.Examples.prop4_counterexample
#print axioms Latc.Examples.twins_same_profile
#print axioms Latc.Examples.complete_pair

-- Theorem 1 and Corollaries 1, 3 and 4
#print axioms Latc.thm1
#print axioms Latc.thm1_noConstraint
#print axioms Latc.thm1_remark
#print axioms Latc.validSpace_isProduct_of_noConstraint
#print axioms Latc.cor1
#print axioms Latc.obsProduct_eq_validSpace_of_all_observed
#print axioms Latc.cor3
#print axioms Latc.cor4

-- Proposition 1
#print axioms Latc.prop1
#print axioms Latc.prop1_condSets
#print axioms Latc.prop1_exists
#print axioms Latc.prop1_exists_full
#print axioms Latc.prop1_exists_full_needs_nonempty
#print axioms Latc.prop1_procedure
#print axioms Latc.evenParity_space
#print axioms Latc.evenParity_profile_determines
#print axioms Latc.evenParity_no_zeroMarginVector

-- Proposition 6
#print axioms Latc.rankFin_bijective
#print axioms Latc.prop6
#print axioms Latc.prop6_existsUnique
#print axioms Latc.prop6_empty_domain

-- Proposition 7
#print axioms Latc.prop7_injective
#print axioms Latc.prop7_not_injective
#print axioms Latc.prop7_not_injective_needs_nonempty
#print axioms Latc.prop7_shared_injective
#print axioms Latc.prop7_shared_not_injective
#print axioms Latc.prop7_may_or_may_not
