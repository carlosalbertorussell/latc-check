import unittest

from latc_check import datasets, tree
from latc_check.checks import structural_report
from latc_check.dmn import ANY, DMNTable, OneOf, Point, Rule, analyse, to_exact, violations
from latc_check.model import DecisionTable, Row, attrs


def _xor():
    t = DecisionTable(attrs([("a", "01"), ("b", "01"), ("c", "xyz")]), [], outcomes=("T", "F"))
    return t.with_rows([Row(c, "T" if c[0] != c[1] else "F") for c in t.full_space()])


class ID3(unittest.TestCase):
    def check_exact(self, t, merge):
        root = tree.id3(t)
        d = tree.to_dmn(root, t, merge_siblings=merge)
        a = analyse(d)
        self.assertEqual(a.gaps, [])
        self.assertEqual(a.overlaps, {})
        self.assertEqual(violations(d, a)["violating_pairs"], [])
        ex, _ = to_exact(d)
        self.assertEqual({r.condition: r.outcome for r in ex.rows}, {r.condition: r.outcome for r in t.rows})
        self.assertEqual(len(ex.rows), len(t.rows))
        for r in t.rows:
            self.assertEqual(tree.classify(root, r.condition), r.outcome)
        return d

    def test_xor_ignores_irrelevant_attribute(self):
        d = self.check_exact(_xor(), False)
        self.assertEqual(len(d.rules), 4)
        self.assertTrue(all(r.entries[2] is ANY for r in d.rules))

    def test_car_tree_reproduces_table(self):
        car = datasets.car()
        d = self.check_exact(car, False)
        self.assertLess(len(d.rules), len(car.rows))
        dm = self.check_exact(car, True)
        self.assertLess(len(dm.rules), len(d.rules))
        self.assertTrue(any(isinstance(e, OneOf) for r in dm.rules for e in r.entries))
        self.assertTrue(all(e is ANY or isinstance(e, (Point, OneOf)) for r in dm.rules for e in r.entries))

    def test_faults_detected(self):
        car = datasets.car()
        d = tree.to_dmn(tree.id3(car), car)
        dropped = DMNTable(d.inputs, d.rules[1:], d.hit_policy, d.output_name, d.output_values)
        self.assertTrue(analyse(dropped).gaps)
        self.assertGreater(structural_report(to_exact(dropped)[0])["uncovered"], 0)
        r0 = d.rules[0]
        k = max(i for i, e in enumerate(r0.entries) if e is not ANY)
        rules = list(d.rules)
        rules[0] = Rule(r0.entries[:k] + (ANY,) + r0.entries[k + 1:], r0.output)
        wide = DMNTable(d.inputs, rules, d.hit_policy, d.output_name, d.output_values)
        self.assertTrue(analyse(wide).overlaps)
        self.assertGreater(structural_report(to_exact(wide)[0])["multi_hit_tuples"], 0)


if __name__ == "__main__":
    unittest.main()
