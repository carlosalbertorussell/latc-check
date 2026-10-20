# ---------------------------------------------------------------------------
# FR-APL-5: surface and occupancy (R822-25, R844-4, Mayotte R861-?).
# ---------------------------------------------------------------------------
RESIDENCES_5 = ["Metropole", "LaReunion", "Mayotte"]
SITUATIONS = ["Celibataire", "Maries", "Pacses", "Concubins", "CelibataireSepareDeFait",
              "ConcubinageDontSepareDeFait"]
AUTRES = ["0", "1", "2", "3"]
ENFANTS = ["0", "1", "2", "3", "4"]
# Every surface threshold the code compares surface_m_carrés against for the
# declared households (see CONVERSION_2.md); intervals [t_i, t_{i+1}).
THRESHOLDS = [9, 13, 16, 18, 22, 25, 27, 31, 34, 36, 40, 43, 45, 49, 52, 54, 58, 61, 63, 67, 70, 72]


def _surface_intervals():
    out = [("below_9", 8)]
    for i, t in enumerate(THRESHOLDS):
        if i + 1 < len(THRESHOLDS):
            out.append(("%d_to_%d" % (t, THRESHOLDS[i + 1] - 1), t))
        else:
            out.append(("from_%d" % t, t))
    return out


SURFACES = _surface_intervals()
YN = ["oui", "non"]
DATE_5 = "2020-03-10"
SRC = "aides_logement/"
SPEC = {
    "id": "FR-APL-5",
    "title": "APL eligibility (ÉligibilitéAidePersonnaliséeLogement.éligibilité), housing surface against household size",
    "source": {"repository": "https://github.com/CatalaLang/catala-examples",
               "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
               "entry_point": "Aides_logement.ÉligibilitéAidePersonnaliséeLogement (output éligibilité), sub-scope ÉligibilitéAidesPersonnelleLogement",
               "files": [SRC + "prologue.catala_fr", SRC + "code_construction_legislatif.catala_fr",
                         SRC + "code_construction_reglementaire.catala_fr", SRC + "tests/tests_eligibilite_apl.catala_fr"]},
    "attributes": [
        {"name": "residence", "kind": "enum", "values": RESIDENCES_5,
         "representative": {c: "France.Collectivité." + c for c in RESIDENCES_5},
         "source": "code_construction_reglementaire.catala_fr:5613-5645 (Mayotte surface rule); other collectivities use R822-25"},
        {"name": "nationalite_demandeur", "kind": "enum", "values": ["Francaise", "Etrangere_T_T"],
         "representative": {"Francaise": "Française",
                            "Etrangere_T_T": "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: vrai, satisfait_art_4_ordonnance_2002_mayotte: vrai}"},
         "source": "code_construction_legislatif.catala_fr:129-136, 1389-1402 (a French applicant is never eligible in Mayotte, so the Mayotte surface rule is only visible with Etrangere_T_T)"},
        {"name": "situation_familiale", "kind": "enum", "values": SITUATIONS,
         "representative": {s: ("SituationFamiliale.Mariés contenu 2010-11-26" if s == "Maries" else "SituationFamiliale." + s) for s in SITUATIONS},
         "source": "code_construction_reglementaire.catala_fr:1015-1027 (1 or 2 persons; 9 or 16 m²; 13 m² in Mayotte)"},
        {"name": "nombre_autres_occupants_logement", "kind": "interval", "values": AUTRES,
         "representative": {a: a for a in AUTRES},
         "source": "code_construction_reglementaire.catala_fr:1015-1056 (+1 person, +9 m² each)"},
        {"name": "nombre_personnes_a_charge", "kind": "interval", "values": ENFANTS,
         "representative": {e: "%s children (the children of Exemple1 in order, then children born 2012-01-01)" % e for e in ENFANTS},
         "source": "code_construction_reglementaire.catala_fr:1015-1056 (nombre de ménage.personnes_à_charge, +9 m² each)"},
        {"name": "surface_m_carres", "kind": "interval", "values": [l for l, _ in SURFACES],
         "representative": {l: str(r) for l, r in SURFACES},
         "source": "code_construction_reglementaire.catala_fr:1030-1057 (R822-25), 5530-5545 (R844-4), 5613-5645 (Mayotte)"},
        {"name": "personnes_agees_handicapees_foyer_r844_4", "kind": "bool", "values": YN,
         "representative": {"oui": "vrai", "non": "faux"},
         "source": "code_construction_reglementaire.catala_fr:5530-5545 (R844-4)"},
    ],
    "output": {"name": "eligibilite_apl", "values": ["eligible", "ineligible"],
               "source": "prologue.catala_fr:336-341, 391; code_construction_legislatif.catala_fr:76-91, 404-410, 631-645"},
    "exclusions": [],
    "fixed_inputs": {
        "date_courante": {"value": DATE_5, "why": "date of official test Exemple1"},
        "other inputs": {"value": "as in official test Exemple1 (tests_eligibilite_apl.catala_fr:8-107), date of marriage 2010-11-26 when Mariés",
                         "why": "base case = the only official test of this scope"},
    },
    "notes": "Sub-table 5 of 5 of FR-APL. Household ranges: 0-3 other occupants and 0-4 dependants, so 1 to 9 persons, which reaches the 70 m² cap (8 persons) and the Mayotte 54 m² cap (9 persons). Surface intervals are bounded by every threshold the code computes for these households, so the output is constant inside each interval; the representative is the lower bound (8 for below_9).",
}


def build_inputs(row):
    c = base_case()
    c["date_courante"] = DATE_5
    c["residence"] = row["residence"]
    c["nationalite"] = row["nationalite_demandeur"]
    c["situation"] = ("Maries", "2010-11-26") if row["situation_familiale"] == "Maries" else row["situation_familiale"]
    c["autres_occupants"] = int(row["nombre_autres_occupants_logement"])
    c["n_enfants"] = int(row["nombre_personnes_a_charge"])
    c["surface"] = dict(SURFACES)[row["surface_m_carres"]]
    c["r844_4"] = row["personnes_agees_handicapees_foyer_r844_4"] == "oui"
    return apl_inputs(c)


OFFICIAL_CASES = [
    {"case_id": "tests_eligibilite_apl.catala_fr:Exemple1",
     "row": {"residence": "Metropole", "nationalite_demandeur": "Francaise", "situation_familiale": "Maries",
             "nombre_autres_occupants_logement": "1", "nombre_personnes_a_charge": "3",
             "surface_m_carres": "from_72", "personnes_agees_handicapees_foyer_r844_4": "non"},
     "expected": "eligible", "original": exemple1_original},
]
