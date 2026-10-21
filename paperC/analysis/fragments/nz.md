## New Zealand rules (OpenFisca Aotearoa, commit 9d77ea7ce3c4)

Scripts: `paperC/analysis/m2_nz.py` (writes `out/m2_nz.json`) and `paperC/analysis/m6_nz.py`
(writes `out/m6_nz.json`), run from the repository root with `python3.12 -I`. Both read the
branches through `git show` and the official YAML tests from `paperC/analysis/_ext/`
(`fetch_sources.sh`). Every number below is printed by, or stored in the JSON of, one of
these scripts. Case identifiers are `file#case[person]` with paths relative to
`openfisca_aotearoa/tests/social_security/`, the case counted from 1 in file order and the
person given by name or by 0-based vector position. The first coder numbers cases the same
way; the second coder counts cases from 0 (`#0:0` there is `#1[0]` here).

Tables covered. First conversion (`origin/paperc-data-nz`): `NZ-SLP`, `NZ-AS` (SSA 2018
formula, 2022-W01), `NZ-SPS`, and the supplementary `NZ-AS-1964` (SSA 1964 formula,
2018-W01, kept outside `paperC/specs`). Second conversion (`origin/paperc-code2-nz`):
`NZ-SLP`, `NZ-AS` (SSA 1964 formula, 2018-W01), `NZ-SPS` (one child).

### M2 (a): official cases, mapped and unmapped

The suite of a rule is every YAML case in its test folder. The first coder counts
"person-values" (one per person whose entry variable a case asserts, README-NZ table,
`paperc-data-nz:paperC/specs/README-NZ.md:39-42`); the second coder counts "person-cases",
one per person of a test it reads (`paperc-code2-nz:paperC/specs2/NZ-SLP/CONVERSION_2.md:32`).
Both units are the same where both coders read the file; the second coder reads fewer files
(below).

| Rule | YAML cases | cases asserting the entry variable | persons in all cases | person-values asserting it | first: table, mapped | second: table, mapped |
|---|---:|---:|---:|---:|---|---|
| SLP | 50 | 7 | 105 | 13 | NZ-SLP 13 | NZ-SLP 13 |
| AS | 47 | 7 | 157 | 12 | NZ-AS 1; NZ-AS-1964 6 | NZ-AS 6 |
| SPS | 25 | 18 | 65 | 38 | NZ-SPS 14 | NZ-SPS 8 |

Unmapped cases by reason (reason category, then the conversion's own wording and line):

**NZ-SLP, both conversions.** Other output or scope: `supported_living_payment/base.yaml`
#1-#43 (assert the amount, with the entry variable set as an input;
`paperc-data-nz:paperC/specs/NZ-SLP/CONVERSION.md:77`,
`paperc-code2-nz:paperC/specs2/NZ-SLP/CONVERSION_2.md:72`). All 13 asserting person-values map
in both conversions.

**NZ-AS, first conversion (2018 formula).**
* Other period (6): `accommodation_supplement/1964/entitled.yaml#1`-`#6`, asserted for 2018-W01, before the 2018 formula applies (`paperc-data-nz:paperC/specs/NZ-AS/CONVERSION.md:76-81`).
* Other, case overrides an intermediate variable (5): `2018/entitled.yaml#1[0]`, `[1]`, `[3]`, `[4]`, `[5]` set `accommodation_supplement__accommodation_costs` = True with no type or costs, which the attributes compute as False (`CONVERSION.md:70-75`).
* Other output or scope (40 YAML cases): `2018/_benefit_me.yaml` #1-#3, `accommodation_supplement.yaml` #1, `area.yaml` #1, `assets.yaml` #1-#4, `base.yaml` #1-#10, `beneficiary.yaml` #1, `costs.yaml` #1-#6, `cutout.yaml` #1, `exclusion.yaml` #1-#7, `rate.yaml` #1, `rebate.yaml` #1, `situation.yaml` #1-#4 (`CONVERSION.md:82-94`).

**NZ-AS-1964, first conversion (supplementary).** Other period (6): `2018/entitled.yaml#1[0]`-`[5]`,
asserted for 2022-W01 (`paperc-data-nz:paperC/openfisca_nz/supplementary/NZ-AS-1964/CONVERSION.md:55-60`).
Other output or scope: the same 40 cases (`CONVERSION.md:67-79`).

**NZ-AS, second conversion (1964 formula).** Other period (6): `2018/entitled.yaml#1[0]`-`[5]`,
"entry variable not asserted at the fixed period 2018-W01"
(`paperc-code2-nz:paperC/specs2/NZ-AS/CONVERSION_2.md:113-118`). Other output or scope: the
same 40 cases; the oracle reads only the two `entitled.yaml` files
(`paperc-code2-nz:paperC/specs2/NZ-AS/oracle.py:21-24`).

The two coders thus put opposite halves of the AS suite on their main tables: the first
coder's main table takes the one 2018 case, the second coder's takes the six 1964 cases.

**NZ-SPS, first conversion.**
* Other household shape (16): the child Tamaiti of `sole_parent_support__benefit.yaml#1`-`#6` and of `sole_parent_support__entitled.yaml#1`, `#2`, `#4`, `#6`-`#12` (`paperc-data-nz:paperC/specs/NZ-SPS/CONVERSION.md:74-110`, "person has role child").
* Other, row excluded by the table's own exclusion SPS-X1 (5): `__entitled.yaml#3[0]`-`[4]` (`CONVERSION.md:89-93`).
* Other, case overrides an intermediate variable (3): `__entitled.yaml#4[Koro]` and `#5[0]` set `sole_parent_support__requirement` = True (`CONVERSION.md:94`, `:96`); `#10[Koro]` sets `sole_parent_support__lost_regular_support` = True without its leaves (`CONVERSION.md:105`).
* Other output or scope (7 YAML cases): `sole_parent_support__split_care.yaml` #1-#7 (`CONVERSION.md:111-112`).

**NZ-SPS, second conversion.**
* Other household shape (16): Tamaiti of `__entitled.yaml#1`, `#2`, `#4`, `#6`-`#12` (10, "person is not the principal"), and the persons of `#3[0]`-`[4]` and `#5[0]` (6, "family is not exactly one principal and one child") (`paperc-code2-nz:paperC/specs2/NZ-SPS/CONVERSION_2.md:123-140`).
* Other, case overrides an intermediate variable (2): `#4[Koro]` (`CONVERSION_2.md:130`), `#10[Koro]` (`CONVERSION_2.md:137`).
* Other, file outside the second coder's list of official tests (12): Koro and Tamaiti of `sole_parent_support__benefit.yaml#1`-`#6`. These cases assert `sole_parent_support__entitled`, and three of them are at 2019-W05, the table's own week; the oracle reads only `sole_parent_support__entitled.yaml` (`paperc-code2-nz:paperC/specs2/NZ-SPS/oracle.py:22`), and the conversion record states that 2019-W05 is "the period of every official test" (`CONVERSION_2.md:83`). The first coder maps the six Koro persons.
* Other output or scope (7 YAML cases): `__split_care.yaml` #1-#7.

### M2 (b): declared values used by the whole suite

Every person of every case is placed on each table's attributes, whatever the case asserts
and whatever its week or household, at every week the case asserts an output (883 person-weeks
for AS, 105 for SLP, 65 for SPS; 89 placement rows for the second coder's SPS, where a family
with two children gives one row per child). Two readings:

* **primary**: an attribute takes a value only when the case sets that input, or sets the
  leaves of a defined term whose formula is a plain function of them (see Judgements);
  otherwise it is UNKNOWN, as the task requires;
* **secondary**: UNKNOWN is replaced by the encoding's default or by what the formula
  computes from the inputs the case sets (sources in `DEFAULTS` of `m2_nz.py` and in the
  Judgements). This reading is reported for information only.

The mapped column is the table's `official_examples.csv`. The suite columns include the
mapped rows.

| Table | declared values | unused, mapped tests | unused, whole suite (primary) | unused, whole suite (secondary) |
|---|---:|---:|---:|---:|
| first NZ-SLP | 16 | 0 | 0 | 0 |
| second NZ-SLP | 16 | 0 | 0 | 0 |
| first NZ-AS (2018) | 34 | 20 | 0 | 0 |
| first NZ-AS-1964 (suppl.) | 18 | 3 | 3 | 2 |
| second NZ-AS (1964) | 18 | 3 | 3 | 2 |
| first NZ-SPS | 41 | 21 | 14 | 12 |
| second NZ-SPS | 22 | 5 | 3 | 2 |

Values still unused by the whole suite:
* NZ-AS-1964 and second NZ-AS: `ordinarily_resident_in_nz` False (primary only; in the secondary reading it comes from the default, `resident.py:77`, in 151 placements), `below_income_threshold` False and `below_cash_threshold` False (both readings: no case sets them False, and their default is True, `entitled.py:153`, `:161`).
* First NZ-SPS: `children` none, 1:14-15, 1:16-17, 1:>=18 and nine of the ten two-child labels (primary; `none` appears in the secondary reading from the single-person vector cases `__entitled.yaml#3` and `#5`, which describe no family); `social_security__principal_caregiver` False (primary). The only two-child label any case reaches is `2:<14+<14` (`__split_care.yaml`, children aged 5 and 3).
* Second NZ-SPS: `principal_caregiver` False (primary), `child_dependent` False and `child_age` 14+ (both readings: every child in the suite is aged 3 or 5, or has no age).

Where the values left unused by the mapped tests come from in the whole suite (first case
found; full lists in `out/m2_nz.json`, key `provenance`):
* First NZ-AS: all 20 come from 2018-folder cases that assert other variables, plus the five `2018/entitled.yaml` persons the first coder could not map: `residential_requirement` False from `2018/entitled.yaml#1[1]`; the six accommodation types and costs > 0 from `_benefit_me.yaml`, `accommodation_supplement.yaml`, `exclusion.yaml#1`, `#6`, `rate.yaml`, `rebate.yaml`; relationship True, dependent children >= 1 and both higher cash-asset bands from `assets.yaml` (families with partner and children); the seven s 67 flags from `exclusion.yaml#2`-`#7`.
* First NZ-SPS: `2:<14+<14`, `receiving` True, the three s 32 flags True from `__split_care.yaml#1`-`#6`; `residential_requirement` False from `__entitled.yaml#3[3]`; `age` <20 from the child persons Tamaiti (29 placements).
* Second NZ-SPS: `residential_requirement` False from `__entitled.yaml#3[3]`; `age` <20 from the child persons.

Restricted to applicants (persons in role principal, or with no family role), the primary
reading leaves one more value unused in each SPS table (`age` <20; first 15, second 4); the
other tables do not change.

UNKNOWN counts per attribute (primary), out of the placement rows: SLP 101 of 105 for
restricted work capacity, 103 blind, 93 residential requirement, 0 age, 103 self-inflicted,
99 caring, 11 dependent children. First NZ-AS (883): from 203 (relationship) to 881
(disability); accommodation type 672, costs 785, cash assets 837. AS-1964 tables (883): age
779, accommodation costs 650, each other attribute 877 to 882. First NZ-SPS (65): children 6,
age 6, relationship 6, principal caregiver 31, residential requirement 36, the s 30 and s 32
flags 55 to 64. Second NZ-SPS (89): child attributes 6, age 6, principal caregiver 43, flags
79 to 88. Ten placements in AS have an `accommodation_type` outside the enum (`under_the_sun`,
`under_the_moon` in `costs.yaml#1`-`#4` and `exclusion.yaml#1`, `#6`); they stay UNKNOWN in
both readings.

Cross-check: the mapped-only counts (0, 20, 3, 21; 0, 3, 5) equal the lists in
`paperc-data-nz:paperC/specs/README-NZ.md:54-72` and
`paperc-code2-nz:paperC/specs2/README-NZ-CODE2.md:22-26`. No discrepancy.

### M2 (c): H1 indicators per table

`missed valid` is the number of valid ground-truth rows outside the product of the observed
values (C1 `missed_valid`).

| Table | valid rows | mapped: unused > 0 / missed valid | whole suite, primary | whole suite, secondary |
|---|---:|---|---|---|
| first NZ-SLP | 224 | no / 0 | no / 0 | no / 0 |
| second NZ-SLP | 256 | no / 0 | no / 0 | no / 0 |
| first NZ-AS (2018) | 48,384 | yes / 48,383 | no / 0 | no / 0 |
| first NZ-AS-1964 | 384 | yes / 336 | yes / 336 | yes / 288 |
| second NZ-AS (1964) | 384 | yes / 336 | yes / 336 | yes / 288 |
| first NZ-SPS | 99,840 | yes / 99,776 | yes / 91,648 | yes / 82,944 |
| second NZ-SPS | 2,048 | yes / 1,984 | yes / 1,792 | yes / 1,536 |

With the whole suite, both indicators still hold for the AS-1964 and SPS tables of both
conversions and stay false for both NZ-SLP tables. They change for one table: the first
coder's NZ-AS (2018 formula), where every declared value occurs somewhere in the 2018 test
folder, so the product of the observed values covers all 48,384 valid rows. The slice
(other output, and the intermediate override in `2018/entitled.yaml`) accounts for all 20
unused values of that table.

### M6 (a): attribute-level alignment

**SLP.** Both conversions make the same seven inputs attributes, with the same cut points:
restricted work capacity, totally blind, residential requirement (kept whole), age (16, 18,
20), self-inflicted, caring for another person, dependent children (0 / 1 or more). Labels
differ only in spelling (`>=20` / `20+`, `>=1` / `1+`); every attribute coincides. Both fix
2019-W01 and a one-person household, and both keep the residential requirement and the
dependent-children count at the level of the defined term. The one difference is the
exclusion: the first coder declares SLP-X1 (self-inflicted without restricted capacity or
blindness, `paperc-data-nz:paperC/specs/NZ-SLP/spec.json:37`); the second declares none
(`paperc-code2-nz:paperC/specs2/NZ-SLP/CONVERSION_2.md:74`).

**AS, SSA 1964 formula (first coder's supplementary table, second coder's main table).**
Both make the same nine inputs attributes: age (16), `immigration__resident` (kept whole),
permanent resident, citizen, ordinarily resident, `accommodation_supplement__accommodation_costs`
(a plain input at 2018-W01), social housing, below the income threshold, below the cash
threshold. All nine coincide (`>=16` / `16+`). Both fix 2018-W01 and a lone applicant, and
both declare the same exclusion (AS64-X1, `paperc-data-nz:paperC/openfisca_nz/supplementary/NZ-AS-1964/CONVERSION.md:12`;
PR-IMPLIES-RESIDENT, `paperc-code2-nz:paperC/specs2/NZ-AS/CONVERSION_2.md:86`).

**AS, SSA 2018 formula.** Only the first coder converts it (main NZ-AS, 2022-W01,
`paperc-data-nz:paperC/specs/NZ-AS/CONVERSION.md:7`). Its 14 attributes (residential
requirement, accommodation type, accommodation costs > 0, relationship, dependent children,
cash assets at 8,100 and 16,200, the partner's AS, and the seven s 67 grant and disability
flags) are inputs the second coder's table never reads, because the second coder fixed
2018-W01, where the 1964 formula applies
(`paperc-code2-nz:paperC/specs2/README-NZ-CODE2.md:36`). No row-level comparison is possible
for this formula: the second conversion has no table for it. Conversely, the first coder's
main NZ-AS reads none of the 1964 inputs (age, the three status flags, the threshold flags).

**SPS.**

| Encoding input | first coder | second coder | relation |
|---|---|---|---|
| residential requirement | attribute | attribute | coincide |
| age (20) | attribute `<20`, `>=20` | attribute `<20`, `20+` | coincide |
| in a relationship | attribute | attribute | coincide |
| s 30(b)-(d): spouse died, dissolved, living apart | attributes | attributes | coincide |
| s 30(e): partner imprisoned, under supervision | attributes | attributes | coincide |
| principal caregiver (month 2019-01) | attribute | attribute | coincide |
| receiving SPS; principal caregiver before living apart; of youngest; by order (s 32) | attributes | fixed at default False: with one child, s 32 split care is True for the principal (`CONVERSION_2.md:63-69`) | first only |
| children (members in role child) | composite `children`: none, one child in bands <14, 14-15, 16-17, >=18, or two children (15 labels), children's financial independence fixed False (`paperc-data-nz:paperC/specs/NZ-SPS/CONVERSION.md:14`, `:17`) | exactly one child, `child_dependent` (kept whole) x `child_age` <14 / 14+ (`paperc-code2-nz:paperC/specs2/NZ-SPS/CONVERSION_2.md:75`, `:81-82`) | on one-child households the first refines the second on age (14-15 and 16-17 both fall in True/14+, 1:>=18 is False/14+); the second's cell False/<14 (a financially independent child under 14) has no first-coder label; the first's `none` and two-child labels have no second-coder counterpart |
| parents living apart | not set (no other parent) | default | both leave it without effect |
| period | 2019-W05 | 2019-W05 | same |

Exclusions: the first coder declares SPS-X1 and SPS-X2 (no dependent child,
`paperc-data-nz:paperC/specs/NZ-SPS/spec.json:281`); the second declares none.

### M6 (b): NZ-SLP row by row

Attribute names are mapped in spec order and the labels `>=20` -> `20+`, `>=1` -> `1+`; the
mapping is a bijection, so all 256 combinations are compared one to one.

* 224 rows agree: every row valid for the first coder has the same output in both tables.
* 32 rows are EXCLUDED by the first coder (SLP-X1) and evaluated by the second: 29 False, 3 True.

The three True rows are self-inflicted = True, restricted capacity = False, blind = False,
caring for another person = True, residential requirement = True, and (age 18-19,
dependent children 0), (age >=20, 0) or (age >=20, >=1). They are True through the s 40
carer route (`supported_living_payment.py:79-106`), which reads neither the s 34 grounds nor
the self-inflicted flag. The first coder's record states that the output of the excluded
rows "would be False in any case (the s 34 branch already fails), so the exclusion changes
labels and never outcomes" (`paperc-data-nz:paperC/specs/NZ-SLP/CONVERSION.md:16`). That
statement holds for 29 of the 32 rows and fails for these 3. The two conversions'
evaluations agree everywhere: the difference lies in the exclusion, and the second
coder's table shows that the excluded combinations are evaluable (their True count, 51,
equals the first coder's 48 plus these 3).

### M6 (c): other row-level comparisons

**NZ-AS-1964 (first) against NZ-AS (second), SSA 1964 formula.** Names mapped in spec order,
`>=16` -> `16+`; all 512 combinations compared one to one. 512 agree, including the 128
EXCLUDED rows, which both coders exclude with the same predicate. No disagreement.

**NZ-SPS.** Common refinement: the first coder's rows with one child and the four s 32
inputs at False (the second coder's defaults), 4 x 2^9 = 2,048 rows; each maps to one
second-coder row through `1:<14` -> (True, <14), `1:14-15` and `1:16-17` -> (True, 14+),
`1:>=18` -> (False, 14+), the other nine attributes by name. These 2,048 rows cover 1,536 of
the second coder's 2,048 rows; the 512 rows with `child_dependent` False and `child_age` <14
have no first-coder counterpart (63 of them are True).

* 1,792 rows agree: every comparable row valid for the first coder.
* 256 rows are EXCLUDED by the first coder (SPS-X1: principal caregiver with `children` = `1:>=18`) and evaluated by the second: 193 False, 63 True.

The 63 True rows are the second coder's (False, 14+) child with principal caregiver True, a
residential requirement, age 20+, and one of the 63 relationship combinations that satisfy
s 30. They are True because of the operator precedence at `sole_parent_support.py:180-181`
(`(dependent_child * age) < 14` holds for a non-dependent child), which both coders record
(`paperc-data-nz:paperC/specs/NZ-SPS/CONVERSION.md:26`,
`paperc-code2-nz:paperC/specs2/NZ-SPS/CONVERSION_2.md:88`). The first coder's SPS-X1 treats
"principal caregiver of a family whose only child is 18 or over" as impossible by definition
(`CONVERSION.md:20`), so those rows never reach the encoding there; the second coder
evaluates them. On rows both coders evaluate, the two ground truths agree completely.

### Judgements (NZ)

1. **Unit of an official case.** One person of one YAML case, as both coders do; for M2 (b) one placement per person and per week at which the case asserts an output (README rule in `m2_nz.py`, docstring). Weeks come from the period keys of the outputs; unkeyed outputs use the case's `period`.
2. **Value at a week.** An input keyed by periods takes the value whose period contains the Monday of the week (`period.start`, `period.first_day`, the first month of the first day: the days the formulas read, e.g. `sole_parent_support.py:130`, `:183`); `ETERNITY` covers every week; an unkeyed input applies to every week of the case. For principal caregiver only the month of the Monday is read; every case sets two months (`month:2019-01:2`), covering the whole week.
3. **Every person is placed, including partners and children.** The task asks to ignore household shape; the results restricted to applicants are reported beside (one extra unused value in each SPS table).
4. **Defined terms derived in the primary reading** when the case sets the leaves and the formula is a plain function of them: `age` from `date_of_birth` (`demographics/ages.py:45-53`); `social_security__dependent_children` from the family's members in role child (`interpretation/child.py:43-54`), each child dependent if `social_security__dependent_child` is set True, or if its age is under 18 and the case sets none of the inputs of financial independence (`interpretation/child.py:17-40`, `financially_independent.py:23-29`); `social_security__in_a_relationship` from an explicit family (principal with a member in role partner, `relationships.py:16-25`); the partner's AS receipt from the partner's own input. A case with no family (vector cases) leaves these UNKNOWN.
5. **First coder's cash assets** are the applicant's plus the partners' (`paperc-data-nz:paperC/specs/NZ-AS/CONVERSION.md:14`); unset members count 0.
6. **`accommodation_supplement__accommodation_costs` on the AS-1964 tables** (an input before 2018-11-26, a formula after): set by the case, or in the secondary reading computed by the 2018 formula (`costs.py:20-94`) from type, costs and tenancy/ownership roles for weeks from 2018-11-26, and default False (`costs.py:17`) before. The primary reading counts it known when the case sets the type or the costs.
7. **First coder's `children` label**: bands <14, 14-15, 16-17, >=18 of the family's child members; a child whose explicit `dependent_child` contradicts its band, or a family with three or more children, gets no label (UNKNOWN). **Second coder's child attributes**: a family with two children gives one placement per child (6 cases of `__split_care.yaml`).
8. **Values outside a declared enum** (`under_the_sun`, `under_the_moon` as accommodation type) stay UNKNOWN.
9. **Second coder's `age: 5` without period** (`CONVERSION_2.md:92-95`): this analysis applies an unkeyed value at the case's weeks (judgement 2), so the child is placed at age 5; the second coder reports that the simulation leaves it at -9999. Both fall in `<14`, so no count changes.
10. **Reason categories** follow each coder's own log text: "does not assert" -> other output or scope; "asserted for ... outside" and "not asserted at the fixed period" -> other period; "role child", "not the principal", "not exactly one principal and one child" -> other household shape; override of an intermediate variable and rows under the table's own exclusion -> other; cases in files the second coder's oracle does not read -> other.
11. **M6 label maps**: attributes paired in spec order for SLP and AS-1964 (same encoding variables in the same order, checked by name); SPS children mapped as above with financial independence False on the first side, which makes a child dependent exactly when under 18.

Problems found: (i) the first coder's claim that SLP-X1 never changes an outcome is wrong for
3 rows (`paperc-data-nz:paperC/specs/NZ-SLP/CONVERSION.md:16`); (ii) the second coder's SPS
oracle skips `sole_parent_support__benefit.yaml`, whose cases assert the entry variable,
three of them at the table's own week (`paperc-code2-nz:paperC/specs2/NZ-SPS/oracle.py:22`),
while its record says 2019-W05 is the period of every official test.
