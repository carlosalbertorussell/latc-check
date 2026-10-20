# Paper C, second coder: French APL eligibility and US IRC section 121

Branch `paperc-code2-fr2`. This folder holds the second, independent conversion of two
Catala encodings into decision tables in the shared format of `paperC/specs/FORMAT.md`
(protocol `paperC/PROTOCOL.md`, registered at `ee7c527`). A later comparison with the
first coder's conversion measures how far two independent conversions agree.

* Encodings: CatalaLang/catala-examples at `2694b17ddd7c2246e207e8f077d586349ee5abea`,
  compiled with Catala 1.3.0 (`paperC/catala_code2/README.md`).
* Official tests run with `clerk`: `aides_logement/tests/tests_eligibilite_apl.catala_fr`
  7 of 7 (interpreter) and 3 of 3 (Python backend);
  `us_tax_code/tests/test_section_121.catala_en` 12 of 12 (interpreter; the clerk target
  declares no Python backend). Every mappable official test also passes through the
  generated Python and through each oracle (`oracle.py --check-official`).

## Blinding

I followed the blinding rules of the task. I did not check out, diff, `git show`,
fetch or read anything on the branches `paperc-data-fr2`, `paperc-data-fr`,
`paperc-data-nz`, `paperc-run-*`, `paperc-verify-*` or any other `paperc-code2-*`
branch, and I read no `paperC/specs/` folder. From `origin/paperc-harness` I read only
`paperC/specs/FORMAT.md` and `paperC/PROTOCOL.md` (with `git show origin/paperc-harness:<path>`),
and from `origin/paperc-catala-family-benefits` only
`paperC/catala_family_benefits/README.md`, for the Catala 1.3.0 install and clerk
commands. Apart from `main` and this session's own working branch, the only branches
fetched were `paperc-harness` and `paperc-catala-family-benefits`. Every attribute, cut, fixed input, representative,
exclusion and output label was chosen from the Catala sources and the official tests
alone, and each choice is recorded with its source in the sample's `CONVERSION_2.md`.

## Samples

| ID | Decision | Attributes (values) | Declared | EXCLUDED | REJECTED | Valid | Outputs in valid space |
|---|---|---|---:|---:|---:|---:|---|
| FR-APL-1 | APL éligibilité, rented housing | date_courante (8), residence (9), mode_occupation (2), bailleur (5) | 720 | 0 | 10 | 710 | eligible 116, ineligible 594 |
| FR-APL-2 | APL éligibilité, logement-foyer | date_courante (8), residence (9), type_logement_foyer (4), conventionne_livre_III_titre_V_chap_III (2), conventionne_selon_regles_drom (2), remplit_conditions_r832_21 (2) | 2,304 | 0 | 32 | 2,272 | eligible 1,028, ineligible 1,244 |
| FR-APL-3 | APL éligibilité, home ownership | date_courante (8), residence (9), mode_occupation (2), type_pret (5), titulaire_pret (2), date_signature_pret (4), anciennete_logement (3), zone (3) | 51,840 | 1,620 | 720 | 49,500 | eligible 2,488, ineligible 47,012 |
| FR-APL-4 | APL éligibilité, common conditions | residence (3), nationalite_demandeur (5), residence_principale (2), rattache_foyer_fiscal_parent_ifi (2), logement_decent (2), loue_ou_sous_loue_a_des_tiers (2), age_personne_sous_location (4), sous_locataire_conforme_l442_1 (3), proprietaire_famille (4), usufruit_famille (4), mode_occupation (2) | 92,160 | 65,280 | 0 | 26,880 | eligible 800, ineligible 26,080 |
| FR-APL-5 | APL éligibilité, surface and household | residence (3), nationalite_demandeur (2), situation_familiale (6), nombre_autres_occupants_logement (4), nombre_personnes_a_charge (5), surface_m_carres (23), personnes_agees_handicapees_foyer_r844_4 (2) | 33,120 | 0 | 2,648 | 30,472 | eligible 7,090, ineligible 23,382 |
| US-121-1 | Section121SinglePerson.requirements_met | property_ownage (10), property_usage_as_principal_residence (10), other_section_121a_sale (4) | 400 | 0 | 300 | 100 | met 25, not_met 75 |
| US-121-2 | Section121TwoPersons.income_excluded_from_gross_income | return_type (3), person1_property_ownage (2), person1_property_usage_as_principal_residence (2), person1_other_section_121a_sale (4), person2_property_ownage (3), person2_property_usage_as_principal_residence (3), person2_other_section_121a_sale (5), gain_from_sale_or_exchange_of_property (3) | 6,480 | 2,928 | 2,808 | 744 | zero 549, full_gain 68, capped_at_250000 124, capped_at_500000 3 |

Every table is within the 200,000-combination limit. For each sample, the rows with
`EXCLUDED` are exactly the rows where an exclusion predicate of `spec.json` holds
(checked over the whole declared space; 0 disagreeing rows).

How the APL decision was split: the decision
`condition_logement_bailleur et condition_logement_prêt et éligibilité_commune.éligibilité`
reads disjoint groups of inputs; each sub-table varies one group and keeps all other
inputs at the official test `Exemple1`, so FR-APL-1 to FR-APL-3 cover the APL-specific
lessor and loan conditions and FR-APL-4 and FR-APL-5 the common conditions.

### Causes of REJECTED rows

| Sample | Rows | Cause |
|---|---:|---|
| FR-APL-1, -2, -3 | 10, 32, 720 | Mayotte in 2024-01-01..2024-10-31: two concurrent Mayotte SMIC definitions (`smic/Smic.catala_fr:443, 489`), Catala `Conflict` |
| FR-APL-5 | 2,648 | Mayotte with R844-4: the Mayotte surface rule and an R844-4 rule are both exceptions to label `base` of `condition_logement_surface` (`code_construction_reglementaire.catala_fr:5645` with `:5538` or `:5545`), Catala `Conflict` |
| US-121-1, US-121-2 | 300, 2,808 | any `MostRecentSaleWhereSection121aApplied`: `section_121.catala_en:376` compares days with `2 year`, Catala `DateError`; the interpreter raises the same error |

Since R is non-empty for six of the seven samples, CTRL-H3 of the protocol will record
rejected rows that C3 can generate for those samples (protocol section 7(c)).

## Official examples

| Sample | Mappable official rows | Official tests left out, with reason |
|---|---:|---|
| FR-APL-1 | 1 (`Exemple1`) | `Exemple2`, `Exemple3`: scope `ÉligibilitéAllocationLogement` |
| FR-APL-2 | 0 | `Exemple1` is a tenancy (no foyer); `Exemple2`, `Exemple3`: other scope |
| FR-APL-3 | 0 | `Exemple1` is a tenancy (no ownership); `Exemple2`, `Exemple3`: other scope |
| FR-APL-4 | 1 (`Exemple1`) | `Exemple2`, `Exemple3`: other scope |
| FR-APL-5 | 1 (`Exemple1`) | `Exemple2`, `Exemple3`: other scope |
| US-121-1 | 4 (`Test1`-`Test4`) | `Test5`, `Test6`: scope `Section121TwoPersons` |
| US-121-2 | 2 (`Test5`, `Test6`) | `Test1`-`Test4`: scope `Section121SinglePerson` |

`--check-official` results: FR-APL-1, -4, -5 1 of 1 each, US-121-1 4 of 4, US-121-2 2 of 2,
both through the encoding with the test's original inputs and through the oracle with the
mapped labels. FR-APL-2 and FR-APL-3 have empty `official_examples.csv` files (header
only), so the harness skips OFFICIAL for them.

## Declared values that the official examples never use

| Sample | Unused | Values |
|---|---:|---|
| FR-APL-1 | 20 of 24 | date_courante: all but `2019-10-01_to_2020-12-31` (7); residence: all but `Metropole` (8); mode_occupation: `SousLocataire`; bailleur: `social_non_conventionne`, `prive_conventionnement_social_conventionne`, `prive_conventionnement_social_non_conventionne`, `prive` |
| FR-APL-2 | all 27 | no official example |
| FR-APL-3 | all 36 | no official example |
| FR-APL-4 | 22 of 33 | residence: `LaReunion`, `Mayotte`; nationalite_demandeur: the four `Etrangere_*`; residence_principale: `non`; rattache_foyer_fiscal_parent_ifi: `oui`; logement_decent: `non`; loue_ou_sous_loue_a_des_tiers: `oui`; age_personne_sous_location: `under_30`, `30th_birthday_on_date`, `over_30`; sous_locataire_conforme_l442_1: `oui`, `non`; proprietaire_famille and usufruit_famille: `parts_below_10pct`, `parts_10pct`, `parts_above_10pct` (3 each); mode_occupation: `AccessionProprieteLocalUsageExclusifHabitation` |
| FR-APL-5 | 38 of 45 | residence: `LaReunion`, `Mayotte`; nationalite_demandeur: `Etrangere_T_T`; situation_familiale: all but `Maries` (5); nombre_autres_occupants_logement: `0`, `2`, `3`; nombre_personnes_a_charge: `0`, `1`, `2`, `4`; surface_m_carres: all but `from_72` (22); personnes_agees_handicapees_foyer_r844_4: `oui` |
| US-121-1 | 18 of 24 | property_ownage: all but `one_inside_window_over_730d` (9); property_usage_as_principal_residence: `none`, `one_inside_window_730d`, `one_across_5y_mark_over_730d`, `one_across_5y_mark_730d`, `one_ended_before_5y_mark`, `two_total_under_730d`; other_section_121a_sale: `under_2_years_before`, `exactly_2_years_before`, `over_2_years_before` |
| US-121-2 | 13 of 25 | return_type: `surviving_spouse_return`; person1/person2 ownership and use: `under_730d` (4); person1_other_section_121a_sale and person2_other_section_121a_sale: `under_2_years_before`, `exactly_2_years_before`, `over_2_years_before` (6); gain: `under_250000`, `over_500000` |

## Files

Each sample folder `paperC/specs2/<ID>/` holds `spec.json`, `ground_truth.csv`,
`official_examples.csv`, `oracle.py`, `ENVIRONMENT.md`, `CONVERSION_2.md` and
`SHA256SUMS` (sha256 of every other file in the folder, in `sha256sum` format).
`oracle.py` is assembled by `paperC/catala_code2/make_oracles.py` and imports the
generated Catala Python from `paperC/catala_code2/`.

## Deviations from FORMAT.md

* The conversion notes are named `CONVERSION_2.md` (as the second-coder task asks)
  where FORMAT.md names the file `CONVERSION.md`. The content follows FORMAT.md.
* `paperC/specs2/` is used in place of `paperC/specs/`, so that the two conversions sit
  side by side; the harness takes the folder as `--spec`.
* `oracle.py` accepts two extra flags, `--write-spec` and `--write-official`, which
  regenerate `spec.json` and `official_examples.csv` from the definitions in the oracle.
