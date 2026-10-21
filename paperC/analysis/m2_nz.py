"""Reader for the OpenFisca Aotearoa official tests of the three NZ rules.

Turns every YAML case into person records: one record per person and per week at
which the case asserts an output. Used by m2_nz.py.

Reading rules (stated in REPORT-M2-M6.md and fragments/nz.md):
* A case's persons are its named persons (`input.persons`) or, for vector cases, one
  person per position of the input/output vectors.
* The weeks of a case are the weeks of the periods its outputs are keyed by
  (`2019-W05-4` -> 2019-W05, `2022-W01`); unkeyed outputs use the case's `period`.
* An input keyed by periods takes the value whose period contains the Monday of the
  record's week (the day `period.start` / `period.first_day` that the formulas read);
  `ETERNITY` covers every week. An input without period keys applies to every week of
  the case. An input with period keys none of which covers the Monday is unset.
"""

import datetime
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I leaves the script dir off sys.path
import common  # noqa: E402

TEST_ROOT = "openfisca_aotearoa/tests/social_security"
RULE_DIRS = {
    "SLP": ["supported_living_payment"],
    "AS": ["accommodation_supplement/1964", "accommodation_supplement/2018"],
    "SPS": ["sole_parent_support"],
}
ENTRY = {
    "SLP": "supported_living_payment__entitled",
    "AS": "accommodation_supplement__entitled",
    "SPS": "sole_parent_support__entitled",
}
MISSING = object()
ROLE_KEYS = {"principal": "principal", "partners": "partner", "children": "child",
             "parents": "parent", "others": "other", "tenants": "tenant",
             "owners": "owner"}


def week_monday(s):
    m = re.fullmatch(r"(\d{4})-W(\d{2})(?:-\d)?", s)
    if m:
        return datetime.date.fromisocalendar(int(m[1]), int(m[2]), 1)
    return None


def to_week(s):
    """Week (ISO string) of an output period key, or None."""
    s = str(s)
    d = week_monday(s)
    if d is None:
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
        if not m:
            return None
        d = datetime.date(int(m[1]), int(m[2]), int(m[3]))
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def period_range(key):
    """(first day, last day) of an OpenFisca period string, or None if not a period."""
    k = str(key)
    if k == "ETERNITY":
        return (datetime.date.min, datetime.date.max)
    m = re.fullmatch(r"(day|week|month|year):([^:]+):(\d+)", k)
    if m:
        unit, start, n = m[1], m[2], int(m[3])
        r = period_range(start)
        if r is None:
            return None
        s = r[0]
        if unit == "day":
            return (s, s + datetime.timedelta(days=n - 1))
        if unit == "week":
            return (s, s + datetime.timedelta(days=7 * n - 1))
        if unit == "month":
            y, mo = s.year, s.month + n
            y, mo = y + (mo - 1) // 12, (mo - 1) % 12 + 1
            return (s, datetime.date(y, mo, 1) - datetime.timedelta(days=1))
        if unit == "year":
            return (s, datetime.date(s.year + n, s.month, s.day) - datetime.timedelta(days=1))
    d = week_monday(k)
    if d:
        return (d, d + datetime.timedelta(days=6))
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", k)
    if m:
        d = datetime.date(int(m[1]), int(m[2]), int(m[3]))
        return (d, d)
    m = re.fullmatch(r"(\d{4})-(\d{2})", k)
    if m:
        s = datetime.date(int(m[1]), int(m[2]), 1)
        nxt = datetime.date(s.year + (s.month == 12), s.month % 12 + 1, 1)
        return (s, nxt - datetime.timedelta(days=1))
    m = re.fullmatch(r"(\d{4})", k)
    if m:
        return (datetime.date(int(k), 1, 1), datetime.date(int(k), 12, 31))
    return None


def is_period_dict(v):
    return isinstance(v, dict) and v and all(period_range(k) is not None for k in v)


def value_at(raw, monday):
    if is_period_dict(raw):
        for k, v in raw.items():
            a, b = period_range(k)
            if a <= monday <= b:
                return v
        return MISSING
    return raw


def pick(v, i):
    if isinstance(v, list):
        return v[i] if i < len(v) else MISSING
    return v


def output_weeks(outputs, case_period):
    weeks = set()
    flat = False

    def visit(v):
        nonlocal flat
        if is_period_dict(v):
            for k in v:
                w = to_week(k)
                if w:
                    weeks.add(w)
                else:
                    flat = True
        else:
            flat = True

    for var, v in outputs.items():
        if var == "persons":
            for pv in v.values():
                for vv in pv.values():
                    visit(vv)
        else:
            visit(v)
    if flat or not weeks:
        w = to_week(case_period)
        if w:
            weeks.add(w)
    return sorted(weeks)


def vector_length(d):
    n = 1
    for v in d.values():
        if isinstance(v, list):
            n = max(n, len(v))
        elif is_period_dict(v):
            for vv in v.values():
                if isinstance(vv, list):
                    n = max(n, len(vv))
    return n


class Person:
    def __init__(self, case, pid, inputs, index, monday):
        self.case, self.pid, self.raw, self.index, self.monday = case, pid, inputs, index, monday
        self.roles = {}   # group entity kind -> role
        self.groups = {}  # group entity kind -> group name

    def get(self, var):
        if var not in self.raw:
            return MISSING
        v = value_at(self.raw[var], self.monday)
        if v is MISSING:
            return MISSING
        return pick(v, self.index) if self.index is not None else v

    def sets(self, var):
        return self.get(var) is not MISSING

    def role(self, kind="family"):
        return self.roles.get(kind)


class Record:
    """One person of one case at one week."""

    def __init__(self, rule, file, case_no, case, person, week, people, asserted):
        self.rule, self.file, self.case_no, self.case = rule, file, case_no, case
        self.person, self.week, self.people = person, week, people
        self.asserted = asserted  # output variables asserted for this person

    @property
    def id(self):
        p = self.person.pid
        return f"{self.file}#{self.case_no}[{p}]@{self.week}"

    def members(self, kind, role):
        g = self.person.groups.get(kind)
        if g is None:
            return []
        return [q for q in self.people if q.groups.get(kind) == g and q.roles.get(kind) == role]

    @property
    def explicit_groups(self):
        return bool(self.person.groups)


def load_rule(rule):
    recs, cases = [], []
    for d in RULE_DIRS[rule]:
        for path in sorted(glob.glob(common.ext_path("openfisca-aotearoa", TEST_ROOT, d, "*.yaml"))):
            rel = os.path.relpath(path, common.ext_path("openfisca-aotearoa", TEST_ROOT))
            text = open(path, encoding="utf-8").read()
            starts = [i + 1 for i, line in enumerate(text.splitlines()) if line.startswith("- name:")]
            for n, case in enumerate(common.load_yaml(text), 1):
                cases.append((rel, n, starts[n - 1], case))
                recs.extend(case_records(rule, rel, n, case))
    return cases, recs


def case_records(rule, rel, n, case):
    inp = case.get("input") or {}
    out = case.get("output") or {}
    weeks = output_weeks(out, case["period"])
    res = []
    for week in weeks:
        monday = week_monday(week)
        if "persons" in inp:
            names = list(inp["persons"])
            people = [Person(case, p, inp["persons"][p] or {}, None, monday) for p in names]
            byname = {p.pid: p for p in people}
            for kind_key, groups in inp.items():
                if kind_key == "persons":
                    continue
                kind = {"families": "family", "family": "family", "tenancies": "tenancy",
                        "tenancy": "tenancy", "ownerships": "ownership",
                        "ownership": "ownership"}.get(kind_key, kind_key)
                if kind_key in ("family", "tenancy", "ownership"):
                    groups = {kind_key: groups}
                for gname, roles in groups.items():
                    for rkey, members in roles.items():
                        members = members if isinstance(members, list) else [members]
                        for m in members:
                            byname[m].roles[kind] = ROLE_KEYS.get(rkey, rkey)
                            byname[m].groups[kind] = gname
            outp = {}
            for var, v in out.items():
                if var == "persons":
                    for pn, pv in v.items():
                        outp.setdefault(pn, set()).update(pv)
                else:
                    for i, pn in enumerate(names):
                        vv = v
                        if is_period_dict(vv):
                            vv = next(iter(vv.values()))
                        if not isinstance(vv, list) or i < len(vv):
                            outp.setdefault(pn, set()).add(var)
        else:
            k = max(vector_length(inp), vector_length(out))
            names = list(range(k))
            people = [Person(case, i, inp, i, monday) for i in names]
            outp = {i: set(out) for i in names}
        for p in people:
            res.append(Record(rule, rel, n, case, p, week, people, sorted(outp.get(p.pid, ()))))
    return res


# =============================================================================== placement
# Each table's attributes are read from a record twice:
#   primary   - only what the case sets (the attribute's variable, or leaves the case sets
#               below it when the formula is a plain function of them); otherwise UNKNOWN;
#   secondary - UNKNOWN replaced by the encoding's default value or by the value the formula
#               computes from what the case sets (sources in DEFAULTS).
# A value that the table cannot label (an enum value outside the declared list, three or
# more children for a composite label) stays UNKNOWN in both readings and is noted.

U = common.UNKNOWN
SRC = "openfisca-aotearoa@9d77ea7ce3c4:openfisca_aotearoa/variables/"
DEFAULTS = {
    "bool": "OpenFisca bool variables without default_value default to False",
    "age": SRC + "demographics/ages.py:41 (default_value = -9999; formula from date_of_birth, lines 45-53)",
    "accommodation_type": SRC + "demographics/housing.py:25 (default AccommodationType.unknown)",
    "accommodation_costs": SRC + "demographics/housing.py:36 (default 0)",
    "cash_assets": SRC + "regulation/social_security_regulation/accommodation_supplement/assets.py:75 (default 0)",
    "social_housing__eligible": SRC + "acts/social_security/accommodation_supplement/entitled.py:144 (default True)",
    "below_thresholds": SRC + "acts/social_security/accommodation_supplement/entitled.py:153, 161 (default True)",
    "residential_requirement": SRC + "acts/social_security/resident.py:35-74 (both formulas are 0 unless social_security__ordinarily_resident_in_new_zealand or ..._in_country_with_reciprocity_agreement is True; both default False)",
    "dependent_children": SRC + "acts/social_security/interpretation/child.py:43-54 (default_value 0 at line 44; count of family members in role child that are dependent children; 0 for a person in role child)",
    "dependent_child": SRC + "acts/social_security/interpretation/child.py:17-40 (child: age < 16, or < 18 and not financially independent; and role child; financially_independent.py:23-29 is False when none of its four inputs is set)",
    "in_a_relationship": SRC + "acts/social_security/relationships.py:16-25 (principal AND (married or civil union or de facto or a member in role partner))",
    "immigration__resident": SRC + "acts/immigration/residence.py:41-42 (holds_resident_visa + permanent_resident)",
    "as_costs": SRC + "acts/social_security/accommodation_supplement/costs.py:17 (default False; formula_2018_11_26 lines 20-94 from 2018-11-26)",
    "basic_grant__entitled": SRC + "regulation/student_allowance/basic_grant.py:17-39 (needs student_allowance__secondary_student or __tertiary_student, students.py:15, 24 default False)",
}
FIN_INDEP_INPUTS = ("social_security__financially_independent", "social_security__full_employment",
                    "social_security__in_receipt_of_basic_grant",
                    "social_security__recieves_goverment_assisted_scheme_payments",
                    "social_security__recieves_main_benefit")
NOTES = {}


def note(key, text):
    NOTES.setdefault(key, set()).add(text)


def b(v):
    return "True" if v else "False"


def plain_bool(rec, var):
    v = rec.person.get(var)
    p = U if v is MISSING else b(v)
    return p, (p if p is not U else "False")


def age_of(person, monday):
    a = person.get("age")
    if a is not MISSING:
        return a
    dob = person.get("date_of_birth")
    if dob is not MISSING:
        d = datetime.date.fromisoformat(str(dob))
        return monday.year - d.year - ((monday.month, monday.day) < (d.month, d.day))
    return MISSING


def age_pair(rec, label):
    a = age_of(rec.person, rec.person.monday)
    return (U if a is MISSING else label(a)), label(-9999 if a is MISSING else a)


def residential(rec):
    v = rec.person.get("social_security__residential_requirement")
    if v is not MISSING:
        return b(v), b(v)
    ores = rec.person.get("social_security__ordinarily_resident_in_new_zealand")
    recip = rec.person.get("social_security__ordinarily_resident_in_country_with_reciprocity_agreement")
    if ores in (MISSING, False) and recip in (MISSING, False):
        return U, "False"
    note("residential", f"{rec.id}: residential requirement depends on unset leaves (refugee, protected person, 2 years' residence)")
    return U, U


def child_dependent(child, monday):
    """(value or MISSING, age or MISSING) of a family child; value derived as in child.py."""
    v = child.get("social_security__dependent_child")
    a = age_of(child, monday)
    if v is not MISSING:
        return bool(v), a
    if any(child.sets(x) for x in FIN_INDEP_INPUTS):
        return MISSING, a
    if a is MISSING:
        return MISSING, a
    return a < 18, a


def dependent_children(rec):
    """(primary count or U, secondary count or U)."""
    v = rec.person.get("social_security__dependent_children")
    if v is not MISSING:
        return v, v
    if not rec.explicit_groups or rec.person.role("family") is None:
        return U, 0
    if rec.person.role("family") == "child":
        return 0, 0
    prim, sec = 0, 0
    for c in rec.members("family", "child"):
        d, a = child_dependent(c, rec.person.monday)
        if d is MISSING:
            prim = U
            d2 = (a if a is not MISSING else -9999) < 18 if not any(c.sets(x) for x in FIN_INDEP_INPUTS) else MISSING
            if d2 is MISSING:
                sec = U
            elif sec is not U:
                sec += int(d2)
        else:
            if prim is not U:
                prim += int(d)
            if sec is not U:
                sec += int(d)
    return prim, sec


def relationship(rec):
    v = rec.person.get("social_security__in_a_relationship")
    if v is not MISSING:
        return b(v), b(v)
    if any(rec.person.sets(x) for x in ("marriage__married", "civil_union__civil_union",
                                        "property_relationships__de_facto_relationship")):
        return U, U
    if rec.explicit_groups and rec.person.role("family") is not None:
        r = rec.person.role("family") == "principal" and bool(rec.members("family", "partner"))
        return b(r), b(r)
    return U, "False"


def lab_dep(n, zero="0", more=">=1"):
    return U if n is U else (zero if n == 0 else more)


# ---------------------------------------------------------------------------------- tables

def slp(rec, coder):
    a20 = ">=20" if coder == 1 else "20+"
    lab = lambda a: "<16" if a < 16 else "16-17" if a < 18 else "18-19" if a < 20 else a20
    names = (["supported_living_payment__restricted_work_capacity", "totally_blind",
              "social_security__residential_requirement", "age",
              "supported_living_payment__disability_self_inflicted",
              "supported_living_payment__caring_for_another_person",
              "social_security__dependent_children"] if coder == 1 else
             ["restricted_work_capacity", "totally_blind", "residential_requirement", "age",
              "disability_self_inflicted", "caring_for_another_person", "dependent_children"])
    dp, ds = dependent_children(rec)
    more = ">=1" if coder == 1 else "1+"
    vals = [plain_bool(rec, "supported_living_payment__restricted_work_capacity"),
            plain_bool(rec, "totally_blind"), residential(rec), age_pair(rec, lab),
            plain_bool(rec, "supported_living_payment__disability_self_inflicted"),
            plain_bool(rec, "supported_living_payment__caring_for_another_person"),
            (lab_dep(dp, "0", more), lab_dep(ds, "0", more))]
    return [({n: v[0] for n, v in zip(names, vals)}, {n: v[1] for n, v in zip(names, vals)})]


AS_TYPES = ["unknown", "rent", "board", "lodging", "mortgage", "social_housing", "residential_care"]


def as_costs_bool(rec):
    """accommodation_supplement__accommodation_costs (primary, secondary)."""
    v = rec.person.get("accommodation_supplement__accommodation_costs")
    if v is not MISSING:
        return b(v), b(v)
    if rec.person.monday < datetime.date(2018, 11, 26):
        return U, "False"
    p = rec.person

    def cost(q):
        c = q.get("accommodation_costs")
        return 0 if c is MISSING else c

    t = p.get("accommodation_type")
    t = "unknown" if t is MISSING else t
    c = cost(p)
    rt, ro = p.role("tenancy"), p.role("ownership")
    a = rt not in ("tenant", "other") and c > 0 and t == "rent"
    bb = ro not in ("owner", "other") and c > 0 and t == "mortgage"
    cc = c > 0 and t in ("board", "lodging")
    ten = sum(cost(q) for q in rec.members("tenancy", "principal") + rec.members("tenancy", "tenant"))
    own = sum(cost(q) for q in rec.members("ownership", "principal") + rec.members("ownership", "owner"))
    d = (rt == "principal" and ten > 0 and t == "rent") or (ro == "principal" and own > 0 and t == "mortgage")
    known = p.sets("accommodation_type") or p.sets("accommodation_costs")
    r = b(a or bb or cc or d)
    return (r if known else U), r


def as1964(rec, coder):
    names = (["age", "immigration__resident", "immigration__permanent_resident",
              "citizenship__citizen", "social_security__ordinarily_resident_in_new_zealand",
              "accommodation_supplement__accommodation_costs", "social_housing__eligible",
              "accommodation_supplement__below_income_threshold",
              "accommodation_supplement__below_cash_threshold"] if coder == 1 else
             ["age", "immigration_resident", "immigration_permanent_resident", "citizen",
              "ordinarily_resident_in_nz", "accommodation_costs", "social_housing",
              "below_income_threshold", "below_cash_threshold"])
    hi = ">=16" if coder == 1 else "16+"
    res = rec.person.get("immigration__resident")
    pr = rec.person.get("immigration__permanent_resident")
    if res is not MISSING:
        resv = (b(res), b(res))
    else:
        hv = rec.person.get("immigration__holds_resident_visa")
        sec = b((hv is not MISSING and hv) or (pr is not MISSING and pr))
        resv = ((sec if (hv is not MISSING or pr is not MISSING) else U), sec)

    def default_true(var):
        v = rec.person.get(var)
        return (U, "True") if v is MISSING else (b(v), b(v))

    vals = [age_pair(rec, lambda a: "<16" if a < 16 else hi), resv,
            plain_bool(rec, "immigration__permanent_resident"),
            plain_bool(rec, "citizenship__citizen"),
            plain_bool(rec, "social_security__ordinarily_resident_in_new_zealand"),
            as_costs_bool(rec), default_true("social_housing__eligible"),
            default_true("accommodation_supplement__below_income_threshold"),
            default_true("accommodation_supplement__below_cash_threshold")]
    return [({n: v[0] for n, v in zip(names, vals)}, {n: v[1] for n, v in zip(names, vals)})]


def as2018(rec, coder):
    p = rec.person
    t = p.get("accommodation_type")
    if t is MISSING:
        tv = (U, "unknown")
    elif t in AS_TYPES:
        tv = (t, t)
    else:
        note("as_type", f"accommodation_type {t!r} is outside the declared enum ({rec.file}#{rec.case_no})")
        tv = (U, U)
    c = p.get("accommodation_costs")
    cv = (U, "<=0") if c is MISSING else (("<=0" if c <= 0 else ">0"),) * 2
    dp, ds = dependent_children(rec)
    partners = rec.members("family", "partner") if p.role("family") == "principal" else []
    # cash assets: applicant plus partners (first coder's C4 / note 4)
    group = [p] + partners
    if any(q.sets("accommodation_supplement__cash_assets") for q in group):
        tot = sum(q.get("accommodation_supplement__cash_assets") if q.sets("accommodation_supplement__cash_assets") else 0 for q in group)
        lab = "<=8100" if tot <= 8100 else "8101-16200" if tot <= 16200 else ">16200"
        cav = (lab, lab)
    else:
        cav = (U, "<=8100")
    if partners:
        vals_ = [q.get("accommodation_supplement__receiving") for q in partners]
        if all(v is MISSING for v in vals_):
            prv = (U, "False")
        else:
            r = b(any(v is not MISSING and v for v in vals_))
            prv = (r, r)
    elif rec.explicit_groups and p.role("family") is not None:
        prv = ("False", "False")
    else:
        prv = (U, "False")
    bge = p.get("basic_grant__entitled")
    if bge is not MISSING:
        bgv = (b(bge), b(bge))
    elif p.sets("student_allowance__secondary_student") or p.sets("student_allowance__tertiary_student"):
        bgv = (U, U)
    else:
        bgv = (U, "False")
    names = ["social_security__residential_requirement", "accommodation_type", "accommodation_costs",
             "social_security__in_a_relationship", "social_security__dependent_children",
             "accommodation_supplement__cash_assets", "partner_accommodation_supplement__receiving",
             "basic_grant__receiving", "independent_circumstances_grant__receiving",
             "basic_grant__entitled", "independent_circumstances_grant__entitled",
             "basic_grant__would_be_entitled", "independent_circumstances_grant__would_be_entitled",
             "accommodation_supplement__disability"]
    vals = [residential(rec), tv, cv, relationship(rec), (lab_dep(dp), lab_dep(ds)), cav, prv,
            plain_bool(rec, "basic_grant__receiving"),
            plain_bool(rec, "independent_circumstances_grant__receiving"), bgv,
            plain_bool(rec, "independent_circumstances_grant__entitled"),
            plain_bool(rec, "basic_grant__would_be_entitled"),
            plain_bool(rec, "independent_circumstances_grant__would_be_entitled"),
            plain_bool(rec, "accommodation_supplement__disability")]
    return [({n: v[0] for n, v in zip(names, vals)}, {n: v[1] for n, v in zip(names, vals)})]


def sps_children(rec):
    """Children of the record's family as (dependent, age) pairs; None when no family is described."""
    if not rec.explicit_groups or rec.person.role("family") is None:
        return None
    return [child_dependent(c, rec.person.monday) for c in rec.members("family", "child")]


def band1(dep, a):
    """First coder's child band (children's financial independence fixed to False)."""
    if dep is MISSING:
        return U
    if a is MISSING:
        return U
    lab = "<14" if a < 14 else "14-15" if a < 16 else "16-17" if a < 18 else ">=18"
    if (lab == ">=18") == bool(dep):   # dependent flag that the band cannot express
        return U
    return lab


def sps(rec, coder):
    p = rec.person
    common_vals = {
        "rr": residential(rec),
        "age": age_pair(rec, lambda a: "<20" if a < 20 else (">=20" if coder == 1 else "20+")),
        "rel": relationship(rec),
        "died": plain_bool(rec, "sole_parent_support__spouse_or_partner_died"),
        "diss": plain_bool(rec, "sole_parent_support__marriage_or_civil_union_dissolved"),
        "apart": plain_bool(rec, "sole_parent_support__living_apart_and_lost_support"),
        "pris": plain_bool(rec, "sole_parent_support__partner_imprisoned"),
        "sup": plain_bool(rec, "sole_parent_support__partner_supervision"),
        "pc": plain_bool(rec, "social_security__principal_caregiver"),
    }
    kids = sps_children(rec)
    if coder == 1:
        if kids is None:
            ch = (U, "none")
        elif len(kids) > 2:
            note("sps_kids", f"{rec.file}#{rec.case_no}: {len(kids)} children, no composite label")
            ch = (U, U)
        else:
            prim = [band1(d, a) for d, a in kids]
            sec = []
            for d, a in kids:
                a2 = a if a is not MISSING else -9999
                d2 = d if d is not MISSING else (a2 < 18)
                sec.append(band1(d2, a2))
            order = ["<14", "14-15", "16-17", ">=18"]

            def comp(bs):
                if any(x is U for x in bs):
                    return U
                if not bs:
                    return "none"
                bs = sorted(bs, key=order.index)
                return f"{len(bs)}:" + "+".join(bs)
            ch = (comp(prim), comp(sec))
        v = common_vals
        names = ["children", "social_security__principal_caregiver", "social_security__in_a_relationship",
                 "sole_parent_support__spouse_or_partner_died",
                 "sole_parent_support__marriage_or_civil_union_dissolved",
                 "sole_parent_support__living_apart_and_lost_support",
                 "sole_parent_support__partner_imprisoned", "sole_parent_support__partner_supervision",
                 "sole_parent_support__receiving", "sole_parent_support__principal_caregiver_before_apart",
                 "sole_parent_support__principal_caregiver_of_youngest",
                 "sole_parent_support__both_primary_caregiver_by_order",
                 "social_security__residential_requirement", "age"]
        vals = [ch, v["pc"], v["rel"], v["died"], v["diss"], v["apart"], v["pris"], v["sup"],
                plain_bool(rec, "sole_parent_support__receiving"),
                plain_bool(rec, "sole_parent_support__principal_caregiver_before_apart"),
                plain_bool(rec, "sole_parent_support__principal_caregiver_of_youngest"),
                plain_bool(rec, "sole_parent_support__both_primary_caregiver_by_order"),
                v["rr"], v["age"]]
        return [({n: x[0] for n, x in zip(names, vals)}, {n: x[1] for n, x in zip(names, vals)})]
    # second coder: one row per child of the family (the table's single child C)
    names = ["residential_requirement", "age", "in_a_relationship", "spouse_or_partner_died",
             "marriage_or_civil_union_dissolved", "living_apart_and_lost_support",
             "partner_imprisoned", "partner_supervision", "principal_caregiver",
             "child_dependent", "child_age"]
    v = common_vals
    base = [v["rr"], v["age"], v["rel"], v["died"], v["diss"], v["apart"], v["pris"], v["sup"], v["pc"]]
    rows = []
    if kids is None:
        # no family described: the encoding's simulation has no child; nothing to place
        kid_pairs = [((U, U), (U, U))]
    elif not kids:
        kid_pairs = [((U, U), (U, U))]
    else:
        kid_pairs = []
        for d, a in kids:
            a2 = a if a is not MISSING else -9999
            d2 = d if d is not MISSING else (a2 < 18)
            kid_pairs.append(((U if d is MISSING else b(d), b(d2)),
                              (U if a is MISSING else ("<14" if a < 14 else "14+"),
                               "<14" if a2 < 14 else "14+")))
        if len(kids) > 1:
            note("sps2_kids", f"{rec.file}#{rec.case_no}: {len(kids)} children placed as {len(kids)} rows")
    for dv, av in kid_pairs:
        vals = base + [dv, av]
        rows.append(({n: x[0] for n, x in zip(names, vals)}, {n: x[1] for n, x in zip(names, vals)}))
    return rows


# ============================================================================ mapping logs
B1, B2 = "paperc-data-nz", "paperc-code2-nz"
TABLES = [
    # (key, coder, rule, branch, folder, conversion record, placement)
    ("1:NZ-SLP", 1, "SLP", B1, "paperC/specs/NZ-SLP", "CONVERSION.md", slp),
    ("1:NZ-AS", 1, "AS", B1, "paperC/specs/NZ-AS", "CONVERSION.md", as2018),
    ("1:NZ-AS-1964", 1, "AS", B1, "paperC/openfisca_nz/supplementary/NZ-AS-1964", "CONVERSION.md", as1964),
    ("1:NZ-SPS", 1, "SPS", B1, "paperC/specs/NZ-SPS", "CONVERSION.md", sps),
    ("2:NZ-SLP", 2, "SLP", B2, "paperC/specs2/NZ-SLP", "CONVERSION_2.md", slp),
    ("2:NZ-AS", 2, "AS", B2, "paperC/specs2/NZ-AS", "CONVERSION_2.md", as1964),
    ("2:NZ-SPS", 2, "SPS", B2, "paperC/specs2/NZ-SPS", "CONVERSION_2.md", sps),
]


def category(text):
    t = text.lower()
    if "does not assert" in t:
        return "other output or scope"
    if "outside" in t and "asserted for" in t or "not asserted at the fixed period" in t:
        return "other period"
    if "role child" in t or "not the principal" in t or "not exactly one principal" in t:
        return "other household shape"
    if "excluded by the spec" in t:
        return "other: row excluded by the table's own exclusion"
    if "sets " in t and ("compute" in t or "formulas do not give" in t):
        return "other: case overrides an intermediate variable with a value its attributes do not produce"
    return "other"


def first_log(folder, conv):
    """{(file, case_no, pid or None): (result, detail, citation)} from the first coder's log table."""
    path = f"{folder}/{conv}"
    out = {}
    for ln, line in enumerate(common.git_lines(B1, path), 1):
        m = re.match(r"\| `([^`#]+)#(\d+)(?:\[([^\]]+)\])?` \| (\w+) \| (.*) \|$", line)
        if m:
            pid = m[3]
            pid = int(pid) if pid is not None and pid.isdigit() else pid
            out[(m[1], int(m[2]), pid)] = (m[4], m[5], f"{B1}:{path}:{ln}")
            continue
        m = re.match(r"\| `([^`]+)` #(\d+)(?:-#(\d+))? (?:\(\d+ cases\) )?\| (\w+) \| (.*) \|$", line)
        if m:
            for k in range(int(m[2]), int(m[3] or m[2]) + 1):
                out[(m[1], k, "*")] = (m[4], m[5], f"{B1}:{path}:{ln}")
    return out


def second_log(folder, conv):
    path = f"{folder}/{conv}"
    out = {}
    for ln, line in enumerate(common.git_lines(B2, path), 1):
        m = re.match(r"UNMAPPED social_security/([^#]+)#(\d+):(\S+): (.*)$", line)
        if m:
            pid = int(m[3]) if m[3].isdigit() else m[3]
            out[(m[1], int(m[2]) + 1, pid)] = ("UNMAPPED", m[4], f"{B2}:{path}:{ln}")
    return out


def mapped_ids(coder, branch, folder):
    ids = []
    for r in common.load_csv(branch, f"{folder}/official_examples.csv"):
        cid = r["case_id"]
        if coder == 1:
            m = re.match(r"openfisca_aotearoa/tests/social_security/([^#]+)#(\d+)(?:\[([^\]]+)\])?$", cid)
            pid = m[3]
            pid = 0 if pid is None else int(pid) if pid.isdigit() else pid
            ids.append((m[1], int(m[2]), pid))
        else:
            m = re.match(r"social_security/([^#]+)#(\d+):(\S+)$", cid)
            ids.append((m[1], int(m[2]) + 1, int(m[3]) if m[3].isdigit() else m[3]))
    return ids


def second_scope(folder):
    path = f"{folder}/oracle.py"
    src = common.git_show(B2, path)
    m = re.search(r"OFFICIAL_TESTS = \[(.*?)\]", src, re.S)
    files = re.findall(r'"social_security/([^"]+)"', m[1])
    return files, common.cite(B2, path, "OFFICIAL_TESTS = [")


def mapping_status(table, cases, recs):
    key, coder, rule, branch, folder, conv, _ = table
    entry = ENTRY[rule]
    mapped = mapped_ids(coder, branch, folder)
    mset = set(mapped)
    persons = {}
    for r in recs:
        persons.setdefault((r.file, r.case_no, r.person.pid), set()).update(r.asserted)
    asserting = sorted((k for k, v in persons.items() if entry in v), key=str)
    log = first_log(folder, conv) if coder == 1 else second_log(folder, conv)
    scope_files, scope_cite = (None, None) if coder == 1 else second_scope(folder)
    unmapped = []
    for k in asserting:
        if k in mset:
            continue
        f, n, pid = k
        hit = log.get(k) or log.get((f, n, None if pid == 0 else pid)) or log.get((f, n, None))
        if hit:
            unmapped.append({"case": f"{f}#{n}[{pid}]", "category": category(hit[1]),
                             "detail": hit[1], "source": hit[2]})
        elif coder == 2 and f not in scope_files:
            unmapped.append({"case": f"{f}#{n}[{pid}]",
                             "category": "other: file outside the second coder's list of official tests",
                             "detail": f"asserts {entry}; the oracle reads only {', '.join(scope_files)}",
                             "source": scope_cite})
        else:
            unmapped.append({"case": f"{f}#{n}[{pid}]", "category": "other",
                             "detail": "no log entry found", "source": ""})
    no_entry = []
    for (f, n, line, case) in cases:
        if not any(entry in persons.get((f, n, p.person.pid), ()) for p in recs
                   if p.file == f and p.case_no == n):
            outs = sorted(case["output"])
            no_entry.append({"case": f"{f}#{n}", "line": line, "asserts": outs})
    return {
        "yaml_cases": len(cases),
        "yaml_cases_asserting_entry": len({(f, n) for f, n, _ in asserting}),
        "persons_in_all_cases": len(persons),
        "person_values_asserting_entry": len(asserting),
        "mapped_rows": len(mapped),
        "mapped_distinct_persons": len(mset),
        "unmapped_asserting": unmapped,
        "cases_without_entry_assertion": no_entry,
    }


# Unused-value counts that each conversion's README states for its mapped examples
README_UNUSED = {
    "1:NZ-SLP": (0, B1, "paperC/specs/README-NZ.md", "**NZ-SLP:** none"),
    "1:NZ-AS": (20, B1, "paperC/specs/README-NZ.md", "**NZ-AS** (one example row)"),
    "1:NZ-AS-1964": (3, B1, "paperC/specs/README-NZ.md", "*NZ-AS-1964:*"),
    "1:NZ-SPS": (21, B1, "paperC/specs/README-NZ.md", "**NZ-SPS:** `children`"),
    "2:NZ-SLP": (0, B2, "paperC/specs2/README-NZ-CODE2.md", "`NZ-SLP`: none"),
    "2:NZ-AS": (3, B2, "paperC/specs2/README-NZ-CODE2.md", "`NZ-AS`: `ordinarily"),
    "2:NZ-SPS": (5, B2, "paperC/specs2/README-NZ-CODE2.md", "`NZ-SPS`: `residential"),
}


def run():
    out = {"reading_rules": __doc__, "defaults": DEFAULTS, "tables": {}}
    loaded = {r: load_rule(r) for r in ("SLP", "AS", "SPS")}
    for t in TABLES:
        key, coder, rule, branch, folder, conv, place = t
        cases, recs = loaded[rule]
        spec = common.load_spec(branch, folder)
        names = common.attr_names(spec)
        valid = common.valid_rows(branch, folder, spec)
        mapped = [{n: r[n] for n in names} for r in common.load_csv(branch, f"{folder}/official_examples.csv")]
        prim, sec, prim_appl, sec_appl, recids = [], [], [], [], []
        for r in recs:
            for p, s in place(r, coder):
                prim.append(p)
                sec.append(s)
                recids.append(r.id)
                if r.person.role("family") in (None, "principal"):
                    prim_appl.append(p)
                    sec_appl.append(s)
        # labels a table does not declare (should not happen) raise in common.usage
        u_p = common.usage(spec, mapped, prim, valid)
        u_s = common.usage(spec, mapped, sec, valid)
        u_a = common.usage(spec, mapped, sec_appl, valid)
        u_pa = common.usage(spec, mapped, prim_appl, valid)
        unk_sec = {n: sum(1 for s in sec if s[n] is U) for n in names}
        # where each value left unused by the mapped tests is found in the whole suite
        prov = {}
        for n in names:
            for v in u_p["attributes"][n]["unused_mapped"]:
                hp = sorted({i.split("@")[0] for i, row in zip(recids, prim) if row[n] == v})
                hs = sorted({i.split("@")[0] for i, row in zip(recids, sec) if row[n] == v})
                prov[f"{n}={v}"] = {"primary": hp[:4], "primary_n": len(hp),
                                    "secondary": hs[:4], "secondary_n": len(hs)}
        st = mapping_status(t, cases, recs)
        out["tables"][key] = {
            "coder": coder, "rule": rule, "branch": branch, "folder": folder,
            "branch_commit": common.branch_commit(branch),
            "mapping": st,
            "records": len(recs), "placement_rows": len(prim),
            "primary": u_p, "secondary": u_s,
            "primary_applicants_only": u_pa, "secondary_applicants_only": u_a,
            "secondary_unknown": unk_sec, "provenance": prov,
            "readme_check": {"stated_unused": README_UNUSED[key][0],
                             "source": common.cite(*README_UNUSED[key][1:]),
                             "computed_unused": u_p["unused_mapped_total"],
                             "agree": README_UNUSED[key][0] == u_p["unused_mapped_total"]},
            "h1": {
                "mapped": {"unused>0": u_p["unused_mapped_total"] > 0,
                           "missed_valid>0": u_p["missed_valid_mapped"] > 0},
                "suite_primary": {"unused>0": u_p["unused_suite_total"] > 0,
                                  "missed_valid>0": u_p["missed_valid_suite"] > 0},
                "suite_secondary": {"unused>0": u_s["unused_suite_total"] > 0,
                                    "missed_valid>0": u_s["missed_valid_suite"] > 0},
            },
        }
    out["notes"] = {k: sorted(v) for k, v in NOTES.items()}
    common.write_json("m2_nz.json", out)
    return out


def summary(out):
    for k, t in out["tables"].items():
        p, s, a, pa = t["primary"], t["secondary"], t["secondary_applicants_only"], t["primary_applicants_only"]
        m = t["mapping"]
        print(f"{k:14} cases {m['yaml_cases']} (entry {m['yaml_cases_asserting_entry']}) "
              f"pv {m['person_values_asserting_entry']} mapped {m['mapped_rows']} | "
              f"declared {p['declared_total']} unused mapped {p['unused_mapped_total']} "
              f"suite P {p['unused_suite_total']} Pappl {pa['unused_suite_total']} S {s['unused_suite_total']} Sappl {a['unused_suite_total']} | "
              f"missed valid {p['missed_valid_mapped']}/{p['valid_total']} -> P {p['missed_valid_suite']} "
              f"Pappl {pa['missed_valid_suite']} S {s['missed_valid_suite']} Sappl {a['missed_valid_suite']}")


if __name__ == "__main__":
    summary(run())
