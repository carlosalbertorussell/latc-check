import itertools
import math
import random
import unittest
from fractions import Fraction

from latc_check import trap_frequency as tf


def brute_with_replacement(probs, k):
    """(P(trap), E[missing]) over every ordered k-sequence of i.i.d. states."""
    domains = [len(p) for p in probs]
    n_states = math.prod(domains)
    states = list(itertools.product(*(range(d) for d in domains)))
    weight = {s: math.prod((p[v] for p, v in zip(probs, s)), start=Fraction(1)) for s in states}
    trap = miss = Fraction(0)
    for seq in itertools.product(states, repeat=k):
        w = math.prod((weight[s] for s in seq), start=Fraction(1))
        obs = math.prod(len({s[i] for s in seq}) for i in range(len(domains)))
        trap += w * (obs < n_states)
        miss += w * (n_states - obs)
    return trap, miss


class Exact(unittest.TestCase):
    def test_equals_brute_force(self):
        for domains in ([2, 2], [3, 4], [2, 3], [2, 2, 3], [2, 3, 4]):
            n = math.prod(domains)
            for k in range(1, n + 1):
                if math.comb(n, k) > 50000:
                    continue
                bp, bm = tf.brute_force(domains, k)
                self.assertEqual(tf.p_trap_exact(domains, k), bp, (domains, k))
                self.assertEqual(tf.expected_missing_exact(domains, k), bm, (domains, k))

    def test_edge_values(self):
        d = [2, 2, 2, 3]
        self.assertEqual(tf.p_trap_exact(d, 2), 1)          # fewer rows than the largest domain
        self.assertEqual(tf.p_trap_exact(d, 17), 0)         # > 24 - 24/3 rows: every value seen
        self.assertEqual(tf.p_trap_exact(d, 24), 0)
        self.assertGreater(tf.p_trap_exact(d, 16), 0)
        self.assertEqual(tf.p_trap_exact([5], 4), 1)
        self.assertEqual(tf.p_trap_exact([5], 5), 0)

    def test_conditional_missing_is_one_value_when_k_large(self):
        # for large k a trap almost surely misses exactly one value of a 4-valued attribute: 1728/4 states
        d = [4, 4, 4, 3, 3, 3]
        k = 200
        cond = tf.expected_missing_exact(d, k) / tf.p_trap_exact(d, k)
        self.assertAlmostEqual(float(cond), 1728 / 4, delta=1)

    def test_grouping_does_not_depend_on_order(self):
        a = tf.p_trap_exact([3, 5, 4, 4, 3, 2, 3, 3], 20)
        b = tf.p_trap_exact([2, 3, 3, 3, 3, 4, 4, 5], 20)
        self.assertEqual(a, b)

    def test_monotone_in_k(self):
        d = [4, 4, 4, 3, 3, 3]
        ps = [tf.p_trap_exact(d, k) for k in range(1, 60)]
        self.assertTrue(all(x >= y for x, y in zip(ps, ps[1:])))


class WithReplacement(unittest.TestCase):
    def test_uniform_and_zipf_equal_enumeration(self):
        for probs in (tf.uniform_probs([2, 3]), tf.zipf_probs([2, 3])):
            for k in (1, 2, 3, 4):
                bp, bm = brute_with_replacement(probs, k)
                self.assertEqual(tf.p_trap_with_replacement(probs, k), bp)
                self.assertEqual(tf.expected_missing_with_replacement(probs, k), bm)

    def test_close_to_exact_when_k_small_relative_to_space(self):
        d = [4] * 12
        for k in (17, 30):
            ex = float(tf.p_trap_exact(d, k))
            wr = float(tf.p_trap_with_replacement(tf.uniform_probs(d), k))
            self.assertAlmostEqual(ex, wr, delta=1e-4)


class Bounds(unittest.TestCase):
    def test_union_bound_and_rule_of_thumb(self):
        for d in ([2, 2, 2, 3], [4, 4, 4, 3, 3, 3], [3, 5, 4, 4, 3, 2, 3, 3]):
            for k in (5, 17, 30, 50):
                if k <= math.prod(d):
                    self.assertLessEqual(float(tf.p_trap_exact(d, k)), tf.union_bound(d, k) + 1e-12)
            for a in (0.05, 0.01):
                k = tf.rule_of_thumb_k(d, a)
                self.assertLessEqual(tf.union_bound(d, k), a)

    def test_smallest_k_matches_scan(self):
        d = [4, 4, 4, 3, 3, 3]
        got = tf.smallest_k(lambda k: tf.p_trap_exact(d, k) <= 0.05, 1, 1728)
        scan = next(k for k in range(1, 1729) if tf.p_trap_exact(d, k) <= 0.05)
        self.assertEqual(got, scan)
        self.assertIsNone(tf.smallest_k(lambda k: False, 1, 100))
        self.assertEqual(tf.smallest_k(lambda k: True, 1, 100), 1)

    def test_mc_thresholds(self):
        covers = list(range(1, 101))                     # 100 draws, cover times 1..100
        self.assertEqual(tf.mc_thresholds(covers, (0.05, 0.01)), {"0.05": 95, "0.01": 99})
        self.assertEqual(tf.mc_thresholds([1, None], (0.01,)), {"0.01": None})


class MonteCarlo(unittest.TestCase):
    def test_uniform_agrees_with_exact(self):
        d, ks = [4, 4, 4, 3, 3, 3], [10, 17]
        mc = tf.monte_carlo(tf.UniformSampler(d, random.Random(1)), d, ks, 4000)
        for k in ks:
            e = mc["per_k"][str(k)]
            self.assertLess(abs(e["p_trap"] - float(tf.p_trap_exact(d, k))), 4 * e["se"] + 1e-9)

    def test_zipf_agrees_with_replacement_formula(self):
        d, ks = [3, 4], [6, 10]
        mc = tf.monte_carlo(tf.ZipfSampler(d, random.Random(2), with_replacement=True), d, ks, 4000, cap=10 ** 6)
        for k in ks:
            e = mc["per_k"][str(k)]
            exact = float(tf.p_trap_with_replacement(tf.zipf_probs(d), k))
            self.assertLess(abs(e["p_trap"] - exact), 4 * e["se"] + 1e-9)

    def test_deterministic(self):
        d = [2, 2, 2, 3]
        a = tf.monte_carlo(tf.UniformSampler(d, random.Random("s")), d, [5, 8], 500)
        b = tf.monte_carlo(tf.UniformSampler(d, random.Random("s")), d, [5, 8], 500)
        self.assertEqual(a, b)

    def test_class_weighted_sampler_draws_distinct_table_rows(self):
        from latc_check import datasets
        car = datasets.car()
        s = tf.ClassWeightedSampler(car, random.Random(3))
        s.reset()
        rows = [s.next() for _ in range(300)]
        self.assertEqual(len(set(rows)), 300)
        index = [{v: j for j, v in enumerate(a.domain)} for a in car.attributes]
        table = {tuple(ix[v] for ix, v in zip(index, r.condition)) for r in car.rows}
        self.assertTrue(set(rows) <= table)
        s.reset()
        self.assertEqual(len({s.next() for _ in range(len(car.rows))}), len(car.rows))


class Stats(unittest.TestCase):
    def test_clopper_pearson(self):
        lo, hi = tf.clopper_pearson(1, 20)
        self.assertAlmostEqual(lo, 0.00127, places=4)
        self.assertAlmostEqual(hi, 0.2487, places=3)
        self.assertEqual(tf.clopper_pearson(0, 20)[0], 0.0)


class ZipfValueOrder(unittest.TestCase):
    def test_orders_assign_zipf_weights_by_rank(self):
        d = [2, 3]
        rev = [[1, 0], [2, 1, 0]]
        decl, r = tf.zipf_probs(d), tf.zipf_probs(d, orders=rev)
        self.assertEqual(tf.zipf_probs(d, orders=[[0, 1], [0, 1, 2]]), decl)
        self.assertEqual(r, [p[::-1] for p in decl])
        self.assertEqual(tf.zipf_probs(d, orders=[[0, 1], [2, 0, 1]])[1], [Fraction(3, 11), Fraction(2, 11), Fraction(6, 11)])
        for bad in ([[0, 1]], [[0, 0], [0, 1, 2]], [[0, 1], [0, 1, 3]]):
            with self.assertRaises(ValueError):
                tf.zipf_probs(d, orders=bad)

    def test_reversed_order_on_symmetric_space_same_result(self):
        d = [2, 2]
        rev = [[1, 0], [1, 0]]
        for k in (1, 2, 3, 4):
            self.assertEqual(tf.p_trap_with_replacement(tf.zipf_probs(d), k),
                             tf.p_trap_with_replacement(tf.zipf_probs(d, orders=rev), k))

    def test_trap_probability_order_invariant_on_asymmetric_space(self):
        # the order only relabels values inside an attribute: P(trap) and E[missing] are unchanged
        # (checked against full enumeration), while which value tends to be missed does change
        d = [2, 3]
        orders = [[[0, 1], [0, 1, 2]], [[1, 0], [2, 1, 0]], [[0, 1], [1, 2, 0]], [[1, 0], [0, 2, 1]]]
        for k in (1, 2, 3, 4):
            ref = brute_with_replacement(tf.zipf_probs(d), k)
            for o in orders:
                probs = tf.zipf_probs(d, orders=o)
                self.assertEqual(brute_with_replacement(probs, k), ref, (o, k))
                self.assertEqual(tf.p_trap_with_replacement(probs, k), ref[0])
        miss_v0 = lambda probs, k: (1 - probs[1][0]) ** k          # P(value 0 of attribute 2 never drawn)
        self.assertNotEqual(miss_v0(tf.zipf_probs(d), 4), miss_v0(tf.zipf_probs(d, orders=orders[1]), 4))

    def test_sampler_with_order_relabels_draw_for_draw(self):
        d, ks = [4, 3, 3], [5, 10, 20]
        rev = [[3, 2, 1, 0], [2, 1, 0], [2, 1, 0]]
        a = tf.ZipfSampler(d, random.Random(7))
        b = tf.ZipfSampler(d, random.Random(7), orders=rev)
        a.reset(); b.reset()
        for _ in range(30):
            x, y = a.next(), b.next()
            self.assertEqual(y, tuple(o[v] for o, v in zip(rev, x)))
        ma = tf.monte_carlo(tf.ZipfSampler(d, random.Random(8)), d, ks, 300)
        mb = tf.monte_carlo(tf.ZipfSampler(d, random.Random(8), orders=rev), d, ks, 300)
        self.assertEqual(ma, mb)
        with self.assertRaises(ValueError):
            tf.ZipfSampler(d, random.Random(1), orders=[[0, 1, 2, 3]])

    def test_value_orders_seeded_permutations(self):
        d = [4, 3, 5]
        vo = tf.value_orders(d, 5)
        self.assertEqual([l for l, _ in vo], ["declared", "reversed"] + [f"random_{i}" for i in range(5)])
        self.assertEqual(vo[0][1], [[0, 1, 2, 3], [0, 1, 2], [0, 1, 2, 3, 4]])
        self.assertEqual(vo[1][1], [[3, 2, 1, 0], [2, 1, 0], [4, 3, 2, 1, 0]])
        for _, o in vo:
            self.assertEqual([sorted(x) for x in o], vo[0][1])
        self.assertEqual(vo, tf.value_orders(d, 5))
        self.assertGreater(len({str(o) for _, o in vo}), 2)

    def test_sensitivity_sweep(self):
        d = [3, 2, 2]
        s = tf.zipf_order_sensitivity(d, ks=(4, 8), n_random=4, mc_draws=500, key="toy")
        self.assertTrue(s["exact_values_identical_across_orders"])
        self.assertEqual(set(s["per_order"]), {"declared", "reversed", "random_0", "random_1", "random_2", "random_3"})
        decl = s["per_order"]["declared"]
        self.assertEqual(decl["p_trap"]["8"], float(tf.p_trap_with_replacement(tf.zipf_probs(d), 8)))
        for stat in ("mean", "min", "max"):
            self.assertAlmostEqual(s["random_summary"]["p_trap"]["4"][stat], decl["p_trap"]["4"])
            self.assertEqual(s["random_summary"]["thresholds"]["0.01"][stat], decl["thresholds"]["0.01"])
        t = decl["thresholds"]["0.05"]
        probs = tf.zipf_probs(d)
        self.assertLessEqual(tf.p_trap_with_replacement(probs, t), Fraction(5, 100))
        self.assertGreater(tf.p_trap_with_replacement(probs, t - 1), Fraction(5, 100))
        self.assertEqual(s["mc_reversed"]["draws"], 500)


if __name__ == "__main__":
    unittest.main()
