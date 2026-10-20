# FR-AF-2: conversion record

Household amount regime of `InterfaceAllocationsFamiliales.i_montant_versé` at
2020-05-01 for households of exactly two children, by residence, resources and,
per child, age, earnings and care arrangement.

## Table-specific choices

**T1. Attributes.** `residence` (9), `ressources` (3 bands: at or below
plafond I, above I and at or below II, above II; A5), and for each of two
children `enfantK_age` (7 bands, A6), `enfantK_remuneration` (2 bands, A7),
`enfantK_prise_en_charge` (the 5 values of `PriseEnCharge`). 9 × 3 × (7 × 2 ×
5)² = 132 300 rows. The resources keep three bands (FR-AF-1 has five) to stay
under the 200 000-row limit with both children fully described.

**T2. Care arrangement.** L521-2 (securite_sociale_L.catala_fr:186-281) maps
the five arrangements to `prise_en_compte` Complète (EffectiveEtPermanente,
GardeAlternéeAllocataireUnique, ServicesSociauxAllocationVerséeÀLaFamille),
Partagée (GardeAlternéePartageAllocations: the amounts are halved) and Zéro
(ServicesSociauxAllocationVerséeAuxServicesSociaux: the child's share goes to
the services sociaux and the family's amount for the child is zero, official
Test9). The five values are kept as declared.

**T3. Fixed inputs.** `est_parent` vrai, `titre_I` faux,
`avait_enfant_avant_2012` faux (as in the official tests apart from Test12),
`a_déjà_ouvert` vrai and no housing aid for both children. With two children
the allocation forfaitaire, which needs three (D521-2 III,
securite_sociale_D.catala_fr:319), cannot apply, so `a_déjà_ouvert` has no
effect here; FR-AF-3 varies it.

**T4. Exclusions: none.** A young child with earnings above the ceiling is
unusual but no rule makes it impossible; the encoding ignores earnings before
the end of compulsory schooling for `droit_ouvert` (securite_sociale_L.catala_fr:52-58).

## Counts

132300 rows: `general_t1` 19200, `general_t2` 19200, `general_t3` 19200, `mayotte` 12048, `outre_mer_1_enfant` 29088, `zero` 33564.

## Within-band birth order (finding of the band-robustness check)

When both children fall in the same age band, the bands do not say which of
them is the elder; the table fixes it by the slot convention of A6 (slot 1 is
the elder by one day). The encoding reads that order through the eldest-child
test (`est_enfant_le_plus_âgé`, epilogue.catala_fr:33-35), which removes the
eldest from the L521-3 al. 1 majoration. `--self-check` separates the
alternatives that keep the children's birth order from those that reverse it:
keeping the order gives no label change; reversing it changes the label in a
few rows (counts in the self-check output below). All of them have the same
shape: an L751-1 residence, one child with `droit_ouvert` whose share is zero
(`ServicesSociauxAllocationVerséeAuxServicesSociaux`), and an elder or younger
child aged 16-19 without `droit_ouvert` (earnings above the ceiling). When the
child without `droit_ouvert` is the younger one it receives the D755-5
majoration (A11, second and third points), so the amount is positive
(`outre_mer_1_enfant`); when it is the elder, the amount is `zero`. A conversion
that orders same-band children differently gets a different label on these
rows; this is a consequence of the slot convention, recorded here.


## Official examples and unmapped tests (`python3 oracle.py --check-official`)

All 15 official scopes pass when run directly through the generated Python.
Mapping onto this table (A9):

```
Mapping of tests_allocations_familiales.catala_fr onto FR-AF-2:
  PASS  Test4: expected amount 99.46 -> general_t1; row ['Metropole', 'le_plafond_I', 'a11_14', 'le_plafond', 'EffectiveEtPermanente', 'a16_19', 'le_plafond', 'GardeAlterneePartageAllocations'] -> oracle general_t1
  PASS  Test6: expected amount 66.30 -> general_t2; row ['Guadeloupe', 'gt_I_le_II', 'a03_11', 'le_plafond', 'EffectiveEtPermanente', 'a00_03', 'gt_plafond', 'EffectiveEtPermanente'] -> oracle general_t2
  PASS  Test9: expected amount 0 -> zero; row ['Guadeloupe', 'gt_I_le_II', 'a16_19', 'gt_plafond', 'ServicesSociauxAllocationVerseeAuxServicesSociaux', 'a11_14', 'gt_plafond', 'ServicesSociauxAllocationVerseeAuxServicesSociaux'] -> oracle zero
  PASS  Test10: expected amount 99.46 -> general_t1; row ['Metropole', 'le_plafond_I', 'a16_19', 'le_plafond', 'EffectiveEtPermanente', 'a03_11', 'le_plafond', 'GardeAlterneePartageAllocations'] -> oracle general_t1

Mapped official examples: 4/4 agree with the oracle
Unmapped:
  Test1: 4 children; the table has 2 child slots
  Test2: 3 children; the table has 2 child slots
  Test3: 1 child(ren); the table describes households of exactly 2 children
  Test5: 1 child(ren); the table describes households of exactly 2 children
  Test7: date_courante 2021-02-01 lies outside the 2020 parameter period [2020-04-01, 2020-12-31] of this table
  Test8: date_courante 2021-01-01 lies outside the 2020 parameter period [2020-04-01, 2020-12-31] of this table
  Test11: date_courante 2021-12-31 lies outside the 2020 parameter period [2020-04-01, 2020-12-31] of this table
  Test12: date_courante 2019-08-26 lies outside the 2020 parameter period [2020-04-01, 2020-12-31] of this table
  Test13: date_courante 2019-08-26 lies outside the 2020 parameter period [2020-04-01, 2020-12-31] of this table
  Test14: date_courante 2022-05-01 lies outside the 2020 parameter period [2020-04-01, 2020-12-31] of this table
wrote /home/user/latc-check/paperC/specs/FR-AF-2/official_examples.csv: 4 rows
```

## Self-check output (`python3 oracle.py --self-check --sample 25`)

```
age bands: ok
earnings ceiling Metropole: encoding 943.02, spec 943.02: ok
earnings ceiling Mayotte: encoding 711.49, spec 711.49: ok
band robustness (every 25-th row):
  alternatives keeping the children's birth order: 54216 evaluations, 0 label changes
  alternatives reversing the birth order of two same-band children: 1728 evaluations, 42 label changes
```

## Common choices of the FR-AF tables (FR-AF-1, FR-AF-2, FR-AF-3)

Encoding: CatalaLang/catala-examples commit `2694b17ddd7c2246e207e8f077d586349ee5abea`,
compiled to Python with Catala 1.3.0 (`paperC/catala_family_benefits/`, unmodified).
`file:line` references point into that commit. Article numbers are those of the
Code de la sécurité sociale as cited in the Catala source.

**A1. Entry point: the wrapper `InterfaceAllocationsFamiliales`.** The wrapper
(epilogue.catala_fr:73-100) takes children as `EnfantEntrée` records without an
`obligation_scolaire` field and derives it from the date of birth
(epilogue.catala_fr:121-131, Code de l'éducation L131-1). Every official
household test calls this wrapper. Calling `AllocationsFamiliales` directly
would add `obligation_scolaire` as a free per-child input that the official
tests never set and that FR-PF already covers.

**A2. Fixed date 2020-05-01.** The date of seven of the fourteen household tests
(Test1-Test6, Test9) and of the FR-PF test. All date-dependent parameters are
constant on 2020-04-01 to 2020-12-31: SMIC 2020 (smic/Smic.catala_fr:80-110),
BMAF 414,4 € from 2020-04-01 (base_mensuelle_allocations_familiales/Bmaf.catala_fr:50-58),
household ceilings 2020 (decrets_divers.catala_fr:101-122) and the Mayotte rates
for 2020 (decrets_divers.catala_fr, Annexe of Décret n°2002-423). An official
test dated inside that period is mapped with its age bands computed against its
own date (Test10, dated 2020-04-20); a test dated outside it is listed as
unmapped. No date in the table reaches the validity assertions of `Smic`
(`>= 2019-01-01`, Smic.catala_fr:18) or `Bmaf` (`>= 2019-04-01`,
Bmaf.catala_fr:12), nor the Mayotte SMIC conflict of 2024.

**A3. Output labels (`regime_montant_verse`, FR-AF-1 and FR-AF-2; FR-AF-3 uses the component labels of its T5).** `i_montant_versé`
(epilogue.catala_fr:80, 90) is a sum of components (epilogue.catala_fr:45-52).
The label names the statutory case that sets the amount:

| Label | Condition | Statutory case |
|---|---|---|
| `zero` | `i_montant_versé = 0 €` | no allowance paid (fewer than two children with `droit_ouvert` outside the one-child exceptions, or every child's share at zero, for example placement with the services sociaux, L521-2 al. 4, securite_sociale_L.catala_fr:261-271) |
| `mayotte` | amount > 0 and résidence = Mayotte | Décret n°2002-423 art. 7: own base scale from the first child, resource-independent (decrets_divers.catala_fr:170-215) |
| `outre_mer_1_enfant` | amount > 0, résidence in L751-1 (Guadeloupe, Guyane, Martinique, La Réunion, Saint-Barthélemy, Saint-Martin) and exactly one child with `droit_ouvert` | L755-12 (entitlement from one child, no forfaitaire, no complément; securite_sociale_L.catala_fr:436-466) and D755-5 (single-child rate 5,88 %, securite_sociale_D.catala_fr:382-404) |
| `general_t1` | amount > 0 otherwise, `ressources_ménage <= plafond_I_d521_3` | L521-1 with D521-1 I 1° (securite_sociale_D.catala_fr:35, 58) |
| `general_t2` | amount > 0 otherwise, `plafond_I < ressources_ménage <= plafond_II` | D521-1 I 2° (securite_sociale_D.catala_fr:77-78, 102-103) |
| `general_t3` | amount > 0 otherwise, `ressources_ménage > plafond_II` | D521-1 I 3° (securite_sociale_D.catala_fr:120, 142) |

`zero` is read from the encoding's amount. For a positive amount the label is
the case whose conditions hold, with the number of children with `droit_ouvert`
(n) taken from the encoding (`PrestationsFamiliales.droit_ouvert` on each child
after the wrapper's transformation, as `enfants_à_charge_droit_ouvert_prestation_familiale`
counts them, securite_sociale_L.catala_fr:86-90) and the ceilings of A5. The
oracle stops with an error if an amount is positive while the general case
would need n >= 2 and n < 2; no row triggers it. The labels do not separate the
complément dégressif (D521-1 II), the allocation forfaitaire or the majorations:
they ride inside the regime's label. The tier also governs the Mayotte
majorations and forfaitaire, but `mayotte` is one label, because the Mayotte
base scale does not vary with resources.

**A4. REJECTED.** The encoding asserts L521-2 al. 3
(securite_sociale_L.catala_fr:240-246): `est_parent` or (`non est_parent` and
`titre_I`). A row with both false makes the generated code raise
`AssertionFailed` at securite_sociale_L.catala_fr:241.3-246.6; the row is
`REJECTED`. The statute does not make that situation impossible (L521-2 al. 3
opens the right from the father or the mother instead), so it is not declared
as an exclusion; the encoding leaves it unmodelled. No other error occurs at
2020-05-01.

**A5. Resource ceilings and representatives.** For 2020:
`plafond_I_d521_3 = 57 759 € + 5 775 € × n`, `plafond_II_d521_3 = 80 831 € + 5 775 € × n`
(Instruction DSS/SD2B/2019/261, decrets_divers.catala_fr:101-122), n as in A3.
Representatives: 30 000 € for the band at or below plafond I (the resources of
most official tests; below plafond I for every n), the exact ceiling for the
`eq_` bands, the midpoint `(plafond_I + plafond_II) / 2` (a whole number of
euros, since both ceilings are) for the band between the ceilings, and
150 000 € above plafond II. The midpoint lies above `plafond_I + 12 × allocation`
for every household of the tables, so the representatives of the general
tiers sit outside the complément dégressif zones; this does not affect the
labels (A3).

**A6. Age bands.** With `b` the date of birth and `dc = 2020-05-01`, every band
is the conjunction of comparisons the encoding makes:

| Label | Definition | Birth dates | Representative (slot 1) |
|---|---|---|---|
| `a00_03` | `b + 3 an >= dc` (Avant, epilogue.catala_fr:123) | from 2017-05-01, including births after `dc` | 2019-01-01 |
| `a03_11` | `b + 3 an < dc` and `b + 11 an > dc` | 2009-05-02 to 2017-04-30 | 2013-01-01 |
| `a11_14` | `b + 11 an <= dc` (D755-5, securite_sociale_D.catala_fr:419) and `b + 14 an > dc` | 2006-05-02 to 2009-05-01 | 2007-01-01 |
| `a14_16` | `b + 14 an <= dc` (L521-3 with R521-1 14 an, securite_sociale_L.catala_fr:319, securite_sociale_R.catala_fr:54) and `b + 16 an >= dc` (Pendant, epilogue.catala_fr:127) | 2004-05-01 to 2006-05-01 | 2005-01-01 |
| `a16_19` | `b + 16 an < dc` and `(b + 20 an) - dc >= 365 jour` | 2001-05-01 to 2004-04-30 | 2003-01-01 |
| `a19_20` | `(b + 20 an) - dc < 365 jour` (forfaitaire, securite_sociale_L.catala_fr:148-152) and `b + 20 an > dc` (L512-3 2°, securite_sociale_L.catala_fr:71) | 2000-05-02 to 2001-04-30 | 2000-08-01 |
| `a20_plus` | `b + 20 an <= dc` | up to 2000-05-01 | 1999-01-01 |

Further thresholds compared by the rules and left without a band of their own:
the 16 an of D755-5 (`b + 16 an > dc` / `<= dc`, securite_sociale_D.catala_fr:420, 431)
differs from the Pendant limit (`>=`) on the 16th birthday only, which lies in
`a14_16`; the 2008 rule (R521-1, securite_sociale_R.catala_fr:80-83:
`b + 11 an <= 2008-04-30` sets the majoration age at 16, 14 otherwise) concerns
births up to 1997-04-30, all inside `a20_plus`, where both ages are passed.
Neither changes a label (band robustness, A10).

Slot k's representative is the band representative plus k − 1 days, so that of
two children in the same band the lower slot is the elder. The eldest child
(`EnfantLePlusÂgé`, epilogue.catala_fr:11-23) is the one with the earliest birth
date. No representative is a 29 February.

**A7. Child earnings.** Two bands around the child earnings ceiling
`plafond_l512_3_2 = (smic.brut_horaire * 55%) * 169,0`
(securite_sociale_R.catala_fr:29-31, 218-223). With the runtime's rounding to the
cent after each multiplication (`Money.__mul__`,
runtime/catala/catala_runtime.py:564-566) the ceiling is 943,02 € (Mayotte
711,49 €) at 2020-05-01 (found by bisection on the encoding, `--self-check`).
`le_plafond` (rep. 0,00 €) includes the ceiling, since L512-3 2° and
`conditions_hors_âge` compare with `<=` (securite_sociale_L.catala_fr:70, 83);
`gt_plafond` (rep. 1 000,00 €) is above both ceilings. FR-PF keeps the
three-way split below / at / above; the FR-AF tables merge "at" into
`le_plafond` because the two behave identically.

**A8. Children list and fixed child fields.** The children of a row are the
child slots in slot order, given `d_identifiant` 0, 1, 2 in list order.
`d_identifiant` is read only through the record equality of the eldest-child
test (epilogue.catala_fr:33-35); distinct values keep two children with the
same birth date distinct. A child field that is not an attribute of the table
takes the value in `fixed_inputs` (with its label). An official test child maps
onto a table only if each of its fixed fields falls in the fixed label's band
(for example 439 € of earnings falls in `le_plafond`, whose representative is
0 €).

**A9. Official tests.** `--check-official` runs all fifteen official scopes
through the generated Python (15/15 pass), maps every household test it can
onto the table, computes the expected label from the test's expected amount and
its own inputs (A3), and checks the oracle's label for the mapped row. A test
maps when its date lies in the 2020 parameter period (A2), its number of
children fits the table, and every fixed input falls in the fixed band.
`tests_ouverture_droits.catala_fr` asserts per-child `droit_ouvert` and maps
onto FR-PF only.

**A10. Band robustness.** `--self-check` re-evaluates rows with each
alternative value of one attribute at a time: first and last birth dates of the
age band (plus two extra probes for the unbounded bands `a00_03`, `a20_plus`),
400,00 € and the ceiling for `le_plafond`, the ceiling + 0,01 € and 5 000,00 € for
`gt_plafond`, and the band ends of the resource bands (0 € and plafond I − 0,01 €
for `lt_plafond_I`; 0 € and plafond I for `le_plafond_I`; plafond I + 0,01 € and
plafond II − 0,01 € (or plafond II) for the middle band; plafond II + 0,01 € and
500 000 € above). It counts label changes, separately for alternatives that
keep the children's birth order and for alternatives that reverse the order of
two children in the same band (the bands do not fix that order; A6). Rows are
sampled (every 25th row) to keep the run under ten minutes per table. Results
are in the self-check output above.

**A11. Behaviour of the encoding recorded during the conversion (kept as is).**
These are properties of the encoding at commit 2694b17; the tables reproduce
them.

* The allocation forfaitaire (L521-1 al. 2) is paid for a child already past 20,
  without time limit, because `(b + 20 an) - dc < 365 jour` also holds for
  negative durations (securite_sociale_L.catala_fr:148-152). Example: Métropole,
  30 000 €, children born 2007-01-01 and 2009-01-01 receive 132,61 €; adding a
  child born 1990-01-01 gives 216,46 € (+ 83,85 € = 20,234 % × 414,4 €).
  `inputs.md` section 3.5 reports the same with a child born 1995.
* The majoration (L521-3) is computed over all `enfants_à_charge`
  (epilogue.catala_fr:39-43), and `droit_ouvert_majoration`
  (securite_sociale_L.catala_fr:315-342) does not require the child's own
  `droit_ouvert`. A child past 20 who is not the eldest therefore receives the
  majoration: the household above with children born 1990-01-01 and
  1995-01-01 added gets 366,61 € = 132,61 € + 2 × 83,85 € + 66,30 € (16 % × 414,4 €
  for the 25-year-old).
* `inputs.md` section 3.4 marks the D755-5 single-child majorations (3,69 % from
  11 years, 5,67 % from 16) as apparently unreachable. They are reachable when a
  household in an L751-1 territory has exactly one child with `droit_ouvert`
  and an elder child without it: Guadeloupe, children born 1999-01-01 and
  2005-01-01 gives 39,66 € = (5,88 % + 3,69 %) × 414,4 €. The labels do not
  distinguish this (`outre_mer_1_enfant`).
