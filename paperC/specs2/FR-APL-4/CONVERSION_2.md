# FR-APL-4: conversion choices (second coder)

Sample `FR-APL-4`: APL eligibility under the conditions common to the personal housing
aids: nationality, main residence, IFI link, decency, subletting, family ownership and
usufruct, with two occupation modes. Fixed date 2020-03-10. 92,160 combinations.
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


## Attributes specific to FR-APL-4

* `residence`: `Metropole`, `LaReunion`, `Mayotte`. At the fixed date these conditions
  differ only for Mayotte (nationality, `code_construction_legislatif.catala_fr:1389-1402`);
  Métropole is the official value and La Réunion stands for the overseas departments under
  the general rules. Keeping all nine would exceed 200,000 combinations.
* `nationalite_demandeur`: `Francaise` and the four combinations of the two flags of
  `ConditionsÉtrangers` (`Etrangere_<l512_2>_<art_4_mayotte>`, T = vrai, F = faux).
  L822-2 reads the first flag (`:129-136`), the Mayotte rule the second and gives
  `Française` the value faux.
* `residence_principale`, `rattache_foyer_fiscal_parent_ifi`, `logement_decent`: booleans
  `oui`/`non` (`:42-46`, `:361-371`, `:381-384`).
* Subletting (L822-4, `:232-255`) as three attributes: `loue_ou_sous_loue_a_des_tiers`
  (`oui`/`non`), `age_personne_sous_location` and `sous_locataire_conforme_l442_1`, the
  last two `sans_objet` when the dwelling is not sublet. The age test calls
  `VérificationÂgeSupérieurÀ` with 30 years, which computes
  `date_naissance + 30 an > date_courante` (`prologue_france/prologue_france.catala_fr:31-39`):
  true for a person under 30. Labels and birth dates relative to 2020-03-10: `under_30`
  (1995-01-01), `30th_birthday_on_date` (1990-03-10, where the strict comparison gives
  faux), `over_30` (1980-01-01).
* `proprietaire_famille`, `usufruit_famille` (L822-3, `:171-221`; threshold 10 % at
  `code_construction_reglementaire.catala_fr:104-106`, compared with strict `<`):
  `autre` (`ParentOuAutre.Autre`), `parts_below_10pct` (0,05), `parts_10pct` (0,10, the
  boundary), `parts_above_10pct` (0,50).
* `mode_occupation`: `Locataire` (the base-case tenancy) and
  `AccessionProprieteLocalUsageExclusifHabitation` with an APL-eligible loan (D331_32,
  applicant, signed 2015-06-01, new dwelling). L822-3 1° applies to tenants only and the
  ownership branch of L822-2 reads `résidence_principale` a second time, so the two
  modes react differently to these conditions.

## Fixed inputs

`date_courante` 2020-03-10 (Exemple1). Everything else is the base case.

## Exclusions

* `sublet_details_iff_sublet`: the subtenant's age and L442-1 status are `sans_objet`
  exactly when `loue_ou_sous_loue_a_des_tiers == 'non'` (the constructor `Non` carries no
  `PersonneSousLocation`). 65,280 rows.

## REJECTED rows

None.

## Hand check

Per collectivity and nationality that passes (Métropole and La Réunion: Française,
Étrangère T_T and T_F; Mayotte: Étrangère T_T and F_T), with main residence, no IFI and a
decent dwelling: 5 accepted subletting cases × (4 accepted ownership/usufruct pairs for a
tenant + 16 for an owner) = 100, so 8 × 100 = 800 eligible rows, the count the encoding
returns.

## Official examples

`Exemple1` maps to (`Metropole`, `Francaise`, `oui`, `non`, `oui`, `non`, `sans_objet`,
`sans_objet`, `autre`, `autre`, `Locataire`) → `eligible`; 1 of 1 passes through the
encoding and through the oracle.

## Reproduction

```sh
cd paperC/specs2/FR-APL-4
python3.12 oracle.py --enumerate        # rewrites ground_truth.csv
python3.12 oracle.py --check-official   # official tests through the encoding and the oracle
```

`spec.json` and `official_examples.csv` are written by `oracle.py --write-spec --write-official`
from the same definitions. This conversion was made by the second coder without access to
the first coder's work (see `paperC/specs2/README-FR2-CODE2.md`).
