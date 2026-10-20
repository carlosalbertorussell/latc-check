"""Independent re-implementation of each NZ table, compared with ground_truth.csv.

Standard library only; no OpenFisca.  Each function restates the formulas of the
encoding at commit 9d77ea7ce3c4 as read by hand (file:line in the comments), with
the fixed inputs of the spec.  Usage: python crosscheck.py  (exit 1 on any mismatch)
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(os.path.dirname(HERE), "specs")
T = "True"


def slp(r):
    # supported_living_payment.py:48-69 (s 34-36) and :79-106 (s 40)
    age = {"<16": 15, "16-17": 16, "18-19": 18, ">=20": 20}[r["age"]]
    dep0 = r["social_security__dependent_children"] == "0"
    resid = r["social_security__residential_requirement"] == T
    disabled = ((r["supported_living_payment__restricted_work_capacity"] == T or r["totally_blind"] == T)
                and resid and age >= 16 and r["supported_living_payment__disability_self_inflicted"] != T)
    carer = (r["supported_living_payment__caring_for_another_person"] == T and resid
             and ((age >= 18 and dep0) or age >= 20))
    return disabled or carer


def sps(r):
    kids = [] if r["children"] == "none" else r["children"].split(":")[1].split("+")
    age_of = {"<14": 5, "14-15": 14, "16-17": 16, ">=18": 18}
    dependent = [age_of[k] < 18 for k in kids]  # child.py:17-40 with financially_independent False
    # sole_parent_support.py:180-181: (dependent_child * age) < 14, as written
    dep_req = any((age_of[k] if d else 0) < 14 for k, d in zip(kids, dependent)) and r["social_security__principal_caregiver"] == T
    reason = (r["social_security__in_a_relationship"] != T
              or r["sole_parent_support__spouse_or_partner_died"] == T
              or r["sole_parent_support__marriage_or_civil_union_dissolved"] == T
              or r["sole_parent_support__living_apart_and_lost_support"] == T
              or r["sole_parent_support__partner_imprisoned"] == T
              or r["sole_parent_support__partner_supervision"] == T)
    requirement = dep_req and reason  # :151-166
    y = sum(dependent) >= 2  # :260
    receiving = r["sole_parent_support__receiving"] == T
    split = ((not y)
             or (y and (receiving or (not receiving and r["sole_parent_support__principal_caregiver_before_apart"] == T)
                        or r["sole_parent_support__principal_caregiver_of_youngest"] == T))
             or r["sole_parent_support__both_primary_caregiver_by_order"] == T)  # :259-294, no other parent
    return (requirement and split and r["social_security__residential_requirement"] == T and r["age"] == ">=20")


def as2018(r):
    t = r["accommodation_type"]
    costs = r["accommodation_costs"] == ">0"
    # costs.py:20-94, applicant sole principal of tenancy and ownership
    acc = costs and t in ("rent", "mortgage", "board", "lodging")
    # assets.py:19-66, total cash assets = applicant's
    cash = {"<=8100": 8100, "8101-16200": 16200, ">16200": 16201}[r["accommodation_supplement__cash_assets"]]
    rel = r["social_security__in_a_relationship"] == T
    kids = r["social_security__dependent_children"] == ">=1"
    assets = (rel and cash <= 16200) or (not rel and kids and cash <= 16200) or (not rel and not kids and cash <= 8100)
    social = t == "social_housing"  # exclusion.py:112-115
    other = (r["partner_accommodation_supplement__receiving"] == T
             or any(r[n] == T for n in ("basic_grant__receiving", "independent_circumstances_grant__receiving",
                                         "basic_grant__entitled", "independent_circumstances_grant__entitled",
                                         "basic_grant__would_be_entitled", "independent_circumstances_grant__would_be_entitled",
                                         "accommodation_supplement__disability"))
             or t == "residential_care")  # exclusion.py:127-173
    return r["social_security__residential_requirement"] == T and acc and assets and not social and not other


def as1964(r):
    # entitled.py:75-138
    return (r["age"] == ">=16"
            and (r["immigration__resident"] == T or r["immigration__permanent_resident"] == T or r["citizenship__citizen"] == T)
            and r["social_security__ordinarily_resident_in_new_zealand"] == T
            and r["accommodation_supplement__accommodation_costs"] == T
            and r["social_housing__eligible"] != T
            and r["accommodation_supplement__below_income_threshold"] == T
            and r["accommodation_supplement__below_cash_threshold"] == T)


TABLES = {
    "NZ-SLP": (os.path.join(SPECS, "NZ-SLP"), slp),
    "NZ-SPS": (os.path.join(SPECS, "NZ-SPS"), sps),
    "NZ-AS": (os.path.join(SPECS, "NZ-AS"), as2018),
    "NZ-AS-1964": (os.path.join(HERE, "supplementary", "NZ-AS-1964"), as1964),
}


def main():
    bad_total = 0
    for name, (folder, fn) in TABLES.items():
        path = os.path.join(folder, "ground_truth.csv")
        if not os.path.exists(path):
            continue
        spec = json.load(open(os.path.join(folder, "spec.json"), encoding="utf-8"))
        n = bad = 0
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                excl = any(eval(e["predicate"], {"__builtins__": {}}, dict(r)) for e in spec["exclusions"])
                want = "EXCLUDED" if excl else ("True" if fn(r) else "False")
                n += 1
                if r["output"] != want:
                    bad += 1
                    if bad <= 5:
                        print(f"  {name} mismatch: {r} expected {want}")
        print(f"{name}: {n - bad}/{n} rows agree with the independent re-implementation")
        bad_total += bad
    return 1 if bad_total else 0


if __name__ == "__main__":
    sys.exit(main())
