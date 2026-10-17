"""Row keys: canonical bytes, prime-product keys, SHA-512 digest index.

What each key does and does not guarantee
-----------------------------------------
* Canonical bytes are injective by construction: two condition tuples get the
  same bytes only if they are the same tuple.  They are the *identity* of a
  row; every other key is checked against them.
* A prime-product key is injective only if every (attribute, value) pair gets
  its own prime.  Reusing a prime across attributes (e.g. "the j-th value of
  any attribute gets the j-th prime") lets factors swap between attributes
  and collide - see ``ambiguous_prime_assignment``.  Products grow with the
  number of attributes, so ``PrimeKeyer.overflow_report`` gives bit lengths.
* SHA-512 is not injective (it maps unbounded inputs to 512 bits).  Collisions
  are not expected in practice, but a lookup that trusts the digest alone
  cannot *show* the matched row is the requested one.  ``DigestIndex``
  therefore stores the canonical bytes and verifies them on every hit.
* None of these keys says anything about outcome consistency: a unique key
  per row shows row identity, not that the outcomes assigned to rows agree
  with each other or with the experts' intent.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from itertools import count
from math import prod
from typing import Callable, Iterator, Sequence

from .model import Attribute, Condition


# -- canonical serialisation ---------------------------------------------------

_MAX_SAFE_INT = 2 ** 53 - 1


def _check_value(v):
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, int):
        if abs(v) > _MAX_SAFE_INT:
            raise ValueError("integers beyond 2**53-1 are not canonical in JCS")
        return v
    raise TypeError(f"only str, int, bool and None values are canonicalised, got {type(v).__name__}")


def canonical_bytes(names: Sequence[str], cond: Condition) -> bytes:
    """JCS-style (RFC 8785 subset) UTF-8 bytes of {attribute: value}.

    Keys sorted by UTF-16 code units as RFC 8785 requires; no whitespace;
    strings escaped as JSON.stringify does; only str/int/bool/None values.
    Values are not Unicode-normalised: declare domains in NFC.
    """
    if len(names) != len(cond):
        raise ValueError("condition length does not match attribute list")
    obj = {n: _check_value(v) for n, v in zip(names, cond)}
    keys = sorted(obj, key=lambda k: k.encode("utf-16-be"))
    body = ",".join(json.dumps(k, ensure_ascii=False) + ":" + json.dumps(obj[k], ensure_ascii=False)
                    for k in keys)
    return ("{" + body + "}").encode("utf-8")


class Canonicalizer:
    """``canonical_bytes`` for a fixed attribute list, with per-value fragments cached.

    Domains are finite, so every '"name":value' fragment can be encoded once.
    Output is byte-identical to ``canonical_bytes``; a value outside the
    declared domains falls back to it (and its validation).
    """

    def __init__(self, attributes: Sequence[Attribute]):
        self.names = tuple(a.name for a in attributes)
        self.order = sorted(range(len(attributes)), key=lambda j: self.names[j].encode("utf-16-be"))
        self.frags = [{v: (json.dumps(a.name, ensure_ascii=False) + ":" +
                           json.dumps(_check_value(v), ensure_ascii=False)).encode("utf-8")
                       for v in a.domain} for a in attributes]

    def __call__(self, cond: Condition) -> bytes:
        try:
            frags = self.frags
            return b"{" + b",".join([frags[j][cond[j]] for j in self.order]) + b"}"
        except (KeyError, IndexError, TypeError):
            return canonical_bytes(self.names, cond)


def naive_join_key(cond: Condition, sep: str = ";") -> bytes:
    """The source's SHA-mode input read literally: values joined by ';'.

    Ambiguous: ('a;b', 'c') and ('a', 'b;c') give the same string.
    Kept only to demonstrate why canonical serialisation is needed.
    """
    return sep.join(str(v) for v in cond).encode("utf-8")


# -- prime-product keys --------------------------------------------------------

def primes() -> Iterator[int]:
    found: list[int] = []
    for n in count(2):
        if all(n % p for p in found if p * p <= n):
            found.append(n)
            yield n


@dataclass
class PrimeKeyer:
    """key(t) = product of prime[(attribute, value)] over the tuple."""
    names: tuple[str, ...]
    assignment: dict  # (attribute name, value) -> prime

    @classmethod
    def distinct(cls, attributes: Sequence[Attribute]) -> "PrimeKeyer":
        """One fresh prime per (attribute, value) pair: injective."""
        gen = primes()
        return cls(tuple(a.name for a in attributes),
                   {(a.name, v): next(gen) for a in attributes for v in a.domain})

    @classmethod
    def ambiguous_prime_assignment(cls, attributes: Sequence[Attribute]) -> "PrimeKeyer":
        """The j-th value of every attribute gets the j-th prime: NOT injective."""
        ps = list(_take(primes(), max(a.card for a in attributes)))
        return cls(tuple(a.name for a in attributes),
                   {(a.name, v): ps[j] for a in attributes for j, v in enumerate(a.domain)})

    def is_one_to_one(self) -> bool:
        return len(set(self.assignment.values())) == len(self.assignment)

    def key(self, cond: Condition) -> int | None:
        """Product key, or None if some value has no prime (out of domain)."""
        try:
            return prod(self.assignment[(n, v)] for n, v in zip(self.names, cond, strict=True))
        except (KeyError, ValueError):
            return None

    def overflow_report(self) -> dict:
        """Bit length of the largest possible key and what it fits in."""
        by_attr: dict[str, list[int]] = {}
        for (n, _), p in self.assignment.items():
            by_attr.setdefault(n, []).append(p)
        largest = prod(max(by_attr[n]) for n in self.names)
        bits = largest.bit_length()
        return {"max_key_bits": bits, "max_key_digits": len(str(largest)),
                "fits_int64": bits <= 63, "fits_uint64": bits <= 64,
                "fits_float64_exact": bits <= 53}


def _take(it, n):
    for _ in range(n):
        yield next(it)


# -- SHA-512 digest index ------------------------------------------------------

def sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


@dataclass
class DigestIndex:
    """digest -> [(canonical bytes, payload)], verified on lookup.

    ``hash_fn`` is injectable so tests can force collisions with a truncated
    hash and show that verification still returns the right row.
    """
    names: tuple[str, ...]
    hash_fn: Callable[[bytes], bytes] = sha512
    buckets: dict = field(default_factory=dict)
    collisions: int = 0  # distinct canonical tuples sharing a digest

    def add(self, cond: Condition, payload) -> None:
        cb = canonical_bytes(self.names, cond)
        bucket = self.buckets.setdefault(self.hash_fn(cb), [])
        for existing, _ in bucket:
            if existing == cb:
                raise KeyError(f"duplicate condition tuple {cond!r}")
        if bucket:
            self.collisions += 1
        bucket.append((cb, payload))

    def lookup_bytes(self, cb: bytes, digest: bytes | None = None):
        bucket = self.buckets.get(digest if digest is not None else self.hash_fn(cb), ())
        for existing, payload in bucket:
            if existing == cb:          # full-tuple verification
                return payload
        return None

    def lookup(self, cond: Condition):
        try:
            cb = canonical_bytes(self.names, cond)
        except (TypeError, ValueError):
            return None
        return self.lookup_bytes(cb)


@dataclass
class UnverifiedDigestIndex(DigestIndex):
    """Digest-only lookup (what the source's SHA mode describes). For contrast."""

    def add(self, cond: Condition, payload) -> None:
        d = self.hash_fn(canonical_bytes(self.names, cond))
        if d in self.buckets:
            self.collisions += 1
        self.buckets[d] = [(b"", payload)]  # last writer wins, bytes not kept

    def lookup_bytes(self, cb: bytes, digest: bytes | None = None):
        bucket = self.buckets.get(digest if digest is not None else self.hash_fn(cb))
        return bucket[0][1] if bucket else None
