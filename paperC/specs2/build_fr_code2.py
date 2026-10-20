#!/usr/bin/env python3
"""Build the second-coder French samples under paperC/specs2/ (FR-PF, FR-AF-1..3).

  python build_fr_code2.py spec       write spec.json (output values left empty) and oracle.py copies
  python build_fr_code2.py outputs    fill output.values from ground_truth.csv and official_examples.csv
  python build_fr_code2.py sums       write SHA256SUMS in every folder

The full sequence is in README-FR-CODE2.md. Standard library only.
"""

import csv
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IDS = ["FR-PF", "FR-AF-1", "FR-AF-2", "FR-AF-3"]
SRC = "allocations_familiales/"

SOURCE = {
    "repository": "https://github.com/CatalaLang/catala-examples",
    "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
    "files": [SRC + f for f in ("prologue.catala_fr", "epilogue.catala_fr", "autres_codes.catala_fr",
                                 "securite_sociale_L.catala_fr", "securite_sociale_R.catala_fr",
                                 "securite_sociale_D.catala_fr", "decrets_divers.catala_fr",
                                 "tests/tests_ouverture_droits.catala_fr",
                                 "tests/tests_allocations_familiales.catala_fr")]
             + ["prologue_france/France.catala_fr", "smic/Smic.catala_fr",
                "base_mensuelle_allocations_familiales/Bmaf.catala_fr"],
}

RESIDENCE = {
    "name": "residence", "kind": "enum", "values": ["metropole", "drom_l751_1", "mayotte"],
    "representative": {"metropole": "Métropole", "drom_l751_1": "Guadeloupe", "mayotte": "Mayotte"},
    "source": "prologue_france/France.catala_fr:9-18 (Collectivité); L751-1 securite_sociale_L.catala_fr:376-385; "
              "smic/Smic.catala_fr:81-112 (SMIC 2020: Mayotte apart); Mayotte rules decrets_divers.catala_fr:181-238, 286-569. "
              "metropole = {Métropole, SaintPierreEtMiquelon}; drom_l751_1 = {Guadeloupe, Guyane, Martinique, LaRéunion, "
              "SaintBarthélemy, SaintMartin}; mayotte = {Mayotte}",
}
BOOL_REP = {"false": "faux", "true": "vrai"}

AGE_VALUES = ["moins_3", "3_11", "11_14", "14_16", "anniversaire_16", "16_19", "19_20", "20_23", "23_plus"]
AGE_REP = {"moins_3": "2019-05-01", "3_11": "2013-05-01", "11_14": "2008-05-01", "14_16": "2005-05-01",
           "anniversaire_16": "2004-05-01", "16_19": "2002-05-01", "19_20": "2000-11-01",
           "20_23": "1999-05-01", "23_plus": "1995-05-01"}
AGE_SOURCE = ("date_de_naissance, banded at date_courante 2020-05-01 by every comparison the code makes: "
              "+3 an >= (epilogue.catala_fr:123, L131-1), +11 an <= (securite_sociale_D.catala_fr:419, D755-5), "
              "+14 an <= (securite_sociale_R.catala_fr:54 with securite_sociale_L.catala_fr:319, R521-1/L521-3), "
              "+16 an >= (epilogue.catala_fr:127) and +16 an > / <= (securite_sociale_D.catala_fr:420, 431), "
              "(+20 an) - date < 365 jour (securite_sociale_L.catala_fr:149-151, L521-1), +20 an > "
              "(securite_sociale_L.catala_fr:71, R512-2 securite_sociale_R.catala_fr:21), "
              "+11 an <= 2008-04-30 (securite_sociale_R.catala_fr:81). Representative = birth date")
REM_VALUES = ["jusqu_plafond_mayotte", "entre_plafonds", "au_dessus_plafonds"]
REM_REP = {"jusqu_plafond_mayotte": "0.00", "entre_plafonds": "800.00", "au_dessus_plafonds": "1500.00"}
REM_SOURCE = ("rémuneration_mensuelle (EUR/month) cut at the two values of plafond_l512_3_2 at 2020-05-01: "
              "711.49 (Mayotte) and 943.02 (all others) = (smic.brut_horaire * 55%) * 169 "
              "(R512-2 securite_sociale_R.catala_fr:29-31, R755-0-2 securite_sociale_R.catala_fr:218-223, "
              "smic/Smic.catala_fr:81-112), compared with <= in L512-3 securite_sociale_L.catala_fr:70 and 83. "
              "Bands: [0, 711.49], (711.49, 943.02], (943.02, +inf)")
PRISE = {"kind": "enum", "values": ["complete", "partagee", "services_sociaux"],
         "representative": {"complete": "EffectiveEtPermanente", "partagee": "GardeAlternéePartageAllocations",
                            "services_sociaux": "ServicesSociauxAllocationVerséeAuxServicesSociaux"},
         "source": "PriseEnCharge prologue.catala_fr:10-15, grouped by prise_en_compte (L521-2 "
                   "securite_sociale_L.catala_fr:188-197, 209-231, 262-281): complete = {EffectiveEtPermanente, "
                   "GardeAlternéeAllocataireUnique, ServicesSociauxAllocationVerséeÀLaFamille} (Complète), "
                   "partagee = {GardeAlternéePartageAllocations} (Partagée), services_sociaux = "
                   "{ServicesSociauxAllocationVerséeAuxServicesSociaux} (Zéro)"}
DEJA = {"kind": "bool", "values": ["false", "true"], "representative": BOOL_REP,
        "source": "a_déjà_ouvert_droit_aux_allocations_familiales, read only by the forfaitaire, L521-1 "
                  "securite_sociale_L.catala_fr:153"}
APL = {"kind": "bool", "values": ["false", "true"], "representative": BOOL_REP,
       "source": "bénéficie_titre_personnel_aide_personnelle_logement, L821-3 autres_codes.catala_fr:22-26"}
RESSOURCES = {
    "name": "ressources", "kind": "interval",
    "values": ["jusqu_plafond_I", "zone_degressive_I", "entre_plafonds_I_II", "zone_degressive_II", "au_dela_plafond_II"],
    "representative": {"jusqu_plafond_I": "30000.00", "zone_degressive_I": "plafond_I_d521_3 + 1.00",
                       "entre_plafonds_I_II": "plafond_II_d521_3", "zone_degressive_II": "plafond_II_d521_3 + 1.00",
                       "au_dela_plafond_II": "200000.00"},
    "source": "ressources_ménage (EUR/year) relative to plafond_I_d521_3 = 57759 + 5775 n and plafond_II_d521_3 = "
              "80831 + 5775 n at 2020 (decrets_divers.catala_fr:102-123), n = enfants with droit ouvert; tiers "
              "D521-1 securite_sociale_D.catala_fr:35, 76-78, 120; zones of the complément dégressif "
              "securite_sociale_D.catala_fr:169-185 and 277-308: zone_degressive_X = (plafond_X, plafond_X + 12 a], "
              "a = max(montant_versé_base + montant_versé_majoration, montant_versé_forfaitaire). plafond_* in a "
              "representative is the value the encoding computes for the household",
}
AVANT = {"name": "avant_2012", "kind": "bool", "values": ["false", "true"], "representative": BOOL_REP,
         "source": "avait_enfant_à_charge_avant_1er_janvier_2012, read only for Mayotte, decrets_divers.catala_fr:"
                   "295-407 (décret 2002-423 annexe)"}
ATTRIBUTAIRE = {"name": "attributaire", "kind": "enum", "values": ["parent", "tiers_titre_I", "aucun"],
                "representative": {"parent": "est_parent = vrai, remplit_titre_I = faux",
                                   "tiers_titre_I": "est_parent = faux, remplit_titre_I = vrai",
                                   "aucun": "est_parent = faux, remplit_titre_I = faux"},
                "source": "personne_charge_effective_permanente_est_parent / _remplit_titre_I, L521-2 "
                          "securite_sociale_L.catala_fr:240-246, epilogue.catala_fr:91-96"}

FIXED_COMMON = {
    "date_courante": {"value": "2020-05-01",
                      "why": "date of the PrestationsFamiliales test and of 7 of the 14 household tests; all "
                             "date-dependent parameters (BMAF Bmaf.catala_fr:52-58, SMIC Smic.catala_fr:81-112, "
                             "plafonds decrets_divers.catala_fr:102-123, Mayotte 2020 rates decrets_divers.catala_fr:"
                             "389-398, 481-487, 562-568) are constant on 2020-04-01..2020-12-31"},
}


def child_attrs(j, fields):
    out = []
    for f in fields:
        if f == "age":
            out.append({"name": f"e{j}_age", "kind": "interval", "values": AGE_VALUES, "representative": AGE_REP,
                        "source": AGE_SOURCE})
        elif f == "remuneration":
            out.append({"name": f"e{j}_remuneration", "kind": "interval", "values": REM_VALUES,
                        "representative": REM_REP, "source": REM_SOURCE})
        elif f == "prise_en_charge":
            out.append({"name": f"e{j}_prise_en_charge", **PRISE})
        elif f == "deja_ouvert":
            out.append({"name": f"e{j}_deja_ouvert", **DEJA})
        elif f == "aide_logement":
            out.append({"name": f"e{j}_aide_logement", **APL})
    return out


AF_OUTPUT_SOURCE = ("regime of montant_versé (epilogue.catala_fr:45-52), read from the components the encoding "
                    "computes: 'sans_droit' when droit_ouvert_base is false (L521-1 securite_sociale_L.catala_fr:"
                    "124-127, L755-12 :436-442, Mayotte decrets_divers.catala_fr:191-194); otherwise "
                    "bareme/tier/parts with bareme general (D521-1), outre_mer_un_enfant (D755-5 securite_sociale_D."
                    "catala_fr:384-433, no tier), mayotte or mayotte_avant_2012 (decrets_divers.catala_fr:181-407); "
                    "tier T1/T2/T3 = ressources vs plafond_I/II (D521-1, D521-2); parts = non-zero components among "
                    "B base, M majorations, F forfaitaire, C complément dégressif (base or forfaitaire), or 'nul'")


def af_spec(sid, n, household, child_fields, fixed_child, notes):
    attrs = []
    for h in household:
        attrs.append({"residence": RESIDENCE, "attributaire": ATTRIBUTAIRE, "ressources": RESSOURCES,
                      "avant_2012": AVANT}[h])
    for j in range(1, n + 1):
        attrs += child_attrs(j, child_fields)
    fixed = dict(FIXED_COMMON)
    fixed["nombre_enfants"] = {"value": str(n), "why": "this sub-table holds households with exactly %d child(ren) "
                                                       "in i_enfants" % n}
    if "attributaire" not in household:
        fixed["personne_charge_effective_permanente_est_parent"] = {
            "value": "vrai", "why": "set in every official test; read only by the L521-2 assertion "
                                    "(securite_sociale_L.catala_fr:240-246); varied in FR-AF-1"}
        fixed["personne_charge_effective_permanente_remplit_titre_I"] = {"value": "faux", "why": "as above"}
    fixed.update(fixed_child)
    fixed["d_identifiant"] = {"value": "1..%d in list order" % n, "why": "only used to tell apart children "
                                                                          "with equal birth dates (EnfantLePlusÂgé)"}
    excl = []
    if "attributaire" in household:
        excl.append({"id": "X-AF-ATTRIB", "description": "the person in charge is neither a parent nor a person "
                     "meeting Title I: outside the domain the encoding asserts",
                     "predicate": "attributaire == 'aucun'",
                     "source": "L521-2 assertion securite_sociale_L.catala_fr:240-246"})
    return {
        "id": sid,
        "title": f"Allocations familiales, household with {n} child{'ren' if n > 1 else ''}: amount regime "
                 f"(second coder)",
        "source": dict(SOURCE, entry_point="InterfaceAllocationsFamiliales (Python: generated.Allocations_familiales."
                                           "interface_allocations_familiales); components read from scope "
                                           "AllocationsFamiliales"),
        "attributes": attrs,
        "output": {"name": "regime_montant", "values": [], "source": AF_OUTPUT_SOURCE},
        "exclusions": excl,
        "fixed_inputs": fixed,
        "notes": notes,
    }


def pf_spec():
    return {
        "id": "FR-PF",
        "title": "Prestations familiales: per-child entitlement droit_ouvert (second coder)",
        "source": dict(SOURCE, entry_point="PrestationsFamiliales.droit_ouvert (Python: generated.Allocations_familiales."
                                           "prestations_familiales(...).droit_ouvert)"),
        "attributes": [
            dict(RESIDENCE),
            {"name": "obligation_scolaire", "kind": "enum", "values": ["Avant", "Pendant", "Apres"],
             "representative": {"Avant": "Avant", "Pendant": "Pendant", "Apres": "Après"},
             "source": "SituationObligationScolaire prologue.catala_fr:17-20; L512-3 securite_sociale_L.catala_fr:52-72"},
            {"name": "remuneration_mensuelle", "kind": "interval", "values": REM_VALUES, "representative": REM_REP,
             "source": REM_SOURCE},
            {"name": "age_20_ans", "kind": "interval", "values": ["moins_20", "20_ou_plus"],
             "representative": {"moins_20": "2005-01-01", "20_ou_plus": "1998-01-01"},
             "source": "date_de_naissance vs date_courante: moins_20 iff date_de_naissance + 20 an > date_courante "
                       "(L512-3 securite_sociale_L.catala_fr:71; R512-2 securite_sociale_R.catala_fr:21). "
                       "Representative = birth date"},
            {"name": "aide_logement_personnelle", **APL},
        ],
        "output": {"name": "droit_ouvert", "values": ["ouvert", "non_ouvert"],
                   "source": "droit_ouvert, L512-3 securite_sociale_L.catala_fr:52-72 with the L821-3 exception "
                             "autres_codes.catala_fr:22-26"},
        "exclusions": [
            {"id": "X-PF-SCOL", "description": "a child aged 20 or more cannot be before or within compulsory "
             "schooling, which ends at 16",
             "predicate": "obligation_scolaire in ('Avant', 'Pendant') and age_20_ans == '20_ou_plus'",
             "source": "Code de l'éducation L131-1 as encoded in epilogue.catala_fr:113-136"},
        ],
        "fixed_inputs": dict(FIXED_COMMON, **{
            "prise_en_charge": {"value": "EffectiveEtPermanente", "why": "not read by droit_ouvert"},
            "a_déjà_ouvert_droit_aux_allocations_familiales": {"value": "vrai", "why": "not read by droit_ouvert"},
            "identifiant": {"value": "1", "why": "not read by droit_ouvert"},
        }),
        "notes": "Second, blinded conversion (see ../README-FR-CODE2.md). Interpretive choices with sources are in "
                 "CONVERSION_2.md. Grouped residence labels were checked member by member (oracle.py --check-groups).",
    }


FIXED_REM0 = {"d_rémuneration_mensuelle": {"value": "0.00", "why": "fixed in this sub-table; varied in FR-AF-1 and "
                                                                   "FR-AF-2"}}
FIXED_PRISE = {"d_prise_en_charge": {"value": "EffectiveEtPermanente", "why": "fixed in this sub-table; varied in "
                                                                             "FR-AF-1 and FR-AF-2"}}
FIXED_DEJA = {"d_a_déjà_ouvert_droit_aux_allocations_familiales": {
    "value": "vrai", "why": "read only by the forfaitaire, which needs 3 or more children (L521-1 "
                            "securite_sociale_L.catala_fr:143); no effect with fewer than 3 children"}}
FIXED_APL = {"d_bénéficie_titre_personnel_aide_personnelle_logement": {
    "value": "faux", "why": "fixed in this sub-table; varied in FR-AF-1 and FR-PF"}}


def specs():
    common_note = ("Second, blinded conversion (see ../README-FR-CODE2.md). Sub-table of the household allowance "
                   "split by number of children. Interpretive choices with sources are in CONVERSION_2.md.")
    return {
        "FR-PF": pf_spec(),
        "FR-AF-1": af_spec("FR-AF-1", 1, ["residence", "attributaire", "ressources", "avant_2012"],
                           ["age", "remuneration", "prise_en_charge", "deja_ouvert", "aide_logement"], {},
                           common_note),
        "FR-AF-2": af_spec("FR-AF-2", 2, ["residence", "ressources", "avant_2012"],
                           ["age", "remuneration", "prise_en_charge"], {**FIXED_DEJA, **FIXED_APL}, common_note),
        "FR-AF-3": af_spec("FR-AF-3", 3, ["residence", "ressources", "avant_2012"],
                           ["age", "deja_ouvert"], {**FIXED_REM0, **FIXED_PRISE, **FIXED_APL}, common_note),
    }


BAREMES = ["general", "outre_mer_un_enfant", "mayotte", "mayotte_avant_2012"]
PARTS = ["nul", "B", "B+M", "B+F", "B+C", "B+M+F", "B+M+C", "B+F+C", "B+M+F+C",
         "M", "M+F", "M+C", "M+F+C", "F", "F+C", "C"]


def label_key(lab):
    if lab == "sans_droit":
        return (0,)
    p = lab.split("/")
    tier = p[1] if len(p) == 3 else ""
    return (1, BAREMES.index(p[0]), tier, PARTS.index(p[-1]))


def fill_outputs(sid):
    path = os.path.join(HERE, sid, "spec.json")
    spec = json.load(open(path, encoding="utf-8"))
    if sid == "FR-PF":
        return
    labels = set()
    for fn in ("ground_truth.csv", "official_examples.csv"):
        with open(os.path.join(HERE, sid, fn), encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["output"] not in ("EXCLUDED", "REJECTED"):
                    labels.add(row["output"])
    spec["output"]["values"] = sorted(labels, key=label_key)
    write_json(path, spec)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_sums(sid):
    folder = os.path.join(HERE, sid)
    lines = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for fn in sorted(files):
            if fn == "SHA256SUMS" or fn.endswith(".pyc"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, folder).replace(os.sep, "/")
            lines.append(f"{hashlib.sha256(open(p, 'rb').read()).hexdigest()}  {rel}")
    with open(os.path.join(folder, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(lines, key=lambda s: s[66:])) + "\n")


def print_stats(sid):
    spec = json.load(open(os.path.join(HERE, sid, "spec.json"), encoding="utf-8"))
    gt = list(csv.DictReader(open(os.path.join(HERE, sid, "ground_truth.csv"), encoding="utf-8")))
    off = list(csv.DictReader(open(os.path.join(HERE, sid, "official_examples.csv"), encoding="utf-8")))
    n_ex = sum(r["output"] == "EXCLUDED" for r in gt)
    n_rej = sum(r["output"] == "REJECTED" for r in gt)
    sizes = " x ".join(str(len(a["values"])) for a in spec["attributes"])
    print(f"### {sid}\n")
    print(f"* attributes: {len(spec['attributes'])}; declared space {sizes} = {len(gt)}")
    print(f"* valid {len(gt) - n_ex - n_rej}, EXCLUDED {n_ex}, REJECTED {n_rej}")
    print(f"* output labels declared: {len(spec['output']['values'])}; occurring in valid rows: "
          f"{len({r['output'] for r in gt} - {'EXCLUDED', 'REJECTED'})}")
    print(f"* official examples: {len(off)} rows")
    unused = []
    for a in spec["attributes"]:
        seen = {r[a["name"]] for r in off}
        miss = [v for v in a["values"] if v not in seen]
        if miss:
            unused.append(f"  * `{a['name']}`: {', '.join(miss)} ({len(miss)}/{len(a['values'])})")
    total = sum(len([v for v in a["values"] if v not in {r[a['name']] for r in off}]) for a in spec["attributes"])
    print(f"* declared attribute values never used by the official examples: {total}")
    print("\n".join(unused))
    outs = [v for v in spec["output"]["values"] if v not in {r["output"] for r in off}]
    print(f"* output labels never used by the official examples: {len(outs)} of {len(spec['output']['values'])}\n")


def main(argv):
    if argv[:1] == ["spec"]:
        src = open(os.path.join(HERE, "FR-PF", "oracle.py"), encoding="utf-8").read()
        for sid, spec in specs().items():
            os.makedirs(os.path.join(HERE, sid), exist_ok=True)
            write_json(os.path.join(HERE, sid, "spec.json"), spec)
            if sid != "FR-PF":
                with open(os.path.join(HERE, sid, "oracle.py"), "w", encoding="utf-8", newline="\n") as f:
                    f.write(re.sub(r'^SAMPLE_ID = ".*"$', f'SAMPLE_ID = "{sid}"', src, count=1, flags=re.M))
    elif argv[:1] == ["outputs"]:
        for sid in IDS:
            fill_outputs(sid)
    elif argv[:1] == ["stats"]:
        for sid in IDS:
            print_stats(sid)
    elif argv[:1] == ["sums"]:
        for sid in IDS:
            write_sums(sid)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
