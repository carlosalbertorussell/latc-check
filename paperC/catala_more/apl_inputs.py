"""Builders for the inputs of the Catala housing-benefit eligibility scopes.

The generated module `generated/Aides_logement.py` (Catala 1.3.0, catala-examples
commit 2694b17) takes nested Catala structures as input. The functions below build
them from plain Python values, field by field, with the field names of
aides_logement/prologue.catala_fr. Nothing here changes the rules: every value is
passed to the generated code unchanged.

Used by run_official_tests_apl.py and by the oracles in paperC/specs/FR-APL/.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# The generated modules do "from catala_runtime import *" and the runtime does
# "import dates", so the runtime directory itself goes on sys.path.
sys.path.insert(0, os.path.join(HERE, "runtime", "catala"))
sys.path.insert(0, HERE)

if sys.version_info < (3, 12):
    sys.exit(f"Python 3.12 or later is required by the Catala 1.3.0 runtime (found {sys.version.split()[0]})")

from catala_runtime import (  # noqa: E402
    Array, Bool, CatalaError, Date, Decimal, Integer, Lang, Money, Unit, catala_set_lang,
)
from generated import Aides_logement as AL  # noqa: E402
from generated import France  # noqa: E402
from generated import Prestations_familiales as PF  # noqa: E402

catala_set_lang(Lang.Fr)


def date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return Date(y, m, d)


def enum(cls, code, content=None):
    """Enumeration value `cls.code`, with `content` for constructors that carry data."""
    return cls(getattr(cls.Code, code), Unit() if content is None else content)


def collectivite(code):
    return enum(France.Collectivite, code)


def nationalite(code, l512_2=False, art_4_mayotte=False):
    """Française, or Étrangère with the two conditions of ConditionsÉtrangers."""
    if code == "Francaise":
        return enum(AL.Nationalite, "Francaise")
    return enum(AL.Nationalite, "Etrangere", AL.ConditionsEtrangers(
        satisfait_conditions_l512_2_code_securite_sociale=Bool(l512_2),
        satisfait_art_4_ordonnance_2002_mayotte=Bool(art_4_mayotte),
    ))


def enfant(identifiant, date_de_naissance, obligation_scolaire, etudes=False,
           remuneration="0", deja_ouvert_af=True, nationalite_enfant=None):
    return enum(AL.PersonneACharge, "EnfantACharge", AL.EnfantACharge(
        identifiant=Integer(identifiant),
        nationalite=nationalite_enfant or nationalite("Francaise"),
        a_deja_ouvert_droit_aux_allocations_familiales=Bool(deja_ouvert_af),
        date_de_naissance=date(date_de_naissance),
        remuneration_mensuelle=Money(remuneration),
        obligation_scolaire=enum(PF.SituationObligationScolaire, obligation_scolaire),
        situation_garde_alternee=enum(AL.SituationGardeAlternee, "PasDeGardeAlternee"),
        etudes_apprentissage_stage_formation_pro_impossibilite_travail=Bool(etudes),
    ))


def bailleur_social(conventionne, rls="0"):
    return enum(AL.TypeBailleur, "BailleurSocial", AL.ConventionBailleurSocial(
        conventionne_livre_III_titre_V_chap_III=Bool(conventionne),
        reduction_loyer_solidarite_percue=Money(rls),
    ))


def bailleur_prive_conventionnement(conventionne):
    return enum(AL.TypeBailleur, "BailleurPriveAvecConventionnementSocial", AL.ConventionANHA(
        conventionne_livre_III_titre_II_chap_I_sec_3=Bool(conventionne),
    ))


def bailleur_prive():
    return enum(AL.TypeBailleur, "BailleurPrive")


def location(bailleur, loyer="750"):
    """A `Location` record; only `bailleur` is read by the eligibility scopes."""
    return AL.Location(
        bailleur=bailleur,
        loyer_principal=Money(loyer),
        beneficiaire_aide_adulte_ou_enfant_handicapes=Bool(False),
        logement_est_chambre=Bool(False),
        colocation=Bool(False),
        agees_ou_handicap_adultes_hebergees_onereux_particuliers=Bool(False),
        logement_meuble_d842_2=Bool(False),
        changement_logement_d842_4=enum(AL.ChangementLogementD8424, "PasDeChangement"),
    )


def logement_foyer(type_logement, conventionne_livre_III, remplit_r832_21, conventionne_drom,
                   date_conventionnement="2000-01-01", redevance="400"):
    """A `LogementFoyer` record; fields not read for eligibility are fixed."""
    return AL.LogementFoyer(
        type_logement=enum(AL.TypeLogementFoyer, type_logement),
        logement_foyer_jeunes_travailleurs=Bool(False),
        remplit_conditions_r832_21=Bool(remplit_r832_21),
        conventionne_livre_III_titre_V_chap_III=Bool(conventionne_livre_III),
        conventionne_selon_regles_drom=Bool(conventionne_drom),
        date_conventionnement=date(date_conventionnement),
        construit_application_loi_1957_12_III=Bool(False),
        redevance=Money(redevance),
        categorie_equivalence_loyer_d842_16=enum(AL.CategorieEquivalenceLoyerAllocationLogementFoyer, "AutresPersonnes"),
        beneficiaire_aide_adulte_ou_enfant_handicapes=Bool(False),
        logement_meuble_d842_2=Bool(False),
        logement_est_chambre=Bool(False),
        colocation=Bool(False),
    )


def proprietaire(type_pret, titulaire_pret, date_signature, anciennete,
                 date_entree_logement="2010-01-01"):
    """A `Propriétaire` record. `anciennete` is "Neuf", "AncienOui" or "AncienNon"
    (NeufOuAncien.Ancien carries AmélioréParOccupant)."""
    if anciennete == "Neuf":
        anc = enum(AL.NeufOuAncien, "Neuf")
    else:
        anc = enum(AL.NeufOuAncien, "Ancien",
                   enum(AL.AmelioreParOccupant, "Oui" if anciennete == "AncienOui" else "Non"))
    return AL.Proprietaire(
        mensualite_principale=Money("500"),
        charges_mensuelles_pret=Money("0"),
        date_entree_logement=date(date_entree_logement),
        type_travaux_logement_d832_15=enum(AL.TypeTravauxLogementD83215, "PasDeTravaux"),
        type_travaux_logement_r842_5=enum(AL.TypeTravauxLogementR8425, "PasDeTravaux"),
        local_habite_premiere_fois_beneficiaire=Bool(False),
        copropriete=Bool(False),
        situation_r822_11_13_17=Bool(False),
        anciennete_logement=anc,
        pret=AL.Pret(
            type_pret=enum(AL.TypePret, type_pret),
            date_signature=date(date_signature),
            titulaire_pret=enum(AL.TitulairePret, titulaire_pret),
            accord_financement_representant_Etat_outre_mer=enum(
                AL.AccordFinancementRepresentantEtatOutreMer, "PasdAccord"),
        ),
        operations_logement_evolutifs_sociaux_accession_propriete_aidee_Etat=Bool(False),
    )


def parent_ou_autre(parts=None):
    """ParentOuAutre: `None` gives Autre; a decimal string gives
    DemandeurOuConjointOuParentOuViaPartsSociétés with that share."""
    if parts is None:
        return enum(AL.ParentOuAutre, "Autre")
    return enum(AL.ParentOuAutre, "DemandeurOuConjointOuParentOuViaPartsSocietes", Decimal(parts))


def loue_tiers(personne_naissance=None, conforme_l442_1=False):
    if personne_naissance is None:
        return enum(AL.LoueOuSousLoueADesTiers, "Non")
    return enum(AL.LoueOuSousLoueADesTiers, "Oui", AL.PersonneSousLocation(
        date_naissance_personne_sous_location=date(personne_naissance),
        conforme_article_l442_1=Bool(conforme_l442_1),
    ))


def logement(mode_occupation, surface, zone="Zone1", residence_principale=True,
             proprietaire_parts=None, usufruit_parts=None, loue=None, decent=True):
    return AL.Logement(
        residence_principale=Bool(residence_principale),
        mode_occupation=mode_occupation,
        proprietaire=parent_ou_autre(proprietaire_parts),
        loue_ou_sous_loue_a_des_tiers=loue if loue is not None else loue_tiers(),
        usufruit=parent_ou_autre(usufruit_parts),
        logement_decent_l89_462=Bool(decent),
        surface_m_carres=Integer(surface),
        zone=enum(AL.ZoneDHabitation, zone),
    )


def situation_familiale(code, date_mariage="2010-11-26"):
    if code == "Maries":
        return enum(AL.SituationFamiliale, "Maries", date(date_mariage))
    return enum(AL.SituationFamiliale, code)


def menage(residence, logement_, personnes_a_charge, situation, prestations=(),
           autres_occupants=0, ifi=False, enfant_a_naitre=False, r844_4=False):
    return AL.Menage(
        prestations_recues=Array([enum(AL.PrestationRecue, p) for p in prestations]),
        logement=logement_,
        personnes_a_charge=Array(list(personnes_a_charge)),
        nombre_autres_occupants_logement=Integer(autres_occupants),
        situation_familiale=situation,
        condition_rattache_foyer_fiscal_parent_ifi=Bool(ifi),
        enfant_a_naitre_apres_quatrieme_mois_grossesse=Bool(enfant_a_naitre),
        personnes_agees_handicapees_foyer_r844_4=Bool(r844_4),
        residence=collectivite(residence),
    )


def demandeur(date_naissance="1970-05-02", nationalite_=None):
    return AL.Demandeur(
        date_naissance=date(date_naissance),
        nationalite=nationalite_ or nationalite("Francaise"),
        personne_hebergee_centre_soin_l_L162_22_3_securite_sociale=Bool(False),
        est_non_salarie_agricole_l781_8_l_781_46_code_rural=Bool(False),
        magistrat_fonctionnaire_centre_interets_materiels_familiaux_hors_mayotte=Bool(False),
    )


def eligibilite_apl(date_courante, menage_, demandeur_):
    """Scope ÉligibilitéAidePersonnaliséeLogement; returns its output record."""
    return AL.eligibilite_aide_personnalisee_logement(AL.EligibiliteAidePersonnaliseeLogementIn(
        menage_in=menage_, demandeur_in=demandeur_, date_courante_in=date(date_courante)))


def eligibilite_al(date_courante, menage_, demandeur_, beneficie_apl):
    """Scope ÉligibilitéAllocationLogement; returns its output record."""
    return AL.eligibilite_allocation_logement(AL.EligibiliteAllocationLogementIn(
        date_courante_in=date(date_courante), menage_in=menage_, demandeur_in=demandeur_,
        beneficie_aide_personnalisee_logement_in=Bool(beneficie_apl)))
