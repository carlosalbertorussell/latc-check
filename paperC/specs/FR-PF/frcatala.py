"""Shared engine for the French family-benefits (Catala) specs of Paper C.

The same file is copied, byte for byte, into every FR-* spec folder so that each
folder runs on its own. It holds:

* access to the Catala 1.3.0 Python build in paperC/catala_family_benefits
  (generated/ + runtime/), resolved relative to this file;
* the age bands, earnings bands and resource bands used by the specs, each
  defined by the exact comparison the encoding performs;
* the label function of the FR-AF tables (amount regime of montant_versé);
* generic --enumerate / --check-official / --self-check drivers.

Only the standard library and the bundled runtime are used. Python 3.12+.
"""

import contextlib
import csv
import hashlib
import io
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.normpath(os.path.join(HERE, "..", "..", "catala_family_benefits"))
sys.path.insert(0, os.path.join(BUILD, "runtime", "catala"))
sys.path.insert(0, BUILD)

if sys.version_info < (3, 12):
    sys.exit(f"Python 3.12 or later is required by the Catala 1.3.0 runtime (found {sys.version.split()[0]})")

import dates  # noqa: E402  (runtime/catala/dates.py)
from catala_runtime import (Array, Bool, CatalaError, Date, Duration, Integer,  # noqa: E402
                            Lang, Money, Unit, catala_set_lang)
from generated import Allocations_familiales as AF  # noqa: E402
from generated import France  # noqa: E402

catala_set_lang(Lang.Fr)

# --------------------------------------------------------------------------- dates

DATE_COURANTE = "2020-05-01"


def date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return Date(y, m, d)


def plus_years(d, n):
    """d + n an, with the rounding mode the generated code uses (AbortOnRound)."""
    return d.__add__(Duration((n, 0, 0)), dates.DateRounding.AbortOnRound, None)


# Age bands. Each predicate is the conjunction of the comparisons that the
# encoding makes on date_de_naissance (b) against date_courante (dc):
#   b + 3 an >= dc             -> Avant              (epilogue.catala_fr:123)
#   b + 16 an >= dc            -> Pendant            (epilogue.catala_fr:127)
#   b + 11 an <= dc            -> D755-5 11 ans      (securite_sociale_D.catala_fr, D755-5)
#   b + 14 an <= dc            -> majoration L521-3  (securite_sociale_L.catala_fr:319, R521-1 14 an)
#   (b + 20 an) - dc < 365 jour -> forfaitaire L521-1 al.2 (securite_sociale_L.catala_fr:148-152)
#   b + 20 an > dc             -> L512-3 2° age limit (securite_sociale_L.catala_fr:71, R512-2 20 an)

def _cmp(b, dc):
    return {
        "p3": plus_years(b, 3) >= dc,       # still before compulsory schooling
        "p11": plus_years(b, 11) <= dc,     # 11th birthday reached
        "p14": plus_years(b, 14) <= dc,     # 14th birthday reached
        "p16": plus_years(b, 16) >= dc,     # still within compulsory schooling
        "f365": (plus_years(b, 20) - dc).__lt__(Duration((0, 0, 365)), None),
        "p20": plus_years(b, 20) > dc,      # below the L512-3 2° age limit
    }


AGE_BANDS_PF = {
    # label: (predicate on the comparisons, representative birth date at 2020-05-01,
    #         first and last birth dates of the band at 2020-05-01 (None = unbounded))
    "a00_03": (lambda c: c["p3"], "2019-01-01", ("2017-05-01", None)),
    "a03_16": (lambda c: (not c["p3"]) and c["p16"], "2007-01-01", ("2004-05-01", "2017-04-30")),
    "a16_20": (lambda c: (not c["p16"]) and c["p20"], "2003-01-01", ("2000-05-02", "2004-04-30")),
    "a20_plus": (lambda c: not c["p20"], "1999-01-01", (None, "2000-05-01")),
}

AGE_BANDS_AF = {
    "a00_03": (lambda c: c["p3"], "2019-01-01", ("2017-05-01", None)),
    "a03_11": (lambda c: (not c["p3"]) and not c["p11"], "2013-01-01", ("2009-05-02", "2017-04-30")),
    "a11_14": (lambda c: c["p11"] and not c["p14"], "2007-01-01", ("2006-05-02", "2009-05-01")),
    "a14_16": (lambda c: c["p14"] and c["p16"], "2005-01-01", ("2004-05-01", "2006-05-01")),
    "a16_19": (lambda c: (not c["p16"]) and not c["f365"], "2003-01-01", ("2001-05-01", "2004-04-30")),
    "a19_20": (lambda c: c["f365"] and c["p20"], "2000-08-01", ("2000-05-02", "2001-04-30")),
    "a20_plus": (lambda c: not c["p20"], "1999-01-01", (None, "2000-05-01")),
}

# Extra probe dates for the unbounded ends (used only by --self-check).
UNBOUNDED_PROBES = {"a00_03": ["2020-05-01", "2020-09-25"], "a20_plus": ["1990-01-01", "1980-06-15"]}


def age_band(bands, birth_iso, dc_iso=DATE_COURANTE):
    c = _cmp(date(birth_iso), date(dc_iso))
    hits = [label for label, (pred, _, _) in bands.items() if pred(c)]
    if len(hits) != 1:
        raise ValueError(f"birth date {birth_iso} at {dc_iso} falls in {hits}")
    return hits[0]


# --------------------------------------------------------------------------- encoding wrappers

def collectivite(code):
    return France.Collectivite(getattr(France.Collectivite.Code, code), Unit())


def prise_en_charge(code):
    return AF.PriseEnCharge(getattr(AF.PriseEnCharge.Code, code), Unit())


def obligation(code):
    return AF.SituationObligationScolaire(getattr(AF.SituationObligationScolaire.Code, code), Unit())


def enfant(ident, obligation_code, naissance, remuneration, prise, deja_ouvert, apl):
    return AF.Enfant(
        identifiant=Integer(ident),
        obligation_scolaire=obligation(obligation_code),
        remuneration_mensuelle=Money(remuneration),
        date_de_naissance=date(naissance),
        prise_en_charge=prise_en_charge(prise),
        a_deja_ouvert_droit_aux_allocations_familiales=Bool(deja_ouvert),
        beneficie_titre_personnel_aide_personnelle_logement=Bool(apl),
    )


def enfant_entree(ident, naissance, remuneration, prise, deja_ouvert, apl):
    return AF.EnfantEntree(
        d_identifiant=Integer(ident),
        d_remuneration_mensuelle=Money(remuneration),
        d_date_de_naissance=date(naissance),
        d_prise_en_charge=prise_en_charge(prise),
        d_a_deja_ouvert_droit_aux_allocations_familiales=Bool(deja_ouvert),
        d_beneficie_titre_personnel_aide_personnelle_logement=Bool(apl),
    )


@contextlib.contextmanager
def quiet():
    """The generated code prints the inputs of a failed assertion on stdout; hide them."""
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def prestations_familiales(dc_iso, residence):
    return AF.prestations_familiales(AF.PrestationsFamilialesIn(
        date_courante_in=date(dc_iso), residence_in=collectivite(residence)))


def derived_obligation(naissance, dc_iso):
    """obligation_scolaire as InterfaceAllocationsFamiliales derives it (epilogue.catala_fr:121-131)."""
    b, dc = date(naissance), date(dc_iso)
    if plus_years(b, 3) >= dc:
        return "Avant"
    if plus_years(b, 16) >= dc:
        return "Pendant"
    return "Apres"


def interface(children, ressources, dc_iso, residence, est_parent, titre_I, avant_2012):
    """Call InterfaceAllocationsFamiliales. children: list of dicts with keys
    naissance, remuneration, prise, deja, apl. Returns montant_versé as Money."""
    enfants = [enfant_entree(i, c["naissance"], c["remuneration"], c["prise"], c["deja"], c["apl"])
               for i, c in enumerate(children)]
    with quiet():
        out = AF.interface_allocations_familiales(AF.InterfaceAllocationsFamilialesIn(
            i_date_courante_in=date(dc_iso),
            i_enfants_in=Array(enfants),
            i_ressources_menage_in=Money(ressources),
            i_residence_in=collectivite(residence),
            i_personne_charge_effective_permanente_est_parent_in=Bool(est_parent),
            i_personne_charge_effective_permanente_remplit_titre_I_in=Bool(titre_I),
            i_avait_enfant_a_charge_avant_1er_janvier_2012_in=Bool(avant_2012),
        ))
    return out.i_montant_verse


def n_droit_ouvert(children, dc_iso, residence):
    """Number of children with PrestationsFamiliales.droit_ouvert, as the encoding counts
    enfants_à_charge_droit_ouvert_prestation_familiale (securite_sociale_L.catala_fr:86-90)."""
    pf = prestations_familiales(dc_iso, residence)
    n = 0
    for i, c in enumerate(children):
        e = enfant(i, derived_obligation(c["naissance"], dc_iso), c["naissance"], c["remuneration"],
                   c["prise"], c["deja"], c["apl"])
        n += 1 if bool(pf.droit_ouvert(e)) else 0
    return n


# --------------------------------------------------------------------------- 2020 parameters

# Earnings ceiling plafond_l512_3_2 = (smic.brut_horaire * 55%) * 169 (R512-2, R755-0-2),
# SMIC 2020: 10,15 € (others) / 7,66 € (Mayotte), smic/Smic.catala_fr:80-110.
# The runtime rounds money to the cent after each multiplication, so the encoding computes
# 10,15 € * 55% = 5,58 € (5,5825 rounded), then * 169 = 943,02 €; Mayotte 7,66 € * 55% = 4,21 €
# (4,213 rounded), then * 169 = 711,49 €. --self-check re-derives both values by bisection
# on the encoding itself.
PLAFOND_REMUNERATION_2020 = {"Mayotte": "711.49", "otherwise": "943.02"}


def plafond_remuneration(residence):
    return PLAFOND_REMUNERATION_2020["Mayotte" if residence == "Mayotte" else "otherwise"]


# Household ceilings for 2020 (Instruction DSS/SD2B/2019/261, decrets_divers.catala_fr:101-122):
#   plafond_I  = 57 759 € + 5 775 € * n,  plafond_II = 80 831 € + 5 775 € * n,
# n = number of children with droit_ouvert.
def plafond_I(n):
    return 57759 + 5775 * n


def plafond_II(n):
    return 80831 + 5775 * n


def in_2020_parameter_period(dc_iso):
    """Every date-dependent parameter equals its 2020-05-01 value on [2020-04-01, 2020-12-31]:
    SMIC 2020 (Smic.catala_fr:80-110), BMAF 414,4 € from 2020-04-01 (Bmaf.catala_fr:50-58),
    household ceilings 2020 (decrets_divers.catala_fr:101-122), Mayotte rates 2020 (decrets_divers)."""
    return "2020-04-01" <= dc_iso <= "2020-12-31"


# --------------------------------------------------------------------------- FR-AF labels

LOI_751_1 = {"Guadeloupe", "Guyane", "Martinique", "LaReunion", "SaintBarthelemy", "SaintMartin"}
AF_LABELS = ["zero", "general_t1", "general_t2", "general_t3", "outre_mer_1_enfant", "mayotte"]


def af_label(montant, residence, n, ressources):
    """Amount regime of montant_versé (see CONVERSION.md of the FR-AF tables).

    zero                 montant_versé = 0 €
    mayotte              montant_versé > 0 and résidence = Mayotte (décret 2002-423 art. 7 scale)
    outre_mer_1_enfant   montant_versé > 0, résidence in L751-1 and exactly one child with
                         droit_ouvert (L755-12, D755-5 single-child rate)
    general_t1/_t2/_t3   montant_versé > 0 otherwise (L521-1, D521-1 scale); tier from
                         ressources_ménage against plafond I / II of D521-3 (2020 values):
                         t1: r <= I, t2: I < r <= II, t3: r > II (D521-1 I 1°, 2°, 3°)
    """
    if montant == Money("0"):
        return "zero"
    if residence == "Mayotte":
        return "mayotte"
    if residence in LOI_751_1 and n == 1:
        return "outre_mer_1_enfant"
    if n < 2:
        raise AssertionError(f"positive amount {montant} with {n} child(ren) ouvrant droit in {residence}")
    r = float(ressources)
    if r <= plafond_I(n):
        return "general_t1"
    if r <= plafond_II(n):
        return "general_t2"
    return "general_t3"


AF_COMPONENT_LABELS = ["zero", "base", "base_majoration", "base_forfaitaire", "base_majoration_forfaitaire"]
_BASE_CACHE = {}


def _reference_base(n, dc_iso):
    """Amount of a Métropole household at 30 000 € with n children in band a03_11 (no majoration,
    no forfaitaire, tier 1): the L521-1 / D521-1 I 1° base for n children, taken from the encoding."""
    if (n, dc_iso) not in _BASE_CACHE:
        kids = [{"naissance": _shift(AGE_BANDS_AF["a03_11"][1], k), "remuneration": "0.00",
                 "prise": "EffectiveEtPermanente", "deja": True, "apl": False} for k in range(n)]
        _BASE_CACHE[(n, dc_iso)] = int(interface(kids, "30000.00", dc_iso, "Metropole", True, False, False))
    return _BASE_CACHE[(n, dc_iso)]


def af_component_label(montant, residence, n, ressources, dc_iso=DATE_COURANTE):
    """Components of montant_versé for a Métropole household at tier 1 (FR-AF-3; CONVERSION.md T5).

    montant = base(n) + a * majoration + b * forfaitaire, with base(n) from the encoding
    (_reference_base), majoration = bmaf * 16 % (D521-1 I 1°) and forfaitaire = bmaf * 20,234 %
    (D521-2 I 1°), each rounded to the cent as the runtime does; a, b in 0..3 found by search."""
    if montant == Money("0"):
        return "zero"
    if residence != "Metropole" or float(ressources) > plafond_I(n) or n < 2:
        raise AssertionError("component labels are defined for Métropole, tier 1, n >= 2 only")
    from catala_runtime import Decimal as CDecimal
    bmaf = Money("414.40")
    maj, forf = int(bmaf * CDecimal("0.16")), int(bmaf * CDecimal("0.20234"))
    residual = int(montant) - _reference_base(n, dc_iso)
    hits = [(a, b) for a in range(4) for b in range(4) if a * maj + b * forf == residual]
    if len(hits) != 1:
        raise AssertionError(f"montant {money_str(montant)} with n={n} does not decompose uniquely: {hits}")
    a, b = hits[0]
    return "base" + ("_majoration" if a else "") + ("_forfaitaire" if b else "")


def label_for(spec, montant, residence, n, ressources, dc_iso=DATE_COURANTE):
    if spec["output"]["name"] == "composantes_montant_verse":
        return af_component_label(montant, residence, n, ressources, dc_iso)
    return af_label(montant, residence, n, ressources)


def resources_band5(ressources, n):
    """Five-way resource band (FR-AF-1): lt_plafond_I, eq_plafond_I, entre_I_II, eq_plafond_II, gt_plafond_II."""
    r = Money(ressources)
    pI, pII = Money(str(plafond_I(n))), Money(str(plafond_II(n)))
    if r < pI:
        return "lt_plafond_I"
    if r == pI:
        return "eq_plafond_I"
    if r < pII:
        return "entre_I_II"
    if r == pII:
        return "eq_plafond_II"
    return "gt_plafond_II"


def resources_band3(ressources, n):
    """Three-way resource band (FR-AF-2): le_plafond_I, gt_I_le_II, gt_plafond_II."""
    r = Money(ressources)
    if r <= Money(str(plafond_I(n))):
        return "le_plafond_I"
    if r <= Money(str(plafond_II(n))):
        return "gt_I_le_II"
    return "gt_plafond_II"


def resources_value(label, n):
    """Representative resource value (euros, string) for a resource band, given n."""
    return {
        "lt_plafond_I": "30000.00",
        "le_plafond_I": "30000.00",
        "eq_plafond_I": f"{plafond_I(n)}.00",
        "entre_I_II": f"{(plafond_I(n) + plafond_II(n)) // 2}.00",
        "gt_I_le_II": f"{(plafond_I(n) + plafond_II(n)) // 2}.00",
        "eq_plafond_II": f"{plafond_II(n)}.00",
        "gt_plafond_II": "150000.00",
    }[label]


def money_str(m):
    """Money (an int of cents in the 1.3.0 runtime) as a euro string, e.g. 943.44."""
    c = int(m)
    return f"{'-' if c < 0 else ''}{abs(c) // 100}.{abs(c) % 100:02d}"


def earnings_band(remuneration, residence):
    return "le_plafond" if Money(remuneration) <= Money(plafond_remuneration(residence)) else "gt_plafond"


# --------------------------------------------------------------------------- official tests

def official_tests():
    """Import the translation of the official test scopes from run_official_tests.py
    (paperC/catala_family_benefits, unmodified) and return (pf_children, af_tests)."""
    sys.path.insert(0, BUILD)
    with quiet():
        import run_official_tests as rot
    return rot


def run_official_directly():
    """Run every official test scope through the generated Python (via run_official_tests.py)."""
    rot = official_tests()
    results = []
    scopes = [("tests_ouverture_droits.catala_fr", "Test1", rot.ouverture_droits_test1)]
    for name, enfants, ressources, dc, res, extra, expected in rot.AF_TESTS:
        scopes.append(("tests_allocations_familiales.catala_fr", name,
                       rot.make_af_test(enfants, ressources, dc, res, extra, expected)))
    for fname, scope, fn in scopes:
        try:
            with quiet():
                checks = fn()
            ok = all(o for _, o in checks)
        except CatalaError as exc:
            ok, checks = False, [(f"error {type(exc).__name__}", False)]
        results.append((fname, scope, ok, len(checks)))
    return results


def af_official_cases():
    """The 14 tests of tests_allocations_familiales.catala_fr as plain data:
    (name, children dicts, ressources, date_courante, résidence, conditions, expected)."""
    rot = official_tests()
    cases = []
    for name, enfants, ressources, dc, res, extra, expected in rot.AF_TESTS:
        children = []
        for e in enfants():
            d = e.d_date_de_naissance
            children.append({
                "naissance": f"{d.value.year:04d}-{d.value.month:02d}-{d.value.day:02d}",
                "remuneration": money_str(e.d_remuneration_mensuelle),
                "prise": e.d_prise_en_charge.code.name,
                "deja": bool(e.d_a_deja_ouvert_droit_aux_allocations_familiales),
                "apl": bool(e.d_beneficie_titre_personnel_aide_personnelle_logement),
            })
        cond = {"est_parent": True, "titre_I": False, "avant_2012": bool(extra.get("avant_2012", False))}
        cases.append((name, children, ressources, dc, res, cond, expected))
    return cases


# --------------------------------------------------------------------------- generic drivers

def load_spec():
    with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as f:
        return json.load(f)


def excluded(spec, row):
    for x in spec["exclusions"]:
        # The shared format defines exclusions as Python boolean expressions over the
        # attribute names; they are read from this folder's own spec.json, without builtins.
        if eval(x["predicate"], {"__builtins__": {}}, dict(row)):
            return x["id"]
    return None


def all_rows(spec):
    names = [a["name"] for a in spec["attributes"]]
    values = [a["values"] for a in spec["attributes"]]
    # odometer order, last attribute fastest
    idx = [0] * len(names)
    while True:
        yield {n: values[i][idx[i]] for i, n in enumerate(names)}
        k = len(names) - 1
        while k >= 0:
            idx[k] += 1
            if idx[k] < len(values[k]):
                break
            idx[k] = 0
            k -= 1
        if k < 0:
            return


def _eval_chunk(args):
    module_path, rows = args
    import importlib.util
    spec_ = importlib.util.spec_from_file_location("oracle_worker", module_path)
    mod = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(mod)
    out = []
    for row in rows:
        out.append(mod.evaluate_with_reason(row))
    return out


def enumerate_table(oracle_file, workers=None):
    spec = load_spec()
    names = [a["name"] for a in spec["attributes"]]
    rows = list(all_rows(spec))
    if len(rows) > 200_000:
        sys.exit(f"{len(rows)} combinations exceed the 200,000 limit")
    chunk = 2000
    chunks = [(oracle_file, rows[i:i + chunk]) for i in range(0, len(rows), chunk)]
    results = []
    with ProcessPoolExecutor(max_workers=workers or os.cpu_count()) as ex:
        for part in ex.map(_eval_chunk, chunks):
            results.extend(part)
    counts, reasons = {}, {}
    path = os.path.join(HERE, "ground_truth.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(names + ["output"])
        for row, (label, reason) in zip(rows, results):
            w.writerow([row[n] for n in names] + [label])
            counts[label] = counts.get(label, 0) + 1
            if reason:
                reasons[(label, reason)] = reasons.get((label, reason), 0) + 1
    print(f"wrote {path}: {len(rows)} rows")
    for label in sorted(counts):
        print(f"  {label}: {counts[label]}")
    for (label, reason), k in sorted(reasons.items()):
        print(f"  [{label}] {reason}: {k}")
    return counts, reasons


def write_sha256sums():
    names = sorted(n for n in os.listdir(HERE)
                   if os.path.isfile(os.path.join(HERE, n)) and n != "SHA256SUMS")
    lines = []
    for n in names:
        with open(os.path.join(HERE, n), "rb") as f:
            lines.append(f"{hashlib.sha256(f.read()).hexdigest()}  {n}\n")
    with open(os.path.join(HERE, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)


def write_official_examples(names, examples):
    """examples: list of (case_id, row dict, label)."""
    path = os.path.join(HERE, "official_examples.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id"] + names + ["output"])
        for case_id, row, label in examples:
            w.writerow([case_id] + [row[n] for n in names] + [label])
    print(f"wrote {path}: {len(examples)} rows")


# --------------------------------------------------------------------------- self-checks

def _shift(iso, days):
    import datetime
    return (datetime.date.fromisoformat(iso) + datetime.timedelta(days=days)).isoformat()


def check_age_bands(bands, dc_iso=DATE_COURANTE):
    """Each band's first/last birth dates fall in the band, the neighbouring days fall outside,
    the representative falls inside, and the bands partition the probes. Returns failures."""
    fails = []
    for label, (_, rep, (first, last)) in bands.items():
        probes_in = [rep] + [d for d in (first, last) if d] + UNBOUNDED_PROBES.get(label, [])
        for d in probes_in:
            if age_band(bands, d, dc_iso) != label:
                fails.append(f"{label}: {d} expected inside")
        if first and age_band(bands, _shift(first, -1), dc_iso) == label:
            fails.append(f"{label}: day before {first} is inside")
        if last and age_band(bands, _shift(last, 1), dc_iso) == label:
            fails.append(f"{label}: day after {last} is inside")
    return fails


def bisect_plafond_remuneration(residence, dc_iso=DATE_COURANTE):
    """Largest monthly earnings (cents) with conditions_hors_âge = vrai, found on the encoding."""
    pf = prestations_familiales(dc_iso, residence)
    lo, hi = 0, 10_000_000
    while hi - lo > 1:
        mid = (lo + hi) // 2
        e = enfant(1, "Apres", "2003-01-01", money_str(Money(mid)), "EffectiveEtPermanente", True, False)
        if bool(pf.conditions_hors_age(e)):
            lo = mid
        else:
            hi = mid
    return money_str(Money(lo))


def robustness(spec, evaluate, alternatives, sample_every=1, order_key=None):
    """Re-evaluate non-excluded rows with every alternative concrete value of one attribute at a
    time (alternatives(attr, label, row) -> list of concrete values) and count label changes.
    With order_key(row, overrides), alternatives that reverse the birth order of two children
    are counted apart (the age bands do not fix which of two same-band children is the elder)."""
    stats = {"kept": [0, 0], "reversed": [0, 0]}
    examples = []
    for i, row in enumerate(all_rows(spec)):
        if i % sample_every or excluded(spec, row):
            continue
        base = evaluate(row)
        base_order = order_key(row, {}) if order_key else None
        for a in spec["attributes"]:
            for alt in alternatives(a["name"], row[a["name"]], row):
                ov = {a["name"]: alt}
                kind = "reversed" if order_key and order_key(row, ov) != base_order else "kept"
                got = evaluate(row, ov)
                stats[kind][0] += 1
                if got != base:
                    stats[kind][1] += 1
                    if kind == "kept" and len(examples) < 20:
                        examples.append((dict(row), a["name"], alt, base, got))
    return stats, examples


# --------------------------------------------------------------------------- FR-AF tables

EARNINGS_REP = {"le_plafond": "0.00", "gt_plafond": "1000.00"}


def resolve_resources(token, n):
    """A resource band label, or an alternative token used by --self-check, as euros."""
    pI, pII = plafond_I(n), plafond_II(n)
    alt = {"zero": "0.00", "PI-1c": f"{pI - 1}.99", "PI+1c": f"{pI}.01", "PII-1c": f"{pII - 1}.99",
           "PII+1c": f"{pII}.01", "PI": f"{pI}.00", "PII": f"{pII}.00", "high": "500000.00"}
    return alt[token] if token in alt else resources_value(token, n)


def resource_alternatives(label):
    return {"lt_plafond_I": ["zero", "PI-1c"], "le_plafond_I": ["zero", "PI"],
            "eq_plafond_I": [], "eq_plafond_II": [],
            "entre_I_II": ["PI+1c", "PII-1c"], "gt_I_le_II": ["PI+1c", "PII"],
            "gt_plafond_II": ["PII+1c", "high"]}[label]


def af_value(row, fixed, key, slot=None):
    if slot is not None:
        name = f"enfant{slot}_{key}"
        return row[name] if name in row else fixed[f"enfant_{key}"]
    return row[key] if key in row else fixed[key]


def af_concrete(row, fixed, nslots, overrides=None, dc_iso=DATE_COURANTE):
    """Concrete inputs of InterfaceAllocationsFamiliales for a row of labels.
    overrides: {attribute name: concrete value} (birth date, euros, or resource token)."""
    overrides = overrides or {}
    children = []
    for k in range(1, nslots + 1):
        age = af_value(row, fixed, "age", k)
        if age == "absent":
            continue
        rep = AGE_BANDS_AF[age][1]
        # Slot k's representative is the band representative plus (k - 1) days, so that of two
        # children in the same band the lower slot is the elder (CONVERSION.md, slot order).
        naissance = overrides.get(f"enfant{k}_age", _shift(rep, k - 1))
        rem_label = af_value(row, fixed, "remuneration", k)
        rem = overrides.get(f"enfant{k}_remuneration", EARNINGS_REP[rem_label])
        children.append({
            "naissance": naissance,
            "remuneration": rem,
            "prise": af_value(row, fixed, "prise_en_charge", k),
            "deja": af_value(row, fixed, "deja_ouvert", k) == "true",
            "apl": af_value(row, fixed, "apl", k) == "true",
        })
    residence = af_value(row, fixed, "residence")
    n = n_droit_ouvert(children, dc_iso, residence)
    ressources = resolve_resources(overrides.get("ressources", af_value(row, fixed, "ressources")), n)
    cond = {k: af_value(row, fixed, k) == "true" for k in ("est_parent", "titre_I", "avait_enfant_avant_2012")}
    return children, residence, ressources, cond, n


def af_evaluate_with_reason(spec, fixed, nslots, row, overrides=None, dc_iso=DATE_COURANTE):
    x = excluded(spec, row)
    if x:
        return "EXCLUDED", x
    try:
        with quiet():
            children, residence, ressources, cond, n = af_concrete(row, fixed, nslots, overrides, dc_iso)
            montant = interface(children, ressources, dc_iso, residence, cond["est_parent"],
                                cond["titre_I"], cond["avait_enfant_avant_2012"])
    except CatalaError as exc:
        pos = exc.source_positions[0] if exc.source_positions else "?"
        return "REJECTED", f"{type(exc).__name__} at {pos}"
    return label_for(spec, montant, residence, n, ressources, dc_iso), None


def af_alternatives(attr, label, row):
    if attr.endswith("_age"):
        if label == "absent":
            return []
        _, _, (first, last) = AGE_BANDS_AF[label]
        return [d for d in (first, last) if d] + UNBOUNDED_PROBES.get(label, [])
    if attr.endswith("_remuneration"):
        p = int(Money(plafond_remuneration(row.get("residence", "Metropole"))))
        return {"le_plafond": ["400.00", money_str(Money(p))],
                "gt_plafond": [money_str(Money(p + 1)), "5000.00"]}[label]
    if attr == "ressources":
        return resource_alternatives(label)
    return []


def af_birth_order(fixed, nslots):
    """order_key for robustness(): slot numbers sorted by the birth dates actually used."""
    def key(row, overrides):
        b = []
        for k in range(1, nslots + 1):
            a = af_value(row, fixed, "age", k)
            if a != "absent":
                b.append((overrides.get(f"enfant{k}_age", _shift(AGE_BANDS_AF[a][1], k - 1)), k))
        return [k for _, k in sorted(b)]
    return key


def af_map_case(case, spec, fixed, nslots):
    """Map an official household test onto a row of this table, or return (None, reason)."""
    name, children, ressources, dc, residence, cond, expected = case
    names = [a["name"] for a in spec["attributes"]]
    if not in_2020_parameter_period(dc):
        return None, f"date_courante {dc} lies outside the 2020 parameter period [2020-04-01, 2020-12-31] of this table"
    if len(children) > nslots:
        return None, f"{len(children)} children; the table has {nslots} child slots"
    if "enfant1_age" in names and "absent" not in spec["attributes"][names.index("enfant1_age")]["values"] \
            and len(children) != nslots:
        return None, f"{len(children)} child(ren); the table describes households of exactly {nslots} children"
    labels = {"residence": residence,
              "est_parent": "true" if cond["est_parent"] else "false",
              "titre_I": "true" if cond["titre_I"] else "false",
              "avait_enfant_avant_2012": "true" if cond["avant_2012"] else "false"}
    n = n_droit_ouvert(children, dc, residence)
    res_values = (spec["attributes"][names.index("ressources")]["values"] if "ressources" in names
                  else [fixed["ressources"]])
    labels["ressources"] = (resources_band5 if "eq_plafond_I" in res_values else resources_band3)(ressources, n)
    for k in range(1, nslots + 1):
        if k > len(children):
            labels[f"enfant{k}_age"] = "absent"
            continue
        c = children[k - 1]
        labels[f"enfant{k}_age"] = age_band(AGE_BANDS_AF, c["naissance"], dc)
        labels[f"enfant{k}_remuneration"] = earnings_band(c["remuneration"], residence)
        labels[f"enfant{k}_prise_en_charge"] = c["prise"]
        labels[f"enfant{k}_deja_ouvert"] = "true" if c["deja"] else "false"
        labels[f"enfant{k}_apl"] = "true" if c["apl"] else "false"
    row = {}
    for key, value in labels.items():
        if key in names:
            row[key] = value
            continue
        is_child = key.startswith("enfant") and key[6].isdigit()
        if is_child and labels[f"enfant{key[6]}_age"] == "absent":
            continue
        fixed_value = fixed[f"enfant_{key.split('_', 1)[1]}"] if is_child else fixed[key]
        if value != fixed_value:
            return None, f"{key} = {value}, the table fixes it to {fixed_value}"
    label = label_for(spec, Money(expected), residence, n, ressources, dc)
    return (row, label), None
