# FR-APL-5: conversion choices (second coder)

Sample `FR-APL-5`: APL eligibility by housing surface against household size
(R822-25, R844-4 and the Mayotte rule). Fixed date 2020-03-10. 33,120 combinations.
Source: catala-examples `2694b17`, Catala 1.3.0.

## Decision and split (common to FR-APL-1 to FR-APL-5)

* **Decision.** Output `éligibilité` of scope `ÉligibilitéAidePersonnaliséeLogement`
  (`aides_logement/prologue.catala_fr:378-404`), labels `eligible` (vrai) and
  `ineligible` (faux). It is the conjunction
  `condition_logement_bailleur et condition_logement_prêt et éligibilité_commune.éligibilité`
  (`code_construction_legislatif.catala_fr:631-645`), with a negative exception for
  Saint-Pierre-et-Miquelon from 2021-01-01 (`:1333-1339`).
  `éligibilité_commune.éligibilité` (scope `ÉligibilitéAidesPersonnelleLogement`,
  `prologue.catala_fr:336-341`) is `condition_nationalité et condition_logement_mode_occupation
  et éligibilité_logement`, and `éligibilité_logement` (`code_construction_legislatif.catala_fr:76-97`)
  is main residence, occupation mode, letting to third parties and surface, cancelled by
  the IFI condition (L822-8) or an indecent dwelling (L822-9).
* **Rules read.** Every definition of the variables above in the module
  `Aides_logement` was located with `grep` over `aides_logement/*.catala_fr` and read:
  `condition_logement_bailleur` at `code_construction_legislatif.catala_fr:669, 691, 738, 756, 1482`
  and `code_construction_reglementaire.catala_fr:3744, 3804, 6012`;
  `condition_logement_prêt` at `code_construction_legislatif.catala_fr:773-815`;
  `caractéristiques_prêt_l831_1_1` at `code_construction_reglementaire.catala_fr:3066, 3104`;
  `logement_situé_commune_déséquilibre_l831_2` at `arrete_2019-09-27.catala_fr:6070-6074`;
  `condition_nationalité` at `code_construction_legislatif.catala_fr:131, 1394`;
  `condition_logement_mode_occupation` at `:149, 186, 202`; `condition_logement_location_tiers`
  at `:235, 240`; `condition_non_ouverture_l822_8` at `:368`; `condition_non_ouverture_l822_9_decence_logement`
  at `:381`; `condition_ouverture_l822_10_peuplement_logement` at `:407`;
  `condition_logement_surface` at `code_construction_reglementaire.catala_fr:1030, 5533, 5541, 5616`;
  `seuil_l822_3_parts_*` at `:105-106`.
* **Split.** All inputs together far exceed 200,000 combinations, so the decision is cut
  into five sub-tables by the part of the law that reads each input. Each sub-table varies
  one group of inputs and holds all other inputs at the values of the base case:
  1. FR-APL-1: rented housing, lessor and its convention (L831-1 2°), by date and collectivity;
  2. FR-APL-2: logements-foyers, type and conventions (L831-1 5°, R832-20, R832-21, DROM rules);
  3. FR-APL-3: home ownership and location-accession, loan type, holder, signature date, age
     of the dwelling and zone (L831-1 1° and 6°, L831-2, R832-5, R832-7, arrêté art. 49);
  4. FR-APL-4: common conditions (nationality, main residence, IFI, decency, subletting,
     family ownership) at a fixed date;
  5. FR-APL-5: surface against household size (R822-25, R844-4, Mayotte rule) at a fixed date.
* **Base case.** The only official test of this scope, `Exemple1`
  (`tests/tests_eligibilite_apl.catala_fr:8-107`): Métropole, date 2020-03-10, married on
  2010-11-26, three children (born 2001-01-01 after compulsory schooling and in studies,
  2009-01-01 and 2012-01-01 in compulsory schooling, French, no shared custody, no pay,
  already entitled to family allowances), one other occupant, received benefits
  AllocationSoutienEnfantHandicapé, ComplémentFamilial and AllocationsFamiliales, tenant of a
  conventioned social lessor (rent 750 €, solidarity reduction 0 €), Zone1, 80 m², main
  residence, decent, owner and usufruct `Autre`, not sublet, no IFI link, no child to be born,
  R844-4 faux, French applicant born 1970-05-02 with all three applicant flags faux. Choosing
  the official test as base case lets it map onto every sub-table whose varied inputs cover it.
* **Inputs left at the base case everywhere.** Received benefits, children's details,
  rent amount, applicant birth date and applicant flags: no rule of the eligibility
  decision reads them, apart from the children's count (FR-APL-5) and the evaluation of
  the family-benefits sub-scope, which reads the children and can only raise errors.
* **Output labels.** `eligible` / `ineligible`; `REJECTED` when the generated Python
  raises (always a Catala `Conflict`, `NoValue` or assertion; each case listed below);
  `EXCLUDED` when an exclusion predicate of `spec.json` holds (checked before running).
* **Official examples.** `tests_eligibilite_apl.catala_fr` holds three test scopes.
  `Exemple1` asserts `ÉligibilitéAidePersonnaliséeLogement.éligibilité = vrai`.
  `Exemple2` (line 109) and `Exemple3` (line 195) assert the output of the different scope
  `ÉligibilitéAllocationLogement` (allocation de logement, type
  `TypeÉligibilitéAllocationLogement`) and cannot map onto an APL table.
* **Representatives of intervals.** The first value of each interval, with two stated
  exceptions (the interval holding the official test date uses that date; an interval
  open on the left uses its last value).


## Attributes specific to FR-APL-5

* `residence`: `Metropole`, `LaReunion`, `Mayotte`. Mayotte has its own minimum
  surfaces (13 m² for a couple, cap 54 m² from 9 persons,
  `code_construction_reglementaire.catala_fr:5613-5645`); the others use R822-25
  (`:1015-1057`).
* `nationalite_demandeur`: `Francaise` (Exemple1) and `Etrangere_T_T`. A French
  applicant is never eligible in Mayotte, so without the second value the Mayotte
  surface rule would never be visible.
* `situation_familiale`: the six values of `SituationFamiliale`; R822-25 counts one
  person (9 m²) for `Célibataire` and `CélibataireSéparéDeFait`, two (16 m², 13 m² in
  Mayotte) for the others. `Mariés` carries the date 2010-11-26 of Exemple1.
* `nombre_autres_occupants_logement` 0 to 3 and `nombre_personnes_a_charge` 0 to 4: each
  adds a person and 9 m². The ranges reach 9 persons, enough for the 70 m² cap
  (8 persons and more) and the Mayotte 54 m² cap (9 persons and more). The code counts
  every dependant in the list (`nombre de ménage.personnes_à_charge`); a household with
  k dependants takes the first k children of Exemple1, then children born 2012-01-01.
* `surface_m_carres`: integer intervals bounded by every threshold the code compares the
  surface against for these households: the R822-25 minima 9 + 9n and 16 + 9n (cap 70),
  the Mayotte minima 9 + 9n and 13 + 9n (cap 54), and the R844-4 values 9 and 16
  (`:5530-5545`). Thresholds 9, 13, 16, 18, 22, 25, 27, 31, 34, 36, 40, 43, 45, 49, 52,
  54, 58, 61, 63, 67, 70, 72 give 23 intervals; the representative is the lower bound,
  and 8 for `below_9`. Check: every integer surface from 0 to 99 was run for every row
  (144,000 runs) and gave the same output as the interval's representative.
* `personnes_agees_handicapees_foyer_r844_4`: `oui`/`non` (R844-4).

## Fixed inputs

`date_courante` 2020-03-10. Everything else is the base case.

## Exclusions

None.

## REJECTED rows (2,648)

Mayotte with `personnes_agees_handicapees_foyer_r844_4 = oui`, whenever the Mayotte
surface rule and an R844-4 rule both apply: both are exceptions to the label `base` of
`condition_logement_surface`, and the generated code raises `Conflict`
(`code_construction_reglementaire.catala_fr:5645` with `:5538` or `:5545`). The
conflict arises for both nationalities (1,324 rows each), since the scope evaluates the
surface condition whatever the nationality. The other Mayotte rows with R844-4 are those
where at most one of the two rules applies: 8 eligible and 1,428 ineligible with
`Etrangere_T_T`, 1,436 ineligible with `Francaise`.

## Official examples

`Exemple1` maps to (`Metropole`, `Francaise`, `Maries`, `1`, `3`, `from_72` for 80 m²,
`non`) → `eligible`; 1 of 1 passes through the encoding (80 m²) and through the oracle
(representative 72 m²).

## Reproduction

```sh
cd paperC/specs2/FR-APL-5
python3.12 oracle.py --enumerate        # rewrites ground_truth.csv
python3.12 oracle.py --check-official   # official tests through the encoding and the oracle
```

`spec.json` and `official_examples.csv` are written by `oracle.py --write-spec --write-official`
from the same definitions. This conversion was made by the second coder without access to
the first coder's work (see `paperC/specs2/README-FR2-CODE2.md`).
