# NZ samples: OpenFisca Aotearoa social-security eligibility

Three Paper C samples built from the OpenFisca Aotearoa encoding of the Social Security
Act 2018, in the format of `paperC/specs/FORMAT.md` (branch `paperc-harness`):

| ID | Entry variable | Week | Attributes |
|---|---|---|---|
| `NZ-SLP` | `supported_living_payment__entitled` | 2019-W01 | 7 |
| `NZ-AS` | `accommodation_supplement__entitled` (SSA 2018 formula) | 2022-W01 | 14 |
| `NZ-SPS` | `sole_parent_support__entitled` | 2019-W05 | 14 |

Encoding: https://github.com/digitalaotearoa/openfisca-aotearoa at commit
`9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb` (version 22.0.0, 6 May 2025, AGPL-3.0).
Environment, verbatim test logs and helper scripts: `paperC/openfisca_nz/`
(`ENVIRONMENT.md` there). A supplementary table for the SSA 1964 formula of
Accommodation Supplement, `NZ-AS-1964`, is kept in `paperC/openfisca_nz/supplementary/`
so that it does not count as a sample (deviation 3).

## Tables

| ID | Declared space | EXCLUDED | REJECTED | Valid | Valid True | Valid False |
|---|---:|---:|---:|---:|---:|---:|
| NZ-SLP | 256 | 0 | 0 | 256 | 51 | 205 |
| NZ-AS | 86,016 | 37,632 | 0 | 48,384 | 28 | 48,356 |
| NZ-SPS | 122,880 | 23,040 | 0 | 99,840 | 6,867 | 92,973 |
| *NZ-AS-1964 (supplementary)* | 512 | 128 | 0 | 384 | 5 | 379 |

No table needed splitting: each is under 200,000 combinations.

## Official examples

`openfisca test` passes every official case of the three rules (50, 47 and 25 cases;
`paperC/openfisca_nz/test_logs/`). `oracle.py --check-official` re-runs every case
directly through OpenFisca and, where a person's eligibility maps onto the table,
through the oracle (mapping rule: CONVERSION.md C6).

| ID | Official cases | Cases asserting eligibility | Asserted person-values (direct pass) | Mapped rows (oracle pass) | Distinct conditions | Unmappable person-values |
|---|---:|---:|---:|---:|---:|---:|
| NZ-SLP | 50 | 7 | 13 (13) | 13 (13) | 12 | 0 |
| NZ-AS | 47 | 7 | 12 (12) | 1 (1) | 1 | 11 |
| NZ-SPS | 25 | 18 | 38 (38) | 14 (14) | 7 | 24 |
| *NZ-AS-1964* | 47 | 7 | 12 (12) | 6 (6) | 6 | 6 |

Main reasons for unmappable cases: most official cases assert an amount or an
intermediate variable instead of eligibility (SLP 43 of 50, AS 40 of 47, SPS 7 of 25);
16 SPS persons are children of the family (the table describes the principal); several
cases override an intermediate variable (for example `sole_parent_support__requirement`
or `accommodation_supplement__accommodation_costs`) with a value that no leaf values of
the case produce; the 6 SSA 1964 cases fall before the NZ-AS formula applies. Each
case and person is listed with its reason at the end of the sample's CONVERSION.md.

### Declared values the official examples never use

* **NZ-SLP:** none; every declared value of every attribute occurs.
* **NZ-AS** (one example row): `social_security__residential_requirement` False;
  `accommodation_type` rent, board, lodging, mortgage, social_housing, residential_care;
  `accommodation_costs` >0; `social_security__in_a_relationship` True;
  `social_security__dependent_children` >=1; `accommodation_supplement__cash_assets`
  8101-16200, >16200; True for each of `partner_accommodation_supplement__receiving`,
  `basic_grant__receiving`, `independent_circumstances_grant__receiving`,
  `basic_grant__entitled`, `independent_circumstances_grant__entitled`,
  `basic_grant__would_be_entitled`, `independent_circumstances_grant__would_be_entitled`,
  `accommodation_supplement__disability`.
* **NZ-SPS:** `children` none, 1:14-15, 1:16-17, 1:>=18 and all ten two-child labels
  (only `1:<14` occurs); `social_security__principal_caregiver` False;
  `sole_parent_support__receiving` True; `sole_parent_support__principal_caregiver_before_apart`
  True; `sole_parent_support__principal_caregiver_of_youngest` True;
  `sole_parent_support__both_primary_caregiver_by_order` True;
  `social_security__residential_requirement` False; `age` <20.
* *NZ-AS-1964:* `social_security__ordinarily_resident_in_new_zealand` False;
  `accommodation_supplement__below_income_threshold` False;
  `accommodation_supplement__below_cash_threshold` False.

(Computed by `paperC/openfisca_nz/summarise.py`; output in `paperC/openfisca_nz/logs/summary.txt`.)

## Verification done

* `paperC/openfisca_nz/crosscheck.py` restates each formula in plain Python without
  OpenFisca and agrees with every row of every `ground_truth.csv`, EXCLUDED labels included.
* `paperC/openfisca_nz/rebuild_all.sh` rebuilds everything from scratch; a clean rebuild
  reproduced every committed table, example file and log byte for byte.
* The harness's own loader (`paperC.harness.spec.load_sample` on branch `paperc-harness`
  at commit `9b8b947`) accepts all three folders: CTRL-HASH and CTRL-GT pass, CTRL-EXCL
  has 0 disagreements, and every predicate passes its syntax whitelist.

## Encoding defects found (reproduced in the ground truth)

1. **Population-wide sum** in `social_security__dependent_children`
   (`interpretation/child.py:54` uses Python's built-in `sum` over all persons). With
   several households in one simulation each household gets the total count. The official
   tests simulate one household at a time, so they do not show it. The oracles simulate
   one row at a time; an earlier batched run of NZ-SPS gave 6,615 True rows where the
   per-row run gives 6,867.
2. **Operator precedence** in `sole_parent_support__dependent_child_requirement`
   (`sole_parent_support.py:180-181`, `(dependent_child * age) < 14`). A child who is
   not a dependent child (18 or over) satisfies the "dependent child under 14" test.
   2,016 valid NZ-SPS rows are True for that reason alone (families whose children are
   one aged 14-17 and one aged 18 or over). The table keeps the encoding's answer.
3. Provisions left out by the encoding (listed in its own comments) are left out of the
   tables: for SLP ss 116, 117, 121, 128, 140, 170 and parts of ss 40-42; for AS s 67(e).

## Licence note for the author

The OpenFisca Aotearoa encoding is licensed under AGPL-3.0. These folders do not copy
its source, but they contain material derived from it: `ground_truth.csv` and
`official_examples.csv` are computed by running it (and the latter is transcribed from
its YAML tests), `spec.json` and `CONVERSION.md` quote its variable labels, docstrings
and comments with file:line references, and each `oracle.py` imports and drives the
package. This repository is MIT (code) and CC BY 4.0 (data, `LICENSE-DATA`). Whether
the derived tables and quotations may be released under those licences, or need an
AGPL notice or separate licensing, is for the author to decide before publication.
**Flagged; nothing has been changed in the repository's licence files.**

## Deviations and interpretive choices

1. **Level of the attributes.** The brief asks for every leaf input as an attribute.
   Six defined terms that have their own formulas, are shared across benefits and are
   set directly by the official tests are attributes (or fixed inputs) at the level of
   the defined term: `social_security__residential_requirement`,
   `social_security__in_a_relationship`, `social_security__dependent_children`,
   `social_security__financially_independent`, `basic_grant__entitled` and, in the
   supplementary table, `immigration__resident` (CONVERSION.md C2, with their sub-trees
   listed per sample). Expanding them would have left almost no official case mappable.
   All variables of each benefit's own provisions are expanded to their leaves.
2. **Fixed weeks differ by rule** (SLP 2019-W01, SPS 2019-W05, AS 2022-W01): each is the
   week of that rule's official eligibility cases. For each rule the formula version and
   every parameter on the path are constant from 2018-11-26 on, so the tables hold for
   any later week; official cases from other weeks in that range are mapped.
3. **Accommodation Supplement has two formula versions.** NZ-AS uses the SSA 2018
   formula (law in force). The six official cases of `1964/entitled.yaml` test the
   SSA 1964 formula at 2018-W01 and cannot map onto NZ-AS, which therefore has a single
   official example row. The SSA 1964 version is provided as `NZ-AS-1964` in
   `paperC/openfisca_nz/supplementary/`, in the same format, with all six cases mapped.
   PROTOCOL.md counts every folder in `paperC/specs` as a sample in the H1-H3 majority
   rules, so adding it there would give Accommodation Supplement two votes; it was kept
   out for that reason. Promoting it is the author's decision.
4. **NZ-SPS household.** The family is the principal applicant plus at most two
   children, with no partner, parent or other member. Without another parent in the
   family, s 32(1) is unreachable and `sole_parent_support__parents_living_apart` has no
   effect. Children are one composite unordered attribute (15 labels), and children's
   financial independence is fixed to False, to stay under 200,000 combinations
   (122,880; per-child flags would give 294,912). Two NZ-SPS tables split by number of
   children were considered and rejected because each sub-table would count as its own sample.
5. **NZ-AS household.** The applicant is the sole principal of a tenancy and of an
   ownership (s 65(2)(d) then coincides with (a) and (b)). A partner member exists only
   when `social_security__in_a_relationship` is True; the cash-assets attribute is the
   applicant-plus-partner total that reg 15 compares.
6. **Exclusions cite the encoding's own text.** legislation.govt.nz and NZLII were
   unreachable from the build environment (HTTP 403), so every exclusion rests on
   definitions quoted in the encoding (labels, docstrings, comments, formulas), with the
   Act section named. Two candidate exclusions that would have needed the Act's text
   (s 67(b)(ii) with (iii) for the same grant; citizen holding a residence visa) were not
   declared. The author may want to check these against the Act.
   Exclusions declared: SPS-X1 (principal caregiver without a dependent child), SPS-X2 (s 32
   child flags without a dependent child), AS-X1 (partner receiving AS without a
   relationship), AS-X2 (independent circumstances grant eligibility while receiving a
   basic grant, reg 8(3) of the Student Allowances Regulations 1998), AS64-X1 (permanent
   resident who is not a resident in the encoding's sense). SLP-X1 (self-inflicted flag
   without restricted capacity or blindness) was declared in the first version and removed
   on 2026-10-21 (Correction below). NZ-AS has a large excluded
   share (43.75%) because its two exclusions each remove a quarter of the space.
7. **Official cases are mapped per person**, and a case that overrides an intermediate
   variable maps only when the override equals what the row computes (CONVERSION.md C6).
   An official person whose row falls under an exclusion is listed as unmappable
   (`sole_parent_support__entitled.yaml` case 3, five persons, SPS-X1: the case sets
   `sole_parent_support__requirement` directly and models no children).
8. **`oracle.py` extras.** Besides `--enumerate` and `--check-official`, each oracle
   accepts `--check-official --write` (rewrites `official_examples.csv`), `--log FILE`
   and `--batch-diagnostic`. Each oracle is assembled from a shared core
   (`paperC/openfisca_nz/oracle_core.py`) and a rule part (`paperC/openfisca_nz/rules/`);
   the copy in the folder is complete and self-contained.
9. **Test logs** in `paperC/openfisca_nz/test_logs/` contain the absolute path of the
   clone used (`/home/user/work/...`); they are records of the run and are not inputs of
   the harness.

## Correction (2026-10-21): NZ-SLP exclusion SLP-X1 removed

An analysis of the two conversions (`paperc-analysis`, `paperC/analysis/REPORT-M2-M6.md`,
"Findings for the author" item 1) found that SLP-X1 rested on a claim about outputs
(the 32 rows "would be False in any case") and that the claim is false for 3 rows,
which the s 40 carer route makes True. An exclusion needs a legal or definitional
impossibility. Section 36 disqualifies only on the s 34 ground and refers to a past act
(the encoding stores the flag with `definition_period = ETERNITY`, beside a weekly
restricted-work-capacity input), so a person with the flag set and neither s 34(a)
condition in week 2019-W01 is possible. The exclusion was removed and every row is now
evaluated through the encoding (OpenFisca Aotearoa 22.0.0, commit `9d77ea7ce3c4`,
OpenFisca-Core 41.5.7). Reasoning in full: `NZ-SLP/CONVERSION.md`, "Correction".

| NZ-SLP | \|D\| | valid | EXCLUDED | REJECTED | valid True | valid False |
|---|---:|---:|---:|---:|---:|---:|
| before | 256 | 224 | 32 | 0 | 48 | 176 |
| after | 256 | 256 | 0 | 0 | 51 | 205 |

The 32 rows are 29 False and 3 True; the other 224 rows keep their output.
`oracle.py --check-official` still passes every mappable official case (13 direct, 13
mapped, 0 unmappable); `official_examples.csv` is unchanged; `crosscheck.py` agrees on
256/256 rows. The table now agrees with the second, blinded conversion, which declared
no exclusion. NZ-AS and NZ-SPS are unchanged.

Not updated with this correction (outside the folder this correction may change):
`paperC/openfisca_nz/logs/summary.txt` and `paperC/openfisca_nz/docs/NZ-SLP.md` still
carry the first version's NZ-SLP counts and item 5. `rebuild_all.sh` regenerates
`NZ-SLP/CONVERSION.md` from `docs/NZ-SLP.md`, so a full rebuild would drop the
Correction section from it until `docs/NZ-SLP.md` is brought in line; the table,
`spec.json` and the oracle outputs would rebuild unchanged.
