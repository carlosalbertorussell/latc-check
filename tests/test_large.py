import os
import random
import tempfile
import unittest
from itertools import product

from latc_check import examples as ex
from latc_check import large
from latc_check.keying import Canonicalizer, canonical_bytes
from latc_check.model import UNKNOWN, Attribute, DecisionTable, attrs
from latc_check.rank import INVALID_CODE, RankIndex
from latc_check.reference import complete, exact_complement


class Rank(unittest.TestCase):
    def test_rank_is_enumeration_order(self):
        at = attrs([("a", "xyz"), ("b", "pq"), ("c", "uvwt")])
        ri = RankIndex(at)
        for i, cond in enumerate(product(*(a.domain for a in at))):
            self.assertEqual(ri.rank(cond), i)
            self.assertEqual(ri.unrank(i), cond)
        self.assertEqual(ri.size, 24)

    def test_out_of_domain_has_no_rank(self):
        ri = RankIndex(attrs([("a", "xy"), ("b", "pq")]))
        self.assertIsNone(ri.rank(("x", "z")))
        self.assertIsNone(ri.rank(("x",)))
        self.assertIsNone(ri.lookup(("z", "p")))

    def test_pension_table_round_trip(self):
        t = ex.pension_completed()
        ri = RankIndex.from_table(t)
        self.assertEqual(len(ri.codes), 24)
        for r in t.rows:
            self.assertEqual(ri.lookup(r.condition), r.outcome)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "pension.codes")
            ri.save(path)
            self.assertEqual(os.path.getsize(path), 24)
            back = RankIndex.load(path)
        self.assertEqual(back.codes, ri.codes)
        self.assertEqual(back.lookup(t.rows[5].condition), t.rows[5].outcome)

    def test_partial_table_and_constraint(self):
        t = DecisionTable(attrs([("X", "ab"), ("Y", "pq")]), constraint=lambda c: c != ("a", "q"))
        ri = RankIndex.from_table(complete(t))
        self.assertEqual(ri.lookup(("a", "p")), UNKNOWN)
        self.assertEqual(ri.codes[ri.rank(("a", "q"))], INVALID_CODE)
        self.assertEqual(ri.lookup(("a", "q")), "INVALID")

    def test_repeated_rows_rejected(self):
        t = ex.pension_table()
        with self.assertRaises(ValueError):
            RankIndex.from_table(t.with_rows(t.rows + t.rows[:1]))


class Canon(unittest.TestCase):
    def test_cached_equals_generic(self):
        at = (Attribute("b", ("x", "é")), Attribute("a", (1, 2)), Attribute("Z", (True, None)))
        can = Canonicalizer(at)
        names = tuple(a.name for a in at)
        for cond in product(*(a.domain for a in at)):
            self.assertEqual(can(cond), canonical_bytes(names, cond))

    def test_out_of_domain_falls_back(self):
        at = attrs([("a", "xy")])
        self.assertEqual(Canonicalizer(at)(("q",)), canonical_bytes(("a",), ("q",)))


class Streaming(unittest.TestCase):
    def test_stream_equals_reference(self):
        t = ex.pension_table()
        self.assertEqual(list(large.stream_complement(t.attributes, set(t.conditions()))),
                         exact_complement(t))

    def test_rank_stream(self):
        rng = random.Random(1)
        t0 = rng.sample(range(500), 40)
        self.assertEqual(list(large.stream_complement_ranks(500, t0)),
                         [r for r in range(500) if r not in set(t0)])

    def test_run_shape_small(self):
        r = large.run_shape("test", 5, 3, t0_size=20, probes=500, log=lambda *_: None)
        self.assertEqual(r["missing_rows"], 243 - 20)
        self.assertEqual(r["rank_vs_dict_mismatches"], 0)
        self.assertEqual(r["sha512_vs_rank_mismatches"], 0)
        self.assertEqual(r["prime_vs_rank_mismatches"], 0)
        self.assertTrue(r["dmn_sparse_cover_ok"] and r["dmn_dense_cover_ok"])
        self.assertEqual(r["rank_disk_mib"] > 0, True)
        self.assertTrue(set(large.CSV_FIELDS) <= set(large.flat(r)))

    def test_hardware(self):
        hw = large.hardware()
        self.assertTrue(hw["python"])


if __name__ == "__main__":
    unittest.main()
