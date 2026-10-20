"""Statistics of PROTOCOL.md section 8."""

from __future__ import annotations

from math import floor, sqrt
from statistics import NormalDist

Z95 = NormalDist().inv_cdf(0.975)


def percentile(values: list[float], p: float) -> float:
    """Hyndman and Fan type 7 (linear interpolation between order statistics)."""
    x = sorted(values)
    if not x:
        raise ValueError("no values")
    h = (len(x) - 1) * p
    lo = floor(h)
    hi = min(lo + 1, len(x) - 1)
    return x[lo] + (h - lo) * (x[hi] - x[lo])


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def describe(values: list[float]) -> dict:
    return {"mean": mean(values), "median": percentile(values, 0.5),
            "p2.5": percentile(values, 0.025), "p97.5": percentile(values, 0.975)}


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        raise ValueError("n = 0")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    # Clamped to [0, 1]: at k = 0 or k = n the bounds are 0 or 1 up to rounding.
    return max(0.0, centre - half), min(1.0, centre + half)
