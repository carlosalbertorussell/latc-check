import random
import unittest
from itertools import product

from latc_check import latc, randomized
from latc_check.compare import compare
from latc_check.model import DecisionTable, Row, attrs
from latc_check.randomized import (AllOf, Exclusion, Implication, Ordinal, UndefinedWhen,
                                   draw_constraint, draw_structured_constraint,
                                   generate_structured_case)
from latc_check.reference import complete, exact_complement


class ConstraintForms(unittest.TestCase):
    def test_each_form_on_hand_built_tuples(self):
        imp = Implication(0, "a", 1, frozenset({"p"}))
        self.assertFalse(imp(("a", "p")))
        self.assertTrue(imp(("a", "q")))
        self.assertTrue(imp(("b", "p")))
        exc = Exclusion(0, "a", 1, "q")
        self.assertFalse(exc(("a", "q")))
        self.assertTrue(exc(("a", "p")))
        orda = Ordinal(0, frozenset({"hi"}), 1, frozenset({"lo"}))
        self.assertFalse(orda(("hi", "lo")))
        self.assertTrue(orda(("hi", "mid")))
        self.assertTrue(orda(("lo", "lo")))
        und = UndefinedWhen(0, "none", 1, "n/a")
        self.assertTrue(und(("none", "n/a")))
        self.assertFalse(und(("none", "x")))
        self.assertFalse(und(("some", "n/a")))
        self.assertTrue(und(("some", "x")))
        both = AllOf((exc, imp))
        self.assertEqual([c for c in product("ab", "pq") if both(c)], [("b", "p"), ("b", "q")])

    def test_drawn_constraints_are_well_formed(self):
        rng = random.Random(3)
        for _ in range(500):
            attributes = randomized._domains(rng, 48)
            c = draw_constraint(rng, attributes)
            self.assertIn(c.kind, randomized.CONSTRAINT_KINDS)
            self.assertNotEqual(c.i, c.j)
            di, dj = attributes[c.i].domain, attributes[c.j].domain
            if isinstance(c, Implication):
                self.assertIn(c.v, di)
                self.assertTrue(c.banned and c.banned < set(dj))
            elif isinstance(c, Exclusion):
                self.assertIn(c.v, di)
                self.assertIn(c.w, dj)
            elif isinstance(c, Ordinal):
                self.assertEqual(c.top, set(di[len(di) - len(c.top):]))     # top of declared order
                self.assertEqual(c.bottom, set(dj[:len(c.bottom)]))         # bottom of declared order
                self.assertTrue(0 < len(c.top) < len(di) and 0 < len(c.bottom) < len(dj))
            else:
                self.assertIsInstance(c, UndefinedWhen)
                self.assertIn(c.v, di)
                self.assertEqual(c.na, dj[-1])
            space = list(product(*(a.domain for a in attributes)))
            # every single constraint is a total predicate that removes something
            self.assertTrue(all(isinstance(c(t), bool) for t in space))
            self.assertLess(sum(c(t) for t in space), len(space))

    def test_valid_space_has_at_least_two_states(self):
        rng = random.Random(4)
        for _ in range(300):
            attributes = randomized._domains(rng, 48)
            constraint, valid = draw_structured_constraint(rng, attributes)
            self.assertTrue(1 <= len(constraint.parts) <= 3)
            self.assertGreaterEqual(len(valid), 2)
            self.assertEqual(valid, [t for t in product(*(a.domain for a in attributes))
                                     if constraint(t)])

    def test_generated_cases(self):
        rng = random.Random(5)
        for _ in range(200):
            t = generate_structured_case(rng)
            valid = list(t.valid_space())
            self.assertGreaterEqual(len(valid), 2)
            self.assertTrue(all(t.is_valid(r.condition) for r in t.rows))
            self.assertTrue(1 <= len(t.rows) < len(valid))
            self.assertEqual(len(set(t.conditions())), len(t.rows))
            for j in range(len(t.attributes)):     # every value occurring in V is observed
                self.assertEqual({c[j] for c in valid}, {c[j] for c in t.conditions()})

    def test_determinism_under_a_seed(self):
        def draw(seed):
            rng = random.Random(seed)
            out = []
            for _ in range(30):
                t = generate_structured_case(rng)
                out.append((t.attributes, t.rows, t.constraint, list(t.valid_space())))
            return out
        self.assertEqual(draw(11), draw(11))
        self.assertNotEqual(draw(11), draw(12))


class StructuredEndToEnd(unittest.TestCase):
    def test_complete_is_exact_on_structured_tables(self):
        rng = random.Random(20210101)
        for _ in range(25):
            t = generate_structured_case(rng)
            ref = exact_complement(t)
            self.assertTrue(compare(ref, t).exact)
            done = complete(t)
            self.assertEqual(set(done.conditions()), set(t.valid_space()))
            self.assertEqual(len(done.rows), t.valid_space_size())
            self.assertEqual(latc.deficit_check(ref, t, latc.valid_space_deficits(t)), [])

    def test_hand_built_table_reading_b_generates_invalid_rows(self):
        a = attrs([("Employed", ("yes", "no")), ("Employer", ("public", "private", "n/a"))])
        t = DecisionTable(a, [Row(("yes", "public"), "YES"), Row(("no", "n/a"), "NO")],
                          constraint=AllOf((UndefinedWhen(0, "no", 1, "n/a"),)))
        self.assertEqual(exact_complement(t), [("yes", "private")])
        self.assertTrue(compare(exact_complement(t), t).exact)
        odo = compare(latc.latc_odometer(t), t)
        self.assertFalse(odo.exact)
        self.assertEqual(odo.outside_space, 2)     # ("yes", "n/a") and ("no", "public")

    def test_run_structured_summary_shape(self):
        out = randomized.run_structured(trials=20, seed=1)
        self.assertEqual(out["reference"]["exact_rate"], 1.0)
        self.assertEqual(out["reference"]["mean_outside_space"], 0)
        self.assertEqual(out["count_checks"]["complement_passes_valid_space_deficit_check"], 1.0)
        c = out["constraints"]
        self.assertTrue(0 < c["excluded_share_min"] <= c["excluded_share_mean"] <= c["excluded_share_max"] < 1)
        self.assertNotIn(randomized.STRUCTURED, randomized.SCENARIOS)


if __name__ == "__main__":
    unittest.main()
