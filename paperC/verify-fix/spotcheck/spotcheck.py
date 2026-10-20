"""Independent spot-check of the Paper C ground truth (FR-APL-1..5, US-121-1..2).

Written for the independent verification on branch paperc-verify-fr2. It uses only
the Python 3.12 standard library, the bundled Catala runtime
(paperC/catala_more/runtime/catala) and the generated modules
(paperC/catala_more/generated). It does not import any oracle.py, oracle_common.py,
fr_apl_common.py, apl_inputs.py, us121_inputs.py, paperC/harness or latc_check.

Inputs are built from the generated module's own record classes. The household that
the FR-APL tables keep fixed is transcribed here from the official test Exemple1
(aides_logement/tests/tests_eligibilite_apl.catala_fr:16-107, catala-examples
2694b17). Each attribute label is translated into a concrete value by parsing the
`representative` string of spec.json.

Draw: for each sample, N = number of data rows of ground_truth.csv; if N > 50,
rng = random.Random(20261020) (fresh per sample) and idx = sorted(rng.sample(range(N), 50));
else idx = all rows.

Usage: python3.12 spotcheck.py            (official-test validation + 50-row draws)
       python3.12 spotcheck.py --full     (also every row of every table, supplementary)
"""

import csv
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PAPERC = os.path.abspath(os.path.join(HERE, "..", ".."))
CATALA_MORE = os.path.join(PAPERC, "catala_more")
sys.path[:0] = [os.path.join(CATALA_MORE, "runtime", "catala"), CATALA_MORE]

from catala_runtime import (  # noqa: E402
    Array, Bool, CatalaError, Date, Decimal, Integer, Money, Option, Unit,
)
import generated.Aides_logement as AL  # noqa: E402
import generated.France as FR  # noqa: E402
import generated.Prestations_familiales as PF  # noqa: E402
import generated.Us_tax_code as US  # noqa: E402

SPECS = os.path.join(PAPERC, "specs")
SAMPLES = [
    ("FR-APL-1", "FR-APL"), ("FR-APL-2", "FR-APL"), ("FR-APL-3", "FR-APL"),
    ("FR-APL-4", "FR-APL"), ("FR-APL-5", "FR-APL"),
    ("US-121-1", "US-121"), ("US-121-2", "US-121"),
]
SEED = 20261020
DRAW = 50


# --------------------------------------------------------------------------- helpers

def enum(cls, label, payload=None):
    """Constructor of a generated CatalaEnum, looked up by its Catala label."""
    for code in cls.Code:
        if code.label == label:
            return cls(code, Unit() if payload is None else payload)
    raise KeyError(f"{cls.__name__} has no constructor {label!r}")


def parse_date(s):
    m = re.fullmatch(r"\|(\d{4})-(\d{2})-(\d{2})\|", s.strip())
    if not m:
        raise ValueError(f"not a Catala date: {s!r}")
    return Date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def parse_bool(s):
    return {"vrai": Bool(True), "faux": Bool(False)}[s.strip()]


def err_text(e):
    return f"{type(e).__name__} at " + ", ".join(str(p) for p in e.source_positions)


# --------------------------------------------------------- Exemple1, transcribed

def ex1_child(ident, born, oblig, etudes):
    return enum(AL.PersonneACharge, "EnfantÀCharge", AL.EnfantACharge(
        identifiant=Integer(ident),
        nationalite=enum(AL.Nationalite, "Française"),
        a_deja_ouvert_droit_aux_allocations_familiales=Bool(True),
        date_de_naissance=born,
        remuneration_mensuelle=Money("0"),
        obligation_scolaire=enum(PF.SituationObligationScolaire, oblig),
        situation_garde_alternee=enum(AL.SituationGardeAlternee, "PasDeGardeAlternée"),
        etudes_apprentissage_stage_formation_pro_impossibilite_travail=Bool(etudes),
    ))


EX1_CHILDREN = [
    ex1_child(0, Date(2001, 1, 1), "Après", True),
    ex1_child(1, Date(2009, 1, 1), "Pendant", False),
    ex1_child(2, Date(2012, 1, 1), "Pendant", False),
]


def ex1_location(bailleur=None):
    if bailleur is None:
        bailleur = enum(AL.TypeBailleur, "BailleurSocial", AL.ConventionBailleurSocial(
            conventionne_livre_III_titre_V_chap_III=Bool(True),
            reduction_loyer_solidarite_percue=Money("0")))
    return AL.Location(
        bailleur=bailleur,
        loyer_principal=Money("750"),
        beneficiaire_aide_adulte_ou_enfant_handicapes=Bool(False),
        logement_est_chambre=Bool(False),
        colocation=Bool(False),
        agees_ou_handicap_adultes_hebergees_onereux_particuliers=Bool(False),
        logement_meuble_d842_2=Bool(False),
        changement_logement_d842_4=enum(AL.ChangementLogementD8424, "PasDeChangement"),
    )


def exemple1_literal():
    """Exemple1 exactly as written in the test file (no parameters)."""
    menage = AL.Menage(
        residence=enum(FR.Collectivite, "Métropole"),
        prestations_recues=Array([
            enum(AL.PrestationRecue, "AllocationSoutienEnfantHandicapé"),
            enum(AL.PrestationRecue, "ComplémentFamilial"),
            enum(AL.PrestationRecue, "AllocationsFamiliales"),
        ]),
        situation_familiale=enum(AL.SituationFamiliale, "Mariés", Date(2010, 11, 26)),
        personnes_a_charge=Array(list(EX1_CHILDREN)),
        logement=AL.Logement(
            zone=enum(AL.ZoneDHabitation, "Zone1"),
            residence_principale=Bool(True),
            mode_occupation=enum(AL.ModeOccupation, "Locataire", ex1_location()),
            proprietaire=enum(AL.ParentOuAutre, "Autre"),
            loue_ou_sous_loue_a_des_tiers=enum(AL.LoueOuSousLoueADesTiers, "Non"),
            usufruit=enum(AL.ParentOuAutre, "Autre"),
            logement_decent_l89_462=Bool(True),
            surface_m_carres=Integer(80),
        ),
        nombre_autres_occupants_logement=Integer(1),
        condition_rattache_foyer_fiscal_parent_ifi=Bool(False),
        enfant_a_naitre_apres_quatrieme_mois_grossesse=Bool(False),
        personnes_agees_handicapees_foyer_r844_4=Bool(False),
    )
    demandeur = AL.Demandeur(
        date_naissance=Date(1970, 5, 2),
        est_non_salarie_agricole_l781_8_l_781_46_code_rural=Bool(False),
        magistrat_fonctionnaire_centre_interets_materiels_familiaux_hors_mayotte=Bool(False),
        nationalite=enum(AL.Nationalite, "Française"),
        personne_hebergee_centre_soin_l_L162_22_3_securite_sociale=Bool(False),
    )
    return menage, demandeur, Date(2020, 3, 10)


def fr_household(p):
    """Exemple1 household with the overrides in dict p."""
    def g(k, default):
        return p[k] if k in p else default
    menage = AL.Menage(
        residence=g("residence", enum(FR.Collectivite, "Métropole")),
        prestations_recues=Array([
            enum(AL.PrestationRecue, "AllocationSoutienEnfantHandicapé"),
            enum(AL.PrestationRecue, "ComplémentFamilial"),
            enum(AL.PrestationRecue, "AllocationsFamiliales"),
        ]),
        situation_familiale=g("situation_familiale",
                              enum(AL.SituationFamiliale, "Mariés", Date(2010, 11, 26))),
        personnes_a_charge=Array(list(EX1_CHILDREN[:g("n_children", 3)])),
        logement=AL.Logement(
            zone=g("zone", enum(AL.ZoneDHabitation, "Zone1")),
            residence_principale=g("residence_principale", Bool(True)),
            mode_occupation=g("mode_occupation",
                              enum(AL.ModeOccupation, "Locataire", ex1_location())),
            proprietaire=g("proprietaire", enum(AL.ParentOuAutre, "Autre")),
            loue_ou_sous_loue_a_des_tiers=g("loue", enum(AL.LoueOuSousLoueADesTiers, "Non")),
            usufruit=g("usufruit", enum(AL.ParentOuAutre, "Autre")),
            logement_decent_l89_462=g("decent", Bool(True)),
            surface_m_carres=g("surface", Integer(80)),
        ),
        nombre_autres_occupants_logement=g("autres", Integer(1)),
        condition_rattache_foyer_fiscal_parent_ifi=g("ifi", Bool(False)),
        enfant_a_naitre_apres_quatrieme_mois_grossesse=Bool(False),
        personnes_agees_handicapees_foyer_r844_4=g("r844_4", Bool(False)),
    )
    demandeur = AL.Demandeur(
        date_naissance=Date(1970, 5, 2),
        est_non_salarie_agricole_l781_8_l_781_46_code_rural=Bool(False),
        magistrat_fonctionnaire_centre_interets_materiels_familiaux_hors_mayotte=Bool(False),
        nationalite=g("nationalite", enum(AL.Nationalite, "Française")),
        personne_hebergee_centre_soin_l_L162_22_3_securite_sociale=Bool(False),
    )
    return menage, demandeur, g("date_courante", Date(2020, 3, 10))


def run_apl(menage, demandeur, date):
    out = AL.eligibilite_aide_personnalisee_logement(AL.EligibiliteAidePersonnaliseeLogementIn(
        menage_in=menage, demandeur_in=demandeur, date_courante_in=date))
    return "eligible" if bool(out.eligibilite) else "not_eligible"


# ------------------------------------------- representative string -> Catala value

def rep_nationalite(s):
    if s == "Française":
        return enum(AL.Nationalite, "Française")
    m = re.fullmatch(r"Étrangère \{satisfait_conditions_l512_2_code_sécurité_sociale: (vrai|faux), "
                     r"satisfait_art_4_ordonnance_2002_mayotte: (vrai|faux)\}", s)
    return enum(AL.Nationalite, "Étrangère", AL.ConditionsEtrangers(
        satisfait_conditions_l512_2_code_securite_sociale=parse_bool(m.group(1)),
        satisfait_art_4_ordonnance_2002_mayotte=parse_bool(m.group(2))))


def rep_situation(s):
    m = re.fullmatch(r"Mariés (\|.*\|)", s)
    if m:
        return enum(AL.SituationFamiliale, "Mariés", parse_date(m.group(1)))
    return enum(AL.SituationFamiliale, s)


def rep_n_children(s):
    if s == "[]":
        return 0
    m = re.fullmatch(r"the first (\d) EnfantÀCharge of Exemple1", s)
    return int(m.group(1))


def rep_bailleur(s):
    m = re.fullmatch(r"BailleurSocial \{conventionné_livre_III_titre_V_chap_III: (vrai|faux), "
                     r"réduction_loyer_solidarité_perçue: 0 €\}", s)
    if m:
        return enum(AL.TypeBailleur, "BailleurSocial", AL.ConventionBailleurSocial(
            conventionne_livre_III_titre_V_chap_III=parse_bool(m.group(1)),
            reduction_loyer_solidarite_percue=Money("0")))
    m = re.fullmatch(r"BailleurPrivéAvecConventionnementSocial \{conventionné_livre_III_titre_II_chap_I_sec_3: (vrai|faux)\}", s)
    if m:
        return enum(AL.TypeBailleur, "BailleurPrivéAvecConventionnementSocial",
                    AL.ConventionANHA(conventionne_livre_III_titre_II_chap_I_sec_3=parse_bool(m.group(1))))
    assert s == "BailleurPrivé", s
    return enum(AL.TypeBailleur, "BailleurPrivé")


def rep_parent_ou_autre(s):
    if s == "Autre":
        return enum(AL.ParentOuAutre, "Autre")
    m = re.fullmatch(r"DemandeurOuConjointOuParentOuViaPartsSociétés contenu (\d+),(\d+)", s)
    return enum(AL.ParentOuAutre, "DemandeurOuConjointOuParentOuViaPartsSociétés",
                Decimal(f"{m.group(1)}.{m.group(2)}"))


def rep_loue(s):
    if s == "Non":
        return enum(AL.LoueOuSousLoueADesTiers, "Non")
    m = re.fullmatch(r"Oui \{date_naissance_personne_sous_location: (\|[^|]+\|), conforme_article_l442_1: (vrai|faux)\}", s)
    return enum(AL.LoueOuSousLoueADesTiers, "Oui", AL.PersonneSousLocation(
        date_naissance_personne_sous_location=parse_date(m.group(1)),
        conforme_article_l442_1=parse_bool(m.group(2))))


def rep_anciennete(s):
    if s == "Neuf":
        return enum(AL.NeufOuAncien, "Neuf")
    m = re.fullmatch(r"Ancien contenu (Oui|Non)", s)
    return enum(AL.NeufOuAncien, "Ancien", enum(AL.AmelioreParOccupant, m.group(1)))


def rep_mode_ctor(s):
    m = re.fullmatch(r"(\S+) \((Location|Propriétaire) \{\.\.\.\}\)", s)
    return m.group(1)


def logement_foyer(type_logement, conv_l3, r832_21, drom):
    return AL.LogementFoyer(
        type_logement=type_logement,
        logement_foyer_jeunes_travailleurs=Bool(False),
        remplit_conditions_r832_21=r832_21,
        conventionne_livre_III_titre_V_chap_III=conv_l3,
        conventionne_selon_regles_drom=drom,
        date_conventionnement=Date(2000, 1, 1),
        construit_application_loi_1957_12_III=Bool(False),
        redevance=Money("400"),
        categorie_equivalence_loyer_d842_16=enum(AL.CategorieEquivalenceLoyerAllocationLogementFoyer, "AutresPersonnes"),
        beneficiaire_aide_adulte_ou_enfant_handicapes=Bool(False),
        logement_meuble_d842_2=Bool(False),
        logement_est_chambre=Bool(False),
        colocation=Bool(False),
    )


def proprietaire(type_pret, titulaire, date_signature, anciennete):
    return AL.Proprietaire(
        mensualite_principale=Money("500"),
        charges_mensuelles_pret=Money("0"),
        date_entree_logement=Date(2010, 1, 1),
        type_travaux_logement_d832_15=enum(AL.TypeTravauxLogementD83215, "PasDeTravaux"),
        type_travaux_logement_r842_5=enum(AL.TypeTravauxLogementR8425, "PasDeTravaux"),
        local_habite_premiere_fois_beneficiaire=Bool(False),
        copropriete=Bool(False),
        situation_r822_11_13_17=Bool(False),
        anciennete_logement=anciennete,
        pret=AL.Pret(type_pret=type_pret, date_signature=date_signature, titulaire_pret=titulaire,
                     accord_financement_representant_Etat_outre_mer=enum(
                         AL.AccordFinancementRepresentantEtatOutreMer, "PasdAccord")),
        operations_logement_evolutifs_sociaux_accession_propriete_aidee_Etat=Bool(False),
    )


def fr_params(sample, reps):
    """reps: attribute name -> representative string. Returns the override dict."""
    p = {}
    if "date_courante" in reps:
        p["date_courante"] = parse_date(reps["date_courante"])
    if "residence" in reps:
        p["residence"] = enum(FR.Collectivite, reps["residence"])
    if "nationalite_demandeur" in reps:
        p["nationalite"] = rep_nationalite(reps["nationalite_demandeur"])
    if sample == "FR-APL-2":
        p["situation_familiale"] = rep_situation(reps["situation_familiale"])
        p["n_children"] = rep_n_children(reps["personnes_a_charge"])
        p["autres"] = Integer(int(reps["autres_occupants"]))
        p["surface"] = Integer(int(reps["surface_m_carres"]))
        p["r844_4"] = parse_bool(reps["personnes_agees_handicapees_r844_4"])
    elif sample == "FR-APL-3":
        loc = ex1_location(rep_bailleur(reps["bailleur"]))
        p["mode_occupation"] = enum(AL.ModeOccupation, rep_mode_ctor(reps["mode_occupation"]), loc)
        p["proprietaire"] = rep_parent_ou_autre(reps["part_propriete_famille"])
        p["usufruit"] = rep_parent_ou_autre(reps["part_usufruit_famille"])
        p["loue"] = rep_loue(reps["loue_ou_sous_loue_a_des_tiers"])
        p["decent"] = parse_bool(reps["logement_decent_l89_462"])
        p["residence_principale"] = parse_bool(reps["residence_principale"])
        p["ifi"] = parse_bool(reps["condition_rattache_foyer_fiscal_parent_ifi"])
    elif sample == "FR-APL-4":
        # fixed_inputs: nationality Étrangère {vrai, vrai}
        p["nationalite"] = rep_nationalite(
            "Étrangère {satisfait_conditions_l512_2_code_sécurité_sociale: vrai, "
            "satisfait_art_4_ordonnance_2002_mayotte: vrai}")
        lf = logement_foyer(enum(AL.TypeLogementFoyer, reps["type_logement_foyer"]),
                            parse_bool(reps["conventionne_livre_III_titre_V_chap_III"]),
                            parse_bool(reps["remplit_conditions_r832_21"]),
                            parse_bool(reps["conventionne_selon_regles_drom"]))
        p["mode_occupation"] = enum(AL.ModeOccupation, "RésidentLogementFoyer", lf)
    elif sample == "FR-APL-5":
        pr = proprietaire(enum(AL.TypePret, reps["type_pret"]),
                          enum(AL.TitulairePret, reps["titulaire_pret"]),
                          parse_date(reps["date_signature_pret"]),
                          rep_anciennete(reps["anciennete_logement"]))
        p["mode_occupation"] = enum(AL.ModeOccupation, rep_mode_ctor(reps["mode_occupation"]), pr)
        p["zone"] = enum(AL.ZoneDHabitation, reps["zone"])
        p["residence_principale"] = parse_bool(reps["residence_principale"])
    return p


# ------------------------------------------------------------------- US-121

def rep_periods(s):
    items = re.findall(r"Period \{begin: (\|[^|]+\|), end: (\|[^|]+\|)\}", s)
    assert s.startswith("[") and s.endswith("]") and (items or s == "[]"), s
    return Array([US.Period(begin=parse_date(b), end=parse_date(e)) for b, e in items])


def rep_sale(s):
    if s == "NoOtherSaleWhereSection121aApplied":
        return enum(US.OtherSection121aSale, "NoOtherSaleWhereSection121aApplied")
    m = re.fullmatch(r"MostRecentSaleWhereSection121aApplied content PreviousSaleWhereSection121aApplied "
                     r"\{date_of_sale_or_exchange: (\|[^|]+\|)\}", s)
    return enum(US.OtherSection121aSale, "MostRecentSaleWhereSection121aApplied",
                US.PreviousSaleWhereSection121aApplied(date_of_sale_or_exchange=parse_date(m.group(1))))


def rep_money(s):
    m = re.fullmatch(r"\$([\d,]+(?:\.\d+)?)", s)
    return Money(m.group(1).replace(",", ""))


SALE_DATE = Date(2021, 1, 1)      # fixed_inputs (TESTS:19)
RETURN_DATE = Date(2021, 1, 1)    # fixed_inputs (TESTS:20)
TEST_GAIN = Money("350000")       # fixed_inputs (TESTS:21)


def run_single(ownage, usage, sale, gain=TEST_GAIN):
    out = US.section121_single_person(US.Section121SinglePersonIn(
        date_of_sale_or_exchange_in=SALE_DATE,
        property_ownage_in=ownage,
        property_usage_as_principal_residence_in=usage,
        gain_cap_in=Option(None),
        gain_from_sale_or_exchange_of_property_in=gain,
        section_121_b_3_applies_in=Option(None),
        other_section_121a_sale_in=sale))
    return out


def run_two(return_type, gain):
    return US.section121_two_persons(US.Section121TwoPersonsIn(
        person1_in=Option(None), person2_in=Option(None), gain_cap_in=Option(None),
        return_type_in=return_type, return_date_in=RETURN_DATE,
        date_of_sale_or_exchange_in=SALE_DATE,
        gain_from_sale_or_exchange_of_property_in=gain))


def label_two(out, gain):
    """Map Section121TwoPersons outputs to the US-121-2 labels (spec output.source)."""
    unc = int(out.income_excluded_from_gross_income_uncapped)
    exc = int(out.income_excluded_from_gross_income)
    cap = 50000000 if bool(out.section_121_b_2_A_condition) else int(out.gain_cap_person_1)
    assert exc == min(unc, cap), (unc, exc, cap)
    if unc == 0:
        return "no_exclusion"
    if unc >= cap:
        return {25000000: "limited_to_250000", 50000000: "limited_to_500000"}[cap]
    assert exc == unc == int(gain)
    return "entire_gain"


def personal(reps, prefix):
    return US.PersonalData(
        property_ownage=rep_periods(reps[prefix + "ownership_days_in_5_years"]),
        property_usage_as_principal_residence=rep_periods(reps[prefix + "use_days_in_5_years"]),
        other_section_121a_sale=rep_sale(reps[prefix + "other_section_121a_sale"]))


def us_return_type(label, p1, p2):
    if label == "single":
        return enum(US.ReturnType, "SingleReturn", p1)
    if label == "joint":
        return enum(US.ReturnType, "JointReturn", US.JointReturn(person1=p1, person2=p2))
    return enum(US.ReturnType, "SingleReturnSurvivingSpouse", US.DeadSpouseInfo(
        return__1=p1, date_of_spouse_death=Date(2020, 6, 1), death_spouse_info_at_time_of_death=p2))


# ------------------------------------------------- supplementary in-band probes
# Non-representative values inside each interval label, chosen by this verifier from
# the band definitions of CONVERSION.md (mostly the band's other end). Supplementary:
# they do not enter the pre-specified verdict.

def _p(b, e):
    return f"[Period {{begin: |{b}|, end: |{e}|}}]"


ALT = {
    "FR-APL-1": {"date_courante": {
        "lt_2019-01-01": ["|2018-04-01|", "|2018-12-31|"],
        "2019-01-01_to_2019-08-31": ["|2019-01-01|", "|2019-08-31|"],
        "2019-09-01_to_2020-12-31": ["|2019-09-01|", "|2020-12-31|"],
        "2021-01-01_to_2023-12-31": ["|2021-01-01|", "|2023-12-31|"],
        "2024-01-01_to_2024-10-31": ["|2024-01-01|", "|2024-10-31|"],
        "ge_2024-11-01": ["|2024-11-01|", "|2027-12-31|"]}},
    "FR-APL-2": {"surface_m_carres": {
        "lt_9": ["0"], "9_to_12": ["12"], "13_to_15": ["15"], "16_to_17": ["17"],
        "18_to_21": ["21"], "22_to_24": ["24"], "25_to_26": ["26"], "27_to_30": ["30"],
        "31_to_33": ["33"], "34_to_35": ["35"], "36_to_39": ["39"], "40_to_42": ["42"],
        "43_to_44": ["44"], "45_to_48": ["48"], "49_to_51": ["51"], "ge_52": ["69", "200"]}},
    "FR-APL-3": {
        "part_propriete_famille": {
            "famille_moins_de_10pc": ["DemandeurOuConjointOuParentOuViaPartsSociétés contenu 0,0",
                                      "DemandeurOuConjointOuParentOuViaPartsSociétés contenu 0,0999"],
            "famille_10pc_ou_plus": ["DemandeurOuConjointOuParentOuViaPartsSociétés contenu 1,0"]},
        "part_usufruit_famille": {
            "famille_moins_de_10pc": ["DemandeurOuConjointOuParentOuViaPartsSociétés contenu 0,0999"],
            "famille_10pc_ou_plus": ["DemandeurOuConjointOuParentOuViaPartsSociétés contenu 0,5"]},
        "loue_ou_sous_loue_a_des_tiers": {
            "Oui_moins_de_30_ans_non_conforme_l442_1": [
                "Oui {date_naissance_personne_sous_location: |1990-03-11|, conforme_article_l442_1: faux}"],
            "Oui_moins_de_30_ans_conforme_l442_1": [
                "Oui {date_naissance_personne_sous_location: |1990-03-11|, conforme_article_l442_1: vrai}"],
            "Oui_30_ans_ou_plus_non_conforme_l442_1": [
                "Oui {date_naissance_personne_sous_location: |1990-03-10|, conforme_article_l442_1: faux}"],
            "Oui_30_ans_ou_plus_conforme_l442_1": [
                "Oui {date_naissance_personne_sous_location: |1990-03-10|, conforme_article_l442_1: vrai}"]}},
    "FR-APL-4": {"date_courante": {
        "2019-09-01_to_2020-12-31": ["|2019-09-01|", "|2020-12-31|"],
        "2021-01-01_to_2023-04-04": ["|2021-01-01|", "|2023-04-04|"],
        "2023-04-05_to_2023-12-31": ["|2023-04-05|", "|2023-12-31|"],
        "2024-01-01_to_2024-10-31": ["|2024-01-01|", "|2024-10-31|"],
        "ge_2024-11-01": ["|2024-11-01|", "|2027-12-31|"]}},
    "FR-APL-5": {
        "date_signature_pret": {
            "lt_2017-12-31": ["|1990-01-01|", "|2017-12-30|"],
            "2018-01-01_to_2019-12-31": ["|2018-01-01|", "|2019-12-31|"],
            "ge_2020-01-01": ["|2020-01-01|", "|2025-01-01|"]},
        "date_courante": {
            "2019-09-01_to_2019-09-30": ["|2019-09-01|", "|2019-09-30|"],
            "ge_2019-10-01": ["|2019-10-01|", "|2027-12-31|"]}},
    "US-121-1": {
        "ownership_days_in_5_years": {"lt_730_days": ["[]", _p("2019-01-03", "2021-01-01")],
                                      "ge_730_days": [_p("2019-01-02", "2021-01-01")]},
        "use_days_in_5_years": {"lt_730_days": [_p("2019-01-03", "2021-01-01")],
                                "ge_730_days": [_p("2019-01-02", "2021-01-01")]},
        "other_section_121a_sale": {
            "within_2_years": ["MostRecentSaleWhereSection121aApplied content PreviousSaleWhereSection121aApplied {date_of_sale_or_exchange: |2020-12-31|}"],
            "more_than_2_years": ["MostRecentSaleWhereSection121aApplied content PreviousSaleWhereSection121aApplied {date_of_sale_or_exchange: |2018-12-31|}"]}},
    "US-121-2": {"gain": {"gt_0_lt_250000": ["$0.01", "$249,999.99"],
                          "250000_to_lt_500000": ["$250,000", "$499,999.99"],
                          "ge_500000": ["$500,000", "$10,000,000"]}},
}
for _a in ("person1_", "person2_"):
    ALT["US-121-2"][_a + "ownership_days_in_5_years"] = ALT["US-121-1"]["ownership_days_in_5_years"]
    ALT["US-121-2"][_a + "use_days_in_5_years"] = ALT["US-121-1"]["use_days_in_5_years"]


def band_probe(sample, spec, row, ref):
    """Re-run the row with each alternative in-band value, one attribute at a time.
    ref = (label, detail) at the representatives. Returns (n_probes, list of mismatches)."""
    n, bad = 0, []
    for attr, table in ALT.get(sample, {}).items():
        for val in table.get(row[attr], []):
            n += 1
            got = evaluate(sample, spec, row, {attr: val})
            same = got[0] == ref[0] and (ref[0] != "REJECTED" or got[1] == ref[1])
            if not same:
                bad.append(f"{attr}={val}: {got[0]} {got[1]}".strip())
    return n, bad


# ------------------------------------------------------------------ evaluation

def evaluate(sample, spec, row, override=None):
    """Return (my_label, detail) for one row of labels (dict attr -> label).
    override: attr -> concrete value string used in place of the representative."""
    reps = {}
    for a in spec["attributes"]:
        reps[a["name"]] = a["representative"][row[a["name"]]]
    reps.update(override or {})
    try:
        if sample.startswith("FR-APL"):
            return run_apl(*fr_household(fr_params(sample, reps))), ""
        if sample == "US-121-1":
            out = run_single(rep_periods(reps["ownership_days_in_5_years"]),
                             rep_periods(reps["use_days_in_5_years"]),
                             rep_sale(reps["other_section_121a_sale"]))
            return ("requirements_met" if bool(out.requirements_met) else "requirements_not_met"), ""
        if sample == "US-121-2":
            gain = rep_money(reps["gain"])
            p1, p2 = personal(reps, "person1_"), personal(reps, "person2_")
            out = run_two(us_return_type(row["return_type"], p1, p2), gain)
            return label_two(out, gain), (f"uncapped={out.income_excluded_from_gross_income_uncapped} "
                                          f"excluded={out.income_excluded_from_gross_income}")
    except CatalaError as e:
        return "REJECTED", err_text(e)


def exclusion_hits(spec, row):
    # Predicates come from the repo's own spec.json and are evaluated exactly as
    # PROTOCOL.md section 2 prescribes (empty builtins, row of label strings).
    return [x["id"] for x in spec["exclusions"]
            if eval(x["predicate"], {"__builtins__": {}}, dict(row))]


def check_row(sample, spec, row, probe=False):
    hits = exclusion_hits(spec, row)
    enc, enc_detail = evaluate(sample, spec, row)
    if probe:
        n, bad = band_probe(sample, spec, row, (enc, enc_detail))
        probe_txt = "" if n == 0 else (f"{n}/{n} in-band probes same" if not bad
                                       else f"{n - len(bad)}/{n} same; differ: " + " | ".join(bad))
    if hits:
        mine = "EXCLUDED"
        detail = f"predicate(s) {';'.join(hits)} hold; encoding gives {enc}" + (f" ({enc_detail})" if enc_detail else "")
    else:
        mine = enc
        detail = enc_detail
    if probe:
        return mine, detail, probe_txt
    return mine, detail


def load(sample, family):
    folder = os.path.join(SPECS, family, sample)
    with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    with open(os.path.join(folder, "ground_truth.csv"), newline="", encoding="utf-8") as f:
        gt = list(csv.DictReader(f))
    with open(os.path.join(folder, "official_examples.csv"), newline="", encoding="utf-8") as f:
        off = list(csv.DictReader(f))
    return spec, gt, off


def draw(n):
    if n > DRAW:
        rng = random.Random(SEED)
        return sorted(rng.sample(range(n), DRAW))
    return list(range(n))


# ------------------------------------------------------- official-test validation

def validate_official():
    lines = []
    ok = True
    # 1. Exemple1 written out literally, run directly.
    m, d, dt = exemple1_literal()
    r = run_apl(m, d, dt)
    lines.append(f"tests_eligibilite_apl/Exemple1 (literal transcription, direct call): {r} (asserted eligible)")
    ok &= r == "eligible"
    # 2. the parameterised builder with no override equals the literal transcription
    m2, d2, dt2 = fr_household({})
    same = bool(m == m2) and bool(d == d2) and bool(dt == dt2)
    lines.append(f"fr_household({{}}) structurally equal to Exemple1 literal: {same}")
    ok &= same
    # 3. US Test1-Test6 written out literally.
    p4 = US.Period(begin=Date(2017, 1, 1), end=Date(2021, 1, 1))
    p1 = US.Period(begin=Date(2019, 1, 1), end=Date(2020, 1, 1))
    p2 = US.Period(begin=Date(2015, 1, 1), end=Date(2017, 1, 2))
    none = enum(US.OtherSection121aSale, "NoOtherSaleWhereSection121aApplied")
    for name, use, exp in [("Test1", [p4], True), ("Test2", [p1], False),
                           ("Test3", [p2], False), ("Test4", [p2, p1], True)]:
        got = bool(run_single(Array([p4]), Array(use), none).requirements_met)
        lines.append(f"test_section_121/{name} (direct): requirements_met={got} (asserted {exp})")
        ok &= got == exp
    ok1 = US.PersonalData(property_ownage=Array([p4]), property_usage_as_principal_residence=Array([p4]),
                          other_section_121a_sale=none)
    ok2 = US.PersonalData(property_ownage=Array([p4]), property_usage_as_principal_residence=Array([p2, p1]),
                          other_section_121a_sale=none)
    t5 = run_two(enum(US.ReturnType, "SingleReturn", ok1), TEST_GAIN).income_excluded_from_gross_income
    t6 = run_two(enum(US.ReturnType, "JointReturn", US.JointReturn(person1=ok1, person2=ok2)),
                 TEST_GAIN).income_excluded_from_gross_income
    lines.append(f"test_section_121/Test5 (direct): income_excluded={t5} (asserted $250,000)")
    lines.append(f"test_section_121/Test6 (direct): income_excluded={t6} (asserted $350,000)")
    ok &= int(t5) == 25000000 and int(t6) == 35000000
    # 4. official_examples.csv rows through the label adapter
    for sample, family in SAMPLES:
        spec, _, off = load(sample, family)
        if not off:
            lines.append(f"{sample}: official_examples.csv has no data row")
        for row in off:
            mine, detail = check_row(sample, spec, row)
            agree = mine == row["output"]
            ok &= agree
            lines.append(f"{sample} {row['case_id']} via label adapter: {mine} (official_examples: {row['output']}) "
                         f"{'AGREE' if agree else 'DISAGREE'}")
    return ok, lines


# ------------------------------------------------------------------------ main

def spot(sample, family, indices, out_csv):
    spec, gt, _ = load(sample, family)
    names = [a["name"] for a in spec["attributes"]]
    res, probes = [], []
    for i in indices:
        row = gt[i]
        if out_csv:
            mine, detail, pr = check_row(sample, spec, row, probe=True)
            probes.append(pr)
        else:
            mine, detail = check_row(sample, spec, row)
        res.append((i, row, mine, detail))
    if out_csv:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["index"] + names + ["gt_output", "my_output", "agree", "detail",
                                            "supplementary_band_probe"])
            for (i, row, mine, detail), pr in zip(res, probes):
                w.writerow([i] + [row[n] for n in names] + [row["output"], mine,
                                                             int(mine == row["output"]), detail, pr])
    return spec, gt, res, probes


def main():
    full = "--full" in sys.argv
    ok, lines = validate_official()
    print("== official-test validation:", "PASS" if ok else "FAIL")
    for ln in lines:
        print("  ", ln)
    summary = {"official_validation": ok, "samples": {}}
    for sample, family in SAMPLES:
        spec, gt, _ = load(sample, family)
        idx = draw(len(gt))
        t0 = time.time()
        _, _, res, probes = spot(sample, family, idx, os.path.join(HERE, f"{sample}.csv"))
        agree = sum(1 for _, row, mine, _ in res if mine == row["output"])
        dis = [(i, dict(row), mine, detail) for i, row, mine, detail in res if mine != row["output"]]
        errs = {}
        for _, row, mine, detail in res:
            if row["output"] == "REJECTED":
                errs[detail] = errs.get(detail, 0) + 1
        excl = {}
        for _, row, mine, detail in res:
            if row["output"] == "EXCLUDED":
                excl[detail] = excl.get(detail, 0) + 1
        s = {"N": len(gt), "indices": idx, "checked": len(res), "agree": agree,
             "disagreements": dis, "rejected_errors": errs, "excluded_details": excl,
             "seconds": round(time.time() - t0, 1)}
        pn = sum(int(p.split("/")[1].split()[0]) for p in probes if p)
        pbad = [(i, p) for (i, _, _, _), p in zip(res, probes) if p and "differ" in p]
        s["band_probes"] = {"rows_probed": sum(1 for p in probes if p), "probes": pn, "rows_with_difference": pbad}
        print(f"== {sample}: N={len(gt)} checked={len(res)} agree={agree} ({s['seconds']} s)")
        print(f"   supplementary in-band probes: {pn} probes on {s['band_probes']['rows_probed']} rows; "
              f"{len(pbad)} rows with a difference")
        for i, p in pbad:
            print(f"   PROBE DIFF row {i}: {p}")
        print("   indices:", idx)
        for d in dis:
            print("   DISAGREE", d)
        for k, v in errs.items():
            print(f"   REJECTED x{v}: {k}")
        for k, v in excl.items():
            print(f"   EXCLUDED x{v}: {k}")
        if full:
            t0 = time.time()
            _, _, allres, _ = spot(sample, family, range(len(gt)), None)
            fa = sum(1 for _, row, mine, _ in allres if mine == row["output"])
            fd = [(i, dict(row), mine, detail) for i, row, mine, detail in allres if mine != row["output"]]
            s["full"] = {"checked": len(allres), "agree": fa, "disagreements": fd[:50],
                         "n_disagreements": len(fd), "seconds": round(time.time() - t0, 1)}
            print(f"   FULL TABLE: checked={len(allres)} agree={fa} ({s['full']['seconds']} s)")
            for d in fd[:20]:
                print("   FULL DISAGREE", d)
        summary["samples"][sample] = s
    with open(os.path.join(HERE, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
