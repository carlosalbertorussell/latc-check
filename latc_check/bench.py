"""Scaling benchmark.

For a grid of (number of attributes n, cardinality c) the full table of c**n
rows is enumerated and indexed.  Reported per configuration:

* build_s            enumerate + canonicalise + SHA-512 + index (wall time)
* prime_build_s      prime keys + dict index
* peak_mib           tracemalloc peak during the SHA-512 build (separate run,
                     so tracing overhead does not inflate build_s)
* prime_key_bits     bit length of the largest prime-product key
* canon_ns, hash_ns, lookup_ns
                     per-lookup medians, measured separately:
                     canonical serialisation of the input tuple, SHA-512 of
                     those bytes, and the index probe with full-tuple
                     verification given a precomputed digest
* prime_key_ns, prime_lookup_ns
                     prime-key computation and dict probe, separately
"""

from __future__ import annotations

import csv
import random
import time
import tracemalloc
from itertools import product
from statistics import median

from .keying import DigestIndex, PrimeKeyer, canonical_bytes, sha512
from .model import Attribute

FIELDS = ["n_attrs", "card", "rows", "build_s", "prime_build_s", "peak_mib", "prime_key_bits",
          "fits_int64", "canon_ns", "hash_ns", "lookup_ns", "prime_key_ns", "prime_lookup_ns"]

DEFAULT_GRID = [(n, c) for n in (2, 3, 4, 6, 8, 10) for c in (2, 3, 4, 6, 8)]


def _attributes(n: int, c: int) -> tuple[Attribute, ...]:
    return tuple(Attribute(f"attr_{i}", tuple(f"val_{j}" for j in range(c))) for i in range(n))


def _build_digest(attributes) -> DigestIndex:
    idx = DigestIndex(tuple(a.name for a in attributes))
    for i, cond in enumerate(product(*(a.domain for a in attributes))):
        idx.add(cond, i)
    return idx


def _per_op_ns(fn, items, repeat: int = 5) -> float:
    """Median over ``repeat`` passes of the mean per-item time, in ns."""
    samples = []
    for _ in range(repeat):
        t = time.perf_counter_ns()
        for x in items:
            fn(x)
        samples.append((time.perf_counter_ns() - t) / len(items))
    return median(samples)


def bench_one(n: int, c: int, probes: int = 2000, seed: int = 0) -> dict:
    attributes = _attributes(n, c)
    names = tuple(a.name for a in attributes)
    rows = c ** n

    t = time.perf_counter()
    idx = _build_digest(attributes)
    build_s = time.perf_counter() - t

    pk = PrimeKeyer.distinct(attributes)
    t = time.perf_counter()
    prime_index = {pk.key(cond): i for i, cond in enumerate(product(*(a.domain for a in attributes)))}
    prime_build_s = time.perf_counter() - t
    assert len(prime_index) == rows

    tracemalloc.start()
    _build_digest(attributes)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    rng = random.Random(seed)
    conds = [tuple(rng.choice(a.domain) for a in attributes) for _ in range(probes)]
    cbs = [canonical_bytes(names, x) for x in conds]
    digests = [sha512(b) for b in cbs]
    pairs = list(zip(cbs, digests))
    pkeys = [pk.key(x) for x in conds]
    assert all(idx.lookup_bytes(b, d) is not None for b, d in pairs)

    return {
        "n_attrs": n, "card": c, "rows": rows,
        "build_s": round(build_s, 4), "prime_build_s": round(prime_build_s, 4),
        "peak_mib": round(peak / 2 ** 20, 2),
        "prime_key_bits": pk.overflow_report()["max_key_bits"],
        "fits_int64": pk.overflow_report()["fits_int64"],
        "canon_ns": round(_per_op_ns(lambda x: canonical_bytes(names, x), conds)),
        "hash_ns": round(_per_op_ns(sha512, cbs)),
        "lookup_ns": round(_per_op_ns(lambda p: idx.lookup_bytes(p[0], p[1]), pairs)),
        "prime_key_ns": round(_per_op_ns(pk.key, conds)),
        "prime_lookup_ns": round(_per_op_ns(prime_index.get, pkeys)),
    }


def run(grid=DEFAULT_GRID, max_rows: int = 300_000, csv_path: str | None = None) -> list[dict]:
    results = [bench_one(n, c) for n, c in grid if c ** n <= max_rows]
    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(results)
    return results


def summarise(results: list[dict]) -> list[str]:
    if not results:
        return ["no configurations run"]
    big = max(results, key=lambda r: r["rows"])
    lines = [
        f"{len(results)} configurations, up to {big['rows']:,} rows "
        f"({big['n_attrs']} attributes x {big['card']} values).",
        f"Largest build: {big['build_s']:.2f} s (SHA-512 index), {big['prime_build_s']:.2f} s (prime index), "
        f"peak {big['peak_mib']:.1f} MiB traced.",
        "Per-lookup medians across configurations: "
        f"canonicalise {median(r['canon_ns'] for r in results)/1000:.1f} us, "
        f"SHA-512 {median(r['hash_ns'] for r in results)/1000:.2f} us, "
        f"verified probe {median(r['lookup_ns'] for r in results)/1000:.2f} us; "
        f"prime key {median(r['prime_key_ns'] for r in results)/1000:.2f} us, "
        f"prime probe {median(r['prime_lookup_ns'] for r in results)/1000:.2f} us.",
    ]
    over = [r for r in results if not r["fits_int64"]]
    if over:
        first = min(over, key=lambda r: (r["prime_key_bits"]))
        lines.append(f"Prime keys exceed int64 in {len(over)} of {len(results)} configurations "
                     f"(first at n={first['n_attrs']}, card={first['card']}: {first['prime_key_bits']} bits).")
    else:
        lines.append("Prime keys fit int64 in every configuration run.")
    return lines
