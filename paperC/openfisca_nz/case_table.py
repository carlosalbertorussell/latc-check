"""Print a Markdown table of the official-case mapping from a check_official log.

Usage: python case_table.py logs/check_official_<ID>.txt
Cases that assert nothing about the output variable are grouped into one line per file.
"""
import sys
from collections import defaultdict

PREFIX = "openfisca_aotearoa/tests/social_security/"


def main(path):
    lines = open(path, encoding="utf-8").read().split("\n\n", 1)[1].strip().splitlines()
    no_assert = defaultdict(list)
    print("| case (person) | result | detail |")
    print("|---|---|---|")
    for line in lines:
        tag, result, *rest = line.split("\t")
        detail = " ".join(rest).replace("|", "/")
        tag = tag.replace(PREFIX, "")
        if detail.startswith("does not assert"):
            file, num = tag.rsplit("#", 1)
            no_assert[(file, detail)].append(num)
            continue
        print(f"| `{tag}` | {result} | {detail} |")
    for (file, detail), nums in no_assert.items():
        which = f"#{nums[0]}" if len(nums) == 1 else f"#{nums[0]}-#{nums[-1]} ({len(nums)} cases)"
        print(f"| `{file}` {which} | UNMAPPABLE | {detail} |")


if __name__ == "__main__":
    main(sys.argv[1])
