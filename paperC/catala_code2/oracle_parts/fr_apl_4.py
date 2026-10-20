# ---------------------------------------------------------------------------
# FR-APL-4: conditions common to the personal housing aids
# (ÉligibilitéAidesPersonnelleLogement) as they reach APL eligibility.
# ---------------------------------------------------------------------------
RESIDENCES_4 = ["Metropole", "LaReunion", "Mayotte"]
NATIONALITES = ["Francaise", "Etrangere_T_T", "Etrangere_T_F", "Etrangere_F_T", "Etrangere_F_F"]
PARTS = [("autre", None), ("parts_below_10pct", "0.05"), ("parts_10pct", "0.10"), ("parts_above_10pct", "0.50")]
AGES = [("sans_objet", None), ("under_30", "1995-01-01"), ("30th_birthday_on_date", "1990-03-10"),
        ("over_30", "1980-01-01")]
YN = ["oui", "non"]
DATE_4 = "2020-03-10"
SRC = "aides_logement/"
SPEC = {
    "id": "FR-APL-4",
    "title": "APL eligibility (ÉligibilitéAidePersonnaliséeLogement.éligibilité), common conditions: nationality, main residence, IFI, decency, subletting, family ownership",
    "source": {"repository": "https://github.com/CatalaLang/catala-examples",
               "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
               "entry_point": "Aides_logement.ÉligibilitéAidePersonnaliséeLogement (output éligibilité), sub-scope ÉligibilitéAidesPersonnelleLogement",
               "files": [SRC + "prologue.catala_fr", SRC + "code_construction_legislatif.catala_fr",
                         SRC + "code_construction_reglementaire.catala_fr", SRC + "tests/tests_eligibilite_apl.catala_fr",
                         "prologue_france/prologue_france.catala_fr"]},
    "attributes": [
        {"name": "residence", "kind": "enum", "values": RESIDENCES_4,
         "representative": {c: "France.Collectivité." + c for c in RESIDENCES_4},
         "source": "code_construction_legislatif.catala_fr:1389-1402 (Mayotte nationality rule); other collectivities share the general rule at the fixed date"},
        {"name": "nationalite_demandeur", "kind": "enum", "values": NATIONALITES,
         "representative": {"Francaise": "Française",
                            "Etrangere_T_T": "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: vrai, satisfait_art_4_ordonnance_2002_mayotte: vrai}",
                            "Etrangere_T_F": "Étrangère {l512_2: vrai, art_4_mayotte: faux}",
                            "Etrangere_F_T": "Étrangère {l512_2: faux, art_4_mayotte: vrai}",
                            "Etrangere_F_F": "Étrangère {l512_2: faux, art_4_mayotte: faux}"},
         "source": "code_construction_legislatif.catala_fr:129-136 (L822-2), 1389-1402 (Mayotte)"},
        {"name": "residence_principale", "kind": "bool", "values": YN,
         "representative": {"oui": "vrai", "non": "faux"},
         "source": "code_construction_legislatif.catala_fr:42-46, 76-91, 146-160"},
        {"name": "rattache_foyer_fiscal_parent_ifi", "kind": "bool", "values": YN,
         "representative": {"oui": "vrai", "non": "faux"},
         "source": "code_construction_legislatif.catala_fr:361-371 (L822-8)"},
        {"name": "logement_decent", "kind": "bool", "values": YN,
         "representative": {"oui": "vrai", "non": "faux"},
         "source": "code_construction_legislatif.catala_fr:381-384 (L822-9)"},
        {"name": "loue_ou_sous_loue_a_des_tiers", "kind": "bool", "values": YN,
         "representative": {"oui": "LouéOuSousLouéÀDesTiers.Oui contenu PersonneSousLocation", "non": "LouéOuSousLouéÀDesTiers.Non"},
         "source": "code_construction_legislatif.catala_fr:232-255 (L822-4)"},
        {"name": "age_personne_sous_location", "kind": "interval", "values": [l for l, _ in AGES],
         "representative": {"sans_objet": "no PersonneSousLocation", "under_30": "born 1995-01-01",
                            "30th_birthday_on_date": "born 1990-03-10", "over_30": "born 1980-01-01"},
         "source": "code_construction_legislatif.catala_fr:240-255; prologue_france VérificationÂgeSupérieurÀ (date_naissance + 30 an > date_courante)"},
        {"name": "sous_locataire_conforme_l442_1", "kind": "enum", "values": ["sans_objet", "oui", "non"],
         "representative": {"sans_objet": "no PersonneSousLocation", "oui": "vrai", "non": "faux"},
         "source": "code_construction_legislatif.catala_fr:240-255"},
        {"name": "proprietaire_famille", "kind": "interval", "values": [l for l, _ in PARTS],
         "representative": {"autre": "ParentOuAutre.Autre", "parts_below_10pct": "DemandeurOuConjointOuParentOuViaPartsSociétés 0,05",
                            "parts_10pct": "DemandeurOuConjointOuParentOuViaPartsSociétés 0,10", "parts_above_10pct": "DemandeurOuConjointOuParentOuViaPartsSociétés 0,50"},
         "source": "code_construction_legislatif.catala_fr:171-221 (L822-3); code_construction_reglementaire.catala_fr:104-106 (threshold 10 %, strict <)"},
        {"name": "usufruit_famille", "kind": "interval", "values": [l for l, _ in PARTS],
         "representative": {"autre": "ParentOuAutre.Autre", "parts_below_10pct": "DemandeurOuConjointOuParentOuViaPartsSociétés 0,05",
                            "parts_10pct": "DemandeurOuConjointOuParentOuViaPartsSociétés 0,10", "parts_above_10pct": "DemandeurOuConjointOuParentOuViaPartsSociétés 0,50"},
         "source": "code_construction_legislatif.catala_fr:171-221; code_construction_reglementaire.catala_fr:104-106"},
        {"name": "mode_occupation", "kind": "enum", "values": ["Locataire", "AccessionProprieteLocalUsageExclusifHabitation"],
         "representative": {"Locataire": "Locataire, Location of Exemple1 (BailleurSocial conventionné)",
                            "AccessionProprieteLocalUsageExclusifHabitation": "Propriétaire with prêt D331_32 held by Demandeur, signed 2015-06-01, Neuf (an APL-eligible loan)"},
         "source": "code_construction_legislatif.catala_fr:146-198 (L822-2, L822-3 1° applies to Locataire only)"},
    ],
    "output": {"name": "eligibilite_apl", "values": ["eligible", "ineligible"],
               "source": "prologue.catala_fr:336-341, 391; code_construction_legislatif.catala_fr:631-645"},
    "exclusions": [
        {"id": "sublet_details_iff_sublet",
         "description": "the subtenant's age and L442-1 status exist exactly when the dwelling is sublet",
         "predicate": "(loue_ou_sous_loue_a_des_tiers == 'non') != (age_personne_sous_location == 'sans_objet') or (loue_ou_sous_loue_a_des_tiers == 'non') != (sous_locataire_conforme_l442_1 == 'sans_objet')",
         "source": "prologue.catala_fr LouéOuSousLouéÀDesTiers (Oui carries PersonneSousLocation, Non carries nothing)"},
    ],
    "fixed_inputs": {
        "date_courante": {"value": DATE_4, "why": "date of official test Exemple1"},
        "other inputs": {"value": "as in official test Exemple1 (tests_eligibilite_apl.catala_fr:8-107)",
                         "why": "base case = the only official test of this scope"},
    },
    "notes": "Sub-table 4 of 5 of FR-APL. Residences reduced to Métropole (official), La Réunion (one overseas department under the general rules) and Mayotte (own nationality rule); at the fixed date 2020-03-10 the other collectivities follow the same rules as Métropole for these conditions. Representatives of age_personne_sous_location are relative to the fixed date 2020-03-10.",
}


def build_inputs(row):
    c = base_case()
    c["date_courante"] = DATE_4
    c["residence"] = row["residence"]
    c["nationalite"] = row["nationalite_demandeur"]
    c["residence_principale"] = row["residence_principale"] == "oui"
    c["ifi"] = row["rattache_foyer_fiscal_parent_ifi"] == "oui"
    c["decent"] = row["logement_decent"] == "oui"
    if row["loue_ou_sous_loue_a_des_tiers"] == "oui":
        c["sous_location"] = sous_location(dict(AGES)[row["age_personne_sous_location"]],
                                           row["sous_locataire_conforme_l442_1"] == "oui")
    c["proprietaire"] = dict(PARTS)[row["proprietaire_famille"]]
    c["usufruit"] = dict(PARTS)[row["usufruit_famille"]]
    if row["mode_occupation"] == "Locataire":
        c["mode"] = ("Locataire", location())
    else:
        c["mode"] = ("AccessionProprieteLocalUsageExclusifHabitation", proprietaire())
    return apl_inputs(c)


OFFICIAL_CASES = [
    {"case_id": "tests_eligibilite_apl.catala_fr:Exemple1",
     "row": {"residence": "Metropole", "nationalite_demandeur": "Francaise", "residence_principale": "oui",
             "rattache_foyer_fiscal_parent_ifi": "non", "logement_decent": "oui",
             "loue_ou_sous_loue_a_des_tiers": "non", "age_personne_sous_location": "sans_objet",
             "sous_locataire_conforme_l442_1": "sans_objet", "proprietaire_famille": "autre",
             "usufruit_famille": "autre", "mode_occupation": "Locataire"},
     "expected": "eligible", "original": exemple1_original},
]
