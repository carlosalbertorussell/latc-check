#!/usr/bin/env python3
"""Oracle for FR-APL-2: APL eligibility by household size and floor area (peuplement).

Holds the table definition (spec.json is written from it with --write-spec), evaluates
rows through the Catala 1.3.0 Python build in paperC/catala_more/, and maps the
official tests onto rows.

  python oracle.py --check-official | --enumerate | --write-official | --check-bands | --write-spec
"""

import os
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(FOLDER, "..", "..", "..", "catala_more")))

import fr_apl_common as F  # noqa: E402
import oracle_common as OC  # noqa: E402

SITUATION = [
    ("Celibataire", "Celibataire", "Célibataire"),
    ("Maries", "Maries", "Mariés |2010-11-26|"),
    ("Pacses", "Pacses", "Pacsés"),
    ("Concubins", "Concubins", "Concubins"),
    ("CelibataireSepareDeFait", "CelibataireSepareDeFait", "CélibataireSéparéDeFait"),
    ("ConcubinageDontSepareDeFait", "ConcubinageDontSepareDeFait", "ConcubinageDontSéparéDeFait"),
]

PERSONNES_A_CHARGE = [(str(k), k, f"the first {k} EnfantÀCharge of Exemple1" if k else "[]") for k in range(4)]
AUTRES_OCCUPANTS = [(str(k), k, str(k)) for k in range(2)]

# Every minimum floor area the code can compare against for 1 or 2 adults, 0..1 other
# occupant and 0..3 dependants: R822-25 (9 + 9 n or 16 + 9 n), its Mayotte version
# (9 + 9 n or 13 + 9 n) and R844-4 (9 or 16). Bands are [cut_i, cut_{i+1}).
CUTS = [9, 13, 16, 18, 22, 25, 27, 31, 34, 36, 40, 43, 45, 49, 52]


def surface_bands():
    bands = [("lt_9", None, 9, 8)]
    for lo, hi in zip(CUTS, CUTS[1:] + [None]):
        label = f"ge_{lo}" if hi is None else f"{lo}_to_{hi - 1}"
        bands.append((label, lo, hi, lo))
    return bands


SURFACE_BANDS = surface_bands()


def surface_band(m2):
    for label, lo, hi, _ in SURFACE_BANDS:
        if (lo is None or m2 >= lo) and (hi is None or m2 < hi):
            return label
    raise ValueError(m2)


ATTRIBUTES = [
    OC.Attribute("residence", "enum", F.RESIDENCE, F.RESIDENCE_SOURCE, F.setter("residence")),
    OC.Attribute("nationalite_demandeur", "enum", F.NATIONALITE, F.NATIONALITE_SOURCE, F.setter("nationalite")),
    OC.Attribute(
        "situation_familiale", "enum", SITUATION,
        "Ménage.situation_familiale, enumeration SituationFamiliale "
        "(aides_logement/code_construction_legislatif.catala_fr:107-117); read by R822-25 "
        "(aides_logement/code_construction_reglementaire.catala_fr:1015-1058) and R861-5 3° (5614-5645)",
        F.setter("situation_familiale")),
    OC.Attribute(
        "personnes_a_charge", "enum", PERSONNES_A_CHARGE,
        "Ménage.personnes_à_charge (aides_logement/prologue.catala_fr:217-226), counted by "
        "`nombre de ménage.personnes_à_charge` in R822-25 (aides_logement/code_construction_reglementaire.catala_fr:"
        "1016-1028, 1042-1045) and R861-5 3° (5629-5632)",
        F.setter("n_enfants")),
    OC.Attribute(
        "autres_occupants", "enum", AUTRES_OCCUPANTS,
        "Ménage.nombre_autres_occupants_logement (aides_logement/prologue.catala_fr:217-226), same rules",
        F.setter("autres_occupants")),
    OC.Attribute(
        "surface_m_carres", "interval",
        [(lab, rep, str(rep)) for lab, _, _, rep in SURFACE_BANDS],
        "Logement.surface_m_carrés (aides_logement/prologue.catala_fr:163-171), compared by R822-25 "
        "(aides_logement/code_construction_reglementaire.catala_fr:1029-1058), R844-4 (5531-5545) and "
        "R861-5 3° for Mayotte (5614-5645)",
        F.setter("surface")),
    OC.Attribute(
        "personnes_agees_handicapees_r844_4", "bool",
        [("faux", False, "faux"), ("vrai", True, "vrai")],
        "Ménage.personnes_âgées_handicapées_foyer_r844_4 (aides_logement/prologue.catala_fr:225), read by R844-4 "
        "(aides_logement/code_construction_reglementaire.catala_fr:5531-5545)",
        F.setter("r844_4")),
]

META = {
    "id": "FR-APL-2",
    "title": "Aide personnalisée au logement (APL): eligibility by household size and floor area",
    "source": F.SOURCE,
    "output": F.OUTPUT,
    "exclusions": [],
    "fixed_inputs": {
        "every ménage and demandeur field that is not an attribute": {
            "value": F.EXEMPLE1_DESCRIPTION,
            "why": "keeps the official test Exemple1 on the table (date_courante |2020-03-10|); dependants are the "
                   "first k children of Exemple1 so that k = 3 reproduces the test exactly",
        },
    },
    "notes": "Sub-table 2 of 5 of FR-APL (amount computation out of scope). The floor-area bands are cut at every "
             "minimum area the code can compare against for the household sizes in the table (2 to 6 persons with "
             "a couple, 1 to 5 with a single adult); the caps of R822-25 (70 m² from 8 persons) and of the Mayotte "
             "rule (54 m² from 9 persons) are out of reach with these sizes. REJECTED rows: in Mayotte the Mayotte "
             "surface rule and R844-4 are both exceptions to the same base rule and conflict (CONVERSION.md).",
}

SPEC = OC.build_spec(META, ATTRIBUTES)
ORACLE = OC.Oracle(SPEC, ATTRIBUTES, F.baseline, F.run_apl, (F.CatalaError,))


def evaluate(row: dict[str, str]) -> str:
    return ORACLE.evaluate(row)


# ------------------------------------------------------------- official tests

def exemple1_row():
    raw = F.BASELINE
    return {
        "residence": F.label_of(F.RESIDENCE, raw["residence"]),
        "nationalite_demandeur": F.label_of(F.NATIONALITE, raw["nationalite"]),
        "situation_familiale": F.label_of(SITUATION, raw["situation_familiale"]),
        "personnes_a_charge": F.label_of(PERSONNES_A_CHARGE, raw["n_enfants"]),
        "autres_occupants": F.label_of(AUTRES_OCCUPANTS, raw["autres_occupants"]),
        "surface_m_carres": surface_band(raw["surface"]),
        "personnes_agees_handicapees_r844_4": "vrai" if raw["r844_4"] else "faux",
    }


def exemple1_inputs_equal():
    """Exemple1's surface (80 m²) is not the band representative (52 m²); compare the
    inputs with the surface override so that every other field is checked exactly."""
    import run_official_tests_apl as R
    built = F.build_inputs(ORACLE.raw_of(exemple1_row(), {"surface_m_carres": F.BASELINE["surface"]}))
    test = R.exemple1_inputs()
    return built[0] == test[0] and bool(built[1] == test[1]) and bool(built[2] == test[2])


CASES = F.official_cases(exemple1_row())
if not exemple1_inputs_equal():
    raise SystemExit("the inputs built for Exemple1's row differ from the test's inputs")

# ---------------------------------------------------------------- band probes

PROBES = {"surface_m_carres": {lab: [m2 for m2 in range(0, 121) if surface_band(m2) == lab and m2 != rep]
                               for lab, _, _, rep in SURFACE_BANDS}}

if __name__ == "__main__":
    sys.exit(OC.main(FOLDER, ORACLE, CASES, PROBES))
