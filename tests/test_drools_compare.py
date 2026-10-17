import unittest

from latc_check.drools_compare import compare, parse_messages, predicate, split_top
from latc_check.dmn import DMNTable, Input, Interval, Rule, closed, half_open


SAMPLE = """=== a.dmn : 4 messages
WARNING\tDECISION_TABLE_GAP\tDMN: Gap detected: [ "a", ( 1 .. 3 ) ] (DMN id: t, DMN Validation)
WARNING\tDECISION_TABLE_OVERLAP_HITPOLICY_UNIQUE\tDMN: Overlap detected: Overlap values: [ 4, [ 2 .. 3 ) ] for rules: [2, 3, 5]. UNIQUE hit policy
ERROR\tDECISION_TABLE_MASKED_RULE\tDMN: Rule 3 is masked by rule: 1 (DMN id: t)
WARNING\tDECISION_TABLE_ANALYSIS_ERROR\tDMN: Skipped Decision Table Analysis of table 'null'
"""


class Parser(unittest.TestCase):
    def test_split_and_predicates(self):
        self.assertEqual(split_top(' "a", ( 1 .. 3 ), <=2, [ "b" .. "d" ] '),
                         ['"a"', '( 1 .. 3 )', '<=2', '[ "b" .. "d" ]'])
        self.assertTrue(predicate("( 1 .. 3 )")(2) and not predicate("( 1 .. 3 )")(3))
        self.assertTrue(predicate("[ 1 .. 3 ]")(3))
        self.assertTrue(predicate("<=2")(2) and not predicate("<2")(2))
        self.assertTrue(predicate('[ "b" .. "d" ]')("c") and not predicate('[ "b" .. "d" ]')("a"))
        self.assertTrue(predicate("-")(123) and predicate('"x"')("x"))

    def test_parse_messages(self):
        f = parse_messages(SAMPLE)["a.dmn"]
        self.assertEqual(len(f["gaps"]), 1)
        self.assertEqual(f["overlaps"], [[1, 2, 4]])
        self.assertEqual(f["masked"], [(2, 0)])
        self.assertTrue(f["skipped"])
        self.assertEqual(f["errors"], [])

    def test_compare_against_oracle(self):
        inp = (Input("x", domain=closed(0, 4)),)
        t = DMNTable(inp, [Rule((half_open(0, 2),), "a"), Rule((Interval(2, 4, False, True),), "b")])
        ok = {"gaps": [[predicate("2")]], "overlaps": [], "masked": [], "skipped": False}
        self.assertEqual(compare(t, ok), {"gaps": True, "overlap_pairs": True})
        miss = dict(ok, gaps=[])
        self.assertFalse(compare(t, miss)["gaps"])


if __name__ == "__main__":
    unittest.main()
