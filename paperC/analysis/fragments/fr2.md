## FR-APL and US-121

Sources. First conversion: `origin/paperc-data-fr2` (FR-APL-1 to -5, US-121-1) and
`origin/paperc-data-fr2-fix` (US-121-2 as corrected on 2026-10-20). Second conversion:
`origin/paperc-code2-fr2`. Official tests: catala-examples `2694b17`,
`aides_logement/tests/tests_eligibilite_apl.catala_fr` (3 test scopes) and
`us_tax_code/tests/test_section_121.catala_en` (6 test scopes). Scripts:
`tests_fr2.py` (reads the tests, with the line of every value), `m2_fr2.py`,
`m6_fr2.py`; output `out/m2_fr2.json`, `out/m6_fr2.json`.

### M2. Official tests and declared values

Unit: one test scope (one taxpayer per placement in US-121-1, see J-US1). Both
conversions map whole test scopes, so the counts below are in the conversions' own unit.

| Rule | Conv. | Table | Suite tests | Mapped | Declared values | Unused, mapped tests | Unused, whole suite | Unknown placements | missed_valid, mapped | missed_valid, whole suite | Valid rows |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FR-APL | 1 | FR-APL-1 | 3 | 1 | 20 | 17 | 15 | 0 | 174 | 171 | 175 |
| FR-APL | 1 | FR-APL-2 | 3 | 1 | 44 | 37 | 32 | 0 | 67,139 | 67,116 | 67,140 |
| FR-APL | 1 | FR-APL-3 | 3 | 1 | 24 | 16 | 15 | 0 | 3,599 | 3,598 | 3,600 |
| FR-APL | 1 | FR-APL-4 | 3 | 0 | 24 | 24 | 20 | 12 | 952 | 952 | 952 |
| FR-APL | 1 | FR-APL-5 | 3 | 0 | 23 | 23 | 19 | 15 | 2,520 | 2,520 | 2,520 |
| FR-APL | 2 | FR-APL-1 | 3 | 1 | 24 | 20 | 17 | 0 | 709 | 702 | 710 |
| FR-APL | 2 | FR-APL-2 | 3 | 0 | 27 | 27 | 23 | 12 | 2,272 | 2,272 | 2,272 |
| FR-APL | 2 | FR-APL-3 | 3 | 0 | 36 | 36 | 30 | 15 | 49,500 | 49,500 | 49,500 |
| FR-APL | 2 | FR-APL-4 | 3 | 1 | 33 | 22 | 21 | 0 | 26,879 | 26,878 | 26,880 |
| FR-APL | 2 | FR-APL-5 | 3 | 1 | 45 | 38 | 32 | 0 | 30,471 | 30,424 | 30,472 |
| US-121 | 1 | US-121-1 | 6 | 4 | 7 | 3 | 3 | 0 | 2 | 2 | 4 |
| US-121 | 1 | US-121-2 | 6 | 2 | 20 | 11 | 10 | 16 | 202 | 201 | 204 |
| US-121 | 2 | US-121-1 | 6 | 4 | 24 | 18 | 18 | 0 | 96 | 96 | 100 |
| US-121 | 2 | US-121-2 | 6 | 2 | 25 | 13 | 12 | 16 | 736 | 728 | 744 |

"Unknown placements" counts (test, attribute) pairs where a test has no value for the
attribute. The mapped-only columns reproduce every list of "declared values that the
official examples never use" in `paperc-data-fr2:paperC/specs/README-FR2.md:67-97` (first conversion; the corrected US-121-2 list is unchanged in `paperc-data-fr2-fix`) and
`README-FR2-CODE2.md:80-90` (second conversion), table by table.

**Unmapped tests and reasons.**

| Conv. | Tables | Test | Category | Detail | Conversion's own statement |
|---|---|---|---|---|---|
| 1, 2 | every FR-APL table | Exemple2, Exemple3 | other output or scope | assert `ÉligibilitéAllocationLogement.éligibilité` (`tests_eligibilite_apl.catala_fr:116`, `:202`), the allocation de logement | first: `paperc-data-fr2:paperC/specs/README-FR2.md:57-58`; second: `paperc-code2-fr2:paperC/specs2/FR-APL-1/CONVERSION_2.md:59-63` |
| 1 | FR-APL-4, FR-APL-5 | Exemple1 | other: housing tenure fixed by the table | Exemple1 is a tenancy (`Locataire`, `tests_eligibilite_apl.catala_fr:71`); FR-APL-4 fixes a logement-foyer, FR-APL-5 home ownership | `paperc-data-fr2:paperC/specs/FR-APL/FR-APL-4/CONVERSION.md:83-85`, `FR-APL-5/CONVERSION.md:81-83` |
| 2 | FR-APL-2, FR-APL-3 | Exemple1 | other: housing tenure fixed by the table | as above (FR-APL-2 logement-foyer, FR-APL-3 home ownership) | `paperc-code2-fr2:paperC/specs2/README-FR2-CODE2.md:68-69` |
| 1, 2 | US-121-1 | Test5, Test6 | other output or scope | assert `Section121TwoPersons.income_excluded_from_gross_income` (`test_section_121.catala_en:139`, `:158`) | first: `paperc-data-fr2:paperC/specs/US-121/US-121-1/CONVERSION.md:104-105`; second: `paperc-code2-fr2:paperC/specs2/US-121-1/CONVERSION_2.md:95-97` |
| 1, 2 | US-121-2 | Test1-Test4 | other output or scope | assert `Section121SinglePerson.requirements_met` (`test_section_121.catala_en:79`, `:94`, `:109`, `:124`) | first: `paperc-data-fr2-fix:paperC/specs/US-121/US-121-2/CONVERSION.md:112`; second: `paperc-code2-fr2:paperC/specs2/US-121-2/CONVERSION_2.md:100-101` |

No test of these rules is unmapped for its period or household shape: every fixed date
of these tables is the date of a test, and Exemple2 and Exemple3 fall in declared date
bands where a table has a date attribute.

**What the whole suite adds** (declared values used by some unmapped test and by no
mapped test):

| Conv. | Table | Values newly used | Attributes with unknown placements |
|---|---|---|---|
| 1 | FR-APL-1 | date `2021-01-01_to_2023-12-31`; residence `LaReunion` | none |
| 1 | FR-APL-2 | residence `LaReunion`; situation `Concubins`; dependants `1`, `2`; other occupants `0` | none |
| 1 | FR-APL-3 | bailleur `BailleurPrive` | none |
| 1 | FR-APL-4 | residence `Metropole`, `LaReunion`; dates `2019-09-01_to_2020-12-31`, `2021-01-01_to_2023-04-04` | the four foyer attributes (3 tests each) |
| 1 | FR-APL-5 | zone `Zone1`, `Zone2`; date `ge_2019-10-01`; residence_principale `vrai` | mode, loan type, holder, signature date, age of dwelling (3 tests each) |
| 2 | FR-APL-1 | date `2021-05-01_to_2023-04-04`; residence `LaReunion`; bailleur `prive` | none |
| 2 | FR-APL-2 | dates `2019-10-01_to_2020-12-31`, `2021-05-01_to_2023-04-04`; residence `Metropole`, `LaReunion` | the four foyer attributes (3 tests each) |
| 2 | FR-APL-3 | the same two dates and two residences; zone `Zone1`, `Zone2` | mode, loan type, holder, signature date, age of dwelling (3 tests each) |
| 2 | FR-APL-4 | residence `LaReunion` | none |
| 2 | FR-APL-5 | residence `LaReunion`; situation `Concubins`; occupants `0`; dependants `1`, `2`; surface `58_to_60` | none |
| 1 | US-121-1 | none (Test5's and Test6's taxpayers fall in labels Test1-Test4 already use) | none |
| 1 | US-121-2 | person 1 use `lt_730_days` (Test2, Test3) | return type and the three person-2 attributes (Test1-Test4) |
| 2 | US-121-1 | none | none |
| 2 | US-121-2 | person 1 use `under_730d` (Test2, Test3) | as for the first conversion |

Read as single returns (J-US2), Test1-Test4 would lower the first conversion's
US-121-2 count to 9 unused values (missed_valid 198) and leave the second conversion's at
12 (missed_valid 728).

**H1 indicators with the whole suite.** In all 14 tables both indicators stay positive:
the whole suite leaves between 3 (first US-121-1) and 32 (first FR-APL-2, second
FR-APL-5) declared values unused, and the product of the observed values still misses
valid rows in every table (smallest case: 2 of 4 valid rows in the first US-121-1).
The largest drop in unused values is 6 (second FR-APL-3, 36 to 30; second FR-APL-5,
38 to 32). For FR-APL the reason is that the three tests share one household type (a
tenant, French applicant, Locataire of a social or private landlord, decent main
residence, no family ownership, no letting), so the slice dropped only two of them and
the two it dropped repeat most of Exemple1's values. For US-121 every test uses
`NoOtherSaleWhereSection121aApplied` (`test_section_121.catala_en:41`, `:48`, `:54`,
`:61`, `:78`, `:93`, `:108`, `:123`), so every earlier-sale label stays unused whatever
the slice.

### M6(a). Attribute-level alignment

The two coders split FR-APL differently: the first by subject with five tables (1 date,
territory and nationality; 2 floor area and household; 3 tenancy conditions;
4 logement-foyer; 5 home buyers), the second by the part of the law (1 tenancy landlord;
2 logement-foyer; 3 home ownership; 4 common conditions; 5 floor area). Every other
input is held at Exemple1's value in both conversions (first: `FR-APL-1/CONVERSION.md:82-92`;
second: `FR-APL-1/CONVERSION_2.md:42-55`), except where stated.

| Encoding input | First conversion | Second conversion | Nesting |
|---|---|---|---|
| `date_courante` | attribute in 1 (6 bands, cuts 2019-01-01, 2019-09-01, 2021-01-01, 2024-01-01, 2024-11-01; `FR-APL-1/CONVERSION.md:40-47`), 4 (5 bands from 2019-09-01, cuts 2021-01-01, 2023-04-05, 2024-01-01, 2024-11-01; `FR-APL-4/CONVERSION.md:33`), 5 (2 bands, cut 2019-10-01; `FR-APL-5/CONVERSION.md:44`); fixed 2020-03-10 in 2, 3 | attribute in 1, 2, 3 (8 bands from 2019-09-01, cuts 2019-10-01, 2021-01-01, 2021-05-01, 2023-04-05, 2023-09-01, 2024-01-01, 2024-11-01; `FR-APL-1/CONVERSION_2.md:74-84`); fixed 2020-03-10 in 4, 5 | from 2019-09-01 the second refines each first-conversion date attribute; the first adds two bands before 2019-09-01 (all REJECTED), which the second leaves outside its domain (`CONVERSION_2.md:76`) |
| `ménage.résidence` | 9 values in 1, 2, 4; fixed Métropole in 3, 5 | 9 values in 1, 2, 3; 3 values (Métropole, La Réunion, Mayotte) in 4, 5 (`FR-APL-4/CONVERSION_2.md:73-76`) | coincide where both declare 9; the second's 3 are a subset |
| `demandeur.nationalité` | 5 values (Française and the four flag pairs) in 1, 2; fixed Étrangère {vrai, vrai} in 4 (`FR-APL-4/CONVERSION.md:45-48`); fixed Française in 3, 5 | 5 values in 4; 2 values (Française, Étrangère T_T) in 5; fixed Française in 1, 2, 3 | the five labels coincide; the second's FR-APL-5 pair is a subset |
| `situation_familiale` | 6 values in 2 | 6 values in 5 | coincide |
| number of dependants | `0`-`3` in 2 (first k children of Exemple1) | `0`-`4` in 5 (first k of Exemple1, then children born 2012-01-01) | the second extends the range; equal households for k <= 3 |
| `nombre_autres_occupants_logement` | `0`, `1` in 2 | `0`-`3` in 5 | the second extends |
| `surface_m_carrés` | 16 bands, cuts 9, 13, 16, 18, 22, 25, 27, 31, 34, 36, 40, 43, 45, 49, 52 (`FR-APL-2/CONVERSION.md:52-56`) | 23 bands, the same cuts plus 54, 58, 61, 63, 67, 70, 72 (`FR-APL-5/CONVERSION_2.md:87-93`) | the second refines (its extra cuts serve households of 7 to 9 persons, which the first does not declare) |
| `personnes_âgées_handicapées_foyer_r844_4` | bool in 2 | bool in 5 | coincide |
| `logement.mode_occupation` | Locataire/SousLocataire in 3; RésidentLogementFoyer fixed in 4; AccessionPropriété/LocationAccession in 5; Locataire fixed in 1, 2 | Locataire/SousLocataire in 1; RésidentLogementFoyer fixed in 2; AccessionPropriété/LocationAccession in 3; Locataire/AccessionPropriété in 4; Locataire fixed in 5 | the same constructors, assigned to different tables |
| landlord (`TypeBailleur` with its flag) | 5 values in 3 | 5 values in 1 | coincide |
| `propriétaire`, `usufruit` (family share) | 3 values: Autre, < 10 %, >= 10 % (`FR-APL-3/CONVERSION.md:35-40`) | 4 values: autre, < 10 %, = 10 %, > 10 % (`FR-APL-4/CONVERSION_2.md:91-94`) | the second refines |
| `loué_ou_sous_loué_à_des_tiers` | one attribute, 5 values: Non; under 30 / 30 or more × L442-1 yes/no (`FR-APL-3/CONVERSION.md:41-48`) | three attributes (sublet yes/no; age sans_objet / under 30 / 30th birthday on the date / over 30; L442-1 sans_objet / yes / no) with an exclusion that removes the combinations describing no input (`FR-APL-4/CONVERSION_2.md:83-90`, `:107-109`) | the second refines (it splits "30 or more" at the 30th birthday) |
| `logement_decent_l89_462`, `condition_rattaché_foyer_fiscal_parent_ifi` | bool in 3 | bool in 4 | coincide |
| `résidence_principale` | bool in 3 and 5 | bool in 4; fixed vrai in 3 | coincide |
| foyer type and three conventions | attributes in 4 | attributes in 2 | coincide; the first declares two exclusions (`FR-APL-4/CONVERSION.md:60-65`), the second none |
| loan type, holder, signature date, age of dwelling, zone | attributes in 5; signature cuts 2017-12-31, 2018-01-01, 2020-01-01 | attributes in 3, the same cuts (`FR-APL-3/CONVERSION_2.md:105-109`) | coincide (representatives differ inside the bands) |
| loan record amounts and entry date | 500 €, entry 2010-01-01 | 700 €, entry = earlier of the signature and decision dates | fixed differently; both record them as unread by eligibility |
| foyer `date_conventionnement` | 2000-01-01 | 2010-01-01 | fixed differently; both record it as unread |
| benefits received, children's details, rent, applicant's birth date and flags | fixed at Exemple1 | fixed at Exemple1 | same fixed values |

US-121:

| Encoding input | First conversion | Second conversion | Nesting |
|---|---|---|---|
| `date_of_sale_or_exchange`, `return_date` | fixed 2021-01-01 | fixed 2021-01-01 | coincide |
| `property_ownage`, `property_usage_as_principal_residence` | 2 bands of the five-year aggregate, < 730 and >= 730 days, in both tables (`US-121-1/CONVERSION.md:25-43`) | US-121-1: 10 list shapes (`CONVERSION_2.md:41-61`); US-121-2: the two bands of the first conversion (`CONVERSION_2.md:52-56`) | US-121-1: the second refines (each shape lies on one side of 730 days); US-121-2: coincide |
| `other_section_121a_sale` | 3 values: none, 1 day to 2 years before, more than 2 years (`US-121-1/CONVERSION.md:45-57`; the same-day sale is in no label) | 4 values: none, under 2 years (2020-01-01), exactly 2 years (2019-01-01), over 2 years (`CONVERSION_2.md:34-36`) | the second's two inner values lie in the first's `within_2_years`; whether the second's `under_2_years_before` holds the same-day sale is not stated, so the two cross at that single date |
| `gain_from_sale_or_exchange_of_property` | fixed $350,000 in US-121-1; in US-121-2 3 bands (0, 250,000), [250,000, 500,000), [500,000, ∞) (`US-121-2/CONVERSION.md:50`, `:68-69`) | fixed $350,000 in US-121-1; in US-121-2 3 bands under 250,000 / 250,000 to 500,000 / over 500,000 (`CONVERSION_2.md:60-64`) | coincide apart from $0, which the first leaves out, and the boundary points, which the second does not assign |
| `return_type` | single, joint, surviving spouse | the same three | coincide |
| person 2 on a one-person return | single: the same taxpayer, other person-2 values EXCLUDED; surviving spouse: the deceased spouse's record, varied (correction, `US-121-2/CONVERSION.md:148-221`) | `not_applicable`; the deceased spouse's record fixed to `person_ok_1` (`CONVERSION_2.md:73-77`) | different representations; the scope reads neither record (`US-121-2/CONVERSION.md:204-212`) |
| `date_of_spouse_death` | fixed 2020-12-31 | fixed 2020-06-01 | fixed differently; unread by `Section121TwoPersons` |

Observation on the second conversion's US-121-2 exclusion. Its description says it removes
non-joint rows "when ... some person-2 attribute has a value"
(`paperc-code2-fr2:paperC/specs2/US-121-2/CONVERSION_2.md:81-84`), and the predicate
`(return_type == 'joint_return') == (p2_own == 'not_applicable' or p2_use == 'not_applicable' or p2_other == 'not_applicable')`
removes non-joint rows only when no person-2 attribute is `not_applicable`. The 2,688
single and surviving-spouse rows with a partly filled person 2 therefore stay in V
(672 labelled, 2,016 REJECTED; `m6_fr2.py`, pair US-121-2, "B rows without
counterpart"). They describe no return. Of the 744 labelled valid rows of that table, 72
describe a well-formed return.

Observation on line references. The second conversion cites the five-year aggregation
of `section_121.catala_en` at lines 205-222 and the 730-day comparisons at 224-240
(`US-121-1/CONVERSION_2.md:20-24`); at commit `2694b17` they are at lines 179-191 and
196-205, which the first conversion cites. The content quoted matches the code.

### M6(b-c). Row-level agreement

A pair compares a first-coder table A with a second-coder table B. Each side is
restricted to the values equal to the other side's fixed inputs, and each B row is mapped
onto the A row whose labels contain B's values (B refines A on every shared attribute
used). The output labels map one to one (`eligible`/`eligible`,
`ineligible`/`not_eligible`; `met`/`requirements_met`; `zero`/`no_exclusion`,
`full_gain`/`entire_gain`, `capped_at_250000`/`limited_to_250000`,
`capped_at_500000`/`limited_to_500000`). EXCLUDED and REJECTED are compared as labels.

| Pair | A (first) | B (second) | Restriction | B rows compared | Agree | Both valid (agree) | A rows of the slice reached |
|---|---|---|---|---|---|---|---|
| tenancy, date × territory | FR-APL-1 | FR-APL-1 | A: Française; B: Locataire, social conventionné | 72 | 72 | 71 (71) | 36 of 54 |
| nationality | FR-APL-1 | FR-APL-4 | A: date band of 2020-03-10, 3 territories; B: other attributes at Exemple1 | 15 | 15 | 15 (15) | 15 of 15 |
| floor area | FR-APL-2 | FR-APL-5 | A: 3 territories, 2 nationalities; B: occupants 0-1, dependants 0-3 | 13,248 | 13,248 | 11,784 (11,784) | 9,216 of 9,216 |
| common conditions | FR-APL-3 | FR-APL-4 | A: Locataire, social conventionné; B: Métropole, Française, Locataire | 896 | 896 | 896 (896) | 360 of 360 |
| landlord | FR-APL-3 | FR-APL-1 | A: other attributes at Exemple1; B: band of 2020-03-10, Métropole | 10 | 10 | 10 (10) | 10 of 10 |
| logement-foyer | FR-APL-4 | FR-APL-2 | none | 2,304 | 1,454 | 1,540 (1,426) | 1,440 of 1,440 |
| home buyers | FR-APL-5 | FR-APL-3 | A: main residence; B: Métropole | 5,760 | 5,760 | 5,580 (5,580) | 1,440 of 1,440 |
| §121(a) | US-121-1 | US-121-1 | none | 400 | 400 | 100 (100) | 12 of 12 |
| §121 amount | US-121-2 | US-121-2 | B rows with a well-formed person 2 | 864 | 864 | 72 (72) | 504 of 1,296 |

Agreement is complete in eight of the nine pairs, REJECTED rows included (1,464 in the
floor-area pair, 300 and 792 in the US pairs) and EXCLUDED rows included (the 180
home-buyer rows with a loan signed after the decision date, which both coders exclude by
the same rule: first `FR-APL-5/CONVERSION.md:59`, second `FR-APL-3/CONVERSION_2.md:128-132`).

Rows without a counterpart, explained:

* tenancy pair: 18 A rows (dates before 2019-09-01, all REJECTED) lie outside B's date
  domain.
* common-conditions pair: 2,176 B rows of the slice are EXCLUDED by
  `sublet_details_iff_sublet`. They are combinations of B's three sublet attributes
  that encode no input; A's single sublet attribute has no such combinations.
* §121 amount pair: B's 2,928 EXCLUDED rows and its 2,688 rows with a partly filled person
  2 on a one-person return (observation above) have no A counterpart. A's 396 single rows
  with person-2 labels different from person 1 (EXCLUDED in A) and A's 396 surviving-spouse
  rows whose deceased spouse differs from `person_ok_1` (B fixes that record) have no B
  counterpart; on these 396 surviving-spouse rows A's outputs do not depend on the
  person-2 labels (`US-121-2/CONVERSION.md:204-212`).

**Disagreements: the logement-foyer pair (850 rows).**

1. *A excludes, B evaluates: 736 rows.* A declares two exclusions and B none.
   `drom_convention_outside_drom` (a DROM convention outside the five DROM): 448 B rows
   (208 eligible, 240 ineligible). `fjt_type_without_l353_2_convention` (a young-workers
   foyer type without the livre III convention that defines it): 224 B rows (74 eligible,
   146 ineligible, 4 REJECTED). Both exclusions hold: 64 B rows (26 eligible, 38
   ineligible). A's sources: `paperc-data-fr2:paperC/specs/FR-APL/FR-APL-4/CONVERSION.md:60-65`.
   B states every combination possible (`FR-APL-2/CONVERSION_2.md:115-117`). The
   disagreement is about the valid space; the encoding returns a value for these rows.
2. *A eligible, B ineligible: 114 rows, all in Mayotte.* The fixed applicant differs:
   A fixes an Étrangère meeting both nationality conditions
   (`FR-APL-4/CONVERSION.md:45-48`), B keeps Exemple1's Française. The Mayotte rule of
   `condition_nationalité` returns faux for a Française
   (`code_construction_legislatif.catala_fr:1389-1402`, recorded by both coders: first
   `FR-APL-1/CONVERSION.md:135-140`, second `FR-APL-2/CONVERSION_2.md:126`). Outside
   Mayotte all 1,426 rows valid on both sides agree, which also confirms that the other
   difference in fixed inputs (`date_conventionnement`) has no effect on eligibility.

No sound mapping is needed for the rest of FR-APL: every first-coder table is covered by
at least one pair above (FR-APL-1 by two, FR-APL-3 by two).

### Judgements

* J-APL1. Exemple2 and Exemple3 are placed on the APL tables through their `ménage`,
  `demandeur` and `date_courante`, which have the same types as the APL scope's inputs
  (`tests_eligibilite_apl.catala_fr:117-192`, `:203-260`). They assert another scope's
  output (`:116`, `:202`), which M2(b) ignores.
* J-APL2. The dependants label is the number of `EnfantÀCharge` in the test's list
  (Exemple2: 2, `tests_eligibilite_apl.catala_fr:126-148`; Exemple3: 1, `:212-223`). The
  first coder's label k is "the first k children of Exemple1" and the rule counts the list
  (`paperc-data-fr2:paperC/specs/FR-APL/FR-APL-2/CONVERSION.md:31-34`); the second
  coder's likewise (`paperc-code2-fr2:paperC/specs2/FR-APL-5/CONVERSION_2.md:82-86`).
* J-APL3. A tenancy has no foyer type, foyer conventions, loan, loan holder, signature
  date or age-of-dwelling field, so these attributes are unknown for all three tests;
  `mode_occupation` is unknown in the home-buyer tables because `Locataire` is not one of
  their labels. `zone` and `résidence_principale` are set by every test
  (`tests_eligibilite_apl.catala_fr:68-69`, `:153-154`, `:227-228`) and are placed.
* J-APL4. Floor area 60 m² (Exemple2 `:178`, Exemple3 `:246`) is `ge_52` (first) and
  `58_to_60` (second); 80 m² (Exemple1 `:93`) is `ge_52` and `from_72`, as both
  conversions mapped it.
* J-US1. US-121-1 describes one taxpayer; each person of a test is one placement, so
  Test5 gives `person_ok_1` and Test6 gives `person_ok_1` and `person_ok_2`
  (`test_section_121.catala_en:138`, `:154-155`). The five-year aggregate is computed
  with `section_121.catala_en:179-191` (`tests_fr2.aggregate_days`): `person_ok_2`'s use
  counts 366 + 365 = 731 days.
* J-US2. Test1-Test4 run `Section121SinglePerson`, which has no return type, so in
  US-121-2 their return type and person 2 are unknown. Reading them as single returns
  (the first coder's convention for one taxpayer, `US-121-2/CONVERSION.md:63-65`) is the
  variant reported above.
* J-US3. The gain of every test is $350,000 (`test_section_121.catala_en:21`), in the
  middle band of both conversions.
* J-M6. Row mappings use each label's definition (cut points), and the representatives
  of B fall inside the mapped A label in every case: dates (A
  `FR-APL-1/CONVERSION.md:40-47`, `FR-APL-4/CONVERSION.md:33`, `FR-APL-5/CONVERSION.md:44`;
  B `FR-APL-1/CONVERSION_2.md:74-84`), surfaces (A `FR-APL-2/CONVERSION.md:52-56`; B
  `FR-APL-5/CONVERSION_2.md:87-93`), shares and third-party ages (A
  `FR-APL-3/CONVERSION.md:35-48` and band check `:71-75`; B `FR-APL-4/CONVERSION_2.md:83-94`),
  §121 lists and earlier sales (A `US-121-1/CONVERSION.md:32-57`; B
  `US-121-1/CONVERSION_2.md:45-56`, `:34-36`). For the nationality pair, B's fixed
  date 2020-03-10 is A's representative of `2019-09-01_to_2020-12-31`
  (`FR-APL-1/CONVERSION.md:44`).
