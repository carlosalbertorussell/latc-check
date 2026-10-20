#!/usr/bin/env python3
"""Cross-check ground_truth.csv rows of the FR-APL and US-121 tables with the Catala interpreter.

For a sample of rows of each table, this script writes Catala test files in which each
row is one #[test] scope with the same inputs as the oracle and an assertion stating
the ground-truth output. `clerk test` (Catala 1.3.0 interpreter, no Python involved)
then runs them; the script reads clerk's verbose report and checks that:

  * every row whose ground truth is a label passes its assertion, and
  * every REJECTED row fails with a Catala runtime error ("During evaluation"; a
    failed assertion counts as a disagreement), with the error position reported by clerk.

Usage (from a catala-examples checkout at commit 2694b17 with Catala 1.3.0 on PATH):

  python3 interpreter_crosscheck.py write <catala-examples dir> [rows per table]
  (cd <catala-examples dir> && clerk test $(cat xcheck_files.txt) --verbose --color=never > report.txt 2>&1)
  python3 interpreter_crosscheck.py read <catala-examples dir>/report.txt

The sample is drawn with random.Random(2026) (all rows when a table has fewer valid
rows than the sample size). EXCLUDED rows are not run.
"""

import csv
import importlib.util
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.normpath(os.path.join(HERE, "..", "specs"))
TABLES = [("FR-APL", f"FR-APL-{i}") for i in range(1, 6)] + [("US-121", "US-121-1"), ("US-121", "US-121-2")]


def load_oracle(group, table):
    path = os.path.join(SPECS, group, table, "oracle.py")
    spec = importlib.util.spec_from_file_location(f"oracle_{table.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------ Catala literals (French)

def b(v):
    return "vrai" if v else "faux"


def dec(s):
    return s.replace(".", ",") if "." in s else s + ",0"


def money_fr(s):
    return f"{s} €"


def nationalite_fr(n):
    if n[0] == "Francaise":
        return "AL.Nationalité.Française"
    return ("AL.Nationalité.Étrangère contenu (AL.ConditionsÉtrangers { "
            f"-- satisfait_conditions_l512_2_code_sécurité_sociale: {b(n[1])} "
            f"-- satisfait_art_4_ordonnance_2002_mayotte: {b(n[2])} }})")


COLLECTIVITE = {"Metropole": "Métropole", "LaReunion": "LaRéunion", "SaintBarthelemy": "SaintBarthélemy"}
SITUATION = {"Celibataire": "Célibataire", "Pacses": "Pacsés", "CelibataireSepareDeFait": "CélibataireSéparéDeFait",
             "ConcubinageDontSepareDeFait": "ConcubinageDontSéparéDeFait"}
PRESTATION = {"AllocationSoutienEnfantHandicape": "AllocationSoutienEnfantHandicapé",
              "ComplementFamilial": "ComplémentFamilial"}
TYPE_FOYER = {"LogementPersonnesAgeesOuHandicapees": "LogementPersonnesÂgéesOuHandicapées",
              "ResidenceSociale": "RésidenceSociale",
              "FoyerJeunesTravailleursOuMigrantsConventionneL353_2Avant1995":
                  "FoyerJeunesTravailleursOuMigrantsConventionnéL353_2Avant1995"}
MODE = {"ResidentLogementFoyer": "RésidentLogementFoyer",
        "AccessionProprieteLocalUsageExclusifHabitation": "AccessionPropriétéLocalUsageExclusifHabitation"}
OBLIGATION = {"Apres": "Après"}


def bailleur_fr(bl):
    if bl[0] == "BailleurSocial":
        return ("AL.TypeBailleur.BailleurSocial contenu (AL.ConventionBailleurSocial { "
                f"-- conventionné_livre_III_titre_V_chap_III: {b(bl[1])} -- réduction_loyer_solidarité_perçue: 0 € }})")
    if bl[0] == "BailleurPriveAvecConventionnementSocial":
        return ("AL.TypeBailleur.BailleurPrivéAvecConventionnementSocial contenu (AL.ConventionANHA { "
                f"-- conventionné_livre_III_titre_II_chap_I_sec_3: {b(bl[1])} }})")
    return "AL.TypeBailleur.BailleurPrivé"


def mode_fr(raw):
    mode = raw["mode"]
    name = MODE.get(mode, mode)
    if mode in ("Locataire", "SousLocataire"):
        content = ("AL.Location { "
                   f"-- bailleur: {bailleur_fr(raw['bailleur'])} -- loyer_principal: {money_fr(raw['loyer'])} "
                   "-- bénéficiaire_aide_adulte_ou_enfant_handicapés: faux -- logement_est_chambre: faux "
                   "-- colocation: faux -- âgées_ou_handicap_adultes_hébergées_onéreux_particuliers: faux "
                   "-- logement_meublé_d842_2: faux -- changement_logement_d842_4: AL.ChangementLogementD842_4.PasDeChangement }")
    elif mode == "ResidentLogementFoyer":
        f = raw["foyer"]
        content = ("AL.LogementFoyer { "
                   f"-- type_logement: AL.TypeLogementFoyer.{TYPE_FOYER.get(f['type'], f['type'])} "
                   "-- logement_foyer_jeunes_travailleurs: faux "
                   f"-- remplit_conditions_r832_21: {b(f['remplit_r832_21'])} "
                   f"-- conventionné_livre_III_titre_V_chap_III: {b(f['conventionne_livre_III'])} "
                   f"-- conventionné_selon_règles_drom: {b(f['conventionne_drom'])} "
                   "-- date_conventionnement: |2000-01-01| -- construit_application_loi_1957_12_III: faux "
                   "-- redevance: 400 € "
                   "-- catégorie_équivalence_loyer_d842_16: AL.CatégorieÉquivalenceLoyerAllocationLogementFoyer.AutresPersonnes "
                   "-- bénéficiaire_aide_adulte_ou_enfant_handicapés: faux -- logement_meublé_d842_2: faux "
                   "-- logement_est_chambre: faux -- colocation: faux }")
    else:
        p = raw["pret"]
        anc = ("AL.NeufOuAncien.Neuf" if p["anciennete"] == "Neuf" else
               "AL.NeufOuAncien.Ancien contenu AL.AmélioréParOccupant." + ("Oui" if p["anciennete"] == "AncienOui" else "Non"))
        content = ("AL.Propriétaire { -- mensualité_principale: 500 € -- charges_mensuelles_prêt: 0 € "
                   "-- date_entrée_logement: |2010-01-01| "
                   "-- type_travaux_logement_d832_15: AL.TypeTravauxLogementD832_15.PasDeTravaux "
                   "-- type_travaux_logement_r842_5: AL.TypeTravauxLogementR842_5.PasDeTravaux "
                   "-- local_habité_première_fois_bénéficiaire: faux -- copropriété: faux "
                   "-- situation_r822_11_13_17: faux "
                   f"-- ancienneté_logement: {anc} "
                   f"-- prêt: AL.Prêt {{ -- type_prêt: AL.TypePrêt.{p['type_pret']} "
                   f"-- date_signature: |{p['date_signature']}| -- titulaire_prêt: AL.TitulairePrêt.{p['titulaire']} "
                   "-- accord_financement_représentant_État_outre_mer: AL.AccordFinancementReprésentantÉtatOutreMer.PasdAccord } "
                   "-- opérations_logement_évolutifs_sociaux_accession_propriété_aidée_État: faux }")
    return f"AL.ModeOccupation.{name} contenu ({content})"


def parent_fr(parts):
    if parts is None:
        return "AL.ParentOuAutre.Autre"
    return f"AL.ParentOuAutre.DemandeurOuConjointOuParentOuViaPartsSociétés contenu {dec(parts)}"


def loue_fr(l):
    if l is None:
        return "AL.LouéOuSousLouéÀDesTiers.Non"
    return ("AL.LouéOuSousLouéÀDesTiers.Oui contenu (AL.PersonneSousLocation { "
            f"-- date_naissance_personne_sous_location: |{l[0]}| -- conforme_article_l442_1: {b(l[1])} }})")


def enfant_fr(e):
    return ("AL.PersonneÀCharge.EnfantÀCharge contenu (AL.EnfantÀCharge { "
            f"-- identifiant: {e['identifiant']} -- nationalité: AL.Nationalité.Française "
            "-- a_déjà_ouvert_droit_aux_allocations_familiales: vrai "
            f"-- date_de_naissance: |{e['date_de_naissance']}| -- rémuneration_mensuelle: 0 € "
            f"-- obligation_scolaire: Prestations_familiales.SituationObligationScolaire.{OBLIGATION.get(e['obligation_scolaire'], e['obligation_scolaire'])} "
            "-- situation_garde_alternée: AL.SituationGardeAlternée.PasDeGardeAlternée "
            f"-- études_apprentissage_stage_formation_pro_impossibilité_travail: {b(e['etudes'])} }})")


def apl_scope_fr(name, raw, expected):
    import fr_apl_common as F
    sit = raw["situation_familiale"]
    sit_lit = (f"AL.SituationFamiliale.Mariés contenu |{raw['date_mariage']}|" if sit == "Maries"
               else f"AL.SituationFamiliale.{SITUATION.get(sit, sit)}")
    enfants = "; ".join(enfant_fr(e) for e in F.EXEMPLE1_ENFANTS[:raw["n_enfants"]])
    prest = "; ".join(f"AL.PrestationReçue.{PRESTATION.get(p, p)}" for p in raw["prestations"])
    menage = (
        "AL.Ménage { "
        f"-- prestations_reçues: [{prest}] "
        "-- logement: AL.Logement { "
        f"-- résidence_principale: {b(raw['residence_principale'])} "
        f"-- mode_occupation: {mode_fr(raw)} "
        f"-- propriétaire: {parent_fr(raw['proprietaire_parts'])} "
        f"-- loué_ou_sous_loué_à_des_tiers: {loue_fr(raw['loue_tiers'])} "
        f"-- usufruit: {parent_fr(raw['usufruit_parts'])} "
        f"-- logement_decent_l89_462: {b(raw['decent'])} "
        f"-- surface_m_carrés: {raw['surface']} "
        f"-- zone: AL.ZoneDHabitation.{raw['zone']} }} "
        f"-- personnes_à_charge: [{enfants}] "
        f"-- nombre_autres_occupants_logement: {raw['autres_occupants']} "
        f"-- situation_familiale: {sit_lit} "
        f"-- condition_rattaché_foyer_fiscal_parent_ifi: {b(raw['ifi'])} "
        f"-- enfant_à_naître_après_quatrième_mois_grossesse: {b(raw['enfant_a_naitre'])} "
        f"-- personnes_âgées_handicapées_foyer_r844_4: {b(raw['r844_4'])} "
        f"-- résidence: France.Collectivité.{COLLECTIVITE.get(raw['residence'], raw['residence'])} }}")
    demandeur = (
        "AL.Demandeur { "
        f"-- date_naissance: |{raw['demandeur_naissance']}| -- nationalité: {nationalite_fr(raw['nationalite'])} "
        "-- personne_hébergée_centre_soin_l_L162_22_3_sécurité_sociale: faux "
        "-- est_non_salarié_agricole_l781_8_l_781_46_code_rural: faux "
        "-- magistrat_fonctionnaire_centre_intérêts_matériels_familiaux_hors_mayotte: faux }")
    assertion = "non éligible" if expected == "not_eligible" else "éligible"
    return (f"#[test]\ndéclaration champ d'application {name}:\n"
            f"  éligibilité champ d'application AL.ÉligibilitéAidePersonnaliséeLogement\n"
            f"  résultat éligible contenu booléen\n\n"
            f"champ d'application {name}:\n"
            f"  définition éligible égal à éligibilité.éligibilité\n"
            f"  assertion {assertion}\n"
            f"  définition éligibilité.date_courante égal à |{raw['date_courante']}|\n"
            f"  définition éligibilité.ménage égal à {menage}\n"
            f"  définition éligibilité.demandeur égal à {demandeur}\n\n")


# ------------------------------------------------------------ Catala literals (English)

def money_en(s):
    whole, _, frac = s.partition(".")
    whole = f"{int(whole):,}"
    return f"${whole}" + (f".{frac.ljust(2, '0')}" if frac else "")


def periods_en(pairs):
    return "[" + "; ".join(f"T.Period {{ -- begin: |{b_}| -- end: |{e}| }}" for b_, e in pairs) + "]"


def other_sale_en(prev):
    if prev is None:
        return "T.OtherSection121aSale.NoOtherSaleWhereSection121aApplied"
    return ("T.OtherSection121aSale.MostRecentSaleWhereSection121aApplied content "
            f"(T.PreviousSaleWhereSection121aApplied {{ -- date_of_sale_or_exchange: |{prev}| }})")


def personal_en(p):
    return (f"T.PersonalData {{ -- property_ownage: {periods_en(p['ownage'])} "
            f"-- property_usage_as_principal_residence: {periods_en(p['usage'])} "
            f"-- other_section_121a_sale: {other_sale_en(p['previous_sale'])} }}")


def us1_scope(name, raw, expected):
    assertion = "s.requirements_met" if expected == "requirements_met" else "not s.requirements_met"
    return (f"#[test]\ndeclaration scope {name}:\n  s scope T.Section121SinglePerson\n  output r content boolean\n\n"
            f"scope {name}:\n"
            f"  definition r equals s.requirements_met\n"
            f"  assertion {assertion}\n"
            f"  definition s.date_of_sale_or_exchange equals |{raw['date_of_sale']}|\n"
            f"  definition s.gain_from_sale_or_exchange_of_property equals {money_en(raw['gain'])}\n"
            f"  definition s.property_ownage equals {periods_en(raw['ownage'])}\n"
            f"  definition s.property_usage_as_principal_residence equals {periods_en(raw['usage'])}\n"
            f"  definition s.other_section_121a_sale equals {other_sale_en(raw['previous_sale'])}\n\n")


def us2_scope(name, raw, expected, gain_cap_note=None):
    kind = raw["return_type"]
    p1, p2 = personal_en(raw["p1"]), personal_en(raw["p2"])
    if kind == "single":
        rt = f"T.ReturnType.SingleReturn content ({p1})"
    elif kind == "joint":
        rt = f"T.ReturnType.JointReturn content (T.JointReturn {{ -- person1: {p1} -- person2: {p2} }})"
    else:
        rt = (f"T.ReturnType.SingleReturnSurvivingSpouse content (T.DeadSpouseInfo {{ -- return: {p1} "
              f"-- date_of_spouse_death: |2020-06-01| -- death_spouse_info_at_time_of_death: {p2} }})")
    gain = money_en(raw["gain"])
    cond = {
        "no_exclusion": "s.income_excluded_from_gross_income_uncapped = $0",
        "entire_gain": f"s.income_excluded_from_gross_income = {gain} and s.income_excluded_from_gross_income_uncapped > $0 and s.income_excluded_from_gross_income_uncapped < (if s.section_121_b_2_A_condition then $500,000 else $250,000)",
        "limited_to_250000": "s.income_excluded_from_gross_income = $250,000 and s.income_excluded_from_gross_income_uncapped >= $250,000 and not s.section_121_b_2_A_condition",
        "limited_to_500000": "s.income_excluded_from_gross_income = $500,000 and s.income_excluded_from_gross_income_uncapped >= $500,000 and s.section_121_b_2_A_condition",
    }.get(expected, "s.income_excluded_from_gross_income >= $0")
    return (f"#[test]\ndeclaration scope {name}:\n  s scope T.Section121TwoPersons\n  output r content money\n\n"
            f"scope {name}:\n"
            f"  definition r equals s.income_excluded_from_gross_income\n"
            f"  assertion {cond}\n"
            f"  definition s.date_of_sale_or_exchange equals |2021-01-01|\n"
            f"  definition s.return_date equals |2021-01-01|\n"
            f"  definition s.gain_from_sale_or_exchange_of_property equals {gain}\n"
            f"  definition s.return_type equals {rt}\n\n")


# ------------------------------------------------------------ driver

def sample(group, table, n):
    path = os.path.join(SPECS, group, table, "ground_truth.csv")
    with open(path, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["output"] != "EXCLUDED"]
    rng = random.Random(2026)
    picked = rows if len(rows) <= n else rng.sample(rows, n)
    # always keep every REJECTED row kind and every output label at least once
    seen = {r["output"] for r in picked}
    for r in rows:
        if r["output"] not in seen:
            picked.append(r)
            seen.add(r["output"])
    return picked


def write(examples_dir, n):
    sys.path.insert(0, HERE)
    fr = ["> Usage de France\n> Usage de Prestations_familiales\n> Usage de Aides_logement en tant que AL\n\n```catala\n"]
    us = ["> Using Us_tax_code as T\n\n```catala\n"]
    manifest = []
    for group, table in TABLES:
        mod = load_oracle(group, table)
        for i, row in enumerate(sample(group, table, n)):
            expected = row.pop("output")
            raw = mod.ORACLE.raw_of(row)
            name = "X" + table.replace("-", "") + f"_{i:04d}"
            if group == "FR-APL":
                fr.append(apl_scope_fr(name, raw, expected))
            elif table == "US-121-1":
                us.append(us1_scope(name, raw, expected))
            else:
                us.append(us2_scope(name, raw, expected))
            manifest.append({"scope": name, "table": table, "row": row, "expected": expected})
    # The interpreter's run time grows faster than linearly with the number of scopes in
    # one file, so the scopes are written in files of at most CHUNK scopes.
    CHUNK = 100
    names = []
    for kind, header, scopes, folder, ext in (
            ("fr_apl", fr[0], fr[1:], os.path.join("aides_logement", "tests"), "catala_fr"),
            ("us121", us[0], us[1:], os.path.join("us_tax_code", "tests"), "catala_en")):
        for k in range(0, len(scopes), CHUNK):
            rel = os.path.join(folder, f"xcheck_{kind}_{k // CHUNK:02d}.{ext}")
            with open(os.path.join(examples_dir, rel), "w", encoding="utf-8") as f:
                f.write(header + "".join(scopes[k:k + CHUNK]) + "```\n")
            names.append(rel)
    with open(os.path.join(examples_dir, "xcheck_files.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(names) + "\n")
    with open(os.path.join(examples_dir, "xcheck_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=0)
    print(f"wrote {len(manifest)} test scopes")


def read(report_path):
    examples_dir = os.path.dirname(os.path.abspath(report_path))
    with open(os.path.join(examples_dir, "xcheck_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    text = open(report_path, encoding="utf-8").read()
    # Each scope line is followed, when it failed, by the command and the error message
    # up to the next "■" line.
    status, message = {}, {}
    for m in re.finditer(r"■ scope (X\S+) (passed|failed)(.*?)(?=\n\s*■|\n__ |\n\n|\Z)", text, re.S):
        status[m.group(1)] = m.group(2)
        msg = " ".join(line.strip() for line in m.group(3).splitlines() if line.strip() and not line.strip().startswith("$"))
        message[m.group(1)] = msg
    by_table = {}
    bad = []
    errors = {}
    for m in manifest:
        st = status.get(m["scope"])
        msg = message.get(m["scope"], "")
        t = by_table.setdefault(m["table"], {"rows": 0, "label_pass": 0, "rejected_fail": 0, "mismatch": 0})
        t["rows"] += 1
        if m["expected"] == "REJECTED":
            # a runtime error of the encoding, not a failure of the row's own assertion
            ok = st == "failed" and "During evaluation" in msg and "ssertion" not in msg
            t["rejected_fail"] += ok
            key = re.sub(r"^.*?(\S+\.catala_\w+:[\d.-]+) During evaluation: ", r"\1: ", msg)
            errors[(m["table"], key)] = errors.get((m["table"], key), 0) + 1
        else:
            ok = st == "passed"
            t["label_pass"] += ok
        if not ok:
            t["mismatch"] += 1
            bad.append((m["scope"], m["table"], m["expected"], st, msg[:200]))
    for table, t in by_table.items():
        print(f"{table}: {t['rows']} rows run; label rows passing their assertion: {t['label_pass']}; "
              f"REJECTED rows raising a runtime error in the interpreter: {t['rejected_fail']}; "
              f"disagreements: {t['mismatch']}")
    for b_ in bad[:50]:
        print("  disagreement:", b_)
    if errors:
        print("interpreter errors of the REJECTED rows:")
        for (table, key), n in sorted(errors.items()):
            print(f"  {table}: {n} x {key}")
    return 0 if not bad else 1


if __name__ == "__main__":
    if sys.argv[1] == "write":
        write(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 300)
    elif sys.argv[1] == "read":
        sys.exit(read(sys.argv[2]))
