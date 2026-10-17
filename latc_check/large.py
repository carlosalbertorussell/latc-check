"""Large-scale test: complete tables with millions of rows.

For each shape (number of attributes x domain sizes) this measures:

1. COMPLETE as a stream: enumerate the declared product lazily and skip T0
   (held as a set of tuples); time and traced peak memory.  The same
   complement is also streamed in rank space (integers, no tuples) to show how
   much of the cost is building Python tuples.
2. Four lookup structures over the completed table:
     dict    canonical bytes -> outcome code
     sha512  digest -> (canonical bytes, code), verified on lookup
     prime   prime-product key -> code
     rank    mixed-radix rank -> flat bytearray of codes (``rank.RankIndex``)
   dict, sha512 and prime cost 100-500 bytes per row in CPython; each is built
   only if its calibrated projection fits in 60 % of the memory available at
   run time.  Otherwise it is skipped and the projection is reported.
3. Lookup latency (median, p95, p99) over random probes, per component:
   canonicalisation (generic and cached), SHA-512, probes, prime key, rank.
4. On-disk size and load time for each structure built.
5. DMN gap analysis (``dmn.analyse``) of the sparse T0 against the full
   declared space, and of a dense table (all rows but |T0|) where it fits.
6. Review cost: rows the experts must assign, at an illustrative 30 s each.

Outcomes for the completed rows are synthetic (code = a fixed hash of the
row's rank); the experts' answers do not exist at this scale.  Only lookups
and sizes are measured, so the choice of outcome does not matter.
"""

from __future__ import annotations

import csv
import ctypes
import gc
import hashlib
import os
import pickle
import platform
import random
import shutil
import sys
import tempfile
import time
import tracemalloc
from itertools import islice, product
from math import prod
from statistics import median

from .dmn import DMNTable, Input, Point, Rule, analyse
from .keying import Canonicalizer, PrimeKeyer, canonical_bytes
from .model import Attribute
from .rank import RankIndex

OUTCOMES = ("YES", "NO", "Rv")
REVIEW_SECONDS = 30
HOURS_PER_PERSON_YEAR = 1760  # 220 working days x 8 h, an assumption

# (label, number of attributes, values per attribute)
DEFAULT_SHAPES = [
    ("1M-10x4", 10, 4),
    ("1M-20x2", 20, 2),
    ("4M-11x4", 11, 4),
    ("16.8M-12x4", 12, 4),
    ("16.8M-24x2 deep", 24, 2),
    ("16.8M-4x64 wide", 4, 64),
    ("67M-13x4", 13, 4),
]


# -- machine ----------------------------------------------------------------------

def _windows_memory():
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(m)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullTotalPhys, m.ullAvailPhys


def memory() -> tuple[int | None, int | None]:
    """(total, available) physical memory in bytes, or None if unknown."""
    try:
        if sys.platform == "win32":
            return _windows_memory()
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k] = int(v.split()[0]) * 1024
        return info["MemTotal"], info.get("MemAvailable")
    except Exception:
        return None, None


def working_set() -> int | None:
    """Current resident memory of this process in bytes, or None."""
    try:
        if sys.platform == "win32":
            class PMC(ctypes.Structure):
                _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
                    (n, ctypes.c_size_t) for n in (
                        "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                        "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                        "PagefileUsage", "PeakPagefileUsage")]
            c = PMC()
            c.cb = ctypes.sizeof(c)
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = ctypes.c_void_p
            k32.K32GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
            k32.K32GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
            return c.WorkingSetSize
        with open("/proc/self/statm") as f:
            return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
    except Exception:
        return None


def hardware() -> dict:
    cpu = platform.processor()
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                cpu = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    else:
        try:
            with open("/proc/cpuinfo") as f:
                cpu = next(l.split(":", 1)[1].strip() for l in f if l.startswith("model name"))
        except (OSError, StopIteration):
            pass
    total, avail = memory()
    return {"cpu": cpu, "logical_cpus": os.cpu_count(),
            "ram_total_gib": round(total / 2 ** 30, 1) if total else None,
            "ram_available_gib_at_start": round(avail / 2 ** 30, 1) if avail else None,
            "os": platform.platform(), "python": platform.python_version(),
            "implementation": platform.python_implementation()}


# -- helpers ----------------------------------------------------------------------

def attributes_for(n: int, c: int) -> tuple[Attribute, ...]:
    return tuple(Attribute(f"attr_{i:02d}", tuple(f"val_{j}" for j in range(c))) for i in range(n))


def code(r: int) -> int:
    """Synthetic outcome code 1..3 for the row of rank r."""
    return 1 + ((r * 2654435761) >> 16) % 3


def percentiles(ns: list[int]) -> dict:
    s = sorted(ns)
    pick = lambda q: s[min(len(s) - 1, int(q * len(s)))]
    return {"median_ns": pick(0.5), "p95_ns": pick(0.95), "p99_ns": pick(0.99)}


def timed_each(fn, items) -> list[int]:
    out, clock = [], time.perf_counter_ns
    for x in items:
        t = clock()
        fn(x)
        out.append(clock() - t)
    return out


def stream_complement(attributes, t0: set):
    """COMPLETE as a generator: declared product minus T0, never materialised."""
    for cond in product(*(a.domain for a in attributes)):
        if cond not in t0:
            yield cond


def stream_complement_ranks(size: int, t0_ranks: list[int]):
    """The same complement in rank space: range(size) minus sorted T0 ranks."""
    prev = 0
    for r in sorted(t0_ranks):
        yield from range(prev, r)
        prev = r + 1
    yield from range(prev, size)


def _dense_dmn(attributes, skip: set) -> DMNTable:
    """Every row but ``skip`` as a point-entry DMN rule (points shared)."""
    inputs = tuple(Input(a.name, values=a.domain) for a in attributes)
    points = [{v: Point(v) for v in a.domain} for a in attributes]
    rules = [Rule(tuple(points[j][v] for j, v in enumerate(cond)), "YES")
             for cond in product(*(a.domain for a in attributes)) if cond not in skip]
    return DMNTable(inputs, rules)


def _region_size(region) -> int:
    return prod(len(seg) for seg in region)


# -- calibration and gating ----------------------------------------------------------

def calibrate(attributes, n: int = 100_000, n_dense: int = 20_000) -> dict:
    """Traced bytes per row of each heavy structure, from its first ``n`` rows."""
    can, pk = Canonicalizer(attributes), PrimeKeyer.distinct(attributes)
    rows = lambda: islice(product(*(a.domain for a in attributes)), n)
    builders = {
        "dict": lambda: {can(x): code(i) for i, x in enumerate(rows())},
        "sha512": lambda: {hashlib.sha512(b).digest(): (b, code(i)) for i, b in enumerate(map(can, rows()))},
        "prime": lambda: {pk.key(x): code(i) for i, x in enumerate(rows())},
        "dmn_dense": lambda: _dense_dmn_prefix(attributes, n_dense),
    }
    out = {}
    for name, build in builders.items():
        gc.collect()
        tracemalloc.start()
        obj = build()
        if name == "dmn_dense":
            analyse(obj, merge=False)
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        del obj
        out[name] = peak / (n_dense if name == "dmn_dense" else n)
    return out


def _dense_dmn_prefix(attributes, n):
    inputs = tuple(Input(a.name, values=a.domain) for a in attributes)
    points = [{v: Point(v) for v in a.domain} for a in attributes]
    rules = [Rule(tuple(points[j][v] for j, v in enumerate(c)), "YES")
             for c in islice(product(*(a.domain for a in attributes)), n)]
    return DMNTable(inputs, rules)


def fits(need_bytes: float, fraction: float = 0.6) -> tuple[bool, float | None]:
    _, avail = memory()
    if avail is None:
        return True, None
    return need_bytes <= fraction * avail, avail


# -- one shape -------------------------------------------------------------------------

def run_shape(label: str, n: int, c: int, t0_size: int = 1000, probes: int = 100_000,
              heavy_max_rows: int = 4_200_000, dense_dmn_max_rows: int = 1_100_000,
              tmpdir: str | None = None, seed: int = 0, log=print) -> dict:
    attributes = attributes_for(n, c)
    size = c ** n
    rng = random.Random(seed)
    ri = RankIndex(attributes, OUTCOMES)
    t0_ranks = rng.sample(range(size), t0_size)
    t0 = {ri.unrank(r) for r in t0_ranks}
    res = {"shape": label, "n_attrs": n, "card": c, "rows": size, "t0_rows": t0_size,
           "missing_rows": size - t0_size}
    log(f"[{label}] {size:,} rows")

    # 1. COMPLETE, streamed
    gc.collect()
    t = time.perf_counter()
    count = sum(1 for _ in stream_complement(attributes, t0))
    res["complete_stream_s"] = time.perf_counter() - t
    assert count == size - t0_size
    t = time.perf_counter()
    count_r = sum(1 for _ in stream_complement_ranks(size, t0_ranks))
    res["complete_rank_stream_s"] = time.perf_counter() - t
    assert count_r == count
    prefix = min(size, 1_000_000)
    tracemalloc.start()
    for _ in islice(stream_complement(attributes, t0), prefix):
        pass
    res["complete_stream_peak_kib"] = tracemalloc.get_traced_memory()[1] / 1024
    tracemalloc.stop()
    res["complete_stream_peak_note"] = f"traced over the first {prefix:,} rows; T0 set built beforehand"
    res["t0_set_kib"] = (sys.getsizeof(t0) + sum(sys.getsizeof(x) for x in t0)) / 1024
    log(f"  COMPLETE stream {res['complete_stream_s']:.1f} s, rank stream {res['complete_rank_stream_s']:.1f} s")

    # 2. structures
    can, pk = Canonicalizer(attributes), PrimeKeyer.distinct(attributes)
    names = tuple(a.name for a in attributes)
    res["prime_key_bits"] = pk.overflow_report()["max_key_bits"]
    res["prime_fits_int64"] = pk.overflow_report()["fits_int64"]

    gc.collect()
    ws0 = working_set()
    t = time.perf_counter()
    ri.codes = bytearray(code(r) for r in range(size))
    res["rank_build_s"] = time.perf_counter() - t
    res["rank_bytes"] = len(ri.codes)
    res["rank_ws_delta_mib"] = ((working_set() or 0) - (ws0 or 0)) / 2 ** 20 if ws0 else None
    log(f"  rank index {res['rank_build_s']:.1f} s, {res['rank_bytes'] / 2 ** 20:.1f} MiB")

    per_row = calibrate(attributes, n=min(size, 100_000), n_dense=min(size, 20_000))
    res["calibrated_bytes_per_row"] = {k: round(v) for k, v in per_row.items()}
    structures = {}
    for name in ("dict", "sha512", "prime"):
        need = per_row[name] * size
        ok, avail = fits(need)
        res[f"{name}_projected_gib"] = need / 2 ** 30
        if size > heavy_max_rows or not ok:
            why = (f"rows > heavy_max_rows ({heavy_max_rows:,})" if size > heavy_max_rows else
                   f"projected {need / 2 ** 30:.2f} GiB > 60% of {avail / 2 ** 30:.2f} GiB available")
            res[f"{name}_skipped"] = why
            log(f"  {name}: skipped, {why}")
            continue
        gc.collect()
        ws0 = working_set()
        t = time.perf_counter()
        rows = enumerate(product(*(a.domain for a in attributes)))
        if name == "dict":
            obj = {can(x): code(i) for i, x in rows}
        elif name == "sha512":
            obj = {hashlib.sha512(b).digest(): (b, code(i)) for i, b in ((i, can(x)) for i, x in rows)}
        else:
            obj = {pk.key(x): code(i) for i, x in rows}
        res[f"{name}_build_s"] = time.perf_counter() - t
        res[f"{name}_ws_delta_mib"] = ((working_set() or 0) - (ws0 or 0)) / 2 ** 20 if ws0 else None
        assert len(obj) == size, f"{name} lost rows to key collisions"
        structures[name] = obj
        log(f"  {name}: {res[f'{name}_build_s']:.1f} s")

    # correctness on random probes
    probe_ranks = [rng.randrange(size) for _ in range(probes)]
    conds = [ri.unrank(r) for r in probe_ranks]
    assert all(ri.rank(x) == r for x, r in zip(conds, probe_ranks))
    if "dict" in structures:
        d = structures["dict"]
        res["rank_vs_dict_mismatches"] = sum(d[can(x)] != ri.codes[ri.rank(x)] for x in conds)
        res["rank_checked_against"] = "dict built in enumeration order"
    else:
        # enumeration order == rank order, checked on the first and last 100k rows
        k = min(size, probes)
        first = all(ri.rank(x) == i for i, x in enumerate(islice(product(*(a.domain for a in attributes)), k)))
        last = all(ri.rank(ri.unrank(r)) == r for r in range(size - k, size))
        res["rank_vs_dict_mismatches"] = None
        res["rank_checked_against"] = f"enumeration order on first {k:,} rows: {first}; unrank/rank on last {k:,}: {last}"
    for name in ("sha512", "prime"):
        if name in structures:
            obj = structures[name]
            if name == "sha512":
                got = [obj[hashlib.sha512(can(x)).digest()] for x in conds]
                res["sha512_vs_rank_mismatches"] = sum(cb != can(x) or v != ri.codes[ri.rank(x)]
                                                       for (cb, v), x in zip(got, conds))
            else:
                res["prime_vs_rank_mismatches"] = sum(obj[pk.key(x)] != ri.codes[ri.rank(x)] for x in conds)

    # 3. latency distributions
    lat = {}
    overhead = timed_each(lambda x: None, conds)
    lat["timer_overhead"] = percentiles(overhead)
    lat["canon_generic"] = percentiles(timed_each(lambda x: canonical_bytes(names, x), conds[:20_000]))
    lat["canon_cached"] = percentiles(timed_each(can, conds))
    cbs = [can(x) for x in conds]
    lat["sha512_hash"] = percentiles(timed_each(lambda b: hashlib.sha512(b).digest(), cbs))
    lat["rank_compute"] = percentiles(timed_each(ri.rank, conds))
    codes = ri.codes
    lat["rank_array_index"] = percentiles(timed_each(codes.__getitem__, probe_ranks))
    lat["rank_end_to_end"] = percentiles(timed_each(lambda x: codes[ri.rank(x)], conds))
    lat["prime_key"] = percentiles(timed_each(pk.key, conds))
    if "dict" in structures:
        d = structures["dict"]
        lat["dict_probe"] = percentiles(timed_each(d.__getitem__, cbs))
        lat["dict_end_to_end"] = percentiles(timed_each(lambda x: d[can(x)], conds))
    if "sha512" in structures:
        s = structures["sha512"]
        digests = [hashlib.sha512(b).digest() for b in cbs]

        def verified(pair):
            cb, dg = pair
            hit = s.get(dg)
            return hit[1] if hit is not None and hit[0] == cb else None

        lat["sha512_probe_verify"] = percentiles(timed_each(verified, list(zip(cbs, digests))))

        def sha_e2e(x):
            cb = can(x)
            hit = s.get(hashlib.sha512(cb).digest())
            return hit[1] if hit is not None and hit[0] == cb else None

        lat["sha512_end_to_end"] = percentiles(timed_each(sha_e2e, conds))
    if "prime" in structures:
        p = structures["prime"]
        pkeys = [pk.key(x) for x in conds]
        lat["prime_probe"] = percentiles(timed_each(p.__getitem__, pkeys))
        lat["prime_end_to_end"] = percentiles(timed_each(lambda x: p[pk.key(x)], conds))
    res["latency"] = lat

    # 4. disk
    tmp = tempfile.mkdtemp(prefix="latc_large_", dir=tmpdir)
    try:
        path = os.path.join(tmp, "rank.codes")
        t = time.perf_counter()
        ri.save(path)
        res["rank_save_s"] = time.perf_counter() - t
        res["rank_disk_mib"] = (os.path.getsize(path) + os.path.getsize(path + ".json")) / 2 ** 20
        t = time.perf_counter()
        loaded = RankIndex.load(path)
        res["rank_load_s"] = time.perf_counter() - t
        assert loaded.codes == ri.codes
        del loaded
        for name, obj in structures.items():
            path = os.path.join(tmp, name + ".pickle")
            t = time.perf_counter()
            with open(path, "wb") as f:
                pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
            res[f"{name}_save_s"] = time.perf_counter() - t
            res[f"{name}_disk_mib"] = os.path.getsize(path) / 2 ** 20
            del obj
            structures[name] = None
            gc.collect()
            t = time.perf_counter()
            with open(path, "rb") as f:
                back = pickle.load(f)
            res[f"{name}_load_s"] = time.perf_counter() - t
            assert len(back) == size
            del back
            os.remove(path)
            gc.collect()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    structures.clear()
    gc.collect()

    # 5. DMN
    dmn = DMNTable(tuple(Input(a.name, values=a.domain) for a in attributes),
                   [Rule(tuple(Point(v) for v in x), "YES") for x in t0])
    t = time.perf_counter()
    a = analyse(dmn)
    res["dmn_sparse_s"] = time.perf_counter() - t
    res["dmn_sparse_regions"] = len(a.gaps)
    res["dmn_sparse_regions_unmerged"] = a.raw_gaps
    res["dmn_sparse_cover_ok"] = sum(_region_size(g) for g in a.gaps) == size - t0_size
    log(f"  DMN sparse T0: {res['dmn_sparse_s']:.1f} s, {len(a.gaps):,} regions")
    del a, dmn
    need = per_row["dmn_dense"] * size
    ok, avail = fits(need)
    res["dmn_dense_projected_gib"] = need / 2 ** 30
    if size <= dense_dmn_max_rows and ok:
        gc.collect()
        dense = _dense_dmn(attributes, t0)
        t = time.perf_counter()
        a = analyse(dense)
        res["dmn_dense_s"] = time.perf_counter() - t
        res["dmn_dense_regions"] = len(a.gaps)
        res["dmn_dense_cover_ok"] = sum(_region_size(g) for g in a.gaps) == t0_size
        log(f"  DMN dense: {res['dmn_dense_s']:.1f} s")
        del a, dense
        gc.collect()
    else:
        res["dmn_dense_skipped"] = (f"rows > dense_dmn_max_rows ({dense_dmn_max_rows:,})"
                                    if size > dense_dmn_max_rows else
                                    f"projected {need / 2 ** 30:.2f} GiB > 60% of {avail / 2 ** 30:.2f} GiB available")
        log(f"  DMN dense: skipped, {res['dmn_dense_skipped']}")

    # 6. review cost
    hours = res["missing_rows"] * REVIEW_SECONDS / 3600
    res["review_hours"] = hours
    res["review_person_years"] = hours / HOURS_PER_PERSON_YEAR
    res["review_hours_if_one_per_dmn_region"] = res["dmn_sparse_regions"] * REVIEW_SECONDS / 3600
    return res


# -- grid --------------------------------------------------------------------------------

CSV_FIELDS = ["shape", "n_attrs", "card", "rows", "missing_rows", "complete_stream_s",
              "complete_rank_stream_s", "complete_stream_peak_kib", "rank_build_s", "rank_bytes",
              "rank_disk_mib", "rank_load_s", "dict_build_s", "dict_disk_mib", "dict_load_s",
              "sha512_build_s", "sha512_disk_mib", "sha512_load_s", "prime_build_s", "prime_disk_mib",
              "prime_load_s", "prime_key_bits", "prime_fits_int64", "dict_projected_gib",
              "sha512_projected_gib", "prime_projected_gib", "rank_e2e_median_ns", "rank_e2e_p99_ns",
              "dict_e2e_median_ns", "sha512_e2e_median_ns", "prime_e2e_median_ns",
              "canon_cached_median_ns", "canon_generic_median_ns", "sha512_hash_median_ns",
              "dmn_sparse_s", "dmn_sparse_regions", "dmn_dense_s", "review_hours", "review_person_years"]


def flat(r: dict) -> dict:
    lat = r.get("latency", {})
    m = lambda k, f="median_ns": lat.get(k, {}).get(f)
    row = {k: r.get(k) for k in CSV_FIELDS}
    row.update({"rank_e2e_median_ns": m("rank_end_to_end"), "rank_e2e_p99_ns": m("rank_end_to_end", "p99_ns"),
                "dict_e2e_median_ns": m("dict_end_to_end"), "sha512_e2e_median_ns": m("sha512_end_to_end"),
                "prime_e2e_median_ns": m("prime_end_to_end"), "canon_cached_median_ns": m("canon_cached"),
                "canon_generic_median_ns": m("canon_generic"), "sha512_hash_median_ns": m("sha512_hash")})
    return row


def run(shapes=DEFAULT_SHAPES, max_rows: int = 70_000_000, csv_path: str | None = None, **kw) -> dict:
    hw = hardware()
    results = []
    for label, n, c in shapes:
        if c ** n > max_rows:
            continue
        results.append(run_shape(label, n, c, **kw))
        if csv_path:  # rewrite after every shape so a long run leaves partial results
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                w.writeheader()
                w.writerows(flat(r) for r in results)
    return {"hardware": hw, "review_seconds_per_row": REVIEW_SECONDS,
            "hours_per_person_year": HOURS_PER_PERSON_YEAR, "shapes": results}
