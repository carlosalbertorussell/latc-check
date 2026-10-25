import LatcFormal.Prop2
import LatcFormal.Examples

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
