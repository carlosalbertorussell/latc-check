import unittest
from itertools import product

from latc_check import datasets
from latc_check import examples as ex
from latc_check import sensitivity as s
from latc_check.dmn import to_exact
from latc_check.dmn_compare import pension_compact_dmn
from latc_check.model import RV


def brute_overlaps(old, new):
    """Old states meeting each new state, by direct box comparison (no rank arithmetic)."""
    out = {}
    for y in product(*(range(len(d.labels)) for d in new)):
        out[tuple(d.labels[j] for d, j in zip(new, y))] = sorted(
            tuple(d.labels[i] for d, i in zip(old, x))
            for x in product(*(range(len(d.labels)) for d in old))
            if all(s._meet(a.meanings[i], b.meanings[j]) for a, b, i, j in zip(old, new, x, y)))
    return out


class Schemas(unittest.TestCase):
    def test_published_bins_reproduce_examples(self):
        dims = s.pension_schema()
        self.assertEqual(s.schema_attributes(dims), ex.PENSION_ATTRS)
        self.assertEqual(s.num_dim("Age", ex.AGE_RANGE, (65,)).labels, (">=65", "<65"))
        self.assertEqual(s.num_dim("C", (0, 60), (20, 30)).labels, (">=30", "20-29", "<20"))

    def test_rank_migration_matches_brute_force(self):
        old = s.pension_schema()
        for age, con in (((60, 67), (30,)), ((65,), (20, 30)), ((62, 65), (35,))):
            new = s.pension_schema(age, con)
            mig = s.Migration(old, new)
            brute = brute_overlaps(old, new)
            for r2 in range(mig.ri_new.size):
                got = sorted(mig.ri_old.unrank(x) for x in mig.old_of(r2))
                self.assertEqual(got, brute[mig.ri_new.unrank(r2)])

    def test_identity_migration(self):
        dims = s.pension_schema()
        res = s.Migration(dims, dims).apply({r.condition: r.outcome for r in ex.pension_completed().rows})
        self.assertEqual(res["categories"]["identical"], 24)
        self.assertEqual(res["fates"]["unchanged"], 24)

    def test_incomparable_schemas_rejected(self):
        a = (s.enum_dim("x", ("a", "b")),)
        with self.assertRaises(ValueError):
            s.Migration(a, (s.enum_dim("x", ("a", "c")),))


class CutPoints(unittest.TestCase):
    def test_published(self):
        c = s.cut_point_case((60, 65), (30,))
        self.assertEqual((c["states"], c["completion"]["missing"], c["completion"]["dmn_gap_regions"]),
                         (24, 16, 7))
        self.assertEqual(c["published_complement"]["unchanged"], 16)
        self.assertTrue(c["completion"]["dmn_gaps_equal_complete"])
        self.assertEqual(c["raw_table1_misaligned_rules"], 0)

    def test_dropping_cut_60_merges_and_conflicts(self):
        c = s.cut_point_case((65,), (30,))
        self.assertEqual(c["states"], 16)
        self.assertEqual(c["t0_fates"], {"unchanged": 3, "merged": 5})
        # F I >=30 <65 joins F I >=30 60-64 (YES) and F I >=30 <60 (NO)
        self.assertIn("F I >=30 <65", c["reuse_24_approved"]["conflicting_states"])
        self.assertEqual(c["liberal_mapping"]["conflicting_tuples"], 1)
        self.assertEqual(c["completion"]["missing"], s.review_load(
            s.Migration(s.pension_schema(), s.pension_schema((65,))).apply(s._t0_dict())))

    def test_refinement_keeps_t0_aligned(self):
        c = s.cut_point_case((55, 60, 65), (20, 30))
        self.assertEqual(c["t0_misaligned_rows"], 0)
        self.assertEqual(c["reuse_24_approved"]["no_outcome"], 0)
        self.assertEqual(c["completion"]["missing"], 48 - 12)


class Constraints(unittest.TestCase):
    def test_pension(self):
        cases = s.pension_constraints()
        rv = cases[1]
        self.assertEqual((rv["valid"], rv["missing_before"], rv["missing_after"]), (21, 17, 14))
        self.assertEqual(rv["t0_rows_dropped"], 1)       # T0 row 6 lies in an excluded Rv state
        for c in cases:
            self.assertTrue(c.get("dmn_explicit_impossible_rules") is None
                            or c["dmn_explicit_impossible_rules"]["overlap_pairs"] == 0)
        self.assertEqual(rv["dmn_native"]["impossible_reported_as_gaps"], 3)
        for c in cases:
            self.assertTrue(c["complete_equals_filtered_unconstrained"])
            self.assertEqual(c["deficit_check_problems"], 0)
            self.assertTrue(c["dmn_native"]["filtered_equals_complete"])
        self.assertEqual(cases[2]["excluded"], 0)        # published bins: nothing excluded
        self.assertEqual(cases[3]["excluded"], 4)        # contribution >= 30 with age < 45


class Policy(unittest.TestCase):
    def test_parametrised_rule_is_the_compact_rule(self):
        compact = {r.condition: r.outcome for r in to_exact(pension_compact_dmn())[0].rows}
        self.assertEqual(s.rule_outcomes(s.pension_schema()), compact)

    def test_versions(self):
        p = {r["version"]: r for r in s.pension_policy()}
        self.assertTrue(p["v2"]["affected_within_re_review"])
        self.assertEqual(p["v2"]["wrong_inherited_outcomes"], {"identical": 0, "contained": 0, "uniform": 0})
        # Keeping the old cut 65 makes 65-66 'contained': the inherited old outcome is wrong there.
        self.assertEqual(p["v2-refined"]["wrong_inherited_outcomes"]["contained"], 4)
        # An outcome-only change is invisible to the schema comparison.
        self.assertEqual(p["v4"]["re_review"], 0)
        self.assertEqual(p["v4"]["policy_affected"], 3)
        self.assertFalse(p["v4"]["affected_within_re_review"])


class Datasets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.car = datasets.car()
        cls.t0 = s.fixed_t0(cls.car, "car")

    def test_merge_conflicts_match_brute_force(self):
        r = s.merge_split("car", self.car, self.t0, attributes=("doors",))
        k = self.car.names.index("doors")
        for m in r["merges"]:
            a, b = m["values"]
            classes = {}
            for row in self.car.rows:
                c = list(row.condition)
                c[k] = "M" if c[k] in (a, b) else c[k]
                classes.setdefault(tuple(c), set()).add(row.outcome)
            self.assertEqual(m["full_table_conflicts"], sum(len(v) > 1 for v in classes.values()))
            self.assertTrue(m["completion"]["dmn_gaps_equal_complete"])
        self.assertTrue(all(sp["functional"] for sp in r["splits"]))
        self.assertEqual(r["baseline"]["missing"], 864)

    def test_pair_constraint(self):
        c = s.dataset_constraints("car", self.car, self.t0, dmn=False)[1]
        self.assertEqual(c["excluded"], 144)
        self.assertTrue(c["complete_equals_filtered_unconstrained"])
        self.assertTrue(c["dmn_explicit_impossible_rules"]["gaps_equal_complete"])
        self.assertEqual(c["dmn_native"]["impossible_reported_as_gaps"],
                         c["missing_before"] - c["missing_after"])


if __name__ == "__main__":
    unittest.main()
