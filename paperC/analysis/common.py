"""Shared helpers for the Paper C M2 and M6 analyses.

Standard library only; run every script with `python3.12 -I`.

* Branch files are read with `git show origin/<branch>:<path>` from the repository
  that contains this file, so no branch is checked out or modified.
* Official tests are read from the clones made by `fetch_sources.sh` in
  `paperC/analysis/_ext/` (pinned commits, checked by `ext_path`).
"""

import csv
import io
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")

CATALA_COMMIT = "2694b17ddd7c2246e207e8f077d586349ee5abea"
OPENFISCA_COMMIT = "9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb"
EXT = {"catala-examples": CATALA_COMMIT, "openfisca-aotearoa": OPENFISCA_COMMIT}

INVALID = ("EXCLUDED", "REJECTED")


# ----------------------------------------------------------------------------- git

def git_show(branch, path):
    """Text of `path` on `origin/<branch>`."""
    return subprocess.run(
        ["git", "-C", REPO, "show", f"origin/{branch}:{path}"],
        check=True, capture_output=True,
    ).stdout.decode("utf-8")


def git_lines(branch, path):
    return git_show(branch, path).splitlines()


def branch_commit(branch):
    return subprocess.run(
        ["git", "-C", REPO, "rev-parse", f"origin/{branch}"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def load_spec(branch, folder):
    return json.loads(git_show(branch, f"{folder}/spec.json"))


def load_csv(branch, path):
    return list(csv.DictReader(io.StringIO(git_show(branch, path))))


def find_line(branch, path, needle, start=1):
    """1-based number of the first line of `path` at or after `start` that contains `needle`."""
    for i, line in enumerate(git_lines(branch, path), 1):
        if i >= start and needle in line:
            return i
    raise KeyError(f"{needle!r} not in origin/{branch}:{path}")


def cite(branch, path, needle, start=1):
    """'branch:path:line' for the first line containing needle (used in reports)."""
    return f"{branch}:{path}:{find_line(branch, path, needle, start)}"


# ------------------------------------------------------------------- external sources

def ext_path(repo, *parts):
    root = os.path.join(HERE, "_ext", repo)
    if not os.path.isdir(root):
        raise SystemExit(f"missing {root}: run paperC/analysis/fetch_sources.sh first")
    head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if head != EXT[repo]:
        raise SystemExit(f"{root} is at {head}, expected {EXT[repo]}")
    return os.path.join(root, *parts)


def read_ext(repo, *parts):
    with open(ext_path(repo, *parts), encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------------- spec and table utilities

def attr_names(spec):
    return [a["name"] for a in spec["attributes"]]


def declared(spec):
    return {a["name"]: list(a["values"]) for a in spec["attributes"]}


def valid_rows(branch, folder, spec=None):
    """Valid conditions of ground_truth.csv as tuples in spec attribute order, with outputs."""
    spec = spec or load_spec(branch, folder)
    names = attr_names(spec)
    out = []
    for r in load_csv(branch, f"{folder}/ground_truth.csv"):
        if r["output"] not in INVALID:
            out.append((tuple(r[n] for n in names), r["output"]))
    return out


def ground_truth(branch, folder, spec=None):
    """dict condition-tuple -> output label (EXCLUDED/REJECTED kept)."""
    spec = spec or load_spec(branch, folder)
    names = attr_names(spec)
    return {tuple(r[n] for n in names): r["output"]
            for r in load_csv(branch, f"{folder}/ground_truth.csv")}


UNKNOWN = None  # an attribute a test cannot be placed on


def usage(spec, mapped_rows, suite_rows, valid):
    """Declared-value usage for one table.

    mapped_rows: list of dicts attr->label (the table's official_examples.csv rows).
    suite_rows:  list of dicts attr->label or UNKNOWN for every official test of the rule
                 placed on the table regardless of the slice (mapped tests included).
    valid:       list of (condition tuple, output) valid rows of the ground truth.
    Returns a dict with per-attribute and total counts and the two H1 indicators.
    """
    dec = declared(spec)
    names = attr_names(spec)
    res = {"attributes": {}, "declared_total": sum(len(v) for v in dec.values())}
    obs_m, obs_s = {}, {}
    for n in names:
        um = {r[n] for r in mapped_rows if r.get(n) is not UNKNOWN}
        us = {r[n] for r in suite_rows if r.get(n) is not UNKNOWN} | um
        bad = (um | us) - set(dec[n])
        if bad:
            raise ValueError(f"{spec['id']}.{n}: undeclared labels {sorted(bad)}")
        unk = sum(1 for r in suite_rows if r.get(n) is UNKNOWN)
        obs_m[n], obs_s[n] = um, us
        res["attributes"][n] = {
            "declared": dec[n],
            "unused_mapped": [v for v in dec[n] if v not in um],
            "unused_suite": [v for v in dec[n] if v not in us],
            "unknown_tests": unk,
        }
    res["unused_mapped_total"] = sum(len(a["unused_mapped"]) for a in res["attributes"].values())
    res["unused_suite_total"] = sum(len(a["unused_suite"]) for a in res["attributes"].values())

    def missed(obs):
        return sum(1 for c, _ in valid if any(c[i] not in obs[n] for i, n in enumerate(names)))

    res["valid_total"] = len(valid)
    res["missed_valid_mapped"] = missed(obs_m)
    res["missed_valid_suite"] = missed(obs_s)
    res["n_mapped_rows"] = len(mapped_rows)
    res["n_suite_rows"] = len(suite_rows)
    return res


def write_json(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")


# ------------------------------------------------------------- minimal YAML reader

class _Y:
    """Reader for the YAML subset used by OpenFisca test files: block mappings and
    sequences, flow sequences and mappings of scalars, `>`/`|` block scalars, comments,
    and plain, single- or double-quoted scalars. Booleans true/false, ints and floats
    are converted; dates and periods (2019-W01, 2018-12) stay strings."""

    def __init__(self, text):
        self.lines = []
        for raw in text.splitlines():
            self.lines.append(raw.rstrip("\n"))
        self.i = 0

    @staticmethod
    def _strip_comment(s):
        out, q = [], None
        for k, ch in enumerate(s):
            if q:
                if ch == q:
                    q = None
            elif ch in "'\"":
                q = ch
            elif ch == "#" and (k == 0 or s[k - 1] in " \t"):
                break
            out.append(ch)
        return "".join(out).rstrip()

    def _next(self):
        while self.i < len(self.lines):
            s = self._strip_comment(self.lines[self.i])
            if s.strip() and s.strip() != "---":
                return self.i, len(s) - len(s.lstrip(" ")), s.strip()
            self.i += 1
        return None

    @staticmethod
    def scalar(s):
        s = s.strip()
        if s == "" or s in ("~", "null", "Null", "NULL"):
            return None
        if s[0] == s[-1] and s[0] in "'\"" and len(s) >= 2:
            return s[1:-1]
        if s.startswith("["):
            return [_Y.scalar(x) for x in _Y._split_flow(s[1:-1])]
        if s.startswith("{"):
            d = {}
            for x in _Y._split_flow(s[1:-1]):
                k, v = x.split(":", 1)
                d[str(_Y.scalar(k))] = _Y.scalar(v)
            return d
        if s in ("true", "True", "TRUE"):
            return True
        if s in ("false", "False", "FALSE"):
            return False
        if re.fullmatch(r"[-+]?\d+", s):
            return int(s)
        if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?", s):
            return float(s)
        if re.fullmatch(r"\d+(_\d+)+", s):
            return int(s.replace("_", ""))
        return s

    @staticmethod
    def _split_flow(s):
        parts, depth, cur, q = [], 0, [], None
        for ch in s:
            if q:
                cur.append(ch)
                if ch == q:
                    q = None
                continue
            if ch in "'\"":
                q = ch
            elif ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        if "".join(cur).strip():
            parts.append("".join(cur))
        return [p.strip() for p in parts]

    @staticmethod
    def _key_split(s):
        q = None
        for k, ch in enumerate(s):
            if q:
                if ch == q:
                    q = None
            elif ch in "'\"":
                q = ch
            elif ch == ":" and (k + 1 == len(s) or s[k + 1] == " "):
                return s[:k].strip(), s[k + 1:].strip()
        return None

    def _block_scalar(self, ind, style):
        self.i += 1
        parts = []
        while self.i < len(self.lines):
            raw = self.lines[self.i]
            if raw.strip() and len(raw) - len(raw.lstrip(" ")) <= ind:
                break
            parts.append(raw.strip())
            self.i += 1
        sep = " " if style.startswith(">") else "\n"
        return sep.join(p for p in parts if p).strip()

    def _value_after_key(self, ind, rest):
        if rest in (">", "|", ">-", "|-", ">+", "|+"):
            return self._block_scalar(ind, rest)
        if rest:
            self.i += 1
            return self.scalar(rest)
        self.i += 1
        nxt = self._next()
        if nxt is None or nxt[1] < ind or (nxt[1] == ind and not nxt[2].startswith("- ")
                                           and nxt[2] != "-"):
            return None
        return self.block(nxt[1])

    def block(self, ind):
        first = self._next()
        if first is None:
            return None
        if first[2] == "-" or first[2].startswith("- "):
            return self._seq(ind)
        return self._map(ind)

    def _map(self, ind):
        d = {}
        while True:
            nxt = self._next()
            if nxt is None or nxt[1] < ind:
                return d
            _, cur, s = nxt
            if cur > ind:
                raise ValueError(f"line {self.i + 1}: bad indentation")
            if s.startswith("- "):
                return d
            k, rest = self._key_split(s)
            d[str(self.scalar(k))] = self._value_after_key(ind, rest)

    def _seq(self, ind):
        out = []
        while True:
            nxt = self._next()
            if nxt is None or nxt[1] < ind:
                return out
            _, cur, s = nxt
            if not (s == "-" or s.startswith("- ")) or cur != ind:
                return out
            body = s[1:].strip()
            if not body:
                self.i += 1
                n2 = self._next()
                out.append(self.block(n2[1]))
                continue
            kv = self._key_split(body)
            if kv is None:
                self.i += 1
                out.append(self.scalar(body))
                continue
            # a mapping that starts on the dash line: rewrite the line without the dash
            child = cur + (len(s) - len(body))
            self.lines[self.i] = " " * child + body
            out.append(self._map(child))


def load_yaml(text):
    return _Y(text).block(0)
