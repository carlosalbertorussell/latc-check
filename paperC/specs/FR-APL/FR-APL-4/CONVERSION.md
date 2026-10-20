# FR-APL-4 conversion record

Table: APL eligibility of residents of a *logement-foyer* (type of foyer, its
conventions, R832-21 conditions), by territory and decision date. Sub-table 4 of the
five FR-APL tables. The amount of the aid is out of scope.

File references are to CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`; `LEG` is
`aides_logement/code_construction_legislatif.catala_fr`, `REG` is
`aides_logement/code_construction_reglementaire.catala_fr`.

## 1. Scope and output

As in FR-APL-1: scope `ÉligibilitéAidePersonnaliséeLogement`, output `éligibilité`,
labels `eligible` / `not_eligible`. For a `RésidentLogementFoyer` the landlord
condition `condition_logement_bailleur` is set by:

* L831-1 5° (`LEG:735-745`, label `logement_foyer`): the foyer is conventioned under
  livre III, titre V, chapitre III;
* R832-21 (`REG:3801-3813`, label `logement_foyer`): `remplit_conditions_r832_21`;
* L861-5-1 (`LEG:1470-1489`, label `logement_foyer`), in Guadeloupe, Guyane,
  Martinique, La Réunion and Mayotte: `conventionné_selon_règles_drom`;
* exception to `logement_foyer` (`REG:3729-3751`): type `Autre` → `faux`;
* exception to `logement_foyer` in the same five territories from 2023-04-05
  (`REG:5995-6019`): type `FoyerJeunesTravailleursOuMigrantsConventionnéL353_2Avant1995`
  → `faux`.

## 2. Attributes

| Attribute | Kind | Labels | Notes |
|---|---|---|---|
| `residence` | enum | the 9 constructors of `France.Collectivité` | as in FR-APL-1 |
| `date_courante` | interval | `2019-09-01_to_2020-12-31` (rep. 2020-03-10), `2021-01-01_to_2023-04-04` (2022-06-01), `2023-04-05_to_2023-12-31` (2023-06-01), `2024-01-01_to_2024-10-31` (2024-06-01), `ge_2024-11-01` (2025-06-01) | cuts: Saint-Pierre-et-Miquelon 2021-01-01 (`LEG:1330-1340`), DROM foyer rule 2023-04-05 (`REG:5995-6019`), Mayotte SMIC overlap 2024-01-01 to 2024-10-31 (`smic/Smic.catala_fr:434-443`, `481-489`) |
| `type_logement_foyer` | enum | the 4 constructors of `TypeLogementFoyer` (`REG:3732-3736`) | |
| `conventionne_livre_III_titre_V_chap_III` | bool | `faux`, `vrai` | |
| `remplit_conditions_r832_21` | bool | `faux`, `vrai` | |
| `conventionne_selon_regles_drom` | bool | `faux`, `vrai` | |

The date domain starts at 2019-09-01. Before that date every input raises `NoValue`
(FR-APL-1, section 5); repeating those two all-REJECTED bands here would add 576 rows
that FR-APL-1 already records.

## 3. Fixed inputs

* `demandeur.nationalité` = `Étrangère {l512_2: vrai, art_4_mayotte: vrai}`: the only
  value that meets the nationality condition in every territory (a `Française`
  applicant is never eligible in Mayotte, FR-APL-1). No official test maps onto this
  table, so nothing ties it to Exemple1's value.
* `mode_occupation` = `RésidentLogementFoyer` with `logement_foyer_jeunes_travailleurs
  faux`, `date_conventionnement` \|2000-01-01\|, `construit_application_loi_1957_12_III
  faux`, `redevance` 400 €, `catégorie_équivalence_loyer_d842_16 AutresPersonnes`,
  other booleans `faux`. These fields are read by the amount computation only: the
  generated functions `eligibilite_aides_personnelle_logement` and
  `eligibilite_aide_personnalisee_logement` never access them.
* Every other input is Exemple1's (household, surface 80 m², Zone1, decent main
  residence).

## 4. Exclusions

| id | Predicate | Rows | Source |
|---|---|---|---|
| `fjt_type_without_l353_2_convention` | `type_logement_foyer == 'FoyerJeunesTravailleursOuMigrantsConventionneL353_2Avant1995' and conventionne_livre_III_titre_V_chap_III == 'faux'` | 180 | R832-20 3° (`REG:3712-3727`): this type is defined as a foyer "ayant fait l'objet d'une convention, prévue à l'article L. 353-2, signée avant le 1er janvier 1995"; L353-2 belongs to livre III, titre V, chapitre III of the CCH, so a foyer of this type carries that convention |
| `drom_convention_outside_drom` | `conventionne_selon_regles_drom == 'vrai' and residence not in ('Guadeloupe', 'Guyane', 'Martinique', 'LaReunion', 'Mayotte')` | 320 | L861-5-1 (`LEG:1463-1489`) defines that convention for these five territories only |

The two predicates overlap in 40 rows; 460 rows are EXCLUDED. Candidates considered and
left out: (a) `remplit_conditions_r832_21 = vrai` for type `Autre`: R832-21 describes
financing conditions that any foyer can meet; (b) a convention under livre III in the
DROM: L861-5-1 rewrites 5° for the DROM, yet a livre III convention can still exist
there.

## 5. REJECTED rows (28)

All are the Mayotte SMIC `Conflict` (`smic/Smic.catala_fr:443` and `489`) in band
`2024-01-01_to_2024-10-31`: the 32 Mayotte rows of that band minus the 4 excluded ones.

## 6. Band check (`python oracle.py --check-bands`)

Every calendar day from 2019-09-01 to 2027-12-31 was evaluated for every row: 595,644
evaluations, all giving the output of the band's representative.

## 7. Official tests

None of the three test scopes of `tests_eligibilite_apl.catala_fr` maps onto this
table: Exemple1's household is a `Locataire`, and Exemple2 and Exemple3 test
`ÉligibilitéAllocationLogement`. `official_examples.csv` has the header only.
`python oracle.py --check-official`: 3/3 direct, 0/3 mapped.

## 8. Behaviour of the encoding recorded by this table

* Type `Autre` is never eligible.
* Outside the five DROM, a foyer of type `LogementPersonnesÂgéesOuHandicapées` or
  `RésidenceSociale` is eligible when it has the livre III convention or meets R832-21;
  a `FoyerJeunesTravailleurs…` foyer is eligible (it has the convention by definition).
* In the five DROM the DROM convention is a further way in, alongside the livre III
  convention and R832-21: the three rules carry the same label and any one suffices.
  L861-5-1 says the 5° "est ainsi rédigé" for these territories, which reads as a
  replacement of the livre III route; the code keeps both.
* In the five DROM, a `FoyerJeunesTravailleurs…` foyer is eligible until 2023-04-04 and
  never from 2023-04-05.
* Saint-Pierre-et-Miquelon: eligible combinations until 2020-12-31, none from 2021.

## 9. Interpreter cross-check

A sample of 600 non-excluded rows was also run through the Catala interpreter: see
`paperC/catala_more/interpreter_crosscheck_report.txt` and `paperC/specs/README-FR2.md`.

Result: 600 rows run through the interpreter, 0 disagreements (581 rows whose label assertion passed, 19 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

1,440 rows: 504 `eligible`, 448 `not_eligible`, 460 EXCLUDED, 28 REJECTED. No
official example.
