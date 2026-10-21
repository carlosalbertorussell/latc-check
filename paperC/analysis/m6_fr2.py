"""M6 row-level agreement for FR-APL and US-121 between the two conversions.

Each comparison pairs a first-coder table A with a second-coder table B. Rows are made
comparable by (1) restricting each side to the values that equal the other side's fixed
inputs, and (2) mapping each B condition onto the A condition whose labels contain B's
representative values (B refines A on every shared attribute used here; the mapping is
written out per pair, with the sources of the label definitions). Outputs are compared
after the output-label mapping; EXCLUDED and REJECTED are compared as such.

Run from the repository root:  python3.12 -I paperC/analysis/m6_fr2.py
Writes paperC/analysis/out/m6_fr2.json and prints a Markdown summary.
"""

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

C1 = "paperc-data-fr2"
C1FIX = "paperc-data-fr2-fix"
C2 = "paperc-code2-fr2"
A_ = lambda t: (C1FIX if t == "US-121-2" else C1, {"US-121-1": "paperC/specs/US-121/US-121-1",
                "US-121-2": "paperC/specs/US-121/US-121-2"}.get(t, f"paperC/specs/FR-APL/{t}"))
B_ = lambda t: (C2, f"paperC/specs2/{t}")

APL_OUT = {"eligible": "eligible", "ineligible": "not_eligible"}
US1_OUT = {"met": "requirements_met", "not_met": "requirements_not_met"}
US2_OUT = {"zero": "no_exclusion", "full_gain": "entire_gain",
           "capped_at_250000": "limited_to_250000", "capped_at_500000": "limited_to_500000"}

C2_DATE_TO_C1_APL1 = {
    "2019-09-01_to_2019-09-30": "2019-09-01_to_2020-12-31",
    "2019-10-01_to_2020-12-31": "2019-09-01_to_2020-12-31",
    "2021-01-01_to_2021-04-30": "2021-01-01_to_2023-12-31",
    "2021-05-01_to_2023-04-04": "2021-01-01_to_2023-12-31",
    "2023-04-05_to_2023-08-31": "2021-01-01_to_2023-12-31",
    "2023-09-01_to_2023-12-31": "2021-01-01_to_2023-12-31",
    "2024-01-01_to_2024-10-31": "2024-01-01_to_2024-10-31",
    "from_2024-11-01": "ge_2024-11-01"}
C2_DATE_TO_C1_APL4 = {
    "2019-09-01_to_2019-09-30": "2019-09-01_to_2020-12-31",
    "2019-10-01_to_2020-12-31": "2019-09-01_to_2020-12-31",
    "2021-01-01_to_2021-04-30": "2021-01-01_to_2023-04-04",
    "2021-05-01_to_2023-04-04": "2021-01-01_to_2023-04-04",
    "2023-04-05_to_2023-08-31": "2023-04-05_to_2023-12-31",
    "2023-09-01_to_2023-12-31": "2023-04-05_to_2023-12-31",
    "2024-01-01_to_2024-10-31": "2024-01-01_to_2024-10-31",
    "from_2024-11-01": "ge_2024-11-01"}
C2_DATE_TO_C1_APL5 = {k: ("2019-09-01_to_2019-09-30" if k == "2019-09-01_to_2019-09-30" else "ge_2019-10-01")
                      for k in C2_DATE_TO_C1_APL1}
NAT = {"Francaise": "francaise", "Etrangere_T_T": "etrangere_l512_2_et_art_4",
       "Etrangere_T_F": "etrangere_l512_2_seulement", "Etrangere_F_T": "etrangere_art_4_seulement",
       "Etrangere_F_F": "etrangere_aucune"}
YN = {"oui": "vrai", "non": "faux"}
BAIL2_TO_C1 = {"social_conventionne": "BailleurSocial_conventionne",
               "social_non_conventionne": "BailleurSocial_non_conventionne",
               "prive_conventionnement_social_conventionne": "BailleurPriveAvecConventionnementSocial_conventionne",
               "prive_conventionnement_social_non_conventionne": "BailleurPriveAvecConventionnementSocial_non_conventionne",
               "prive": "BailleurPrive"}
SHARE = {"autre": "Autre", "parts_below_10pct": "famille_moins_de_10pc",
         "parts_10pct": "famille_10pc_ou_plus", "parts_above_10pct": "famille_10pc_ou_plus"}


def sublet(b):
    if b["loue_ou_sous_loue_a_des_tiers"] == "non":
        return "Non"
    age = "moins_de_30_ans" if b["age_personne_sous_location"] == "under_30" else "30_ans_ou_plus"
    conf = "conforme_l442_1" if b["sous_locataire_conforme_l442_1"] == "oui" else "non_conforme_l442_1"
    return f"Oui_{age}_{conf}"


def sublet_malformed(b):
    """Rows the second coder excludes by `sublet_details_iff_sublet` (FR-APL-4 CONVERSION_2.md:107-109):
    the three sublet attributes encode one input, and these combinations describe no input."""
    no = b["loue_ou_sous_loue_a_des_tiers"] == "non"
    return no != (b["age_personne_sous_location"] == "sans_objet") or \
        no != (b["sous_locataire_conforme_l442_1"] == "sans_objet")


def c2_days_to_c1(label):
    """Second coder's period-list shape (US-121-1 CONVERSION_2.md:45-56) -> first coder's band."""
    ge = label in ("one_inside_window_over_730d", "one_inside_window_730d", "one_across_5y_mark_over_730d",
                   "one_across_5y_mark_730d", "two_total_730d_or_more", "730d_or_more")
    return "ge_730_days" if ge else "lt_730_days"


OTHER = {"none": "none", "under_2_years_before": "within_2_years",
         "exactly_2_years_before": "within_2_years", "over_2_years_before": "more_than_2_years"}
GAIN = {"under_250000": "gt_0_lt_250000", "250000_to_500000": "250000_to_lt_500000",
        "over_500000": "ge_500000"}


def us2_map(b):
    """B row of code2 US-121-2 -> A condition of the corrected first-coder US-121-2, or None."""
    p2 = [b["person2_property_ownage"], b["person2_property_usage_as_principal_residence"],
          b["person2_other_section_121a_sale"]]
    rt = b["return_type"]
    a = {"return_type": {"single_return": "single", "joint_return": "joint",
                         "surviving_spouse_return": "surviving_spouse"}[rt],
         "person1_ownership_days_in_5_years": c2_days_to_c1(b["person1_property_ownage"]),
         "person1_use_days_in_5_years": c2_days_to_c1(b["person1_property_usage_as_principal_residence"]),
         "person1_other_section_121a_sale": OTHER[b["person1_other_section_121a_sale"]],
         "gain": GAIN[b["gain_from_sale_or_exchange_of_property"]]}
    if rt == "joint_return":
        if "not_applicable" in p2:
            return None
        src = (c2_days_to_c1(p2[0]), c2_days_to_c1(p2[1]), OTHER[p2[2]])
    else:
        if p2 != ["not_applicable"] * 3:
            return None  # partly filled person 2 on a one-person return: no counterpart
        if rt == "single_return":   # first coder: person 2 = the same taxpayer (CONVERSION.md:63-65)
            src = (a["person1_ownership_days_in_5_years"], a["person1_use_days_in_5_years"],
                   a["person1_other_section_121a_sale"])
        else:  # code2 fixes the deceased spouse's record to person_ok_1 (CONVERSION_2.md:73-77)
            src = ("ge_730_days", "ge_730_days", "none")
    a["person2_ownership_days_in_5_years"], a["person2_use_days_in_5_years"], \
        a["person2_other_section_121a_sale"] = src
    return a


PAIRS = [
    {"id": "APL-tenancy-date-territory", "A": "FR-APL-1", "B": "FR-APL-1",
     "A_fix": {"nationalite_demandeur": "francaise"},
     "B_fix": {"mode_occupation": "Locataire", "bailleur": "social_conventionne"},
     "map": lambda b: {"date_courante": C2_DATE_TO_C1_APL1[b["date_courante"]],
                       "residence": b["residence"], "nationalite_demandeur": "francaise"},
     "out": APL_OUT,
     "why": "A fixes Locataire with a conventioned social landlord (FR-APL-1 CONVERSION.md:84-90); "
            "B fixes the applicant Française (CONVERSION_2.md:42-51). B's eight date bands refine A's "
            "bands from 2019-09-01 on (A CONVERSION.md:40-47, B CONVERSION_2.md:74-84)."},
    {"id": "APL-nationality", "A": "FR-APL-1", "B": "FR-APL-4",
     "A_fix": {"date_courante": "2019-09-01_to_2020-12-31", "residence": ("Metropole", "LaReunion", "Mayotte")},
     "B_fix": {"residence_principale": "oui", "rattache_foyer_fiscal_parent_ifi": "non", "logement_decent": "oui",
               "loue_ou_sous_loue_a_des_tiers": "non", "age_personne_sous_location": "sans_objet",
               "sous_locataire_conforme_l442_1": "sans_objet", "proprietaire_famille": "autre",
               "usufruit_famille": "autre", "mode_occupation": "Locataire"},
     "map": lambda b: {"date_courante": "2019-09-01_to_2020-12-31", "residence": b["residence"],
                       "nationalite_demandeur": NAT[b["nationalite_demandeur"]]},
     "out": APL_OUT,
     "why": "B fixes date_courante 2020-03-10 (FR-APL-4 CONVERSION_2.md:103), A's representative of "
            "2019-09-01_to_2020-12-31 (FR-APL-1 CONVERSION.md:44); B keeps three territories; the other "
            "B attributes are held at Exemple1's values, which A fixes."},
    {"id": "APL-floor-area", "A": "FR-APL-2", "B": "FR-APL-5",
     "A_fix": {"residence": ("Metropole", "LaReunion", "Mayotte"),
               "nationalite_demandeur": ("francaise", "etrangere_l512_2_et_art_4")},
     "B_fix": {"nombre_autres_occupants_logement": ("0", "1"), "nombre_personnes_a_charge": ("0", "1", "2", "3")},
     "map": lambda b: {"residence": b["residence"], "nationalite_demandeur": NAT[b["nationalite_demandeur"]],
                       "situation_familiale": b["situation_familiale"],
                       "personnes_a_charge": b["nombre_personnes_a_charge"],
                       "autres_occupants": b["nombre_autres_occupants_logement"],
                       "surface_m_carres": "lt_9" if b["surface_m_carres"] == "below_9" else
                       ("ge_52" if b["surface_m_carres"] in ("52_to_53", "54_to_57", "58_to_60", "61_to_62",
                                                              "63_to_66", "67_to_69", "70_to_71", "from_72")
                        else b["surface_m_carres"]),
                       "personnes_agees_handicapees_r844_4": YN[b["personnes_agees_handicapees_foyer_r844_4"]]},
     "out": APL_OUT,
     "why": "Both fix 2020-03-10 and Exemple1's household; k dependants are the first k children of Exemple1 "
            "on both sides for k <= 3 (A FR-APL-2 CONVERSION.md:31-33, B FR-APL-5 CONVERSION_2.md:82-86). "
            "B's 23 surface bands refine A's 16 (A :52-56, B :87-93)."},
    {"id": "APL-common-conditions", "A": "FR-APL-3", "B": "FR-APL-4",
     "A_fix": {"mode_occupation": "Locataire", "bailleur": "BailleurSocial_conventionne"},
     "B_fix": {"residence": "Metropole", "nationalite_demandeur": "Francaise", "mode_occupation": "Locataire"},
     "map": lambda b: None if sublet_malformed(b) else {
                       "mode_occupation": "Locataire", "bailleur": "BailleurSocial_conventionne",
                       "part_propriete_famille": SHARE[b["proprietaire_famille"]],
                       "part_usufruit_famille": SHARE[b["usufruit_famille"]],
                       "loue_ou_sous_loue_a_des_tiers": sublet(b),
                       "logement_decent_l89_462": YN[b["logement_decent"]],
                       "residence_principale": YN[b["residence_principale"]],
                       "condition_rattache_foyer_fiscal_parent_ifi": YN[b["rattache_foyer_fiscal_parent_ifi"]]},
     "out": APL_OUT,
     "why": "Both fix 2020-03-10 and Exemple1's household. Shares: B's parts_10pct and parts_above_10pct lie in "
            "A's famille_10pc_ou_plus (A FR-APL-3 CONVERSION.md:35-40, B FR-APL-4 CONVERSION_2.md:91-94). "
            "Third party's age: B's 30th_birthday_on_date and over_30 lie in A's 30_ans_ou_plus (A :41-48 "
            "and band check :71-75, B :83-90)."},
    {"id": "APL-landlord", "A": "FR-APL-3", "B": "FR-APL-1",
     "A_fix": {"part_propriete_famille": "Autre", "part_usufruit_famille": "Autre",
               "loue_ou_sous_loue_a_des_tiers": "Non", "logement_decent_l89_462": "vrai",
               "residence_principale": "vrai", "condition_rattache_foyer_fiscal_parent_ifi": "faux"},
     "B_fix": {"date_courante": "2019-10-01_to_2020-12-31", "residence": "Metropole"},
     "map": lambda b: {"mode_occupation": b["mode_occupation"], "bailleur": BAIL2_TO_C1[b["bailleur"]],
                       "part_propriete_famille": "Autre", "part_usufruit_famille": "Autre",
                       "loue_ou_sous_loue_a_des_tiers": "Non", "logement_decent_l89_462": "vrai",
                       "residence_principale": "vrai", "condition_rattache_foyer_fiscal_parent_ifi": "faux"},
     "out": APL_OUT,
     "why": "A fixes 2020-03-10, Métropole (FR-APL-3 CONVERSION.md:50-55); B's band holding that date has "
            "2020-03-10 as representative (FR-APL-1 CONVERSION_2.md:78)."},
    {"id": "APL-logement-foyer", "A": "FR-APL-4", "B": "FR-APL-2",
     "A_fix": {}, "B_fix": {},
     "map": lambda b: {"residence": b["residence"], "date_courante": C2_DATE_TO_C1_APL4[b["date_courante"]],
                       "type_logement_foyer": b["type_logement_foyer"],
                       "conventionne_livre_III_titre_V_chap_III": YN[b["conventionne_livre_III_titre_V_chap_III"]],
                       "remplit_conditions_r832_21": YN[b["remplit_conditions_r832_21"]],
                       "conventionne_selon_regles_drom": YN[b["conventionne_selon_regles_drom"]]},
     "out": APL_OUT,
     "why": "Same six inputs. Fixed inputs differ: A's applicant is Étrangère {l512_2: vrai, art_4_mayotte: vrai} "
            "(FR-APL-4 CONVERSION.md:45-48), B's is Exemple1's Française (FR-APL-2 CONVERSION_2.md:107-113); "
            "date_conventionnement 2000-01-01 (A) and 2010-01-01 (B), which both coders record as unread by "
            "eligibility. B's date bands refine A's (A CONVERSION.md:33, B :74-84)."},
    {"id": "APL-home-buyers", "A": "FR-APL-5", "B": "FR-APL-3",
     "A_fix": {"residence_principale": "vrai"},
     "B_fix": {"residence": "Metropole"},
     "map": lambda b: {"mode_occupation": b["mode_occupation"], "type_pret": b["type_pret"],
                       "titulaire_pret": b["titulaire_pret"],
                       "date_signature_pret": {"before_2017-12-31": "lt_2017-12-31",
                                               "on_2017-12-31": "eq_2017-12-31",
                                               "2018-01-01_to_2019-12-31": "2018-01-01_to_2019-12-31",
                                               "from_2020-01-01": "ge_2020-01-01"}[b["date_signature_pret"]],
                       "anciennete_logement": {"neuf": "Neuf",
                                               "ancien_ameliore_par_occupant": "Ancien_ameliore_par_occupant",
                                               "ancien_non_ameliore_par_occupant": "Ancien_non_ameliore_par_occupant"}
                       [b["anciennete_logement"]],
                       "zone": b["zone"], "date_courante": C2_DATE_TO_C1_APL5[b["date_courante"]],
                       "residence_principale": "vrai"},
     "out": APL_OUT,
     "why": "A fixes Métropole (FR-APL-5 CONVERSION.md:53), B fixes résidence_principale vrai (FR-APL-3 "
            "CONVERSION_2.md:123). Loan records differ (A: 500 €, entry 2010-01-01; B: 700 €, entry = earlier "
            "of signature and decision date), recorded by both as unread by eligibility."},
    {"id": "US-121-1", "A": "US-121-1", "B": "US-121-1", "A_fix": {}, "B_fix": {},
     "map": lambda b: {"ownership_days_in_5_years": c2_days_to_c1(b["property_ownage"]),
                       "use_days_in_5_years": c2_days_to_c1(b["property_usage_as_principal_residence"]),
                       "other_section_121a_sale": OTHER[b["other_section_121a_sale"]]},
     "out": US1_OUT,
     "why": "B's ten period-list shapes each fall on one side of 730 days (B CONVERSION_2.md:45-56); "
            "B's under_2_years_before and exactly_2_years_before lie in A's within_2_years (1 day to 2 years, "
            "A CONVERSION.md:51-57)."},
    {"id": "US-121-2", "A": "US-121-2", "B": "US-121-2", "A_fix": {}, "B_fix": {},
     "map": us2_map, "out": US2_OUT,
     "why": "Joint rows map person by person. A one-person return in B has person 2 not_applicable; A puts "
            "the same taxpayer in person 2 for single returns (A CONVERSION.md:63-65) and the deceased spouse "
            "for surviving-spouse returns (A :66-67), which B fixes to person_ok_1 (B CONVERSION_2.md:73-77). "
            "B rows with a partly filled person 2 on a one-person return have no counterpart."},
]


def fired(spec, row):
    """Ids of the spec's exclusion predicates that hold for row (predicates are the spec's own
    Python expressions over attribute names; evaluated without builtins)."""
    return [e["id"] for e in spec.get("exclusions", [])
            if eval(e["predicate"], {"__builtins__": {}}, dict(row))]


def ok(row, fix):
    for k, v in fix.items():
        if (row[k] not in v) if isinstance(v, tuple) else (row[k] != v):
            return False
    return True


def compare(p):
    abr, af = A_(p["A"])
    bbr, bf = B_(p["B"])
    sa, sb = common.load_spec(abr, af), common.load_spec(bbr, bf)
    na, nb = common.attr_names(sa), common.attr_names(sb)
    ga = common.ground_truth(abr, af, sa)
    gb = common.ground_truth(bbr, bf, sb)
    out_map = dict(p["out"], EXCLUDED="EXCLUDED", REJECTED="REJECTED")
    cells = collections.Counter()
    dis = []
    reached = set()
    unmapped_b = collections.Counter()
    for cb, ob in gb.items():
        rb = dict(zip(nb, cb))
        if not ok(rb, p["B_fix"]):
            continue
        ra = p["map"](rb)
        if ra is None:
            unmapped_b[ob if ob in ("EXCLUDED", "REJECTED") else "valid"] += 1
            continue
        assert ok(ra, p["A_fix"]), (p["id"], ra)
        ca = tuple(ra[n] for n in na)
        oa = ga[ca]
        reached.add(ca)
        obm = out_map[ob]
        cells[(oa, obm)] += 1
        if oa != obm:
            dis.append({"A": ra, "A_output": oa, "B": rb, "B_output": ob,
                        "A_exclusions": fired(sa, ra) if oa == "EXCLUDED" else [],
                        "B_exclusions": fired(sb, rb) if ob == "EXCLUDED" else []})
    a_slice = [c for c in ga if ok(dict(zip(na, c)), p["A_fix"])]
    a_unreached = [c for c in a_slice if c not in reached]
    agree = sum(v for (x, y), v in cells.items() if x == y)
    total = sum(cells.values())
    both_valid = sum(v for (x, y), v in cells.items() if x not in common.INVALID and y not in common.INVALID)
    both_valid_agree = sum(v for (x, y), v in cells.items()
                           if x == y and x not in common.INVALID)
    return {
        "id": p["id"], "A": f"{abr}:{af}", "B": f"{bbr}:{bf}", "why": p["why"],
        "A_fix": {k: list(v) if isinstance(v, tuple) else v for k, v in p["A_fix"].items()},
        "B_fix": {k: list(v) if isinstance(v, tuple) else v for k, v in p["B_fix"].items()},
        "B_rows_compared": total, "agree": agree, "disagree": total - agree,
        "both_valid": both_valid, "both_valid_agree": both_valid_agree,
        "cells": {f"{x} | {y}": v for (x, y), v in sorted(cells.items())},
        "A_slice_rows": len(a_slice), "A_slice_rows_reached": len(a_slice) - len(a_unreached),
        "A_unreached_outputs": dict(collections.Counter(ga[c] for c in a_unreached)),
        "A_unreached_examples": [dict(zip(na, c)) for c in a_unreached[:3]],
        "B_rows_without_counterpart": dict(unmapped_b),
        "disagreements": dis,
    }


def summarise(d, keys):
    """Group disagreements by output pair and the values of `keys` on side A."""
    g = collections.Counter()
    for x in d:
        g[(x["A_output"], x["B_output"]) + tuple(f"{k}={x['A'][k]}" for k in keys)] += 1
    return g


GROUP_KEYS = {
    "APL-tenancy-date-territory": ["residence", "date_courante"],
    "APL-nationality": ["residence", "nationalite_demandeur"],
    "APL-floor-area": ["residence", "nationalite_demandeur", "personnes_agees_handicapees_r844_4"],
    "APL-common-conditions": ["loue_ou_sous_loue_a_des_tiers"],
    "APL-landlord": ["mode_occupation", "bailleur"],
    "APL-logement-foyer": ["residence", "type_logement_foyer"],
    "APL-home-buyers": ["mode_occupation", "titulaire_pret", "type_pret"],
    "US-121-1": ["other_section_121a_sale"],
    "US-121-2": ["return_type", "person1_other_section_121a_sale"],
}


def main():
    res = [compare(p) for p in PAIRS]
    common.write_json("m6_fr2.json", {"comparisons": res})
    print("| Pair | A (first) | B (second) | B rows compared | Agree | Disagree | Both valid (agree) | "
          "A slice rows reached | B rows without counterpart |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in res:
        print(f"| {r['id']} | {r['A'].split('/')[-1]} | {r['B'].split('/')[-1]} | {r['B_rows_compared']} | "
              f"{r['agree']} | {r['disagree']} | {r['both_valid']} ({r['both_valid_agree']}) | "
              f"{r['A_slice_rows_reached']}/{r['A_slice_rows']} | {r['B_rows_without_counterpart'] or '-'} |")
    for r in res:
        print(f"\n### {r['id']}\ncells (A | B): {r['cells']}")
        if r["A_unreached_outputs"]:
            print(f"A rows with no B counterpart: {r['A_unreached_outputs']}, e.g. {r['A_unreached_examples'][0]}")
        for k, v in sorted(summarise(r["disagreements"], GROUP_KEYS[r["id"]]).items()):
            print(f"   {v:6d}  {k}")
        ex = collections.Counter((x["A_output"], x["B_output"], "+".join(x["A_exclusions"]))
                                 for x in r["disagreements"] if x["A_exclusions"])
        for k, v in sorted(ex.items()):
            print(f"   by A exclusion: {v:6d}  {k}")
        if r["disagreements"]:
            print("   example:", r["disagreements"][0])


if __name__ == "__main__":
    main()
