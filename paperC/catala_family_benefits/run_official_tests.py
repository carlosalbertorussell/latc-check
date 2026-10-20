#!/usr/bin/env python3
"""Re-run the official Catala tests of allocations_familiales through the generated Python.

Source of the tests (CatalaLang/catala-examples, commit 2694b17):
  allocations_familiales/tests/tests_ouverture_droits.catala_fr      (scope Test1)
  allocations_familiales/tests/tests_allocations_familiales.catala_fr (scopes Test1..Test14)

Each scope below is a line-by-line translation of the Catala test scope: the same
inputs, and the same assertions. Only the standard library and the bundled runtime
(runtime/catala, Catala 1.3.0) are used.

Run:  python3 run_official_tests.py        (exit status 0 when every assertion holds)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# The generated modules do "from catala_runtime import *" and the runtime does
# "import dates", so the runtime directory itself goes on sys.path.
sys.path.insert(0, os.path.join(HERE, "runtime", "catala"))
sys.path.insert(0, HERE)

# The Catala 1.3.0 Python runtime uses PEP 695 generics (class Array[T: Value])
# and typing.override, so it needs Python 3.12 or later.
if sys.version_info < (3, 12):
    sys.exit(f"Python 3.12 or later is required by the Catala 1.3.0 runtime (found {sys.version.split()[0]})")

from catala_runtime import Array, Bool, Date, Integer, Money, Unit, catala_set_lang, Lang  # noqa: E402
from generated import Allocations_familiales as AF  # noqa: E402
from generated import France  # noqa: E402

catala_set_lang(Lang.Fr)

# ---------------------------------------------------------------- helpers

def collectivite(name):
    return France.Collectivite(getattr(France.Collectivite.Code, name), Unit())

def prise_en_charge(name):
    return AF.PriseEnCharge(getattr(AF.PriseEnCharge.Code, name), Unit())

def obligation_scolaire(name):
    return AF.SituationObligationScolaire(getattr(AF.SituationObligationScolaire.Code, name), Unit())

def money(euros):
    """Money from a string in euros, e.g. "351.54"."""
    return Money(euros)

def date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return Date(y, m, d)

def enfant_entree(ident, naissance, remuneration, prise, deja_ouvert=True, apl=False):
    return AF.EnfantEntree(
        d_identifiant=Integer(ident),
        d_remuneration_mensuelle=money(remuneration),
        d_date_de_naissance=date(naissance),
        d_prise_en_charge=prise_en_charge(prise),
        d_a_deja_ouvert_droit_aux_allocations_familiales=Bool(deja_ouvert),
        d_beneficie_titre_personnel_aide_personnelle_logement=Bool(apl),
    )

def enfant(ident, obligation, naissance, remuneration, prise, deja_ouvert=True, apl=False):
    return AF.Enfant(
        identifiant=Integer(ident),
        obligation_scolaire=obligation_scolaire(obligation),
        remuneration_mensuelle=money(remuneration),
        date_de_naissance=date(naissance),
        prise_en_charge=prise_en_charge(prise),
        a_deja_ouvert_droit_aux_allocations_familiales=Bool(deja_ouvert),
        beneficie_titre_personnel_aide_personnelle_logement=Bool(apl),
    )

def interface(enfants, ressources, date_courante, residence,
              est_parent=False, titre_I=False, avant_2012=False):
    """Call scope InterfaceAllocationsFamiliales. A condition the test sets with
    `règle f.x rempli` is True; a condition the test leaves alone is False."""
    out = AF.interface_allocations_familiales(AF.InterfaceAllocationsFamilialesIn(
        i_date_courante_in=date(date_courante),
        i_enfants_in=Array(enfants),
        i_ressources_menage_in=money(ressources),
        i_residence_in=collectivite(residence),
        i_personne_charge_effective_permanente_est_parent_in=Bool(est_parent),
        i_personne_charge_effective_permanente_remplit_titre_I_in=Bool(titre_I),
        i_avait_enfant_a_charge_avant_1er_janvier_2012_in=Bool(avant_2012),
    ))
    return out.i_montant_verse

# ------------------------------------------- tests_ouverture_droits.catala_fr

def ouverture_droits_test1():
    # champ d'application Données
    enfant1 = enfant(1, "Pendant", "2007-01-01", "0.00", "EffectiveEtPermanente")
    enfant2 = enfant(2, "Apres", "2003-01-01", "1000.00", "EffectiveEtPermanente")
    enfant3 = enfant(3, "Apres", "2003-01-01", "400.00", "EffectiveEtPermanente")
    enfant4 = enfant(4, "Apres", "1999-01-01", "0.00", "EffectiveEtPermanente")
    # champ d'application Test1: f champ d'application AF.PrestationsFamiliales
    f = AF.prestations_familiales(AF.PrestationsFamilialesIn(
        date_courante_in=date("2020-05-01"),
        residence_in=collectivite("Metropole"),
    ))
    return [
        ("f.droit_ouvert de données.enfant1", bool(f.droit_ouvert(enfant1)) is True),
        ("non (f.droit_ouvert de données.enfant2)", bool(f.droit_ouvert(enfant2)) is False),
        ("f.droit_ouvert de données.enfant3", bool(f.droit_ouvert(enfant3)) is True),
        ("non (f.droit_ouvert de données.enfant4)", bool(f.droit_ouvert(enfant4)) is False),
    ]

# --------------------------------------- tests_allocations_familiales.catala_fr

# champ d'application Données
D1 = enfant_entree(1, "2007-01-01", "0.00", "EffectiveEtPermanente")
D2 = enfant_entree(2, "2009-01-01", "0.00", "EffectiveEtPermanente")
D3 = enfant_entree(3, "2003-01-01", "400.00", "GardeAlterneePartageAllocations")
D4 = enfant_entree(4, "2001-01-01", "1100.00", "EffectiveEtPermanente")
D5 = enfant_entree(5, "2000-01-01", "0.00", "EffectiveEtPermanente")

# (name, enfants, ressources_ménage, date_courante, résidence, extra conditions, expected montant_versé)
AF_TESTS = [
    ("Test1", lambda: [D1, D2, D3, D4], "30000", "2020-05-01", "Metropole", {}, "351.54"),
    ("Test2", lambda: [D1, D2, D5], "30000", "2020-05-01", "Metropole", {}, "216.46"),
    ("Test3", lambda: [D1], "63540", "2020-05-01", "Guyane", {}, "24.37"),
    ("Test4", lambda: [D1, D3], "67250", "2020-05-01", "Metropole", {}, "99.46"),
    ("Test5", lambda: [D1], "30000", "2020-05-01", "Metropole", {}, "0.00"),
    ("Test6", lambda: [
        enfant_entree(0, "2009-11-10", "439", "EffectiveEtPermanente"),
        enfant_entree(1, "2020-09-25", "1949", "EffectiveEtPermanente"),
    ], "78830", "2020-05-01", "Guadeloupe", {}, "66.30"),
    ("Test7", lambda: [D1, D2, D3, D4], "30000", "2021-02-01", "Metropole", {}, "417.84"),
    ("Test8", lambda: [
        enfant_entree(0, "2004-01-01", "0", "EffectiveEtPermanente"),
        enfant_entree(1, "2005-01-01", "0", "EffectiveEtPermanente"),
    ], "69945", "2021-01-01", "Metropole", {}, "197.90"),
    ("Test9", lambda: [
        enfant_entree(0, "2001-07-27", "1258", "ServicesSociauxAllocationVerseeAuxServicesSociaux"),
        enfant_entree(1, "2008-04-27", "1766", "ServicesSociauxAllocationVerseeAuxServicesSociaux"),
    ], "75786", "2020-05-01", "Guadeloupe", {}, "0"),
    ("Test10", lambda: [
        enfant_entree(0, "2003-02-22", "0", "EffectiveEtPermanente"),
        enfant_entree(1, "2013-09-30", "300", "GardeAlterneePartageAllocations"),
    ], "30000", "2020-04-20", "Metropole", {}, "99.46"),
    ("Test11", lambda: [
        enfant_entree(0, "2003-02-22", "0", "EffectiveEtPermanente"),
        enfant_entree(1, "2013-09-30", "300", "EffectiveEtPermanente"),
        enfant_entree(2, "2007-04-16", "0", "EffectiveEtPermanente"),
    ], "30000", "2021-12-31", "Metropole", {}, "435.55"),
    ("Test12", lambda: [
        enfant_entree(0, "2003-02-22", "0", "EffectiveEtPermanente"),
        enfant_entree(1, "2013-09-30", "300", "EffectiveEtPermanente"),
        enfant_entree(2, "2007-04-16", "0", "EffectiveEtPermanente"),
        enfant_entree(3, "2012-02-02", "0", "EffectiveEtPermanente"),
    ], "20000", "2019-08-26", "Mayotte", {"avant_2012": True}, "315.84"),
    ("Test13", lambda: [
        enfant_entree(0, "2008-02-22", "0", "EffectiveEtPermanente"),
    ], "65000", "2019-08-26", "Mayotte", {}, "34.99"),
    ("Test14", lambda: [
        enfant_entree(0, "2004-12-22", "435", "EffectiveEtPermanente"),
        enfant_entree(1, "2001-12-05", "1682", "GardeAlterneeAllocataireUnique"),
    ], "64033", "2022-05-01", "Guadeloupe", {}, "48.77"),
]

def make_af_test(enfants, ressources, date_courante, residence, extra, expected):
    def run():
        # Every test scope sets `règle f.i_personne_charge_effective_permanente_est_parent rempli`.
        got = interface(enfants(), ressources, date_courante, residence, est_parent=True, **extra)
        ok = bool(got == money(expected))
        return [(f"f.i_montant_versé = {expected} € (got {got})", ok)]
    return run

# ---------------------------------------------------------------- driver

def main():
    tests = [("tests_ouverture_droits.catala_fr", "Test1", ouverture_droits_test1)]
    for name, enfants, ressources, dc, res, extra, expected in AF_TESTS:
        tests.append(("tests_allocations_familiales.catala_fr", name,
                      make_af_test(enfants, ressources, dc, res, extra, expected)))

    print(f"Python {sys.version.split()[0]}")
    n_pass = n_fail = n_assert = 0
    for fname, scope, fn in tests:
        try:
            results = fn()
            error = None
        except Exception as exc:  # a Catala runtime error counts as a failure
            results, error = [], f"{type(exc).__name__}: {exc}"
        failed = [label for label, ok in results if not ok]
        n_assert += len(results)
        if error is None and not failed:
            n_pass += 1
            print(f"PASS  {fname}  {scope}  ({len(results)} assertion(s))")
        else:
            n_fail += 1
            print(f"FAIL  {fname}  {scope}")
            if error:
                print(f"      error: {error}")
            for label in failed:
                print(f"      assertion failed: {label}")
    print(f"\n{n_pass} passed, {n_fail} failed, {len(tests)} test scopes, {n_assert} assertions checked")
    return 0 if n_fail == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
