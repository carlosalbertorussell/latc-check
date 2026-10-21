"""M6 for the New Zealand rules: how far do the two conversions agree?

(a) attribute-level alignment of the two conversions per rule;
(b) NZ-SLP: row-by-row comparison of the two ground truths on all 256 combinations;
(c) NZ-AS (SSA 1964 formula at 2018-W01): first coder's supplementary NZ-AS-1964 against
    the second coder's NZ-AS on all 512 combinations; NZ-SPS on the common refinement
    (first coder's one-child rows with the second coder's defaults).

Run from the repository root: python3.12 -I paperC/analysis/m6_nz.py  -> out/m6_nz.json
"""

import collections
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I leaves the script dir off sys.path
import common  # noqa: E402

B1, B2 = "paperc-data-nz", "paperc-code2-nz"
F1 = {"SLP": "paperC/specs/NZ-SLP", "AS2018": "paperC/specs/NZ-AS",
      "AS1964": "paperC/openfisca_nz/supplementary/NZ-AS-1964", "SPS": "paperC/specs/NZ-SPS"}
F2 = {"SLP": "paperC/specs2/NZ-SLP", "AS1964": "paperC/specs2/NZ-AS", "SPS": "paperC/specs2/NZ-SPS"}


def nesting(pairs, d1, d2):
    """Relation between two partitions of one input given the overlapping label pairs."""
    to2 = collections.defaultdict(set)
    to1 = collections.defaultdict(set)
    for a, b in pairs:
        to2[a].add(b)
        to1[b].add(a)
    f12 = all(len(to2[a]) == 1 for a in d1 if a in to2)
    f21 = all(len(to1[b]) == 1 for b in d2 if b in to1)
    cover1 = set(to2) == set(d1)
    cover2 = set(to1) == set(d2)
    if f12 and f21:
        rel = "coincide"
    elif f12:
        rel = "first refines second"
    elif f21:
        rel = "second refines first"
    else:
        rel = "cross"
    gaps = []
    if not cover1:
        gaps.append("first-coder labels with no counterpart: " + ", ".join(a for a in d1 if a not in to2))
    if not cover2:
        gaps.append("second-coder labels with no counterpart: " + ", ".join(b for b in d2 if b not in to1))
    return rel, gaps


def same_labels(d1, d2, rename=None):
    rename = rename or {}
    return [(a, rename.get(a, a)) for a in d1 if rename.get(a, a) in d2]


# ------------------------------------------------------------------------- (a) alignment
# One entry per encoding input on the path from the entry variable. 'first'/'second' give
# what each conversion made of it: ("attribute", name) | ("fixed", text) | ("left out", text).
# Sources: each conversion's spec.json and CONVERSION(_2).md; cited in the fragment.

def alignment():
    s1 = {k: common.load_spec(B1, f) for k, f in F1.items()}
    s2 = {k: common.load_spec(B2, f) for k, f in F2.items()}
    d1 = {k: common.declared(v) for k, v in s1.items()}
    d2 = {k: common.declared(v) for k, v in s2.items()}
    res = {}

    def row(inp, first, second, pairs=None, k1=None, k2=None):
        r = {"input": inp, "first": first, "second": second}
        if first[0] == "attribute" and second[0] == "attribute":
            a, b = d1[k1][first[1]], d2[k2][second[1]]
            r["first_values"], r["second_values"] = a, b
            r["relation"], r["gaps"] = nesting(pairs if pairs is not None else same_labels(a, b), a, b)
        elif first[0] == "attribute":
            r["first_values"] = d1[k1][first[1]]
        elif second[0] == "attribute":
            r["second_values"] = d2[k2][second[1]]
        return r

    # SLP: seven attributes on each side
    slp = []
    for n1, n2 in zip(common.attr_names(s1["SLP"]), common.attr_names(s2["SLP"])):
        ren = {">=20": "20+", ">=1": "1+"}
        slp.append(row(n1, ("attribute", n1), ("attribute", n2),
                       same_labels(d1["SLP"][n1], d2["SLP"][n2], ren), "SLP", "SLP"))
    slp.append({"input": "period", "first": ("fixed", "2019-W01"), "second": ("fixed", "2019-W01")})
    slp.append({"input": "household", "first": ("fixed", "applicant alone, principal of a one-person family"),
                "second": ("fixed", "one person P, principal of a one-person family")})
    slp.append({"input": "leaves of social_security__residential_requirement (citizen_or_resident, ordinarily_resident, ...)",
                "first": ("left out", "kept whole at the defined term (C2)"),
                "second": ("left out", "kept whole at the defined term (rule 1)")})
    slp.append({"input": "children of the family (leaves of social_security__dependent_children)",
                "first": ("left out", "count set directly"), "second": ("left out", "count set directly")})
    res["NZ-SLP"] = slp

    # AS, SSA 1964 formula: nine attributes on each side
    a64 = []
    for n1, n2 in zip(common.attr_names(s1["AS1964"]), common.attr_names(s2["AS1964"])):
        a64.append(row(n1, ("attribute", n1), ("attribute", n2),
                       same_labels(d1["AS1964"][n1], d2["AS1964"][n2], {">=16": "16+"}), "AS1964", "AS1964"))
    a64.append({"input": "period", "first": ("fixed", "2018-W01 (supplementary table)"),
                "second": ("fixed", "2018-W01 (main table)")})
    a64.append({"input": "immigration__holds_resident_visa (leaf of immigration__resident)",
                "first": ("left out", "immigration__resident kept whole"),
                "second": ("left out", "immigration__resident kept whole")})
    res["NZ-AS (SSA 1964 formula)"] = a64

    # AS, SSA 2018 formula: first coder's main table only
    a18 = []
    for n1 in common.attr_names(s1["AS2018"]):
        a18.append(row(n1, ("attribute", n1),
                       ("left out", "the second coder's NZ-AS uses the SSA 1964 formula at 2018-W01, which does not read this input"),
                       k1="AS2018"))
    a18.append({"input": "period", "first": ("fixed", "2022-W01"), "second": ("fixed", "2018-W01 (other formula)")})
    a18.append({"input": "household (tenancy, ownership, partner)",
                "first": ("fixed", "sole principal of family, tenancy and ownership; one partner when in a relationship"),
                "second": ("left out", "")})
    res["NZ-AS (SSA 2018 formula)"] = a18

    # SPS
    sps = []
    pairs_named = [
        ("social_security__residential_requirement", "residential_requirement", {}),
        ("age", "age", {">=20": "20+"}),
        ("social_security__in_a_relationship", "in_a_relationship", {}),
        ("sole_parent_support__spouse_or_partner_died", "spouse_or_partner_died", {}),
        ("sole_parent_support__marriage_or_civil_union_dissolved", "marriage_or_civil_union_dissolved", {}),
        ("sole_parent_support__living_apart_and_lost_support", "living_apart_and_lost_support", {}),
        ("sole_parent_support__partner_imprisoned", "partner_imprisoned", {}),
        ("sole_parent_support__partner_supervision", "partner_supervision", {}),
        ("social_security__principal_caregiver", "principal_caregiver", {}),
    ]
    for n1, n2, ren in pairs_named:
        sps.append(row(n1, ("attribute", n1), ("attribute", n2),
                       same_labels(d1["SPS"][n1], d2["SPS"][n2], ren), "SPS", "SPS"))
    for n1 in ["sole_parent_support__receiving", "sole_parent_support__principal_caregiver_before_apart",
               "sole_parent_support__principal_caregiver_of_youngest",
               "sole_parent_support__both_primary_caregiver_by_order"]:
        sps.append(row(n1, ("attribute", n1),
                       ("fixed", "default False; read only by s 32 split care, which is True for P with one child"),
                       k1="SPS"))
    # children: first coder's composite against second's (child_dependent, child_age) product
    prod = [f"{d}/{a}" for d in d2["SPS"]["child_dependent"] for a in d2["SPS"]["child_age"]]
    child_pairs = [("1:<14", "True/<14"), ("1:14-15", "True/14+"), ("1:16-17", "True/14+"),
                   ("1:>=18", "False/14+")]
    rel, gaps = nesting(child_pairs, d1["SPS"]["children"], prod)
    sps.append({"input": "children of the family (members in role child: social_security__dependent_child, age)",
                "first": ("attribute", "children"), "second": ("attribute", "child_dependent x child_age"),
                "first_values": d1["SPS"]["children"], "second_values": prod,
                "relation": rel, "gaps": gaps})
    sps.append({"input": "social_security__financially_independent (children)",
                "first": ("fixed", "False"),
                "second": ("left out", "inside child_dependent, kept whole")})
    sps.append({"input": "sole_parent_support__parents_living_apart",
                "first": ("fixed", "not set (no effect without another parent)"),
                "second": ("fixed", "default (no effect with one child)")})
    sps.append({"input": "household", "first": ("fixed", "principal plus 0-2 children, no partner/parent/other"),
                "second": ("fixed", "principal plus exactly one child")})
    sps.append({"input": "period", "first": ("fixed", "2019-W05"), "second": ("fixed", "2019-W05")})
    res["NZ-SPS"] = sps
    return res


# ---------------------------------------------------------------------- row comparisons

def compare(k1, k2, rename_attr, rename_val, extra_filter=None, fixed2=None):
    """Compare first-coder rows (filtered and translated) with second-coder rows."""
    s1, s2 = common.load_spec(B1, F1[k1]), common.load_spec(B2, F2[k2])
    g1 = common.ground_truth(B1, F1[k1], s1)
    g2 = common.ground_truth(B2, F2[k2], s2)
    n1, n2 = common.attr_names(s1), common.attr_names(s2)
    rows = []
    for c1, o1 in g1.items():
        r1 = dict(zip(n1, c1))
        if extra_filter and not extra_filter(r1):
            continue
        r2 = {}
        for a in n1:
            if a in rename_attr:
                b = rename_attr[a]
                r2[b] = rename_val.get((a, r1[a]), r1[a])
        if fixed2:
            r2.update(fixed2(r1))
        c2 = tuple(r2[b] for b in n2)
        rows.append((r1, c2, o1, g2[c2]))
    return rows, n1, n2, len(g1), len(g2)


def tally(rows):
    c = collections.Counter()
    for _, _, o1, o2 in rows:
        if o1 == o2:
            c["agree"] += 1
        elif o1 == "EXCLUDED" or o2 == "EXCLUDED":
            c[f"excluded on one side: first={o1} second={o2}"] += 1
        else:
            c[f"output differs: first={o1} second={o2}"] += 1
    return dict(c)


def slp_compare():
    s1 = common.load_spec(B1, F1["SLP"])
    s2 = common.load_spec(B2, F2["SLP"])
    ren = dict(zip(common.attr_names(s1), common.attr_names(s2)))
    vals = {("age", ">=20"): "20+", ("social_security__dependent_children", ">=1"): "1+"}
    rows, n1, n2, l1, l2 = compare("SLP", "SLP", ren, vals)
    dis = [{"first_row": r, "second_row": dict(zip(n2, c2)), "first": o1, "second": o2}
           for r, c2, o1, o2 in rows if o1 != o2]
    excl_true = [d for d in dis if d["first"] == "EXCLUDED" and d["second"] == "True"]
    conv = f"{F1['SLP']}/CONVERSION.md"
    return {
        "rows_first": l1, "rows_second": l2, "compared": len(rows),
        "distinct_second_rows": len({c for _, c, _, _ in rows}),
        "tally": tally(rows), "disagreements": dis,
        "excluded_rows_true_in_second": excl_true,
        "first_coder_claim": common.cite(B1, conv, "would be False in any case"),
        "carer_route": "supported_living_payment.py:79-106 (s 40 carer: caring AND residential requirement AND ((age >= 18 AND dependent children = 0) OR age >= 20)); the carer branch does not read restricted work capacity, blindness or the self-inflicted flag",
    }


def as64_compare():
    s1 = common.load_spec(B1, F1["AS1964"])
    s2 = common.load_spec(B2, F2["AS1964"])
    ren = dict(zip(common.attr_names(s1), common.attr_names(s2)))
    rows, n1, n2, l1, l2 = compare("AS1964", "AS1964", ren, {("age", ">=16"): "16+"})
    dis = [{"first_row": r, "second": o2, "first": o1} for r, c2, o1, o2 in rows if o1 != o2]
    ex1 = sum(1 for _, _, o1, _ in rows if o1 == "EXCLUDED")
    ex2 = sum(1 for _, _, _, o2 in rows if o2 == "EXCLUDED")
    both = sum(1 for _, _, o1, o2 in rows if o1 == o2 == "EXCLUDED")
    return {"rows_first": l1, "rows_second": l2, "compared": len(rows), "tally": tally(rows),
            "excluded_first": ex1, "excluded_second": ex2, "excluded_both": both,
            "exclusion_first": s1["exclusions"], "exclusion_second": s2["exclusions"],
            "disagreements": dis}


SPS_CHILD = {"1:<14": ("True", "<14"), "1:14-15": ("True", "14+"), "1:16-17": ("True", "14+"),
             "1:>=18": ("False", "14+")}
SPS_FIXED_FALSE = ["sole_parent_support__receiving", "sole_parent_support__principal_caregiver_before_apart",
                   "sole_parent_support__principal_caregiver_of_youngest",
                   "sole_parent_support__both_primary_caregiver_by_order"]


def sps_compare():
    ren = {"social_security__residential_requirement": "residential_requirement", "age": "age",
           "social_security__in_a_relationship": "in_a_relationship",
           "sole_parent_support__spouse_or_partner_died": "spouse_or_partner_died",
           "sole_parent_support__marriage_or_civil_union_dissolved": "marriage_or_civil_union_dissolved",
           "sole_parent_support__living_apart_and_lost_support": "living_apart_and_lost_support",
           "sole_parent_support__partner_imprisoned": "partner_imprisoned",
           "sole_parent_support__partner_supervision": "partner_supervision",
           "social_security__principal_caregiver": "principal_caregiver"}

    def keep(r):
        return r["children"] in SPS_CHILD and all(r[a] == "False" for a in SPS_FIXED_FALSE)

    def fixed2(r):
        d, a = SPS_CHILD[r["children"]]
        return {"child_dependent": d, "child_age": a}

    rows, n1, n2, l1, l2 = compare("SPS", "SPS", ren, {("age", ">=20"): "20+"}, keep, fixed2)
    groups = collections.defaultdict(list)
    for r, c2, o1, o2 in rows:
        if o1 != o2:
            key = (r["children"], r["social_security__principal_caregiver"], o1, o2)
            groups[key].append(r)
    dis = []
    for (ch, pc, o1, o2), rs in sorted(groups.items()):
        dis.append({"children": ch, "principal_caregiver": pc, "first": o1, "second": o2,
                    "count": len(rs), "example": rs[0]})
    covered2 = {c for _, c, _, _ in rows}
    g2 = common.ground_truth(B2, F2["SPS"])
    n2l = common.attr_names(common.load_spec(B2, F2["SPS"]))
    uncovered = collections.Counter()
    for c, o in g2.items():
        if c not in covered2:
            r = dict(zip(n2l, c))
            uncovered[(r["child_dependent"], r["child_age"], o)] += 1
    # second-coder rows by child cell, for the explanation of '1:>=18'
    by_cell = collections.Counter()
    for c, o in g2.items():
        r = dict(zip(n2l, c))
        by_cell[(r["child_dependent"], r["child_age"], r["principal_caregiver"], o)] += 1
    return {"rows_first": l1, "rows_second": l2, "first_rows_compared": len(rows),
            "second_rows_covered": len(covered2), "tally": tally(rows), "disagreement_groups": dis,
            "second_rows_without_counterpart": {f"child_dependent={a} child_age={b} output={o}": n
                                                for (a, b, o), n in sorted(uncovered.items())},
            "second_by_child_cell": {f"{a}/{b}/pc={p}/{o}": n for (a, b, p, o), n in sorted(by_cell.items())}}


def run():
    out = {"branches": {B1: common.branch_commit(B1), B2: common.branch_commit(B2)},
           "alignment": alignment(), "NZ-SLP": slp_compare(), "NZ-AS-1964": as64_compare(),
           "NZ-SPS": sps_compare()}
    common.write_json("m6_nz.json", out)
    return out


if __name__ == "__main__":
    o = run()
    for k in ("NZ-SLP", "NZ-AS-1964", "NZ-SPS"):
        print(k, o[k]["tally"])
    for k, rows in o["alignment"].items():
        for r in rows:
            if "relation" in r:
                print(" ", k, r["input"], r["relation"], r["gaps"])
