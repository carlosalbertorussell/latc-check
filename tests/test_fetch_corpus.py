import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch_corpus as fc  # noqa: E402


class CommandsTest(unittest.TestCase):
    def test_line_endings_kept_in_every_command_and_config(self):
        cmds = fc.commands("p", "https://example.org/r", "abc", fc.SPARSE)
        for cmd in cmds:
            self.assertEqual(cmd[:5], ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf"])
        self.assertIn(["config", "core.autocrlf", "false"], [c[-3:] for c in cmds])
        self.assertIn(["config", "core.eol", "lf"], [c[-3:] for c in cmds])
        self.assertEqual(cmds[-1][-3:], ["checkout", "-q", "FETCH_HEAD"])

    def test_sparse_patterns(self):
        path, sparse = fc.target("R", {"name": "dmn-tck/tck"})
        self.assertEqual((path, sparse), (os.path.join("R", "dmn-tck"), ["*.dmn", "*-test-*.xml"]))
        self.assertEqual(fc.target("R", {"name": "a/b"}), (os.path.join("R", "corpus", "a__b"), ["*.dmn"]))
        _, sparse = fc.target("R", {"name": "ulaurson/dmn-js (verifier fork)"})
        self.assertIsNone(sparse)
        cmds = fc.commands("p", "u", "s", fc.TCK_SPARSE)
        self.assertIn(["set", "--no-cone", "*.dmn", "*-test-*.xml"], [c[-4:] for c in cmds])
        self.assertFalse(any("sparse-checkout" in c for c in fc.commands("p", "u", "s", None)))


if __name__ == "__main__":
    unittest.main()
