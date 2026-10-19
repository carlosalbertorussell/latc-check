import json
import os
import tempfile
import unittest

from latc_check import dmn_testinputs as ti
from latc_check import dmn_corpus as dc

NS13 = "https://www.omg.org/spec/DMN/20191111/MODEL/"
TC = ('<testCases xmlns="http://www.omg.org/spec/DMN/20160719/testcase" '
      'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
      '<modelName>m.dmn</modelName>{}</testCases>')


def model(body):
    return (f'<definitions xmlns="{NS13}" id="d" name="d" namespace="x">'
            '<inputData id="i1" name="Colour"><variable name="Colour" typeRef="string"/></inputData>'
            f'{body}</definitions>').encode()


def dtable(exprs, rules, hp=None, types=None, default=False):
    ins = "".join(f'<input id="in{k}"><inputExpression id="e{k}" typeRef="{(types or {}).get(k, "string")}">'
                  f'<text>{e}</text></inputExpression></input>' for k, e in enumerate(exprs))
    rs = "".join(f'<rule id="r{k}">' + "".join(f"<inputEntry><text>{x}</text></inputEntry>" for x in r)
                 + '<outputEntry><text>"y"</text></outputEntry></rule>' for k, r in enumerate(rules))
    h = f' hitPolicy="{hp}"' if hp else ""
    d = '<defaultOutputEntry><text>"z"</text></defaultOutputEntry>' if default else ""
    return f'<decisionTable id="dt"{h}>{ins}<output id="o" name="out" typeRef="string">{d}</output>{rs}</decisionTable>'


def decision(name, table, requires=(), dec_id=None):
    req = "".join(f'<informationRequirement><requiredDecision href="#{r}"/></informationRequirement>'
                  for r in requires)
    return f'<decision id="{dec_id or name}" name="{name}">{req}{table}</decision>'


def case(inputs, result="D", cid="001", desc=None, expected="ok", extra=""):
    ins = "".join(f'<inputNode name="{n}">{v}</inputNode>' for n, v in inputs)
    d = f"<description>{desc}</description>" if desc else ""
    e = ('<value xsi:nil="true"/>' if expected is None else f'<value xsi:type="xsd:string">{expected}</value>')
    return (f'<testCase id="{cid}"{extra}>{d}{ins}<resultNode name="{result}" type="decision">'
            f"<expected>{e}</expected></resultNode></testCase>")


def sval(v):
    return f'<value xsi:type="xsd:string">{v}</value>'


def run(model_body, cases):
    return ti.analyse_test_file(TC.format("".join(cases)).encode(), model(model_body), "t-test-01.xml", "m.dmn")


class ParseTest(unittest.TestCase):
    def test_values_components_lists_and_nil(self):
        data = TC.format(case([("A", sval("x")),
                               ("B", '<component name="c"><value xsi:type="xsd:decimal">3</value></component>'),
                               ("C", "<list><item>" + sval("p") + "</item></list>"),
                               ("N", '<value xsi:nil="true"/>')], desc="a test")).encode()
        tf = ti.parse_tck_tests(data)
        self.assertEqual(tf["model_name"], "m.dmn")
        c = tf["cases"][0]
        self.assertEqual(c["description"], "a test")
        vals = {i["name"]: i["value"] for i in c["inputs"]}
        self.assertEqual(vals["A"], {"t": "string", "v": "x"})
        self.assertEqual(vals["B"]["c"]["c"], {"t": "decimal", "v": "3"})
        self.assertEqual(vals["C"]["t"], "list")
        self.assertEqual(vals["N"], {"t": "null"})
        self.assertEqual(c["results"][0]["expected"], {"t": "string", "v": "ok"})

    def test_not_a_test_file(self):
        self.assertIsNone(ti.parse_tck_tests(b"<project/>"))
        self.assertIsNone(ti.parse_tck_tests(b"<!DOCTYPE x><testCases/>"))


class AdmitsTest(unittest.TestCase):
    def test_classes(self):
        e = dc.entry_info
        self.assertEqual(ti.column_admits([e('"a"'), e("-")], "c"), "wildcard")
        self.assertEqual(ti.column_admits([e('"a"'), e("")], "c"), "wildcard")
        self.assertEqual(ti.column_admits([e('"a"'), e('not("b")')], "c"), "not")
        self.assertEqual(ti.column_admits([e('"a"'), e("f(x)")], "c"), "unknown")
        self.assertEqual(ti.column_admits([e('"a"'), e('"b","d"')], "c"), "no_match")


class ResolutionTest(unittest.TestCase):
    def test_unmentioned_value_no_match_exposed(self):
        r = run(decision("D", dtable(["Colour"], [['"red"'], ['"green"']])),
                [case([("Colour", sval("blue"))], desc="no match expected", expected=None)])
        self.assertEqual(len(r["links"]), 1)
        x = r["links"][0]
        self.assertTrue(x["unmentioned"])
        self.assertEqual(x["admits"], "no_match")
        self.assertTrue(x["exposed_table"] and x["exposed_column"] and x["single_hit"])
        self.assertFalse(x["declared"])
        self.assertTrue(x["expected_null"])
        self.assertIn("no match", x["deliberate_words"])

    def test_mentioned_value_and_wildcard(self):
        r = run(decision("D", dtable(["Colour"], [['"red"'], ["-"]], hp="FIRST")),
                [case([("Colour", sval("red"))], cid="1"), case([("Colour", sval("Blue "))], cid="2")])
        a, b = r["links"]
        self.assertFalse(a["unmentioned"])
        self.assertTrue(b["unmentioned"])
        self.assertEqual(b["admits"], "wildcard")
        self.assertFalse(b["exposed_table"])          # the "-" rule is a catch-all
        self.assertEqual(b["deliberate_words"], [])

    def test_near_mention_and_declared(self):
        t = dtable(["Colour"], [['"red"'], ['"green"']]).replace(
            "</inputExpression>", '</inputExpression><inputValues><text>"red","green","Red"</text></inputValues>')
        r = run(decision("D", t, ), [case([("Colour", sval("Red"))])])
        x = r["links"][0]
        self.assertTrue(x["unmentioned"] and x["near_mention"] and x["declared"] and x["in_declared"])
        self.assertFalse(x["exposed_table"])

    def test_multi_hit_and_default_output(self):
        r = run(decision("D", dtable(["Colour"], [['"red"']], hp="COLLECT", default=True)),
                [case([("Colour", sval("blue"))])])
        x = r["links"][0]
        self.assertFalse(x["single_hit"])
        self.assertTrue(x["default_output"])
        self.assertEqual(x["admits"], "no_match")

    def test_non_string_and_null_values(self):
        r = run(decision("D", dtable(["Colour"], [['"red"']])),
                [case([("Colour", '<value xsi:type="xsd:decimal">3</value>')], cid="1"),
                 case([("Colour", '<value xsi:nil="true"/>')], cid="2")])
        self.assertEqual([x["value_type"] for x in r["links"]], ["decimal", "null"])
        self.assertFalse(any(x["unmentioned"] for x in r["links"]))

    def test_dotted_path_into_components(self):
        r = run(decision("D", dtable(["Applicant.status"], [['"single"']])),
                [case([("Applicant", '<component name="status">' + sval("widowed") + "</component>")])])
        x = r["links"][0]
        self.assertEqual((x["input"], x["path"], x["value"]), ("Applicant", ["status"], "widowed"))
        self.assertTrue(x["unmentioned"])

    def test_absent_component(self):
        r = run(decision("D", dtable(["Applicant.status"], [['"single"']])),
                [case([("Applicant", '<component name="age"><value xsi:type="xsd:decimal">3</value></component>')])])
        self.assertEqual(r["links"][0]["value_type"], "absent")

    def test_closure_excludes_unrequired_decisions(self):
        body = (decision("Other", dtable(["Colour"], [['"red"']]))
                + decision("D", dtable(["Colour"], [['"red"']]), requires=["E"])
                + decision("E", dtable(["Colour"], [['"red"']])))
        r = run(body, [case([("Colour", sval("blue"))], result="D")])
        self.assertEqual(sorted(x["table"] for x in r["links"]), ["D", "E"])
        self.assertEqual(r["closure_all"], 0)

    def test_closure_falls_back_to_all(self):
        r = run(decision("D", dtable(["Colour"], [['"red"']])), [case([("Colour", sval("red"))], result="Nope")])
        self.assertEqual(len(r["links"]), 1)
        self.assertEqual(r["closure_all"], 1)

    def test_bkm_invocation_binding(self):
        bkm = ('<businessKnowledgeModel id="b" name="Rules"><encapsulatedLogic><formalParameter name="c"/>'
               + dtable(["c"], [['"red"']]) + "</encapsulatedLogic></businessKnowledgeModel>")
        dec = ('<decision id="D" name="D"><knowledgeRequirement><requiredKnowledge href="#b"/></knowledgeRequirement>'
               '<invocation><literalExpression><text>Rules</text></literalExpression><binding>'
               '<parameter name="c"/><literalExpression><text>Colour</text></literalExpression></binding>'
               "</invocation></decision>")
        r = run(bkm + dec, [case([("Colour", sval("blue"))])])
        x = r["links"][0]
        self.assertEqual((x["input"], x["via_bkm"], x["admits"]), ("Colour", "Rules(c)", "no_match"))

    def test_bkm_feel_call(self):
        bkm = ('<businessKnowledgeModel id="b" name="My rules"><encapsulatedLogic><formalParameter name="p"/>'
               '<formalParameter name="q"/>' + dtable(["q"], [['"red"']]) + "</encapsulatedLogic></businessKnowledgeModel>")
        dec = ('<decision id="D" name="D"><literalExpression><text>My rules(1, Applicant.colour)</text>'
               "</literalExpression></decision>")
        r = run(bkm + dec, [case([("Applicant", '<component name="colour">' + sval("red") + "</component>")])])
        x = r["links"][0]
        self.assertEqual((x["input"], x["path"], x["value"]), ("Applicant", ["colour"], "red"))
        self.assertFalse(x["unmentioned"])

    def test_bkm_test_type(self):
        bkm = ('<businessKnowledgeModel id="b" name="Rules"><encapsulatedLogic><formalParameter name="c"/>'
               + dtable(["c"], [['"red"']]) + "</encapsulatedLogic></businessKnowledgeModel>")
        r = run(bkm, [case([("c", sval("blue"))], result="Rules", extra=' type="bkm" invocableName="Rules"')])
        self.assertEqual(len(r["links"]), 1)
        self.assertTrue(r["links"][0]["unmentioned"])

    def test_unresolved_reasons(self):
        body = decision("D", '<literalExpression><text>Colour</text></literalExpression>')
        r = run(body, [case([("Colour", sval("blue")), ("D", sval("x"))])])
        self.assertEqual(r["links"], [])
        self.assertEqual(r["unresolved"], {"no decision-table column reads it directly": 1,
                                           "decision value supplied as input": 1})


class RunTest(unittest.TestCase):
    def test_run_writes_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "tck", "TestCases", "x")
            os.makedirs(src)
            with open(os.path.join(src, "m.dmn"), "wb") as fh:
                fh.write(model(decision("D", dtable(["Colour"], [['"red"'], ['"green"']]))))
            for k in (1, 2):           # a byte-identical copy counts once
                with open(os.path.join(src, f"m-test-0{k}.xml"), "w", encoding="utf-8") as fh:
                    fh.write(TC.format(case([("Colour", sval("blue"))]) + case([("Colour", sval("red"))], cid="2")))
            out = os.path.join(d, "out")
            res = ti.run([{"name": "tck", "path": os.path.join(d, "tck"), "role": "tck"}], out)
            s = res["summary"]["all"]
            self.assertEqual((s["test_files"], s["test_cases"], s["links"], s["unmentioned"],
                              s["unmentioned_no_match"]), (1, 2, 2, 1, 1))
            self.assertEqual(s["distinct_unmentioned"], 1)
            self.assertEqual(res["files"][0]["kind"], "tck")
            self.assertEqual(res["files"][0]["copies"], 2)
            with open(os.path.join(out, "testinputs.json"), encoding="utf-8") as fh:
                self.assertEqual(len(json.load(fh)["instances"]), 1)
            with open(os.path.join(out, "TESTINPUTS.md"), encoding="utf-8") as fh:
                md = fh.read()
            self.assertIn("`blue`", md)
            self.assertIn("no_match", md)


if __name__ == "__main__":
    unittest.main()
