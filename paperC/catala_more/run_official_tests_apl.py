#!/usr/bin/env python3
"""Re-run the official Catala tests of tests_eligibilite_apl.catala_fr through the generated Python.

Source of the tests (CatalaLang/catala-examples, commit 2694b17):
  aides_logement/tests/tests_eligibilite_apl.catala_fr
    Exemple1  scope AL.ÉligibilitéAidePersonnaliséeLogement, assertion éligible
    Exemple2  scope AL.ÉligibilitéAllocationLogement, assertion éligible = AllocationLogementFamiliale
    Exemple3  scope AL.ÉligibilitéAllocationLogement, assertion éligible = AllocationLogementFamiliale

Each function below is a field-by-field translation of the Catala test scope (same
inputs, same assertion). Only the standard library and the bundled runtime are used.

Run:  python3 run_official_tests_apl.py     (exit status 0 when every assertion holds)
"""

import sys

import apl_inputs as I
from apl_inputs import AL


def exemple1_inputs():
    """Inputs of Exemple1 (tests_eligibilite_apl.catala_fr lines 13-107)."""
    m = I.menage(
        residence="Metropole",
        prestations=["AllocationSoutienEnfantHandicape", "ComplementFamilial", "AllocationsFamiliales"],
        situation=I.situation_familiale("Maries", "2010-11-26"),
        personnes_a_charge=[
            I.enfant(0, "2001-01-01", "Apres", etudes=True),
            I.enfant(1, "2009-01-01", "Pendant", etudes=False),
            I.enfant(2, "2012-01-01", "Pendant", etudes=False),
        ],
        logement_=I.logement(
            I.enum(AL.ModeOccupation, "Locataire", I.location(I.bailleur_social(True), loyer="750")),
            surface=80, zone="Zone1"),
        autres_occupants=1,
    )
    return "2020-03-10", m, I.demandeur("1970-05-02")


def exemple1():
    dc, m, d = exemple1_inputs()
    out = I.eligibilite_apl(dc, m, d)
    return [("éligible (got %s)" % out.eligibilite, bool(out.eligibilite) is True)]


def exemple2():
    """tests_eligibilite_apl.catala_fr lines 114-193."""
    m = I.menage(
        residence="Metropole",
        prestations=["AllocationsFamiliales"],
        situation=I.situation_familiale("Concubins"),
        personnes_a_charge=[
            I.enfant(0, "2016-01-01", "Pendant"),
            I.enfant(1, "2015-01-01", "Pendant"),
        ],
        logement_=I.logement(
            I.enum(AL.ModeOccupation, "Locataire", I.location(I.bailleur_social(True), loyer="450")),
            surface=60, zone="Zone2"),
        autres_occupants=0,
    )
    out = I.eligibilite_al("2022-05-01", m, I.demandeur("1992-01-01"), beneficie_apl=False)
    want = I.enum(AL.TypeEligibiliteAllocationLogement, "AllocationLogementFamiliale")
    return [("éligible = AllocationLogementFamiliale (got %s)" % out.eligibilite,
             bool(out.eligibilite == want))]


def exemple3():
    """tests_eligibilite_apl.catala_fr lines 200-261."""
    m = I.menage(
        residence="LaReunion",
        prestations=["AllocationsFamiliales"],
        situation=I.situation_familiale("Concubins"),
        personnes_a_charge=[I.enfant(0, "2016-01-01", "Pendant")],
        logement_=I.logement(
            I.enum(AL.ModeOccupation, "Locataire", I.location(I.bailleur_prive(), loyer="375")),
            surface=60, zone="Zone2"),
        autres_occupants=0,
    )
    out = I.eligibilite_al("2023-04-01", m, I.demandeur("1992-01-01"), beneficie_apl=False)
    want = I.enum(AL.TypeEligibiliteAllocationLogement, "AllocationLogementFamiliale")
    return [("éligible = AllocationLogementFamiliale (got %s)" % out.eligibilite,
             bool(out.eligibilite == want))]


TESTS = [
    ("tests_eligibilite_apl.catala_fr", "Exemple1", exemple1),
    ("tests_eligibilite_apl.catala_fr", "Exemple2", exemple2),
    ("tests_eligibilite_apl.catala_fr", "Exemple3", exemple3),
]


def main():
    print(f"Python {sys.version.split()[0]}")
    n_pass = n_fail = n_assert = 0
    for fname, scope, fn in TESTS:
        try:
            results, error = fn(), None
        except Exception as exc:  # a Catala runtime error counts as a failure
            results, error = [], f"{type(exc).__name__}: {exc}"
        failed = [label for label, ok in results if not ok]
        n_assert += len(results)
        if error is None and not failed:
            n_pass += 1
            print(f"PASS  {fname}  {scope}  ({len(results)} assertion(s)): {results[0][0]}")
        else:
            n_fail += 1
            print(f"FAIL  {fname}  {scope}")
            if error:
                print(f"      error: {error}")
            for label in failed:
                print(f"      assertion failed: {label}")
    print(f"\n{n_pass} passed, {n_fail} failed, {len(TESTS)} test scopes, {n_assert} assertions checked")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
