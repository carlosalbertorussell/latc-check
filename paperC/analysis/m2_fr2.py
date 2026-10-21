"""M2 for FR-APL and US-121 (both conversions).

For every table: the official tests of the rule, which of them each conversion mapped,
the reason for each unmapped test, and the declared values used by the mapped tests
against the values used when every official test of the rule is placed on the table's
attributes regardless of the slice (table's own labels and cut points).

Run from the repository root:  python3.12 -I paperC/analysis/m2_fr2.py
Writes paperC/analysis/out/m2_fr2.json and prints a Markdown summary.
"""

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import tests_fr2 as T  # noqa: E402

U = common.UNKNOWN
D = dt.date.fromisoformat

C1 = "paperc-data-fr2"
C1FIX = "paperc-data-fr2-fix"  # corrected US-121-2 (README-FR2.md "Correction of 2026-10-20")
C2 = "paperc-code2-fr2"

TABLES = [
    # (rule, conversion, table id, branch, folder)
    ("FR-APL", 1, "FR-APL-1", C1, "paperC/specs/FR-APL/FR-APL-1"),
    ("FR-APL", 1, "FR-APL-2", C1, "paperC/specs/FR-APL/FR-APL-2"),
    ("FR-APL", 1, "FR-APL-3", C1, "paperC/specs/FR-APL/FR-APL-3"),
    ("FR-APL", 1, "FR-APL-4", C1, "paperC/specs/FR-APL/FR-APL-4"),
    ("FR-APL", 1, "FR-APL-5", C1, "paperC/specs/FR-APL/FR-APL-5"),
    ("FR-APL", 2, "FR-APL-1", C2, "paperC/specs2/FR-APL-1"),
    ("FR-APL", 2, "FR-APL-2", C2, "paperC/specs2/FR-APL-2"),
    ("FR-APL", 2, "FR-APL-3", C2, "paperC/specs2/FR-APL-3"),
    ("FR-APL", 2, "FR-APL-4", C2, "paperC/specs2/FR-APL-4"),
    ("FR-APL", 2, "FR-APL-5", C2, "paperC/specs2/FR-APL-5"),
    ("US-121", 1, "US-121-1", C1, "paperC/specs/US-121/US-121-1"),
    ("US-121", 1, "US-121-2", C1FIX, "paperC/specs/US-121/US-121-2"),
    ("US-121", 2, "US-121-1", C2, "paperC/specs2/US-121-1"),
    ("US-121", 2, "US-121-2", C2, "paperC/specs2/US-121-2"),
]


def band(date, cuts):
    """cuts: list of (first day, label) in increasing order; first entry may be (None, label)."""
    lab = None
    for start, label in cuts:
        if start is None or date >= D(start):
            lab = label
    return lab


# ----------------------------------------------------------------- FR-APL placements
# Cut points: each table's spec.json (labels) and CONVERSION.md / CONVERSION_2.md
# (date bands: C1 FR-APL-1 CONVERSION.md:40-47, FR-APL-4 :33, FR-APL-5 :44;
#  C2 CONVERSION_2.md:74-84 of FR-APL-1/2/3).

C1_APL1_DATES = [(None, "lt_2019-01-01"), ("2019-01-01", "2019-01-01_to_2019-08-31"),
                 ("2019-09-01", "2019-09-01_to_2020-12-31"), ("2021-01-01", "2021-01-01_to_2023-12-31"),
                 ("2024-01-01", "2024-01-01_to_2024-10-31"), ("2024-11-01", "ge_2024-11-01")]
C1_APL4_DATES = [("2019-09-01", "2019-09-01_to_2020-12-31"), ("2021-01-01", "2021-01-01_to_2023-04-04"),
                 ("2023-04-05", "2023-04-05_to_2023-12-31"), ("2024-01-01", "2024-01-01_to_2024-10-31"),
                 ("2024-11-01", "ge_2024-11-01")]
C1_APL5_DATES = [("2019-09-01", "2019-09-01_to_2019-09-30"), ("2019-10-01", "ge_2019-10-01")]
C2_DATES = [("2019-09-01", "2019-09-01_to_2019-09-30"), ("2019-10-01", "2019-10-01_to_2020-12-31"),
            ("2021-01-01", "2021-01-01_to_2021-04-30"), ("2021-05-01", "2021-05-01_to_2023-04-04"),
            ("2023-04-05", "2023-04-05_to_2023-08-31"), ("2023-09-01", "2023-09-01_to_2023-12-31"),
            ("2024-01-01", "2024-01-01_to_2024-10-31"), ("2024-11-01", "from_2024-11-01")]

RES = {"Métropole": "Metropole", "LaRéunion": "LaReunion", "Guadeloupe": "Guadeloupe",
       "Guyane": "Guyane", "Martinique": "Martinique", "Mayotte": "Mayotte",
       "SaintBarthélemy": "SaintBarthelemy", "SaintMartin": "SaintMartin",
       "SaintPierreEtMiquelon": "SaintPierreEtMiquelon"}
SIT = {"Célibataire": "Celibataire", "Mariés": "Maries", "Pacsés": "Pacses", "Concubins": "Concubins",
       "CélibataireSéparéDeFait": "CelibataireSepareDeFait",
       "ConcubinageDontSéparéDeFait": "ConcubinageDontSepareDeFait"}

# Surface bands: lower bounds (C1 FR-APL-2 CONVERSION.md:52-56; C2 FR-APL-5 CONVERSION_2.md:87-93).
C1_SURF = [(0, "lt_9"), (9, "9_to_12"), (13, "13_to_15"), (16, "16_to_17"), (18, "18_to_21"),
           (22, "22_to_24"), (25, "25_to_26"), (27, "27_to_30"), (31, "31_to_33"), (34, "34_to_35"),
           (36, "36_to_39"), (40, "40_to_42"), (43, "43_to_44"), (45, "45_to_48"), (49, "49_to_51"),
           (52, "ge_52")]
C2_SURF = [(0, "below_9"), (9, "9_to_12"), (13, "13_to_15"), (16, "16_to_17"), (18, "18_to_21"),
           (22, "22_to_24"), (25, "25_to_26"), (27, "27_to_30"), (31, "31_to_33"), (34, "34_to_35"),
           (36, "36_to_39"), (40, "40_to_42"), (43, "43_to_44"), (45, "45_to_48"), (49, "49_to_51"),
           (52, "52_to_53"), (54, "54_to_57"), (58, "58_to_60"), (61, "61_to_62"), (63, "63_to_66"),
           (67, "67_to_69"), (70, "70_to_71"), (72, "from_72")]


def surf(n, cuts):
    return [lab for lo, lab in cuts if n >= lo][-1]


def c1_bailleur(t):
    b, conv = t["bailleur"][0], t["bailleur_conventionne"][0]
    if b == "BailleurPrivé":
        return "BailleurPrive"
    suffix = "conventionne" if conv == "vrai" else "non_conventionne"
    return {"BailleurSocial": "BailleurSocial_", "BailleurPrivéAvecConventionnementSocial":
            "BailleurPriveAvecConventionnementSocial_"}[b] + suffix


def c2_bailleur(t):
    b, conv = t["bailleur"][0], t["bailleur_conventionne"][0]
    if b == "BailleurPrivé":
        return "prive"
    pre = {"BailleurSocial": "social_", "BailleurPrivéAvecConventionnementSocial":
           "prive_conventionnement_social_"}[b]
    return pre + ("conventionne" if conv == "vrai" else "non_conventionne")


def nat(t, conv):
    n = t["nationalite_demandeur"][0]
    assert n == "Française"  # all three tests (lines 105, 190, 258); no Étrangère label needed
    return "francaise" if conv == 1 else "Francaise"


def b1(v):  # Catala boolean -> C1 label
    return {"vrai": "vrai", "faux": "faux"}[v]


def b2(v):  # Catala boolean -> C2 label
    return {"vrai": "oui", "faux": "non"}[v]


def place_apl(conv, tid, t):
    """Labels of test t on the table's attributes; UNKNOWN where the test has no counterpart."""
    d = D(t["date_courante"][0])
    res = RES[t["residence"][0]]
    tenancy = t["mode_occupation"][0]  # 'Locataire' in all three tests
    if conv == 1:
        if tid == "FR-APL-1":
            return {"date_courante": band(d, C1_APL1_DATES), "residence": res,
                    "nationalite_demandeur": nat(t, 1)}
        if tid == "FR-APL-2":
            return {"residence": res, "nationalite_demandeur": nat(t, 1),
                    "situation_familiale": SIT[t["situation_familiale"][0]],
                    "personnes_a_charge": str(t["personnes_a_charge"][0]),
                    "autres_occupants": str(t["autres_occupants"][0]),
                    "surface_m_carres": surf(t["surface"][0], C1_SURF),
                    "personnes_agees_handicapees_r844_4": b1(t["r844_4"][0])}
        if tid == "FR-APL-3":
            assert t["loue_ou_sous_loue"][0] == "Non"
            return {"mode_occupation": tenancy, "bailleur": c1_bailleur(t),
                    "part_propriete_famille": t["proprietaire"][0],
                    "part_usufruit_famille": t["usufruit"][0],
                    "loue_ou_sous_loue_a_des_tiers": "Non",
                    "logement_decent_l89_462": b1(t["logement_decent"][0]),
                    "residence_principale": b1(t["residence_principale"][0]),
                    "condition_rattache_foyer_fiscal_parent_ifi": b1(t["ifi"][0])}
        if tid == "FR-APL-4":  # logement-foyer fields do not exist in a tenancy
            return {"residence": res, "date_courante": band(d, C1_APL4_DATES),
                    "type_logement_foyer": U, "conventionne_livre_III_titre_V_chap_III": U,
                    "remplit_conditions_r832_21": U, "conventionne_selon_regles_drom": U}
        if tid == "FR-APL-5":  # loan fields do not exist in a tenancy; mode is outside the labels
            return {"mode_occupation": U, "type_pret": U, "titulaire_pret": U,
                    "date_signature_pret": U, "anciennete_logement": U, "zone": t["zone"][0],
                    "date_courante": band(d, C1_APL5_DATES),
                    "residence_principale": b1(t["residence_principale"][0])}
    else:
        if tid == "FR-APL-1":
            return {"date_courante": band(d, C2_DATES), "residence": res,
                    "mode_occupation": tenancy, "bailleur": c2_bailleur(t)}
        if tid == "FR-APL-2":
            return {"date_courante": band(d, C2_DATES), "residence": res,
                    "type_logement_foyer": U, "conventionne_livre_III_titre_V_chap_III": U,
                    "conventionne_selon_regles_drom": U, "remplit_conditions_r832_21": U}
        if tid == "FR-APL-3":
            return {"date_courante": band(d, C2_DATES), "residence": res, "mode_occupation": U,
                    "type_pret": U, "titulaire_pret": U, "date_signature_pret": U,
                    "anciennete_logement": U, "zone": t["zone"][0]}
        if tid == "FR-APL-4":
            assert t["loue_ou_sous_loue"][0] == "Non"
            return {"residence": res if res in ("Metropole", "LaReunion", "Mayotte") else U,
                    "nationalite_demandeur": nat(t, 2),
                    "residence_principale": b2(t["residence_principale"][0]),
                    "rattache_foyer_fiscal_parent_ifi": b2(t["ifi"][0]),
                    "logement_decent": b2(t["logement_decent"][0]),
                    "loue_ou_sous_loue_a_des_tiers": "non", "age_personne_sous_location": "sans_objet",
                    "sous_locataire_conforme_l442_1": "sans_objet",
                    "proprietaire_famille": t["proprietaire"][0].lower(),
                    "usufruit_famille": t["usufruit"][0].lower(), "mode_occupation": tenancy}
        if tid == "FR-APL-5":
            return {"residence": res if res in ("Metropole", "LaReunion", "Mayotte") else U,
                    "nationalite_demandeur": nat(t, 2),
                    "situation_familiale": SIT[t["situation_familiale"][0]],
                    "nombre_autres_occupants_logement": str(t["autres_occupants"][0]),
                    "nombre_personnes_a_charge": str(t["personnes_a_charge"][0]),
                    "surface_m_carres": surf(t["surface"][0], C2_SURF),
                    "personnes_agees_handicapees_foyer_r844_4": b2(t["r844_4"][0])}
    raise KeyError(tid)


# ----------------------------------------------------------------- US-121 placements

def c1_days(n):  # US-121-1 CONVERSION.md:32-35
    return "ge_730_days" if n >= 730 else "lt_730_days"


def c2_days(n):  # code2 US-121-2 CONVERSION_2.md:52-56
    return "730d_or_more" if n >= 730 else "under_730d"


def c2_shape(periods, sale):
    """Second coder's US-121-1 list labels (CONVERSION_2.md:41-61)."""
    if not periods:
        return "none"
    n = T.aggregate_days(periods, sale)
    if len(periods) == 2:
        return "two_total_730d_or_more" if n >= 730 else "two_total_under_730d"
    if len(periods) > 2:
        return U
    b, e = periods[0]
    if sale <= T.add_years(b, 5):
        pos = "one_inside_window"
    elif sale >= T.add_years(e, 5):
        return "one_ended_before_5y_mark"
    else:
        pos = "one_across_5y_mark"
    return f"{pos}_{'over_730d' if n > 730 else '730d' if n == 730 else 'under_730d'}"


def other(o, conv):
    assert o == "NoOtherSaleWhereSection121aApplied"  # every test (Data, lines 41-61, 78-123)
    return "none"


def c1_gain(g):  # US-121-2 CONVERSION.md:50
    return "gt_0_lt_250000" if g < 250000 else "250000_to_lt_500000" if g < 500000 else "ge_500000"


def c2_gain(g):  # code2 US-121-2 CONVERSION_2.md:60-64
    return "under_250000" if g < 250000 else "250000_to_500000" if g < 500000 else "over_500000"


def place_us(conv, tid, t, data):
    """A list of placements (one per person for single-person tables)."""
    sale, gain = data["sale"][0], data["gain"][0]
    ps = t["persons"]
    out = []
    if tid == "US-121-1":
        # One person per placement: Test6 (joint) gives two persons (judgement J-US1).
        for p in ps:
            if conv == 1:
                out.append({"ownership_days_in_5_years": c1_days(T.aggregate_days(p["own"], sale)),
                            "use_days_in_5_years": c1_days(T.aggregate_days(p["use"], sale)),
                            "other_section_121a_sale": other(p["other"], 1)})
            else:
                out.append({"property_ownage": c2_shape(p["own"], sale),
                            "property_usage_as_principal_residence": c2_shape(p["use"], sale),
                            "other_section_121a_sale": other(p["other"], 2)})
        return out
    # US-121-2: one placement per test.
    rt = t["return_type"]
    p1 = ps[0]
    p2 = ps[1] if len(ps) > 1 else None
    if conv == 1:
        r = {"return_type": rt if rt else U,
             "person1_ownership_days_in_5_years": c1_days(T.aggregate_days(p1["own"], sale)),
             "person1_use_days_in_5_years": c1_days(T.aggregate_days(p1["use"], sale)),
             "person1_other_section_121a_sale": other(p1["other"], 1),
             "gain": c1_gain(gain)}
        src = p2 if p2 else (p1 if rt == "single" else None)  # C1: single return => p2 = p1
        for k, f in (("ownership_days_in_5_years", "own"), ("use_days_in_5_years", "use")):
            r[f"person2_{k}"] = c1_days(T.aggregate_days(src[f], sale)) if src else U
        r["person2_other_section_121a_sale"] = other(src["other"], 1) if src else U
    else:
        r = {"return_type": {"single": "single_return", "joint": "joint_return", None: U}[rt],
             "person1_property_ownage": c2_days(T.aggregate_days(p1["own"], sale)),
             "person1_property_usage_as_principal_residence": c2_days(T.aggregate_days(p1["use"], sale)),
             "person1_other_section_121a_sale": other(p1["other"], 2),
             "gain_from_sale_or_exchange_of_property": c2_gain(gain)}
        for k, f in (("property_ownage", "own"), ("property_usage_as_principal_residence", "use")):
            r[f"person2_{k}"] = (c2_days(T.aggregate_days(p2[f], sale)) if p2
                                 else "not_applicable" if rt == "single" else U)
        r["person2_other_section_121a_sale"] = (other(p2["other"], 2) if p2
                                                else "not_applicable" if rt == "single" else U)
    return [r]


# ----------------------------------------------------------------- mapping and reasons

def case_key(conv, case_id):
    """Test name of an official_examples.csv case id."""
    return case_id.split(":")[-1].split("/")[-1]


def apl_reason(conv, tid, t):
    """Reason category and detail for a test the table did not map."""
    scope = t["scope"][0]
    if scope != "ÉligibilitéAidePersonnaliséeLogement":
        return ("other output or scope",
                f"asserts {scope}.éligibilité ({T.APL_FILE}:{t['asserts'][1]}), "
                "the allocation de logement scope")
    return ("other: housing tenure fixed by the table",
            f"Exemple1 is a tenancy (Locataire, {T.APL_FILE}:{t['mode_occupation'][1]}); "
            f"the table fixes a {'logement-foyer' if tid in ('FR-APL-4',) and conv == 1 or tid == 'FR-APL-2' and conv == 2 else 'home-ownership'} occupation mode")


def us_reason(conv, tid, t):
    want = "Section121SinglePerson" if tid == "US-121-1" else "Section121TwoPersons"
    assert t["scope"] != want
    out = "requirements_met" if t["scope"] == "Section121SinglePerson" else "income_excluded_from_gross_income"
    return ("other output or scope", f"asserts {t['scope']}.{out} ({T.US_FILE}:{t['assert_line']})")


# Lines of each conversion that state why the unmapped tests were left out.
REASON_SOURCES = {
    (1, "FR-APL"): [(C1, "paperC/specs/README-FR2.md", "| | Exemple2 |"),
                    (C1, "paperC/specs/FR-APL/FR-APL-4/CONVERSION.md", "Exemple1's household is a `Locataire`"),
                    (C1, "paperC/specs/FR-APL/FR-APL-5/CONVERSION.md", "Exemple1's household is a `Locataire`")],
    (2, "FR-APL"): [(C2, "paperC/specs2/README-FR2-CODE2.md", "| FR-APL-2 | 0 |"),
                    (C2, "paperC/specs2/README-FR2-CODE2.md", "| FR-APL-3 | 0 |"),
                    (C2, "paperC/specs2/FR-APL-1/CONVERSION_2.md", "cannot map onto an APL table")],
    (1, "US-121"): [(C1, "paperC/specs/US-121/US-121-1/CONVERSION.md", "| `test_section_121/Test5` | no |"),
                    (C1FIX, "paperC/specs/US-121/US-121-2/CONVERSION.md", "`test_section_121/Test1`–`Test4` | no |")],
    (2, "US-121"): [(C2, "paperC/specs2/US-121-1/CONVERSION_2.md", "unmappable here"),
                    (C2, "paperC/specs2/US-121-2/CONVERSION_2.md", "unmappable here")],
}


def main():
    apl = T.apl_tests()
    us_data, us = T.us_tests()
    results = []
    for rule, conv, tid, br, folder in TABLES:
        spec = common.load_spec(br, folder)
        mapped = common.load_csv(br, f"{folder}/official_examples.csv")
        valid = common.valid_rows(br, folder, spec)
        names = common.attr_names(spec)
        mapped_rows = [{n: r[n] for n in names} for r in mapped]
        mapped_ids = [case_key(conv, r["case_id"]) for r in mapped]
        suite = apl if rule == "FR-APL" else us
        suite_rows, unmapped, placements = [], [], []
        for t in suite:
            if rule == "FR-APL":
                pl = [place_apl(conv, tid, t)]
            else:
                pl = place_us(conv, tid, t, us_data)
            for p in pl:
                assert set(p) == set(names), (tid, set(p) ^ set(names))
            if t["name"] in mapped_ids:
                # A mapped test is placed as the conversion mapped it (its official_examples row);
                # check that the placement by cut points gives the same labels.
                row = mapped_rows[mapped_ids.index(t["name"])]
                agree = all(p[n] is U or p[n] == row[n] for p in pl for n in names)
                placements.append({"test": t["name"], "mapped": True, "labels_by_cut_points": pl,
                                   "agrees_with_official_examples_row": agree})
                suite_rows.append(row)
            else:
                cat, detail = (apl_reason if rule == "FR-APL" else us_reason)(conv, tid, t)
                unmapped.append({"test": t["name"], "category": cat, "detail": detail})
                placements.append({"test": t["name"], "mapped": False, "labels_by_cut_points": pl})
                suite_rows.extend(pl)
        u = common.usage(spec, mapped_rows, suite_rows, valid)
        results.append({
            "rule": rule, "conversion": conv, "table": tid, "branch": br, "folder": folder,
            "branch_commit": common.branch_commit(br),
            "suite_tests": len(suite), "mapped_tests": len(mapped_ids), "mapped_ids": mapped_ids,
            "unmapped": unmapped, "placements": placements, "usage": u,
            "H1_mapped": {"unused_gt_0": u["unused_mapped_total"] > 0,
                          "missed_valid_gt_0": u["missed_valid_mapped"] > 0},
            "H1_suite": {"unused_gt_0": u["unused_suite_total"] > 0,
                         "missed_valid_gt_0": u["missed_valid_suite"] > 0},
        })
    # Variant for US-121-2 (judgement J-US2): read each Section121SinglePerson test as a single return.
    variant = []
    for r in results:
        if r["table"] != "US-121-2":
            continue
        br, folder = r["branch"], r["folder"]
        spec = common.load_spec(br, folder)
        names = common.attr_names(spec)
        mapped_rows = [{n: x[n] for n in names} for x in common.load_csv(br, f"{folder}/official_examples.csv")]
        rows = list(mapped_rows)
        for t in us:
            if t["scope"] == "Section121SinglePerson":
                rows.extend(place_us(r["conversion"], "US-121-2", dict(t, return_type="single"), us_data))
        u = common.usage(spec, mapped_rows, rows, common.valid_rows(br, folder, spec))
        variant.append({"conversion": r["conversion"], "table": "US-121-2",
                        "unused_suite_total": u["unused_suite_total"],
                        "missed_valid_suite": u["missed_valid_suite"],
                        "unused_suite": {n: a["unused_suite"] for n, a in u["attributes"].items()}})
    sources = {f"{c}|{r}": [common.cite(b, p, n) for b, p, n in v] for (c, r), v in REASON_SOURCES.items()}
    common.write_json("m2_fr2.json", {"tables": results, "reason_sources": sources,
                                       "variant_us121_2_single_return": variant})

    print("| Rule | Conv. | Table | Suite tests | Mapped | Declared | Unused (mapped) | Unused (suite) "
          "| Unknown placements | missed_valid (mapped) | missed_valid (suite) | Valid |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        u = r["usage"]
        unk = sum(a["unknown_tests"] for a in u["attributes"].values())
        print(f"| {r['rule']} | {r['conversion']} | {r['table']} | {r['suite_tests']} | {r['mapped_tests']} | "
              f"{u['declared_total']} | {u['unused_mapped_total']} | {u['unused_suite_total']} | {unk} | "
              f"{u['missed_valid_mapped']} | {u['missed_valid_suite']} | {u['valid_total']} |")
    print()
    for v in variant:
        print(f"Variant (single-person tests read as single returns), conversion {v['conversion']} US-121-2: "
              f"unused {v['unused_suite_total']}, missed_valid {v['missed_valid_suite']}")
    for r in results:
        changed = {n: sorted(set(a["unused_mapped"]) - set(a["unused_suite"]))
                   for n, a in r["usage"]["attributes"].items()
                   if set(a["unused_mapped"]) != set(a["unused_suite"])}
        unk = {n: a["unknown_tests"] for n, a in r["usage"]["attributes"].items() if a["unknown_tests"]}
        print(f"{r['conversion']}:{r['table']} newly used by the whole suite: {changed}; unknown: {unk}")
        for p in r["placements"]:
            if p["mapped"] and not p["agrees_with_official_examples_row"]:
                print(f"   NOTE {p['test']}: cut-point placement differs from the official_examples row")


if __name__ == "__main__":
    main()
