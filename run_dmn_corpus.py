"""Survey of domain declarations in public DMN models: run ``latc_check.dmn_corpus``.

    python -I run_dmn_corpus.py [--corpus ../corpus] [--tck ../dmn-tck] [--out results/corpus]

The sources are shallow, sparse clones (``.dmn`` files only) of public GitHub
repositories, made outside this repository (see ``SOURCES`` for the list and
each source's role).  This script records each clone's commit SHA in
``results/corpus/sources.json`` and writes ``results.json``, ``inputs.csv``
and ``SUMMARY.md`` there.  Standard library only (plus ``git`` for the SHAs).
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # also works under python -I

from latc_check import dmn_corpus  # noqa: E402

# (owner/repo, role).  role: tck | analyser | product | example
SOURCES = [
    ("dmn-tck/tck", "tck"),
    ("red6/dmn-check", "analyser"),
    ("apache/incubator-kie-drools", "product"),
    ("apache/incubator-kie-kogito-runtimes", "product"),
    ("apache/incubator-kie-kogito-apps", "product"),
    ("apache/incubator-kie-tools", "product"),
    ("camunda/camunda-bpm-platform", "product"),
    ("operaton/operaton", "product"),
    ("camunda/camunda", "product"),
    ("camunda/dmn-scala", "product"),
    ("camunda/camunda-modeler", "product"),
    ("camunda/camunda-modeler-plugins", "product"),
    ("bpmn-io/dmn-js", "product"),
    ("bpmn-io/dmn-js-properties-panel", "product"),
    ("flowable/flowable-engine", "product"),
    ("goldmansachs/jdmn", "product"),
    ("adamecr/Common.DMN.Engine", "product"),
    ("DecisionToolkit/dsntk", "product"),
    ("russellmcdonell/pyDMNrules", "product"),
    ("camunda-community-hub/camunda-dmn-tester", "product"),
    ("powerflows/powerflows-dmn", "product"),
    ("apache/incubator-kie-kogito-examples", "example"),
    ("camunda/camunda-bpm-examples", "example"),
    ("bpmn-io/dmn-js-examples", "example"),
    ("camunda/camunda-8-tutorials", "example"),
    ("camunda-community-hub/camunda-8-examples", "example"),
    ("kiegroup/kie-wb-playground", "example"),
    ("camunda-consulting/code", "example"),
    ("operaton/operaton-examples", "example"),
    ("redhat-cop/businessautomation-cop", "example"),
    ("kiegroup/trusty-ai-sandbox", "example"),
    ("steffenbrand/dmn-decision-tables", "example"),
    ("DigiBP/digibp-saentis", "example"),
    ("NPDeehan/Risk-Analysis-DMN-OpenAI-Camunda", "example"),
    ("gautric/KYC-DMN", "example"),
    ("gautric/dmn-lambda", "example"),
    ("tarilabs/dmn-framingham-cvd-risk-score", "example"),
    ("tarilabs/dmn-aldrete", "example"),
    ("tasso94/camunda-dmn-feel-1.2-example", "example"),
    ("holunda-io/camunda-decision", "example"),
    ("holunda-io/camunda-example-tenant-specific-dmn", "example"),
    ("Miragon/design-iq", "example"),
    ("cogneon/lernos-prozessmodellierung", "example"),
    ("AbSamrah/SmartLoanSystem", "example"),
    ("darioajr/resgate-dmn", "example"),
    ("caponetto/streaming-dmn-kafka", "example"),
    ("russellmcdonell/DecisionCentral", "example"),
    ("CodeForPhilly/benefit-decision-toolkit", "example"),
]


# analyser fixtures already present next to this repository (from earlier tool audits):
# (name, role, path relative to ../tools, url, sha when the copy is not a git checkout)
LOCAL_SOURCES = [
    ("ulaurson/dmn-js (verifier fork)", "analyser", "dmn-js-verifier",
     "https://github.com/ulaurson/dmn-js", None),
    ("jonasblatt/ma-jonasblatt-dmn-verifier (Corea, Blatt, Delfmann)", "analyser",
     os.path.join("corea-verifier", "src"),
     "https://gitlab.uni-koblenz.de/jonasblatt/ma-jonasblatt-dmn-verifier",
     "5b307e8481170d37b63a9b256a45c3c38c7fa50c"),
]


# product repositories whose "examples" folders hold engine test models, not business examples
EXAMPLES_ARE_TESTS = {"DecisionToolkit/dsntk"}


def _git(path, *args):
    try:
        return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True,
                              timeout=60).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def build_sources(corpus, tck, tools):
    out, missing = [], []
    for repo, role in SOURCES:
        path = tck if repo == "dmn-tck/tck" else os.path.join(corpus, repo.replace("/", "__"))
        if not os.path.isdir(path):
            missing.append(repo)
            continue
        out.append({"name": repo, "url": f"https://github.com/{repo}", "role": role,
                    "examples_are_tests": repo in EXAMPLES_ARE_TESTS,
                    "path": os.path.abspath(path), "sha": _git(path, "rev-parse", "HEAD"),
                    "dmn_files_in_checkout": sum(f.lower().endswith(".dmn")
                                                 for _, _, fs in os.walk(path) for f in fs)})
    for name, role, rel, url, sha in LOCAL_SOURCES:
        path = os.path.join(tools, rel)
        if not os.path.isdir(path):
            missing.append(name)
            continue
        out.append({"name": name, "url": url, "role": role, "path": os.path.abspath(path),
                    "sha": sha or _git(path, "rev-parse", "HEAD"),
                    "dmn_files_in_checkout": sum(f.lower().endswith(".dmn")
                                                 for _, _, fs in os.walk(path) for f in fs)})
    return out, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", default=os.path.join(HERE, "..", "corpus"))
    ap.add_argument("--tck", default=os.path.join(HERE, "..", "dmn-tck"))
    ap.add_argument("--tools", default=os.path.join(HERE, "..", "tools"))
    ap.add_argument("--out", default=os.path.join(HERE, "results", "corpus"))
    a = ap.parse_args()
    sources, missing = build_sources(a.corpus, a.tck, a.tools)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "sources.json"), "w", encoding="utf-8") as fh:
        json.dump({"sources": [{k: v for k, v in s.items() if k != "path"} for s in sources],
                   "missing": missing}, fh, indent=1)
    res = dmn_corpus.run(sources, a.out)
    with open(os.path.join(a.out, "SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write(dmn_corpus.summary_md(res, sources, missing))
    for g, v in res["summary"].items():
        st = v.get("string", {})
        print(f"{g:13s} files={v['files']:5d} tables={v['decision_tables']:5d} "
              f"string={st.get('inputs', 0):5d} iv={st.get('input_values_pct')}% "
              f"av={st.get('reachable_allowed_pct')}% drools={st.get('drools_usable_pct')}% "
              f"all-decl={v.get('tables_all_string_declared_pct')}% unused={st.get('with_unused_value_pct')}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
