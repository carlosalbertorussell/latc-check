import math
import os
import tempfile
import unittest

from latc_check import dmn_import as di
from latc_check import dmn_oracle
from latc_check.datasets_report import bounded_proxy
from latc_check.dmn import ANY, DMN14_NS, Interval, Not, OneOf, Point, analyse, violations

NAMESPACES = {
    "1.1": "http://www.omg.org/spec/DMN/20151101/dmn.xsd",
    "1.2": "http://www.omg.org/spec/DMN/20180521/MODEL/",
    "1.3": "https://www.omg.org/spec/DMN/20191111/MODEL/",
    "1.4": DMN14_NS,
    "1.5": "https://www.omg.org/spec/DMN/20230324/MODEL/",
}

TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="{ns}" id="d" name="d" namespace="urn:x">
  <itemDefinition name="tColour"><typeRef>string</typeRef>
    <allowedValues><text>"red","green","blue"</text></allowedValues></itemDefinition>
  <decision id="dec" name="Pick">
    <decisionTable id="dt" hitPolicy="{hp}">
      <input id="i1" label="Age"><inputExpression typeRef="number"><text>Age</text></inputExpression>
        <inputValues><text>[0..10]</text></inputValues></input>
      <input id="i2" label="Colour"><inputExpression typeRef="tColour"><text>Colour</text></inputExpression></input>
      <output id="o" name="out" typeRef="string"><outputValues><text>"A","B"</text></outputValues></output>
      <rule id="r1"><inputEntry><text>&lt; 5</text></inputEntry><inputEntry><text>"red","green"</text></inputEntry>
        <outputEntry><text>"A"</text></outputEntry></rule>
      <rule id="r2"><inputEntry><text>[5..10]</text></inputEntry><inputEntry><text>-</text></inputEntry>
        <outputEntry><text>"B"</text></outputEntry></rule>
      <rule id="r3"><inputEntry><text>]3..6[</text></inputEntry><inputEntry><text>not("blue")</text></inputEntry>
        <outputEntry><text>"B"</text></outputEntry></rule>
    </decisionTable>
  </decision>
</definitions>
"""


class FEEL(unittest.TestCase):
    def test_entries(self):
        self.assertIs(di.parse_entry("-", "string"), ANY)
        self.assertEqual(di.parse_entry('"a"', "string"), Point("a"))
        self.assertEqual(di.parse_entry('"a", "b,c"', "string"), OneOf(frozenset({"a", "b,c"})))
        self.assertEqual(di.parse_entry("<= 3", "number"), Interval(-math.inf, 3, True, True))
        self.assertEqual(di.parse_entry("> -2.5", "number"), Interval(-2.5, math.inf, False, True))
        self.assertEqual(di.parse_entry("[1..2)", "number"), Interval(1, 2, True, False))
        self.assertEqual(di.parse_entry("]1..2]", "number"), Interval(1, 2, False, True))
        self.assertEqual(di.parse_entry("(1..2)", "number"), Interval(1, 2, False, False))
        self.assertEqual(di.parse_entry("7", "number"), Point(7))
        self.assertEqual(di.parse_entry("not([1..2))", "number"), Not(Interval(1, 2, True, False)))
        self.assertEqual(di.parse_entry('not("x","y")', "string"), Not(OneOf(frozenset({"x", "y"}))))

    def test_unsupported(self):
        for text, kind, reason in (("<18,>=60", "number", "numeric disjunction"),
                                   (">= Passenger.Miles", "number", "non-literal"),
                                   ("[a..b]", "number", "non-literal"),
                                   ("Complex.aString", "string", "non-literal"),
                                   ('date("2016-10-01")', "string", "non-literal")):
            with self.assertRaises(di.Unsupported) as cm:
                di.parse_entry(text, kind)
            self.assertIn(reason, cm.exception.reason)


class Import(unittest.TestCase):
    def _import(self, xml: str, **kw):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.dmn")
            with open(p, "w", encoding="utf-8") as f:
                f.write(xml)
            return di.import_file(p, d, **kw)

    def test_every_namespace(self):
        for ver, ns in NAMESPACES.items():
            ts, err = self._import(TEMPLATE.format(ns=ns, hp="UNIQUE"))
            self.assertIsNone(err)
            self.assertEqual(len(ts), 1, ver)
            t = ts[0]
            self.assertEqual((t.status, t.version, t.name), ("parsed", ver, "Pick"), t.reason)
            self.assertEqual(t.dmn.inputs[1].values, ("red", "green", "blue"))
            self.assertEqual(t.dmn.inputs[0].domain, Interval(0, 10))

    def test_analysis_and_oracle(self):
        t = self._import(TEMPLATE.format(ns=NAMESPACES["1.4"], hp="UNIQUE"))[0][0]
        a = analyse(t.dmn)
        v = violations(t.dmn, a)
        self.assertTrue(a.gaps)                  # Age < 5 with Colour blue is uncovered
        self.assertEqual(v["overlapping_pairs"], 2)
        ok, _ = di.finite_for_oracle(t.dmn)
        self.assertTrue(ok)
        self.assertTrue(all(dmn_oracle.differential(t.dmn).values()))

    def test_skip_reasons(self):
        ns = NAMESPACES["1.5"]
        ts = self._import(TEMPLATE.format(ns=ns, hp="COLLECT"))[0]
        self.assertEqual((ts[0].status, ts[0].reason), ("skipped", "hit policy COLLECT"))
        two_out = TEMPLATE.format(ns=ns, hp="UNIQUE").replace(
            '<output id="o"', '<output id="o2" name="x" typeRef="string"/><output id="o"')
        self.assertEqual(self._import(two_out)[0][0].reason, "multiple outputs")
        dated = TEMPLATE.format(ns=ns, hp="UNIQUE").replace('typeRef="number"', 'typeRef="date"')
        self.assertEqual(self._import(dated)[0][0].reason, "input type date")
        body = TEMPLATE.format(ns=ns, hp="UNIQUE").split("?>", 1)[1]
        doctype = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]>' + body
        self.assertEqual(self._import(doctype), ([], "doctype"))
        self.assertEqual(self._import(TEMPLATE.format(ns="urn:not-dmn", hp="UNIQUE")), ([], None))

    def test_booleans_and_open_strings(self):
        xml = (TEMPLATE.format(ns=NAMESPACES["1.5"], hp="FIRST")
               .replace('typeRef="tColour"', 'typeRef="boolean"')
               .replace('"red","green"', "true").replace('not("blue")', "false"))
        self.assertEqual(self._import(xml)[0][0].reason, "input type boolean")
        t = self._import(xml, booleans="enum")[0][0]
        self.assertEqual(t.status, "parsed")
        self.assertEqual(t.dmn.inputs[1].values, ("true", "false"))
        no_dom = TEMPLATE.format(ns=NAMESPACES["1.5"], hp="UNIQUE").replace(
            'typeRef="tColour"', 'typeRef="string"')
        t = self._import(no_dom)[0][0]
        self.assertEqual(set(t.dmn.inputs[1].values), {"red", "green", "blue", di.OTHER})
        self.assertEqual(t.dmn.inputs[1].values[-1], di.OTHER)

    def test_unbounded_number_and_proxy(self):
        xml = TEMPLATE.format(ns=NAMESPACES["1.5"], hp="PRIORITY").replace(
            "<inputValues><text>[0..10]</text></inputValues>", "")
        t = self._import(xml)[0][0]
        self.assertEqual(t.dmn.inputs[0].domain, Interval(-math.inf, math.inf))
        self.assertFalse(di.finite_for_oracle(t.dmn)[0])
        p = bounded_proxy(t.dmn)
        self.assertEqual(p.inputs[0].domain, Interval(2, 11))
        self.assertTrue(all(dmn_oracle.differential(p).values()))
        self.assertEqual(sorted(analyse(t.dmn).overlaps), sorted(analyse(p).overlaps))


if __name__ == "__main__":
    unittest.main()
