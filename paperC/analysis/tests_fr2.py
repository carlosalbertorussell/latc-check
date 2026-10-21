"""Read the official tests of FR-APL and US-121 from catala-examples (pinned commit).

Every extracted value keeps the line it comes from, so that the report can cite
`<test file>:<line>` for each placement. Standard library only.
"""

import datetime as dt
import re

import common

APL_FILE = "aides_logement/tests/tests_eligibilite_apl.catala_fr"
US_FILE = "us_tax_code/tests/test_section_121.catala_en"


def _blocks(lines, head_re):
    """(name, first_line, last_line) of each scope body whose header matches head_re."""
    starts = [(i, m.group(1)) for i, l in enumerate(lines, 1) if (m := re.match(head_re, l))]
    out = []
    for k, (i, name) in enumerate(starts):
        j = len(lines)
        for n in range(i + 1, len(lines) + 1):
            if lines[n - 1].startswith("#[test]") or lines[n - 1].startswith("```"):
                j = n - 1
                break
            if k + 1 < len(starts) and n == starts[k + 1][0]:
                j = n - 1
                break
        out.append((name, i, j))
    return out


def _find(lines, a, b, pattern):
    """First match of pattern in lines a..b (1-based, inclusive): (groups, line)."""
    for n in range(a, b + 1):
        m = re.search(pattern, lines[n - 1])
        if m:
            if not m.groups():
                return m.group(0), n
            return m.groups() if len(m.groups()) > 1 else m.group(1), n
    return None, None


def apl_tests():
    """One dict per test scope of tests_eligibilite_apl.catala_fr.

    Each field is (value, line); `scope` is the tested scope, `asserts` the assertion line.
    """
    lines = common.read_ext("catala-examples", "aides_logement", "tests",
                            "tests_eligibilite_apl.catala_fr").splitlines()
    decl = {}
    for i, l in enumerate(lines, 1):
        m = re.match(r"déclaration champ d'application (\w+):", l)
        if m:
            s = re.search(r"champ d'application AL\.(\w+)", lines[i])
            decl[m.group(1)] = (s.group(1), i + 1)
    tests = []
    for name, a, b in _blocks(lines, r"champ d'application (Exemple\d+):"):
        t = {"name": name, "lines": (a, b), "scope": decl[name]}
        f = lambda p: _find(lines, a, b, p)
        t["asserts"] = f(r"(assertion .*)")
        t["date_courante"] = f(r"date_courante égal à \|(\d{4}-\d\d-\d\d)\|")
        t["residence"] = f(r"-- résidence: (\w+)")
        t["situation_familiale"] = f(r"-- situation_familiale: (\w+)")
        kids = [n for n in range(a, b + 1) if "EnfantÀCharge contenu" in lines[n - 1]]
        t["personnes_a_charge"] = (len(kids), kids[0] if kids else None)
        t["zone"] = f(r"-- zone: (\w+)")
        t["residence_principale"] = f(r"-- résidence_principale: (\w+)")
        t["mode_occupation"] = f(r"-- mode_occupation:\s*$")
        mo, mo_line = _find(lines, t["mode_occupation"][1] + 1, b, r"^\s+(\w+) contenu")
        t["mode_occupation"] = (mo, mo_line)
        bl, bl_line = f(r"-- bailleur:\s*(\S*)")
        if not bl:  # constructor on the next line
            bl, bl_line = _find(lines, bl_line + 1, b, r"^\s+(\w+)")
        conv = f(r"conventionné_livre_III_titre_V_chap_III: (\w+)")
        t["bailleur"] = (bl, bl_line)
        t["bailleur_conventionne"] = conv
        t["proprietaire"] = f(r"-- propriétaire: AL\.ParentOuAutre\.(\w+)")
        t["usufruit"] = f(r"-- usufruit: AL\.ParentOuAutre\.(\w+)")
        t["loue_ou_sous_loue"] = f(r"-- loué_ou_sous_loué_à_des_tiers: AL\.LouéOuSousLouéÀDesTiers\.(\w+)")
        t["logement_decent"] = f(r"-- logement_decent_l89_462: (\w+)")
        s, sl = f(r"-- surface_m_carrés: (\d+)")
        t["surface"] = (int(s), sl)
        o, ol = f(r"-- nombre_autres_occupants_logement: (\d+)")
        t["autres_occupants"] = (int(o), ol)
        t["ifi"] = f(r"-- condition_rattaché_foyer_fiscal_parent_ifi: (\w+)")
        t["r844_4"] = f(r"-- personnes_âgées_handicapées_foyer_r844_4: (\w+)")
        # the applicant's nationality: the first `nationalité` after `AL.Demandeur {`
        _, dl = f(r"AL\.Demandeur \{")
        t["nationalite_demandeur"] = _find(lines, dl, b, r"-- nationalité: (\w+)")
        tests.append(t)
    return tests


# ------------------------------------------------------------------------- US §121

def _d(s):
    return dt.date.fromisoformat(s)


def add_years(d, n):
    """Catala `date + n year` (no 29 February occurs in these tests)."""
    return d.replace(year=d.year + n)


def aggregate_days(periods, sale):
    """section_121.catala_en:179-191 at commit 2694b17."""
    total = 0
    for b, e in periods:
        if sale <= add_years(b, 5):
            total += (e - b).days
        elif sale >= add_years(e, 5):
            total += 0
        else:
            total += (add_years(e, 5) - sale).days
    return total


def us_tests():
    """Data scope and the six test scopes of test_section_121.catala_en."""
    lines = common.read_ext("catala-examples", "us_tax_code", "tests",
                            "test_section_121.catala_en").splitlines()
    data = {"lines": lines}
    periods = {}
    for i, l in enumerate(lines, 1):
        m = re.match(r"\s+definition (period_\w+) equals", l)
        if m:
            b = re.search(r"begin: \|([\d-]+)\|", lines[i + 1]).group(1)
            e = re.search(r"end: \|([\d-]+)\|", lines[i + 2]).group(1)
            periods[m.group(1)] = ((_d(b), _d(e)), i)
    data["periods"] = periods
    data["sale"] = (_d(re.search(r"\|([\d-]+)\|", lines[18]).group(1)), 19)
    assert "date_of_sale_or_exchange" in lines[18]
    data["gain"] = (int(re.search(r"\$([\d,]+)", lines[20]).group(1).replace(",", "")), 21)
    assert "gain_from_sale_or_exchange_of_property" in lines[20]

    persons = {}
    for i, l in enumerate(lines, 1):
        m = re.match(r"\s+definition (person_\w+) equals", l)
        if m:
            p = {"line": i}
            k = i
            while "}" not in lines[k]:
                k += 1
            body = " ".join(lines[i:k + 1])
            own = re.search(r"property_ownage: \[([^\]]*)\]", body).group(1)
            use = re.search(r"property_usage_as_principal_residence:\s*\[([^\]]*)\]", body).group(1)
            p["own"] = [periods[x.strip()][0] for x in own.split(";")]
            p["use"] = [periods[x.strip()][0] for x in use.split(";")]
            p["other"] = re.search(r"OtherSection121aSale\.(\w+)", body).group(1)
            persons[m.group(1)] = p
    data["persons"] = persons

    tests = []
    for name, a, b in _blocks(lines, r"scope (Test\d+):"):
        body = "\n".join(lines[a - 1:b])
        t = {"name": name, "lines": (a, b)}
        decl = next(i for i, l in enumerate(lines, 1) if l == f"declaration scope {name}:")
        t["scope"] = re.search(r"scope T\.(\w+)", lines[decl]).group(1)
        t["assert_line"] = next(n for n in range(a, b + 1) if "assertion" in lines[n - 1])
        if t["scope"] == "Section121SinglePerson":
            own = re.search(r"property_ownage equals \[([^\]]*)\]", body).group(1)
            use = re.search(r"property_usage_as_principal_residence equals\s*\[([^\]]*)\]", body).group(1)
            per = lambda s: [periods[x.strip().replace("data_.", "")][0] for x in s.split(";")]
            t["persons"] = [{"own": per(own), "use": per(use),
                             "other": re.search(r"OtherSection121aSale\.(\w+)", body).group(1),
                             "line": a}]
            t["return_type"] = None
        else:
            if "SingleReturn content" in body:
                t["return_type"] = "single"
                who = [re.search(r"SingleReturn content data_\.(\w+)", body).group(1)]
            else:
                t["return_type"] = "joint"
                who = re.findall(r"-- person[12]: data_\.(\w+)", body)
            t["persons"] = [dict(persons[w], name=w) for w in who]
        tests.append(t)
    return data, tests
