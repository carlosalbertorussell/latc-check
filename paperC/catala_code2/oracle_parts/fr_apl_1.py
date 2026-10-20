# ---------------------------------------------------------------------------
# FR-APL-1: rental housing (Locataire, SousLocataire): lessor and convention.
# ---------------------------------------------------------------------------
BAILLEURS = {
    "social_conventionne": ("BailleurSocial", True),
    "social_non_conventionne": ("BailleurSocial", False),
    "prive_conventionnement_social_conventionne": ("BailleurPriveAvecConventionnementSocial", True),
    "prive_conventionnement_social_non_conventionne": ("BailleurPriveAvecConventionnementSocial", False),
    "prive": ("BailleurPrive", False),
}
SRC = "aides_logement/"
SPEC = {
    "id": "FR-APL-1",
    "title": "APL eligibility (ÉligibilitéAidePersonnaliséeLogement.éligibilité), rented housing: lessor and convention by date and collectivity",
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
         "source": "prologue_france/prologue_france.catala_fr:9-18 (Collectivité); Ménage.résidence prologue.catala_fr"},
        {"name": "mode_occupation", "kind": "enum", "values": ["Locataire", "SousLocataire"],
         "representative": {"Locataire": "ModeOccupation.Locataire (Location of Exemple1 with the lessor below)",
                            "SousLocataire": "ModeOccupation.SousLocataire (same Location)"},
         "source": "prologue.catala_fr ModeOccupation; code_construction_legislatif.catala_fr:690-709 (L831-1 2°)"},
        {"name": "bailleur", "kind": "enum", "values": list(BAILLEURS),
         "representative": {
             "social_conventionne": "BailleurSocial {conventionné_livre_III_titre_V_chap_III: vrai, réduction_loyer_solidarité_perçue: 0 €}",
             "social_non_conventionne": "BailleurSocial {conventionné_livre_III_titre_V_chap_III: faux, réduction_loyer_solidarité_perçue: 0 €}",
             "prive_conventionnement_social_conventionne": "BailleurPrivéAvecConventionnementSocial {conventionné_livre_III_titre_II_chap_I_sec_3: vrai}",
             "prive_conventionnement_social_non_conventionne": "BailleurPrivéAvecConventionnementSocial {conventionné_livre_III_titre_II_chap_I_sec_3: faux}",
             "prive": "BailleurPrivé"},
         "source": "prologue.catala_fr TypeBailleur, ConventionBailleurSocial, ConventionANHA; code_construction_legislatif.catala_fr:690-709"},
    ],
    "output": {"name": "eligibilite_apl", "values": ["eligible", "ineligible"],
               "source": "prologue.catala_fr:391 (résultat éligibilité condition); code_construction_legislatif.catala_fr:631-645"},
    "exclusions": [],
    "fixed_inputs": {
        "other inputs": {"value": "as in official test Exemple1 (tests_eligibilite_apl.catala_fr:8-107): married 2010-11-26, 3 children, 1 other occupant, 80 m², Zone1, main residence, decent, not sublet, no family ownership, French applicant born 1970-05-02, rent 750 €",
                         "why": "base case = the only official test of this scope; only the attributes above vary"},
    },
    "notes": "Sub-table 1 of 5 of FR-APL. Rented housing only; the lessor convention is the APL-specific condition L831-1 2°. Mayotte rows are ineligible throughout because the fixed applicant is French and the Mayotte rule of condition_nationalité maps Française to faux (code_construction_legislatif.catala_fr:1394-1402). Mayotte between 2024-01-01 and 2024-10-31 raises a Catala Conflict in Smic (REJECTED).",
}


def build_inputs(row):
    c = base_case()
    c["date_courante"] = date_of(row["date_courante"])
    c["residence"] = row["residence"]
    code, conv = BAILLEURS[row["bailleur"]]
    c["mode"] = (row["mode_occupation"], location(code, conv))
    return apl_inputs(c)


OFFICIAL_CASES = [
    {"case_id": "tests_eligibilite_apl.catala_fr:Exemple1",
     "row": {"date_courante": "2019-10-01_to_2020-12-31", "residence": "Metropole",
             "mode_occupation": "Locataire", "bailleur": "social_conventionne"},
     "expected": "eligible", "original": exemple1_original},
]
