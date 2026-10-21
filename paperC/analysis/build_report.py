"""Assemble paperC/analysis/REPORT-M2-M6.md from fragments/ (head, then FR-PF/FR-AF,
FR-APL/US-121, NZ). Section headings of every family are set to level 2.
Run from the repository root:  python3.12 -I paperC/analysis/build_report.py
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ["head.md", "fr_af.md", "fr2.md", "nz.md"]


def level(text, top):
    """Shift headings so that the fragment's highest heading becomes level `top`."""
    lines = text.splitlines()
    fence = False
    levels = []
    for l in lines:
        if l.startswith("```"):
            fence = not fence
        elif not fence and (m := re.match(r"(#+) ", l)):
            levels.append(len(m.group(1)))
    shift = top - min(levels)
    out, fence = [], False
    for l in lines:
        if l.startswith("```"):
            fence = not fence
        elif not fence and (m := re.match(r"(#+) ", l)):
            l = "#" * (len(m.group(1)) + shift) + l[len(m.group(1)):]
        out.append(l)
    return "\n".join(out).rstrip() + "\n"


parts = []
for i, name in enumerate(PARTS):
    with open(os.path.join(HERE, "fragments", name), encoding="utf-8") as f:
        parts.append(level(f.read(), 1 if i == 0 else 2))
with open(os.path.join(HERE, "REPORT-M2-M6.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print("wrote", os.path.join(HERE, "REPORT-M2-M6.md"))
