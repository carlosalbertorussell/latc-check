"""Ground-truth spot-check (task step 2), independent of the spec folders' oracle.py
and frcatala.py.

For each sample, draws 50 row indices of ground_truth.csv with
random.Random(20261020).sample(range(|D|), 50), translates each row's labels to
concrete inputs with spec.json's representatives, evaluates them through the
generated Catala Python in paperC/catala_family_benefits/ and derives the label
with this file's own reading of spec.json's output definitions:

* FR-PF: droit_ouvert vrai/faux -> entitled/not_entitled.
* FR-AF-1, FR-AF-2 (regime_montant_verse): zero if i_montant_versé = 0; else mayotte
  if résidence Mayotte; else outre_mer_1_enfant if résidence in L751-1 and exactly
  one child with droit_ouvert; else general_t1/t2/t3 by ressources against
  plafond I / plafond II (<=, <=, >).
* FR-AF-3 (composantes_montant_verse): zero, or the components with a positive
  amount among montant_versé_base, _majoration, _forfaitaire.

The number of children with droit_ouvert, the two resource ceilings and the
amount components are read from the encoding itself: a profiler hook captures the
local variables of the generated function `allocations_familiales` when it returns
(`enfants_a_charge_droit_ouvert_prestation_familiale`, `plafond_i_d521_3`,
`plafond_i_i_d521_3`, `montant_verse_base`, `montant_verse_majoration`,
`montant_verse_forfaitaire`, and the two complément variables). No generated file is
modified.

EXCLUDED rows (FR-PF) are checked against the exclusions' stated source: the
obligation_scolaire that the encoding's own interface derives from the
representative birth date (epilogue.catala_fr:121-131, generated as
`_enfants_a_charge__1` in interface_allocations_familiales: b + 3 an >= dc -> Avant,
b + 16 an >= dc -> Pendant, otherwise Après) must differ from the row's label.

Usage: python3.12 spotcheck.py <repo root> <out folder>
"""

import csv
import json
import os
import random
import sys

SEED = 20261020
K = 50
L751_1 = {"Guadeloupe", "Guyane", "Martinique", "LaReunion", "SaintBarthelemy", "SaintMartin"}

ROOT = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
BUILD = os.path.join(ROOT, "paperC", "catala_family_benefits")
sys.path.insert(0, os.path.join(BUILD, "runtime", "catala"))
sys.path.insert(0, BUILD)

from catala_runtime import (Array, Bool, Date, Duration, Integer, Money, Unit,  # noqa: E402
                            catala_set_lang, Lang)
import dates  # noqa: E402
from generated import Allocations_familiales as AF  # noqa: E402
from generated import France  # noqa: E402

catala_set_lang(Lang.Fr)
DC = Date(2020, 5, 1)

# Catala constructor names (spec representatives) -> generated Python constructor names
ASCII = {"LaRéunion": "LaReunion", "SaintBarthélemy": "SaintBarthelemy", "Métropole": "Metropole",
         "Après": "Apres",
         "GardeAlternéePartageAllocations": "GardeAlterneePartageAllocations",
         "GardeAlternéeAllocataireUnique": "GardeAlterneeAllocataireUnique",
         "ServicesSociauxAllocationVerséeÀLaFamille": "ServicesSociauxAllocationVerseeALaFamille",
         "ServicesSociauxAllocationVerséeAuxServicesSociaux": "ServicesSociauxAllocationVerseeAuxServicesSociaux"}


def py_name(catala_name):
    return ASCII.get(catala_name, catala_name)


def collectivite(rep):
    return France.Collectivite(getattr(France.Collectivite.Code, py_name(rep)), Unit())


def prise(rep):
    return AF.PriseEnCharge(getattr(AF.PriseEnCharge.Code, py_name(rep)), Unit())


def date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return Date(y, m, d)


def boolean(rep):
    return Bool({"vrai": True, "faux": False}[rep])


def derived_obligation(birth):
    """The encoding's own derivation (epilogue.catala_fr:121-131)."""
    if birth.__add__(Duration((3, 0, 0)), dates.DateRounding.AbortOnRound, None) >= DC:
        return "Avant"
    if birth.__add__(Duration((16, 0, 0)), dates.DateRounding.AbortOnRound, None) >= DC:
        return "Pendant"
    return "Apres"


# ------------------------------------------------------------ capture of locals

_captured = {}


def _profile(frame, event, arg):
    if event == "return" and frame.f_code is AF.allocations_familiales.__code__:
        _captured.clear()
        _captured.update(frame.f_locals)


def opt_value(o):
    return o.value[0] if (o is not None and o.value is not None) else None


def call_interface(children, ressources, residence, est_parent, titre_I, avant_2012):
    _captured.clear()
    sys.setprofile(_profile)
    try:
        out = AF.interface_allocations_familiales(AF.InterfaceAllocationsFamilialesIn(
            i_date_courante_in=DC,
            i_enfants_in=Array(children),
            i_ressources_menage_in=Money(ressources),
            i_residence_in=collectivite(residence),
            i_personne_charge_effective_permanente_est_parent_in=boolean(est_parent),
            i_personne_charge_effective_permanente_remplit_titre_I_in=boolean(titre_I),
            i_avait_enfant_a_charge_avant_1er_janvier_2012_in=boolean(avant_2012),
        ))
        err = None
    except Exception as exc:  # Catala runtime errors (AssertionFailed, ...)
        out, err = None, "%s" % type(exc).__name__
    finally:
        sys.setprofile(None)
    cap = dict(_captured)
    info = {}
    eo = opt_value(cap.get("enfants_a_charge_droit_ouvert_prestation_familiale"))
    info["n_droit_ouvert"] = len(eo) if eo is not None else None
    for k in ("plafond_i_d521_3", "plafond_i_i_d521_3", "montant_verse_base", "montant_verse_majoration",
              "montant_verse_forfaitaire", "montant_verse_complement_pour_base_et_majoration",
              "montant_verse_complement_pour_forfaitaire"):
        v = opt_value(cap.get(k))
        info[k] = int(v) if v is not None else None  # cents
    return (int(out.i_montant_verse) if out is not None else None), err, info


# ------------------------------------------------------------ samples


def rep_of(spec, name, label):
    for a in spec["attributes"]:
        if a["name"] == name:
            return a["representative"][label]
    raise KeyError(name)


def fixed_value(spec, key):
    return spec["fixed_inputs"][key]["value"]


def eval_pf(spec, row):
    res_rep = rep_of(spec, "residence", row["residence"])
    rem_attr = [a for a in spec["attributes"] if a["name"] == "remuneration"][0]
    if row["remuneration"] == "eq_plafond":
        by = rem_attr["representative_by_residence"]["eq_plafond"]
        rem = by.get(row["residence"], by["otherwise"])
    else:
        rem = rem_attr["representative"][row["remuneration"]]
    birth = date(rep_of(spec, "age", row["age"]))
    enfant = AF.Enfant(
        identifiant=Integer(int(fixed_value(spec, "identifiant"))),
        obligation_scolaire=AF.SituationObligationScolaire(
            getattr(AF.SituationObligationScolaire.Code, py_name(rep_of(spec, "obligation_scolaire", row["obligation_scolaire"]))), Unit()),
        remuneration_mensuelle=Money(rem),
        date_de_naissance=birth,
        prise_en_charge=prise(rep_of(spec, "prise_en_charge", row["prise_en_charge"])),
        a_deja_ouvert_droit_aux_allocations_familiales=boolean(fixed_value(spec, "a_deja_ouvert_droit_aux_allocations_familiales")),
        beneficie_titre_personnel_aide_personnelle_logement=boolean(rep_of(spec, "apl", row["apl"])),
    )
    pf = AF.prestations_familiales(AF.PrestationsFamilialesIn(date_courante_in=DC, residence_in=collectivite(res_rep)))
    label = "entitled" if bool(pf.droit_ouvert(enfant)) else "not_entitled"
    derived = derived_obligation(birth)
    detail = "droit_ouvert=%s; obligation derived from birth %s = %s" % (bool(pf.droit_ouvert(enfant)), rep_of(spec, "age", row["age"]), derived)
    excluded_by_source = derived != row["obligation_scolaire"]
    return label, detail, excluded_by_source


def af_inputs(spec, row):
    names = [a["name"] for a in spec["attributes"]]
    fx = spec["fixed_inputs"]

    def get(name, fixed_key):
        if name in names:
            return rep_of(spec, name, row[name])
        return fx[fixed_key]["value"]

    slots = int(fx["child_slots"]["value"])
    children = []
    for k in range(1, slots + 1):
        age_label = row["enfant%d_age" % k]
        if age_label == "absent":
            continue
        ident = len(children)
        children.append(AF.EnfantEntree(
            d_identifiant=Integer(ident),
            d_remuneration_mensuelle=Money(get("enfant%d_remuneration" % k, "enfant_remuneration")),
            d_date_de_naissance=date(rep_of(spec, "enfant%d_age" % k, age_label)),
            d_prise_en_charge=prise(get("enfant%d_prise_en_charge" % k, "enfant_prise_en_charge")),
            d_a_deja_ouvert_droit_aux_allocations_familiales=boolean(get("enfant%d_deja_ouvert" % k, "enfant_deja_ouvert")),
            d_beneficie_titre_personnel_aide_personnelle_logement=boolean(get("enfant%d_apl" % k, "enfant_apl")),
        ))
    residence_label = row["residence"] if "residence" in names else fx["residence"]["label"]
    residence_rep = get("residence", "residence")
    res_label = row["ressources"] if "ressources" in names else fx["ressources"]["label"]
    flags = (get("est_parent", "est_parent"), get("titre_I", "titre_I"),
             get("avait_enfant_avant_2012", "avait_enfant_avant_2012"))
    return children, residence_label, residence_rep, res_label, flags


def resources_value(spec, res_label, p1, p2):
    """Concrete resources for a band label (CONVERSION.md A5, spec representative strings)."""
    names = [a["name"] for a in spec["attributes"]]
    if "ressources" in names:
        rep = rep_of(spec, "ressources", res_label)
    else:
        rep = spec["fixed_inputs"]["ressources"]["value"]
    if rep == "plafond_I(n)":
        return "%d.%02d" % divmod(p1, 100)
    if rep == "plafond_II(n)":
        return "%d.%02d" % divmod(p2, 100)
    if rep == "(plafond_I(n) + plafond_II(n)) / 2":
        mid_euros = ((p1 + p2) // 2) // 100  # rounded down to the euro
        return "%d.00" % mid_euros
    return rep


def eval_af(spec, row):
    children, residence_label, residence_rep, res_label, flags = af_inputs(spec, row)
    # first pass: the ceilings and n do not depend on the resources
    amt, err, info = call_interface(children, "30000.00", residence_rep, *flags)
    p1, p2 = info["plafond_i_d521_3"], info["plafond_i_i_d521_3"]
    n = info["n_droit_ouvert"]
    statute_ok = (p1 == (5775900 + 577500 * n) and p2 == (8083100 + 577500 * n)) if (p1 is not None and n is not None) else None
    res_value = resources_value(spec, res_label, p1, p2) if p1 is not None else "30000.00"
    amt, err, info = call_interface(children, res_value, residence_rep, *flags)
    detail = "children=%d n_droit_ouvert=%s ressources=%s plafonds=%s/%s (statute formula %s) amount=%s err=%s comps=%s/%s/%s/%s/%s" % (
        len(children), n, res_value, p1, p2, statute_ok, amt, err,
        info["montant_verse_base"], info["montant_verse_majoration"], info["montant_verse_forfaitaire"],
        info["montant_verse_complement_pour_base_et_majoration"], info["montant_verse_complement_pour_forfaitaire"])
    if err is not None:
        return "REJECTED", detail
    if amt == 0:
        return "zero", detail
    out = spec["output"]["name"]
    if out == "composantes_montant_verse":
        parts = []
        if info["montant_verse_base"]:
            parts.append("base")
        if info["montant_verse_majoration"]:
            parts.append("majoration")
        if info["montant_verse_forfaitaire"]:
            parts.append("forfaitaire")
        if info["montant_verse_complement_pour_base_et_majoration"] or info["montant_verse_complement_pour_forfaitaire"]:
            parts.append("complement")
        return "_".join(parts), detail
    if residence_label == "Mayotte":
        return "mayotte", detail
    if residence_label in L751_1 and n == 1:
        return "outre_mer_1_enfant", detail
    r = int(Money(res_value))
    if r <= p1:
        return "general_t1", detail
    if r <= p2:
        return "general_t2", detail
    return "general_t3", detail


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for sid in ("FR-PF", "FR-AF-1", "FR-AF-2", "FR-AF-3"):
        folder = os.path.join(ROOT, "paperC", "specs", sid)
        with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
            spec = json.load(f)
        with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        idx = random.Random(SEED).sample(range(len(rows)), K)
        lines = []
        agree = 0
        for i in idx:
            row = rows[i]
            gt = row["output"]
            if sid == "FR-PF":
                label, detail, excl_src = eval_pf(spec, row)
                if gt == "EXCLUDED":
                    ok = excl_src
                    verdict = "agree (exclusion confirmed by the epilogue derivation)" if ok else "DISAGREE (derivation matches the label)"
                else:
                    ok = (label == gt) and not excl_src
                    verdict = "agree" if ok else "DISAGREE"
                detail += "; encoding label %s" % label
            else:
                label, detail = eval_af(spec, row)
                ok = label == gt
                verdict = "agree" if ok else "DISAGREE"
            agree += ok
            cond = ",".join(row[k] for k in list(row)[:-1])
            lines.append([sid, i, i + 2, cond, gt, label, int(ok), verdict, detail])
        with open(os.path.join(OUT, "spotcheck_%s.csv" % sid), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["sample", "row_index", "file_line", "condition", "ground_truth", "verifier_label", "agree", "verdict", "detail"])
            w.writerows(lines)
        summary.append((sid, agree, K, sorted(idx)))
        print(sid, "agree %d/%d" % (agree, K))
    with open(os.path.join(OUT, "spotcheck_indices.txt"), "w", encoding="utf-8") as f:
        for sid, a, k, idx in summary:
            f.write("%s (agree %d/%d) row indices (0-based data rows): %s\n" % (sid, a, k, " ".join(map(str, idx))))


def full_pf():
    """Extra check beyond the 50-row draw: every row of FR-PF through the adapter."""
    folder = os.path.join(ROOT, "paperC", "specs", "FR-PF")
    with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    bad = []
    for i, row in enumerate(rows):
        label, detail, excl_src = eval_pf(spec, row)
        gt = row["output"]
        ok = excl_src if gt == "EXCLUDED" else (label == gt and not excl_src)
        if not ok:
            bad.append((i, gt, label, detail))
    with open(os.path.join(OUT, "full_FR-PF.txt"), "w", encoding="utf-8") as f:
        f.write("FR-PF full enumeration through the verifier adapter: %d rows, %d disagreements\n" % (len(rows), len(bad)))
        for b in bad:
            f.write("%r\n" % (b,))
    print("FR-PF full:", len(rows), "rows,", len(bad), "disagreements")


def extended(sid, k, seed):
    """Supplementary larger draw (beyond the prescribed 50 rows)."""
    folder = os.path.join(ROOT, "paperC", "specs", sid)
    with open(os.path.join(folder, "spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    with open(os.path.join(folder, "ground_truth.csv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    idx = random.Random(seed).sample(range(len(rows)), k)
    bad, counts = [], {}
    for i in idx:
        row = rows[i]
        label, detail = eval_af(spec, row)
        counts[row["output"]] = counts.get(row["output"], 0) + 1
        if label != row["output"]:
            bad.append((i, row["output"], label, detail))
    with open(os.path.join(OUT, "extended_%s.txt" % sid), "w", encoding="utf-8") as f:
        f.write("%s supplementary draw: random.Random(%d).sample(range(%d), %d); %d disagreements\n" % (sid, seed, len(rows), k, len(bad)))
        f.write("ground-truth labels drawn: %s\n" % ", ".join("%s %d" % kv for kv in sorted(counts.items())))
        for b in bad:
            f.write("%r\n" % (b,))
    print(sid, "extended:", k, "rows,", len(bad), "disagreements")


if __name__ == "__main__":
    if sys.argv[3:4] == ["--extended"]:
        extended(sys.argv[4], int(sys.argv[5]), int(sys.argv[6]))
    elif sys.argv[3:] == ["--full-pf"]:
        full_pf()
    else:
        main()
