#!/usr/bin/env python3
"""Oracle for FR-APL-5: APL eligibility of home buyers (accession à la propriété and
location-accession): loan type, loan holder, signature date, age of the dwelling, zone.

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

MODE = [
    ("AccessionProprieteLocalUsageExclusifHabitation", "AccessionProprieteLocalUsageExclusifHabitation",
     "AccessionPropriétéLocalUsageExclusifHabitation (Propriétaire {...})"),
    ("LocationAccession", "LocationAccession", "LocationAccession (Propriétaire {...})"),
]
TYPE_PRET = [(c, c, c) for c in ("D331_32", "D331_63_64", "D331_59_8", "D331_76_1", "Autre")]
TITULAIRE = [
    ("Demandeur", "Demandeur", "Demandeur"),
    ("VendeurQuandDemandeurAContratLocationAccession", "VendeurQuandDemandeurAContratLocationAccession",
     "VendeurQuandDemandeurAContratLocationAccession"),
]
SIGNATURE_BANDS = [
    ("lt_2017-12-31", None, "2017-12-31", "2015-06-01"),
    ("eq_2017-12-31", "2017-12-31", "2018-01-01", "2017-12-31"),
    ("2018-01-01_to_2019-12-31", "2018-01-01", "2020-01-01", "2018-06-01"),
    ("ge_2020-01-01", "2020-01-01", None, "2020-01-15"),
]
ANCIENNETE = [
    ("Neuf", "Neuf", "Neuf"),
    ("Ancien_ameliore_par_occupant", "AncienOui", "Ancien contenu Oui"),
    ("Ancien_non_ameliore_par_occupant", "AncienNon", "Ancien contenu Non"),
]
ZONE = [(z, z, z) for z in ("Zone1", "Zone2", "Zone3")]
DATE_BANDS = [
    ("2019-09-01_to_2019-09-30", "2019-09-01", "2019-10-01", "2019-09-15"),
    ("ge_2019-10-01", "2019-10-01", None, "2020-03-10"),
]
BOOL = [("faux", False, "faux"), ("vrai", True, "vrai")]


def band(bands, iso):
    for label, lo, hi, _ in bands:
        if (lo is None or iso >= lo) and (hi is None or iso < hi):
            return label
    return None


def pret_field(key):
    def apply(raw, value):
        raw["pret"][key] = value
    return apply


def baseline():
    """Exemple1, with the household buying its home (mode from the attributes)."""
    return F.baseline(
        bailleur=None,
        pret={"type_pret": None, "titulaire": None, "date_signature": None, "anciennete": None},
    )


ATTRIBUTES = [
    OC.Attribute(
        "mode_occupation", "enum", MODE,
        "Logement.mode_occupation, constructors AccessionPropriétéLocalUsageExclusifHabitation and LocationAccession "
        "of ModeOccupation (aides_logement/prologue.catala_fr:143-149); read by L822-2 II (" + LEG + ":147-160), "
        "L831-1 1° and 6° (" + LEG + ":658-676, 754-763) and L831-2 (" + LEG + ":771-815)",
        F.setter("mode")),
    OC.Attribute(
        "type_pret", "enum", TYPE_PRET,
        "Prêt.type_prêt, enumeration TypePrêt (aides_logement/prologue.catala_fr:44-60); read by R832-5 and R832-7 "
        "(" + REG + ":3064-3074, 3102-3112)",
        pret_field("type_pret")),
    OC.Attribute(
        "titulaire_pret", "enum", TITULAIRE,
        "Prêt.titulaire_prêt, enumeration TitulairePrêt (aides_logement/prologue.catala_fr:51-53); same rules",
        pret_field("titulaire")),
    OC.Attribute(
        "date_signature_pret", "interval", [(lab, rep, f"|{rep}|") for lab, _, _, rep in SIGNATURE_BANDS],
        "Prêt.date_signature (aides_logement/prologue.catala_fr:55-60); compared with |2017-12-31| (>=), "
        "|2018-01-01| (>=) and |2020-01-01| (<) by L831-2 (" + LEG + ":771-815)",
        pret_field("date_signature")),
    OC.Attribute(
        "anciennete_logement", "enum", ANCIENNETE,
        "Propriétaire.ancienneté_logement, enumeration NeufOuAncien carrying AmélioréParOccupant "
        "(aides_logement/prologue.catala_fr:87-95); read by L831-2 (" + LEG + ":795-815)",
        pret_field("anciennete")),
    OC.Attribute(
        "zone", "enum", ZONE,
        "Logement.zone, enumeration ZoneDHabitation (aides_logement/prologue.catala_fr:258-261); read by "
        "logement_situé_commune_déséquilibre_l831_2 (aides_logement/arrete_2019-09-27.catala_fr:6070-6076)",
        F.setter("zone")),
    OC.Attribute(
        "date_courante", "interval", [(lab, rep, f"|{rep}|") for lab, _, _, rep in DATE_BANDS],
        "ÉligibilitéAidePersonnaliséeLogement.date_courante (aides_logement/prologue.catala_fr:378-381); compared "
        "with |2019-10-01| by aides_logement/arrete_2019-09-27.catala_fr:6070-6076. The domain starts at "
        "2019-09-01: before that date every input raises NoValue (see FR-APL-1)",
        F.setter("date_courante")),
    OC.Attribute(
        "residence_principale", "bool", BOOL,
        "Logement.résidence_principale (aides_logement/prologue.catala_fr:164); read by L821-2 (" + LEG + ":42-46) "
        "and by L822-2 II for AccessionPropriétéLocalUsageExclusifHabitation (" + LEG + ":147-160)",
        F.setter("residence_principale")),
]

META = {
    "id": "FR-APL-5",
    "title": "Aide personnalisée au logement (APL): eligibility of home buyers (accession and location-accession)",
    "source": F.SOURCE,
    "output": F.OUTPUT,
    "exclusions": [
        {
            "id": "loan_signed_after_decision_date",
            "description": "Every loan signature date of the label lies after every decision date of the label: "
                           "the loan that finances the dwelling cannot have been signed after the date at which "
                           "eligibility is assessed",
            "predicate": "date_signature_pret == 'ge_2020-01-01' and date_courante == '2019-09-01_to_2019-09-30'",
            "source": LEG + ":648-657 (L831-1 1°: dwellings \"construits, acquis ou améliorés au moyen ... de prêts\", "
                      "i.e. financed by an existing loan)",
        },
    ],
    "fixed_inputs": {
        "logement.mode_occupation content (Propriétaire)": {
            "value": "mensualité_principale 500 €, charges_mensuelles_prêt 0 €, date_entrée_logement |2010-01-01|, "
                     "type_travaux_logement_d832_15 PasDeTravaux, type_travaux_logement_r842_5 PasDeTravaux, every "
                     "boolean faux, prêt.accord_financement_représentant_État_outre_mer PasdAccord; type_prêt, "
                     "titulaire_prêt, date_signature and ancienneté_logement from the attributes",
            "why": "the fields that are not attributes are read only by the amount computation (or by the AL scope)",
        },
        "every other ménage and demandeur field": {
            "value": F.EXEMPLE1_DESCRIPTION + " (résidence Métropole, demandeur Française)",
            "why": "same household as the other FR-APL tables",
        },
    },
    "notes": "Sub-table 5 of 5 of FR-APL (amount computation out of scope). In the encoding a LocationAccession can "
             "never be eligible: caractéristiques_prêt_l831_1_6 is declared (aides_logement/prologue.catala_fr:387) "
             "and used (" + LEG + ":754-763) but never defined, so it is always false; the R832-7 case of a "
             "location-accession whose seller holds the loan is encoded under caractéristiques_prêt_l831_1_1 and "
             "reached only with mode AccessionPropriété (CONVERSION.md). No official test of "
             "tests_eligibilite_apl.catala_fr concerns home buyers, so official_examples.csv has no data row.",
}

SPEC = OC.build_spec(META, ATTRIBUTES)
ORACLE = OC.Oracle(SPEC, ATTRIBUTES, baseline, F.run_apl, (F.CatalaError,))


def evaluate(row: dict[str, str]) -> str:
    return ORACLE.evaluate(row)


CASES = F.official_cases(None, "Exemple1's household is a Locataire; this table fixes mode_occupation to an "
                               "accession or location-accession, so no row describes it")


def date_probes():
    reps = {rep for _, _, _, rep in DATE_BANDS}
    out = {lab: [] for lab, _, _, _ in DATE_BANDS}
    d = datetime.date(2019, 9, 1)
    while d < datetime.date(2028, 1, 1):
        iso = d.isoformat()
        if iso not in reps and (d.day in (1, 15, 28) or d < datetime.date(2019, 10, 3)):
            out[band(DATE_BANDS, iso)].append(iso)
        d += datetime.timedelta(days=1)
    return out


PROBES = {
    "date_courante": date_probes(),
    "date_signature_pret": {
        "lt_2017-12-31": ["1990-01-01", "2010-06-30", "2017-01-01", "2017-12-30"],
        "2018-01-01_to_2019-12-31": ["2018-01-01", "2018-12-31", "2019-09-01", "2019-12-31"],
        "ge_2020-01-01": ["2020-01-01", "2020-03-10", "2021-06-01", "2025-01-01"],
    },
}

if __name__ == "__main__":
    sys.exit(OC.main(FOLDER, ORACLE, CASES, PROBES))
