"""Assemble paperC/specs/NZ-*/oracle.py from rules/<ID>.py and oracle_core.py.

    python build_oracles.py          write every oracle.py
    python build_oracles.py --check  fail if any oracle.py differs from its parts
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(os.path.dirname(HERE), "specs")
TARGETS = {
    "NZ-SLP": os.path.join(SPECS, "NZ-SLP"),
    "NZ-SPS": os.path.join(SPECS, "NZ-SPS"),
    "NZ-AS": os.path.join(SPECS, "NZ-AS"),
    "NZ-AS-1964": os.path.join(HERE, "supplementary", "NZ-AS-1964"),
}


def assemble(rule_id):
    with open(os.path.join(HERE, "rules", rule_id + ".py"), encoding="utf-8") as f:
        head = f.read().rstrip("\n")
    with open(os.path.join(HERE, "oracle_core.py"), encoding="utf-8") as f:
        core = f.read()
    return head + "\n\n\n" + core


def main(check):
    bad = 0
    for rule_id, folder in TARGETS.items():
        if not os.path.exists(os.path.join(HERE, "rules", rule_id + ".py")):
            continue
        text = assemble(rule_id)
        path = os.path.join(folder, "oracle.py")
        if check:
            with open(path, encoding="utf-8") as f:
                same = f.read() == text
            print(f"{rule_id}: {'identical' if same else 'DIFFERS'}")
            bad += not same
        else:
            os.makedirs(folder, exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print(f"{rule_id}: wrote {os.path.relpath(path, HERE)}")
    return bad


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv[1:]))
