#!/usr/bin/env python3
"""FR-PF oracle: PrestationsFamiliales.droit_ouvert per child at 2020-05-01.

  python oracle.py --enumerate        write ground_truth.csv
  python oracle.py --check-official   re-run the official tests and their mapping; write official_examples.csv
  python oracle.py --self-check       check the bands and the representatives against the encoding

evaluate(row) takes a row of labels (strings) and returns the output label,
EXCLUDED or REJECTED.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frcatala as F  # noqa: E402

SPEC = F.load_spec()
NAMES = [a["name"] for a in SPEC["attributes"]]
AGE = F.AGE_BANDS_PF
DC = SPEC["fixed_inputs"]["date_courante"]["value"]


def remuneration_value(label, residence):
    if label == "eq_plafond":
        return F.plafond_remuneration(residence)
    return {"lt_plafond": "400.00", "gt_plafond": "1000.00"}[label]


def concrete(row, overrides=None):
    c = {
        "residence": row["residence"],
        "obligation_scolaire": row["obligation_scolaire"],
        "prise_en_charge": row["prise_en_charge"],
        "naissance": AGE[row["age"]][1],
        "remuneration": remuneration_value(row["remuneration"], row["residence"]),
        "apl": row["apl"] == "true",
    }
    for k, v in (overrides or {}).items():
        c["naissance" if k == "age" else k] = v
    return c


def evaluate_with_reason(row, overrides=None):
    x = F.excluded(SPEC, row)
    if x:
        return "EXCLUDED", x
    c = concrete(row, overrides)
    try:
        with F.quiet():
            pf = F.prestations_familiales(DC, c["residence"])
            e = F.enfant(1, c["obligation_scolaire"], c["naissance"], c["remuneration"],
                         c["prise_en_charge"], True, c["apl"])
            ok = bool(pf.droit_ouvert(e))
    except F.CatalaError as exc:
        return "REJECTED", f"{type(exc).__name__} at {exc.source_positions[0] if exc.source_positions else '?'}"
    return ("entitled" if ok else "not_entitled"), None


def evaluate(row, overrides=None):
    return evaluate_with_reason(row, overrides)[0]


# ------------------------------------------------------------------ official tests

def map_pf_child(child, dc_iso, residence):
    """Map a child of tests_ouverture_droits Test1 onto a row (labels)."""
    return {
        "residence": residence,
        "obligation_scolaire": child.obligation_scolaire.code.name,
        "prise_en_charge": child.prise_en_charge.code.name,
        "age": F.age_band(AGE, iso(child.date_de_naissance), dc_iso),
        "remuneration": rem_band(child.remuneration_mensuelle, residence),
        "apl": "true" if bool(child.beneficie_titre_personnel_aide_personnelle_logement) else "false",
    }


def iso(d):
    return f"{d.value.year:04d}-{d.value.month:02d}-{d.value.day:02d}"


def rem_band(m, residence):
    p = F.Money(F.plafond_remuneration(residence))
    return "lt_plafond" if m < p else ("eq_plafond" if m == p else "gt_plafond")


def check_official():
    direct = F.run_official_directly()
    n_ok = sum(1 for r in direct if r[2])
    print(f"Direct run of the official test scopes through the generated Python: {n_ok}/{len(direct)} scopes pass")
    for fname, scope, ok, k in direct:
        print(f"  {'PASS' if ok else 'FAIL'}  {fname}  {scope}  ({k} assertion(s))")

    rot = F.official_tests()
    # tests_ouverture_droits.catala_fr Test1: date 2020-05-01, Métropole, four children.
    children = [
        ("ouverture_droits.Test1.enfant1", rot.enfant(1, "Pendant", "2007-01-01", "0.00", "EffectiveEtPermanente"), True),
        ("ouverture_droits.Test1.enfant2", rot.enfant(2, "Apres", "2003-01-01", "1000.00", "EffectiveEtPermanente"), False),
        ("ouverture_droits.Test1.enfant3", rot.enfant(3, "Apres", "2003-01-01", "400.00", "EffectiveEtPermanente"), True),
        ("ouverture_droits.Test1.enfant4", rot.enfant(4, "Apres", "1999-01-01", "0.00", "EffectiveEtPermanente"), False),
    ]
    pf = F.prestations_familiales("2020-05-01", "Metropole")
    examples, n_map_ok = [], 0
    print("\nMapping of the per-child assertions onto the table (tests_ouverture_droits.catala_fr Test1):")
    for case_id, child, expected in children:
        direct_ok = bool(pf.droit_ouvert(child)) is expected
        row = map_pf_child(child, "2020-05-01", "Metropole")
        exp_label = "entitled" if expected else "not_entitled"
        got = evaluate(row)
        ok = direct_ok and got == exp_label
        n_map_ok += ok
        examples.append((case_id, row, exp_label))
        print(f"  {'PASS' if ok else 'FAIL'}  {case_id}: direct={'ok' if direct_ok else 'MISMATCH'} "
              f"row={[row[n] for n in NAMES]} oracle={got} expected={exp_label}")
    print(f"\nMapped official examples: {n_map_ok}/{len(children)} agree with the oracle")
    print("Unmapped: the 14 scopes of tests_allocations_familiales.catala_fr assert household amounts "
          "(i_montant_versé), not droit_ouvert of a child (see CONVERSION.md C9).")
    if n_ok == len(direct) and n_map_ok == len(children):
        F.write_official_examples(NAMES, examples)
        return 0
    return 1


# ------------------------------------------------------------------ self-check

def alternatives(attr, label, row):
    if attr == "age":
        _, _, (first, last) = AGE[label]
        return [d for d in (first, last) if d] + F.UNBOUNDED_PROBES.get(label, [])
    if attr == "remuneration":
        p = F.Money(F.plafond_remuneration(row["residence"]))
        one = F.Money(1)  # 1 cent in the runtime's integer representation
        return {"lt_plafond": ["0.00", F.money_str(F.Money(int(p) - 1))],
                "eq_plafond": [],
                "gt_plafond": [F.money_str(F.Money(int(p) + int(one))), "5000.00"]}[label]
    return []


def self_check():
    fails = F.check_age_bands(AGE, DC)
    print(f"age bands: {'ok' if not fails else fails}")
    for res in ("Metropole", "Mayotte"):
        got = F.bisect_plafond_remuneration(res, DC)
        exp = F.plafond_remuneration(res)
        print(f"earnings ceiling {res}: encoding {got}, spec {exp}: {'ok' if got == exp else 'MISMATCH'}")
        fails += [] if got == exp else [res]
    stats, ex = F.robustness(SPEC, evaluate, alternatives)
    checked, changed = stats["kept"]
    print(f"band robustness: {checked} alternative evaluations, {changed} label changes")
    for e in ex:
        print("   ", e)
    return 0 if not fails and not changed else 1


if __name__ == "__main__":
    if "--enumerate" in sys.argv:
        F.enumerate_table(os.path.abspath(__file__))
    elif "--check-official" in sys.argv:
        sys.exit(check_official())
    elif "--self-check" in sys.argv:
        sys.exit(self_check())
    elif "--sha256" in sys.argv:
        F.write_sha256sums()
    else:
        print(__doc__)
