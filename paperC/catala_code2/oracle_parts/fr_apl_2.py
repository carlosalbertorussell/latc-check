# ---------------------------------------------------------------------------
# FR-APL-2: logement-foyer (RésidentLogementFoyer): type and conventions.
# ---------------------------------------------------------------------------
FOYER_TYPES = ["LogementPersonnesAgeesOuHandicapees", "ResidenceSociale",
               "FoyerJeunesTravailleursOuMigrantsConventionneL353_2Avant1995", "Autre"]
YN = ["oui", "non"]
SRC = "aides_logement/"
SPEC = {
    "id": "FR-APL-2",
    "title": "APL eligibility (ÉligibilitéAidePersonnaliséeLogement.éligibilité), logement-foyer: type and conventions by date and collectivity",
    "source": {"repository": "https://github.com/CatalaLang/catala-examples",
               "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
               "entry_point": "Aides_logement.ÉligibilitéAidePersonnaliséeLogement (output éligibilité)",
               "files": [SRC + "prologue.catala_fr", SRC + "code_construction_legislatif.catala_fr",
                         SRC + "code_construction_reglementaire.catala_fr", SRC + "arrete_2019-09-27.catala_fr",
                         SRC + "archives.catala_fr", SRC + "autres_sources.catala_fr",
                         SRC + "code_sécurité_sociale.catala_fr", SRC + "tests/tests_eligibilite_apl.catala_fr",
                         "smic/Smic.catala_fr", "prestations_familiales/", "prologue_france/"]},
    "attributes": [
        {"name": "date_courante", "kind": "interval", "values": [l for l, _ in DATE_INTERVALS],
         "representative": {l: r for l, r in DATE_INTERVALS}, "source": DATE_SOURCE},
        {"name": "residence", "kind": "enum", "values": COLLECTIVITES,
         "representative": {c: "France.Collectivité." + c for c in COLLECTIVITES},
         "source": "prologue_france/prologue_france.catala_fr:9-18; code_construction_legislatif.catala_fr:1471-1488 and code_construction_reglementaire.catala_fr:6001-6018 (DROM rules)"},
        {"name": "type_logement_foyer", "kind": "enum", "values": FOYER_TYPES,
         "representative": {t: "TypeLogementFoyer." + t for t in FOYER_TYPES},
         "source": "code_construction_reglementaire.catala_fr:3729-3752 (R832-20, type Autre excluded); 6001-6018 (R861-20 1°)"},
        {"name": "conventionne_livre_III_titre_V_chap_III", "kind": "bool", "values": YN,
         "representative": {"oui": "vrai", "non": "faux"},
         "source": "code_construction_legislatif.catala_fr:736-744 (L831-1 5°)"},
        {"name": "conventionne_selon_regles_drom", "kind": "bool", "values": YN,
         "representative": {"oui": "vrai", "non": "faux"},
         "source": "code_construction_legislatif.catala_fr:1471-1488 (L861-? 5° for Guadeloupe, Guyane, Martinique, La Réunion, Mayotte)"},
        {"name": "remplit_conditions_r832_21", "kind": "bool", "values": YN,
         "representative": {"oui": "vrai", "non": "faux"},
         "source": "code_construction_reglementaire.catala_fr:3800-3813 (R832-21)"},
    ],
    "output": {"name": "eligibilite_apl", "values": ["eligible", "ineligible"],
               "source": "prologue.catala_fr:391; code_construction_legislatif.catala_fr:631-645"},
    "exclusions": [],
    "fixed_inputs": {
        "mode_occupation": {"value": "RésidentLogementFoyer with logement_foyer_jeunes_travailleurs faux, date_conventionnement 2010-01-01, construit_application_loi_1957_12_III faux, redevance 400 €, catégorie AutresPersonnes, not furnished, not a room, no colocation",
                            "why": "fields that the eligibility rules of the APL scope do not read; values chosen once"},
        "other inputs": {"value": "as in official test Exemple1 (tests_eligibilite_apl.catala_fr:8-107) apart from mode_occupation",
                         "why": "base case = the only official test of this scope"},
    },
    "notes": "Sub-table 2 of 5 of FR-APL. Official test Exemple1 is a tenancy, so no official row maps onto this table. Mayotte rows are ineligible throughout (French applicant, see FR-APL-1 notes) and REJECTED in 2024-01-01..2024-10-31 (Smic Conflict).",
}


def build_inputs(row):
    c = base_case()
    c["date_courante"] = date_of(row["date_courante"])
    c["residence"] = row["residence"]
    lf = logement_foyer(row["conventionne_livre_III_titre_V_chap_III"] == "oui",
                        row["conventionne_selon_regles_drom"] == "oui",
                        type_logement=row["type_logement_foyer"],
                        r832_21=row["remplit_conditions_r832_21"] == "oui")
    c["mode"] = ("ResidentLogementFoyer", lf)
    return apl_inputs(c)


OFFICIAL_CASES = []
