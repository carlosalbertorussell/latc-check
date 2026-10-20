#!/usr/bin/env python3
"""FR-AF oracle: amount regime of InterfaceAllocationsFamiliales.i_montant_versé at 2020-05-01.

The same file serves FR-AF-1, FR-AF-2 and FR-AF-3; the table layout (attributes,
fixed inputs and their labels, number of child slots) comes from spec.json.

  python oracle.py --enumerate        write ground_truth.csv
  python oracle.py --check-official   re-run the official tests and their mapping; write official_examples.csv
  python oracle.py --self-check       check bands and representatives against the encoding
  python oracle.py --self-check --sample N   band robustness on every N-th row only

evaluate(row) takes a row of labels (strings) and returns the output label,
EXCLUDED or REJECTED.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frcatala as F  # noqa: E402

SPEC = F.load_spec()
NAMES = [a["name"] for a in SPEC["attributes"]]
DC = SPEC["fixed_inputs"]["date_courante"]["value"]
FIXED = {k: v["label"] for k, v in SPEC["fixed_inputs"].items() if "label" in v}
NSLOTS = SPEC["fixed_inputs"]["child_slots"]["value"]


def evaluate_with_reason(row, overrides=None):
    return F.af_evaluate_with_reason(SPEC, FIXED, NSLOTS, row, overrides, DC)


def evaluate(row, overrides=None):
    return evaluate_with_reason(row, overrides)[0]


def check_official():
    direct = F.run_official_directly()
    n_ok = sum(1 for r in direct if r[2])
    print(f"Direct run of the official test scopes through the generated Python: {n_ok}/{len(direct)} scopes pass")
    for fname, scope, ok, k in direct:
        print(f"  {'PASS' if ok else 'FAIL'}  {fname}  {scope}  ({k} assertion(s))")
    print("  (tests_ouverture_droits.catala_fr Test1 asserts per-child droit_ouvert; it maps onto FR-PF, not onto this table)")

    examples, n_map_ok, unmapped = [], 0, []
    print(f"\nMapping of tests_allocations_familiales.catala_fr onto {SPEC['id']}:")
    for case in F.af_official_cases():
        name = case[0]
        mapped, reason = F.af_map_case(case, SPEC, FIXED, NSLOTS)
        if mapped is None:
            unmapped.append((name, reason))
            continue
        row, expected_label = mapped
        got = evaluate(row)
        ok = got == expected_label
        n_map_ok += ok
        examples.append((f"allocations_familiales.{name}", row, expected_label))
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: expected amount {case[6]} -> {expected_label}; "
              f"row {[row[n] for n in NAMES]} -> oracle {got}")
    print(f"\nMapped official examples: {n_map_ok}/{len(examples)} agree with the oracle")
    print("Unmapped:")
    for name, reason in unmapped:
        print(f"  {name}: {reason}")
    if n_ok == len(direct) and n_map_ok == len(examples):
        F.write_official_examples(NAMES, examples)
        return 0
    return 1


def self_check(sample_every):
    fails = F.check_age_bands(F.AGE_BANDS_AF, DC)
    print(f"age bands: {'ok' if not fails else fails}")
    for res in ("Metropole", "Mayotte"):
        got = F.bisect_plafond_remuneration(res, DC)
        exp = F.plafond_remuneration(res)
        print(f"earnings ceiling {res}: encoding {got}, spec {exp}: {'ok' if got == exp else 'MISMATCH'}")
        fails += [] if got == exp else [res]
    stats, ex = F.robustness(SPEC, evaluate, F.af_alternatives, sample_every, F.af_birth_order(FIXED, NSLOTS))
    (k_n, k_c), (r_n, r_c) = stats["kept"], stats["reversed"]
    print(f"band robustness (every {sample_every}-th row):")
    print(f"  alternatives keeping the children's birth order: {k_n} evaluations, {k_c} label changes")
    print(f"  alternatives reversing the birth order of two same-band children: {r_n} evaluations, {r_c} label changes")
    for e in ex:
        print("   ", e)
    return 0 if not fails and not k_c else 1


if __name__ == "__main__":
    if "--enumerate" in sys.argv:
        F.enumerate_table(os.path.abspath(__file__))
    elif "--check-official" in sys.argv:
        sys.exit(check_official())
    elif "--self-check" in sys.argv:
        m = re.search(r"--sample[= ](\d+)", " ".join(sys.argv))
        sys.exit(self_check(int(m.group(1)) if m else 1))
    elif "--sha256" in sys.argv:
        F.write_sha256sums()
    else:
        print(__doc__)
