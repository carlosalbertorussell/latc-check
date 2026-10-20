"""Shared input model of the FR-APL tables (paperC/specs/FR-APL/FR-APL-*/oracle.py).

Every FR-APL table starts from the household of the official test Exemple1
(aides_logement/tests/tests_eligibilite_apl.catala_fr lines 13-107) and changes only
the inputs its attributes describe. A household is described by a flat dict of raw
values (`BASELINE` below); `run_apl(raw)` turns it into the Catala structures and calls
the scope ÉligibilitéAidePersonnaliséeLogement of the generated Python.
"""

import copy

import apl_inputs as I
from apl_inputs import AL, CatalaError

# Raw description of Exemple1. Keys are documented in build_inputs().
BASELINE = {
    "date_courante": "2020-03-10",
    "residence": "Metropole",
    "nationalite": ("Francaise",),
    "demandeur_naissance": "1970-05-02",
    "situation_familiale": "Maries",
    "date_mariage": "2010-11-26",
    "n_enfants": 3,
    "autres_occupants": 1,
    "prestations": ("AllocationSoutienEnfantHandicape", "ComplementFamilial", "AllocationsFamiliales"),
    "ifi": False,
    "enfant_a_naitre": False,
    "r844_4": False,
    "zone": "Zone1",
    "residence_principale": True,
    "decent": True,
    "surface": 80,
    "proprietaire_parts": None,
    "usufruit_parts": None,
    "loue_tiers": None,
    "mode": "Locataire",
    "bailleur": ("BailleurSocial", True),
    "loyer": "750",
    "foyer": None,
    "pret": None,
}

# The three children of Exemple1, in the order of the test (lines 29-63).
EXEMPLE1_ENFANTS = [
    dict(identifiant=0, date_de_naissance="2001-01-01", obligation_scolaire="Apres", etudes=True),
    dict(identifiant=1, date_de_naissance="2009-01-01", obligation_scolaire="Pendant", etudes=False),
    dict(identifiant=2, date_de_naissance="2012-01-01", obligation_scolaire="Pendant", etudes=False),
]


def baseline(**changes):
    raw = copy.deepcopy(BASELINE)
    for k, v in changes.items():
        if k not in raw:
            raise KeyError(k)
        raw[k] = v
    return raw


def nationalite(spec):
    """("Francaise",) or ("Etrangere", satisfait_l512_2, satisfait_art_4_mayotte)."""
    if spec[0] == "Francaise":
        return I.nationalite("Francaise")
    return I.nationalite("Etrangere", spec[1], spec[2])


def bailleur(spec):
    """("BailleurSocial", conventionné), ("BailleurPriveAvecConventionnementSocial", conventionné)
    or ("BailleurPrive",)."""
    if spec[0] == "BailleurSocial":
        return I.bailleur_social(spec[1])
    if spec[0] == "BailleurPriveAvecConventionnementSocial":
        return I.bailleur_prive_conventionnement(spec[1])
    return I.bailleur_prive()


def build_inputs(raw):
    """Return (date_courante, ménage, demandeur) for the generated scope.

    raw["mode"] is the ModeOccupation constructor. "Locataire" and "SousLocataire" read
    raw["bailleur"] and raw["loyer"]; "RésidentLogementFoyer" reads raw["foyer"]
    (keys type, conventionne_livre_III, remplit_r832_21, conventionne_drom);
    "AccessionProprieteLocalUsageExclusifHabitation" and "LocationAccession" read
    raw["pret"] (keys type_pret, titulaire, date_signature, anciennete)."""
    mode = raw["mode"]
    if mode in ("Locataire", "SousLocataire"):
        content = I.location(bailleur(raw["bailleur"]), loyer=raw["loyer"])
    elif mode == "ResidentLogementFoyer":
        f = raw["foyer"]
        content = I.logement_foyer(f["type"], f["conventionne_livre_III"], f["remplit_r832_21"], f["conventionne_drom"])
    elif mode in ("AccessionProprieteLocalUsageExclusifHabitation", "LocationAccession"):
        p = raw["pret"]
        content = I.proprietaire(p["type_pret"], p["titulaire"], p["date_signature"], p["anciennete"])
    else:
        raise ValueError(mode)
    loue = None if raw["loue_tiers"] is None else I.loue_tiers(*raw["loue_tiers"])
    logement = I.logement(
        I.enum(AL.ModeOccupation, mode, content),
        surface=raw["surface"], zone=raw["zone"], residence_principale=raw["residence_principale"],
        proprietaire_parts=raw["proprietaire_parts"], usufruit_parts=raw["usufruit_parts"],
        loue=loue, decent=raw["decent"])
    enfants = [I.enfant(**e) for e in EXEMPLE1_ENFANTS[:raw["n_enfants"]]]
    menage = I.menage(
        residence=raw["residence"], logement_=logement, personnes_a_charge=enfants,
        situation=I.situation_familiale(raw["situation_familiale"], raw["date_mariage"]),
        prestations=raw["prestations"], autres_occupants=raw["autres_occupants"],
        ifi=raw["ifi"], enfant_a_naitre=raw["enfant_a_naitre"], r844_4=raw["r844_4"])
    demandeur = I.demandeur(raw["demandeur_naissance"], nationalite(raw["nationalite"]))
    return raw["date_courante"], menage, demandeur


def run_apl(raw):
    """Output label of ÉligibilitéAidePersonnaliséeLogement.éligibilité for `raw`:
    "eligible" or "not_eligible". Catala runtime errors propagate (CatalaError)."""
    dc, m, d = build_inputs(raw)
    out = I.eligibilite_apl(dc, m, d)
    return "eligible" if bool(out.eligibilite) else "not_eligible"


# ------------------------------------------------- label lists shared by the tables

# (label, raw value, literal written to spec.json as the representative)
NATIONALITE = [
    ("francaise", ("Francaise",), "Française"),
    ("etrangere_l512_2_et_art_4", ("Etrangere", True, True),
     "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: vrai, satisfait_art_4_ordonnance_2002_mayotte: vrai}"),
    ("etrangere_l512_2_seulement", ("Etrangere", True, False),
     "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: vrai, satisfait_art_4_ordonnance_2002_mayotte: faux}"),
    ("etrangere_art_4_seulement", ("Etrangere", False, True),
     "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: faux, satisfait_art_4_ordonnance_2002_mayotte: vrai}"),
    ("etrangere_aucune", ("Etrangere", False, False),
     "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: faux, satisfait_art_4_ordonnance_2002_mayotte: faux}"),
]
NATIONALITE_SOURCE = (
    "Demandeur.nationalité (aides_logement/prologue.catala_fr:228-247); read by L822-2 I "
    "(aides_logement/code_construction_legislatif.catala_fr:130-136) and its Mayotte version L861-5 1° "
    "(aides_logement/code_construction_legislatif.catala_fr:1389-1400)")

RESIDENCE = [
    ("Metropole", "Metropole", "Métropole"),
    ("Guadeloupe", "Guadeloupe", "Guadeloupe"),
    ("Guyane", "Guyane", "Guyane"),
    ("Martinique", "Martinique", "Martinique"),
    ("LaReunion", "LaReunion", "LaRéunion"),
    ("SaintBarthelemy", "SaintBarthelemy", "SaintBarthélemy"),
    ("SaintMartin", "SaintMartin", "SaintMartin"),
    ("SaintPierreEtMiquelon", "SaintPierreEtMiquelon", "SaintPierreEtMiquelon"),
    ("Mayotte", "Mayotte", "Mayotte"),
]
RESIDENCE_SOURCE = "Ménage.résidence, enumeration France.Collectivité (prologue_france/France.catala_fr:9-18)"

SOURCE = {
    "repository": "https://github.com/CatalaLang/catala-examples",
    "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
    "entry_point": "Aides_logement scope ÉligibilitéAidePersonnaliséeLogement, output éligibilité "
                   "(Python: generated.Aides_logement.eligibilite_aide_personnalisee_logement, Catala 1.3.0)",
    "files": [
        "aides_logement/prologue.catala_fr",
        "aides_logement/code_construction_legislatif.catala_fr",
        "aides_logement/code_construction_reglementaire.catala_fr",
        "aides_logement/archives.catala_fr",
        "aides_logement/arrete_2019-09-27.catala_fr",
        "aides_logement/autres_sources.catala_fr",
        "aides_logement/code_sécurité_sociale.catala_fr",
        "prologue_france/France.catala_fr",
        "prestations_familiales/prologue.catala_fr",
        "smic/Smic.catala_fr",
        "aides_logement/tests/tests_eligibilite_apl.catala_fr",
    ],
}

OUTPUT = {
    "name": "eligibilite_apl",
    "values": ["eligible", "not_eligible"],
    "source": "ÉligibilitéAidePersonnaliséeLogement.éligibilité (condition), aides_logement/prologue.catala_fr:391; "
              "rules aides_logement/code_construction_legislatif.catala_fr:631-645 and 1333-1339",
}

EXEMPLE1_DESCRIPTION = (
    "as in the official test Exemple1 (aides_logement/tests/tests_eligibilite_apl.catala_fr:16-107): "
    "date_courante |2020-03-10|, résidence Métropole, Mariés |2010-11-26|, three EnfantÀCharge (born 2001-01-01 "
    "Après with études, 2009-01-01 Pendant, 2012-01-01 Pendant; French, 0 € pay, no shared custody, "
    "a_déjà_ouvert_droit_aux_allocations_familiales vrai), prestations [AllocationSoutienEnfantHandicapé; "
    "ComplémentFamilial; AllocationsFamiliales], 1 other occupant, Locataire of a BailleurSocial conventionné "
    "(loyer 750 €, RLS 0 €, every other Location boolean faux, PasDeChangement), Zone1, résidence principale, "
    "décent, 80 m², propriétaire Autre, usufruit Autre, not let to third parties, no IFI, no unborn child, "
    "not R844-4; demandeur born 1970-05-02, Française, with every other boolean faux")


def setter(key):
    def apply(raw, value):
        raw[key] = value
    return apply


def direct(fn):
    """Wrap a run_official_tests_apl test function as a `direct` callable for oracle_common."""
    def run():
        results = fn()
        return all(ok for _, ok in results), "; ".join(label for label, _ in results)
    return run


def label_of(labels, raw_value):
    return next(lab for lab, r, _ in labels if r == raw_value)


def inputs_equal_exemple1(oracle, row):
    """True when the Catala inputs built for `row` equal those of Exemple1 exactly."""
    import run_official_tests_apl as R
    built = build_inputs(oracle.raw_of(row))
    test = R.exemple1_inputs()
    return built[0] == test[0] and bool(built[1] == test[1]) and bool(built[2] == test[2])


def official_cases(exemple1_row, exemple1_reason=None):
    """The three test scopes of tests_eligibilite_apl.catala_fr. `exemple1_row` is the
    mapped row, or None with `exemple1_reason`."""
    import run_official_tests_apl as R
    al = ("tests scope ÉligibilitéAllocationLogement (allocation de logement), whose output is a "
          "TypeÉligibilitéAllocationLogement; the FR-APL tables are the APL scope ÉligibilitéAidePersonnaliséeLogement")
    return [
        {"case_id": "tests_eligibilite_apl/Exemple1", "direct": direct(R.exemple1),
         "row": exemple1_row, "expected": "eligible" if exemple1_row else None, "reason": exemple1_reason},
        {"case_id": "tests_eligibilite_apl/Exemple2", "direct": direct(R.exemple2),
         "row": None, "expected": None, "reason": al},
        {"case_id": "tests_eligibilite_apl/Exemple3", "direct": direct(R.exemple3),
         "row": None, "expected": None, "reason": al},
    ]


__all__ = ["BASELINE", "EXEMPLE1_ENFANTS", "baseline", "build_inputs", "run_apl", "CatalaError"]
