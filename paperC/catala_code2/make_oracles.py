"""Assemble paperC/specs2/<ID>/oracle.py from the parts in oracle_parts/.

Each oracle.py is self-contained apart from the generated Catala Python in
paperC/catala_code2/{generated,runtime}. Run: python3 make_oracles.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "oracle_parts")
SPECS = os.path.normpath(os.path.join(HERE, "..", "specs2"))

LAYOUT = {
    "FR-APL-1": ["apl_common.py", "fr_dates.py", "fr_apl_1.py"],
    "FR-APL-2": ["apl_common.py", "fr_dates.py", "fr_apl_2.py"],
    "FR-APL-3": ["apl_common.py", "fr_dates.py", "fr_apl_3.py"],
    "FR-APL-4": ["apl_common.py", "fr_apl_4.py"],
    "FR-APL-5": ["apl_common.py", "fr_apl_5.py"],
    "US-121-1": ["us_common.py", "us_121_1.py"],
    "US-121-2": ["us_common.py", "us_121_2.py"],
}

HEADER = '''#!/usr/bin/env python3
"""Oracle for sample {id} (Paper C, second coder, paperC/specs2/{id}).

Usage:
  python3 oracle.py --enumerate        # writes ground_truth.csv
  python3 oracle.py --check-official   # official tests: encoding vs oracle
  python3 oracle.py --write-spec --write-official   # regenerate spec.json, official_examples.csv

Assembled by paperC/catala_code2/make_oracles.py from paperC/catala_code2/oracle_parts/.
Requires Python >= 3.12 (Catala 1.3.0 runtime).
"""
'''


def main():
    generic = open(os.path.join(HERE, "oracle_template.py"), encoding="utf-8").read()
    for sid, parts in LAYOUT.items():
        if not all(os.path.exists(os.path.join(PARTS, p)) for p in parts):
            print("skip", sid)
            continue
        body = [HEADER.format(id=sid)]
        for p in parts:
            body.append("\n# ===== part: %s =====\n" % p)
            body.append(open(os.path.join(PARTS, p), encoding="utf-8").read())
        body.append("\n# ===== part: oracle_template.py =====\n")
        body.append(generic)
        d = os.path.join(SPECS, sid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "oracle.py"), "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(body))
        print("wrote", sid)


if __name__ == "__main__":
    main()
