#!/usr/bin/env python3
"""Oracle for sample FR-APL-5 (Paper C, second coder, paperC/specs2/FR-APL-5).

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

# ===== part: fr_apl_5.py =====
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
