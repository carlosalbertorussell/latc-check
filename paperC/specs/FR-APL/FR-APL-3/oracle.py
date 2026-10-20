#!/usr/bin/env python3
"""Oracle for FR-APL-3: APL eligibility of tenants and sub-tenants (landlord, family
ownership, letting to third parties, decency, main residence, IFI).

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

LEG = "aides_logement/code_construction_legislatif.catala_fr"

MODE = [
    ("Locataire", "Locataire", "Locataire (Location {...})"),
    ("SousLocataire", "SousLocataire", "SousLocataire (Location {...})"),
]

BAILLEUR = [
    ("BailleurSocial_conventionne", ("BailleurSocial", True),
     "BailleurSocial {conventionné_livre_III_titre_V_chap_III: vrai, réduction_loyer_solidarité_perçue: 0 €}"),
    ("BailleurSocial_non_conventionne", ("BailleurSocial", False),
     "BailleurSocial {conventionné_livre_III_titre_V_chap_III: faux, réduction_loyer_solidarité_perçue: 0 €}"),
    ("BailleurPriveAvecConventionnementSocial_conventionne", ("BailleurPriveAvecConventionnementSocial", True),
     "BailleurPrivéAvecConventionnementSocial {conventionné_livre_III_titre_II_chap_I_sec_3: vrai}"),
    ("BailleurPriveAvecConventionnementSocial_non_conventionne", ("BailleurPriveAvecConventionnementSocial", False),
     "BailleurPrivéAvecConventionnementSocial {conventionné_livre_III_titre_II_chap_I_sec_3: faux}"),
    ("BailleurPrive", ("BailleurPrive",), "BailleurPrivé"),
]


def parts(kind):
    return [
        ("Autre", None, "Autre"),
        ("famille_moins_de_10pc", "0.05", "DemandeurOuConjointOuParentOuViaPartsSociétés contenu 0,05"),
        ("famille_10pc_ou_plus", "0.1", "DemandeurOuConjointOuParentOuViaPartsSociétés contenu 0,1"),
    ]


def part_band(value):
    if value is None:
        return "Autre"
    from fractions import Fraction
    return "famille_moins_de_10pc" if Fraction(value) < Fraction("0.1") else "famille_10pc_ou_plus"


# Letting part of the dwelling to a third party (L822-4). Age is judged at date_courante
# |2020-03-10|: VérificationÂgeSupérieurÀ.est_supérieur is "date_naissance + 30 an >
# date_courante" (prologue_france/France.catala_fr:37-39), i.e. the person is under 30.
LOUE = [
    ("Non", None, "Non"),
    ("Oui_moins_de_30_ans_non_conforme_l442_1", ("2000-01-01", False),
     "Oui {date_naissance_personne_sous_location: |2000-01-01|, conforme_article_l442_1: faux}"),
    ("Oui_moins_de_30_ans_conforme_l442_1", ("2000-01-01", True),
     "Oui {date_naissance_personne_sous_location: |2000-01-01|, conforme_article_l442_1: vrai}"),
    ("Oui_30_ans_ou_plus_non_conforme_l442_1", ("1980-01-01", False),
     "Oui {date_naissance_personne_sous_location: |1980-01-01|, conforme_article_l442_1: faux}"),
    ("Oui_30_ans_ou_plus_conforme_l442_1", ("1980-01-01", True),
     "Oui {date_naissance_personne_sous_location: |1980-01-01|, conforme_article_l442_1: vrai}"),
]

BOOL = [("faux", False, "faux"), ("vrai", True, "vrai")]

ATTRIBUTES = [
    OC.Attribute(
        "mode_occupation", "enum", MODE,
        "Logement.mode_occupation, constructors Locataire and SousLocataire of ModeOccupation "
        "(aides_logement/prologue.catala_fr:143-149); read by L822-2 II (" + LEG + ":146-161), L822-3 (" + LEG +
        ":171-222) and L831-1 2° (" + LEG + ":689-706)",
        F.setter("mode")),
    OC.Attribute(
        "bailleur", "enum", BAILLEUR,
        "Location.bailleur, enumeration TypeBailleur (aides_logement/prologue.catala_fr:16-38); read by "
        "L831-1 2° (" + LEG + ":689-706)",
        F.setter("bailleur")),
    OC.Attribute(
        "part_propriete_famille", "interval", parts("propriété"),
        "Logement.propriétaire, enumeration ParentOuAutre (aides_logement/prologue.catala_fr:151-153); read by "
        "L822-3 (" + LEG + ":171-222) with the 10 % threshold of R822-1 "
        "(aides_logement/code_construction_reglementaire.catala_fr:103-107)",
        F.setter("proprietaire_parts")),
    OC.Attribute(
        "part_usufruit_famille", "interval", parts("usufruit"),
        "Logement.usufruit, enumeration ParentOuAutre (aides_logement/prologue.catala_fr:151-153); same rules",
        F.setter("usufruit_parts")),
    OC.Attribute(
        "loue_ou_sous_loue_a_des_tiers", "enum", LOUE,
        "Logement.loué_ou_sous_loué_à_des_tiers, enumeration LouéOuSousLouéÀDesTiers with PersonneSousLocation "
        "(aides_logement/prologue.catala_fr:155-161); read by L822-4 (" + LEG + ":232-254)",
        F.setter("loue_tiers")),
    OC.Attribute(
        "logement_decent_l89_462", "bool", BOOL,
        "Logement.logement_decent_l89_462 (aides_logement/prologue.catala_fr:169); read by L822-9 (" + LEG + ":382-385)",
        F.setter("decent")),
    OC.Attribute(
        "residence_principale", "bool", BOOL,
        "Logement.résidence_principale (aides_logement/prologue.catala_fr:164); read by L821-2 (" + LEG + ":42-47)",
        F.setter("residence_principale")),
    OC.Attribute(
        "condition_rattache_foyer_fiscal_parent_ifi", "bool", BOOL,
        "Ménage.condition_rattaché_foyer_fiscal_parent_ifi (aides_logement/prologue.catala_fr:223); read by L822-8 "
        "(" + LEG + ":368-371)",
        F.setter("ifi")),
]

META = {
    "id": "FR-APL-3",
    "title": "Aide personnalisée au logement (APL): eligibility of tenants and sub-tenants",
    "source": F.SOURCE,
    "output": F.OUTPUT,
    "exclusions": [],
    "fixed_inputs": {
        "every ménage and demandeur field that is not an attribute": {
            "value": F.EXEMPLE1_DESCRIPTION,
            "why": "keeps the official test Exemple1 on the table; the Location record keeps Exemple1's values "
                   "for every field other than bailleur (loyer 750 €, every boolean faux, PasDeChangement)",
        },
    },
    "notes": "Sub-table 3 of 5 of FR-APL (amount computation out of scope). In the encoding a SousLocataire can "
             "never be eligible for the APL: condition_logement_bailleur has rules for Locataire, "
             "RésidentLogementFoyer, AccessionPropriétéLocalUsageExclusifHabitation and LocationAccession only "
             "(CONVERSION.md).",
}

SPEC = OC.build_spec(META, ATTRIBUTES)
ORACLE = OC.Oracle(SPEC, ATTRIBUTES, F.baseline, F.run_apl, (F.CatalaError,))


def evaluate(row: dict[str, str]) -> str:
    return ORACLE.evaluate(row)


# ------------------------------------------------------------- official tests

def exemple1_row():
    raw = F.BASELINE
    return {
        "mode_occupation": F.label_of(MODE, raw["mode"]),
        "bailleur": F.label_of(BAILLEUR, raw["bailleur"]),
        "part_propriete_famille": part_band(raw["proprietaire_parts"]),
        "part_usufruit_famille": part_band(raw["usufruit_parts"]),
        "loue_ou_sous_loue_a_des_tiers": F.label_of(LOUE, raw["loue_tiers"]),
        "logement_decent_l89_462": "vrai" if raw["decent"] else "faux",
        "residence_principale": "vrai" if raw["residence_principale"] else "faux",
        "condition_rattache_foyer_fiscal_parent_ifi": "vrai" if raw["ifi"] else "faux",
    }


CASES = F.official_cases(exemple1_row())
if not F.inputs_equal_exemple1(ORACLE, exemple1_row()):
    raise SystemExit("the inputs built for Exemple1's row differ from the test's inputs")

# ---------------------------------------------------------------- band probes

PART_PROBES = {
    "famille_moins_de_10pc": ["0", "0.01", "0.0999"],
    "famille_10pc_ou_plus": ["0.1001", "0.15", "0.19", "0.5", "1"],
}
PROBES = {
    "part_propriete_famille": PART_PROBES,
    "part_usufruit_famille": PART_PROBES,
    "loue_ou_sous_loue_a_des_tiers": {
        # 30th birthday of a person born 1990-03-10 is the decision date 2020-03-10.
        "Oui_moins_de_30_ans_non_conforme_l442_1": [(b, False) for b in ("1990-03-11", "1995-06-30", "2019-01-01")],
        "Oui_moins_de_30_ans_conforme_l442_1": [(b, True) for b in ("1990-03-11", "1995-06-30", "2019-01-01")],
        "Oui_30_ans_ou_plus_non_conforme_l442_1": [(b, False) for b in ("1990-03-10", "1990-03-09", "1940-01-01")],
        "Oui_30_ans_ou_plus_conforme_l442_1": [(b, True) for b in ("1990-03-10", "1990-03-09", "1940-01-01")],
    },
}

if __name__ == "__main__":
    sys.exit(OC.main(FOLDER, ORACLE, CASES, PROBES))
