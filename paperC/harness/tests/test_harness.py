"""Unit tests for the Paper C harness.

Every expected number is computed by hand in the comments, on a 3 x 2 table:

    A in (a1, a2, a3), B in (b1, b2)
    D, odometer order: (a1,b1) (a1,b2) (a2,b1) (a2,b2) (a3,b1) (a3,b2)

Run from the repository root:  python3.12 -m unittest discover -s paperC/harness/tests -t .
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import tempfile
import unittest

from paperC.harness import experiment as ex
from paperC.harness.run import run_all
from paperC.harness.spec import SpecError, load_sample
from paperC.harness.stats import describe, percentile, wilson

D = [("a1", "b1"), ("a1", "b2"), ("a2", "b1"), ("a2", "b2"), ("a3", "b1"), ("a3", "b2")]


def write_sample(folder, outputs, official, exclusions=(), extra=None):
    """Write a sample folder in FORMAT.md form; ``outputs`` follows D's order."""
    spec = {"id": "TEST", "title": "t", "source": {},
            "attributes": [{"name": "A", "kind": "enum", "values": ["a1", "a2", "a3"]},
                           {"name": "B", "kind": "enum", "values": ["b1", "b2"]}],
            "output": {"name": "y", "values": ["yes", "no"]},
            "exclusions": [{"id": f"x{i}", "predicate": p} for i, p in enumerate(exclusions)],
            "fixed_inputs": {}, "notes": ""}
    with open(os.path.join(folder, "spec.json"), "w") as f:
        json.dump(spec, f)
    with open(os.path.join(folder, "ground_truth.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["A", "B", "output"])
        for c, y in zip(D, outputs):
            w.writerow([*c, y])
    with open(os.path.join(folder, "official_examples.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id", "A", "B", "output"])
        for i, (c, y) in enumerate(official):
            w.writerow([f"t{i}", *c, y])
    for name, text in (extra or {}).items():
        with open(os.path.join(folder, name), "w") as f:
            f.write(text)
    lines = []
    for name in sorted(os.listdir(folder)):
        if name != "SHA256SUMS":
            with open(os.path.join(folder, name), "rb") as f:
                lines.append(f"{hashlib.sha256(f.read()).hexdigest()}  {name}\n")
    with open(os.path.join(folder, "SHA256SUMS"), "w") as f:
        f.writelines(lines)


def runs_for(sample, examples):
    em = ex.example_metrics(sample, examples)
    out = {}
    for cond in ex.CONDITIONS:
        g, rep = ex.generate(sample, examples, cond)
        out[cond] = {**em, **ex.run_metrics(sample, em, g, rep), "G": sorted(g)}
    return out


class TempSample(unittest.TestCase):
    def make(self, *args, **kw):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d))
        write_sample(d, *args, **kw)
        return d


OFFICIAL = [(("a1", "b1"), "yes"), (("a2", "b2"), "no")]


class NoExclusions(TempSample):
    # GT: yes no yes no yes no; V = D (6 rows); examples X = {(a1,b1), (a2,b2)}.
    def setUp(self):
        self.s = load_sample(self.make(["yes", "no"] * 3, OFFICIAL))
        self.r = runs_for(self.s, list(self.s.official))

    def test_example_metrics(self):
        r = self.r["C1"]
        # A seen {a1,a2} of 3, B seen {b1,b2} of 2 -> min 2/3, one unseen value.
        self.assertEqual(r["value_coverage"], "A=2/3;B=2/2")
        self.assertAlmostEqual(r["min_value_coverage"], 2 / 3)
        self.assertEqual(r["unseen_values"], 1)
        self.assertEqual(r["true_gap"], 4)              # 6 - 2
        self.assertEqual(r["contradictory_pairs"], 0)

    def test_c1(self):
        r = self.r["C1"]
        # Observed domains {a1,a2} x {b1,b2} = 4; missing_count = 4 - 2 = 2;
        # generated (a1,b2), (a2,b1).  X u G covers 4 of 6 valid rows.
        self.assertEqual(r["G"], [("a1", "b2"), ("a2", "b1")])
        self.assertEqual(r["reported_missing"], 2)
        self.assertEqual(r["workload"], 2)
        self.assertEqual(r["covered_valid"], 4)
        self.assertAlmostEqual(r["valid_coverage"], 4 / 6)
        self.assertEqual(r["missed_valid"], 2)          # (a3,b1), (a3,b2)
        self.assertEqual(r["spurious"], 0)
        self.assertEqual(r["complete"], 0)

    def test_c2_c3(self):
        # Declared domains: 6 - 2 = 4 generated, every valid row covered.
        for cond in ("C2", "C3"):
            r = self.r[cond]
            self.assertEqual(r["workload"], 4)
            self.assertEqual(r["reported_missing"], 4)
            self.assertEqual(r["valid_coverage"], 1.0)
            self.assertEqual(r["complete"], 1)


class WithExclusion(TempSample):
    # (a3,b2) EXCLUDED by "A == 'a3' and B == 'b2'"; V has 5 rows.
    def setUp(self):
        self.s = load_sample(self.make(["yes", "no", "yes", "no", "yes", "EXCLUDED"], OFFICIAL,
                                       exclusions=["A == 'a3' and B == 'b2'"]))
        self.r = runs_for(self.s, list(self.s.official))

    def test_sets(self):
        self.assertEqual(len(self.s.V), 5)
        self.assertEqual(self.s.E, {("a3", "b2")})
        self.assertEqual(self.s.excl_disagreements, 0)   # CTRL-EXCL passes

    def test_c1(self):
        # G = (a1,b2), (a2,b1); covered = (a1,b1) (a2,b2) (a1,b2) (a2,b1) = 4 of 5.
        r = self.r["C1"]
        self.assertAlmostEqual(r["valid_coverage"], 0.8)
        self.assertEqual(r["missed_valid"], 1)           # (a3,b1)
        self.assertEqual(r["spurious"], 0)

    def test_c2(self):
        # G = (a1,b2) (a2,b1) (a3,b1) (a3,b2): coverage 5/5; (a3,b2) is spurious;
        # share 1/4.
        r = self.r["C2"]
        self.assertEqual(r["valid_coverage"], 1.0)
        self.assertEqual(r["spurious_excluded"], 1)
        self.assertEqual(r["spurious"], 1)
        self.assertAlmostEqual(r["spurious_share"], 0.25)
        self.assertEqual(r["complete"], 0)

    def test_c3(self):
        # S = D minus (a3,b2) = 5 rows; reported = 5 - 2 = 3; G = 3 rows; complete.
        r = self.r["C3"]
        self.assertEqual(r["G"], [("a1", "b2"), ("a2", "b1"), ("a3", "b1")])
        self.assertEqual(r["reported_missing"], 3)
        self.assertEqual(r["spurious"], 0)
        self.assertEqual(r["complete"], 1)

    def test_inconsistent_exclusion_is_counted(self):
        # Predicate also excludes (a3,b1), which GT labels yes: 1 disagreement.
        s = load_sample(self.make(["yes", "no", "yes", "no", "yes", "EXCLUDED"], OFFICIAL,
                                  exclusions=["A == 'a3'"]))
        self.assertEqual(s.excl_disagreements, 1)


class WithRejected(TempSample):
    # (a3,b2) EXCLUDED, (a2,b1) REJECTED.  V = (a1,b1) (a1,b2) (a2,b2) (a3,b1): 4 rows.
    def setUp(self):
        self.s = load_sample(self.make(["yes", "no", "REJECTED", "no", "yes", "EXCLUDED"], OFFICIAL,
                                       exclusions=["A == 'a3' and B == 'b2'"]))
        self.r = runs_for(self.s, list(self.s.official))

    def test_c1(self):
        # G = (a1,b2), (a2,b1).  Covered valid: (a1,b1) (a2,b2) (a1,b2) = 3 of 4.
        # (a2,b1) is REJECTED -> spurious_rejected 1, share 1/2.
        r = self.r["C1"]
        self.assertAlmostEqual(r["valid_coverage"], 0.75)
        self.assertEqual(r["missed_valid"], 1)
        self.assertEqual(r["spurious_rejected"], 1)
        self.assertAlmostEqual(r["spurious_share"], 0.5)

    def test_c2(self):
        # G = 4 rows; spurious = (a3,b2) excluded + (a2,b1) rejected = 2; share 2/4.
        r = self.r["C2"]
        self.assertEqual((r["spurious_excluded"], r["spurious_rejected"]), (1, 1))
        self.assertAlmostEqual(r["spurious_share"], 0.5)

    def test_c3_fails_h3(self):
        # The spec knows only the exclusion, so C3 still generates (a2,b1):
        # G = (a1,b2) (a2,b1) (a3,b1); coverage 1, spurious 1, share 1/3, not complete.
        r = self.r["C3"]
        self.assertEqual(r["valid_coverage"], 1.0)
        self.assertEqual(r["spurious_rejected"], 1)
        self.assertAlmostEqual(r["spurious_share"], 1 / 3)
        self.assertEqual(r["complete"], 0)

    def test_sources_draw_only_valid_rows(self):
        for n in (10, 50):
            for fn in (ex.uniform_examples, ex.zipf_examples):
                ex_rows = fn(self.s, n, 3)
                self.assertEqual(len(ex_rows), n)
                self.assertTrue(all(c in self.s.V and y == self.s.gt[c] for c, y in ex_rows))

    def test_run_all_controls(self):
        runs, controls = run_all(self.s, progress=False)
        # 1 OFFICIAL + 1 FULL + 2 sources x 7 sizes x 30 seeds = 422 example sets, x 3.
        self.assertEqual(len(runs), 422 * 3)
        by = {c["control"]: c for c in controls if c["source"] in ("-", "ALL")}
        self.assertEqual(by["CTRL-EXCL"]["pass"], 1)
        self.assertEqual(by["CTRL-PLANT"]["pass"], 1)
        self.assertEqual(by["CTRL-H3"]["pass"], 0)       # the REJECTED row
        self.assertEqual(by["CTRL-H3"]["observed"], 0)   # (a2,b1) never drawn: always generated


class ExampleMetrics(TempSample):
    def setUp(self):
        self.s = load_sample(self.make(["yes", "no", "yes", "no", "yes", "EXCLUDED"], OFFICIAL,
                                       exclusions=["A == 'a3' and B == 'b2'"]))

    def test_contradictions_and_disagreements(self):
        c, d = ("a1", "b1"), ("a2", "b2")
        rows = [(c, "yes"), (c, "no"), (c, "yes"), (d, "no"), (("a3", "b2"), "yes")]
        # c: C(3,2)=3 pairs minus C(2,2)=1 same-output pair = 2.  d alone: 0.
        self.assertEqual(ex.contradictory_pairs(rows), 2)
        m = ex.example_metrics(self.s, rows)
        # GT(c)=yes so (c,"no") disagrees; GT(a3,b2)=EXCLUDED so that row disagrees too.
        self.assertEqual(m["examples_disagree_gt"], 2)
        self.assertEqual(m["examples_invalid"], 1)       # (a3,b2) is in E
        self.assertEqual(m["n_distinct_examples"], 3)

    def test_planted_defect(self):
        # Counts of A in OFFICIAL: a1 1, a2 1, a3 0 -> v = a3, nothing removed;
        # C2 must generate (a3,b1) and (a3,b2) = |B| = 2 rows; C1 generates none.
        p = ex.planted_defect(self.s, list(OFFICIAL))
        self.assertEqual((p["value"], p["removed"], p["expected"], p["c2_generated"], p["c1_generated"]),
                         ("a3", 0, 2, 2, 0))
        self.assertTrue(p["pass"])
        # a1 2, a2 1, a3 2 -> v = a2; one row removed.
        rows = [(("a1", "b1"), "yes"), (("a2", "b1"), "yes"), (("a3", "b1"), "yes"),
                (("a1", "b2"), "no"), (("a3", "b1"), "yes")]
        p = ex.planted_defect(self.s, rows)
        self.assertEqual((p["value"], p["removed"]), ("a2", 1))
        self.assertTrue(p["pass"])
        # Tie a1 = a2 = a3 = 1 -> declared order picks a1.
        rows = [(("a3", "b1"), "yes"), (("a2", "b1"), "yes"), (("a1", "b1"), "yes")]
        self.assertEqual(ex.planted_value(self.s, rows), "a1")


class Rng(TempSample):
    def setUp(self):
        self.s = load_sample(self.make(["yes", "no"] * 3, OFFICIAL))

    def test_uniform_is_one_choices_call(self):
        want = random.Random(7).choices(self.s.V_list, k=20)
        self.assertEqual([c for c, _ in ex.uniform_examples(self.s, 20, 7)], want)
        # Same seed, smaller n: a prefix.
        self.assertEqual([c for c, _ in ex.uniform_examples(self.s, 10, 7)], want[:10])

    def test_zipf_is_shuffle_then_choices(self):
        rng = random.Random(7)
        perm = list(self.s.V_list)
        rng.shuffle(perm)
        want = rng.choices(perm, weights=[1 / k for k in range(1, 7)], k=20)
        self.assertEqual([c for c, _ in ex.zipf_examples(self.s, 20, 7)], want)


class SpecChecks(TempSample):
    def test_hash_mismatch_aborts(self):
        d = self.make(["yes", "no"] * 3, OFFICIAL)
        with open(os.path.join(d, "ground_truth.csv"), "a") as f:
            f.write("\n")
        with self.assertRaises(SpecError):
            load_sample(d)

    def test_unlisted_file_aborts(self):
        d = self.make(["yes", "no"] * 3, OFFICIAL)
        with open(os.path.join(d, "extra.txt"), "w") as f:
            f.write("x")
        with self.assertRaises(SpecError):
            load_sample(d)

    def test_order_and_labels(self):
        d = self.make(["yes", "no", "maybe", "no", "yes", "no"], OFFICIAL)
        with self.assertRaises(SpecError):          # 'maybe' is no declared output
            load_sample(d)
        d = self.make(["yes", "no"] * 3, [(("a9", "b1"), "yes")])
        with self.assertRaises(SpecError):          # undeclared label in official
            load_sample(d)

    def test_predicate_whitelist(self):
        d = self.make(["yes", "no"] * 3, OFFICIAL, exclusions=["__import__('os') is None"])
        with self.assertRaises(SpecError):
            load_sample(d)


class Stats(unittest.TestCase):
    def test_percentile_type7(self):
        x = [4, 1, 3, 2]
        # sorted 1 2 3 4; p=.025: h = 3 * .025 = .075 -> 1 + .075 = 1.075
        self.assertAlmostEqual(percentile(x, 0.025), 1.075)
        # p=.975: h = 2.925 -> 3 + .925 = 3.925
        self.assertAlmostEqual(percentile(x, 0.975), 3.925)
        self.assertAlmostEqual(percentile(x, 0.5), 2.5)
        self.assertEqual(describe([5.0])["p97.5"], 5.0)

    def test_wilson(self):
        # k=0, n=30, z=1.959964, z^2=3.841459:
        # upper = (z^2/60 + z*sqrt(z^2/3600)) / (1 + z^2/30)
        #       = (0.0640243 + 0.0640243) / 1.1280486 = 0.113513
        lo, hi = wilson(0, 30)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.113513, places=5)
        # k=15, n=30: centre 0.5, half = z*sqrt(1/120 + z^2/3600)/1.128049 = 0.16846
        lo, hi = wilson(15, 30)
        self.assertAlmostEqual(lo, 0.33154, places=4)
        self.assertAlmostEqual(hi, 0.66846, places=4)


if __name__ == "__main__":
    unittest.main()
