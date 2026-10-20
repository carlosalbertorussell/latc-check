#!/usr/bin/env python3
"""Oracle for sample FR-APL-3 (Paper C, second coder, paperC/specs2/FR-APL-3).

Usage:
  python3 oracle.py --enumerate        # writes ground_truth.csv
  python3 oracle.py --check-official   # official tests: encoding vs oracle
  python3 oracle.py --write-spec --write-official   # regenerate spec.json, official_examples.csv

Assembled by paperC/catala_code2/make_oracles.py from paperC/catala_code2/oracle_parts/.
Requires Python >= 3.12 (Catala 1.3.0 runtime).
"""

# ===== part: apl_common.py =====
# ---------------------------------------------------------------------------
# APL common part (identical in every FR-APL-* oracle): imports the Python
# that Catala 1.3.0 generated from catala-examples 2694b17 and builds the
# inputs of ÉligibilitéAidePersonnaliséeLogement. The base case is the
# official test Exemple1 (tests_eligibilite_apl.catala_fr lines 8-107);
# each sub-table overrides some of its fields.
# ---------------------------------------------------------------------------
import os as _os
import sys as _sys

_GEN = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "catala_code2"))
_sys.path.insert(0, _os.path.join(_GEN, "runtime"))
_sys.path.insert(0, _GEN)

from catala_runtime import Array, Bool, Date, Integer, Money, Decimal, Unit  # noqa: E402
from generated import Aides_logement as al  # noqa: E402
from generated import Prestations_familiales as pf  # noqa: E402
from generated import France as fr  # noqa: E402

D = lambda s: Date(*map(int, s.split("-")))  # noqa: E731

COLLECTIVITES = ["Metropole", "Guadeloupe", "Guyane", "Martinique", "LaReunion",
                 "Mayotte", "SaintBarthelemy", "SaintMartin", "SaintPierreEtMiquelon"]


def enum(cls, code, payload=None):
    return cls(getattr(cls.Code, code), Unit() if payload is None else payload)


def child(ident, born, scol, etudes):
    return enum(al.PersonneACharge, "EnfantACharge", al.EnfantACharge(
        identifiant=Integer(ident),
        nationalite=enum(al.Nationalite, "Francaise"),
        a_deja_ouvert_droit_aux_allocations_familiales=Bool(True),
        date_de_naissance=D(born),
        remuneration_mensuelle=Money("0.00"),
        obligation_scolaire=enum(pf.SituationObligationScolaire, scol),
        situation_garde_alternee=enum(al.SituationGardeAlternee, "PasDeGardeAlternee"),
        etudes_apprentissage_stage_formation_pro_impossibilite_travail=Bool(etudes)))


# The three children of Exemple1, in order; a household with k children takes
# the first k of this list, extended with further children born 2012-01-01.
EXEMPLE1_CHILDREN = [("2001-01-01", "Apres", True), ("2009-01-01", "Pendant", False),
                     ("2012-01-01", "Pendant", False)]


def children(k):
    spec = (EXEMPLE1_CHILDREN + [("2012-01-01", "Pendant", False)] * 10)[:k]
    return [child(i, b, s, e) for i, (b, s, e) in enumerate(spec)]


def location(bailleur_code="BailleurSocial", convention=True):
    if bailleur_code == "BailleurSocial":
        b = enum(al.TypeBailleur, "BailleurSocial", al.ConventionBailleurSocial(
            conventionne_livre_III_titre_V_chap_III=Bool(convention),
            reduction_loyer_solidarite_percue=Money("0.00")))
    elif bailleur_code == "BailleurPriveAvecConventionnementSocial":
        b = enum(al.TypeBailleur, "BailleurPriveAvecConventionnementSocial", al.ConventionANHA(
            conventionne_livre_III_titre_II_chap_I_sec_3=Bool(convention)))
    else:
        b = enum(al.TypeBailleur, "BailleurPrive")
    return al.Location(
        bailleur=b, loyer_principal=Money("750.00"),
        beneficiaire_aide_adulte_ou_enfant_handicapes=Bool(False),
        logement_est_chambre=Bool(False), colocation=Bool(False),
        agees_ou_handicap_adultes_hebergees_onereux_particuliers=Bool(False),
        logement_meuble_d842_2=Bool(False),
        changement_logement_d842_4=enum(al.ChangementLogementD8424, "PasDeChangement"))


def logement_foyer(conv_metropole, conv_drom, type_logement="ResidenceSociale", r832_21=True):
    return al.LogementFoyer(
        type_logement=enum(al.TypeLogementFoyer, type_logement),
        logement_foyer_jeunes_travailleurs=Bool(False),
        remplit_conditions_r832_21=Bool(r832_21),
        conventionne_livre_III_titre_V_chap_III=Bool(conv_metropole),
        conventionne_selon_regles_drom=Bool(conv_drom),
        date_conventionnement=D("2010-01-01"),
        construit_application_loi_1957_12_III=Bool(False),
        redevance=Money("400.00"),
        categorie_equivalence_loyer_d842_16=enum(al.CategorieEquivalenceLoyerAllocationLogementFoyer, "AutresPersonnes"),
        beneficiaire_aide_adulte_ou_enfant_handicapes=Bool(False),
        logement_meuble_d842_2=Bool(False), logement_est_chambre=Bool(False),
        colocation=Bool(False))


def proprietaire(type_pret="D331_32", titulaire="Demandeur", date_signature="2015-06-01",
                 anciennete="Neuf", date_entree="2015-06-01"):
    if anciennete == "Neuf":
        anc = enum(al.NeufOuAncien, "Neuf")
    else:  # "Ancien_Oui" / "Ancien_Non"
        anc = enum(al.NeufOuAncien, "Ancien", enum(al.AmelioreParOccupant, anciennete.split("_")[1]))
    return al.Proprietaire(
        mensualite_principale=Money("700.00"), charges_mensuelles_pret=Money("0.00"),
        date_entree_logement=D(date_entree),
        type_travaux_logement_d832_15=enum(al.TypeTravauxLogementD83215, "PasDeTravaux"),
        type_travaux_logement_r842_5=enum(al.TypeTravauxLogementR8425, "PasDeTravaux"),
        local_habite_premiere_fois_beneficiaire=Bool(False), copropriete=Bool(False),
        situation_r822_11_13_17=Bool(False), anciennete_logement=anc,
        pret=al.Pret(type_pret=enum(al.TypePret, type_pret), date_signature=D(date_signature),
                     titulaire_pret=enum(al.TitulairePret, titulaire),
                     accord_financement_representant_Etat_outre_mer=enum(
                         al.AccordFinancementRepresentantEtatOutreMer, "PasdAccord")),
        operations_logement_evolutifs_sociaux_accession_propriete_aidee_Etat=Bool(False))


def nationalite(code):
    """'Francaise' or 'Etrangere_<l512_2>_<mayotte_art4>' with T/F flags."""
    if code == "Francaise":
        return enum(al.Nationalite, "Francaise")
    _, a, b = code.split("_")
    return enum(al.Nationalite, "Etrangere", al.ConditionsEtrangers(
        satisfait_conditions_l512_2_code_securite_sociale=Bool(a == "T"),
        satisfait_art_4_ordonnance_2002_mayotte=Bool(b == "T")))


def parent_ou_autre(parts):
    """None -> Autre; a decimal string -> DemandeurOuConjointOuParentOuViaPartsSociétés."""
    if parts is None:
        return enum(al.ParentOuAutre, "Autre")
    return enum(al.ParentOuAutre, "DemandeurOuConjointOuParentOuViaPartsSocietes", Decimal(parts))


def sous_location(birth=None, conforme=False):
    if birth is None:
        return enum(al.LoueOuSousLoueADesTiers, "Non")
    return enum(al.LoueOuSousLoueADesTiers, "Oui", al.PersonneSousLocation(
        date_naissance_personne_sous_location=D(birth), conforme_article_l442_1=Bool(conforme)))


def base_case():
    """Field values of the official test Exemple1."""
    return dict(
        date_courante="2020-03-10", residence="Metropole",
        prestations=["AllocationSoutienEnfantHandicape", "ComplementFamilial", "AllocationsFamiliales"],
        situation=("Maries", "2010-11-26"), n_enfants=3, autres_occupants=1,
        mode=("Locataire", location()), residence_principale=True,
        proprietaire=None, usufruit=None, sous_location=sous_location(),
        decent=True, surface=80, zone="Zone1", ifi=False, enfant_a_naitre=False,
        r844_4=False, demandeur_naissance="1970-05-02", nationalite="Francaise")


def situation_familiale(code, date_mariage="2010-11-26"):
    if code == "Maries":
        return enum(al.SituationFamiliale, "Maries", D(date_mariage))
    return enum(al.SituationFamiliale, code)


def apl_inputs(c):
    mode_code, mode_payload = c["mode"]
    menage = al.Menage(
        prestations_recues=Array([enum(al.PrestationRecue, p) for p in c["prestations"]]),
        logement=al.Logement(
            residence_principale=Bool(c["residence_principale"]),
            mode_occupation=enum(al.ModeOccupation, mode_code, mode_payload),
            proprietaire=parent_ou_autre(c["proprietaire"]),
            loue_ou_sous_loue_a_des_tiers=c["sous_location"],
            usufruit=parent_ou_autre(c["usufruit"]),
            logement_decent_l89_462=Bool(c["decent"]),
            surface_m_carres=Integer(c["surface"]),
            zone=enum(al.ZoneDHabitation, c["zone"])),
        personnes_a_charge=Array(children(c["n_enfants"])),
        nombre_autres_occupants_logement=Integer(c["autres_occupants"]),
        situation_familiale=situation_familiale(*((c["situation"],) if isinstance(c["situation"], str) else c["situation"])),
        condition_rattache_foyer_fiscal_parent_ifi=Bool(c["ifi"]),
        enfant_a_naitre_apres_quatrieme_mois_grossesse=Bool(c["enfant_a_naitre"]),
        personnes_agees_handicapees_foyer_r844_4=Bool(c["r844_4"]),
        residence=enum(fr.Collectivite, c["residence"]))
    demandeur = al.Demandeur(
        date_naissance=D(c["demandeur_naissance"]), nationalite=nationalite(c["nationalite"]),
        personne_hebergee_centre_soin_l_L162_22_3_securite_sociale=Bool(False),
        est_non_salarie_agricole_l781_8_l_781_46_code_rural=Bool(False),
        magistrat_fonctionnaire_centre_interets_materiels_familiaux_hors_mayotte=Bool(False))
    return al.EligibiliteAidePersonnaliseeLogementIn(
        menage_in=menage, demandeur_in=demandeur, date_courante_in=D(c["date_courante"]))


def run_encoding(inputs):
    res = al.eligibilite_aide_personnalisee_logement(inputs)
    return "eligible" if bool(res.eligibilite) else "ineligible"


def exemple1_original():
    """Official Exemple1 with its own inputs (assertion: éligible)."""
    return run_encoding(apl_inputs(base_case()))

# ===== part: fr_dates.py =====
# Date intervals shared by FR-APL-1, -2 and -3. Each cut is a date that the
# encoding compares date_courante against (see CONVERSION_2.md); the
# representative is the interval's first day, except for the interval holding
# the official test date, whose representative is that date (2020-03-10).
DATE_INTERVALS = [
    ("2019-09-01_to_2019-09-30", "2019-09-01"),
    ("2019-10-01_to_2020-12-31", "2020-03-10"),
    ("2021-01-01_to_2021-04-30", "2021-01-01"),
    ("2021-05-01_to_2023-04-04", "2021-05-01"),
    ("2023-04-05_to_2023-08-31", "2023-04-05"),
    ("2023-09-01_to_2023-12-31", "2023-09-01"),
    ("2024-01-01_to_2024-10-31", "2024-01-01"),
    ("from_2024-11-01", "2024-11-01"),
]
DATE_REP = dict(DATE_INTERVALS)
DATE_SOURCE = ("cuts: 2019-09-01 aides_logement/archives.catala_fr:10-12 (personnes_à_charge_prises_en_compte "
               "defined from this date; earlier dates raise NoValue); 2019-10-01 arrete_2019-09-27.catala_fr:6070-6074 "
               "(zone III rule); 2021-01-01 code_construction_legislatif.catala_fr:1333-1339 (Saint-Pierre-et-Miquelon) and "
               "code_construction_reglementaire.catala_fr:6207; 2021-05-01 code_construction_reglementaire.catala_fr:6209-6213; "
               "2023-04-05 code_construction_reglementaire.catala_fr:6001-6018; 2023-09-01 archives.catala_fr:10-24, "
               "code_sécurité_sociale.catala_fr:188-221; 2024-01-01 and 2024-11-01 smic/Smic.catala_fr:431-500 (Mayotte SMIC)")


def date_of(label):
    return DATE_REP[label]

# ===== part: fr_apl_3.py =====
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

# ===== part: oracle_template.py =====
# ---------------------------------------------------------------------------
# Generic part shared (by copy) by every oracle.py of paperC/specs2/.
# The text between the BEGIN/END GENERIC markers is identical in every oracle.
# ---------------------------------------------------------------------------
# BEGIN GENERIC
import csv
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "catala_code2"))


def _attr_names():
    return [a["name"] for a in SPEC["attributes"]]


def excluded(row):
    for ex in SPEC["exclusions"]:
        if eval(ex["predicate"], {"__builtins__": {}}, dict(row)):
            return True
    return False


def evaluate(row):
    """Label of the decision for one row of declared labels."""
    if excluded(row):
        return "EXCLUDED"
    try:
        return run_encoding(build_inputs(row))
    except Exception as exc:  # error or assertion failure raised by the encoding
        LAST_ERRORS[tuple(row[a] for a in _attr_names())] = _describe(exc)
        return "REJECTED"


LAST_ERRORS = {}


def _describe(exc):
    import re
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(exc)).replace("\n", " ").strip()
    return "%s: %s" % (type(exc).__name__, msg)


def enumerate_rows():
    names = _attr_names()
    domains = [a["values"] for a in SPEC["attributes"]]
    for combo in itertools.product(*domains):
        yield dict(zip(names, combo))


def write_ground_truth(path):
    names = _attr_names()
    counts = {}
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(names + ["output"])
        for row in enumerate_rows():
            out = evaluate(row)
            counts[out] = counts.get(out, 0) + 1
            w.writerow([row[a] for a in names] + [out])
    return counts


def write_spec(path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(SPEC, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_official(path):
    names = _attr_names()
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id"] + names + ["output"])
        for case in OFFICIAL_CASES:
            w.writerow([case["case_id"]] + [case["row"][a] for a in names] + [case["expected"]])


def check_official():
    """Re-run each mappable official test through the encoding (original inputs)
    and through the oracle (mapped labels); both must give the asserted label."""
    ok_enc = ok_orc = 0
    for case in OFFICIAL_CASES:
        enc = case["original"]()
        orc = evaluate(case["row"])
        e_ok = enc == case["expected"]
        o_ok = orc == case["expected"]
        ok_enc += e_ok
        ok_orc += o_ok
        print("%s  %s  encoding=%s oracle=%s expected=%s" % (
            "PASS" if (e_ok and o_ok) else "FAIL", case["case_id"], enc, orc, case["expected"]))
    n = len(OFFICIAL_CASES)
    print("encoding (original inputs): %d/%d passed" % (ok_enc, n))
    print("oracle (mapped labels):     %d/%d passed" % (ok_orc, n))
    return ok_enc == n and ok_orc == n


def main(argv):
    if "--write-spec" in argv:
        write_spec(os.path.join(HERE, "spec.json"))
    if "--write-official" in argv:
        write_official(os.path.join(HERE, "official_examples.csv"))
    if "--enumerate" in argv:
        counts = write_ground_truth(os.path.join(HERE, "ground_truth.csv"))
        print(json.dumps(counts, sort_keys=True))
        kinds = {}
        for err in LAST_ERRORS.values():
            k = err.split(":")[0]
            kinds[k] = kinds.get(k, 0) + 1
        if kinds:
            print("REJECTED by exception type:", json.dumps(kinds, sort_keys=True))
            for msg in sorted(set(LAST_ERRORS.values())):
                print("  error:", msg[:300])
    if "--check-official" in argv:
        if not check_official():
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
# END GENERIC
