import random
import unittest

from latc_check import examples as ex
from latc_check import latc, randomized
from latc_check.checks import summed_frequency_check
from latc_check.compare import best_block_order, compare, count_marginal_solutions
from latc_check.model import DecisionTable, Row, attrs
from latc_check.reference import complete, exact_complement


class PensionExample(unittest.TestCase):
    def setUp(self):
        self.t = ex.pension_table()

    def test_source_counts_reproduced(self):
        self.assertEqual(latc.product_of_cards(self.t), 24)
        self.assertEqual(latc.missing_count(self.t), 16)
        self.assertEqual(latc.frequency_table(self.t), [
            {"M": 4, "F": 4}, {"D": 3, "I": 5}, {">=30": 5, "<30": 3},
            {">=65": 3, "60-64": 4, "<60": 1}])
        # Values printed in the source's "Table of Contents of Cp".
        self.assertEqual(latc.deficits(self.t), [
            {"M": 8, "F": 8}, {"D": 9, "I": 7}, {">=30": 7, "<30": 9},
            {">=65": 5, "60-64": 4, "<60": 7}])

    def test_reference(self):
        ref = exact_complement(self.t)
        self.assertEqual(len(ref), 16)
        self.assertEqual(len(complete(self.t).rows), 24)
        self.assertFalse(set(ref) & set(self.t.conditions()))

    def test_published_table_is_exact_complement(self):
        pub = [c for _, c, _ in ex.PENSION_PUBLISHED_COMPLEMENT]
        self.assertEqual(set(pub), set(exact_complement(self.t)))
        self.assertEqual(len(pub), 16)
        self.assertEqual(latc.deficit_check(pub, self.t), [])

    def test_reading_a_is_wrong(self):
        r = compare(latc.deficit_fill(self.t), self.t)
        self.assertFalse(r.exact)
        self.assertGreater(r.missed, 0)
        self.assertGreater(r.regenerated_t0, 0)
        # ... yet its marginals match the deficits and the source's own
        # summed-frequency completeness check passes.
        self.assertEqual(latc.deficit_check(latc.deficit_fill(self.t), self.t), [])
        merged = self.t.with_rows(self.t.rows + [Row(c) for c in latc.deficit_fill(self.t)])
        self.assertTrue(summed_frequency_check(merged))

    def test_no_block_order_rescues_reading_a(self):
        best, tried, any_exact = best_block_order(self.t)
        self.assertEqual(tried, 48)
        self.assertFalse(any_exact)

    def test_reading_b_is_exact(self):
        assembled, missing = latc.odometer_assembly(self.t)
        self.assertEqual(len(assembled), 24)
        self.assertEqual(len(set(assembled)), 24)
        self.assertTrue(compare(missing, self.t).exact)

    def test_deficits_do_not_determine_the_missing_set(self):
        n_any = count_marginal_solutions(list(self.t.full_space()), latc.deficits(self.t))
        free = [c for c in self.t.full_space() if c not in set(self.t.conditions())]
        n_disjoint = count_marginal_solutions(free, latc.deficits(self.t))
        self.assertGreater(n_any, 1)
        self.assertEqual(n_disjoint, 1)


class Counterexample(unittest.TestCase):
    def test_naive_fill_regenerates_t0(self):
        t = ex.counterexample_table()
        filled = latc.deficit_fill(t)
        self.assertEqual(sorted(filled), sorted(t.conditions()))
        self.assertEqual(set(exact_complement(t)), {("M", "I"), ("F", "D")})
        r = compare(filled, t)
        self.assertEqual((r.missed, r.regenerated_t0, r.exact), (2, 2, False))

    def test_twins_share_frequency_table_but_not_complement(self):
        a, b = ex.counterexample_table(), ex.counterexample_twin()
        self.assertEqual(latc.frequency_table(a), latc.frequency_table(b))  # same counts
        self.assertFalse(set(exact_complement(a)) & set(exact_complement(b)))
        # With a fixed block order the fill is identical for both, so at most
        # one of them can be right:
        order = [("M", "F"), ("D", "I")]
        self.assertEqual(latc.deficit_fill(a, order), latc.deficit_fill(b, order))
        self.assertFalse(compare(latc.deficit_fill(a, order), a).exact
                         and compare(latc.deficit_fill(b, order), b).exact)
        # With first-appearance order (the default) each regenerates its own T0.
        for t in (a, b):
            self.assertEqual(compare(latc.deficit_fill(t), t).regenerated_t0, 2)


class AssumptionBoundaries(unittest.TestCase):
    def test_unobserved_value_is_invisible_to_latc(self):
        t = DecisionTable(attrs([("X", "ab"), ("Y", "pqr")]), [Row(("a", "p")), Row(("b", "q"))])
        self.assertEqual(latc.missing_count(t), 2)        # LATC sees 2x2
        self.assertEqual(len(exact_complement(t)), 4)      # true space is 2x3
        self.assertEqual(compare(latc.latc_odometer(t), t).missed, 2)

    def test_constraint_breaks_corollary3(self):
        t = DecisionTable(attrs([("X", "ab"), ("Y", "pq")]), [Row(("a", "p")), Row(("b", "q"))],
                          constraint=lambda c: c != ("a", "q"))
        self.assertEqual(latc.missing_count(t), 2)
        self.assertEqual(exact_complement(t), [("b", "p")])
        self.assertEqual(compare(latc.latc_odometer(t), t).outside_space, 1)
        ref = exact_complement(t)
        self.assertTrue(latc.deficit_check(ref, t))                                   # [12] wrong here
        self.assertEqual(latc.deficit_check(ref, t, latc.valid_space_deficits(t)), [])  # generalised OK

    def test_duplicate_rows_in_t0(self):
        t = DecisionTable(attrs([("X", "ab"), ("Y", "pq")]),
                          [Row(("a", "p"), "YES"), Row(("a", "p"), "NO")])
        self.assertEqual(latc.missing_count(t), -1)   # 1x1 observed space minus 2 rows
        self.assertEqual(latc.deficit_fill(t), [])


class RandomisedProperties(unittest.TestCase):
    def test_reference_and_odometer_properties(self):
        rng = random.Random(7)
        for _ in range(300):
            t = randomized.generate_case(rng, "observed")
            ref = exact_complement(t)
            self.assertTrue(compare(ref, t).exact)
            self.assertEqual(len(ref) + len(t.rows), t.valid_space_size())
            self.assertTrue(compare(latc.latc_odometer(t), t).exact)
            self.assertEqual(latc.missing_count(t), len(ref))
            self.assertEqual(latc.deficit_check(ref, t), [])
            # Reading A always matches the marginals, right or wrong
            self.assertEqual(latc.deficit_check(latc.deficit_fill(t), t), [])

    def test_reference_exact_under_all_scenarios(self):
        rng = random.Random(8)
        for scenario in randomized.SCENARIOS:
            for _ in range(100):
                t = randomized.generate_case(rng, scenario)
                self.assertTrue(compare(exact_complement(t), t).exact)
                self.assertEqual(latc.deficit_check(exact_complement(t), t,
                                                    latc.valid_space_deficits(t)), [])

    def test_generator_profile_replays_run(self):
        p = randomized.generator_profile(trials=30, seed=3, baseline_draws=200)
        rng = random.Random(3)
        shares = []
        for _ in range(30):
            t = randomized.generate_case(rng, "observed")
            shares.append(len(t.rows) / t.valid_space_size())
        self.assertAlmostEqual(p["observed"]["mean_t0_share_of_valid_space"], sum(shares) / 30)
        c = p["constrained"]
        self.assertLess(c["mean_valid_space_size"], c["mean_product_size"])
        self.assertEqual(p["without_redraw"]["mean_t0_share_of_valid_space"], 0.5)

    def test_run_summary_shape(self):
        out = randomized.run(trials=20, seed=1)
        self.assertEqual(out["observed"]["reference"]["exact_rate"], 1.0)
        self.assertEqual(out["observed"]["latc_B_odometer"]["exact_rate"], 1.0)
        self.assertLess(out["observed"]["latc_A_deficit_fill"]["exact_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
