import json
import os
import tempfile
import unittest

from latc_check import dmn_exposed_sample as des


def _table(source, path, fp, kind="example", single=True, catch_all=False, ti=0):
    return {"source": source, "path": path, "table": "T", "table_index": ti, "hit_policy": "UNIQUE",
            "n_rules": 2, "single_hit": single, "has_catch_all": catch_all, "fingerprint": fp,
            "kind": kind}


def _input(source, path, fp, mentioned=("a", "b"), declared=False, base="string", n_any=0, ti=0):
    return {"source": source, "path": path, "table_index": ti, "input_index": 0, "label": "x",
            "base": base, "declared": declared, "mentioned": list(mentioned), "n_any": n_any,
            "fingerprint": fp}


def _res():
    tables, inputs = [], []
    # fp1 in three files (one product test, two examples); fp2 once; fp3..fp6 not exposed
    for src, kind in (("p", "product-test"), ("e1", "example"), ("e2", "example")):
        tables.append(_table(src, "m.dmn", "fp1", kind))
        inputs.append(_input(src, "m.dmn", "fp1"))
    tables.append(_table("q", "n.dmn", "fp2"))
    inputs.append(_input("q", "n.dmn", "fp2", n_any=1))
    tables.append(_table("q", "a.dmn", "fp3", single=False))
    inputs.append(_input("q", "a.dmn", "fp3"))
    tables.append(_table("q", "b.dmn", "fp4", catch_all=True))
    inputs.append(_input("q", "b.dmn", "fp4"))
    tables.append(_table("q", "c.dmn", "fp5"))
    inputs.append(_input("q", "c.dmn", "fp5", declared=True))
    tables.append(_table("q", "d.dmn", "fp6"))
    inputs.append(_input("q", "d.dmn", "fp6", mentioned=()))
    return {"tables": tables, "inputs": inputs, "summary": {"all": {"exposed_tables": 4}}}


class FrameTest(unittest.TestCase):
    def test_one_entry_per_content_with_copies_and_kind_priority(self):
        f = des.exposed_frame(_res())
        self.assertEqual([e["fingerprint"] for e in f], ["fp1", "fp2"])
        self.assertEqual(f[0]["copies"], 3)
        self.assertEqual(f[0]["kind"], "example")       # example outranks product test
        self.assertEqual(f[0]["source"], "e1")          # first copy of that kind
        self.assertEqual(f[1]["columns"][0]["has_dash"], True)
        self.assertEqual(f[0]["columns"][0]["mentioned"], ["a", "b"])


class DrawTest(unittest.TestCase):
    def test_deterministic_and_without_replacement(self):
        frame = [{"fingerprint": f"{i:04d}"} for i in range(190)]
        a, b = des.draw(frame), des.draw(frame)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 50)
        self.assertEqual(len({e["fingerprint"] for e in a}), 50)
        self.assertNotEqual(a, des.draw(frame, seed=1))
        self.assertEqual(des.draw(frame[:10]), frame[:10])


class WilsonTest(unittest.TestCase):
    def test_known_values(self):
        lo, hi = des.wilson(1, 50)
        self.assertAlmostEqual(lo, 0.00354, places=4)
        self.assertAlmostEqual(hi, 0.10496, places=4)
        self.assertEqual(des.wilson(0, 0), (0.0, 1.0))
        self.assertEqual(des.wilson(0, 10)[0], 0.0)


class OutputTest(unittest.TestCase):
    def test_write_outputs(self):
        res = _res()
        with tempfile.TemporaryDirectory() as d:
            cp = os.path.join(d, "c.json")
            with open(cp, "w", encoding="utf-8") as fh:
                json.dump({"fp1": {"class": "OPEN", "domain": "OPEN", "partial_protection": False,
                                   "justification": "country"},
                           "fp2": {"class": "PARTIAL", "domain": "SYNTHETIC", "partial_protection": True,
                                   "justification": "fixture"}}, fh)
            s = des.write_outputs(res, d, cp)
            self.assertEqual(len(s), 2)
            with open(os.path.join(d, "exposed_sample.csv"), encoding="utf-8") as fh:
                txt = fh.read()
            self.assertIn("OPEN", txt)
            self.assertIn("fixture", txt)
            with open(os.path.join(d, "EXPOSED_SAMPLE.md"), encoding="utf-8") as fh:
                md = fh.read()
            self.assertIn("| OPEN | 1 | 50% |", md)
            # copy-weighted: fp1 has 3 copies, fp2 one, so 3/4 of copies are OPEN
            self.assertIn("3/4 copies = 75%", md)


if __name__ == "__main__":
    unittest.main()
