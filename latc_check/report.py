"""Print the results report (RQ2 completion correctness, RQ4 operations,
B4 DMN gap/overlap baseline).

    python run_report.py [--trials N] [--seed S] [--max-rows R] [--out DIR]

Writes ``DIR/results.json`` and ``DIR/benchmark.csv`` next to the printed
report.  Everything is seeded, so reruns reproduce the numbers except the
timings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from itertools import product

from . import __version__, bench, latc, randomized
from . import examples as ex
from .checks import Evaluator, is_sound, structural_report, summed_frequency_check
from .compare import best_block_order, compare, count_marginal_solutions
from .keying import (DigestIndex, PrimeKeyer, UnverifiedDigestIndex,
                     canonical_bytes, naive_join_key)
from .model import OUT_OF_RANGE, Row, attrs
from .reference import exact_complement


def h(title: str) -> None:
    print("\n" + title + "\n" + "-" * len(title))


def fmt_result(r) -> str:
    return (f"rows {r.n_candidate}/{r.n_expected}, missed {r.missed}, duplicates {r.duplicates}, "
            f"regenerated T0 {r.regenerated_t0}, outside space {r.outside_space}, exact {r.exact}")


def worked_example() -> dict:
    t = ex.pension_table()
    ref = exact_complement(t)
    a = latc.deficit_fill(t)
    ra = compare(a, t)
    best, tried, any_exact = best_block_order(t)
    rb = compare(latc.latc_odometer(t), t)
    pub = [c for _, c, _ in ex.PENSION_PUBLISHED_COMPLEMENT]
    merged = t.with_rows(t.rows + [Row(c) for c in a])
    free = [c for c in t.full_space() if c not in set(t.conditions())]
    n_sets = count_marginal_solutions(list(t.full_space()), latc.deficits(t))
    n_sets_disjoint = count_marginal_solutions(free, latc.deficits(t))

    h("RQ2.1  Worked example: pension rule (Table 1a)")
    print(f"Source rows: {ex.SOURCE_STATUS}.")
    print(f"T0 rows {len(t.rows)}; prod Card(Ai) = {latc.product_of_cards(t)}; "
          f"Corollary 3 missing = {latc.missing_count(t)}; exact complement = {len(ref)}.")
    print("Corollary 4 deficits:", "; ".join(
        f"{a.name} " + ", ".join(f"{v}:{k}" for v, k in d.items())
        for a, d in zip(t.attributes, latc.deficits(t))))
    print(f"Published complementary table (16 rows) == exact complement: {set(pub) == set(ref)}")
    print(f"Reading A, deficit block fill:     {fmt_result(ra)}")
    print(f"Reading A, best of {tried} block orders: {fmt_result(best)}; any order exact: {any_exact}")
    print(f"Reading B, odometer + T0 matching: {fmt_result(rb)}")
    print(f"Reading A's marginals equal the deficits: {latc.deficit_check(a, t) == []}; "
          f"source's summed-frequency check on T0 + Reading A passes: {summed_frequency_check(merged)}")
    print(f"Distinct 16-row sets of the 24-cell space with exactly these deficits: {n_sets}; "
          f"of those disjoint from T0: {n_sets_disjoint}")
    print("Reading A rows (* = already in T0):")
    t0 = set(t.conditions())
    for row in a:
        print("   ", "*" if row in t0 else " ", " ".join(f"{v:>5}" for v in row))
    return {"source_status": ex.SOURCE_STATUS, "t0_rows": len(t.rows),
            "product_of_cards": latc.product_of_cards(t), "corollary3_missing": latc.missing_count(t),
            "exact_complement": len(ref), "deficits": latc.deficits(t),
            "published_equals_exact": set(pub) == set(ref),
            "reading_A": ra.as_dict(), "reading_A_best_order": best.as_dict(),
            "reading_A_orders_tried": tried, "reading_A_any_order_exact": any_exact,
            "reading_B": rb.as_dict(), "summed_frequency_check_passes_on_A": summed_frequency_check(merged),
            "marginal_consistent_sets": n_sets, "marginal_consistent_sets_disjoint_from_T0": n_sets_disjoint}


def counterexample() -> dict:
    a, b = ex.counterexample_table(), ex.counterexample_twin()
    ra = compare(latc.deficit_fill(a), a)
    order = [("M", "F"), ("D", "I")]
    h("RQ2.2  Two-attribute counterexample")
    print(f"T0 = {a.conditions()}; exact complement = {exact_complement(a)}")
    print(f"Reading A fill = {latc.deficit_fill(a)} -> {fmt_result(ra)}")
    print(f"Twin T0 = {b.conditions()} has the same frequency table "
          f"({latc.frequency_table(a) == latc.frequency_table(b)}) and complement {exact_complement(b)}.")
    print(f"With block order {order} both get {latc.deficit_fill(a, order)}: correct for at most one.")
    print(f"Reading B: {fmt_result(compare(latc.latc_odometer(a), a))}")
    return {"reading_A": ra.as_dict(), "reading_B": compare(latc.latc_odometer(a), a).as_dict(),
            "twin_same_frequency_table": latc.frequency_table(a) == latc.frequency_table(b)}


def randomised(trials: int, seed: int) -> dict:
    out = randomized.run(trials=trials, seed=seed)
    h(f"RQ2.3  Randomised property tests ({trials} tables per scenario, seed {seed})")
    cols = ("trials", "exact_rate", "mean_missed", "mean_duplicates", "mean_regenerated_t0",
            "mean_outside_space")
    print(f"{'scenario':<12} {'method':<22} " + " ".join(f"{c:>19}" for c in cols))
    for sc, res in out.items():
        for m in randomized.METHODS:
            s = res[m]
            print(f"{sc:<12} {m:<22} " + " ".join(
                f"{s.get(c, 0):>19.3f}" if isinstance(s.get(c), float) else f"{s.get(c, 0):>19}"
                for c in cols))
        for k, v in res["count_checks"].items():
            print(f"{'':<12} {k}: {v:.3f}")
    print("latc_A_best_order only covers tables with <= 2000 block orders.")
    return out


def randomised_structured(trials: int, seed: int) -> dict:
    out = randomized.run_structured(trials=trials, seed=seed)
    h(f"RQ2.3b Structured valid-state constraints ({trials} tables, seed {seed})")
    cols = ("trials", "exact_rate", "mean_missed", "mean_duplicates", "mean_regenerated_t0",
            "mean_outside_space")
    print(f"{'method':<22} " + " ".join(f"{c:>19}" for c in cols))
    for m in randomized.METHODS:
        s = out[m]
        print(f"{m:<22} " + " ".join(
            f"{s.get(c, 0):>19.3f}" if isinstance(s.get(c), float) else f"{s.get(c, 0):>19}"
            for c in cols))
    for k, v in out["count_checks"].items():
        print(f"  {k}: {v:.3f}")
    c = out["constraints"]
    print(f"  excluded share of the product space: mean {c['excluded_share_mean']:.3f}, "
          f"min {c['excluded_share_min']:.3f}, max {c['excluded_share_max']:.3f}")
    print(f"  constraints per table {c['mean_constraints_per_table']:.2f}; kinds {c['constraint_kind_counts']}")
    print(f"  tables where a declared value is absent from V: "
          f"{c['tables_with_a_declared_value_absent_from_valid_space']:.3f}; "
          f"V a product of its values: {c['valid_space_is_product_of_its_values']:.3f}")
    return out


def operations() -> dict:
    t = ex.pension_completed()
    rep = structural_report(t)
    h("RQ4.1  Structural checks on the completed pension table (T0 + published Table 2 bis)")
    print(", ".join(f"{k} {v}" for k, v in rep.items()), "-> sound:", is_sound(rep))
    bad = t.with_rows(t.rows + [Row(t.rows[0].condition, "NO")])
    rep_bad = structural_report(bad)
    print(f"Injected conflicting duplicate: multi-hit {rep_bad['multi_hit_tuples']}, "
          f"conflicts {rep_bad['conflicting_tuples']}, sound {is_sound(rep_bad)}")

    h("RQ4.2  Out-of-domain inputs")
    probes = [
        {"Sex": "X", "Activity": "D", "ContributionYears": 35, "Age": 70},
        {"Sex": "M", "Activity": "D", "ContributionYears": 35, "Age": 130},
        {"Sex": "M", "Activity": "D", "ContributionYears": 35, "Age": 17},
        {"Sex": "M", "Activity": "D", "ContributionYears": -1, "Age": 70},
        {"Sex": "M", "Activity": "D", "ContributionYears": 35},
        {"Sex": "M", "Activity": "D", "ContributionYears": 35, "Age": 70, "Extra": 1},
        {"Sex": "M", "Activity": "D", "ContributionYears": 35.5, "Age": 70},
        {"Sex": "M", "Activity": None, "ContributionYears": 35, "Age": 70},
    ]
    routed = {}
    for b in ("dict", "sha512", "prime"):
        ev = Evaluator(t, b, ex.PENSION_BINNERS)
        ds = [ev.evaluate(p) for p in probes]
        routed[b] = sum(d.outcome == OUT_OF_RANGE and d.row is None for d in ds)
    print(f"{len(probes)} out-of-domain probes routed to '{OUT_OF_RANGE}' (never to an in-domain row): {routed}")
    print(f"Example reason: {Evaluator(t, 'sha512', ex.PENSION_BINNERS).evaluate(probes[1]).reason}")
    print(f"Assumed operating ranges: Age {ex.AGE_RANGE}, contribution years {ex.CONTRIBUTION_RANGE}.")

    h("RQ4.3  Keying")
    names = t.names
    print("Canonical bytes of T0 row 1:", canonical_bytes(names, t.rows[0].condition).decode())
    print(f"Naive ';'-join: ('a;b','c') and ('a','b;c') collide: "
          f"{naive_join_key(('a;b', 'c')) == naive_join_key(('a', 'b;c'))}; canonical bytes collide: "
          f"{canonical_bytes(('p', 'q'), ('a;b', 'c')) == canonical_bytes(('p', 'q'), ('a', 'b;c'))}")
    pk = PrimeKeyer.distinct(t.attributes)
    n_keys = len({pk.key(c) for c in t.full_space()})
    print(f"Distinct primes per (attribute, value): one-to-one {pk.is_one_to_one()}, "
          f"{n_keys}/24 distinct keys, {pk.overflow_report()}")
    amb = PrimeKeyer.ambiguous_prime_assignment(t.attributes)
    amb_keys = [amb.key(c) for c in t.full_space()]
    print(f"Ambiguous assignment (j-th value of every attribute -> j-th prime): one-to-one "
          f"{amb.is_one_to_one()}, {len(set(amb_keys))}/24 distinct keys "
          f"({24 - len(set(amb_keys))} rows lost to collisions)")
    at = attrs([(f"A{i}", tuple(range(4))) for i in range(5)])
    conds = list(product(*(a.domain for a in at)))
    trunc = lambda b: hashlib.sha512(b).digest()[:1]
    v_idx, n_idx = DigestIndex(tuple(a.name for a in at), trunc), UnverifiedDigestIndex(tuple(a.name for a in at), trunc)
    for i, c in enumerate(conds):
        v_idx.add(c, i)
        n_idx.add(c, i)
    v_ok = sum(v_idx.lookup(c) == i for i, c in enumerate(conds))
    n_ok = sum(n_idx.lookup(c) == i for i, c in enumerate(conds))
    print(f"Forced-collision test (SHA-512 truncated to 8 bits, {len(conds)} rows, "
          f"{v_idx.collisions} colliding inserts): verified index correct {v_ok}/{len(conds)}, "
          f"digest-only index correct {n_ok}/{len(conds)}")
    big = PrimeKeyer.distinct(attrs([(f"A{i}", tuple(range(8))) for i in range(10)])).overflow_report()
    print(f"Prime key size at 10 attributes x 8 values: {big['max_key_bits']} bits (fits int64: {big['fits_int64']})")
    return {"structural": rep, "conflict_injection": rep_bad, "out_of_range_routed": routed,
            "out_of_range_probes": len(probes), "prime_distinct": pk.overflow_report(),
            "ambiguous_prime_distinct_keys": len(set(amb_keys)),
            "forced_collision": {"rows": len(conds), "colliding_inserts": v_idx.collisions,
                                 "verified_correct": v_ok, "digest_only_correct": n_ok},
            "prime_10x8": big}


def benchmark(max_rows: int, csv_path: str) -> list[dict]:
    h(f"RQ4.4  Scaling benchmark (rows <= {max_rows:,})")
    res = bench.run(max_rows=max_rows, csv_path=csv_path)
    print(f"{'n':>3} {'card':>4} {'rows':>9} {'build_s':>8} {'prime_s':>8} {'MiB':>7} {'bits':>5} "
          f"{'canon_ns':>9} {'hash_ns':>8} {'probe_ns':>9} {'pkey_ns':>8} {'pprobe_ns':>9}")
    for r in res:
        print(f"{r['n_attrs']:>3} {r['card']:>4} {r['rows']:>9,} {r['build_s']:>8.3f} {r['prime_build_s']:>8.3f} "
              f"{r['peak_mib']:>7.1f} {r['prime_key_bits']:>5} {r['canon_ns']:>9} {r['hash_ns']:>8} "
              f"{r['lookup_ns']:>9} {r['prime_key_ns']:>8} {r['prime_lookup_ns']:>9}")
    for line in bench.summarise(res):
        print(line)
    print(f"CSV: {csv_path}")
    return res


def dmn_baseline(trials: int, seed: int, max_space: int, out_dir: str) -> dict:
    from . import dmn_compare as dc
    from .dmn import to_dmn_xml

    a = dc.pension_t0()
    h("B4.1  DMN gap analysis of T0 (Table 1a as 8 DMN rules)")
    print(f"DMN gap regions: {a['gap_regions']} merged ({a['gap_regions_unmerged']} before merging; "
          f"{a['gap_regions_set_grouping']} with list-entry grouping), covering {a['gap_tuples']} tuples; "
          f"COMPLETE: {a['complete_rows']} rows.")
    print(f"Expanded DMN gaps == COMPLETE's rows: {a['gap_tuples_equal_complete']}; "
          f"partly covered bins {a['partial_bins']}; overlapping pairs {a['overlap_pairs']}.")
    for r in a["regions"]:
        print("    gap:", r)

    b = dc.pension_compact()
    h("B4.2  The completed rule written compactly (wildcards and intervals)")
    print(f"Compact UNIQUE table: {b['review_compact']['rules']} rules, "
          f"{b['review_compact']['non_wildcard_cells']} non-'-' input cells; exact table: "
          f"{b['review_exact']['rules']} rows, {b['review_exact']['non_wildcard_cells']} input cells.")
    print(f"Expands to the 24 completed rows with the same outcomes: {b['expands_to_completed_table']}; "
          f"DMN gaps {b['gap_regions']}, overlaps {b['overlap_pairs']}; COMPLETE structural check: "
          f"coverage {b['structural']['coverage']}, single-hit {b['structural']['single_hit']}.")
    for name, f in b["faults"].items():
        print(f"Seeded fault {name}: DMN gaps {f['dmn_gap_regions']} region(s)/{f['dmn_gap_tuples']} tuple(s), "
              f"overlap pairs {f['dmn_overlap_pairs']} ({f['dmn_violations']} UNIQUE violations) | "
              f"COMPLETE uncovered {f['complete_uncovered']}, multi-hit {f['complete_multi_hit']}, "
              f"conflicts {f['complete_conflicts']}")

    c = dc.raw_table1()
    h("B4.3  Raw Table 1 (Age written as >=65, >=60, <60, <65)")
    print("Overlapping pairs by hit policy:", {k: v["pairs"] for k, v in c["overlaps_by_policy"].items()},
          "-> no rows conflict under UNIQUE.")
    print(f"Age elementary cells from the rule bounds: {', '.join(c['age_elementary_cells'])} "
          f"(the normalised bins <60, 60-64, >=65 up to the range end points).")
    print(f"Raw rules cover {c['raw_rules_cover_tuples']} of 24 discretised tuples; Table 1a covers "
          f"{c['table1a_covers']}. DMN gaps: {c['dmn_gap_regions']} regions / {c['dmn_gap_tuples']} tuples, "
          f"equal to COMPLETE on the discretised raw table: {c['dmn_gaps_equal_complete']}.")
    print(f"LATC on the raw labels as opaque values: Card(Age) {c['latc_label_view']['card_age']}, "
          f"prod Card {c['latc_label_view']['product']}, missing {c['latc_label_view']['missing']}.")
    for p in c["per_row"]:
        note = []
        if p["raw_tuples"] > 1:
            note.append(f"narrowed from {p['raw_tuples']} tuples")
        if p["outcome_changed"]:
            note.append("outcome changed")
        print(f"    row {p['row']}: {p['raw']:<24} => 1a {p['table1a']:<24} {'; '.join(note)}")

    d_ce = dc.counterexample()
    d = dc.random_scenarios(trials, seed)
    h(f"B4.4  Counterexample and random scenarios (same {trials} tables per scenario as RQ2.3)")
    for k, v in d_ce.items():
        print(f"Counterexample {k}: DMN gaps {v['regions']} -> exact {v['exact']}")
    print(f"{'scenario':<12} {'variant':<32} {'exact_rate':>10} {'missed':>8} {'outside':>8} "
          f"{'regions':>8} {'points':>8}")
    for sc, res in d.items():
        for v in dc.VARIANTS:
            s = res[v]
            print(f"{sc:<12} {v:<32} {s['exact_rate']:>10.3f} {s['mean_missed']:>8.3f} "
                  f"{s['mean_outside_space']:>8.3f} {s['mean_gap_regions']:>8.2f} {res['mean_missing_points']:>8.2f}")
    print("DMN has no valid-state constraint: natively, impossible states are reported as gaps;"
          " the filtered variant drops them with the exact model's constraint, outside DMN.")

    csv_path = os.path.join(out_dir, "dmn_benchmark.csv")
    e = dc.bench(max_space=max_space, csv_path=csv_path)
    h(f"B4.5  Analysis time, T0 = random half of the space (space <= {max_space:,})")
    print(f"{'n':>3} {'card':>4} {'space':>8} {'missing':>8} {'COMPLETE_s':>10} {'DMN_s':>8} {'regions':>8}")
    for r in e:
        print(f"{r['n_attrs']:>3} {r['card']:>4} {r['space']:>8,} {r['missing']:>8,} {r['complete_s']:>10.4f} "
              f"{r['dmn_s']:>8.4f} {r['dmn_gap_regions']:>8,}")
    print(f"CSV: {csv_path}")

    xml_dir = os.path.join(out_dir, "dmn")
    os.makedirs(xml_dir, exist_ok=True)
    for name, t in (("pension_t0", dc.pension_t0_dmn()), ("pension_compact", dc.pension_compact_dmn()),
                    ("pension_raw_table1", dc.raw_table1_dmn())):
        with open(os.path.join(xml_dir, name + ".dmn"), "w", encoding="utf-8") as f:
            f.write(to_dmn_xml(t, name))
    print(f"DMN 1.4 XML: {xml_dir} (pension_t0, pension_compact, pension_raw_table1)")
    f = differential(trials, seed)
    return {"t0": a, "compact": b, "raw_table1": c, "counterexample": d_ce, "random": d, "timing": e,
            "differential": f}


def differential(trials: int, seed: int) -> dict:
    from . import dmn_oracle
    s = dmn_oracle.run(trials, seed)
    h(f"B4.6  Differential test against an exhaustive oracle ({trials} random tables)")
    print("Tables of 1-3 inputs and 1-6 rules, every entry kind (points, lists, open/closed intervals,")
    print("negation), all four hit policies; the oracle evaluates every grid point directly.")
    for k in s["total"]:
        print(f"    {k:<14} agree {s['agree'][k]:>6} / {s['total'][k]}")
    print(f"Failures: {s['failures'] or 'none'}")
    return s


def _ns(lat: dict, key: str) -> str:
    v = lat.get(key)
    return f"{v['median_ns'] / 1000:.1f}/{v['p99_ns'] / 1000:.1f}" if v else "-"


def large_scale(args) -> dict:
    from . import large

    csv_path = os.path.join(args.out, "large.csv")
    h("L1  Large-scale test (behind --large)")
    out = large.run(max_rows=args.large_max_rows, csv_path=csv_path, t0_size=args.large_t0,
                    probes=args.large_probes, heavy_max_rows=args.large_heavy_max_rows,
                    log=lambda m: print(m, flush=True))
    hw = out["hardware"]
    print(f"\nHardware: {hw['cpu']}, {hw['logical_cpus']} logical CPUs, {hw['ram_total_gib']} GiB RAM "
          f"({hw['ram_available_gib_at_start']} GiB available at start), {hw['os']}, "
          f"{hw['implementation']} {hw['python']}")
    rows = out["shapes"]
    if not rows:
        print("No shape fits --large-max-rows.")
        return out

    h("L2  Build, memory and disk")
    print(f"{'shape':<17} {'rows':>11} {'COMPLETE_s':>10} {'rankstr_s':>9} {'rank_s':>7} {'rank_MiB':>8} "
          f"{'load_s':>6} {'dict':>16} {'sha512':>16} {'prime':>16} {'bits':>5}")
    for r in rows:
        def st(name):
            if f"{name}_build_s" in r:
                return f"{r[name + '_build_s']:.1f}s/{r[name + '_disk_mib']:.0f}MiB"
            return f"skip({r[name + '_projected_gib']:.1f}GiB)"
        print(f"{r['shape']:<17} {r['rows']:>11,} {r['complete_stream_s']:>10.1f} {r['complete_rank_stream_s']:>9.1f} "
              f"{r['rank_build_s']:>7.1f} {r['rank_bytes'] / 2 ** 20:>8.1f} {r['rank_load_s']:>6.2f} "
              f"{st('dict'):>16} {st('sha512'):>16} {st('prime'):>16} {r['prime_key_bits']:>5}")
    print("dict/sha512/prime: build time / pickled size, or skip(projected in-memory size). "
          "Projections use traced bytes per row from the first 100k rows.")
    for r in rows:
        skipped = [f"{k[:-8]}: {v}" for k, v in r.items() if k.endswith("_skipped")]
        if skipped:
            print(f"  {r['shape']}: " + "; ".join(skipped))
    print("Streaming COMPLETE peak traced memory: " + ", ".join(
        f"{r['shape']} {r['complete_stream_peak_kib']:.0f} KiB" for r in rows) + f" (plus the T0 set, "
          f"{rows[0]['t0_set_kib']:.0f} KiB for {rows[0]['t0_rows']} rows).")

    h(f"L3  Lookup latency, median/p99 in microseconds ({args.large_probes:,} random probes)")
    keys = [("canon_generic", "canon"), ("canon_cached", "canon$"), ("sha512_hash", "sha512"),
            ("dict_probe", "dict_pr"), ("sha512_probe_verify", "sha_pr+v"), ("prime_key", "pkey"),
            ("prime_probe", "p_pr"), ("rank_compute", "rank"), ("rank_array_index", "arr[i]"),
            ("dict_end_to_end", "DICT"), ("sha512_end_to_end", "SHA"), ("prime_end_to_end", "PRIME"),
            ("rank_end_to_end", "RANK")]
    print(f"{'shape':<17} " + " ".join(f"{lab:>10}" for _, lab in keys))
    for r in rows:
        print(f"{r['shape']:<17} " + " ".join(f"{_ns(r['latency'], k):>10}" for k, _ in keys))
    oh = rows[0]["latency"]["timer_overhead"]["median_ns"]
    print(f"canon = generic canonical_bytes, canon$ = cached fragments; capitals are end to end. "
          f"Timer overhead (empty call) {oh} ns is included; perf_counter_ns resolution on this OS may be 100 ns.")

    h("L4  DMN gap analysis at scale")
    for r in rows:
        dense = (f"dense {r['dmn_dense_s']:.1f} s, {r['dmn_dense_regions']:,} regions" if "dmn_dense_s" in r
                 else f"dense skipped ({r['dmn_dense_skipped']})")
        print(f"{r['shape']:<17} sparse T0 ({r['t0_rows']} rules): {r['dmn_sparse_s']:.2f} s, "
              f"{r['dmn_sparse_regions']:,} gap regions (cover ok {r['dmn_sparse_cover_ok']}); {dense}")

    h(f"L5  Review cost at {out['review_seconds_per_row']} s per row (illustrative)")
    print(f"{'shape':<17} {'rows to review':>15} {'hours':>12} {'person-years':>13} {'h if 1/DMN region':>18}")
    for r in rows:
        print(f"{r['shape']:<17} {r['missing_rows']:>15,} {r['review_hours']:>12,.0f} "
              f"{r['review_person_years']:>13,.1f} {r['review_hours_if_one_per_dmn_region']:>18,.0f}")
    print(f"Person-year = {out['hours_per_person_year']} h (assumption). The DMN column is a lower bound that "
          "holds only if every gap region gets a single outcome.")
    print(f"CSV: {csv_path}")
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--trials", type=int, default=1000)
    p.add_argument("--seed", type=int, default=20210101)
    p.add_argument("--max-rows", type=int, default=300_000)
    p.add_argument("--out", default="results")
    p.add_argument("--skip-bench", action="store_true")
    p.add_argument("--dmn-max-space", type=int, default=300_000,
                   help="largest condition space timed for the DMN baseline")
    p.add_argument("--large", action="store_true", help="also run the large-scale test (minutes)")
    p.add_argument("--large-only", action="store_true",
                   help="run only the large-scale test and merge it into an existing results.json")
    p.add_argument("--large-max-rows", type=int, default=70_000_000)
    p.add_argument("--large-heavy-max-rows", type=int, default=4_200_000,
                   help="largest table for the dict / SHA-512 / prime structures (memory permitting)")
    p.add_argument("--large-probes", type=int, default=100_000)
    p.add_argument("--large-t0", type=int, default=1000)
    args = p.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)

    print(f"latc_check {__version__} | Python {platform.python_version()} | {platform.platform()}")
    json_path = os.path.join(args.out, "results.json")
    if args.large_only:
        results = {}
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                results = json.load(f)
        results["large"] = large_scale(args)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nJSON: {json_path}")
        return 0
    results = {"worked_example": worked_example(), "counterexample": counterexample(),
               "randomised": randomised(args.trials, args.seed),
               "randomised_structured": randomised_structured(args.trials, args.seed),
               "operations": operations()}
    if not args.skip_bench:
        results["benchmark"] = benchmark(args.max_rows, os.path.join(args.out, "benchmark.csv"))
    results["dmn_baseline"] = dmn_baseline(args.trials, args.seed,
                                           args.dmn_max_space if not args.skip_bench else 4096, args.out)
    if args.large:
        results["large"] = large_scale(args)
    elif os.path.exists(json_path):
        # keep a large-scale section from an earlier --large / --large-only run
        try:
            with open(json_path, encoding="utf-8") as f:
                previous = json.load(f)
        except (OSError, ValueError):
            previous = {}
        if "large" in previous:
            results["large"] = previous["large"]
    with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nJSON: {os.path.join(args.out, 'results.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
