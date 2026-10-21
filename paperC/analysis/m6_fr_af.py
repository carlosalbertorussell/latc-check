"""M6 for the French family benefits (FR-PF, FR-AF): attribute-level alignment of the two
conversions and row-level agreement of their ground truths where rows are comparable.

Row comparison, for each pair of tables that describe the same household shape:
  direction A  every row of the first coder's slice is turned into concrete inputs with the
               first coder's representatives, those inputs are labelled with the second
               coder's cut points, and the two ground-truth outputs are compared;
  direction B  the same from the second coder's rows with the second coder's representatives.
Outputs are compared after coarsening the second coder's labels to the first coder's label
set (mapping in `coarsen`; it is exact because both are read from the same encoding output).
Inputs that one table fixes and the other varies are restricted to the fixed value.
Every disagreement is explained by re-evaluating the encoding with one input group at a time
taken from the other side's representatives (`explain`).

Run: python3.12 -I paperC/analysis/m6_fr_af.py   (writes paperC/analysis/out/m6_fr_af.json)
"""

import itertools
import os
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import m2_fr_af as M  # noqa: E402

B1, B2 = M.B1, M.B2
F1, F2 = "paperC/specs", "paperC/specs2"
INV = common.INVALID

REP2_RES = {"metropole": "Metropole", "drom_l751_1": "Guadeloupe", "mayotte": "Mayotte"}
REP2_PRISE = {"complete": "EffectiveEtPermanente", "partagee": "GardeAlterneePartageAllocations",
              "services_sociaux": "ServicesSociauxAllocationVerseeAuxServicesSociaux"}
REP2_REM = {"jusqu_plafond_mayotte": "0.00", "entre_plafonds": "800.00", "au_dessus_plafonds": "1500.00"}
REP2_AGE = {"moins_3": "2019-05-01", "3_11": "2013-05-01", "11_14": "2008-05-01", "14_16": "2005-05-01",
            "anniversaire_16": "2004-05-01", "16_19": "2002-05-01", "19_20": "2000-11-01",
            "20_23": "1999-05-01", "23_plus": "1995-05-01"}
REP1_REM = {"le_plafond": "0.00", "gt_plafond": "1000.00"}
ATTRIB = {"parent": (True, False), "tiers_titre_I": (False, True), "aucun": (False, False)}


# ================================================================== concrete inputs

def n_of(kids, residence):
    return sum(M.droit_ouvert(c, M.FIXED, residence) for c in kids)


def res_value(label, n):
    """Representative resources (euros) of either coder's resource label for n entitled children."""
    p1, p2 = M.plafond_I(n), M.plafond_II(n)
    return {"lt_plafond_I": 30000.0, "le_plafond_I": 30000.0, "eq_plafond_I": float(p1),
            "entre_I_II": float((p1 + p2) // 2), "gt_I_le_II": float((p1 + p2) // 2),
            "eq_plafond_II": float(p2), "gt_plafond_II": 150000.0,
            "jusqu_plafond_I": 30000.0, "zone_degressive_I": p1 + 1.0, "entre_plafonds_I_II": float(p2),
            "zone_degressive_II": p2 + 1.0, "au_dela_plafond_II": 200000.0}[label]


def first_concrete(table, spec, row):
    """Concrete inputs of a first-coder row (spec.json representatives, CONVERSION.md A5-A8)."""
    reps = {a["name"]: a["representative"] for a in spec["attributes"]}
    nslots = {"FR-AF-1": 3, "FR-AF-2": 2, "FR-AF-3": 3}[table]
    kids = []
    for k in range(1, nslots + 1):
        age = row[f"enfant{k}_age"]
        if age == "absent":
            continue
        kids.append({"naissance": reps[f"enfant{k}_age"][age],
                     "remuneration": REP1_REM[row.get(f"enfant{k}_remuneration", "le_plafond")],
                     "prise": row.get(f"enfant{k}_prise_en_charge", "EffectiveEtPermanente"),
                     "deja": row.get(f"enfant{k}_deja_ouvert", "true") == "true",
                     "apl": row.get(f"enfant{k}_apl", "false") == "true"})
    residence = row.get("residence", "Metropole")
    n = n_of(kids, residence)
    ress = res_value(row["ressources"], n) if "ressources" in row else 30000.0
    return {"residence": residence, "ressources": ress, "kids": kids,
            "est_parent": row.get("est_parent", "true") == "true", "titre_I": row.get("titre_I", "false") == "true",
            "avant": row.get("avait_enfant_avant_2012", "false") == "true"}


def second_concrete(table, row):
    """Concrete inputs of a second-coder row (CONVERSION_2.md C2, C3, A2-A4; oracle.py reps)."""
    nslots = {"FR-AF-1": 1, "FR-AF-2": 2, "FR-AF-3": 3}[table]
    kids = []
    for k in range(1, nslots + 1):
        kids.append({"naissance": REP2_AGE[row[f"e{k}_age"]],
                     "remuneration": REP2_REM[row.get(f"e{k}_remuneration", "jusqu_plafond_mayotte")],
                     "prise": REP2_PRISE[row.get(f"e{k}_prise_en_charge", "complete")],
                     "deja": row.get(f"e{k}_deja_ouvert", "true") == "true",
                     "apl": row.get(f"e{k}_aide_logement", "false") == "true"})
    residence = REP2_RES[row["residence"]]
    n = n_of(kids, residence)
    est, titre = ATTRIB[row.get("attributaire", "parent")]
    return {"residence": residence, "ressources": res_value(row["ressources"], n), "kids": kids,
            "est_parent": est, "titre_I": titre, "avant": row["avant_2012"] == "true"}


def call(conc):
    enc = M.encoding()
    ch = [{"naissance": M.d(c["naissance"]), "remuneration": c["remuneration"], "prise": c["prise"],
           "deja_ouvert": c["deja"], "aide_logement": c["apl"]} for c in conc["kids"]]
    return enc.call_interface(ch, int(round(conc["ressources"] * 100)), conc["residence"], M.FIXED,
                              conc["est_parent"], conc["titre_I"], conc["avant"])


# ================================================================== labels of concrete inputs

def first_labels(table, conc):
    """The first coder's labels for concrete inputs (dict keyed by its attribute names)."""
    kids, res = conc["kids"], conc["residence"]
    n = n_of(kids, res)
    row = {}
    if table == "FR-AF-1":
        row.update(residence=res, ressources=M.res5(conc["ressources"], n),
                   avait_enfant_avant_2012=M.B(conc["avant"]), est_parent=M.B(conc["est_parent"]),
                   titre_I=M.B(conc["titre_I"]))
        for k in range(3):
            row[f"enfant{k + 1}_age"] = M.age7(M.d(kids[k]["naissance"]), M.FIXED) if k < len(kids) else "absent"
    elif table == "FR-AF-2":
        row.update(residence=res, ressources=M.res3(conc["ressources"], n))
        for k in range(2):
            c = kids[k]
            row.update({f"enfant{k + 1}_age": M.age7(M.d(c["naissance"]), M.FIXED),
                        f"enfant{k + 1}_remuneration": M.rem2_first(c["remuneration"], res),
                        f"enfant{k + 1}_prise_en_charge": c["prise"]})
    else:
        for k in range(3):
            c = kids[k]
            row.update({f"enfant{k + 1}_age": M.age7(M.d(c["naissance"]), M.FIXED),
                        f"enfant{k + 1}_remuneration": M.rem2_first(c["remuneration"], res),
                        f"enfant{k + 1}_deja_ouvert": M.B(c["deja"]), f"enfant{k + 1}_apl": M.B(c["apl"])})
    return row


def second_labels(table, conc, comp):
    enc = M.encoding()
    kids = conc["kids"]
    row = {"residence": M.res_group(conc["residence"]), "ressources": enc.ressources_region(comp),
           "avant_2012": M.B(conc["avant"])}
    if table == "FR-AF-1":
        row["attributaire"] = "parent" if conc["est_parent"] else ("tiers_titre_I" if conc["titre_I"] else "aucun")
    for k, c in enumerate(kids, 1):
        row.update({f"e{k}_age": M.age9(M.d(c["naissance"]), M.FIXED), f"e{k}_remuneration": M.rem_second(c["remuneration"]),
                    f"e{k}_prise_en_charge": M.PRISE_GROUP[c["prise"]], f"e{k}_deja_ouvert": M.B(c["deja"]),
                    f"e{k}_aide_logement": M.B(c["apl"])})
    return row


# ================================================================== output coarsening

def coarsen(label2, components=False):
    """Second coder's regime label -> first coder's label set.

    Regime labels (FR-AF-1/2 of the first coder, CONVERSION.md A3): sans_droit or parts `nul` -> zero
    (amount 0); bareme mayotte or mayotte_avant_2012 -> mayotte; outre_mer_un_enfant -> outre_mer_1_enfant;
    general/Tk -> general_tk. Component labels (first FR-AF-3, CONVERSION.md T5): zero, or B with M and/or F.
    """
    if label2 in INV:
        return label2
    if label2 == "sans_droit" or label2.endswith("/nul"):
        return "zero"
    parts = label2.split("/")
    if components:
        p = set(parts[-1].split("+"))
        if parts[0] != "general" or "B" not in p or "C" in p:
            return f"unmapped:{label2}"
        return "base" + ("_majoration" if "M" in p else "") + ("_forfaitaire" if "F" in p else "")
    if parts[0].startswith("mayotte"):
        return "mayotte"
    if parts[0] == "outre_mer_un_enfant":
        return "outre_mer_1_enfant"
    return "general_" + parts[1].lower()


def first_style(montant, comp, conc, components=False):
    """Label of the first coder's scheme for an encoding result (for the explanations)."""
    if components:
        return coarsen(M.encoding().regime_label(comp), True)
    if montant == 0:
        return "zero"
    if conc["residence"] == "Mayotte":
        return "mayotte"
    if conc["residence"] in M.L751_1 and comp["n_droit_ouvert"] == 1:
        return "outre_mer_1_enfant"
    r = comp["ressources"]
    return "general_t1" if r <= comp["plafond_I"] else ("general_t2" if r <= comp["plafond_II"] else "general_t3")


# ================================================================== explanation of a disagreement

def factors(conc):
    f = {"residence": conc["residence"], "ressources": conc["ressources"],
         "household flags": (conc["est_parent"], conc["titre_I"], conc["avant"])}
    for k, c in enumerate(conc["kids"], 1):
        f[f"child{k} birth date"] = c["naissance"]
        f[f"child{k} earnings"] = c["remuneration"]
        f[f"child{k} prise"] = c["prise"]
        f[f"child{k} deja/apl"] = (c["deja"], c["apl"])
    return f


def apply(conc, name, other):
    c = {**conc, "kids": [dict(k) for k in conc["kids"]]}
    if name == "residence":
        c["residence"] = other["residence"]
    elif name == "ressources":
        c["ressources"] = other["ressources"]
    elif name == "household flags":
        c["est_parent"], c["titre_I"], c["avant"] = other["est_parent"], other["titre_I"], other["avant"]
    else:
        k = int(name[5]) - 1
        o = other["kids"][k]
        key = name.split(" ", 1)[1]
        if key == "birth date":
            c["kids"][k]["naissance"] = o["naissance"]
        elif key == "earnings":
            c["kids"][k]["remuneration"] = o["remuneration"]
        elif key == "prise":
            c["kids"][k]["prise"] = o["prise"]
        else:
            c["kids"][k]["deja"], c["kids"][k]["apl"] = o["deja"], o["apl"]
    return c


def explain(src, dst, components):
    """Which single input group of the other side's representatives changes the label."""
    m0, c0 = call(src)
    m1, c1 = call(dst)
    l0, l1 = first_style(m0, c0, src, components), first_style(m1, c1, dst, components)
    fs, fd = factors(src), factors(dst)
    diff = [k for k in fs if fs[k] != fd.get(k)]
    flips = []
    for k in diff:
        m, c = call(apply(src, k, dst))
        if first_style(m, c, src, components) != l0:
            flips.append(k)
    return {"src_label": l0, "dst_label": l1, "differing": diff, "single_flips": flips,
            "src_amount": m0, "dst_amount": m1}


# ================================================================== pairs

PAIRS = [  # id, first table, first slice, second table, second slice, components
    ("P1", "FR-AF-1", "one child in slot 1 (slots 2-3 absent)", "FR-AF-1",
     "e1 earnings jusqu_plafond_mayotte, prise complete, deja true, aide false"),
    ("P2", "FR-AF-1", "two children in slots 1-2 (slot 3 absent); est_parent true, titre_I false", "FR-AF-2",
     "both children earnings jusqu_plafond_mayotte, prise complete"),
    ("P3", "FR-AF-1", "three children; est_parent true, titre_I false", "FR-AF-3", "all deja true"),
    ("P4", "FR-AF-2", "all rows", "FR-AF-2", "avant_2012 false"),
    ("P5", "FR-AF-3", "all earnings le_plafond, all apl false", "FR-AF-3",
     "residence metropole, ressources jusqu_plafond_I, avant_2012 false"),
]


def in_first_slice(pid, row):
    if pid == "P1":
        return row["enfant1_age"] != "absent" and row["enfant2_age"] == "absent" and row["enfant3_age"] == "absent"
    if pid == "P2":
        return (row["enfant1_age"] != "absent" and row["enfant2_age"] != "absent" and row["enfant3_age"] == "absent"
                and row["est_parent"] == "true" and row["titre_I"] == "false")
    if pid == "P3":
        return (all(row[f"enfant{k}_age"] != "absent" for k in (1, 2, 3))
                and row["est_parent"] == "true" and row["titre_I"] == "false")
    if pid == "P4":
        return True
    return all(row[f"enfant{k}_remuneration"] == "le_plafond" and row[f"enfant{k}_apl"] == "false" for k in (1, 2, 3))


def in_second_slice(pid, row):
    if pid == "P1":
        return (row["e1_remuneration"] == "jusqu_plafond_mayotte" and row["e1_prise_en_charge"] == "complete"
                and row["e1_deja_ouvert"] == "true" and row["e1_aide_logement"] == "false")
    if pid == "P2":
        return all(row[f"e{k}_remuneration"] == "jusqu_plafond_mayotte" and row[f"e{k}_prise_en_charge"] == "complete"
                   for k in (1, 2))
    if pid == "P3":
        return all(row[f"e{k}_deja_ouvert"] == "true" for k in (1, 2, 3))
    if pid == "P4":
        return row["avant_2012"] == "false"
    return row["residence"] == "metropole" and row["ressources"] == "jusqu_plafond_I" and row["avant_2012"] == "false"


def rows_of(branch, folder):
    spec = common.load_spec(branch, folder)
    names = common.attr_names(spec)
    gt = common.ground_truth(branch, folder, spec)
    return spec, names, gt


_CTX = {}


def _dir_a_chunk(args):
    pid, t1, t2, rows = args
    spec1 = _CTX.setdefault(t1, common.load_spec(B1, f"{F1}/{t1}"))
    out = []
    for row in rows:
        conc = first_concrete(t1, spec1, row)
        if not conc["est_parent"] and not conc["titre_I"]:  # first coder's REJECTED cells (A4)
            lab2 = second_labels(t2, conc, {"ressources": 0, "plafond_I": 0, "plafond_II": 0,
                                             "allocation_pour_complement": 0, "forfaitaire": 0})
            out.append((row, conc, lab2, "REJECTED"))
            continue
        try:
            m, comp = call(conc)
            lab2 = second_labels(t2, conc, comp)
            own = first_style(m, comp, conc, pid == "P5")
        except Exception as exc:  # the encoding's L521-2 assertion
            lab2, own = None, f"error {type(exc).__name__}"
        out.append((row, conc, lab2, own))
    return out


def compare_pair(pid, t1, slice1, t2, slice2, workers):
    comp_mode = pid == "P5"
    spec1, n1, gt1 = rows_of(B1, f"{F1}/{t1}")
    spec2, n2, gt2 = rows_of(B2, f"{F2}/{t2}")
    res = {"pair": pid, "first": t1, "first_slice": slice1, "second": t2, "second_slice": slice2}
    # direction A
    rows1 = [dict(zip(n1, c)) for c in gt1 if in_first_slice(pid, dict(zip(n1, c)))]
    chunks = [(pid, t1, t2, rows1[i:i + 400]) for i in range(0, len(rows1), 400)]
    with ProcessPoolExecutor(workers) as ex:
        evald = [x for part in ex.map(_dir_a_chunk, chunks) for x in part]
    cnt, dis = Counter(), []
    own_mismatch = 0
    for row, conc, lab2, own in evald:
        o1 = gt1[tuple(row[n] for n in n1)]
        if o1 in INV:
            k2 = tuple(lab2[n] for n in n2) if lab2 else None
            o2 = gt2.get(k2) if k2 else None
            cnt[f"first {o1}; second {o2 if o2 in INV else 'valid' if o2 else 'not evaluated'}"] += 1
            continue
        if own != o1:
            own_mismatch += 1
        k2 = tuple(lab2[n] for n in n2)
        if not in_second_slice(pid, lab2):
            cnt["maps outside the second slice"] += 1
            continue
        o2 = coarsen(gt2[k2], comp_mode)
        if o2 in INV:
            cnt[f"first valid; second {o2}"] += 1
        elif o2 == o1:
            cnt["agree"] += 1
        else:
            cnt["disagree"] += 1
            dis.append({"first_row": row, "first_out": o1, "second_row": lab2, "second_out": gt2[k2],
                        "second_coarse": o2, "src": conc, "dst": second_concrete(t2, lab2)})
    res["A"] = {"rows": len(rows1), "counts": dict(cnt), "first_repr_reproduces_gt_failures": own_mismatch}
    res["A_dis"] = dis
    # direction B
    cnt, disb = Counter(), []
    rows2 = [dict(zip(n2, c)) for c in gt2 if in_second_slice(pid, dict(zip(n2, c)))]
    for row in rows2:
        o2 = gt2[tuple(row[n] for n in n2)]
        conc = second_concrete(t2, row)
        lab1 = first_labels(t1, conc)
        if pid == "P5":
            lab1 = {k: v for k, v in lab1.items() if k in n1}
        k1 = tuple(lab1[n] for n in n1)
        o1 = gt1[k1]
        if o2 in INV:
            cnt[f"second {o2}; first {o1 if o1 in INV else 'valid'}"] += 1
            continue
        oc = coarsen(o2, pid == "P5")
        if o1 in INV:
            cnt[f"second valid; first {o1}"] += 1
        elif o1 == oc:
            cnt["agree"] += 1
        else:
            cnt["disagree"] += 1
            disb.append({"second_row": row, "second_out": o2, "second_coarse": oc, "first_row": lab1,
                         "first_out": o1, "src": conc, "dst": first_concrete(t1, spec1, lab1)})
    res["B"] = {"rows": len(rows2), "counts": dict(cnt)}
    res["B_dis"] = disb
    return res


def explain_all(res):
    comp_mode = res["pair"] == "P5"
    for side in ("A_dis", "B_dis"):
        groups = {}
        for x in res[side]:
            e = explain(x["src"], x["dst"], comp_mode)
            fr = x["first_row"]
            same = len({fr[f"enfant{k}_age"] for k in (1, 2, 3) if f"enfant{k}_age" in fr and fr[f"enfant{k}_age"] != "absent"}) == 1
            key = (x["first_out"], x["second_coarse"], tuple(e["single_flips"]) if e["single_flips"] else ("none single",), same)
            g = groups.setdefault(key, {"count": 0, "example": None, "shapes": Counter()})
            g["count"] += 1
            g["shapes"][" | ".join(f"{k}={v}" for k, v in sorted(fr.items()) if k.startswith("enfant"))] += 1
            if g["example"] is None:
                g["example"] = {k: x[k] for k in ("first_row", "first_out", "second_row", "second_out")}
                g["example"]["explanation"] = e
                g["example"]["source_inputs"] = x["src"]
                g["example"]["target_inputs"] = x["dst"]
        res[side.replace("_dis", "_groups")] = [
            {"first_out": k[0], "second_coarse": k[1], "flipping_inputs": list(k[2]), "all_children_same_first_band": k[3], **v}
            for k, v in groups.items()]
        for g in res[side.replace("_dis", "_groups")]:
            g["shapes"] = dict(g["shapes"])
        res[side] = len(res[side])


# ================================================================== FR-PF

def pf_pair():
    s1, n1, gt1 = rows_of(B1, f"{F1}/FR-PF")
    s2, n2, gt2 = rows_of(B2, f"{F2}/FR-PF")
    reps1 = {a["name"]: a["representative"] for a in s1["attributes"]}
    out1 = {"entitled": "ouvert", "not_entitled": "non_ouvert"}
    A, B = Counter(), Counter()
    disA, disB = [], []
    for c, o1 in gt1.items():
        r = dict(zip(n1, c))
        if r["prise_en_charge"] != "EffectiveEtPermanente":  # fixed by the second coder (P1 of CONVERSION_2.md)
            A["first prise_en_charge differs from the second coder's fixed value"] += 1
            continue
        earn = "711.49" if (r["remuneration"] == "eq_plafond" and r["residence"] == "Mayotte") else reps1["remuneration"][r["remuneration"]]
        lab2 = {"residence": M.res_group(r["residence"]), "obligation_scolaire": r["obligation_scolaire"],
                "remuneration_mensuelle": M.rem_second(earn),
                "age_20_ans": M.age20(M.d(reps1["age"][r["age"]]), M.FIXED), "aide_logement_personnelle": r["apl"]}
        o2 = gt2[tuple(lab2[n] for n in n2)]
        key = ("first " + (o1 if o1 in INV else "valid")) + "; second " + (o2 if o2 in INV else "valid")
        if o1 in INV or o2 in INV:
            A[key] += 1
        elif out1[o1] == o2:
            A["agree"] += 1
        else:
            A["disagree"] += 1
            disA.append({"first_row": r, "first_out": o1, "second_row": lab2, "second_out": o2})
    REP2_B = {"moins_20": "2005-01-01", "20_ou_plus": "1998-01-01"}
    for c, o2 in gt2.items():
        r = dict(zip(n2, c))
        res = REP2_RES[r["residence"]]
        earn = REP2_REM[r["remuneration_mensuelle"]]
        lab1 = {"residence": res, "obligation_scolaire": r["obligation_scolaire"], "prise_en_charge": "EffectiveEtPermanente",
                "age": M.age4(M.d(REP2_B[r["age_20_ans"]]), M.FIXED), "remuneration": M.rem3_first(earn, res),
                "apl": r["aide_logement_personnelle"]}
        o1 = gt1[tuple(lab1[n] for n in n1)]
        key = ("second " + (o2 if o2 in INV else "valid")) + "; first " + (o1 if o1 in INV else "valid")
        if o1 in INV or o2 in INV:
            B[key] += 1
        elif out1[o1] == o2:
            B["agree"] += 1
        else:
            B["disagree"] += 1
            disB.append({"second_row": r, "second_out": o2, "first_row": lab1, "first_out": o1})
    # which exclusion rows meet which
    excl = Counter()
    for c, o2 in gt2.items():
        r = dict(zip(n2, c))
        if o2 == "EXCLUDED":
            excl["second X-PF-SCOL rows"] += 1
    return {"A": {"rows": len(gt1), "counts": dict(A)}, "A_disagreements": disA,
            "B": {"rows": len(gt2), "counts": dict(B)}, "B_disagreements": disB}


def pf_common_refinement():
    """Exact comparison on the common refinement of both FR-PF tables: every cell of
    residence(9) x obligation(3) x age cut at 3/16/20 x earnings cut at 711.49/943.02 (and the
    ceilings' points) x apl, with prise EffectiveEtPermanente, labelled into both tables."""
    s1, n1, gt1 = rows_of(B1, f"{F1}/FR-PF")
    s2, n2, gt2 = rows_of(B2, f"{F2}/FR-PF")
    births = {"lt3": "2019-01-01", "3to16": "2007-01-01", "16to20": "2003-01-01", "ge20": "1999-01-01"}
    earns = ["0.00", "711.49", "800.00", "943.02", "1000.00"]
    cnt = Counter()
    dis = []
    out1 = {"entitled": "ouvert", "not_entitled": "non_ouvert"}
    for res, obl, b, e, apl in itertools.product(s1["attributes"][0]["values"], ["Avant", "Pendant", "Apres"],
                                                 births.values(), earns, ["false", "true"]):
        l1 = {"residence": res, "obligation_scolaire": obl, "prise_en_charge": "EffectiveEtPermanente",
              "age": M.age4(M.d(b), M.FIXED), "remuneration": M.rem3_first(e, res), "apl": apl}
        l2 = {"residence": M.res_group(res), "obligation_scolaire": obl, "remuneration_mensuelle": M.rem_second(e),
              "age_20_ans": M.age20(M.d(b), M.FIXED), "aide_logement_personnelle": apl}
        o1, o2 = gt1[tuple(l1[n] for n in n1)], gt2[tuple(l2[n] for n in n2)]
        if o1 in INV or o2 in INV:
            cnt[f"first {o1 if o1 in INV else 'valid'}; second {o2 if o2 in INV else 'valid'}"] += 1
        elif out1[o1] == o2:
            cnt["agree"] += 1
        else:
            cnt["disagree"] += 1
            dis.append({"cell": [res, obl, b, e, apl], "first": [l1, o1], "second": [l2, o2]})
    return {"cells": sum(cnt.values()), "counts": dict(cnt), "disagreements": dis}


# ================================================================== alignment (M6 a)

def cite1(path_in_folder, table, needle):
    return common.cite(B1, f"{F1}/{table}/{path_in_folder}", needle)


def cite2(path_in_folder, table, needle):
    return common.cite(B2, f"{F2}/{table}/{path_in_folder}", needle)


def alignment():
    pf = [
        {"input": "date_courante", "first": "fixed 2020-05-01", "second": "fixed 2020-05-01", "nesting": "coincide",
         "src1": cite1("spec.json", "FR-PF", '"date_courante"'), "src2": cite2("spec.json", "FR-PF", '"date_courante"')},
        {"input": "résidence", "first": "attribute, 9 collectivités", "second": "attribute, 3 classes "
         "(metropole = Métropole+SaintPierreEtMiquelon; drom_l751_1 = 6 L751-1 territories; mayotte)",
         "nesting": "first refines second", "src1": cite1("spec.json", "FR-PF", '"name": "residence"'),
         "src2": cite2("CONVERSION_2.md", "FR-PF", "| `metropole` |")},
        {"input": "obligation_scolaire", "first": "attribute Avant/Pendant/Apres", "second": "attribute Avant/Pendant/Apres",
         "nesting": "coincide", "src1": cite1("spec.json", "FR-PF", '"name": "obligation_scolaire"'),
         "src2": cite2("spec.json", "FR-PF", '"name": "obligation_scolaire"')},
        {"input": "date_de_naissance", "first": "attribute age, cuts at 3, 16, 20 years (a00_03, a03_16, a16_20, a20_plus)",
         "second": "attribute age_20_ans, cut at 20 years (moins_20, 20_ou_plus)", "nesting": "first refines second "
         "(same strictness at 20: b + 20 an > date_courante)", "src1": cite1("spec.json", "FR-PF", '"name": "age"'),
         "src2": cite2("CONVERSION_2.md", "FR-PF", "### P2. Age: one cut, at 20")},
        {"input": "rémuneration_mensuelle", "first": "attribute, 3 bands relative to the residence's ceiling: "
         "< ceiling, = ceiling, > ceiling (943,02 EUR; Mayotte 711,49 EUR)", "second": "attribute, 3 absolute bands: "
         "[0, 711,49], (711,49, 943,02], > 943,02 EUR", "nesting": "cross (first isolates the ceiling point and is "
         "residence-relative; second cuts at both ceilings for every residence)",
         "src1": cite1("CONVERSION.md", "FR-PF", "**C6. Earnings bands"), "src2": cite2("CONVERSION_2.md", "FR-PF", "### C3.")},
        {"input": "prise_en_charge", "first": "attribute, 5 values (not read by droit_ouvert)",
         "second": "fixed EffectiveEtPermanente", "nesting": "first varies, second fixes",
         "src1": cite1("CONVERSION.md", "FR-PF", "**C4."), "src2": cite2("CONVERSION_2.md", "FR-PF", "are fixed (`fixed_inputs`)")},
        {"input": "a_déjà_ouvert_droit_aux_allocations_familiales", "first": "fixed vrai", "second": "fixed vrai",
         "nesting": "coincide", "src1": cite1("CONVERSION.md", "FR-PF", "**C7. `apl`**"),
         "src2": cite2("spec.json", "FR-PF", '"a_déjà_ouvert_droit_aux_allocations_familiales"')},
        {"input": "bénéficie_titre_personnel_aide_personnelle_logement", "first": "attribute apl", "second":
         "attribute aide_logement_personnelle", "nesting": "coincide", "src1": cite1("spec.json", "FR-PF", '"name": "apl"'),
         "src2": cite2("spec.json", "FR-PF", '"name": "aide_logement_personnelle"')},
        {"input": "identifiant", "first": "fixed 1", "second": "fixed 1", "nesting": "coincide",
         "src1": cite1("spec.json", "FR-PF", '"identifiant"'), "src2": cite2("spec.json", "FR-PF", '"identifiant"')},
        {"input": "exclusions", "first": "X1-X3: obligation_scolaire inconsistent with the 3/16-year cuts (2 160 of 3 240 rows)",
         "second": "X-PF-SCOL: Avant or Pendant with age 20 or more (36 of 108 rows)",
         "nesting": "first's exclusions contain the second's (every X-PF-SCOL cell is in X1 or X2); the first also "
         "excludes Avant at 3-19, Pendant under 3 or at 16-19 and Apres under 16, which the second's single age cut cannot state",
         "src1": cite1("CONVERSION.md", "FR-PF", "**C8. Exclusions X1-X3.**"), "src2": cite2("CONVERSION_2.md", "FR-PF", "### P3. Exclusion X-PF-SCOL")},
    ]
    af = [
        {"input": "date_courante", "first": "fixed 2020-05-01 (all three tables)", "second": "fixed 2020-05-01 (all three tables)",
         "nesting": "coincide", "src1": cite1("CONVERSION.md", "FR-AF-1", "**A2. Fixed date 2020-05-01.**"),
         "src2": cite2("CONVERSION_2.md", "FR-AF-1", "### C1. Fixed date")},
        {"input": "number of children (i_enfants length)", "first": "FR-AF-1: 0-3 (slots with `absent`); FR-AF-2: exactly 2; "
         "FR-AF-3: exactly 3", "second": "FR-AF-1: exactly 1; FR-AF-2: exactly 2; FR-AF-3: exactly 3",
         "nesting": "first FR-AF-1 covers the 1-, 2- and 3-child shapes of all three second tables (with fewer per-child inputs); "
         "0 children only in the first", "src1": cite1("CONVERSION.md", "FR-AF-1", "**T2. Number of children.**"),
         "src2": cite2("CONVERSION_2.md", "FR-AF-1", "### A1. Split into sub-tables")},
        {"input": "i_résidence", "first": "attribute 9 values in FR-AF-1, FR-AF-2; fixed Métropole in FR-AF-3",
         "second": "attribute 3 classes in all three tables", "nesting": "first refines second where both vary",
         "src1": cite1("spec.json", "FR-AF-1", '"name": "residence"'), "src2": cite2("CONVERSION_2.md", "FR-AF-1", "### C2. Residence")},
        {"input": "i_ressources_ménage", "first": "FR-AF-1: 5 bands < pI, = pI, (pI, pII), = pII, > pII; FR-AF-2: 3 bands "
         "<= pI, (pI, pII], > pII; FR-AF-3: fixed 30 000 EUR; pI = 57 759 + 5 775 n, pII = 80 831 + 5 775 n EUR",
         "second": "5 bands in all tables: <= pI, (pI, pI + 12a], (pI + 12a, pII], (pII, pII + 12a], > pII + 12a, "
         "a = allocation computed by the encoding", "nesting": "cross. Both cut at pI and pII. The second adds the "
         "complément dégressif cuts pI + 12a and pII + 12a; the first FR-AF-1 isolates the points pI and pII. First FR-AF-2's "
         "3 bands are refined by the second's 5", "src1": cite1("CONVERSION.md", "FR-AF-1", "**A5. Resource ceilings"),
         "src2": cite2("CONVERSION_2.md", "FR-AF-1", "### A4. Household resources")},
        {"input": "i_personne_charge_effective_permanente_est_parent / _remplit_titre_I", "first": "two attributes in FR-AF-1 "
         "(both false = REJECTED); fixed (vrai, faux) in FR-AF-2, FR-AF-3", "second": "one attribute attributaire in FR-AF-1: "
         "parent (vrai, faux), tiers_titre_I (faux, vrai), aucun (EXCLUDED); (vrai, vrai) has no label; fixed parent in FR-AF-2, FR-AF-3",
         "nesting": "first refines second on FR-AF-1 ((vrai, vrai) is a cell of its own in the first)",
         "src1": cite1("CONVERSION.md", "FR-AF-1", "**A4. REJECTED.**"), "src2": cite2("CONVERSION_2.md", "FR-AF-1", "`attributaire` combines")},
        {"input": "i_avait_enfant_à_charge_avant_1er_janvier_2012", "first": "attribute in FR-AF-1; fixed faux in FR-AF-2, FR-AF-3",
         "second": "attribute in all three tables", "nesting": "coincide where both vary",
         "src1": cite1("spec.json", "FR-AF-1", '"name": "avait_enfant_avant_2012"'), "src2": cite2("spec.json", "FR-AF-2", '"name": "avant_2012"')},
        {"input": "d_date_de_naissance (per child)", "first": "7 bands a00_03, a03_11, a11_14, a14_16 (14th birthday to 16th "
         "birthday inclusive), a16_19, a19_20, a20_plus; slot k is (k - 1) days younger than slot 1", "second": "9 bands moins_3, "
         "3_11, 11_14, 14_16 (16th birthday excluded), anniversaire_16 (the 16th birthday), 16_19, 19_20, 20_23, 23_plus "
         "(born on or before 1997-04-30); all slots share the band representative", "nesting": "second refines first: "
         "a14_16 = 14_16 + anniversaire_16; a20_plus = 20_23 + 23_plus; other bands coincide",
         "src1": cite1("CONVERSION.md", "FR-AF-1", "**A6. Age bands.**"), "src2": cite2("CONVERSION_2.md", "FR-AF-1", "**Age** (`eN_age`)")},
        {"input": "d_rémuneration_mensuelle (per child)", "first": "fixed 0 EUR in FR-AF-1; 2 bands <= ceiling of the residence "
         "(943,02 / Mayotte 711,49) and above, in FR-AF-2, FR-AF-3", "second": "3 absolute bands [0, 711,49], (711,49, 943,02], "
         "> 943,02 in FR-AF-1, FR-AF-2; fixed 0 EUR in FR-AF-3", "nesting": "second refines first (for Mayotte the first's "
         "cut is 711,49, for the others 943,02; both are cuts of the second)",
         "src1": cite1("CONVERSION.md", "FR-AF-1", "**A7. Child earnings.**"), "src2": cite2("CONVERSION_2.md", "FR-AF-1", "### C3. Child's monthly earnings")},
        {"input": "d_prise_en_charge (per child)", "first": "fixed EffectiveEtPermanente in FR-AF-1, FR-AF-3; attribute 5 values in FR-AF-2",
         "second": "attribute 3 classes (complete, partagee, services_sociaux) in FR-AF-1, FR-AF-2; fixed EffectiveEtPermanente in FR-AF-3",
         "nesting": "first refines second where both vary (FR-AF-2)", "src1": cite1("CONVERSION.md", "FR-AF-2", "**T2. Care arrangement.**"),
         "src2": cite2("CONVERSION_2.md", "FR-AF-1", "**Prise en charge**")},
        {"input": "d_a_déjà_ouvert_droit_aux_allocations_familiales", "first": "fixed vrai in FR-AF-1, FR-AF-2; attribute in FR-AF-3",
         "second": "attribute in FR-AF-1, FR-AF-3; fixed vrai in FR-AF-2", "nesting": "coincide where both vary (FR-AF-3)",
         "src1": cite1("spec.json", "FR-AF-3", '"name": "enfant1_deja_ouvert"'), "src2": cite2("spec.json", "FR-AF-3", '"name": "e1_deja_ouvert"')},
        {"input": "d_bénéficie_titre_personnel_aide_personnelle_logement", "first": "fixed faux in FR-AF-1, FR-AF-2; attribute in FR-AF-3",
         "second": "attribute in FR-AF-1; fixed faux in FR-AF-2, FR-AF-3", "nesting": "never varied together in tables of the same shape",
         "src1": cite1("spec.json", "FR-AF-3", '"name": "enfant1_apl"'), "src2": cite2("spec.json", "FR-AF-1", '"name": "e1_aide_logement"')},
        {"input": "d_identifiant", "first": "fixed 0, 1, 2 in list order", "second": "fixed 1, 2, 3 in list order",
         "nesting": "coincide in effect (distinct values in list order)", "src1": cite1("spec.json", "FR-AF-1", '"identifiants"'),
         "src2": cite2("spec.json", "FR-AF-1", '"d_identifiant"')},
        {"input": "output", "first": "FR-AF-1, FR-AF-2: regime zero, general_t1-3, outre_mer_1_enfant, mayotte; FR-AF-3: components zero, "
         "base, base_majoration, base_forfaitaire, base_majoration_forfaitaire", "second": "sans_droit or bareme/tier/parts "
         "(19, 54 and 62 labels)", "nesting": "second refines first: each second label maps to one first label (`coarsen`)",
         "src1": cite1("CONVERSION.md", "FR-AF-1", "**A3. Output labels"), "src2": cite2("CONVERSION_2.md", "FR-AF-1", "### A5. Output: amount regime")},
    ]
    return {"FR-PF": pf, "FR-AF": af}


# ================================================================== main

def main():
    workers = min(4, os.cpu_count() or 1)
    out = {"alignment": alignment(), "FR-PF": pf_pair(), "FR-PF_common_refinement": pf_common_refinement(), "FR-AF": []}
    for pid, t1, s1, t2, s2 in PAIRS:
        r = compare_pair(pid, t1, s1, t2, s2, workers)
        explain_all(r)
        out["FR-AF"].append(r)
        print(pid, t1, "->", t2, "A", r["A"], "B", r["B"])
        for side in ("A_groups", "B_groups"):
            for g in r[side]:
                print("   ", side, g["count"], g["first_out"], "vs", g["second_coarse"], "flips:", g["flipping_inputs"],
                      "same band:", g["all_children_same_first_band"])
    p = out["FR-PF"]
    print("FR-PF A", p["A"], "B", p["B"])
    print("FR-PF refinement", out["FR-PF_common_refinement"]["counts"])
    common.write_json("m6_fr_af.json", out)


if __name__ == "__main__":
    main()
