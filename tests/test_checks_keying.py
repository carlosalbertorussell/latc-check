import unittest
from itertools import product

from latc_check import bench
from latc_check import examples as ex
from latc_check.checks import Evaluator, is_sound, structural_report
from latc_check.keying import (DigestIndex, PrimeKeyer, UnverifiedDigestIndex,
                               canonical_bytes, naive_join_key)
from latc_check.model import OUT_OF_RANGE, UNKNOWN, DecisionTable, Row, attrs
from latc_check.reference import complete

BACKENDS = ("dict", "sha512", "prime")


class Structural(unittest.TestCase):
    def test_completed_pension_is_sound(self):
        rep = structural_report(ex.pension_completed())
        self.assertTrue(is_sound(rep))
        self.assertEqual((rep["rows"], rep["coverage"], rep["unknown_outcomes"]), (24, 1.0, 0))

    def test_t0_alone_is_incomplete(self):
        rep = structural_report(ex.pension_table())
        self.assertAlmostEqual(rep["coverage"], 8 / 24)
        self.assertFalse(is_sound(rep))

    def test_reference_completion_has_unknowns_only_in_new_rows(self):
        rep = structural_report(complete(ex.pension_table()))
        self.assertTrue(is_sound(rep))
        self.assertEqual(rep["unknown_outcomes"], 16)

    def test_conflict_and_multi_hit_detected(self):
        t = ex.pension_completed()
        t = t.with_rows(t.rows + [Row(t.rows[0].condition, "NO")])
        rep = structural_report(t)
        self.assertEqual((rep["multi_hit_tuples"], rep["conflicting_tuples"]), (1, 1))
        self.assertFalse(is_sound(rep))
        with self.assertRaises(ValueError):
            Evaluator(t)

    def test_unique_keys_do_not_imply_consistent_outcomes(self):
        # Two rows that the experts consider the same case, different outcomes,
        # but distinct condition tuples: every key is unique, the table is
        # single-hit, and nothing structural flags the semantic inconsistency.
        t = ex.pension_completed()
        rep = structural_report(t)
        self.assertTrue(rep["single_hit"])
        pk = PrimeKeyer.distinct(t.attributes)
        self.assertEqual(len({pk.key(r.condition) for r in t.rows}), 24)
        same_case = [r for r in t.rows if r.condition[1:] == ("I", "<30", ">=65")]
        self.assertEqual({r.outcome for r in same_case}, {"Rv"})  # M and F rows
        # whether 'Rv' for both sexes is *right* is an expert question.


class Evaluation(unittest.TestCase):
    def setUp(self):
        self.t = ex.pension_completed()

    def test_backends_agree_on_whole_space(self):
        evs = [Evaluator(self.t, b, ex.PENSION_BINNERS) for b in BACKENDS]
        for i, r in enumerate(self.t.rows):
            inp = dict(zip(self.t.names, r.condition))
            inp["Age"] = {">=65": 70, "60-64": 62, "<60": 40}[inp["Age"]]
            inp["ContributionYears"] = {">=30": 35, "<30": 10}[inp["ContributionYears"]]
            for ev in evs:
                d = ev.evaluate(inp)
                self.assertEqual((d.outcome, d.row), (r.outcome, i))

    def test_out_of_domain_goes_to_referral(self):
        bad = [
            {"Sex": "X", "Activity": "D", "ContributionYears": 35, "Age": 70},
            {"Sex": "M", "Activity": "D", "ContributionYears": 35, "Age": 130},
            {"Sex": "M", "Activity": "D", "ContributionYears": -1, "Age": 70},
            {"Sex": "M", "Activity": "D", "ContributionYears": 35},
            {"Sex": "M", "Activity": "D", "ContributionYears": 35, "Age": 70, "Extra": 1},
            {"Sex": "M", "Activity": "D", "ContributionYears": 35.5, "Age": 70},
            {"Sex": "M", "Activity": None, "ContributionYears": 35, "Age": 70},
        ]
        for b in BACKENDS:
            ev = Evaluator(self.t, b, ex.PENSION_BINNERS)
            for inp in bad:
                d = ev.evaluate(inp)
                self.assertEqual(d.outcome, OUT_OF_RANGE, (b, inp))
                self.assertIsNone(d.row)

    def test_invalid_state_goes_to_referral(self):
        t = DecisionTable(attrs([("X", "ab"), ("Y", "pq")]),
                          constraint=lambda c: c != ("a", "q"))
        t = complete(t)
        for b in BACKENDS:
            self.assertEqual(Evaluator(t, b).evaluate({"X": "a", "Y": "q"}).outcome, OUT_OF_RANGE)
            self.assertEqual(Evaluator(t, b).evaluate({"X": "a", "Y": "p"}).outcome, UNKNOWN)


class Keying(unittest.TestCase):
    def test_canonical_bytes(self):
        self.assertEqual(canonical_bytes(("b", "a"), ("x", 1)), b'{"a":1,"b":"x"}')
        self.assertEqual(canonical_bytes(("a", "b"), (1, "x")), canonical_bytes(("b", "a"), ("x", 1)))
        self.assertEqual(canonical_bytes(("a",), ("é\n",)), '{"a":"é\\n"}'.encode())
        with self.assertRaises(TypeError):
            canonical_bytes(("a",), (1.5,))
        with self.assertRaises(ValueError):
            canonical_bytes(("a",), (2 ** 60,))

    def test_canonical_bytes_injective_where_naive_join_is_not(self):
        names = ("p", "q")
        a, b = ("a;b", "c"), ("a", "b;c")
        self.assertEqual(naive_join_key(a), naive_join_key(b))
        self.assertNotEqual(canonical_bytes(names, a), canonical_bytes(names, b))

    def test_distinct_primes_are_injective(self):
        t = ex.pension_table()
        pk = PrimeKeyer.distinct(t.attributes)
        self.assertTrue(pk.is_one_to_one())
        keys = [pk.key(c) for c in t.full_space()]
        self.assertEqual(len(set(keys)), 24)
        self.assertIsNone(pk.key(("M", "D", ">=30", "70")))

    def test_ambiguous_prime_assignment_collides(self):
        at = attrs([("X", ("yes", "no")), ("Y", ("yes", "no"))])
        pk = PrimeKeyer.ambiguous_prime_assignment(at)
        self.assertFalse(pk.is_one_to_one())
        self.assertEqual(pk.key(("yes", "no")), pk.key(("no", "yes")))  # 2*3 == 3*2
        keys = [pk.key(c) for c in product(*(a.domain for a in at))]
        self.assertLess(len(set(keys)), len(keys))
        t = complete(DecisionTable(at))
        with self.assertRaises(ValueError):
            Evaluator(t, "prime", prime_keyer=pk)

    def test_overflow_report(self):
        at = attrs([(f"A{i}", tuple(range(8))) for i in range(10)])
        rep = PrimeKeyer.distinct(at).overflow_report()
        self.assertFalse(rep["fits_int64"])
        self.assertGreater(rep["max_key_bits"], 64)

    def test_digest_index_verifies_full_tuple(self):
        truncated = lambda b: __import__("hashlib").sha512(b).digest()[:1]  # 256 buckets
        at = attrs([(f"A{i}", tuple(range(4))) for i in range(5)])          # 1024 rows
        names = tuple(a.name for a in at)
        conds = list(product(*(a.domain for a in at)))
        verified = DigestIndex(names, truncated)
        naive = UnverifiedDigestIndex(names, truncated)
        for i, c in enumerate(conds):
            verified.add(c, i)
            naive.add(c, i)
        self.assertGreater(verified.collisions, 0)
        self.assertTrue(all(verified.lookup(c) == i for i, c in enumerate(conds)))
        wrong = sum(naive.lookup(c) != i for i, c in enumerate(conds))
        self.assertGreater(wrong, 0)  # digest-only lookup returns other rows
        self.assertIsNone(verified.lookup((9, 9, 9, 9, 9)))

    def test_digest_index_rejects_duplicates(self):
        idx = DigestIndex(("a",))
        idx.add(("x",), 0)
        with self.assertRaises(KeyError):
            idx.add(("x",), 1)


class Bench(unittest.TestCase):
    def test_bench_one(self):
        r = bench.bench_one(3, 3, probes=50)
        self.assertEqual(r["rows"], 27)
        self.assertTrue(set(bench.FIELDS) <= set(r))


if __name__ == "__main__":
    unittest.main()
