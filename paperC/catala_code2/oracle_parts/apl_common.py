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
