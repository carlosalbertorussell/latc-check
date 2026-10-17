import random
import unittest
import xml.etree.ElementTree as ET

from latc_check import dmn_compare as dc
from latc_check import examples as ex
from latc_check import randomized
from latc_check.compare import compare
from latc_check import dmn_oracle
from latc_check.dmn import (ANY, DMN14_NS, DMNTable, Input, Interval, Not, OneOf, Point, Rule,
                            analyse, at_least, below, closed, entry_set, expand, from_exact,
                            half_open, merge_regions, to_dmn_xml, to_exact, violations)
from latc_check.reference import exact_complement


class Intervals(unittest.TestCase):
    def test_bounds(self):
        self.assertTrue(half_open(60, 65).contains(60))
        self.assertFalse(half_open(60, 65).contains(65))
        self.assertFalse(half_open(60, 65).intersects(at_least(65)))
        self.assertTrue(closed(60, 65).intersects(at_least(65)))
        self.assertTrue(Interval(1, 1, True, False).is_empty())
        self.assertTrue(half_open(60, 65).issubset(at_least(60)))
        self.assertEqual(half_open(60, 65).feel(), "[60..65)")
        self.assertEqual(below(60).feel(), "< 60")


class Sweep(unittest.TestCase):
    def num(self, rules, hp="UNIQUE"):
        inp = (Input("x", domain=closed(0, 10)),)
        return DMNTable(inp, [Rule((e,), o) for e, o in rules], hp)

    def test_open_closed_gap_at_a_point(self):
        a = analyse(self.num([(below(5), "a"), (Interval(5, 10, False, True), "b")]))
        self.assertEqual(a.gaps, [(closed(5, 5),)])   # x = 5 is missing
        self.assertEqual(a.overlaps, {})

    def test_overlap_at_a_shared_closed_bound(self):
        a = analyse(self.num([(closed(0, 5), "a"), (closed(5, 10), "b")]))
        self.assertEqual(a.gaps, [])
        self.assertEqual(list(a.overlaps), [(0, 1)])
        self.assertEqual(a.overlaps[(0, 1)], (closed(5, 5),))

    def test_hit_policies(self):
        t = self.num([(closed(0, 6), "a"), (closed(4, 10), "a"), (closed(5, 10), "b")])
        a = analyse(t)
        self.assertEqual(len(violations(t, a)["violating_pairs"]), 3)
        t.hit_policy = "ANY"
        self.assertEqual(violations(t, a)["violating_pairs"], [(0, 2), (1, 2)])
        t.hit_policy = "FIRST"
        v = violations(t, analyse(t))
        # rule 2 [5, 10] lies inside rule 1 [4, 10], which comes first: masked
        self.assertEqual((v["violating_pairs"], v["masked_pairs"], v["never_fire"]),
                         ([(2, 1)], [(2, 1)], [2]))
        self.assertEqual(v["maximal_overlap_sets"], [(0, 1, 2)])

    def test_priority_follows_output_order(self):
        inp = (Input("x", domain=closed(0, 10)),)
        rules = [Rule((closed(0, 10),), "low"), Rule((closed(3, 4),), "high")]
        t = DMNTable(inp, rules, "PRIORITY", output_values=("high", "low"))
        v = violations(t, analyse(t))
        self.assertEqual((v["masked_pairs"], v["never_fire"]), ([], []))
        t.output_values = ("low", "high")
        v = violations(t, analyse(t))
        self.assertEqual((v["masked_pairs"], v["never_fire"]), ([(1, 0)], [1]))
        exact, _ = to_exact(DMNTable((Input("x", domain=closed(0, 10),
                                            bins=(("a", half_open(0, 3)), ("b", closed(3, 4)),
                                                  ("c", Interval(4, 10, False, True)))),),
                                     rules, "PRIORITY", output_values=("high", "low")))
        self.assertEqual([(r.condition, r.outcome) for r in exact.rows],
                         [(("b",), "high"), (("a",), "low"), (("c",), "low")])

    def test_masking_by_a_union_is_never_fire_only(self):
        inp = (Input("x", domain=closed(0, 10)),)
        t = DMNTable(inp, [Rule((closed(0, 5),), "a"), Rule((closed(5, 10),), "b"),
                           Rule((closed(2, 8),), "c")], "FIRST")
        v = violations(t, analyse(t))
        self.assertEqual((v["masked_pairs"], v["never_fire"]), ([], [2]))

    def test_negation(self):
        num = Input("x", domain=closed(0, 10))
        enum = Input("e", values=("a", "b", "c"))
        self.assertEqual(entry_set(enum, Not(OneOf(frozenset("ab")))), frozenset("c"))
        u = entry_set(num, Not(half_open(3, 5)))
        self.assertTrue(u.contains(2.9) and u.contains(5) and not u.contains(3))
        t = DMNTable((num,), [Rule((Not(half_open(3, 5)),), "out"), Rule((closed(4, 6),), "in")])
        a = analyse(t)
        self.assertEqual(a.gaps, [(half_open(3, 4),)])
        self.assertEqual(a.overlap_pairs, [(0, 1)])
        self.assertIn("not([3..5))", to_dmn_xml(t))
        with self.assertRaises(TypeError):
            entry_set(num, Not(ANY))

    def test_merge(self):
        inp = (Input("e", values=("a", "b", "c")), Input("x", domain=closed(0, 10)))
        regs = [(frozenset("a"), half_open(0, 5)), (frozenset("a"), closed(5, 10)),
                (frozenset("b"), closed(0, 10))]
        self.assertEqual(merge_regions(regs, inp), [(frozenset("ab"), closed(0, 10))])

    def test_enum_list_entry_and_undeclared_value(self):
        inp = (Input("e", values=("a", "b", "c")),)
        t = DMNTable(inp, [Rule((OneOf(frozenset("ac")),), "x"), Rule((Point("z"),), "y")])
        a = analyse(t)
        self.assertEqual(expand(a.gaps, inp)[0], [("b",)])
        self.assertEqual(a.undeclared, [(1, "e", "z")])

    def test_empty_table_is_one_gap(self):
        t = DMNTable(dc.PENSION_INPUTS, [])
        a = analyse(t)
        self.assertEqual(len(a.gaps), 1)
        self.assertEqual(len(expand(a.gaps, t.inputs)[0]), 24)


class Pension(unittest.TestCase):
    def test_t0_gaps_equal_complete(self):
        r = dc.pension_t0()
        self.assertTrue(r["gap_tuples_equal_complete"])
        self.assertEqual((r["gap_tuples"], r["partial_bins"], r["overlap_pairs"]), (16, 0, 0))
        self.assertLess(r["gap_regions"], 16)

    def test_round_trip(self):
        t = ex.pension_completed()
        back, info = to_exact(from_exact(t, dc.PENSION_NUMERIC))
        self.assertEqual(info["misaligned_entries"], [])
        self.assertEqual([(r.condition, r.outcome) for r in back.rows],
                         [(r.condition, r.outcome) for r in t.rows])

    def test_compact_equals_completed_table(self):
        r = dc.pension_compact()
        self.assertTrue(r["expands_to_completed_table"])
        self.assertEqual((r["gap_regions"], r["overlap_pairs"]), (0, 0))
        self.assertEqual(r["review_compact"]["rules"], 8)

    def test_seeded_faults_seen_by_both(self):
        f = dc.pension_compact()["faults"]
        self.assertEqual((f["drop_rule_5"]["dmn_gap_tuples"], f["drop_rule_5"]["complete_uncovered"]), (1, 1))
        w = f["widen_rule_2"]
        self.assertEqual(len(w["dmn_overlap_pairs"]), 3)
        self.assertEqual((w["complete_multi_hit"], w["complete_conflicts"]), (4, 4))

    def test_misaligned_entry_is_flagged(self):
        t = DMNTable(dc.PENSION_INPUTS, [Rule((ANY, ANY, ANY, at_least(62)), "YES")])
        _, info = to_exact(t)
        self.assertEqual(info["misaligned_entries"], [(0, "Age")])

    def test_raw_table1(self):
        r = dc.raw_table1()
        self.assertEqual(r["overlaps_by_policy"]["UNIQUE"]["pairs"], 0)
        self.assertTrue(r["dmn_gaps_equal_complete"])
        self.assertEqual((r["raw_rules_cover_tuples"], r["table1a_covers"]), (12, 8))
        self.assertEqual(r["latc_label_view"]["product"], 32)
        self.assertEqual([p["row"] for p in r["per_row"] if p["raw_tuples"] > 1], [3, 4, 7, 8])
        self.assertEqual([p["row"] for p in r["per_row"] if p["outcome_changed"]], [6, 8])

    def test_raw_overlap_if_age_labels_cross(self):
        # The raw Age labels do overlap; they just never meet in rows that agree
        # on the other inputs.  Put two of them in the same slab and DMN sees it.
        rules = [Rule((Point("F"), Point("D"), ANY, at_least(60)), "YES"),
                 Rule((Point("F"), Point("D"), ANY, below(65)), "NO")]
        t = DMNTable(dc.PENSION_INPUTS, rules)
        a = analyse(t)
        self.assertEqual(list(a.overlaps), [(0, 1)])
        self.assertEqual(a.overlaps[(0, 1)][3], half_open(60, 65))


class Agreement(unittest.TestCase):
    def test_counterexample(self):
        r = dc.counterexample()
        self.assertTrue(r["T0"]["exact"] and r["twin"]["exact"])

    def test_random_scenarios(self):
        rng = random.Random(3)
        for scenario in randomized.SCENARIOS:
            for _ in range(60):
                t = randomized.generate_case(rng, scenario)
                tuples, _ = expand(analyse(from_exact(t)).gaps, from_exact(t).inputs)
                filtered = [c for c in tuples if t.is_valid(c)]
                self.assertTrue(compare(filtered, t).exact)
                if scenario != "constrained":
                    self.assertTrue(compare(tuples, t).exact)
                if scenario == "unobserved":
                    obs = from_exact(t, values="observed")
                    self.assertFalse(compare(expand(analyse(obs).gaps, obs.inputs)[0], t).exact)

    def test_set_grouping_same_tuples(self):
        rng = random.Random(4)
        for _ in range(50):
            t = randomized.generate_case(rng, "observed")
            d = from_exact(t)
            a = sorted(expand(analyse(d, enum_grouping="set").gaps, d.inputs)[0])
            self.assertEqual(a, sorted(exact_complement(t)))

    def test_bench(self):
        rows = dc.bench(grid=[(3, 3)])
        self.assertEqual(rows[0]["space"], 27)


class Differential(unittest.TestCase):
    """analyse + violations against the exhaustive oracle on small random tables."""

    def test_matches_oracle_on_random_tables(self):
        rng = random.Random(11)
        for policy in ("UNIQUE", "ANY", "FIRST", "PRIORITY"):
            for trial in range(150):
                t = dmn_oracle.random_table(rng, policy)
                res = dmn_oracle.differential(t)
                self.assertTrue(all(res.values()), (policy, trial, res, t))

    def test_oracle_grid_hits_open_cells(self):
        inp = (Input("x", domain=closed(0, 2)),)
        t = DMNTable(inp, [Rule((Interval(0, 1, True, False),), "a"),
                           Rule((Interval(1, 2, False, True),), "b")])
        self.assertEqual(dmn_oracle.oracle(t)["uncovered"], [(1.0,)])

    def test_summary_run(self):
        s = dmn_oracle.run(trials=200, seed=5)
        self.assertEqual(s["failures"], [])
        self.assertEqual(s["agree"]["gaps"], 200)


class Xml(unittest.TestCase):
    def test_export_parses(self):
        xml = to_dmn_xml(dc.pension_compact_dmn(), "pension")
        root = ET.fromstring(xml.split("\n", 1)[1])
        ns = {"d": DMN14_NS}
        self.assertEqual(root.tag, f"{{{DMN14_NS}}}definitions")
        self.assertEqual(len(root.findall(".//d:rule", ns)), 8)
        self.assertEqual(root.find(".//d:decisionTable", ns).get("hitPolicy"), "UNIQUE")
        texts = [e.text for e in root.findall(".//d:inputEntry/d:text", ns)]
        self.assertIn("[60..65)", texts)
        self.assertIn("-", texts)
        self.assertIn('"M"', texts)


if __name__ == "__main__":
    unittest.main()
