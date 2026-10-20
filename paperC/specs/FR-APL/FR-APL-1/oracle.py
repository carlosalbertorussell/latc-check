#!/usr/bin/env python3
"""Oracle for FR-APL-1: APL eligibility by date, territory and applicant nationality.

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

# Date bands: (label, first day, first day after the band, representative).
DATE_BANDS = [
    ("lt_2019-01-01", None, "2019-01-01", "2018-06-01"),
    ("2019-01-01_to_2019-08-31", "2019-01-01", "2019-09-01", "2019-05-01"),
    ("2019-09-01_to_2020-12-31", "2019-09-01", "2021-01-01", "2020-03-10"),
    ("2021-01-01_to_2023-12-31", "2021-01-01", "2024-01-01", "2022-06-01"),
    ("2024-01-01_to_2024-10-31", "2024-01-01", "2024-11-01", "2024-06-01"),
    ("ge_2024-11-01", "2024-11-01", None, "2025-06-01"),
]


def date_band(iso):
    for label, lo, hi, _ in DATE_BANDS:
        if (lo is None or iso >= lo) and (hi is None or iso < hi):
            return label
    raise ValueError(iso)


ATTRIBUTES = [
    OC.Attribute(
        "date_courante", "interval",
        [(lab, rep, f"|{rep}|") for lab, _, _, rep in DATE_BANDS],
        "ÉligibilitéAidePersonnaliséeLogement.date_courante (aides_logement/prologue.catala_fr:378-381). Cut points: "
        "smic/Smic.catala_fr:9-18 (brut_horaire has no definition before 2019-01-01); "
        "aides_logement/archives.catala_fr:11-16 (personnes_à_charge_prises_en_compte defined from 2019-09-01, "
        "counted at aides_logement/prologue.catala_fr:342-343); "
        "aides_logement/code_construction_legislatif.catala_fr:1333-1339 (L860-3: Saint-Pierre-et-Miquelon "
        "excluded from 2021-01-01); smic/Smic.catala_fr:434-443 and 481-489 (two Mayotte SMIC definitions "
        "overlap from 2024-01-01 to 2024-10-31)",
        F.setter("date_courante")),
    OC.Attribute("residence", "enum", F.RESIDENCE, F.RESIDENCE_SOURCE, F.setter("residence")),
    OC.Attribute("nationalite_demandeur", "enum", F.NATIONALITE, F.NATIONALITE_SOURCE, F.setter("nationalite")),
]

META = {
    "id": "FR-APL-1",
    "title": "Aide personnalisée au logement (APL): eligibility by date, territory and applicant nationality",
    "source": F.SOURCE,
    "output": F.OUTPUT,
    "exclusions": [],
    "fixed_inputs": {
        "every ménage and demandeur field that is not an attribute": {
            "value": F.EXEMPLE1_DESCRIPTION,
            "why": "keeps the official test Exemple1 on the table; the other FR-APL tables vary these inputs",
        },
    },
    "notes": "Sub-table 1 of 5 of FR-APL (the APL eligibility decision split by subject; amount computation "
             "is out of scope). REJECTED rows are Catala runtime errors raised by the scope: NoValue before "
             "2019-09-01 in every territory, and a Conflict between two SMIC definitions for Mayotte from "
             "2024-01-01 to 2024-10-31 (CONVERSION.md).",
}

SPEC = OC.build_spec(META, ATTRIBUTES)
ORACLE = OC.Oracle(SPEC, ATTRIBUTES, F.baseline, F.run_apl, (F.CatalaError,))


def evaluate(row: dict[str, str]) -> str:
    return ORACLE.evaluate(row)


# ------------------------------------------------------------- official tests

def exemple1_row():
    """Labels of Exemple1, derived from its raw inputs (fr_apl_common.BASELINE)."""
    raw = F.BASELINE
    return {
        "date_courante": date_band(raw["date_courante"]),
        "residence": F.label_of(F.RESIDENCE, raw["residence"]),
        "nationalite_demandeur": F.label_of(F.NATIONALITE, raw["nationalite"]),
    }


CASES = F.official_cases(exemple1_row())
if not F.inputs_equal_exemple1(ORACLE, exemple1_row()):
    raise SystemExit("the inputs built for Exemple1's row differ from the test's inputs")


# ---------------------------------------------------------------- band probes

def date_probes():
    """Every calendar day from 2017-01-01 to 2027-12-31 except the representatives."""
    reps = {rep for _, _, _, rep in DATE_BANDS}
    out = {lab: [] for lab, _, _, _ in DATE_BANDS}
    d = datetime.date(2017, 1, 1)
    while d < datetime.date(2028, 1, 1):
        iso = d.isoformat()
        if iso not in reps:
            out[date_band(iso)].append(iso)
        d += datetime.timedelta(days=1)
    return out


PROBES = {"date_courante": date_probes()}

if __name__ == "__main__":
    sys.exit(OC.main(FOLDER, ORACLE, CASES, PROBES))
