"""Oracle for NZ-SPS: Sole Parent Support eligibility in OpenFisca Aotearoa.

Encoding: https://github.com/digitalaotearoa/openfisca-aotearoa at commit
9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb (AGPL-3.0), variable
sole_parent_support__entitled, week 2019-W05.  Needs openfisca_aotearoa
installed (paperC/openfisca_nz/ENVIRONMENT.md); --check-official also needs the
clone's test files (environment variable OPENFISCA_AOTEAROA_DIR, or the
editable install's source tree).

    python oracle.py --enumerate                  writes ground_truth.csv (one simulation per row)
    python oracle.py --batch-diagnostic           shows whether batching rows would change results
    python oracle.py --check-official [--write] [--log FILE]
                                                  re-runs every official YAML case
                                                  directly and through the oracle;
                                                  --write rewrites official_examples.csv
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as _f:
    SPEC = json.load(_f)

PERIOD = "2019-W05"
MONTH = "2019-01"  # period.first_month of 2019-W05 (Monday 2019-01-28)
OUTPUT_VAR = "sole_parent_support__entitled"
TEST_FILES = ["openfisca_aotearoa/tests/social_security/sole_parent_support/*.yaml"]
ATTR_VARS = {a["name"] for a in SPEC["attributes"]} - {"children"} | {"social_security__financially_independent"}
REP = {a["name"]: a["representative"] for a in SPEC["attributes"]}
FIXED_CHECKS: list = []
VALID_FROM, VALID_UNTIL = "2018-11-26", None  # formula_2018_11_26; parameters constant since

CHILD_BANDS = [("<14", None, 14), ("14-15", 14, 16), ("16-17", 16, 18), (">=18", 18, None)]
AGE_BANDS = [("<20", None, 20), (">=20", 20, None)]
WEEK_BOOLS = [
    "social_security__in_a_relationship",
    "sole_parent_support__spouse_or_partner_died",
    "sole_parent_support__marriage_or_civil_union_dissolved",
    "sole_parent_support__living_apart_and_lost_support",
    "sole_parent_support__partner_imprisoned",
    "sole_parent_support__partner_supervision",
    "sole_parent_support__receiving",
    "sole_parent_support__principal_caregiver_before_apart",
    "sole_parent_support__principal_caregiver_of_youngest",
    "sole_parent_support__both_primary_caregiver_by_order",
    "social_security__residential_requirement",
]


def build_unit(row, uid):
    applicant = {n: {PERIOD: REP[n][row[n]]} for n in WEEK_BOOLS}
    applicant["social_security__principal_caregiver"] = {MONTH: REP["social_security__principal_caregiver"][row["social_security__principal_caregiver"]]}
    applicant["age"] = {PERIOD: REP["age"][row["age"]]}
    pid = f"{uid}_applicant"
    persons = {pid: applicant}
    kids = []
    for k, a in enumerate(REP["children"][row["children"]]):
        cid = f"{uid}_child{k + 1}"
        persons[cid] = {"age": {PERIOD: a}, "social_security__financially_independent": {PERIOD: False}}
        kids.append(cid)
    family = {"principal": pid}
    if kids:
        family["children"] = kids
    return persons, {"families": {f"{uid}_family": family}}, pid


def _band(value, bands):
    for label, lo, hi in bands:
        if (lo is None or value >= lo) and (hi is None or value < hi):
            return label
    raise Unmappable(f"value {value} outside every band")


def map_person(sim, i, period):
    from openfisca_core import periods
    p = periods.period(period)
    fam = sim.persons.family
    f_id = fam.members_entity_id[i]
    roles = [r.key for r in fam.members_role]
    if roles[i] != "principal":
        raise Unmappable(f"person has role {roles[i]} in the family; the table describes the family's principal")
    members = [j for j in range(len(roles)) if fam.members_entity_id[j] == f_id and j != i]
    others = sorted({roles[j] for j in members if roles[j] != "child"})
    if others:
        raise Unmappable(f"family has members in role(s) {', '.join(others)}; the table fixes a family of principal and children only")
    kids = [j for j in members if roles[j] == "child"]
    if len(kids) > 2:
        raise Unmappable(f"family has {len(kids)} children; the table covers at most 2")
    independent = sim.calculate("social_security__financially_independent", p.first_week)
    if any(independent[j] for j in kids):
        raise Unmappable("a child is financially independent; the table fixes this to False")
    ages = sim.calculate("age", p.start)
    order = [b[0] for b in CHILD_BANDS]
    bands = sorted((_band(int(ages[j]), CHILD_BANDS) for j in kids), key=order.index)
    children = "none" if not bands else f"{len(bands)}:" + "+".join(bands)
    row = {"children": children,
           "social_security__principal_caregiver": label_bool(sim.calculate("social_security__principal_caregiver", p.first_month)[i])}
    for n in WEEK_BOOLS:
        row[n] = label_bool(sim.calculate(n, p.first_week)[i])
    row["age"] = _band(int(sim.calculate("age", p.start)[i]), AGE_BANDS)
    return {n: row[n] for n in NAMES}


# ---------------------------------------------------------------------------
# Shared oracle core for the NZ samples (paperC/specs/NZ-*/oracle.py).
#
# This block is copied verbatim into every NZ oracle.py below the rule-specific
# part, so that each sample folder is self-contained.  The master copy is
# paperC/openfisca_nz/oracle_core.py; paperC/openfisca_nz/build_oracles.py does
# the copying and checks that the copies are identical.
#
# The rule-specific part defines:
#   SPEC, PERIOD, OUTPUT_VAR, TEST_FILES, ATTR_VARS, FIXED_CHECKS,
#   VALID_FROM, VALID_UNTIL (ISO dates or None: weeks whose output the table gives),
#   build_unit(row, uid) -> (persons, groups, applicant_id)
#   map_person(sim, index, period) -> dict[str, str]  (raises Unmappable)
# ---------------------------------------------------------------------------

import csv
import glob
import json
import os
import sys
from itertools import product

NAMES = [a["name"] for a in SPEC["attributes"]]
DOMAINS = [a["values"] for a in SPEC["attributes"]]
EXCLUSIONS = SPEC["exclusions"]


class Unmappable(Exception):
    """An official case (or one person of it) that does not map onto the table."""


_TBS = None


def tbs():
    global _TBS
    if _TBS is None:
        from openfisca_aotearoa import CountryTaxBenefitSystem
        _TBS = CountryTaxBenefitSystem()
    return _TBS


def label_bool(value) -> str:
    return "True" if bool(value) else "False"


def excluded(row: dict[str, str]) -> bool:
    # Predicates are the spec's own text; PROTOCOL.md section 2 evaluates them this way.
    return any(eval(e["predicate"], {"__builtins__": {}}, dict(row)) for e in EXCLUSIONS)


def build_situation(rows):
    """One independent household per row; returns (situation, applicant ids)."""
    situation: dict[str, dict] = {"persons": {}}
    applicants = []
    for k, row in enumerate(rows):
        persons, groups, applicant = build_unit(row, f"u{k}")
        situation["persons"].update(persons)
        for plural, items in groups.items():
            situation.setdefault(plural, {}).update(items)
        applicants.append(applicant)
    return situation, applicants


def simulate(rows, trace=False):
    from openfisca_core.simulation_builder import SimulationBuilder
    situation, applicants = build_situation(rows)
    builder = SimulationBuilder()
    builder.set_default_period(PERIOD)
    sim = builder.build_from_entities(tbs(), situation)
    sim.trace = trace
    values = sim.calculate(OUTPUT_VAR, PERIOD)
    ids = list(sim.persons.ids)
    index = [ids.index(a) for a in applicants]
    return sim, index, [label_bool(values[i]) for i in index]


def evaluate(row: dict[str, str]) -> str:
    """Label of OUTPUT_VAR for one row (EXCLUDED rows are not special-cased here)."""
    return simulate([row])[2][0]


def _evaluate_one(row):
    try:
        return evaluate(row)
    except Exception:
        return "REJECTED"


def enumerate_space(path=None, workers=None) -> dict:
    """Every row gets its own simulation (see CONVERSION.md: batching is unsafe)."""
    import multiprocessing
    path = path or os.path.join(HERE, "ground_truth.csv")
    rows = [dict(zip(NAMES, c)) for c in product(*DOMAINS)]
    outputs = ["EXCLUDED" if excluded(r) else None for r in rows]
    todo = [i for i, y in enumerate(outputs) if y is None]
    with multiprocessing.get_context("fork").Pool(workers or os.cpu_count()) as pool:
        results = pool.map(_evaluate_one, [rows[i] for i in todo], chunksize=500)
    for i, y in zip(todo, results):
        outputs[i] = y
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(NAMES + ["output"])
        for r, y in zip(rows, outputs):
            w.writerow([r[n] for n in NAMES] + [y])
    counts: dict[str, int] = {}
    for y in outputs:
        counts[y] = counts.get(y, 0) + 1
    print(f"{SPEC['id']}: {len(rows)} rows written to {os.path.basename(path)}; counts {dict(sorted(counts.items()))}")
    return counts


def check_batch_equals_single(n=300, seed=20261020) -> int:
    """Diagnostic only: compare n rows simulated together with each row simulated alone.

    The ground truth never batches rows; this shows whether batching would change it."""
    import random
    rng = random.Random(seed)
    rows = [dict(zip(NAMES, c)) for c in product(*DOMAINS)]
    rows = [r for r in rows if not excluded(r)]
    sample = rng.sample(rows, min(n, len(rows)))
    batch = simulate(sample)[2]
    bad = sum(evaluate(r) != y for r, y in zip(sample, batch))
    print(f"batch-versus-single check: {len(sample) - bad}/{len(sample)} rows agree")
    return bad


# ----------------------------------------------------------------- official


def source_dir() -> str:
    d = os.environ.get("OPENFISCA_AOTEAROA_DIR")
    if d:
        return d
    import openfisca_aotearoa
    return os.path.dirname(os.path.dirname(os.path.abspath(openfisca_aotearoa.__file__)))


def _load_cases():
    import yaml
    root = source_dir()
    cases = []
    for pattern in TEST_FILES:
        for path in sorted(glob.glob(os.path.join(root, pattern))):
            rel = os.path.relpath(path, root)
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            for k, case in enumerate(data if isinstance(data, list) else [data]):
                cases.append((f"{rel}#{k + 1}", case))
    return cases


def _assertions(case):
    """(period, expected, entity_ids or None) for every assertion of OUTPUT_VAR."""
    out = case.get("output") or {}
    found = []

    def add(value, ids):
        if isinstance(value, dict):
            for p, v in value.items():
                found.append((str(p), v, ids))
        else:
            found.append((str(case["period"]), value, ids))

    if OUTPUT_VAR in out:
        add(out[OUTPUT_VAR], None)
    persons = out.get("persons")
    if isinstance(persons, dict):
        for pid, values in persons.items():
            if isinstance(values, dict) and OUTPUT_VAR in values:
                add(values[OUTPUT_VAR], [pid])
    return found


def _input_vars(case, pid, sim):
    """Variables the case sets for this person (or for all persons when flat)."""
    inp = case.get("input") or {}
    plurals = {e.plural for e in tbs().entities}
    if "persons" in inp:
        names = set((inp["persons"].get(pid) or {}).keys())
        for plural, groups in inp.items():
            if plural == "persons" or not isinstance(groups, dict):
                continue
            for gid, g in groups.items():
                for key in (g or {}):
                    if key in tbs().variables:
                        names.add(key)
        return names
    return {k for k in inp if k not in plurals}


def _traced(sim):
    seen = set()

    def walk(node):
        seen.add((node.name, node.period))
        for c in node.children:
            walk(c)

    for t in sim.tracer.trees:
        walk(t)
    return seen


def _same(a, b) -> bool:
    try:
        import numpy
        if isinstance(a, (float, numpy.floating)) or isinstance(b, (float, numpy.floating)):
            return abs(float(a) - float(b)) < 1e-9
    except Exception:
        pass
    return a == b


def map_case_person(case, direct, index, pid, period):
    """Map one person of an official case onto a table row, or raise Unmappable."""
    from openfisca_core import periods
    pp = periods.period(period)
    if (VALID_FROM and str(pp.start) < VALID_FROM) or (VALID_UNTIL and str(pp.stop) > VALID_UNTIL):
        raise Unmappable(f"asserted for {period}, outside {VALID_FROM or '...'} to {VALID_UNTIL or '...'}, "
                         "where the table's formula version and parameter values apply")
    row = map_person(direct, index, period)
    for n in NAMES:
        if row[n] not in DOMAINS[NAMES.index(n)]:
            raise Unmappable(f"{n}={row[n]!r} is not a declared label")
    if excluded(row):
        raise Unmappable("maps onto a row excluded by the spec: " + ", ".join(
            e["id"] for e in EXCLUSIONS if eval(e["predicate"], {"__builtins__": {}}, dict(row))))
    for check in FIXED_CHECKS:
        check(direct, index, period)
    osim, oindex, _ = simulate([row], trace=True)
    oi = oindex[0]
    notes = []
    for name, p in sorted(_traced(osim), key=lambda x: (x[0], str(x[1]))):
        if name in ATTR_VARS or name not in _input_vars(case, pid, direct):
            continue
        dv = direct.calculate(name, p)[index]
        ov = osim.calculate(name, p)[oi]
        if not _same(dv, ov):
            raise Unmappable(f"sets {name}@{p} = {dv}, which the table's attributes compute as {ov}")
        notes.append(f"{name}@{p} set to {dv}, equal to the value computed from the row")
    ignored = sorted(_input_vars(case, pid, direct) - ATTR_VARS - {n for n, _ in _traced(osim)})
    if ignored:
        notes.append("inputs the oracle does not read (any effect reaches the row through the attribute values read from the case): " + ", ".join(ignored))
    return row, notes


def check_official(write=False, log_path=None) -> int:
    from openfisca_core.simulation_builder import SimulationBuilder
    cases = _load_cases()
    lines = []
    mapped = []
    n_direct = n_direct_ok = 0
    n_unmappable_cases = 0
    for case_id, case in cases:
        builder = SimulationBuilder()
        builder.set_default_period(case["period"])
        direct = builder.build_from_dict(tbs(), case["input"])
        asserts = _assertions(case)
        if not asserts:
            outs = sorted((case.get("output") or {}).keys())
            lines.append(f"{case_id}\tUNMAPPABLE\tdoes not assert {OUTPUT_VAR} (asserts {', '.join(outs)})")
            n_unmappable_cases += 1
            continue
        ids = list(direct.persons.ids)
        for p_assert, expected, only in asserts:
            values = direct.calculate(OUTPUT_VAR, p_assert)
            exp = expected if isinstance(expected, list) else [expected] * len(ids)
            for i, pid in enumerate(ids):
                if only is not None and pid not in only:
                    continue
                e = exp[0] if only is not None and not isinstance(expected, list) else exp[i]
                n_direct += 1
                n_direct_ok += bool(values[i]) == bool(e)
                tag = f"{case_id}[{pid}]" if len(ids) > 1 else case_id
                try:
                    row, notes = map_case_person(case, direct, i, pid, p_assert)
                except Unmappable as u:
                    lines.append(f"{tag}\tUNMAPPABLE\t{u}")
                    continue
                y = evaluate(row)
                ok = y == label_bool(e)
                mapped.append((tag, row, label_bool(e), ok))
                lines.append(f"{tag}\t{'PASS' if ok else 'FAIL'}\toracle={y} expected={label_bool(e)}"
                             + ("\t" + "; ".join(notes) if notes else ""))
    n_ok = sum(m[3] for m in mapped)
    summary = [
        f"{SPEC['id']}: {len(cases)} official cases in {', '.join(TEST_FILES)}",
        f"  cases without an assertion of {OUTPUT_VAR}: {n_unmappable_cases}",
        f"  asserted person-values run directly through OpenFisca: {n_direct_ok}/{n_direct} passed",
        f"  person-values mapped onto the table: {len(mapped)}; through the oracle: {n_ok}/{len(mapped)} passed",
        f"  person-values unmappable: {n_direct - len(mapped)}",
    ]
    print("\n".join(summary))
    if log_path:
        with open(log_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(summary) + "\n\n" + "\n".join(lines) + "\n")
    if write:
        with open(os.path.join(HERE, "official_examples.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["case_id"] + NAMES + ["output"])
            for tag, row, y, _ in mapped:
                w.writerow([tag] + [row[n] for n in NAMES] + [y])
    return 0 if n_ok == len(mapped) and n_direct_ok == n_direct else 1


def main(argv):
    if argv == ["--enumerate"]:
        enumerate_space()
        return 0
    if argv == ["--batch-diagnostic"]:
        return check_batch_equals_single()
    if argv[:1] == ["--check-official"]:
        log = argv[argv.index("--log") + 1] if "--log" in argv else None
        return check_official(write="--write" in argv, log_path=log)
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
