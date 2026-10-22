"""Fetch the public DMN sources of the corpus survey at the commits recorded in sources.json.

    python -I fetch_corpus.py [--sources results/corpus/sources.json] [--root ..] [--dry-run]

``run_dmn_corpus.py`` expects this layout next to the repository (``--root``, default the
parent folder):

    <root>/corpus/<owner>__<repo>/      one sparse checkout per GitHub source (.dmn files only)
    <root>/dmn-tck/                     the DMN TCK
    <root>/tools/dmn-js-verifier/       ulaurson/dmn-js, the 2016 verifier fork
    <root>/tools/corea-verifier/src/    the Corea, Blatt and Delfmann verifier (GitLab)

Each source is fetched with ``git`` at exactly the recorded commit, depth 1, with a sparse
checkout of ``*.dmn`` files (the two analyser repositories are checked out in full, as the tool
audit builds them; the DMN TCK checkout adds its ``*-test-*.xml`` test files, which
``run_dmn_testinputs.py`` reads).  Every git command runs with ``core.autocrlf=false`` and
``core.eol=lf``, and both are also set in each clone's local config, so the checked-out bytes
are those the repository stores, on Windows as on Linux: the corpus survey deduplicates files
by the SHA-256 of their bytes, and a line-ending conversion would split copies of one model.
Existing folders are left alone.  ``--dry-run`` prints the commands.
Standard library only; needs ``git`` 2.25 or later and network access.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# analyser sources kept under <root>/tools (see LOCAL_SOURCES in run_dmn_corpus.py)
TOOL_DIRS = {
    "ulaurson/dmn-js (verifier fork)": "dmn-js-verifier",
    "jonasblatt/ma-jonasblatt-dmn-verifier (Corea, Blatt, Delfmann)": os.path.join("corea-verifier", "src"),
}


# checked-out bytes equal the stored bytes on every platform (no CRLF conversion)
EOL = ["-c", "core.autocrlf=false", "-c", "core.eol=lf"]

# sparse patterns; the TCK also needs its test cases (see run_dmn_testinputs.py)
SPARSE = ["*.dmn"]
TCK_SPARSE = ["*.dmn", "*-test-*.xml"]


def target(root, src):
    name = src["name"]
    if name in TOOL_DIRS:
        return os.path.join(root, "tools", TOOL_DIRS[name]), None
    if name == "dmn-tck/tck":
        return os.path.join(root, "dmn-tck"), TCK_SPARSE
    return os.path.join(root, "corpus", name.replace("/", "__")), SPARSE


def commands(path, url, sha, sparse):
    git = ["git", *EOL]
    cmds = [[*git, "init", "-q", path],
            [*git, "-C", path, "config", "core.autocrlf", "false"],
            [*git, "-C", path, "config", "core.eol", "lf"],
            [*git, "-C", path, "remote", "add", "origin", url]]
    if sparse:
        cmds.append([*git, "-C", path, "sparse-checkout", "set", "--no-cone", *sparse])
    cmds += [[*git, "-C", path, "fetch", "-q", "--depth", "1", "origin", sha],
             [*git, "-C", path, "checkout", "-q", "FETCH_HEAD"]]
    return cmds


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sources", default=os.path.join(HERE, "results", "corpus", "sources.json"))
    ap.add_argument("--root", default=os.path.dirname(HERE))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    with open(a.sources, encoding="utf-8") as fh:
        sources = json.load(fh)["sources"]
    failed = []
    for src in sources:
        path, sparse = target(a.root, src)
        if not src.get("sha"):
            print(f"skip {src['name']}: no commit recorded")
            failed.append(src["name"])
            continue
        if os.path.isdir(path) and not a.dry_run:
            print(f"exists {path}")
            continue
        for cmd in commands(path, src["url"], src["sha"], sparse):
            if a.dry_run:
                print(" ".join(f'"{c}"' if " " in c or "*" in c else c for c in cmd))
                continue
            if subprocess.run(cmd).returncode != 0:
                print(f"failed {src['name']}: {' '.join(cmd)}")
                failed.append(src["name"])
                break
    print(f"{len(sources) - len(failed)} of {len(sources)} sources ready" if not a.dry_run
          else f"{len(sources)} sources")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
