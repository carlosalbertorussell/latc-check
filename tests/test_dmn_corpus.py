import os
import tempfile
import unittest

from latc_check import dmn_corpus as dc

NS13 = "https://www.omg.org/spec/DMN/20191111/MODEL/"
NS11 = "http://www.omg.org/spec/DMN/20151101/dmn.xsd"


def model(body, ns=NS13, items=""):
    return (f'<definitions xmlns="{ns}" xmlns:feel="http://www.omg.org/spec/FEEL/20140401" '
            f'id="d" name="d" namespace="x">{items}{body}</definitions>').encode()


def table(inputs, rules, name="T", hp=None):
    """inputs: list of (expr, typeRef or None, inputValues text or None)."""
    ins = []
    for k, (expr, tr, iv) in enumerate(inputs):
        t = f' typeRef="{tr}"' if tr else ""
        ivx = f"<inputValues><text>{iv}</text></inputValues>" if iv is not None else ""
        ins.append(f'<input id="i{k}" label="{expr}"><inputExpression id="e{k}"{t}>'
                   f"<text>{expr}</text></inputExpression>{ivx}</input>")
    rs = []
    for k, ents in enumerate(rules):
        e = "".join(f"<inputEntry><text>{x}</text></inputEntry>" for x in ents)
        rs.append(f'<rule id="r{k}">{e}<outputEntry><text>"y"</text></outputEntry></rule>')
    h = f' hitPolicy="{hp}"' if hp else ""
    return (f'<decision id="dec" name="{name}"><decisionTable id="dt"{h}>{"".join(ins)}'
            f'<output id="o" name="out" typeRef="string"/>{"".join(rs)}</decisionTable></decision>')


def rows_of(data):
    f, t, r = dc.analyse_bytes(data, "m.dmn")
    return f, t, r


class InputValuesTest(unittest.TestCase):
    def test_input_values_declared_with_unused_value(self):
        d = model(table([("colour", "string", '"red","green","blue"')],
                        [['"red"'], ['"green"']]))
        f, t, r = rows_of(d)
        self.assertIsNone(f["error"])
        self.assertEqual(f["version"], "1.3")
        self.assertEqual(t[0]["n_rules"], 2)
        row = r[0]
        self.assertEqual(row["base"], "string")
        self.assertTrue(row["has_input_values"] and row["drools_declared"] and row["declared"])
        self.assertEqual(row["declared_values"], ["red", "green", "blue"])
        self.assertEqual(row["unused_declared"], ["blue"])
        self.assertEqual(row["unmatched_declared"], ["blue"])
        self.assertEqual(row["outside_declared"], [])

    def test_wildcard_covers_unused_value(self):
        d = model(table([("c", "string", '"a","b"')], [['"a"'], ["-"]]))
        row = rows_of(d)[2][0]
        self.assertEqual(row["unused_declared"], ["b"])
        self.assertEqual(row["unmatched_declared"], [])

    def test_not_entry_matches_rest(self):
        d = model(table([("c", "string", '"a","b","c"')], [['"a"'], ['not("a","b")']]))
        row = rows_of(d)[2][0]
        self.assertEqual(row["unused_declared"], ["c"])     # "b" is mentioned, inside not()
        self.assertEqual(row["unmatched_declared"], ["b"])  # "c" matches not(...); "b" nothing

    def test_outside_values(self):
        d = model(table([("c", "string", '"a"')], [['"a"'], ['"z"']]))
        self.assertEqual(rows_of(d)[2][0]["outside_declared"], ["z"])

    def test_nonliteral_entry_makes_unmatched_unknown(self):
        d = model(table([("c", "string", '"a","b"')], [['"a"'], ["starts with(c, \"x\")"]]))
        row = rows_of(d)[2][0]
        self.assertIsNone(row["unmatched_declared"])
        self.assertEqual(row["n_nonliteral"], 1)
        self.assertEqual(row["unused_declared"], ["b"])   # "x" counts as mentioned, "b" not

    def test_quoted_strings_in_expressions_count_as_mentioned(self):
        d = model(table([("c", "string", '"a","b"')], [['"a"'], ['? = "b"']]))
        row = rows_of(d)[2][0]
        self.assertEqual(row["mentioned"], ["a", "b"])
        self.assertEqual(row["unused_declared"], [])


class ItemDefinitionTest(unittest.TestCase):
    ITEMS = ('<itemDefinition name="tColour"><typeRef>string</typeRef>'
             '<allowedValues><text>"r","g"</text></allowedValues></itemDefinition>'
             '<itemDefinition name="tAlias"><typeRef>tColour</typeRef></itemDefinition>')

    def test_direct_allowed_values_usable_by_drools(self):
        d = model(table([("c", "tColour", None)], [['"r"']]), items=self.ITEMS)
        row = rows_of(d)[2][0]
        self.assertEqual(row["base"], "string")
        self.assertEqual(row["av_direct"], '"r","g"')
        self.assertTrue(row["drools_declared"])
        self.assertEqual(row["declared_source"], "av_direct")
        self.assertEqual(row["unused_declared"], ["g"])

    def test_chain_not_counted_for_drools(self):
        d = model(table([("c", "tAlias", None)], [['"r"']]), items=self.ITEMS)
        row = rows_of(d)[2][0]
        self.assertEqual(row["base"], "string")
        self.assertIsNone(row["av_direct"])
        self.assertEqual(row["av_chain"], '"r","g"')
        self.assertFalse(row["drools_declared"])
        self.assertTrue(row["declared"] and row["reachable_allowed"])

    def test_input_data_variable_only(self):
        body = ('<inputData id="id1" name="Colour"><variable name="Colour" typeRef="tColour"/></inputData>'
                + table([("Colour", "string", None)], [['"r"']]))
        row = rows_of(model(body, items=self.ITEMS))[2][0]
        self.assertFalse(row["drools_declared"])
        self.assertEqual(row["av_variable"], '"r","g"')
        self.assertTrue(row["declared"])

    def test_dotted_path_into_structure(self):
        items = ('<itemDefinition name="tP"><itemComponent name="status"><typeRef>string</typeRef>'
                 '<allowedValues><text>"S","M"</text></allowedValues></itemComponent></itemDefinition>')
        body = ('<inputData id="id1" name="Applicant"><variable name="Applicant" typeRef="tP"/></inputData>'
                + table([("Applicant.status", None, None)], [['"S"']]))
        row = rows_of(model(body, items=items))[2][0]
        self.assertEqual(row["base"], "string")
        self.assertEqual(row["type_source"], "variable")
        self.assertEqual(row["av_variable"], '"S","M"')
        self.assertEqual(row["unused_declared"], ["M"])

    def test_dmn15_type_constraint(self):
        items = ('<itemDefinition name="tC"><typeRef>string</typeRef>'
                 '<typeConstraint><text>"x","y"</text></typeConstraint></itemDefinition>')
        d = model(table([("c", "tC", None)], [['"x"']]),
                  ns="https://www.omg.org/spec/DMN/20230324/MODEL/", items=items)
        row = rows_of(d)[2][0]
        self.assertEqual(row["av_direct"], '"x","y"')


class TypingTest(unittest.TestCase):
    def test_undeclared_string(self):
        row = rows_of(model(table([("c", "string", None)], [['"a"']])))[2][0]
        self.assertFalse(row["declared"])
        self.assertIsNone(row["unused_declared"])
        self.assertEqual(row["mentioned"], ["a"])

    def test_untyped_inferred(self):
        rows = rows_of(model(table([("c", None, None), ("n", None, None), ("b", None, None)],
                                   [['"a"', "&lt; 3", "true"], ['"b"', "[3..5]", "false"]])))[2]
        self.assertEqual([r["base"] for r in rows], ["string", "number", "boolean"])
        self.assertEqual(rows[0]["type_source"], "inferred")

    def test_feel_prefix_and_dmn11(self):
        d = model(table([("c", "feel:string", '"a","b"')], [['"a"']]), ns=NS11)
        f, t, r = rows_of(d)
        self.assertEqual(f["version"], "1.1")
        self.assertEqual(r[0]["base"], "string")
        self.assertTrue(r[0]["has_input_values"])

    def test_numeric_input_values_not_enumerable(self):
        row = rows_of(model(table([("n", "number", "[0..10]")], [["&lt; 5"]])))[2][0]
        self.assertEqual(row["base"], "number")
        self.assertTrue(row["has_input_values"])
        self.assertIsNone(row["declared_values"])

    def test_doctype_refused(self):
        f, t, r = dc.analyse_bytes(b'<!DOCTYPE x [<!ENTITY a "b">]><definitions/>', "x")
        self.assertEqual(f["error"], "doctype")
        self.assertEqual((t, r), ([], []))

    def test_hit_policy(self):
        t = rows_of(model(table([("c", "string", None)], [['"a"']], hp="FIRST")))[1][0]
        self.assertEqual(t["hit_policy"], "FIRST")


class CorpusTest(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(dc.classify({"role": "tck"}, "a.dmn"), "tck")
        self.assertEqual(dc.classify({"role": "product"}, "x/src/test/resources/a.dmn"), "product-test")
        self.assertEqual(dc.classify({"role": "product"}, "kie-dmn-validation/src/test/a.dmn"), "analyser")
        self.assertEqual(dc.classify({"role": "product"}, "examples/loan/a.dmn"), "example")
        self.assertEqual(dc.classify({"role": "product"}, "core/src/main/a.dmn"), "other")
        self.assertEqual(dc.classify({"role": "example"}, "src/test/a.dmn"), "example")

    def test_run_dedup_and_summary(self):
        a = model(table([("c", "string", '"a","b"')], [['"a"']]))
        b = model(table([("c", "string", None), ("d", "boolean", None)], [['"a"', "true"]]))
        with tempfile.TemporaryDirectory() as tmp:
            s1, s2 = os.path.join(tmp, "s1"), os.path.join(tmp, "s2")
            os.makedirs(os.path.join(s1, "examples"))
            os.makedirs(os.path.join(s2, "src", "test"))
            for p, data in ((os.path.join(s1, "examples", "a.dmn"), a),
                            (os.path.join(s1, "examples", "b.dmn"), b),
                            (os.path.join(s2, "src", "test", "a.dmn"), a)):
                with open(p, "wb") as fh:
                    fh.write(data)
            res = dc.run([{"name": "s1", "path": s1, "role": "example"},
                          {"name": "s2", "path": s2, "role": "product"}], os.path.join(tmp, "out"))
            self.assertTrue(os.path.exists(os.path.join(tmp, "out", "inputs.csv")))
        s = res["summary"]["all"]
        self.assertEqual(s["files"], 2)
        self.assertEqual(res["duplicates_dropped_by_kind"], {"product-test": 1})
        self.assertEqual(s["string"]["inputs"], 2)
        self.assertEqual(s["string"]["input_values_pct"], 50.0)
        self.assertEqual(s["string"]["with_unused_value"], 1)
        self.assertEqual(s["boolean"]["inputs"], 1)
        self.assertEqual(s["tables_all_string_declared"], 1)
        self.assertEqual(s["tables_with_string_inputs"], 2)
        self.assertEqual(s["sources_files"], 1)          # the duplicate is kept in s1 (example)
        self.assertEqual(res["unmatched_combinations"]["combinations_unmatched"], 1)


def summary_of(data, path="m.dmn"):
    f, t, r = dc.analyse_bytes(data, path)
    for x in [f] + t + r:
        x["source"], x["kind"] = "s", "example"
    return dc.summarise([f], t, r)["all"]


class ExposureTest(unittest.TestCase):
    INPUTS = [("c", "string", None), ("n", "number", None)]

    def test_exposed_without_catch_all(self):
        d = model(table(self.INPUTS, [['"a"', "&lt; 3"], ['"b"', "-"]]))
        t = rows_of(d)[1][0]
        self.assertTrue(t["single_hit"])
        self.assertFalse(t["has_catch_all"])
        s = summary_of(d)
        self.assertEqual((s["tables_with_string_inputs"], s["exposed_tables"], s["exposed_tables_no_dash"]),
                         (1, 1, 1))
        self.assertEqual(s["string_tables_hit_policy"], {"UNIQUE": 1})

    def test_catch_all_rule_covers_column(self):
        d = model(table(self.INPUTS, [['"a"', "&lt; 3"], ["-", ""]], hp="FIRST"))
        self.assertTrue(rows_of(d)[1][0]["has_catch_all"])
        s = summary_of(d)
        self.assertEqual((s["exposed_tables"], s["exposed_tables_no_dash"]), (0, 0))

    def test_dash_without_catch_all_is_exposed_but_not_in_variant(self):
        d = model(table(self.INPUTS, [['"a"', "&lt; 3"], ["-", "&gt;= 3"]]))
        self.assertFalse(rows_of(d)[1][0]["has_catch_all"])
        s = summary_of(d)
        self.assertEqual((s["exposed_tables"], s["exposed_tables_no_dash"]), (1, 0))

    def test_collect_never_exposed(self):
        d = model(table(self.INPUTS, [['"a"', "&lt; 3"]], hp="COLLECT"))
        self.assertFalse(rows_of(d)[1][0]["single_hit"])
        s = summary_of(d)
        self.assertEqual(s["exposed_tables"], 0)
        self.assertEqual(s["string_tables_hit_policy"], {"COLLECT": 1})
        self.assertEqual(s["string_tables_single_hit"], 0)
        self.assertEqual(s["single_hit_string_inputs"], 0)

    def test_declared_input_not_exposed(self):
        d = model(table([("c", "string", '"a","b"')], [['"a"']]))
        s = summary_of(d)
        self.assertEqual(s["exposed_tables"], 0)
        self.assertEqual((s["single_hit_string_declared"], s["single_hit_string_inputs"]), (1, 1))

    def test_undeclared_column_without_literals_not_exposed(self):
        d = model(table([("c", "string", None)], [["starts with(c, x)"]]))
        self.assertEqual(summary_of(d)["exposed_tables"], 0)

    def test_strict_exposure_needs_literal_entries_only(self):
        lits = summary_of(model(table(self.INPUTS, [['"a"', "&lt; 3"], ['"b"', "-"]])))
        self.assertEqual((lits["exposed_tables"], lits["exposed_tables_strict"]), (1, 1))
        neg = summary_of(model(table(self.INPUTS, [['"LOW"', "&lt; 3"], ['not("LOW")', "&gt;= 3"]])))
        self.assertEqual((neg["exposed_tables"], neg["exposed_tables_strict"]), (1, 0))
        dash = summary_of(model(table(self.INPUTS, [['"a"', "&lt; 3"], ["-", "&gt;= 3"]])))
        self.assertEqual(dash["exposed_tables_strict"], 0)


class CopiedDeclarationTest(unittest.TestCase):
    def test_equal_sets_including_not(self):
        d = model(table([("c", "string", '"a","b","c"')], [['"a"'], ['not("b","c")']]))
        s = summary_of(d)
        self.assertEqual((s["copied_declaration"], s["copied_declaration_of"]), (1, 1))

    def test_declaration_adds_a_value(self):
        d = model(table([("c", "string", '"a","b","c"')], [['"a"'], ['"b"']]))
        self.assertEqual(summary_of(d)["copied_declaration"], 0)

    def test_rules_outside_declaration_not_equal(self):
        d = model(table([("c", "string", '"a"')], [['"a"'], ['"z"']]))
        self.assertEqual(summary_of(d)["copied_declaration"], 0)


class FixturePathTest(unittest.TestCase):
    def test_fixture_path(self):
        self.assertTrue(dc.is_fixture_path("kie-dmn-validation/dtanalysis/DTusingNOT.dmn"))
        self.assertTrue(dc.is_fixture_path("x/loan-with-enumeration-MISSING.dmn"))
        self.assertTrue(dc.is_fixture_path("gaps/a.dmn"))
        self.assertFalse(dc.is_fixture_path("examples/loan/a.dmn"))

    def test_unmatched_excluded_in_fixture_path(self):
        d = model(table([("c", "string", '"a","b"')], [['"a"']]))
        s = summary_of(d, "tests/incomplete/a.dmn")
        self.assertEqual((s["string"]["with_unmatched_value"], s["unmatched_fixture_path"]), (1, 1))
        self.assertEqual((s["with_unmatched_value_nonfixture"], s["unmatched_known_nonfixture"]), (0, 0))
        f, t, r = dc.analyse_bytes(d, "tests/incomplete/a.dmn")
        g, u, q = dc.analyse_bytes(d, "examples/a.dmn")
        c = dc.unmatched_combinations(r + q)
        self.assertEqual((c["combinations_known"], c["combinations_unmatched"]), (1, 1))
        self.assertEqual(c["combinations_with_fixture_path"], 1)
        self.assertEqual(c["combinations_unmatched_nonfixture"], 1)   # still present outside fixtures


if __name__ == "__main__":
    unittest.main()
