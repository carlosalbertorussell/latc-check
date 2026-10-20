#!/usr/bin/env python3
"""Oracle for FR-APL-4: APL eligibility of residents of a logement-foyer.

Holds the table definition (spec.json is written from it with --write-spec), evaluates
rows through the Catala 1.3.0 Python build in paperC/catala_more/, and maps the
official tests onto rows.

  python oracle.py --check-official | --enumerate | --write-official | --check-bands | --write-spec
"""

import datetime
import os
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(FOLDER, "..", "..", "..", "catala_more")))

import fr_apl_common as F  # noqa: E402
import oracle_common as OC  # noqa: E402

LEG = "aides_logement/code_construction_legislatif.catala_fr"
REG = "aides_logement/code_construction_reglementaire.catala_fr"
DROM = ("Guadeloupe", "Guyane", "Martinique", "LaReunion", "Mayotte")

DATE_BANDS = [
    ("2019-09-01_to_2020-12-31", "2019-09-01", "2021-01-01", "2020-03-10"),
    ("2021-01-01_to_2023-04-04", "2021-01-01", "2023-04-05", "2022-06-01"),
    ("2023-04-05_to_2023-12-31", "2023-04-05", "2024-01-01", "2023-06-01"),
    ("2024-01-01_to_2024-10-31", "2024-01-01", "2024-11-01", "2024-06-01"),
    ("ge_2024-11-01", "2024-11-01", None, "2025-06-01"),
]


def date_band(iso):
    for label, lo, hi, _ in DATE_BANDS:
        if (lo is None or iso >= lo) and (hi is None or iso < hi):
            return label
    return None


TYPE = [
    ("LogementPersonnesAgeesOuHandicapees", "LogementPersonnesAgeesOuHandicapees", "LogementPersonnesÂgéesOuHandicapées"),
    ("ResidenceSociale", "ResidenceSociale", "RésidenceSociale"),
    ("FoyerJeunesTravailleursOuMigrantsConventionneL353_2Avant1995",
     "FoyerJeunesTravailleursOuMigrantsConventionneL353_2Avant1995",
     "FoyerJeunesTravailleursOuMigrantsConventionnéL353_2Avant1995"),
    ("Autre", "Autre", "Autre"),
]
BOOL = [("faux", False, "faux"), ("vrai", True, "vrai")]


def foyer_field(key):
    def apply(raw, value):
        raw["foyer"][key] = value
    return apply


def baseline():
    """Exemple1, with the applicant a foreign national meeting both nationality
    conditions and the household resident of a logement-foyer."""
    return F.baseline(
        nationalite=("Etrangere", True, True),
        mode="ResidentLogementFoyer",
        bailleur=None,
        foyer={"type": None, "conventionne_livre_III": None, "remplit_r832_21": None, "conventionne_drom": None},
    )


ATTRIBUTES = [
    OC.Attribute("residence", "enum", F.RESIDENCE, F.RESIDENCE_SOURCE, F.setter("residence")),
    OC.Attribute(
        "date_courante", "interval", [(lab, rep, f"|{rep}|") for lab, _, _, rep in DATE_BANDS],
        "ÉligibilitéAidePersonnaliséeLogement.date_courante (aides_logement/prologue.catala_fr:378-381). Cut points: "
        + LEG + ":1333-1339 (Saint-Pierre-et-Miquelon from 2021-01-01); " + REG + ":5995-6019 (DROM rule for "
        "FoyerJeunesTravailleurs… from 2023-04-05); smic/Smic.catala_fr:434-443 and 481-489 (Mayotte SMIC "
        "conflict 2024-01-01 to 2024-10-31). The domain starts at 2019-09-01: before that date every input raises "
        "NoValue (see FR-APL-1)",
        F.setter("date_courante")),
    OC.Attribute(
        "type_logement_foyer", "enum", TYPE,
        "LogementFoyer.type_logement, enumeration TypeLogementFoyer (" + REG + ":3732-3736); read by "
        + REG + ":3729-3751 and 5995-6019",
        foyer_field("type")),
    OC.Attribute(
        "conventionne_livre_III_titre_V_chap_III", "bool", BOOL,
        "LogementFoyer.conventionné_livre_III_titre_V_chap_III (aides_logement/prologue.catala_fr:117-135); read by "
        "L831-1 5° (" + LEG + ":735-745)",
        foyer_field("conventionne_livre_III")),
    OC.Attribute(
        "remplit_conditions_r832_21", "bool", BOOL,
        "LogementFoyer.remplit_conditions_r832_21 (aides_logement/prologue.catala_fr:117-135); read by R832-21 "
        "(" + REG + ":3801-3813)",
        foyer_field("remplit_r832_21")),
    OC.Attribute(
        "conventionne_selon_regles_drom", "bool", BOOL,
        "LogementFoyer.conventionné_selon_règles_drom (aides_logement/prologue.catala_fr:117-135); read by "
        "L861-5-1 (" + LEG + ":1463-1489) in Guadeloupe, Guyane, Martinique, La Réunion and Mayotte",
        foyer_field("conventionne_drom")),
]

DROM_TUPLE = "(" + ", ".join(repr(r) for r in DROM) + ")"

META = {
    "id": "FR-APL-4",
    "title": "Aide personnalisée au logement (APL): eligibility of residents of a logement-foyer",
    "source": F.SOURCE,
    "output": F.OUTPUT,
    "exclusions": [
        {
            "id": "fjt_type_without_l353_2_convention",
            "description": "The type FoyerJeunesTravailleursOuMigrantsConventionnéL353_2Avant1995 is by definition a "
                           "foyer that signed an L353-2 convention before 1995; L353-2 is in livre III, titre V, "
                           "chapitre III of the code de la construction, so the foyer cannot be unconventioned under "
                           "that chapter",
            "predicate": "type_logement_foyer == 'FoyerJeunesTravailleursOuMigrantsConventionneL353_2Avant1995' "
                         "and conventionne_livre_III_titre_V_chap_III == 'faux'",
            "source": REG + ":3712-3727 (R832-20 3°: foyers \"ayant fait l'objet d'une convention, prévue à "
                      "l'article L. 353-2, signée avant le 1er janvier 1995\") and 3732-3736 (enumeration)",
        },
        {
            "id": "drom_convention_outside_drom",
            "description": "A convention under the DROM rules of L861-5-1 exists only for foyers in Guadeloupe, "
                           "Guyane, Martinique, La Réunion and Mayotte",
            "predicate": f"conventionne_selon_regles_drom == 'vrai' and residence not in {DROM_TUPLE}",
            "source": LEG + ":1463-1489 (L861-5-1, which defines that convention for these five territories only)",
        },
    ],
    "fixed_inputs": {
        "demandeur.nationalité": {
            "value": "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: vrai, "
                     "satisfait_art_4_ordonnance_2002_mayotte: vrai}",
            "why": "the only nationality value that meets the nationality condition in every territory, including "
                   "Mayotte where Française fails (L861-5 1°, FR-APL-1); no official test maps onto this table, so "
                   "nothing ties it to Exemple1's Française",
        },
        "logement.mode_occupation": {
            "value": "RésidentLogementFoyer {logement_foyer_jeunes_travailleurs: faux, date_conventionnement: "
                     "|2000-01-01|, construit_application_loi_1957_12_III: faux, redevance: 400 €, "
                     "catégorie_équivalence_loyer_d842_16: AutresPersonnes, every other boolean faux; type_logement "
                     "and the three convention booleans from the attributes}",
            "why": "the fields that are not attributes are read only by the amount computation",
        },
        "every other ménage and demandeur field": {
            "value": F.EXEMPLE1_DESCRIPTION,
            "why": "same household as the other FR-APL tables",
        },
    },
    "notes": "Sub-table 4 of 5 of FR-APL (amount computation out of scope). No official test of "
             "tests_eligibilite_apl.catala_fr concerns a logement-foyer, so official_examples.csv has no data row.",
}

SPEC = OC.build_spec(META, ATTRIBUTES)
ORACLE = OC.Oracle(SPEC, ATTRIBUTES, baseline, F.run_apl, (F.CatalaError,))


def evaluate(row: dict[str, str]) -> str:
    return ORACLE.evaluate(row)


CASES = F.official_cases(None, "Exemple1's household is a Locataire; this table fixes mode_occupation to "
                               "RésidentLogementFoyer, so no row describes it")


def date_probes():
    reps = {rep for _, _, _, rep in DATE_BANDS}
    out = {lab: [] for lab, _, _, _ in DATE_BANDS}
    d = datetime.date(2019, 9, 1)
    while d < datetime.date(2028, 1, 1):
        iso = d.isoformat()
        if iso not in reps:
            out[date_band(iso)].append(iso)
        d += datetime.timedelta(days=1)
    return out


PROBES = {"date_courante": date_probes()}

if __name__ == "__main__":
    sys.exit(OC.main(FOLDER, ORACLE, CASES, PROBES))
