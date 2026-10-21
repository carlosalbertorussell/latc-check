"""M2 for the French family benefits (FR-PF, FR-AF-1..3), both conversions.

For every table: the official suite of its rule, the tests mapped by the conversion
(official_examples.csv), the unmapped tests with the conversion's stated reason and the
reason categories that apply, and the declared-value usage when every test of the suite
is placed on the table's attributes regardless of the slice (common.usage).

Placement uses each table's own labels and cut points at 2020-05-01 (ceilings 943,02 /
711,49 EUR, D521-3 ceilings 2020 with n children having droit_ouvert); ages are measured
at each test's own date. The second coder's resource labels depend on the computed amount
(zone dégressive = plafond + 12 x allocation); those are evaluated through the unmodified
Catala 1.3.0 Python build, with the test's children shifted to 2020-05-01 at equal ages.

Run: python3.12 -I paperC/analysis/m2_fr_af.py   (writes paperC/analysis/out/m2_fr_af.json)
Needs paperC/analysis/fetch_sources.sh to have been run.
"""

import datetime as dt
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


PF_FILE = "allocations_familiales/tests/tests_ouverture_droits.catala_fr"
AF_FILE = "allocations_familiales/tests/tests_allocations_familiales.catala_fr"

ASCII = str.maketrans("éèêàÀÉ", "eeeaAE")


def _ascii(name):
    return name.translate(ASCII)


def _money(s):
    s = s.replace("€", "").replace(" ", "").replace(",", ".").strip()
    return f"{float(s):.2f}"


def _records(lines, start, end):
    """Records `{ -- field: value ... }` between line indices start..end (0-based)."""
    out, cur = [], None
    for i in range(start, end):
        s = lines[i].strip()
        if s.endswith("{"):
            cur = {"line": i + 1}
        elif s.startswith("--") and cur is not None:
            k, v = s[2:].split(":", 1)
            cur[k.strip()] = v.strip()
        elif s.startswith("}") and cur is not None:
            out.append(cur)
            cur = None
    return out


def _child(rec):
    g = lambda k: rec.get(k, rec.get("d_" + k))  # noqa: E731
    return {
        "line": rec["line"],
        "naissance": g("date_de_naissance").strip("|"),
        "remuneration": _money(g("rémuneration_mensuelle")),
        "prise": _ascii(g("prise_en_charge").split(".")[-1]),
        "deja": g("a_déjà_ouvert_droit_aux_allocations_familiales") == "vrai",
        "apl": g("bénéficie_titre_personnel_aide_personnelle_logement") == "vrai",
        "obligation": _ascii(rec["obligation_scolaire"].split(".")[-1]) if "obligation_scolaire" in rec else None,
    }


def _blocks(lines):
    """(name, start, end) of each `champ d'application X:` body (0-based, end exclusive)."""
    heads = [(i, re.match(r"champ d'application (\w+):", l.strip()).group(1))
             for i, l in enumerate(lines) if re.match(r"champ d'application \w+:", l.strip())]
    out = []
    for k, (i, name) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        out.append((name, i, end))
    return out


def _data_children(lines):
    """enfantN definitions of scope Données: name -> child."""
    kids = {}
    for name, s, e in _blocks(lines):
        if name != "Données":
            continue
        for i in range(s, e):
            m = re.match(r"définition (enfant\d+) égal à", lines[i].strip())
            if m:
                rec = _records(lines, i, e)[0]
                kids[m.group(1)] = _child(rec)
    return kids


def pf_children():
    """The four children of tests_ouverture_droits Test1 with their asserted droit_ouvert."""
    lines = common.read_ext("catala-examples", PF_FILE).splitlines()
    kids = _data_children(lines)
    out = []
    for name, s, e in _blocks(lines):
        if name != "Test1":
            continue
        date = res = None
        for i in range(s, e):
            t = lines[i].strip()
            if t.startswith("définition f.date_courante"):
                date = t.split("|")[1]
            if t.startswith("définition f.résidence"):
                res = _ascii(t.split()[-1])
            m = re.match(r"assertion \((non )?\(?f\.droit_ouvert de données\.(enfant\d+)\)", t)
            if m:
                c = dict(kids[m.group(2)])
                c.update(case=f"ouverture_droits.Test1.{m.group(2)}", assert_line=i + 1,
                         expected=m.group(1) is None)
                out.append(c)
        for c in out:
            c["date"], c["residence"], c["test_line"] = date, res, s + 1
    return out


def af_tests():
    lines = common.read_ext("catala-examples", AF_FILE).splitlines()
    data = _data_children(lines)
    tests = []
    for name, s, e in _blocks(lines):
        if not name.startswith("Test"):
            continue
        t = {"name": name, "line": s + 1, "est_parent": False, "titre_I": False, "avant_2012": False}
        body = "\n".join(lines[s:e])
        m = re.search(r"définition f\.i_enfants égal à\s*\[(.*?)\]", body, re.S)
        inner = m.group(1)
        if "{" in inner:
            off = body[:m.start()].count("\n")
            j = s + off
            t["children"] = [_child(r) for r in _records(lines, j, e)]
        else:
            t["children"] = [dict(data[x.split(".")[1]]) for x in re.findall(r"données\.enfant\d+", inner)]
        t["ressources"] = _money(re.search(r"i_ressources_ménage égal à ([\d ,]+) ?€", body).group(1))
        t["date"] = re.search(r"i_date_courante égal à \|([\d-]+)\|", body).group(1)
        t["residence"] = _ascii(re.search(r"i_résidence égal à (\w+)", body).group(1))
        t["est_parent"] = "i_personne_charge_effective_permanente_est_parent rempli" in body
        t["titre_I"] = "remplit_titre_I rempli" in body
        t["avant_2012"] = "i_avait_enfant_à_charge_avant_1er_janvier_2012 rempli" in body
        t["expected"] = _money(re.search(r"assertion f\.i_montant_versé = ([\d ,]+) ?€", body).group(1))
        tests.append(t)
    return tests


# ------------------------------------------------------------------ date helpers

def d(iso):
    return dt.date.fromisoformat(iso)


def plus_years(b, n):
    """Catala `b + n an` for the birth dates of the tests (none is a 29 February)."""
    return b.replace(year=b.year + n)


def derived_obligation(b, dc):
    """obligation_scolaire as InterfaceAllocationsFamiliales derives it (epilogue.catala_fr:121-131)."""
    if plus_years(b, 3) >= dc:
        return "Avant"
    if plus_years(b, 16) >= dc:
        return "Pendant"
    return "Apres"


CEILING_2020 = {"Mayotte": 711.49, "otherwise": 943.02}


def ceiling(residence):
    return CEILING_2020["Mayotte" if residence == "Mayotte" else "otherwise"]


def droit_ouvert(child, dc, residence):
    """PrestationsFamiliales.droit_ouvert by its three rules (securite_sociale_L.catala_fr:52-72,
    autres_codes.catala_fr:21-27), with the 2020-05-01 earnings ceiling of the tables."""
    if child["apl"]:
        return False
    b = d(child["naissance"])
    obl = derived_obligation(b, dc)
    if obl in ("Avant", "Pendant"):
        return True
    return float(child["remuneration"]) <= ceiling(residence) and plus_years(b, 20) > dc


# ------------------------------------------------------------------ encoding access

def branch_tree(branch):
    """Extract paperC/ of origin/<branch> (git archive) into _ext/branches/<commit>/."""
    commit = common.branch_commit(branch)
    root = os.path.join(common.HERE, "_ext", "branches", commit)
    if not os.path.isdir(os.path.join(root, "paperC")):
        os.makedirs(root, exist_ok=True)
        tar = subprocess.run(["git", "-C", common.REPO, "archive", f"origin/{branch}", "paperC"],
                             check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", root], input=tar, check=True)
    return os.path.join(root, "paperC")


_ORACLE2 = None


def encoding():
    """The second coder's oracle module (FR-AF-2 folder) of origin/paperc-code2-fr; used only
    for its `call_interface`, a thin call of the unmodified Catala 1.3.0 Python build that
    returns the amount and the computed components (ceilings, n, allocation)."""
    global _ORACLE2
    if _ORACLE2 is None:
        import importlib.util
        path = os.path.join(branch_tree("paperc-code2-fr"), "specs2", "FR-AF-2", "oracle.py")
        spec = importlib.util.spec_from_file_location("oracle2_fr_af_2", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ORACLE2 = mod
    return _ORACLE2


FIXED = d("2020-05-01")
PERIOD = (d("2020-04-01"), d("2020-12-31"))


def shifted(test):
    """The test's children with birth dates moved by (2020-05-01 - test date) days, so that the
    household can be evaluated with the table's 2020-05-01 parameters at the same ages."""
    delta = FIXED - d(test["date"])
    return [dict(c, naissance=(d(c["naissance"]) + delta).isoformat()) for c in test["children"]]


def run_interface(test, kids=None):
    """Encoding call at 2020-05-01 for the test household (children shifted to keep ages)."""
    enc = encoding()
    kids = kids if kids is not None else shifted(test)
    ch = [{"naissance": d(c["naissance"]), "remuneration": c["remuneration"], "prise": c["prise"],
           "deja_ouvert": c["deja"], "aide_logement": c["apl"]} for c in kids]
    cents = enc.cents(enc.Money(test["ressources"]))
    return enc.call_interface(ch, cents, test["residence"], FIXED, test["est_parent"],
                              test["titre_I"], test["avant_2012"])


# ================================================================== tables

B1, B2 = "paperc-data-fr", "paperc-code2-fr"
TABLES = [  # (conversion, table, branch, folder, conversion record)
    ("first", "FR-PF", B1, "paperC/specs/FR-PF", "paperC/specs/FR-PF/CONVERSION.md"),
    ("first", "FR-AF-1", B1, "paperC/specs/FR-AF-1", "paperC/specs/FR-AF-1/CONVERSION.md"),
    ("first", "FR-AF-2", B1, "paperC/specs/FR-AF-2", "paperC/specs/FR-AF-2/CONVERSION.md"),
    ("first", "FR-AF-3", B1, "paperC/specs/FR-AF-3", "paperC/specs/FR-AF-3/CONVERSION.md"),
    ("second", "FR-PF", B2, "paperC/specs2/FR-PF", "paperC/specs2/FR-PF/CONVERSION_2.md"),
    ("second", "FR-AF-1", B2, "paperC/specs2/FR-AF-1", "paperC/specs2/FR-AF-1/CONVERSION_2.md"),
    ("second", "FR-AF-2", B2, "paperC/specs2/FR-AF-2", "paperC/specs2/FR-AF-2/CONVERSION_2.md"),
    ("second", "FR-AF-3", B2, "paperC/specs2/FR-AF-3", "paperC/specs2/FR-AF-3/CONVERSION_2.md"),
]
L751_1 = {"Guadeloupe", "Guyane", "Martinique", "LaReunion", "SaintBarthelemy", "SaintMartin"}
B = lambda x: "true" if x else "false"  # noqa: E731


# --- first coder's labels (spec.json intervals of origin/paperc-data-fr)

def age7(b, dc):
    """FR-AF-1..3 age bands (spec.json `intervals`; CONVERSION.md A6)."""
    if plus_years(b, 3) >= dc:
        return "a00_03"
    if plus_years(b, 11) > dc:
        return "a03_11"
    if plus_years(b, 14) > dc:
        return "a11_14"
    if plus_years(b, 16) >= dc:
        return "a14_16"
    if (plus_years(b, 20) - dc).days >= 365:
        return "a16_19"
    if plus_years(b, 20) > dc:
        return "a19_20"
    return "a20_plus"


def age4(b, dc):
    """FR-PF age bands (spec.json `intervals`; CONVERSION.md C5)."""
    if plus_years(b, 3) >= dc:
        return "a00_03"
    if plus_years(b, 16) >= dc:
        return "a03_16"
    if plus_years(b, 20) > dc:
        return "a16_20"
    return "a20_plus"


def rem3_first(eur, residence):
    """FR-PF: lt/eq/gt the residence's ceiling (CONVERSION.md C6)."""
    x, c = round(float(eur), 2), ceiling(residence)
    return "lt_plafond" if x < c else ("eq_plafond" if x == c else "gt_plafond")


def rem2_first(eur, residence):
    """FR-AF: le_plafond / gt_plafond (CONVERSION.md A7)."""
    return "le_plafond" if float(eur) <= ceiling(residence) else "gt_plafond"


def plafond_I(n):
    return 57759 + 5775 * n  # CONVERSION.md A5 (decrets_divers.catala_fr:101-122)


def plafond_II(n):
    return 80831 + 5775 * n


def res5(r, n):
    r = float(r)
    if r < plafond_I(n):
        return "lt_plafond_I"
    if r == plafond_I(n):
        return "eq_plafond_I"
    if r < plafond_II(n):
        return "entre_I_II"
    return "eq_plafond_II" if r == plafond_II(n) else "gt_plafond_II"


def res3(r, n):
    r = float(r)
    return "le_plafond_I" if r <= plafond_I(n) else ("gt_I_le_II" if r <= plafond_II(n) else "gt_plafond_II")


# --- second coder's labels (CONVERSION_2.md C2, C3, A3, A4 of origin/paperc-code2-fr)

def res_group(name):
    if name == "Mayotte":
        return "mayotte"
    return "drom_l751_1" if name in L751_1 else "metropole"


def rem_second(eur):
    x = round(float(eur), 2)
    return "jusqu_plafond_mayotte" if x <= 711.49 else ("entre_plafonds" if x <= 943.02 else "au_dessus_plafonds")


def age9(b, dc):
    if plus_years(b, 3) >= dc:
        return "moins_3"
    if plus_years(b, 11) > dc:
        return "3_11"
    if plus_years(b, 14) > dc:
        return "11_14"
    if plus_years(b, 16) > dc:
        return "14_16"
    if plus_years(b, 16) == dc:
        return "anniversaire_16"
    if (plus_years(b, 20) - dc).days >= 365:
        return "16_19"
    if plus_years(b, 20) > dc:
        return "19_20"
    if plus_years(b, 11) > dt.date(2008, 4, 30):
        return "20_23"
    return "23_plus"


def age20(b, dc):
    return "moins_20" if plus_years(b, 20) > dc else "20_ou_plus"


PRISE_GROUP = {"EffectiveEtPermanente": "complete", "GardeAlterneeAllocataireUnique": "complete",
               "ServicesSociauxAllocationVerseeALaFamille": "complete",
               "GardeAlterneePartageAllocations": "partagee",
               "ServicesSociauxAllocationVerseeAuxServicesSociaux": "services_sociaux"}


# ================================================================== placement

def n_droit(test):
    dc = d(test["date"])
    return sum(droit_ouvert(c, dc, test["residence"]) for c in test["children"])


def place(conv, table, test, slots_note):
    """Row dict attr -> label (UNKNOWN where the test cannot be placed) for a household test."""
    U = common.UNKNOWN
    dc, res, kids = d(test["date"]), test["residence"], test["children"]
    n = n_droit(test)
    row = {}
    if conv == "first":
        if table == "FR-AF-1":
            row.update(residence=res, ressources=res5(test["ressources"], n),
                       avait_enfant_avant_2012=B(test["avant_2012"]),
                       est_parent=B(test["est_parent"]), titre_I=B(test["titre_I"]))
            for k in range(3):
                row[f"enfant{k + 1}_age"] = age7(d(kids[k]["naissance"]), dc) if k < len(kids) else "absent"
        elif table == "FR-AF-2":
            row.update(residence=res, ressources=res3(test["ressources"], n))
            for k in range(2):
                c = kids[k] if k < len(kids) else None
                row[f"enfant{k + 1}_age"] = age7(d(c["naissance"]), dc) if c else U
                row[f"enfant{k + 1}_remuneration"] = rem2_first(c["remuneration"], res) if c else U
                row[f"enfant{k + 1}_prise_en_charge"] = c["prise"] if c else U
        elif table == "FR-AF-3":
            for k in range(3):
                c = kids[k] if k < len(kids) else None
                row[f"enfant{k + 1}_age"] = age7(d(c["naissance"]), dc) if c else U
                row[f"enfant{k + 1}_remuneration"] = rem2_first(c["remuneration"], res) if c else U
                row[f"enfant{k + 1}_deja_ouvert"] = B(c["deja"]) if c else U
                row[f"enfant{k + 1}_apl"] = B(c["apl"]) if c else U
    else:
        nslots = {"FR-AF-1": 1, "FR-AF-2": 2, "FR-AF-3": 3}[table]
        _, comp = run_interface(test)
        enc = encoding()
        row.update(residence=res_group(res), ressources=enc.ressources_region(comp), avant_2012=B(test["avant_2012"]))
        if table == "FR-AF-1":
            row["attributaire"] = {(True, False): "parent", (True, True): "parent", (False, True): "tiers_titre_I",
                                   (False, False): "aucun"}[(test["est_parent"], test["titre_I"])]
        fields = {"FR-AF-1": ["age", "remuneration", "prise_en_charge", "deja_ouvert", "aide_logement"],
                  "FR-AF-2": ["age", "remuneration", "prise_en_charge"], "FR-AF-3": ["age", "deja_ouvert"]}[table]
        for k in range(nslots):
            c = kids[k] if k < len(kids) else None
            vals = {} if c is None else {
                "age": age9(d(c["naissance"]), dc), "remuneration": rem_second(c["remuneration"]),
                "prise_en_charge": PRISE_GROUP[c["prise"]], "deja_ouvert": B(c["deja"]), "aide_logement": B(c["apl"])}
            for f in fields:
                row[f"e{k + 1}_{f}"] = vals.get(f, U)
        slots_note["n_droit_ouvert_encoding"] = comp["n_droit_ouvert"]
    slots_note["n_droit_ouvert"] = n
    return row


def place_pf_child(conv, c, date, residence):
    dc = d(date)
    b = d(c["naissance"])
    obl = c["obligation"] or derived_obligation(b, dc)
    if conv == "first":
        return {"residence": residence, "obligation_scolaire": obl, "prise_en_charge": c["prise"],
                "age": age4(b, dc), "remuneration": rem3_first(c["remuneration"], residence), "apl": B(c["apl"])}
    return {"residence": res_group(residence), "obligation_scolaire": obl,
            "remuneration_mensuelle": rem_second(c["remuneration"]), "age_20_ans": age20(b, dc),
            "aide_logement_personnelle": B(c["apl"])}


# ================================================================== unmapped reasons

def categories(conv, table, test):
    """Every reason category that applies to a household test on an FR-AF table."""
    out = []
    dc, kids, res = d(test["date"]), test["children"], test["residence"]
    if not (PERIOD[0] <= dc <= PERIOD[1]):
        out.append(("other period", f"date_courante {test['date']} outside [2020-04-01, 2020-12-31]"))
    need = {("first", "FR-AF-1"): (1, 3), ("first", "FR-AF-2"): (2, 2), ("first", "FR-AF-3"): (3, 3),
            ("second", "FR-AF-1"): (1, 1), ("second", "FR-AF-2"): (2, 2), ("second", "FR-AF-3"): (3, 3)}[(conv, table)]
    if not need[0] <= len(kids) <= need[1]:
        out.append(("other household shape", f"{len(kids)} children; table holds {need[0]}-{need[1]}"))
    fixed = []
    if conv == "first":
        if table == "FR-AF-1":
            for k, c in enumerate(kids[:3]):
                if rem2_first(c["remuneration"], res) != "le_plafond":
                    fixed.append(f"enfant{k + 1}_remuneration gt_plafond (fixed le_plafond)")
                if c["prise"] != "EffectiveEtPermanente":
                    fixed.append(f"enfant{k + 1}_prise_en_charge {c['prise']} (fixed EffectiveEtPermanente)")
        if table in ("FR-AF-2", "FR-AF-3") and test["avant_2012"]:
            fixed.append("avait_enfant_avant_2012 true (fixed false)")
        if table == "FR-AF-3":
            if res != "Metropole":
                fixed.append(f"residence {res} (fixed Metropole)")
            if res3(test["ressources"], n_droit(test)) != "le_plafond_I":
                fixed.append("ressources above plafond I (fixed le_plafond_I)")
            for k, c in enumerate(kids[:3]):
                if c["prise"] != "EffectiveEtPermanente":
                    fixed.append(f"enfant{k + 1}_prise_en_charge {c['prise']} (fixed EffectiveEtPermanente)")
    else:
        if table == "FR-AF-3":
            for k, c in enumerate(kids[:3]):
                if rem_second(c["remuneration"]) != "jusqu_plafond_mayotte":
                    fixed.append(f"e{k + 1} earnings {c['remuneration']} (fixed jusqu_plafond_mayotte)")
                if PRISE_GROUP[c["prise"]] != "complete":
                    fixed.append(f"e{k + 1} prise_en_charge {c['prise']} (fixed complete)")
    if fixed:
        out.append(("other: fixed input outside its fixed band", "; ".join(fixed)))
    return out


def stated_reason(branch, path, name):
    """The conversion record's line naming the test among its unmapped tests."""
    lines = common.git_lines(branch, path)
    start = next(i for i, l in enumerate(lines) if l.startswith("Unmapped"))
    pat = re.compile(rf"(?<![/\w]){name}\b(?!/)")
    for i in range(start, len(lines)):
        if pat.search(lines[i]):
            return lines[i].strip(), f"{branch}:{path}:{i + 1}"
    return None, None


# ================================================================== README cross-check

def readme_unused():
    """Unused values stated by each README, as {(conv, table): {attr: set}}."""
    out = {}
    lines = common.git_lines(B1, "paperC/specs/README-FR.md")
    s = next(i for i, l in enumerate(lines) if l.startswith("## Declared values the official examples never use"))
    for l in lines[s + 1:]:
        if l.startswith("## "):
            break
        m = re.match(r"\| (FR-[A-Z0-9-]+) \| ([^|]+) \| ([^|]+) \|", l)
        if not m or m.group(1) == "Table":
            continue
        vals = set() if "(none)" in m.group(3) else {v.strip() for v in m.group(3).split(",")}
        for a in m.group(2).split(","):
            a = a.strip()
            mm = re.match(r"enfant(\d)-(\d)_(\w+)", a)
            names = [f"enfant{k}_{mm.group(3)}" for k in range(int(mm.group(1)), int(mm.group(2)) + 1)] if mm else [a]
            for nme in names:
                out.setdefault(("first", m.group(1)), {})[nme] = vals
    lines = common.git_lines(B2, "paperC/specs2/README-FR-CODE2.md")
    cur = None
    for l in lines:
        m = re.match(r"### (FR-[A-Z0-9-]+) \(", l)
        if m:
            cur = m.group(1)
            out.setdefault(("second", cur), {})
            continue
        if l.startswith("## ") and cur:
            cur = None if "Declared" not in l else cur
        m = re.match(r"\* `(\w+)`: (.+) \(\d+/\d+\)", l)
        if cur and m:
            out[("second", cur)][m.group(1)] = {v.strip() for v in m.group(2).split(",")}
    return out


# ================================================================== main

def main():
    pf = pf_children()
    af = af_tests()
    readme = readme_unused()
    results = []
    shift_check = []
    for t in af:  # ages kept by the 2020-05-01 shift used for encoding calls
        for c0, c1 in zip(t["children"], shifted(t)):
            a = (age9(d(c0["naissance"]), d(t["date"])), age7(d(c0["naissance"]), d(t["date"])))
            b = (age9(d(c1["naissance"]), FIXED), age7(d(c1["naissance"]), FIXED))
            if a != b:
                shift_check.append({"test": t["name"], "child_line": c0["line"], "at_date": a, "shifted": b})
    for conv, table, branch, folder, record in TABLES:
        spec = common.load_spec(branch, folder)
        names = common.attr_names(spec)
        mapped = common.load_csv(branch, f"{folder}/official_examples.csv")
        mapped_ids = [r["case_id"] for r in mapped]
        mapped_rows = [{n: r[n] for n in names} for r in mapped]
        valid = common.valid_rows(branch, folder, spec)
        entry = {"conversion": conv, "table": table, "branch": branch, "folder": folder,
                 "branch_commit": common.branch_commit(branch), "mapped_case_ids": mapped_ids}
        if table == "FR-PF":
            suite = [(c["case"], place_pf_child(conv, c, c["date"], c["residence"])) for c in pf]
            entry["suite"] = "tests_ouverture_droits.catala_fr Test1 (4 droit_ouvert assertions)"
            entry["unmapped"] = []
            entry["placements"] = [{"case": cid, "row": r} for cid, r in suite]
            entry["placement_equals_mapped"] = [r for _, r in suite] == mapped_rows
            entry["usage"] = common.usage(spec, mapped_rows, [r for _, r in suite], valid)
            var = []
            for t in af:
                for k, c in enumerate(t["children"]):
                    var.append((f"{t['name']}.child{k + 1}", t, c, place_pf_child(conv, c, t["date"], t["residence"])))
            entry["variant"] = {
                "suite": "the 4 asserted children plus every child of the 14 household tests "
                         "(obligation_scolaire derived as epilogue.catala_fr:121-131); droit_ouvert is "
                         "computed inside those tests and never asserted",
                "n_children_added": len(var),
                "placements": [{"case": cid, "date": t["date"], "line": c["line"], "row": r} for cid, t, c, r in var],
                "usage": common.usage(spec, mapped_rows, [r for _, r in suite] + [v[3] for v in var], valid),
            }
        else:
            entry["suite"] = "tests_allocations_familiales.catala_fr Test1-Test14"
            rows, unm, places = [], [], []
            for t in af:
                note = {}
                r = place(conv, table, t, note)
                ismapped = any(re.split(r"[./]", m)[-1] == t["name"] for m in mapped_ids)
                nslots = {"FR-AF-1": 3 if conv == "first" else 1, "FR-AF-2": 2, "FR-AF-3": 3}[table]
                places.append({"test": t["name"], "line": t["line"], "date": t["date"], "mapped": ismapped,
                               "row": r, "children": len(t["children"]),
                               "children_not_placed": max(0, len(t["children"]) - nslots), **note})
                rows.append(r)
                if not ismapped:
                    txt, src = stated_reason(branch, record, t["name"])
                    unm.append({"test": t["name"], "line": t["line"], "stated": txt, "stated_source": src,
                                "categories": categories(conv, table, t)})
            mrows = [p["row"] for p in places if p["mapped"]]
            key = lambda r: sorted(r.items())  # noqa: E731
            entry["placement_equals_mapped"] = sorted(map(key, mrows)) == sorted(map(key, mapped_rows))
            entry["unmapped"] = unm
            entry["placements"] = places
            entry["usage"] = common.usage(spec, mapped_rows, rows, valid)
        # README cross-check (mapped tests only)
        stated = readme.get((conv, table), {})
        mine = {a: set(v["unused_mapped"]) for a, v in entry["usage"]["attributes"].items() if v["unused_mapped"]}
        diffs = []
        for a in sorted(set(stated) | set(mine)):
            if stated.get(a, set()) != mine.get(a, set()):
                diffs.append({"attribute": a, "readme": sorted(stated.get(a, set())), "computed": sorted(mine.get(a, set()))})
        entry["readme_check"] = diffs
        entry["suite_size"] = len(pf) if table == "FR-PF" else len(af)
        entry["mapped"] = len(mapped_ids)
        results.append(entry)
    common.write_json("m2_fr_af.json", {"shift_check": shift_check, "tables": results})
    for e in results:
        u = e["usage"]
        print(f"{e['conversion']:6} {e['table']:8} suite {e['suite_size']:2} mapped {e['mapped']} "
              f"declared {u['declared_total']:3} unused mapped {u['unused_mapped_total']:3} suite {u['unused_suite_total']:3} "
              f"missed_valid {u['missed_valid_mapped']}/{u['missed_valid_suite']} of {u['valid_total']} "
              f"place==mapped {e['placement_equals_mapped']} readme_diffs {len(e['readme_check'])}")
        if "variant" in e:
            v = e["variant"]["usage"]
            print(f"       variant +{e['variant']['n_children_added']} children: unused {v['unused_suite_total']} "
                  f"missed_valid {v['missed_valid_suite']}")
    print("shift check mismatches:", len(shift_check))


if __name__ == "__main__":
    main()
