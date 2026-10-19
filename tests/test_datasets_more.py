import unittest
from fractions import Fraction

from latc_check import datasets, datasets_more as dm, datasets_report, latc, trap_frequency
from latc_check.model import Row


class Loaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {k: dm.load(k) for k in dm.DATASETS}

    def test_lenses(self):
        t, info = self.tables["lenses"]
        v = datasets.verify(t)
        self.assertEqual(v["domain_sizes"], [3, 2, 2, 2])
        self.assertEqual((v["states"], v["rows"]), (24, 24))
        self.assertTrue(v["full_product"] and v["one_class_per_tuple"])
        self.assertEqual(v["class_counts"], {"1": 4, "2": 5, "3": 15})
        self.assertTrue(info["stated_class_counts_match"])
        self.assertTrue(info["ids_are_line_order"])
        self.assertEqual(info["value_labels"]["age_of_the_patient"],
                         {"1": "young", "2": "pre-presbyopic", "3": "presbyopic"})
        self.assertEqual(t.outcomes, ("1", "2", "3"))

    def test_balance(self):
        t, info = self.tables["balance"]
        v = datasets.verify(t)
        self.assertEqual(v["domain_sizes"], [5, 5, 5, 5])
        self.assertEqual(v["rows"], 625)
        self.assertTrue(v["full_product"] and v["one_class_per_tuple"])
        self.assertEqual(v["class_counts"], {"L": 288, "B": 49, "R": 288})
        self.assertEqual(t.outcomes, ("L", "B", "R"))
        self.assertTrue(info["stated_counts_match"])
        self.assertTrue(info["stated_class_counts_match"])
        self.assertEqual(info["rows_disagreeing_with_rule"], 0)

    def test_monks(self):
        counts = {1: {"0": 216, "1": 216}, 2: {"0": 290, "1": 142}, 3: {"0": 204, "1": 228}}
        train_rows = {1: 124, 2: 169, 3: 122}
        for p in (1, 2, 3):
            t, info = self.tables[f"monks{p}"]
            v = datasets.verify(t)
            self.assertEqual(v["domain_sizes"], [3, 3, 2, 3, 4, 2])
            self.assertEqual(v["rows"], 432)
            self.assertTrue(v["full_product"] and v["one_class_per_tuple"])
            self.assertEqual(v["class_counts"], counts[p])
            self.assertEqual(info["rows_disagreeing_with_target"], 0)
            tr = info["train"]
            self.assertEqual(tr["rows"], train_rows[p])
            self.assertTrue(tr["all_in_test"])
            self.assertEqual(tr["labels_differing_from_test"], 6 if p == 3 else 0)
            self.assertEqual(tr["labels_differing_from_target"], 6 if p == 3 else 0)
        # same inputs in all three .test files
        conds = [sorted(r.condition for r in self.tables[f"monks{p}"][0].rows) for p in (1, 2, 3)]
        self.assertEqual(conds[0], conds[1])
        self.assertEqual(conds[0], conds[2])

    def test_verify_detects_a_hole(self):
        t = self.tables["lenses"][0]
        v = datasets.verify(t.with_rows(t.rows[1:] + [Row(t.rows[1].condition, "1")]))
        self.assertFalse(v["full_product"])
        self.assertEqual(v["tuples_with_more_than_one_class"], 1)


class Parsers(unittest.TestCase):
    def test_balance_count_mismatch_is_reported(self):
        text = "7. Attribute Information:\n\t1. Class Name: 3 (L, B, R)\n\t2. Left-Weight: 4 (1, 2, 3, 4, 5)\n8. x\n"
        d = dm.parse_balance_names(text)
        self.assertFalse(d["stated_counts_match"])
        self.assertEqual(d["attributes"], [("Left_Weight", ("1", "2", "3", "4", "5"))])

    def test_unexpected_token_rejected(self):
        with self.assertRaises(ValueError):
            dm.parse_monks_names("7. Attribute information:\n 1. class: 0, 1\n 2. a1: 1, 2; drop\n8. x\n")

    def test_rules(self):
        self.assertEqual(dm.balance_rule(("1", "1", "1", "1")), "B")
        self.assertEqual(dm.balance_rule(("5", "1", "1", "4")), "L")
        self.assertEqual(dm.monk_rule(1, ("2", "2", "1", "1", "3", "1")), "1")
        self.assertEqual(dm.monk_rule(2, ("1", "1", "2", "2", "2", "2")), "1")


class Experiments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lenses = dm.load("lenses")[0]

    def test_keep_rule(self):
        self.assertEqual([dm.keep_count(x, 24) for x in datasets_report.LEVELS], [22, 18, 12, 6, 2, 1])
        self.assertEqual([dm.keep_count(x, 625) for x in datasets_report.LEVELS], [562, 469, 312, 156, 62, 6])

    def test_random_removal_matches_datasets_report(self):
        levels, seeds = (0.5, 0.1, 0.01), 4
        mine = dm.random_removal(self.lenses, "lenses", levels, seeds, 7)
        ref = datasets_report.random_removal(self.lenses, "lenses", levels, seeds, 7)
        for lv in ref:
            for k in ("t0_rows", "restore_ok", "runs_with_unobserved_value", "mean_unobserved_declared_values"):
                self.assertEqual(mine[lv][k], ref[lv][k])
            for m in datasets_report.METHODS:
                a, b = dict(mine[lv]["methods"][m]), dict(ref[lv]["methods"][m])
                a.pop("mean_ms"), b.pop("mean_ms")
                self.assertEqual(a, b)

    def test_one_row_is_declared_complete(self):
        r = dm.random_removal(self.lenses, "lenses", (0.01,), 3, 1)["0.01"]
        self.assertEqual(r["t0_rows"], 1)
        self.assertEqual(r["latc"]["declares_complete"], 3)
        self.assertEqual(r["latc"]["mean_states_missed_when_declared_complete"], 23)
        self.assertEqual(r["methods"]["COMPLETE"]["exact_rate"], 1.0)
        self.assertEqual(r["methods"]["DMN (declared values)"]["exact_rate"], 1.0)
        self.assertEqual(r["methods"]["LATC B (odometer)"]["exact_rate"], 0.0)
        self.assertEqual(r["restore_ok"], 3)

    def test_structured_end_to_end(self):
        s = dm.structured_removal(self.lenses, "lenses")
        self.assertEqual(s["restore_runs"], 9)
        self.assertEqual(s["restore_ok"], 9)
        self.assertEqual(s["methods"]["COMPLETE"]["exact_rate"], 1.0)
        self.assertEqual(s["methods"]["DMN (declared values)"]["exact_rate"], 1.0)
        for m in ("LATC A (deficit fill)", "LATC B (odometer)", "DMN (observed values)"):
            self.assertEqual(s["methods"][m]["exact_rate"], 0.0)
        self.assertEqual(s["latc"]["declares_complete"], 9)
        self.assertEqual(s["latc"]["mean_states_missed_when_declared_complete"], (3 * 8 + 6 * 12) / 9)
        for c in s["cases"]:
            self.assertEqual(c["latc"]["corollary3_count"], 0)
            self.assertEqual(c["methods"]["LATC B (odometer)"]["missed"], c["missing"])

    def test_latc_view(self):
        t0 = self.lenses.with_rows(self.lenses.rows[:2])      # differ in tear production only
        v = dm.latc_view(t0, 24)
        self.assertEqual(latc.missing_count(t0), 0)
        self.assertTrue(v["declares_complete"])
        self.assertEqual(v["true_missing"], 22)
        self.assertFalse(v["corollary3_correct"])

    def test_trap_table(self):
        t = dm.trap_table([3, 2, 2, 2])
        self.assertEqual(t["ks"], [5, 8, 10, 17, 20])
        self.assertEqual(t["by_k"]["17"]["p_trap"], 0.0)        # 17 rows cannot avoid any value
        self.assertEqual(Fraction(t["by_k"]["8"]["p_trap_fraction"]),
                         trap_frequency.p_trap_exact([2, 2, 2, 3], 8))
        p, _ = trap_frequency.brute_force([3, 2, 2, 2], 5)
        self.assertAlmostEqual(t["by_k"]["5"]["p_trap"], float(p), places=15)
        self.assertEqual(t["smallest_k"], {"0.05": 9, "0.01": 11})


if __name__ == "__main__":
    unittest.main()
