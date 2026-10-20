# ---------------------------------------------------------------------------
# FR-APL-3: home ownership (AccessionPropriété..., LocationAccession): loan.
# ---------------------------------------------------------------------------
TYPES_PRET = ["D331_32", "D331_63_64", "D331_59_8", "D331_76_1", "Autre"]
TITULAIRES = ["Demandeur", "VendeurQuandDemandeurAContratLocationAccession"]
SIGNATURES = [("before_2017-12-31", "2017-12-30"), ("on_2017-12-31", "2017-12-31"),
              ("2018-01-01_to_2019-12-31", "2018-01-01"), ("from_2020-01-01", "2020-01-01")]
ANCIENNETE = {"neuf": "Neuf", "ancien_ameliore_par_occupant": "Ancien_Oui",
              "ancien_non_ameliore_par_occupant": "Ancien_Non"}
SRC = "aides_logement/"
SPEC = {
    "id": "FR-APL-3",
    "title": "APL eligibility (ÉligibilitéAidePersonnaliséeLogement.éligibilité), home ownership: loan type, holder, signature date, age of dwelling, zone",
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
         "source": "prologue_france/prologue_france.catala_fr:9-18"},
        {"name": "mode_occupation", "kind": "enum",
         "values": ["AccessionProprieteLocalUsageExclusifHabitation", "LocationAccession"],
         "representative": {"AccessionProprieteLocalUsageExclusifHabitation": "ModeOccupation.AccessionPropriétéLocalUsageExclusifHabitation (Propriétaire below)",
                            "LocationAccession": "ModeOccupation.LocationAccession (Propriétaire below)"},
         "source": "prologue.catala_fr ModeOccupation; code_construction_legislatif.catala_fr:668-677 (L831-1 1°), 755-763 (L831-1 6°)"},
        {"name": "type_pret", "kind": "enum", "values": TYPES_PRET,
         "representative": {t: "TypePrêt." + t for t in TYPES_PRET},
         "source": "code_construction_reglementaire.catala_fr:3065-3073 (R832-5), 3103-3111 (R832-7)"},
        {"name": "titulaire_pret", "kind": "enum", "values": TITULAIRES,
         "representative": {t: "TitulairePrêt." + t for t in TITULAIRES},
         "source": "code_construction_reglementaire.catala_fr:3065-3111"},
        {"name": "date_signature_pret", "kind": "interval", "values": [l for l, _ in SIGNATURES],
         "representative": {l: r for l, r in SIGNATURES},
         "source": "code_construction_legislatif.catala_fr:772-815 (L831-2: >= 2017-12-31 base exclusion, [2018-01-01, 2020-01-01) exception)"},
        {"name": "anciennete_logement", "kind": "enum", "values": list(ANCIENNETE),
         "representative": {"neuf": "NeufOuAncien.Neuf", "ancien_ameliore_par_occupant": "NeufOuAncien.Ancien contenu AmélioréParOccupant.Oui",
                            "ancien_non_ameliore_par_occupant": "NeufOuAncien.Ancien contenu AmélioréParOccupant.Non"},
         "source": "prologue.catala_fr NeufOuAncien; code_construction_legislatif.catala_fr:796-815"},
        {"name": "zone", "kind": "enum", "values": ["Zone1", "Zone2", "Zone3"],
         "representative": {z: "ZoneDHabitation." + z for z in ["Zone1", "Zone2", "Zone3"]},
         "source": "arrete_2019-09-27.catala_fr:6070-6074 (Zone3 = commune of L831-2 last paragraph, from 2019-10-01)"},
    ],
    "output": {"name": "eligibilite_apl", "values": ["eligible", "ineligible"],
               "source": "prologue.catala_fr:391; code_construction_legislatif.catala_fr:631-645"},
    "exclusions": [
        {"id": "loan_signed_after_current_date",
         "description": "a loan signed on or after 2020-01-01 cannot exist on a current date in 2019-09-01..2019-09-30",
         "predicate": "date_signature_pret == 'from_2020-01-01' and date_courante == '2019-09-01_to_2019-09-30'",
         "source": "factual: date_signature is a past event at date_courante (Prêt.date_signature, prologue.catala_fr)"},
    ],
    "fixed_inputs": {
        "Propriétaire": {"value": "mensualité_principale 700 €, charges 0 €, date_entrée_logement = the earlier of the signature and current-date representatives, no works (PasDeTravaux both), not first occupation, no copropriété, situation_r822_11_13_17 faux, opérations_logement_évolutifs_sociaux faux, accord_financement PasdAccord",
                         "why": "fields that the eligibility rules of the APL scope do not read; values chosen once"},
        "other inputs": {"value": "as in official test Exemple1 (tests_eligibilite_apl.catala_fr:8-107) apart from mode_occupation and zone",
                         "why": "base case = the only official test of this scope"},
    },
    "notes": "Sub-table 3 of 5 of FR-APL. No official test of this scope covers home ownership, so no official row maps here. caractéristiques_prêt_l831_1_6 (prologue.catala_fr:387) has no definition, so LocationAccession is never eligible. Mayotte rows are ineligible throughout (French applicant) and REJECTED in 2024-01-01..2024-10-31 (Smic Conflict).",
}


def build_inputs(row):
    c = base_case()
    d = date_of(row["date_courante"])
    s = dict(SIGNATURES)[row["date_signature_pret"]]
    c["date_courante"] = d
    c["residence"] = row["residence"]
    c["zone"] = row["zone"]
    p = proprietaire(type_pret=row["type_pret"], titulaire=row["titulaire_pret"],
                     date_signature=s, anciennete=ANCIENNETE[row["anciennete_logement"]],
                     date_entree=min(s, d))
    c["mode"] = (row["mode_occupation"], p)
    return apl_inputs(c)


OFFICIAL_CASES = []
