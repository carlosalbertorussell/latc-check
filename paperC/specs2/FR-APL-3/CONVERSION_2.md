# FR-APL-3: conversion choices (second coder)

Sample `FR-APL-3`: APL eligibility for home ownership and location-accession, by loan
type, holder, signature date, age of the dwelling, zone, date and collectivity.
51,840 combinations. Source: catala-examples `2694b17`, Catala 1.3.0.

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


## Attribute `date_courante` (FR-APL-1, -2, -3)

Cuts are the dates the encoding compares `date_courante` against on the path to
`éligibilité`, plus the bounds outside which the encoding raises:

| Label | Representative | Why the interval starts here |
|---|---|---|
| `2019-09-01_to_2019-09-30` | 2019-09-01 | first date with a definition of `personnes_à_charge_prises_en_compte` (`archives.catala_fr:10-14`); earlier dates raise `NoValue` (and before 2019-01-01 the SMIC raises `NoValue`), so they are outside the table |
| `2019-10-01_to_2020-12-31` | 2020-03-10 | Zone III rule of L831-2 applies from 2019-10-01 (`arrete_2019-09-27.catala_fr:6070-6074`); representative = date of `Exemple1` |
| `2021-01-01_to_2021-04-30` | 2021-01-01 | Saint-Pierre-et-Miquelon exclusion (`code_construction_legislatif.catala_fr:1333-1339`); `date_entrée_vigueur_différée_cch` (`code_construction_reglementaire.catala_fr:6207`) |
| `2021-05-01_to_2023-04-04` | 2021-05-01 | deferred date for home ownership (`code_construction_reglementaire.catala_fr:6209-6213`) |
| `2023-04-05_to_2023-08-31` | 2023-04-05 | DROM exclusion of young-workers foyers (`code_construction_reglementaire.catala_fr:6001-6018`) |
| `2023-09-01_to_2023-12-31` | 2023-09-01 | end of the archived dependants rules, start of the current ones (`archives.catala_fr:10-24`, `code_sécurité_sociale.catala_fr:188-221`) |
| `2024-01-01_to_2024-10-31` | 2024-01-01 | two concurrent Mayotte SMIC definitions (`smic/Smic.catala_fr:431-500`) make the scope raise `Conflict` for Mayotte |
| `from_2024-11-01` | 2024-11-01 | end of the overlapping Mayotte SMIC definitions |

Other dated definitions in the module (yearly amounts, SMIC and BMAF revaluations,
`plafond_individuel_l815_9_sécu`) feed amounts or the treatment of dependants other than
children; for the households of these tables they leave `éligibilité` unchanged, so they
were left as interior points of these intervals.


## Attributes specific to FR-APL-3

* `residence`: all nine collectivities (see FR-APL-1).
* `mode_occupation`: `AccessionPropriétéLocalUsageExclusifHabitation` (L831-1 1°,
  `code_construction_legislatif.catala_fr:668-677`) and `LocationAccession` (L831-1 6°,
  `:755-763`). Both carry a `Propriétaire` with a `Prêt`.
* `type_pret`: the five values of `TypePrêt`. R832-5 (`code_construction_reglementaire.catala_fr:3065-3073`)
  accepts D331_32 and D331_63_64 held by the applicant; R832-7 (`:3103-3111`) accepts
  D331_59_8 and D331_76_1 held by the vendor.
* `titulaire_pret`: the two values of `TitulairePrêt`. Both are kept for both modes:
  the encoding reads R832-7 into `caractéristiques_prêt_l831_1_1`, which serves the
  ownership mode, so a vendor-held loan under `AccessionPropriété...` is the only path to
  R832-7 that the code offers.
* `date_signature_pret`, cut where L831-2 compares (`code_construction_legislatif.catala_fr:772-815`):
  `before_2017-12-31` (representative 2017-12-30, the interval is open on the left),
  `on_2017-12-31` (2017-12-31: the base exclusion uses `>= 2017-12-31` while the exception
  starts at `>= 2018-01-01`, so this single day has its own outcome), `2018-01-01_to_2019-12-31`
  (2018-01-01) and `from_2020-01-01` (2020-01-01).
* `anciennete_logement`: `neuf`, `ancien_ameliore_par_occupant`, `ancien_non_ameliore_par_occupant`
  (`NeufOuAncien`, `AmélioréParOccupant`); the L831-2 exception asks for `Ancien` of either kind.
* `zone`: `Zone1`, `Zone2`, `Zone3`. Zone III is the commune list of L831-2 last
  paragraph from 2019-10-01 (`arrete_2019-09-27.catala_fr:6070-6074`).

## Fixed inputs

`Propriétaire` fields that the eligibility rules do not read: monthly payment 700 €,
charges 0 €, no works (`PasDeTravaux` for D832-15 and R842-5), not a first occupation,
no copropriété, `situation_r822_11_13_17` faux, `opérations_logement_évolutifs_sociaux...`
faux, `accord_financement_représentant_État_outre_mer` `PasdAccord`. `date_entrée_logement`
= the earlier of the signature and current-date representatives, so the occupant never
moves in after the current date. All other inputs are the base case (Zone replaced by the
attribute). `résidence_principale` stays vrai, which the ownership branch of L822-2
requires (`code_construction_legislatif.catala_fr:146-160`); FR-APL-4 varies it.

## Exclusions

* `loan_signed_after_current_date`: `date_signature_pret == 'from_2020-01-01'` and
  `date_courante == '2019-09-01_to_2019-09-30'`. A loan signed on or after 2020-01-01 does
  not exist yet on any date of September 2019. The other interval pairs contain possible
  dates, and their representatives are chosen in order (2020-03-10 for the interval of
  late 2019 and 2020). 1,620 rows.

## REJECTED rows (720)

`residence = Mayotte`, `date_courante = 2024-01-01_to_2024-10-31`: `Conflict` in
`smic/Smic.catala_fr` (see FR-APL-1).

## Other observations

* `caractéristiques_prêt_l831_1_6` is declared (`prologue.catala_fr:387`) and never
  defined, so `LocationAccession` is `ineligible` for every loan.
* Mayotte rows outside 2024 are `ineligible` (French applicant, see FR-APL-1).
* Hand check: for each eligible (date, collectivity) pair there are 4 accepted
  type/holder pairs × (9 combinations signed before 2017-12-31 + 2 of the 2018-2019
  exception from 2019-10-01), giving 2,488 eligible rows, the count the encoding returns.

## Official examples

None: no official test of this scope concerns home ownership. `official_examples.csv`
holds the header only.

## Reproduction

```sh
cd paperC/specs2/FR-APL-3
python3.12 oracle.py --enumerate        # rewrites ground_truth.csv
python3.12 oracle.py --check-official   # official tests through the encoding and the oracle
```

`spec.json` and `official_examples.csv` are written by `oracle.py --write-spec --write-official`
from the same definitions. This conversion was made by the second coder without access to
the first coder's work (see `paperC/specs2/README-FR2-CODE2.md`).
