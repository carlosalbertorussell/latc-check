import unittest

from latc_check import datasets, latc
from latc_check.datasets_report import restore_check, run_methods
from latc_check.model import Row
from latc_check.reference import exact_complement


class Loaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.car, cls.car_info = datasets.load("car")
        cls.nursery, cls.nursery_info = datasets.load("nursery")

    def test_car_is_full_product(self):
        v = datasets.verify(self.car)
        self.assertEqual(v["domain_sizes"], [4, 4, 4, 3, 3, 3])
        self.assertEqual(v["rows"], 1728)
        self.assertTrue(v["full_product"])
        self.assertTrue(v["one_class_per_tuple"])
        self.assertEqual(v["class_counts"], {"unacc": 1210, "acc": 384, "good": 69, "vgood": 65})
        self.assertEqual(self.car.attributes[0].domain, ("vhigh", "high", "med", "low"))
        self.assertTrue(self.car_info["names_order_matches"])

    def test_nursery_is_full_product(self):
        v = datasets.verify(self.nursery)
        self.assertEqual(v["domain_sizes"], [3, 5, 4, 4, 3, 2, 3, 3])
        self.assertEqual(v["rows"], 12960)
        self.assertTrue(v["full_product"])
        self.assertTrue(v["one_class_per_tuple"])
        self.assertEqual(self.nursery_info["blank_lines"], 1)
        self.assertEqual(self.nursery.outcomes,
                         ("not_recom", "recommend", "very_recom", "priority", "spec_prior"))

    def test_verify_detects_problems(self):
        rows = self.car.rows[:-1] + [Row(self.car.rows[0].condition, "acc")]
        v = datasets.verify(self.car.with_rows(rows))
        self.assertFalse(v["full_product"])
        self.assertEqual(v["duplicate_condition_tuples"], 1)
        self.assertEqual(v["tuples_with_more_than_one_class"], 1)

    def test_parse_c45_names(self):
        classes, spec = datasets.parse_c45_names("| c\n\na, b.\n\nx: 1, 2.\ny: p, q, r.\n")
        self.assertEqual(classes, ("a", "b"))
        self.assertEqual(spec, [("x", ("1", "2")), ("y", ("p", "q", "r"))])

    def test_unobserved_value_breaks_reading_b_not_complete(self):
        full = self.car
        t0 = full.with_rows([r for r in full.rows if r.condition[5] != "low"])
        res = run_methods(t0)
        self.assertTrue(res["COMPLETE"]["exact"])
        self.assertTrue(res["DMN (declared values)"]["exact"])
        self.assertEqual(res["DMN (declared values)"]["regions"], 1)
        self.assertEqual(res["LATC B (odometer)"]["missed"], 576)
        self.assertEqual(res["DMN (observed values)"]["missed"], 576)
        self.assertEqual(latc.missing_count(t0), 0)
        truth = {r.condition: r.outcome for r in full.rows}
        rc = restore_check(t0, exact_complement(t0), truth)
        self.assertTrue(rc["sound"] and rc["equals_full_table"])


if __name__ == "__main__":
    unittest.main()
