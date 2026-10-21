# French family benefits: FR-PF and FR-AF (both conversions)

Scripts: `paperC/analysis/m2_fr_af.py` (writes `out/m2_fr_af.json`) and
`paperC/analysis/m6_fr_af.py` (writes `out/m6_fr_af.json`), both run with `python3.12 -I`
from the repository root after `paperC/analysis/fetch_sources.sh`. Branch commits read:
`origin/paperc-data-fr` 0aee62d (first conversion), `origin/paperc-code2-fr` c957417
(second conversion). Official tests: catala-examples 2694b17,
`allocations_familiales/tests/tests_ouverture_droits.catala_fr` (scope Test1, lines 61-67,
four `droit_ouvert` assertions) and `tests_allocations_familiales.catala_fr` (Test1-Test14,
one amount assertion each). The test files are parsed by `m2_fr_af.py` (`pf_children`,
`af_tests`); the parsed inputs equal the hand copies in the second coder's `oracle.py`.

## M2. Official tests and declared values

### Suites and mapped tests

| Rule | Suite | Cases |
|---|---|---:|
| FR-PF (`PrestationsFamiliales.droit_ouvert`) | tests_ouverture_droits Test1, one case per asserted child | 4 |
| FR-AF (`InterfaceAllocationsFamiliales.i_montant_versé`) | tests_allocations_familiales Test1-Test14 | 14 |

Both conversions map all 4 FR-PF cases. The FR-AF tests mapped are: first conversion
FR-AF-1 Test2, Test3, Test5; FR-AF-2 Test4, Test6, Test9, Test10; FR-AF-3 Test2. Second
conversion FR-AF-1 Test3, Test5; FR-AF-2 Test4, Test6, Test9, Test10; FR-AF-3 Test2. No FR-AF
test is mapped onto any table by either conversion when its date lies outside
2020-04-01..2020-12-31, which removes six tests (Test7, 8, 11, 12, 13, 14) from every table.

Unmapped household tests. Each cell gives every reason category that applies (computed by
`categories()` in `m2_fr_af.py`) and the line of the conversion record that states the
conversion's own reason. "period" = other period; "shape" = other household shape (number of
children outside the table's range); "fixed input" = an input that the table fixes lies outside
the fixed value's band (classified as "other" in the task's terms). No FR-AF test is of another
output or scope.

First conversion (stated lines in `paperc-data-fr:paperC/specs/<table>/CONVERSION.md`):

| Test (line) | date | children | FR-AF-1 | FR-AF-2 | FR-AF-3 |
|---|---|---:|---|---|---|
| Test1 (:66) | 2020-05-01 | 4 | shape; fixed input (stated: line 62) | shape (stated: line 73) | shape; fixed input (stated: line 73) |
| Test2 (:80) | 2020-05-01 | 3 | mapped | shape (stated: line 74) | mapped |
| Test3 (:94) | 2020-05-01 | 1 | mapped | shape (stated: line 75) | shape; fixed input (stated: line 74) |
| Test4 (:107) | 2020-05-01 | 2 | fixed input (stated: line 63) | mapped | shape; fixed input (stated: line 75) |
| Test5 (:120) | 2020-05-01 | 1 | mapped | shape (stated: line 76) | shape (stated: line 76) |
| Test6 (:132) | 2020-05-01 | 2 | fixed input (stated: line 64) | mapped | shape; fixed input (stated: line 77) |
| Test7 (:163) | 2021-02-01 | 4 | period; shape; fixed input (stated: line 65) | period; shape (stated: line 77) | period; shape; fixed input (stated: line 78) |
| Test8 (:176) | 2021-01-01 | 2 | period (stated: line 66) | period (stated: line 78) | period; shape; fixed input (stated: line 79) |
| Test9 (:206) | 2020-05-01 | 2 | fixed input (stated: line 67) | mapped | shape; fixed input (stated: line 80) |
| Test10 (:236) | 2020-04-20 | 2 | fixed input (stated: line 68) | mapped | shape; fixed input (stated: line 81) |
| Test11 (:266) | 2021-12-31 | 3 | period (stated: line 69) | period; shape (stated: line 79) | period (stated: line 82) |
| Test12 (:304) | 2019-08-26 | 4 | period; shape (stated: line 70) | period; shape; fixed input (stated: line 80) | period; shape; fixed input (stated: line 83) |
| Test13 (:351) | 2019-08-26 | 1 | period (stated: line 71) | period; shape (stated: line 81) | period; shape; fixed input (stated: line 84) |
| Test14 (:373) | 2022-05-01 | 2 | period; fixed input (stated: line 72) | period (stated: line 82) | period; shape; fixed input (stated: line 85) |

Second conversion (stated lines in `paperc-code2-fr:paperC/specs2/<table>/CONVERSION_2.md`):

| Test (line) | date | children | FR-AF-1 | FR-AF-2 | FR-AF-3 |
|---|---|---:|---|---|---|
| Test1 (:66) | 2020-05-01 | 4 | shape (stated: line 295) | shape (stated: line 301) | shape; fixed input (stated: line 292) |
| Test2 (:80) | 2020-05-01 | 3 | shape (stated: line 296) | shape (stated: line 302) | mapped |
| Test3 (:94) | 2020-05-01 | 1 | mapped | shape (stated: line 303) | shape (stated: line 293) |
| Test4 (:107) | 2020-05-01 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test5 (:120) | 2020-05-01 | 1 | mapped | shape (stated: line 303) | shape (stated: line 293) |
| Test6 (:132) | 2020-05-01 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test7 (:163) | 2021-02-01 | 4 | period; shape (stated: line 295) | period; shape (stated: line 301) | period; shape; fixed input (stated: line 292) |
| Test8 (:176) | 2021-01-01 | 2 | period; shape (stated: line 297) | period (stated: line 304) | period; shape (stated: line 293) |
| Test9 (:206) | 2020-05-01 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test10 (:236) | 2020-04-20 | 2 | shape (stated: line 297) | mapped | shape; fixed input (stated: line 293) |
| Test11 (:266) | 2021-12-31 | 3 | period; shape (stated: line 296) | period; shape (stated: line 302) | period (stated: line 294) |
| Test12 (:304) | 2019-08-26 | 4 | period; shape (stated: line 295) | period; shape (stated: line 301) | period; shape (stated: line 292) |
| Test13 (:351) | 2019-08-26 | 1 | period (stated: line 298) | period; shape (stated: line 303) | period; shape (stated: line 293) |
| Test14 (:373) | 2022-05-01 | 2 | period; shape (stated: line 297) | period (stated: line 305) | period; shape; fixed input (stated: line 293) |

Tests that the period alone keeps out (every other condition of the table holds): first
conversion FR-AF-1 Test8, Test11, Test13; FR-AF-2 Test8, Test14; FR-AF-3 Test11. Second
conversion FR-AF-1 Test13; FR-AF-2 Test8, Test14; FR-AF-3 Test11. Where several reasons
apply, the conversions state one: the first names the period first (for example Test7,
FR-AF-1 line 65), the second names the number of children first (Test7, Test12).

The second coder's README counts 18 cases for the French rules (the 4 FR-PF children plus
the 14 household tests, `paperc-code2-fr:paperC/specs2/README-FR-CODE2.md:52`); here each
rule's suite holds only the tests of its own scope, so FR-PF has 4 and FR-AF has 14.

### Declared-value usage, mapped tests against the whole suite

"Whole suite" places every test of the rule on the table's attributes with the table's own
labels and 2020-05-01 cut points, whatever its date, household shape or fixed inputs
(placement rules in Judgements 2-7). `missed_valid` is the number of valid rows outside the
product of the values observed (protocol C1).

| Conversion | Table | Suite | Mapped | Declared values | Unused (mapped) | Unused (whole suite) | missed_valid, mapped | missed_valid, whole suite | valid rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| first | FR-PF | 4 | 4 | 26 | 16 | 16 | 1 074 | 1 074 | 1 080 |
| first | FR-AF-1 | 14 | 3 | 44 | 32 | 18 | 138 224 | 136 000 | 138 240 |
| first | FR-AF-2 | 14 | 4 | 40 | 20 | 14 | 131 148 | 126 156 | 132 300 |
| first | FR-AF-3 | 14 | 1 | 39 | 27 | 14 | 175 615 | 175 232 | 175 616 |
| second | FR-PF | 4 | 4 | 13 | 5 | 5 | 66 | 66 | 72 |
| second | FR-AF-1 | 14 | 2 | 32 | 21 | 13 | 19 436 | 19 152 | 19 440 |
| second | FR-AF-2 | 14 | 4 | 40 | 19 | 13 | 195 678 | 186 462 | 196 830 |
| second | FR-AF-3 | 14 | 1 | 43 | 34 | 18 | 174 959 | 173 232 | 174 960 |

FR-PF variant (stated as a variant: the 14 household tests compute `droit_ouvert` for each
of their children inside the household amount and never assert it). Adding the 33 children
of the 14 household tests, with `obligation_scolaire` derived as the wrapper derives it
(catala-examples `allocations_familiales/epilogue.catala_fr:121-131`):

| Conversion | Declared | Unused (4 asserted children) | Unused (with the 33 household children) | missed_valid | valid rows |
|---|---:|---:|---:|---:|---:|
| first | 26 | 16 | 8 | 952 | 1 080 |
| second | 13 | 5 | 2 | 48 | 72 |

Values still unused in the variant: first FR-PF residence Martinique, LaReunion,
SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon; prise_en_charge
ServicesSociauxAllocationVerseeALaFamille; remuneration eq_plafond; apl true. Second FR-PF
remuneration_mensuelle entre_plafonds; aide_logement_personnelle true.

Per attribute (UNKNOWN = number of suite tests that cannot be placed on the attribute; in
every case the cause is a table slot with no child in the test, since every test sets every
input of its children and household):

**First FR-PF** (whole suite equals the mapped set): unused residence Guadeloupe, Guyane,
Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte;
obligation_scolaire Avant; prise_en_charge GardeAlterneePartageAllocations,
GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille,
ServicesSociauxAllocationVerseeAuxServicesSociaux; age a00_03; remuneration eq_plafond; apl true.

**First FR-AF-1**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 9 | Guadeloupe, Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte | Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon | 0 |
| ressources | 5 | eq_plafond_I, eq_plafond_II, gt_plafond_II | eq_plafond_I, eq_plafond_II, gt_plafond_II | 0 |
| avait_enfant_avant_2012 | 2 | true | none | 0 |
| est_parent | 2 | false | false | 0 |
| titre_I | 2 | true | true | 0 |
| enfant1_age | 8 | absent, a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | absent, a00_03, a19_20, a20_plus | 0 |
| enfant2_age | 8 | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | a19_20 | 0 |
| enfant3_age | 8 | a00_03, a03_11, a11_14, a14_16, a16_19, a19_20 | a00_03, a03_11, a19_20 | 0 |

**First FR-AF-2**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 9 | Guyane, Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte | Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon | 0 |
| ressources | 3 | gt_plafond_II | gt_plafond_II | 0 |
| enfant1_age | 7 | a00_03, a14_16, a19_20, a20_plus | a00_03, a19_20, a20_plus | 0 |
| enfant1_remuneration | 2 | none | none | 0 |
| enfant1_prise_en_charge | 5 | GardeAlterneePartageAllocations, GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille | the same three | 0 |
| enfant2_age | 7 | a14_16, a19_20, a20_plus | a19_20 | 3 |
| enfant2_remuneration | 2 | none | none | 3 |
| enfant2_prise_en_charge | 5 | GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille | ServicesSociauxAllocationVerseeALaFamille | 3 |

**First FR-AF-3** (residence and resources are fixed and not counted)

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| enfant1_age | 7 | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | a00_03, a19_20, a20_plus | 0 |
| enfant1_remuneration | 2 | gt_plafond | none | 0 |
| enfant1_deja_ouvert | 2 | false | false | 0 |
| enfant1_apl | 2 | true | true | 0 |
| enfant2_age | 7 | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus | a19_20 | 3 |
| enfant2_remuneration | 2 | gt_plafond | none | 3 |
| enfant2_deja_ouvert | 2 | false | false | 3 |
| enfant2_apl | 2 | true | true | 3 |
| enfant3_age | 7 | a00_03, a03_11, a11_14, a14_16, a16_19, a19_20 | a00_03, a03_11, a19_20 | 9 |
| enfant3_remuneration | 2 | gt_plafond | gt_plafond | 9 |
| enfant3_deja_ouvert | 2 | false | false | 9 |
| enfant3_apl | 2 | true | true | 9 |

**Second FR-PF** (whole suite equals the mapped set): unused residence drom_l751_1, mayotte;
obligation_scolaire Avant; remuneration_mensuelle entre_plafonds; aide_logement_personnelle true.

**Second FR-AF-1**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 3 | mayotte | none | 0 |
| attributaire | 3 | tiers_titre_I, aucun | tiers_titre_I, aucun | 0 |
| ressources | 5 | entre_plafonds_I_II, zone_degressive_II, au_dela_plafond_II | zone_degressive_II, au_dela_plafond_II | 0 |
| avant_2012 | 2 | true | none | 0 |
| e1_age | 9 | moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus | moins_3, anniversaire_16, 19_20, 20_23, 23_plus | 0 |
| e1_remuneration | 3 | entre_plafonds, au_dessus_plafonds | entre_plafonds | 0 |
| e1_prise_en_charge | 3 | partagee, services_sociaux | partagee | 0 |
| e1_deja_ouvert | 2 | false | false | 0 |
| e1_aide_logement | 2 | true | true | 0 |

**Second FR-AF-2**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 3 | mayotte | none | 0 |
| ressources | 5 | zone_degressive_I, zone_degressive_II, au_dela_plafond_II | zone_degressive_II, au_dela_plafond_II | 0 |
| avant_2012 | 2 | true | none | 0 |
| e1_age | 9 | moins_3, 14_16, anniversaire_16, 19_20, 20_23, 23_plus | moins_3, anniversaire_16, 19_20, 20_23, 23_plus | 0 |
| e1_remuneration | 3 | entre_plafonds | entre_plafonds | 0 |
| e1_prise_en_charge | 3 | partagee | partagee | 0 |
| e2_age | 9 | 14_16, anniversaire_16, 19_20, 20_23, 23_plus | 14_16, 19_20, 23_plus | 3 |
| e2_remuneration | 3 | entre_plafonds | entre_plafonds | 3 |
| e2_prise_en_charge | 3 | none | none | 3 |

**Second FR-AF-3**

| Attribute | Declared | Unused by mapped | Unused by whole suite | UNKNOWN |
|---|---:|---|---|---:|
| residence | 3 | drom_l751_1, mayotte | none | 0 |
| ressources | 5 | zone_degressive_I, entre_plafonds_I_II, zone_degressive_II, au_dela_plafond_II | zone_degressive_II, au_dela_plafond_II | 0 |
| avant_2012 | 2 | true | none | 0 |
| e1_age | 9 | moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus | moins_3, anniversaire_16, 19_20, 20_23, 23_plus | 0 |
| e1_deja_ouvert | 2 | false | false | 0 |
| e2_age | 9 | moins_3, 3_11, 14_16, anniversaire_16, 16_19, 19_20, 20_23, 23_plus | 14_16, 19_20, 23_plus | 3 |
| e2_deja_ouvert | 2 | false | false | 3 |
| e3_age | 9 | moins_3, 3_11, 11_14, 14_16, anniversaire_16, 16_19, 19_20, 23_plus | moins_3, 3_11, anniversaire_16, 19_20, 23_plus | 9 |
| e3_deja_ouvert | 2 | false | false | 9 |

Values that no official test reaches under any placement, in both conversions: a child aged
19 to 20 (`a19_20` / `19_20`, the forfaitaire window), a child under 3 in the first slot,
earnings exactly at the ceiling (first FR-PF), personal housing aid true, `déjà ouvert` false,
a person in charge who is not a parent (first `est_parent` false, `titre_I` true; second
`tiers_titre_I`), and resources above plafond II (in the second conversion both bands above plafond II,
`zone_degressive_II` and `au_dela_plafond_II`). Every test sets `déjà ouvert` vrai and housing aid faux.

Checks:
* Placing the mapped tests with the placement code reproduces every row of each
  `official_examples.csv` (12 first-conversion rows, 11 second-conversion rows; flag
  `placement_equals_mapped` in the JSON).
* The number of children with `droit_ouvert` computed by the three rules agrees with the
  encoding's own count for all 14 household tests.
* Shifting each test's children to 2020-05-01 at equal ages (Judgement 4) changes no age band
  of either conversion (0 mismatches over the 33 children).
* The mapped-only unused values equal, attribute by attribute, the lists in
  `paperc-data-fr:paperC/specs/README-FR.md:66` and
  `paperc-code2-fr:paperC/specs2/README-FR-CODE2.md` (sections from line 69). One discrepancy
  in the second README: its heading `FR-AF-1 (21 of 34 attribute values)`
  (`README-FR-CODE2.md:77`) gives 34 declared values; the spec declares 3+3+5+2+9+3+3+2+2 = 32,
  and the 21 listed values are right.

### H1 with the whole suite

H1's indicators per table: (1) unused declared values > 0; (2) `missed_valid` > 0.

| Conversion | Table | (1) mapped | (1) whole suite | (2) mapped | (2) whole suite |
|---|---|---|---|---|---|
| first | FR-PF | yes (16) | yes (16; variant 8) | yes | yes (variant yes, 952) |
| first | FR-AF-1 | yes (32) | yes (18) | yes | yes |
| first | FR-AF-2 | yes (20) | yes (14) | yes | yes |
| first | FR-AF-3 | yes (27) | yes (14) | yes | yes |
| second | FR-PF | yes (5) | yes (5; variant 2) | yes | yes (variant yes, 48) |
| second | FR-AF-1 | yes (21) | yes (13) | yes | yes |
| second | FR-AF-2 | yes (19) | yes (13) | yes | yes |
| second | FR-AF-3 | yes (34) | yes (18) | yes | yes |

Both indicators hold for every French family-benefit table of both conversions when the whole
suite is used. Using the whole suite lowers the unused count of an FR-AF table by 6 to 16 values (first
FR-AF-1 by 14, FR-AF-2 by 6, FR-AF-3 by 13; second FR-AF-1 by 8, FR-AF-2 by 6, FR-AF-3 by 16)
and leaves the FR-PF counts unchanged; the values that remain unused are values that no
official test sets (list above). The share of valid rows outside the product of observed
values falls from 99.1-100 % to 94.7-99.8 % for the FR-AF tables (lowest: second FR-AF-2,
186 462 of 196 830; first FR-AF-2, 126 156 of 132 300) and stays at 99.4 % (first) and
91.7 % (second) for FR-PF.

## M6. Agreement between the two conversions

### M6 (a) Attribute-level alignment

Tables are paired by household shape: first FR-AF-1 (0-3 children) contains the shapes of all
three second tables; first FR-AF-2 and second FR-AF-2 both have exactly 2 children; first
FR-AF-3 (exactly 3 children, Métropole, 30 000 EUR) is a slice of second FR-AF-3.

FR-PF:

| Encoding input | First conversion | Second conversion | Nesting | Sources |
|---|---|---|---|---|
| date_courante | fixed 2020-05-01 | fixed 2020-05-01 | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:101; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:113 |
| résidence | attribute, 9 collectivités | attribute, 3 classes: metropole = Métropole + SaintPierreEtMiquelon; drom_l751_1 = the 6 L751-1 territories; mayotte | first refines second | paperc-data-fr:paperC/specs/FR-PF/spec.json:21; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:50 |
| obligation_scolaire | attribute Avant / Pendant / Apres | attribute Avant / Pendant / Apres | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:28; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:40 |
| date_de_naissance | attribute `age`, cuts at 3, 16 and 20 years | attribute `age_20_ans`, cut at 20 years | first refines second (same strict comparison at 20) | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:59; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:110 |
| rémuneration_mensuelle | attribute, 3 bands relative to the residence's ceiling: below, equal to, above 943,02 EUR (Mayotte 711,49 EUR) | attribute, 3 absolute bands: [0; 711,49], (711,49; 943,02], above 943,02 EUR | cross: the first isolates the ceiling point of each residence; the second cuts at both ceilings for every residence | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:83; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:57 |
| prise_en_charge | attribute, 5 values (read by no rule of droit_ouvert) | fixed EffectiveEtPermanente | first varies, second fixes | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:52; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:97 |
| a_déjà_ouvert_droit_aux_allocations_familiales | fixed vrai | fixed vrai | coincide | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:98; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:121 |
| bénéficie_titre_personnel_aide_personnelle_logement | attribute `apl` | attribute `aide_logement_personnelle` | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:68; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:83 |
| identifiant | fixed 1 | fixed 1 | coincide | paperc-data-fr:paperC/specs/FR-PF/spec.json:102; paperc-code2-fr:paperC/specs2/FR-PF/spec.json:125 |
| exclusions | X1-X3, obligation_scolaire against the 3-, 16- and 20-year bands (2 160 of 3 240 rows) | X-PF-SCOL, Avant or Pendant at 20 or more (36 of 108 rows) | the first's exclusions contain the second's; the first also excludes Avant from age 3, Pendant under 3 or from 16, Apres under 16, which a single cut at 20 cannot express | paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:103; paperc-code2-fr:paperC/specs2/FR-PF/CONVERSION_2.md:119 |

FR-AF (the source line of each row, in each conversion's spec.json or conversion record, is in `out/m6_fr_af.json`, key `alignment`):

| Encoding input | First conversion | Second conversion | Nesting |
|---|---|---|---|
| date_courante | fixed 2020-05-01 | fixed 2020-05-01 | coincide |
| number of children | FR-AF-1: 0-3 (`absent` slots); FR-AF-2: 2; FR-AF-3: 3 | FR-AF-1: 1; FR-AF-2: 2; FR-AF-3: 3 | first FR-AF-1 covers the 1-, 2- and 3-child shapes; 0 children only in the first |
| i_résidence | 9 values (FR-AF-1, FR-AF-2); fixed Métropole (FR-AF-3) | 3 classes (all tables) | first refines second where both vary |
| i_ressources_ménage | FR-AF-1: below pI, = pI, between, = pII, above pII; FR-AF-2: <= pI, (pI; pII], > pII; FR-AF-3: fixed 30 000 EUR. pI = 57 759 + 5 775 n EUR, pII = 80 831 + 5 775 n EUR, n = children with droit_ouvert | 5 bands in all tables: <= pI, (pI; pI + 12a], (pI + 12a; pII], (pII; pII + 12a], > pII + 12a, a = the allocation the encoding computes | cross: both cut at pI and pII; the second adds the complément dégressif cuts pI + 12a and pII + 12a; the first FR-AF-1 isolates the points pI and pII. The second's 5 bands refine the first FR-AF-2's 3 |
| est_parent, remplit_titre_I | two attributes in FR-AF-1 (both false = REJECTED); fixed (vrai, faux) elsewhere | one attribute `attributaire` in FR-AF-1: parent (vrai, faux), tiers_titre_I (faux, vrai), aucun (EXCLUDED); (vrai, vrai) has no label of its own; fixed parent elsewhere | first refines second ((vrai, vrai) is its own cell in the first) |
| avait_enfant_à_charge_avant_1er_janvier_2012 | attribute (FR-AF-1); fixed faux (FR-AF-2, FR-AF-3) | attribute (all tables) | coincide where both vary |
| per-child date_de_naissance | 7 bands: a00_03, a03_11, a11_14, a14_16 (from the 14th birthday to the 16th birthday inclusive), a16_19, a19_20, a20_plus; slot k is k - 1 days younger than slot 1 | 9 bands: moins_3, 3_11, 11_14, 14_16 (16th birthday excluded), anniversaire_16 (the 16th birthday itself), 16_19, 19_20, 20_23, 23_plus (born on or before 1997-04-30); every slot uses the band's single representative | second refines first: a14_16 = 14_16 + anniversaire_16, a20_plus = 20_23 + 23_plus, the other bands coincide |
| per-child rémuneration | fixed 0 EUR (FR-AF-1); <= the residence's ceiling / above (FR-AF-2, FR-AF-3) | [0; 711,49], (711,49; 943,02], above (FR-AF-1, FR-AF-2); fixed 0 EUR (FR-AF-3) | second refines first (the first's cut is 711,49 in Mayotte and 943,02 elsewhere, both cuts of the second) |
| per-child prise_en_charge | fixed EffectiveEtPermanente (FR-AF-1, FR-AF-3); 5 values (FR-AF-2) | 3 classes complete / partagee / services_sociaux (FR-AF-1, FR-AF-2); fixed EffectiveEtPermanente (FR-AF-3) | first refines second where both vary |
| per-child a_déjà_ouvert | fixed vrai (FR-AF-1, FR-AF-2); attribute (FR-AF-3) | attribute (FR-AF-1, FR-AF-3); fixed vrai (FR-AF-2) | coincide where both vary |
| per-child housing aid | fixed faux (FR-AF-1, FR-AF-2); attribute (FR-AF-3) | attribute (FR-AF-1); fixed faux (FR-AF-2, FR-AF-3) | never varied by both in tables of the same shape |
| d_identifiant | fixed 0, 1, 2 in list order | fixed 1, 2, 3 in list order | coincide in effect |
| output | FR-AF-1, FR-AF-2: zero, general_t1-3, outre_mer_1_enfant, mayotte; FR-AF-3: zero, base, base_majoration, base_forfaitaire, base_majoration_forfaitaire | sans_droit or bareme/tier/parts (19, 54, 62 labels) | second refines first: each second label maps onto one first label (`coarsen` in m6_fr_af.py) |

### M6 (b, c) Row-level agreement

Method (`m6_fr_af.py`): direction A takes every row of the first table's slice, builds its
concrete inputs from the first coder's representatives, labels those inputs with the second
coder's cut points (the second's resource band through the encoding, since it depends on the
computed allocation), and compares the first ground truth with the second ground truth of that
row after coarsening the second label. Direction B does the same from the second table. Inputs
that one table fixes are restricted to the fixed value on the other side. The first coder's
representatives, run through the encoding, reproduce the first ground truth on every compared
row (0 failures).

Output coarsening (exact, since both labels are read from the same encoding result):
sans_droit and every `.../nul` -> zero; mayotte and mayotte_avant_2012 -> mayotte;
outre_mer_un_enfant -> outre_mer_1_enfant; general/Tk -> general_tk. For first FR-AF-3:
general/T1/B -> base, B+M -> base_majoration, B+F -> base_forfaitaire, B+M+F ->
base_majoration_forfaitaire.

| Pair | First slice | Second slice | Direction A rows: agree / disagree / invalid on a side | Direction B rows: agree / disagree / invalid on a side |
|---|---|---|---|---|
| FR-PF | prise_en_charge EffectiveEtPermanente (648 of 3 240 rows) | all 108 rows | 216 / 0 / 432 (first EXCLUDED: 324 with the second valid, 108 with the second EXCLUDED) | 36 / 0 / 72 (36 second valid with the first EXCLUDED, 36 both EXCLUDED) |
| P1 | FR-AF-1, one child in slot 1 | FR-AF-1, child earnings jusqu_plafond_mayotte, care complete, déjà ouvert true, housing aid false | 1 890 / 0 / 630 (first REJECTED, second EXCLUDED) | 540 / 0 / 270 (second EXCLUDED, first REJECTED) |
| P2 | FR-AF-1, two children in slots 1-2, parent | FR-AF-2, both children earnings jusqu_plafond_mayotte, care complete | 4 410 / 0 / 0 | 2 430 / 0 / 0 |
| P3 | FR-AF-1, three children, parent | FR-AF-3, déjà ouvert true for all | 30 870 / 0 / 0 | 21 870 / 0 / 0 |
| P4 | FR-AF-2, all rows | FR-AF-2, avant_2012 false | 131 964 / 336 / 0 | 98 255 / 160 / 0 |
| P5 | FR-AF-3, earnings le_plafond and housing aid false for all | FR-AF-3, metropole, jusqu_plafond_I, avant_2012 false | 2 744 / 0 / 0 | 5 832 / 0 / 0 |

FR-PF on the common refinement (residence 9 x obligation 3 x birth date on each side of 3,
16, 20 years x earnings 0 / 711,49 / 800 / 943,02 / 1 000 EUR x housing aid 2, care
EffectiveEtPermanente; 1 080 cells, each labelled into both tables): 360 agree, 0 disagree,
540 first EXCLUDED with the second valid, 180 EXCLUDED in both.

Explanation of every non-agreement:

1. **FR-PF, invalid on one side (direction A 324 rows, direction B 36 rows, common refinement
   540 cells).** All come from the exclusions. The first coder's X1-X3 use the 3- and 16-year
   cuts; the second coder has no such cut and excludes only Avant or Pendant at 20 or more.
   A second-coder row such as (Avant, moins_20) covers children under 3 (valid in the first)
   and children aged 3 to 19 (X1 in the first). In direction B, the second's representative of
   `moins_20` is born 2005-01-01 (aged 15), so its 36 (Avant, moins_20) and (Apres, moins_20)
   rows fall into the first's X1 and X3. On the outputs where both sides are valid there is no
   disagreement.
2. **FR-AF P1, invalid on both sides (630 and 270 rows).** The household where the person in
   charge is neither a parent nor meets Title I: REJECTED by the first coder (the encoding's
   L521-2 assertion fails, `paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:139`) and EXCLUDED
   by the second (`attributaire = aucun`, X-AF-ATTRIB, `paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:142`). Both sides keep the row out of the valid
   space; the conversions differ only in the status they give it.
3. **FR-AF P4, 336 (direction A) and 160 (direction B) disagreements, one cause.** In every
   disagreeing row the two children lie in the same first-coder age band (`a16_19` or `a19_20`),
   one child has `droit_ouvert` with its share paid to the services sociaux, and the other has
   earnings above the ceiling (no `droit_ouvert`). Re-evaluating the encoding with one input
   group swapped at a time, the only input whose swap flips the label is a child's birth date.
   The first coder makes slot 1 one day older than slot 2
   (`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:181`); the second gives both children
   the band's single representative date, and with equal dates the encoding treats the last
   child in list order as the eldest
   (`paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:171`). The eldest child is left out
   of the L521-3 al. 1 majoration, so which child is the eldest decides whether the
   non-entitled child adds a majoration: the amount is positive (outre_mer_1_enfant or mayotte)
   on one side and zero on the other. The first coder recorded the same effect in its own
   robustness check (`paperc-data-fr:paperC/specs/FR-AF-2/CONVERSION.md:39`). Groups:

   | Direction | Count | Residence | First output | Second output (coarsened) | Example (first row) |
   |---|---:|---|---|---|---|
   | A | 144 | L751-1 | outre_mer_1_enfant | zero | Guadeloupe, le_plafond_I, child 1 a16_19 le_plafond ServicesSociauxAllocationVerseeAuxServicesSociaux, child 2 a16_19 gt_plafond GardeAlterneePartageAllocations -> second outre_mer_un_enfant/nul |
   | A | 144 | L751-1 | zero | outre_mer_1_enfant | the same with the two children swapped -> second outre_mer_un_enfant/M |
   | A | 24 | Mayotte | mayotte | zero | Mayotte, the same children as the first example -> mayotte/T1/nul |
   | A | 24 | Mayotte | zero | mayotte | swapped -> mayotte/T1/M |
   | B | 40 | L751-1 | outre_mer_1_enfant | zero | second drom_l751_1, jusqu_plafond_I, 16_19 jusqu services_sociaux + 16_19 au_dessus complete (outre_mer_un_enfant/nul) -> first outre_mer_1_enfant |
   | B | 40 | L751-1 | zero | outre_mer_1_enfant | swapped (outre_mer_un_enfant/M) -> first zero |
   | B | 40 | Mayotte | mayotte | zero | mayotte, the same children (mayotte/T1/nul) -> first mayotte |
   | B | 40 | Mayotte | zero | mayotte | swapped (mayotte/T1/M) -> first zero |

   Each line of this table joins two groups of equal size, one with both children in
   `a16_19` and one with both in `a19_20` (72 + 72, 12 + 12, 20 + 20); the JSON lists every
   group with its row shapes (`shapes`) and one example. In every disagreeing row the entitled
   child has earnings `le_plafond` and care ServicesSociauxAllocationVerseeAuxServicesSociaux,
   and the other child has earnings `gt_plafond` with any other care arrangement. This is a property of the representatives: the age bands of
   both conversions leave the birth order of two same-band children open, and each coder closed
   it differently.

No other disagreement occurs: 0 in P1, P2, P3 and P5 in either direction, and 0 output
disagreements in FR-PF.

Where no row comparison was made, and why: the first FR-AF-1 rows with an `absent` slot
before a present one (they repeat a household of the canonical rows,
`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:25`); the first FR-AF-1 rows with no
child (no second-coder table); the first FR-AF-1 rows with est_parent and titre_I both true in
P2 and P3 (the second fixes (vrai, faux) there); first FR-PF rows with a prise_en_charge other
than EffectiveEtPermanente and first FR-AF-2 rows against second FR-AF-2 rows with avant_2012
true (each fixed on the other side); first FR-AF-3 rows with child earnings above the ceiling
or housing aid (fixed in the second FR-AF-3); and second-coder rows outside each slice.

## Judgements

1. **Suites.** FR-PF: the four asserted children of `tests_ouverture_droits.catala_fr` Test1
   (lines 61-67). FR-AF: the 14 household tests. The second README's count of 18 cases mixes
   both scopes (`paperc-code2-fr:paperC/specs2/README-FR-CODE2.md:52`).
2. **Ages at the test's own date.** Every age band is evaluated against the test's own
   `date_courante`, as both conversions do for Test10
   (`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:109`;
   `paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:36`).
3. **2020-05-01 cut points for every test.** Child earnings are cut at 943,02 / 711,49 EUR and
   household resources at the 2020 D521-3 ceilings (formula in
   `paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:148`) whatever the test's date; n
   (children with droit_ouvert) is computed by the three rules of droit_ouvert with
   obligation_scolaire derived as `epilogue.catala_fr:121-131` does, and checked against the
   encoding.
4. **Second coder's resource bands.** They depend on the computed allocation a
   (`paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:221`), so each test household is
   run through the unmodified Catala build (the second coder's `call_interface`) at 2020-05-01
   with its children's birth dates moved by (2020-05-01 - test date) days; this moves no child
   to another age band.
5. **Child slots in list order.** Both conversions place the test's children in list order
   (`paperc-data-fr:paperC/specs/FR-AF-1/CONVERSION.md:198`; the second's mapped rows, for
   example Test9). When a test has more children than slots, the first k children fill the
   slots, the household attributes (resources band) use the whole household, and the extra
   children are recorded as not placed (`children_not_placed` in the JSON). When it has fewer,
   the empty slots are UNKNOWN, except in the first FR-AF-1, whose declared value `absent` is
   the label of an empty slot (`CONVERSION.md:25`).
6. **Fixed inputs are not counted.** A table's fixed inputs (for example first FR-AF-3's
   residence and resources) add no declared value; a test whose value differs from the fixed one
   is still placed on the attributes.
7. **Second coder's `attributaire`.** Every test sets est_parent and leaves titre_I faux, which
   is `parent` (`paperc-code2-fr:paperC/specs2/FR-AF-1/CONVERSION_2.md:137`).
8. **Reason categories.** Each unmapped test gets every category that applies (period outside
   2020-04-01..2020-12-31, number of children outside the table's range, fixed input outside
   its band), next to the single reason the conversion record states.
9. **FR-PF variant.** The 33 household children are a variant only: their `droit_ouvert` is
   computed inside the household tests and never asserted
   (`paperc-data-fr:paperC/specs/FR-PF/CONVERSION.md:121`).
10. **M6 restrictions.** Rows are compared only where the fixed inputs coincide. First
    est_parent = titre_I = true is mapped to the second's `parent`, which the second coder
    states behaves the same (`CONVERSION_2.md:137`); this pair occurs only in P1, where all its
    rows agree.
11. **M6 label mapping.** Residence by the second coder's three classes; care arrangement by
    its three classes; ages and earnings through each side's representative values; outputs by
    `coarsen`.
