# FR-PF: conversion choices (second coder)

Rule: `PrestationsFamiliales.droit_ouvert` (`pro:46-58`), the per-child entitlement to
family benefits, in the Python build `generated.Allocations_familiales.prestations_familiales(...)
.droit_ouvert(enfant)`. This file is `CONVERSION_2.md`: it plays the part of the
`CONVERSION.md` of FORMAT.md, named as the second-coder task asks.

## Sources

* Rules: CatalaLang/catala-examples, commit `2694b17ddd7c2246e207e8f077d586349ee5abea`.
  Paths below are relative to that repository; `L:`, `R:`, `D:` abbreviate
  `allocations_familiales/securite_sociale_{L,R,D}.catala_fr`, `epi:` abbreviates
  `allocations_familiales/epilogue.catala_fr`, `pro:` abbreviates
  `allocations_familiales/prologue.catala_fr`, `dec:` abbreviates
  `allocations_familiales/decrets_divers.catala_fr`.
* Executable: `paperC/catala_family_benefits/generated/` (Catala 1.3.0 Python build of
  the same commit), unedited. The line references `gen:` are to
  `generated/Allocations_familiales.py`.
* Every choice below was made by reading these sources and running the encoding. No
  other conversion of these rules was consulted (see `../README-FR-CODE2.md`).

## Choices shared by the French samples of the second coder

### C1. Fixed date: 2020-05-01

`date_courante` is fixed at 2020-05-01. Reasons: it is the date of the only
`PrestationsFamiliales` test (`tests/tests_ouverture_droits.catala_fr:62`) and of 7 of the
14 household tests; and on the period 2020-04-01 to 2020-12-31 every date-dependent
parameter is constant: BMAF 414,40 EUR (`base_mensuelle_allocations_familiales/Bmaf.catala_fr:52-58`),
SMIC 10,15 EUR and 7,66 EUR for Mayotte (`smic/Smic.catala_fr:81-112`), plafonds of
D521-3 for 2020 (`dec:102-123`), Mayotte rates for 2020 (`dec:389-398`, `dec:481-487`,
`dec:562-568`). The date is later than both validity assertions (SMIC from 2019-01-01,
BMAF from 2019-04-01) and earlier than the 2024 Mayotte SMIC overlap, so no cell can
raise a Catala error because of the date.

An official test is mapped only when its date lies in that period; its ages are then
measured at its own date. Test10 (2020-04-20) is mapped this way.

### C2. Residence: three labels

`France.Collectivité` has nine values (`prologue_france/France.catala_fr:9-18`). The
encoding distinguishes them only through three predicates: `régime_outre_mer_l751_1`
(six values, `L:376-385`), `résidence = Mayotte` (`dec:181-238`, `dec:286-569`,
`smic/Smic.catala_fr:103-112`), and the SMIC rule for every other value
(`smic/Smic.catala_fr:81-95`, which lists Métropole and Saint-Pierre-et-Miquelon with
the six overseas values). Labels:

| label | members | representative |
|---|---|---|
| `metropole` | Métropole, SaintPierreEtMiquelon | Métropole |
| `drom_l751_1` | Guadeloupe, Guyane, Martinique, LaRéunion, SaintBarthélemy, SaintMartin | Guadeloupe |
| `mayotte` | Mayotte | Mayotte |

`oracle.py --check-groups` re-evaluates rows with every other member in place of the
representative; the result is in `../README-FR-CODE2.md`.

### C3. Child's monthly earnings: three intervals

The only comparison on `rémuneration_mensuelle` is `<= plafond_l512_3_2` (`L:70`, `L:83`),
with `plafond_l512_3_2 = (smic.brut_horaire * 55%) * 169,0` (R512-2 `R:29-31`; R755-0-2
`R:218-223` gives the same formula overseas). At 2020-05-01 the encoding gives
711,49 EUR for Mayotte and 943,02 EUR elsewhere (checked by bisection through the
encoding; `oracle.py` re-checks both cut points on every run). Cutting at both values
gives `jusqu_plafond_mayotte` = [0; 711,49] (representative 0,00),
`entre_plafonds` = (711,49; 943,02] (800,00), `au_dessus_plafonds` = (943,02; +inf)
(1500,00). Negative earnings are outside the domain.

### C4. Who has `droit_ouvert`

Not a choice: the encoding computes it (L512-3 `L:52-72`; L821-3 exception
`autres_codes.catala_fr:22-26`). Facts used in the choices below: a child before or
within compulsory schooling is entitled whatever its earnings; after compulsory
schooling, it needs earnings under the ceiling and age under 20; holding personal
housing aid removes the entitlement in every case.

## Mapping official tests

An official test maps onto a table when (i) it uses the table's entry point and number
of children, (ii) its date lies in the period of C1, (iii) each input falls in the region
of a declared label, and (iv) each input that is fixed in the table falls in the region of
the fixed value (for earnings: the band of 0,00 EUR). Its `output` is the label computed
from the encoding at the official inputs; `--check-official` checks that the encoding
reproduces the official expected value, and that the oracle at the representatives of
the mapped row returns the same label. Every official test is run through the encoding
in every folder; the per-folder list of unmapped tests with reasons is below.

## Choices for FR-PF

### P1. Attributes

The scope takes `date_courante`, `résidence` and the `Enfant` record (`pro:22-29`). The
rule reads four fields of `Enfant`: `obligation_scolaire`, `rémuneration_mensuelle`,
`date_de_naissance`, `bénéficie_titre_personnel_aide_personnelle_logement` (`L:52-84`,
`autres_codes.catala_fr:22-26`). These four plus `résidence` are the attributes.
The other fields (`identifiant`, `prise_en_charge`,
`a_déjà_ouvert_droit_aux_allocations_familiales`) are never read by `droit_ouvert` and
are fixed (`fixed_inputs`).

| attribute | values | source |
|---|---|---|
| `residence` | metropole, drom_l751_1, mayotte | C2 |
| `obligation_scolaire` | Avant, Pendant, Apres (representative of `Apres`: `Après`) | `pro:17-20`, `L:56-57`, `L:69` |
| `remuneration_mensuelle` | jusqu_plafond_mayotte, entre_plafonds, au_dessus_plafonds | C3 |
| `age_20_ans` | moins_20 (born 2005-01-01), 20_ou_plus (born 1998-01-01) | `L:71`, R512-2 `R:21` |
| `aide_logement_personnelle` | false, true | `autres_codes.catala_fr:22-26` |

`obligation_scolaire` stays an attribute of its own because in this scope it is an input
(`pro:24`); only the household wrapper derives it from age (`epi:121-131`).

### P2. Age: one cut, at 20

The only age comparison in the rule is `enfant.date_de_naissance + âge_l512_3_2 >
date_courante` with `âge_l512_3_2 = 20 an` (`L:71`, `R:21`). So `age_20_ans` has two
labels: `moins_20` when the 20th birthday is after the date, `20_ou_plus` otherwise
(the 20th birthday itself counts as 20, since the comparison is strict). The ages 3 and
16 of compulsory schooling are not compared in this scope; they enter only through the
exclusion below.

### P3. Exclusion X-PF-SCOL

`obligation_scolaire in ('Avant', 'Pendant') and age_20_ans == '20_ou_plus'`. Compulsory
schooling runs from 3 to 16 (Code de l'éducation L131-1, encoded at `epi:104-136`, where
`Pendant` ends on the 16th birthday), so a child aged 20 or more is always `Après`. The
encoding would answer `ouvert` for such a record (`L:56-58` does not look at age), which
no real child can produce. 36 of the 108 rows are excluded.

### P4. Output

`droit_ouvert`: `ouvert` when the encoding returns true, `non_ouvert` otherwise.

### P5. Errors

No cell raises an error in the encoding (REJECTED = 0).

### P6. Official tests

`tests/tests_ouverture_droits.catala_fr` Test1 (`:61-67`) holds four assertions on four
children (`:14-54`) at 2020-05-01 in Métropole; each child is one row of
`official_examples.csv` (case ids `tests_ouverture_droits/Test1/enfant1` to `enfant4`).
All four map: enfant1 (Pendant, 0 EUR, born 2007) -> ouvert; enfant2 (Après, 1000 EUR,
born 2003) -> non_ouvert; enfant3 (Après, 400 EUR, born 2003) -> ouvert; enfant4 (Après,
0 EUR, born 1999, so 21) -> non_ouvert.

The 14 scopes of `tests/tests_allocations_familiales.catala_fr` assert the household
amount and never `droit_ouvert`; they are run through the encoding (all pass) and are
not rows of this table. The separate module `prestations_familiales/` (scope
`ÉligibilitéPrestationsFamiliales`) has its own tests; that scope is a different entry
point and is outside this sample.
