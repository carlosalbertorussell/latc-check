import unittest
import xml.etree.ElementTree as ET

from latc_check import drools_domains as dd
from latc_check.dmn import DMN14_NS
from latc_check.model import DecisionTable, Row, attrs

Q = lambda t: f"{{{DMN14_NS}}}{t}"

SKIP = ('DMN: Columns: [buying, maint] relate to FEEL string values which can be enumerated '
        'for the inputs; Gap analysis skipped. (DMN id: t, DMN Validation)')

OUTPUT = """=== a.dmn : 2 messages
WARNING\tDECISION_TABLE_GAP\tDMN: Gap detected: [ "z", - ] (DMN id: t, DMN Validation, Gap Analysis)
WARNING\tDECISION_TABLE_2NDNFVIOLATION\tDMN: Second Normal Form Violation: Input 2 is irrelevant
"""


def small():
    full = DecisionTable(attrs([("a", ("x", "y", "z")), ("b", ("p", "q"))]),
                         [Row((a, b), "o") for a in "xyz" for b in "pq"], outcomes=("o",))
    return full


class Cases(unittest.TestCase):
    def test_removal_and_missing(self):
        cs = dd.removal_cases(small())
        self.assertEqual([(a, v) for a, v, _ in cs], [("a", "x"), ("a", "y"), ("a", "z"), ("b", "p"), ("b", "q")])
        a, v, t0 = cs[2]
        self.assertEqual(len(t0.rows), 4)
        self.assertEqual(dd.missing_states(t0), {("z", "p"), ("z", "q")})
        self.assertEqual(dd.observed_values(t0), {"a": ("x", "y"), "b": ("p", "q")})


class Export(unittest.TestCase):
    def setUp(self):
        _, _, t0 = dd.removal_cases(small())[2]
        self.t0 = t0
        self.d = dd.dmn_of(t0)
        self.obs = dd.observed_values(t0)

    def parse(self, var):
        return ET.fromstring(dd.export_variant(self.d, "t", var, "a", self.obs))

    def iv(self, root):
        return [e.find(Q("text")).text if e is not None else None
                for e in (i.find(Q("inputValues")) for i in root.iter(Q("input")))]

    def expr_types(self, root):
        return [e.get("typeRef") for e in root.iter(Q("inputExpression"))]

    def items(self, root):
        return {i.get("name"): i.find(f"{Q('allowedValues')}/{Q('text')}").text
                for i in root.iter(Q("itemDefinition"))}

    def test_variants(self):
        r = self.parse("V1")
        self.assertEqual(self.iv(r), ['"x","y","z"', '"p","q"'])
        self.assertEqual(self.items(r), {})
        r = self.parse("V2")
        self.assertEqual(self.iv(r), [None, None])
        self.assertEqual(self.expr_types(r), ["string", "string"])
        r = self.parse("V3a")
        self.assertEqual(self.iv(r), [None, None])
        self.assertEqual(self.expr_types(r), ["string", "string"])
        self.assertEqual(self.items(r)["t_input_0_full"], '"x","y","z"')
        var_types = [v.get("typeRef") for v in r.iter(Q("variable")) if v.get("id", "").startswith("input_data")]
        self.assertEqual(var_types, ["t_input_0_full", "t_input_1_full"])
        r = self.parse("V3b")
        self.assertEqual(self.expr_types(r), ["t_input_0_full", "t_input_1_full"])
        self.assertEqual(self.iv(self.parse("V4")), ['"x","y"', '"p","q"'])
        self.assertEqual(self.iv(self.parse("V5")), [None, '"p","q"'])
        r = self.parse("V6")
        self.assertEqual(self.iv(r), ['"x","y"', '"p","q"'])
        self.assertEqual(self.items(r)["t_input_0_full"], '"x","y","z"')
        r = self.parse("V7")
        self.assertEqual(self.iv(r), ['"x","y","z"', '"p","q"'])
        self.assertEqual(self.items(r)["t_input_0_observed"], '"x","y"')
        # itemDefinitions come before the decision (schema order)
        self.assertEqual(r[0].tag, Q("itemDefinition"))
        with self.assertRaises(ValueError):
            dd.export_variant(self.d, "t", "V9")


class Parse(unittest.TestCase):
    def test_skip_columns(self):
        self.assertEqual(dd.gap_skip_columns(SKIP), ["buying", "maint"])
        self.assertIsNone(dd.gap_skip_columns("DMN: Gap detected: [ - ]"))

    def test_evaluate(self):
        _, _, t0 = dd.removal_cases(small())[2]
        r = dd.evaluate(OUTPUT, t0.attributes, dd.missing_states(t0))
        self.assertEqual(r["outcome"], "gaps reported")
        self.assertEqual((r["missing_covered"], r["covered_not_missing"]), (2, 0))
        r = dd.evaluate("=== b.dmn : 1 messages\nWARNING\tDECISION_TABLE_GAP\t" + SKIP + "\n",
                        t0.attributes, dd.missing_states(t0))
        self.assertEqual(r["outcome"], "gap analysis skipped")
        self.assertEqual(r["gap_skip_columns"], ["buying", "maint"])
        self.assertEqual(r["missing_covered"], 0)
        self.assertEqual(dd.evaluate("", t0.attributes, set())["outcome"], "error")

    def test_wildcard_read_over_drools_domain(self):
        _, _, t0 = dd.removal_cases(small())[2]          # a = z removed
        d, obs, miss = dd.dmn_of(t0), dd.observed_values(t0), dd.missing_states(t0)
        self.assertEqual(dd.effective_domains(d, "V4", "a", obs), [("x", "y"), ("p", "q")])
        self.assertEqual(dd.effective_domains(d, "V2", "a", obs), [None, None])
        self.assertEqual(dd.effective_domains(d, "V5", "a", obs), [None, ("p", "q")])
        self.assertEqual(dd.effective_domains(d, "V7", "a", obs)[0], ("x", "y", "z"))
        out = "=== c.dmn : 1 messages\nWARNING\tDECISION_TABLE_GAP\tDMN: Gap detected: [ -, \"p\" ] (DMN id: t)\n"
        r = dd.evaluate(out, t0.attributes, miss, dd.effective_domains(d, "V4", "a", obs), 0, "z")
        self.assertEqual((r["missing_covered"], r["removed_value_states_found"]), (0, 0))
        self.assertEqual(r["covered_not_missing"], 2)
        self.assertEqual(r["missing_covered_full_wildcard"], 1)
        self.assertEqual(r["gaps_first"], ['-, "p"'])


if __name__ == "__main__":
    unittest.main()
