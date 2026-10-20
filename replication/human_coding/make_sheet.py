"""Build the blank human coding sheet from the blind sheet of the LLM coders.

    python -I replication/human_coding/make_sheet.py

Reads ``results/corpus/coding/blind_sheet.csv`` (the sheet the second LLM coder used, without
labels) and ``results/corpus/sources.json`` (the commit of every source), and writes
``coding_sheet_blank.csv`` next to this script.  Each local ``<repos>/...`` path becomes a link
to the file at the recorded commit, so a coder needs only a web browser; ``local_path`` keeps
the path under the folder that ``fetch_corpus.py`` fills, for coders who prefer local files.
Standard library only.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLIND = os.path.join(REPO, "results", "corpus", "coding", "blind_sheet.csv")
SOURCES = os.path.join(REPO, "results", "corpus", "sources.json")
OUT = os.path.join(HERE, "coding_sheet_blank.csv")

# where fetch_corpus.py puts each analyser source (see TOOL_DIRS there)
TOOL_DIRS = {
    "ulaurson/dmn-js (verifier fork)": "tools/dmn-js-verifier",
    "jonasblatt/ma-jonasblatt-dmn-verifier (Corea, Blatt, Delfmann)": "tools/corea-verifier/src",
}
SHEET_COLS = ["sample_no", "source", "kind", "model_url", "local_path", "table", "table_index",
              "hit_policy", "n_rules", "exposed_inputs", "mentioned_literals", "dash_in_column"]
ANSWER_COLS = ["class", "domain", "justification", "minutes"]


def prefixes(sources):
    """(local prefix, web URL prefix) per source, longest prefix first."""
    out = []
    for s in sources:
        name, url, sha = s["name"], s["url"].rstrip("/"), s["sha"]
        if name in TOOL_DIRS:
            local = TOOL_DIRS[name]
        elif name == "dmn-tck/tck":
            local = "dmn-tck"
        else:
            local = "corpus/" + name.replace("/", "__")
        web = f"{url}/-/blob/{sha}" if "gitlab" in url else f"{url}/blob/{sha}"
        out.append((local + "/", web + "/"))
    return sorted(out, key=lambda p: -len(p[0]))


def link(model_file, pref):
    rel = model_file.replace("\\", "/")
    if rel.startswith("<repos>/"):
        rel = rel[len("<repos>/"):]
    for local, web in pref:
        if rel.startswith(local):
            return web + rel[len(local):].replace(" ", "%20"), rel
    raise ValueError(f"no source for {model_file}")


def main():
    with open(SOURCES, encoding="utf-8") as fh:
        pref = prefixes(json.load(fh)["sources"])
    with open(BLIND, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, SHEET_COLS + ANSWER_COLS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            url, local = link(r["model_file"], pref)
            out = {k: r[k] for k in SHEET_COLS if k in r}
            out.update({"model_url": url, "local_path": local})
            out.update({k: "" for k in ANSWER_COLS})
            w.writerow(out)
    print(f"{len(rows)} tables -> {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
