#!/usr/bin/env python3
"""Oracle for a Paper C sample (second coder, French family benefits).

The same file sits in every folder paperC/specs2/FR-*/ ; only SAMPLE_ID differs.
It evaluates the Catala 1.3.0 Python build in paperC/catala_family_benefits/ (unedited),
at the representative values declared in spec.json, and maps the official Catala tests
onto the table.

  python oracle.py --enumerate        check the official tests, then write ground_truth.csv
  python oracle.py --check-official   re-run every official test through the encoding and
                                      the oracle and print pass counts
  python oracle.py --write-official   write official_examples.csv
  python oracle.py --check-groups     check that every member of a grouped enum label gives
                                      the same output as its representative

Python 3.12 or later (the Catala 1.3.0 runtime needs it). Standard library only.
"""

SAMPLE_ID = "FR-PF"

import csv
import datetime as dt
import itertools
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CATALA_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "catala_family_benefits"))
sys.path.insert(0, os.path.join(CATALA_DIR, "runtime", "catala"))
sys.path.insert(0, CATALA_DIR)

if sys.version_info < (3, 12):
    sys.exit("Python 3.12 or later is required by the Catala 1.3.0 runtime")

from catala_runtime import Array, Bool, Date, Integer, Money, Unit, catala_set_lang, Lang  # noqa: E402
from generated import Allocations_familiales as AF  # noqa: E402
from generated import France  # noqa: E402

catala_set_lang(Lang.Fr)

# ---------------------------------------------------------------- fixed date and labels

FIXED_DATE = dt.date(2020, 5, 1)
# Every date-dependent parameter of the encoding is constant on this period (BMAF from
# 2020-04-01, SMIC 2020, D521-3 ceilings 2020, Mayotte rates 2020); an official test whose
# date lies in it is mapped with its ages measured at its own date.
PERIOD = (dt.date(2020, 4, 1), dt.date(2020, 12, 31))

RESIDENCE_REP = {"metropole": "Metropole", "drom_l751_1": "Guadeloupe", "mayotte": "Mayotte"}
RESIDENCE_MEMBERS = {
    "metropole": ["Metropole", "SaintPierreEtMiquelon"],
    "drom_l751_1": ["Guadeloupe", "Guyane", "Martinique", "LaReunion", "SaintBarthelemy", "SaintMartin"],
    "mayotte": ["Mayotte"],
}
PRISE_REP = {
    "complete": "EffectiveEtPermanente",
    "partagee": "GardeAlterneePartageAllocations",
    "services_sociaux": "ServicesSociauxAllocationVerseeAuxServicesSociaux",
}
PRISE_MEMBERS = {
    "complete": ["EffectiveEtPermanente", "GardeAlterneeAllocataireUnique",
                 "ServicesSociauxAllocationVerseeALaFamille"],
    "partagee": ["GardeAlterneePartageAllocations"],
    "services_sociaux": ["ServicesSociauxAllocationVerseeAuxServicesSociaux"],
}
# Monthly earnings ceiling (smic.brut_horaire * 55%) * 169 at 2020-05-01, as computed by
# the encoding: Mayotte 7,66 EUR -> 711,49 EUR; every other collectivite 10,15 EUR -> 943,02 EUR.
CEILING_MAYOTTE = "711.49"
CEILING_OTHERS = "943.02"
REM_REP = {"jusqu_plafond_mayotte": "0.00", "entre_plafonds": "800.00", "au_dessus_plafonds": "1500.00"}
# Birth dates; every age band is defined by the comparisons the code makes (see CONVERSION_2.md).
AGE_REP = {
    "moins_3": "2019-05-01",
    "3_11": "2013-05-01",
    "11_14": "2008-05-01",
    "14_16": "2005-05-01",
    "anniversaire_16": "2004-05-01",
    "16_19": "2002-05-01",
    "19_20": "2000-11-01",
    "20_23": "1999-05-01",
    "23_plus": "1995-05-01",
}
AGE20_REP = {"moins_20": "2005-01-01", "20_ou_plus": "1998-01-01"}
RESSOURCES_LABELS = ["jusqu_plafond_I", "zone_degressive_I", "entre_plafonds_I_II",
                     "zone_degressive_II", "au_dela_plafond_II"]
BOOL = {"true": True, "false": False}

# Per-child inputs that are not attributes of a sample take these values.
CHILD_DEFAULTS = {"remuneration": "jusqu_plafond_mayotte", "prise_en_charge": "complete",
                  "deja_ouvert": "true", "aide_logement": "false"}

SAMPLES = {
    "FR-PF": {"kind": "PF",
              "attributes": ["residence", "obligation_scolaire", "remuneration_mensuelle",
                             "age_20_ans", "aide_logement_personnelle"]},
    "FR-AF-1": {"kind": "AF", "children": 1, "household": ["residence", "attributaire", "ressources", "avant_2012"],
                "child": ["age", "remuneration", "prise_en_charge", "deja_ouvert", "aide_logement"]},
    "FR-AF-2": {"kind": "AF", "children": 2, "household": ["residence", "ressources", "avant_2012"],
                "child": ["age", "remuneration", "prise_en_charge"]},
    "FR-AF-3": {"kind": "AF", "children": 3, "household": ["residence", "ressources", "avant_2012"],
                "child": ["age", "deja_ouvert"]},
}
CFG = SAMPLES[SAMPLE_ID]


def load_spec():
    with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- encoding helpers

def collectivite(name):
    return France.Collectivite(getattr(France.Collectivite.Code, name), Unit())


def prise(name):
    return AF.PriseEnCharge(getattr(AF.PriseEnCharge.Code, name), Unit())


def obligation(name):
    return AF.SituationObligationScolaire(getattr(AF.SituationObligationScolaire.Code, name), Unit())


def cdate(d):
    return Date(d.year, d.month, d.day)


def pdate(iso):
    return dt.date.fromisoformat(iso)


def cents(m):
    return int(m)


def money_str(c):
    return f"{c // 100}.{c % 100:02d}"


_captured = {}
_AF_CODE = AF.allocations_familiales.__code__


def _profiler(frame, event, arg):
    # Read the locals of the scope AllocationsFamiliales when it returns; nothing is changed.
    if event == "return" and frame.f_code is _AF_CODE:
        _captured.clear()
        _captured.update(frame.f_locals)


def _opt(name):
    v = _captured[name]
    return v.value[0] if hasattr(v, "value") and not isinstance(v, (Money, Bool)) else v


def call_interface(children, ressources_cents, residence, date, est_parent=True, titre_i=False, avant_2012=False):
    """children: list of dicts with naissance (date), remuneration (str EUR), prise (code name),
    deja_ouvert (bool), aide_logement (bool). Returns (montant cents, captured components)."""
    enfants = [AF.EnfantEntree(
        d_identifiant=Integer(i + 1),
        d_remuneration_mensuelle=Money(c["remuneration"]),
        d_date_de_naissance=cdate(c["naissance"]),
        d_prise_en_charge=prise(c["prise"]),
        d_a_deja_ouvert_droit_aux_allocations_familiales=Bool(c["deja_ouvert"]),
        d_beneficie_titre_personnel_aide_personnelle_logement=Bool(c["aide_logement"]),
    ) for i, c in enumerate(children)]
    _captured.clear()
    sys.setprofile(_profiler)
    try:
        out = AF.interface_allocations_familiales(AF.InterfaceAllocationsFamilialesIn(
            i_date_courante_in=cdate(date),
            i_enfants_in=Array(enfants),
            i_ressources_menage_in=Money(ressources_cents),
            i_residence_in=collectivite(residence),
            i_personne_charge_effective_permanente_est_parent_in=Bool(est_parent),
            i_personne_charge_effective_permanente_remplit_titre_I_in=Bool(titre_i),
            i_avait_enfant_a_charge_avant_1er_janvier_2012_in=Bool(avant_2012),
        ))
    finally:
        sys.setprofile(None)
    comp = {
        "droit_ouvert_base": bool(_opt("droit_ouvert_base")),
        "base": cents(_opt("montant_verse_base")),
        "majoration": cents(_opt("montant_verse_majoration")),
        "forfaitaire": cents(_opt("montant_verse_forfaitaire")),
        "complement_base": cents(_opt("montant_verse_complement_pour_base_et_majoration")),
        "complement_forfaitaire": cents(_opt("montant_verse_complement_pour_forfaitaire")),
        "allocation_pour_complement": cents(_opt("montant_base_complement_pour_base_et_majoration")),
        "plafond_I": cents(_opt("plafond_i_d521_3")),
        "plafond_II": cents(_opt("plafond_i_i_d521_3")),
        "n_droit_ouvert": int(_opt("enfants_a_charge_droit_ouvert_prestation_familiale").length()),
        "outre_mer_l751_1": bool(_captured["prestations_familiales__2"].regime_outre_mer_l751_1),
        "mayotte": residence == "Mayotte",
        "avant_2012": avant_2012,
        "ressources": ressources_cents,
    }
    return cents(out.i_montant_verse), comp


def regime_label(comp):
    """Amount regime from the components the encoding computed (CONVERSION_2.md, section Output)."""
    if not comp["droit_ouvert_base"]:
        return "sans_droit"
    if comp["mayotte"]:
        bareme = "mayotte_avant_2012" if comp["avant_2012"] else "mayotte"
    elif comp["outre_mer_l751_1"] and comp["n_droit_ouvert"] == 1:
        bareme = "outre_mer_un_enfant"
    else:
        bareme = "general"
    parts = []
    if comp["base"] > 0:
        parts.append("B")
    if comp["majoration"] > 0:
        parts.append("M")
    if comp["forfaitaire"] > 0:
        parts.append("F")
    if comp["complement_base"] + comp["complement_forfaitaire"] > 0:
        parts.append("C")
    parts = "+".join(parts) or "nul"
    if bareme == "outre_mer_un_enfant":
        # D755-5 rates and the L755-12 exclusions do not depend on the resource tier.
        return f"{bareme}/{parts}"
    r = comp["ressources"]
    tier = "T1" if r <= comp["plafond_I"] else ("T2" if r <= comp["plafond_II"] else "T3")
    return f"{bareme}/{tier}/{parts}"


def ressources_region(comp):
    """Label of the resources region that the value comp['ressources'] lies in."""
    r, p1, p2 = comp["ressources"], comp["plafond_I"], comp["plafond_II"]
    a12 = 12 * max(comp["allocation_pour_complement"], comp["forfaitaire"])
    if r <= p1:
        return "jusqu_plafond_I"
    if r <= p2:
        return "zone_degressive_I" if r <= p1 + a12 else "entre_plafonds_I_II"
    return "zone_degressive_II" if r <= p2 + a12 else "au_dela_plafond_II"


def ressources_rep(label, p1, p2):
    return {"jusqu_plafond_I": 3000000, "zone_degressive_I": p1 + 100, "entre_plafonds_I_II": p2,
            "zone_degressive_II": p2 + 100, "au_dela_plafond_II": 20000000}[label]


def call_pf(residence, obl, remuneration, naissance, aide_logement, date):
    pf = AF.prestations_familiales(AF.PrestationsFamilialesIn(
        date_courante_in=cdate(date), residence_in=collectivite(residence)))
    enfant = AF.Enfant(
        identifiant=Integer(1),
        obligation_scolaire=obligation(obl),
        remuneration_mensuelle=Money(remuneration),
        date_de_naissance=cdate(naissance),
        prise_en_charge=prise("EffectiveEtPermanente"),
        a_deja_ouvert_droit_aux_allocations_familiales=Bool(True),
        beneficie_titre_personnel_aide_personnelle_logement=Bool(aide_logement),
    )
    return "ouvert" if bool(pf.droit_ouvert(enfant)) else "non_ouvert"


# ---------------------------------------------------------------- evaluation

def exclusion_holds(spec, row):
    # Evaluated as PROTOCOL.md section 2 states: eval with empty builtins, over label strings
    # only; the predicates are the fixed strings of this folder's spec.json.
    for e in spec["exclusions"]:
        if eval(e["predicate"], {"__builtins__": {}}, dict(row)):
            return e["id"]
    return None


def af_children_from_row(row, prise_override=None):
    kids = []
    for j in range(1, CFG["children"] + 1):
        def get(field):
            key = f"e{j}_{field}"
            return row[key] if key in row else CHILD_DEFAULTS[field]
        p = PRISE_REP[get("prise_en_charge")]
        if prise_override and j in prise_override:
            p = prise_override[j]
        kids.append({"naissance": pdate(AGE_REP[get("age")]), "remuneration": REM_REP[get("remuneration")],
                     "prise": p, "deja_ouvert": BOOL[get("deja_ouvert")], "aide_logement": BOOL[get("aide_logement")]})
    return kids


def af_household(row):
    att = row.get("attributaire", "parent")
    est_parent, titre_i = {"parent": (True, False), "tiers_titre_I": (False, True), "aucun": (False, False)}[att]
    return est_parent, titre_i, BOOL[row["avant_2012"]]


def evaluate_detail(row, spec=None, residence_override=None, prise_override=None):
    """Returns (label, note). note is None, or a string for REJECTED / empty-region cells."""
    spec = spec or SPEC
    if exclusion_holds(spec, row):
        return "EXCLUDED", None
    residence = residence_override or RESIDENCE_REP[row["residence"]]
    try:
        if CFG["kind"] == "PF":
            obl = {"Avant": "Avant", "Pendant": "Pendant", "Apres": "Apres"}[row["obligation_scolaire"]]
            return call_pf(residence, obl, REM_REP[row["remuneration_mensuelle"]],
                           pdate(AGE20_REP[row["age_20_ans"]]), BOOL[row["aide_logement_personnelle"]],
                           FIXED_DATE), None
        kids = af_children_from_row(row, prise_override)
        est_parent, titre_i, avant = af_household(row)
        _, comp0 = call_interface(kids, 0, residence, FIXED_DATE, est_parent, titre_i, avant)
        r = ressources_rep(row["ressources"], comp0["plafond_I"], comp0["plafond_II"])
        _, comp = call_interface(kids, r, residence, FIXED_DATE, est_parent, titre_i, avant)
        note = None
        if ressources_region(comp) != row["ressources"]:
            note = f"empty region: representative lies in {ressources_region(comp)}"
        return regime_label(comp), note
    except Exception as exc:  # a Catala runtime error or failed assertion
        return "REJECTED", f"{type(exc).__name__}: {exc}"


def evaluate(row: dict[str, str]) -> str:
    return evaluate_detail(row)[0]


def all_rows(spec):
    names = [a["name"] for a in spec["attributes"]]
    for combo in itertools.product(*[a["values"] for a in spec["attributes"]]):
        yield dict(zip(names, combo))


def _eval_chunk(rows):
    return [evaluate_detail(r) for r in rows]


SPEC = load_spec()

# ---------------------------------------------------------------- official tests
# Line-by-line copies of the official Catala test scopes (catala-examples 2694b17,
# allocations_familiales/tests/). Same inputs as paperC/catala_family_benefits/run_official_tests.py.

def _k(naissance, rem, prise_name, deja=True, apl=False):
    return {"naissance": pdate(naissance), "remuneration": rem, "prise": prise_name,
            "deja_ouvert": deja, "aide_logement": apl}


_D1 = _k("2007-01-01", "0.00", "EffectiveEtPermanente")
_D2 = _k("2009-01-01", "0.00", "EffectiveEtPermanente")
_D3 = _k("2003-01-01", "400.00", "GardeAlterneePartageAllocations")
_D4 = _k("2001-01-01", "1100.00", "EffectiveEtPermanente")
_D5 = _k("2000-01-01", "0.00", "EffectiveEtPermanente")

# (case_id, children, ressources EUR, date, residence, avant_2012, expected EUR, source line)
AF_TESTS = [
    ("tests_allocations_familiales/Test1", [_D1, _D2, _D3, _D4], "30000", "2020-05-01", "Metropole", False, "351.54", 66),
    ("tests_allocations_familiales/Test2", [_D1, _D2, _D5], "30000", "2020-05-01", "Metropole", False, "216.46", 80),
    ("tests_allocations_familiales/Test3", [_D1], "63540", "2020-05-01", "Guyane", False, "24.37", 94),
    ("tests_allocations_familiales/Test4", [_D1, _D3], "67250", "2020-05-01", "Metropole", False, "99.46", 107),
    ("tests_allocations_familiales/Test5", [_D1], "30000", "2020-05-01", "Metropole", False, "0.00", 120),
    ("tests_allocations_familiales/Test6", [_k("2009-11-10", "439", "EffectiveEtPermanente"),
                                            _k("2020-09-25", "1949", "EffectiveEtPermanente")],
     "78830", "2020-05-01", "Guadeloupe", False, "66.30", 132),
    ("tests_allocations_familiales/Test7", [_D1, _D2, _D3, _D4], "30000", "2021-02-01", "Metropole", False, "417.84", 163),
    ("tests_allocations_familiales/Test8", [_k("2004-01-01", "0", "EffectiveEtPermanente"),
                                            _k("2005-01-01", "0", "EffectiveEtPermanente")],
     "69945", "2021-01-01", "Metropole", False, "197.90", 176),
    ("tests_allocations_familiales/Test9", [_k("2001-07-27", "1258", "ServicesSociauxAllocationVerseeAuxServicesSociaux"),
                                            _k("2008-04-27", "1766", "ServicesSociauxAllocationVerseeAuxServicesSociaux")],
     "75786", "2020-05-01", "Guadeloupe", False, "0.00", 206),
    ("tests_allocations_familiales/Test10", [_k("2003-02-22", "0", "EffectiveEtPermanente"),
                                             _k("2013-09-30", "300", "GardeAlterneePartageAllocations")],
     "30000", "2020-04-20", "Metropole", False, "99.46", 236),
    ("tests_allocations_familiales/Test11", [_k("2003-02-22", "0", "EffectiveEtPermanente"),
                                             _k("2013-09-30", "300", "EffectiveEtPermanente"),
                                             _k("2007-04-16", "0", "EffectiveEtPermanente")],
     "30000", "2021-12-31", "Metropole", False, "435.55", 266),
    ("tests_allocations_familiales/Test12", [_k("2003-02-22", "0", "EffectiveEtPermanente"),
                                             _k("2013-09-30", "300", "EffectiveEtPermanente"),
                                             _k("2007-04-16", "0", "EffectiveEtPermanente"),
                                             _k("2012-02-02", "0", "EffectiveEtPermanente")],
     "20000", "2019-08-26", "Mayotte", True, "315.84", 304),
    ("tests_allocations_familiales/Test13", [_k("2008-02-22", "0", "EffectiveEtPermanente")],
     "65000", "2019-08-26", "Mayotte", False, "34.99", 351),
    ("tests_allocations_familiales/Test14", [_k("2004-12-22", "435", "EffectiveEtPermanente"),
                                             _k("2001-12-05", "1682", "GardeAlterneeAllocataireUnique")],
     "64033", "2022-05-01", "Guadeloupe", False, "48.77", 373),
]

# tests_ouverture_droits.catala_fr Test1 (lines 61-67): scope PrestationsFamiliales,
# Metropole, 2020-05-01; (case_id, obligation, birth, earnings, expected droit_ouvert)
PF_TESTS = [
    ("tests_ouverture_droits/Test1/enfant1", "Pendant", "2007-01-01", "0.00", True),
    ("tests_ouverture_droits/Test1/enfant2", "Apres", "2003-01-01", "1000.00", False),
    ("tests_ouverture_droits/Test1/enfant3", "Apres", "2003-01-01", "400.00", True),
    ("tests_ouverture_droits/Test1/enfant4", "Apres", "1999-01-01", "0.00", False),
]


def add_years(d, n):
    return d.replace(year=d.year + n)


def residence_label(name):
    return next(k for k, v in RESIDENCE_MEMBERS.items() if name in v)


def prise_label(name):
    return next(k for k, v in PRISE_MEMBERS.items() if name in v)


def rem_label(eur):
    c = cents(Money(eur))
    if c <= cents(Money(CEILING_MAYOTTE)):
        return "jusqu_plafond_mayotte"
    if c <= cents(Money(CEILING_OTHERS)):
        return "entre_plafonds"
    return "au_dessus_plafonds"


def age_label(b, t):
    if add_years(b, 3) >= t:
        return "moins_3"
    if add_years(b, 11) > t:
        return "3_11"
    if add_years(b, 14) > t:
        return "11_14"
    if add_years(b, 16) > t:
        return "14_16"
    if add_years(b, 16) == t:
        return "anniversaire_16"
    if (add_years(b, 20) - t).days >= 365:
        return "16_19"
    if add_years(b, 20) > t:
        return "19_20"
    if add_years(b, 11) > dt.date(2008, 4, 30):
        return "20_23"
    return "23_plus"


def age20_label(b, t):
    return "moins_20" if add_years(b, 20) > t else "20_ou_plus"


def map_af_test(case):
    """Returns (row, None) or (None, reason)."""
    cid, kids, res, date, residence, avant, expected, line = case
    t = pdate(date)
    if len(kids) != CFG["children"]:
        return None, f"{len(kids)} child(ren) in the test; this table has {CFG['children']}"
    if not (PERIOD[0] <= t <= PERIOD[1]):
        return None, f"date {date} outside the period {PERIOD[0]}..{PERIOD[1]} of the fixed date"
    _, comp = call_interface(kids, cents(Money(res)), residence, t, True, False, avant)
    row = {"residence": residence_label(residence), "attributaire": "parent",
           "ressources": ressources_region(comp), "avant_2012": "true" if avant else "false"}
    for j, k in enumerate(kids, start=1):
        vals = {"age": age_label(k["naissance"], t), "remuneration": rem_label(k["remuneration"]),
                "prise_en_charge": prise_label(k["prise"]),
                "deja_ouvert": "true" if k["deja_ouvert"] else "false",
                "aide_logement": "true" if k["aide_logement"] else "false"}
        for field, v in vals.items():
            if field in CFG["child"]:
                row[f"e{j}_{field}"] = v
            elif v != CHILD_DEFAULTS[field]:
                return None, f"child {j}: {field} = {v}, fixed to {CHILD_DEFAULTS[field]} in this table"
    names = [a["name"] for a in SPEC["attributes"]]
    return {n: row[n] for n in names}, None


def map_pf_test(case):
    cid, obl, naissance, rem, expected = case
    row = {"residence": "metropole", "obligation_scolaire": obl, "remuneration_mensuelle": rem_label(rem),
           "age_20_ans": age20_label(pdate(naissance), dt.date(2020, 5, 1)), "aide_logement_personnelle": "false"}
    return row, None


def official_cases():
    """Every official test: dict(case_id, encoding_ok, label, row or None, reason)."""
    out = []
    for cid, obl, naissance, rem, expected in PF_TESTS:
        got = call_pf("Metropole", obl, rem, pdate(naissance), False, dt.date(2020, 5, 1))
        exp = "ouvert" if expected else "non_ouvert"
        rec = {"case_id": cid, "encoding_ok": got == exp, "label": exp, "row": None, "reason": None}
        if CFG["kind"] == "PF":
            rec["row"], rec["reason"] = map_pf_test((cid, obl, naissance, rem, expected))
        else:
            rec["reason"] = "asserts droit_ouvert of PrestationsFamiliales (sample FR-PF)"
        out.append(rec)
    for case in AF_TESTS:
        cid, kids, res, date, residence, avant, expected, line = case
        try:
            montant, comp = call_interface(kids, cents(Money(res)), residence, pdate(date), True, False, avant)
            ok, label = montant == cents(Money(expected)), regime_label(comp)
        except Exception as exc:
            ok, label = False, f"error {type(exc).__name__}"
        rec = {"case_id": cid, "encoding_ok": ok, "label": label, "row": None, "reason": None}
        if CFG["kind"] == "AF":
            rec["row"], rec["reason"] = map_af_test(case)
        else:
            rec["reason"] = "asserts the household amount (samples FR-AF-1 to FR-AF-3)"
        out.append(rec)
    return out


def check_ceilings():
    """The earnings cut points equal the encoding's ceilings at the fixed date."""
    ok = True
    for res, ceil in (("Mayotte", CEILING_MAYOTTE), ("Metropole", CEILING_OTHERS), ("Guadeloupe", CEILING_OTHERS)):
        at = call_pf(res, "Apres", ceil, pdate("2002-05-01"), False, FIXED_DATE)
        above = call_pf(res, "Apres", money_str(cents(Money(ceil)) + 1), pdate("2002-05-01"), False, FIXED_DATE)
        ok &= (at, above) == ("ouvert", "non_ouvert")
    return ok


def check_official(verbose=True):
    cases = official_cases()
    enc_pass = sum(c["encoding_ok"] for c in cases)
    mapped = [c for c in cases if c["row"] is not None]
    orc_pass = 0
    for c in mapped:
        got = evaluate(c["row"])
        c["oracle"] = got
        orc_pass += got == c["label"]
    ceil_ok = check_ceilings()
    if verbose:
        print(f"sample {SAMPLE_ID}")
        print(f"earnings ceilings at {FIXED_DATE} match the encoding: {ceil_ok}")
        for c in cases:
            status = "PASS" if c["encoding_ok"] else "FAIL"
            if c["row"] is not None:
                o = "PASS" if c.get("oracle") == c["label"] else f"FAIL (oracle {c.get('oracle')})"
                print(f"{status} encoding  {o} oracle  {c['case_id']}  -> {c['label']}")
            else:
                print(f"{status} encoding  unmapped     {c['case_id']}: {c['reason']}")
        print(f"\nencoding: {enc_pass}/{len(cases)} official test cases pass")
        print(f"oracle:   {orc_pass}/{len(mapped)} mapped official cases agree with the encoding")
    return enc_pass == len(cases) and orc_pass == len(mapped) and ceil_ok, cases


def write_official(cases):
    names = [a["name"] for a in SPEC["attributes"]]
    with open(os.path.join(HERE, "official_examples.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id"] + names + ["output"])
        for c in cases:
            if c["row"] is not None:
                w.writerow([c["case_id"]] + [c["row"][n] for n in names] + [c["label"]])


def enumerate_table(jobs=None):
    ok, cases = check_official(verbose=False)
    if not ok:
        sys.exit("official tests do not all pass; run --check-official")
    rows = list(all_rows(SPEC))
    chunk = 500
    chunks = [rows[i:i + chunk] for i in range(0, len(rows), chunk)]
    if len(rows) > 2000:
        with ProcessPoolExecutor(max_workers=jobs or os.cpu_count()) as ex:
            results = [r for part in ex.map(_eval_chunk, chunks) for r in part]
    else:
        results = _eval_chunk(rows)
    names = [a["name"] for a in SPEC["attributes"]]
    with open(os.path.join(HERE, "ground_truth.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(names + ["output"])
        for row, (label, _) in zip(rows, results):
            w.writerow([row[n] for n in names] + [label])
    counts = {}
    notes = {}
    for label, note in results:
        counts[label] = counts.get(label, 0) + 1
        if note:
            key = note.split(":")[0] if label != "REJECTED" else note
            notes[key] = notes.get(key, 0) + 1
    print(f"{SAMPLE_ID}: {len(rows)} rows")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    for k in sorted(notes):
        print(f"  note: {k}: {notes[k]}")


def _group_chunk(rows):
    bad = 0
    n = 0
    for row in rows:
        base = evaluate(row)
        if base == "EXCLUDED":
            continue
        for m in RESIDENCE_MEMBERS[row["residence"]]:
            if m != RESIDENCE_REP[row["residence"]]:
                n += 1
                bad += evaluate_detail(row, residence_override=m)[0] != base
        if CFG["kind"] == "AF":
            for j in range(1, CFG["children"] + 1):
                key = f"e{j}_prise_en_charge"
                if key in row:
                    for m in PRISE_MEMBERS[row[key]]:
                        if m != PRISE_REP[row[key]]:
                            n += 1
                            bad += evaluate_detail(row, prise_override={j: m})[0] != base
    return n, bad


def check_groups(stride):
    rows = list(all_rows(SPEC))[::stride]
    chunks = [rows[i:i + 200] for i in range(0, len(rows), 200)]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        res = list(ex.map(_group_chunk, chunks))
    n = sum(r[0] for r in res)
    bad = sum(r[1] for r in res)
    print(f"{SAMPLE_ID}: {len(rows)} rows checked (every {stride}th), {n} member substitutions, {bad} disagreements")
    return bad == 0


def main(argv):
    if "--check-official" in argv:
        ok, _ = check_official()
        return 0 if ok else 1
    if "--write-official" in argv:
        ok, cases = check_official(verbose=False)
        if not ok:
            sys.exit("official tests do not all pass")
        write_official(cases)
        return 0
    if "--enumerate" in argv:
        enumerate_table()
        return 0
    if "--check-groups" in argv:
        stride = int(argv[argv.index("--check-groups") + 1]) if len(argv) > argv.index("--check-groups") + 1 else 1
        return 0 if check_groups(stride) else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
