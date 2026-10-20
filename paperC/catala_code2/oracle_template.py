# ---------------------------------------------------------------------------
# Generic part shared (by copy) by every oracle.py of paperC/specs2/.
# The text between the BEGIN/END GENERIC markers is identical in every oracle.
# ---------------------------------------------------------------------------
# BEGIN GENERIC
import csv
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "catala_code2"))


def _attr_names():
    return [a["name"] for a in SPEC["attributes"]]


def excluded(row):
    for ex in SPEC["exclusions"]:
        if eval(ex["predicate"], {"__builtins__": {}}, dict(row)):
            return True
    return False


def evaluate(row):
    """Label of the decision for one row of declared labels."""
    if excluded(row):
        return "EXCLUDED"
    try:
        return run_encoding(build_inputs(row))
    except Exception as exc:  # error or assertion failure raised by the encoding
        LAST_ERRORS[tuple(row[a] for a in _attr_names())] = _describe(exc)
        return "REJECTED"


LAST_ERRORS = {}


def _describe(exc):
    import re
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(exc)).replace("\n", " ").strip()
    return "%s: %s" % (type(exc).__name__, msg)


def enumerate_rows():
    names = _attr_names()
    domains = [a["values"] for a in SPEC["attributes"]]
    for combo in itertools.product(*domains):
        yield dict(zip(names, combo))


def write_ground_truth(path):
    names = _attr_names()
    counts = {}
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(names + ["output"])
        for row in enumerate_rows():
            out = evaluate(row)
            counts[out] = counts.get(out, 0) + 1
            w.writerow([row[a] for a in names] + [out])
    return counts


def write_spec(path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(SPEC, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_official(path):
    names = _attr_names()
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id"] + names + ["output"])
        for case in OFFICIAL_CASES:
            w.writerow([case["case_id"]] + [case["row"][a] for a in names] + [case["expected"]])


def check_official():
    """Re-run each mappable official test through the encoding (original inputs)
    and through the oracle (mapped labels); both must give the asserted label."""
    ok_enc = ok_orc = 0
    for case in OFFICIAL_CASES:
        enc = case["original"]()
        orc = evaluate(case["row"])
        e_ok = enc == case["expected"]
        o_ok = orc == case["expected"]
        ok_enc += e_ok
        ok_orc += o_ok
        print("%s  %s  encoding=%s oracle=%s expected=%s" % (
            "PASS" if (e_ok and o_ok) else "FAIL", case["case_id"], enc, orc, case["expected"]))
    n = len(OFFICIAL_CASES)
    print("encoding (original inputs): %d/%d passed" % (ok_enc, n))
    print("oracle (mapped labels):     %d/%d passed" % (ok_orc, n))
    return ok_enc == n and ok_orc == n


def main(argv):
    if "--write-spec" in argv:
        write_spec(os.path.join(HERE, "spec.json"))
    if "--write-official" in argv:
        write_official(os.path.join(HERE, "official_examples.csv"))
    if "--enumerate" in argv:
        counts = write_ground_truth(os.path.join(HERE, "ground_truth.csv"))
        print(json.dumps(counts, sort_keys=True))
        kinds = {}
        for err in LAST_ERRORS.values():
            k = err.split(":")[0]
            kinds[k] = kinds.get(k, 0) + 1
        if kinds:
            print("REJECTED by exception type:", json.dumps(kinds, sort_keys=True))
            for msg in sorted(set(LAST_ERRORS.values())):
                print("  error:", msg[:300])
    if "--check-official" in argv:
        if not check_official():
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
# END GENERIC
