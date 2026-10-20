# FR-APL-5 conversion record

Table: APL eligibility of home buyers, *accession à la propriété* and
*location-accession*: type and holder of the loan, signature date, age of the
dwelling, zone, decision date and main residence. Sub-table 5 of the five FR-APL
tables. The amount of the aid is out of scope.

File references are to CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`; `LEG` is
`aides_logement/code_construction_legislatif.catala_fr`, `REG` is
`aides_logement/code_construction_reglementaire.catala_fr`, `ARR` is
`aides_logement/arrete_2019-09-27.catala_fr`.

## 1. Scope and output

As in FR-APL-1: scope `ÉligibilitéAidePersonnaliséeLogement`, output `éligibilité`,
labels `eligible` / `not_eligible`. For home buyers:

* `condition_logement_bailleur` (L831-1 1°, `LEG:658-676`) holds for
  `AccessionPropriétéLocalUsageExclusifHabitation` when
  `caractéristiques_prêt_l831_1_1` of the loan holds: R832-5 (`REG:3064-3074`, holder
  `Demandeur` and type `D331_32` or `D331_63_64`) or R832-7 (`REG:3102-3112`, holder
  `VendeurQuandDemandeurAContratLocationAccession` and type `D331_59_8` or
  `D331_76_1`). For `LocationAccession` it calls `caractéristiques_prêt_l831_1_6`
  (L831-1 6°, `LEG:754-763`).
* `condition_logement_prêt` (L831-2, `LEG:771-786`, `795-815`): `faux` when the loan was
  signed on or after 2017-12-31, except when it was signed from 2018-01-01 to
  2019-12-31 for an old dwelling (`Ancien`) in a commune where the derogation applies;
  `logement_situé_commune_déséquilibre_l831_2` holds for `Zone3` from 2019-10-01
  (`ARR:6070-6076`, arrêté of 27 September 2019, art. 49 and 50).
* L822-2 II (`LEG:146-161`) requires the dwelling to be the main residence for
  `AccessionPropriété…`, and L821-2 (`LEG:42-47`) for everyone.

## 2. Attributes

| Attribute | Kind | Labels | Representative / notes |
|---|---|---|---|
| `mode_occupation` | enum | `AccessionProprieteLocalUsageExclusifHabitation`, `LocationAccession` | both carry a `Propriétaire` record |
| `type_pret` | enum | `D331_32`, `D331_63_64`, `D331_59_8`, `D331_76_1`, `Autre` | every constructor of `TypePrêt` |
| `titulaire_pret` | enum | `Demandeur`, `VendeurQuandDemandeurAContratLocationAccession` | every constructor of `TitulairePrêt` |
| `date_signature_pret` | interval | `lt_2017-12-31` (2015-06-01), `eq_2017-12-31` (2017-12-31), `2018-01-01_to_2019-12-31` (2018-06-01), `ge_2020-01-01` (2020-01-15) | cut at the three dates L831-2 compares against: `>= \|2017-12-31\|`, `>= \|2018-01-01\|`, `< \|2020-01-01\|`; the single day 2017-12-31 is its own label because the two first comparisons differ on it |
| `anciennete_logement` | enum | `Neuf`, `Ancien_ameliore_par_occupant`, `Ancien_non_ameliore_par_occupant` | `NeufOuAncien` is `Neuf` or `Ancien` carrying `AmélioréParOccupant` (Oui/Non) |
| `zone` | enum | `Zone1`, `Zone2`, `Zone3` | `ZoneDHabitation` |
| `date_courante` | interval | `2019-09-01_to_2019-09-30` (2019-09-15), `ge_2019-10-01` (2020-03-10) | cut at 2019-10-01 (`ARR:6070-6076`); the domain starts at 2019-09-01 as in FR-APL-4 |
| `residence_principale` | bool | `faux`, `vrai` | |

## 3. Fixed inputs

* The `Propriétaire` record: `mensualité_principale` 500 €, `charges_mensuelles_prêt`
  0 €, `date_entrée_logement` \|2010-01-01\|, no works (`PasDeTravaux` twice), every
  boolean `faux`, `accord_financement_représentant_État_outre_mer` `PasdAccord`. The
  generated eligibility functions never access these fields.
* `résidence` Métropole, `nationalité` Française and every other input from Exemple1.

## 4. Exclusions

| id | Predicate | Rows | Source |
|---|---|---|---|
| `loan_signed_after_decision_date` | `date_signature_pret == 'ge_2020-01-01' and date_courante == '2019-09-01_to_2019-09-30'` | 360 | L831-1 1° (`LEG:648-657`): the aid concerns dwellings "construits, acquis ou améliorés au moyen ... de prêts", i.e. financed by a loan that exists; in this cell every signature date lies after every decision date |

Candidates considered and left out: (a) holder `VendeurQuandDemandeurAContratLocationAccession`
with mode `AccessionPropriété…`: the encoding reaches R832-7, which concerns
location-accession, only through this combination (section 8), so excluding it would
remove the encoding's only R832-7 rows; (b) the band `2018-01-01_to_2019-12-31` with
the September 2019 decision dates: part of the band precedes the decision date.

## 5. REJECTED rows

None.

## 6. Band check (`python oracle.py --check-bands`)

Decision dates on the 1st, 15th and 28th of every month from 2019-09-01 to 2027-12-31
and every day of 2019-09-01 to 2019-10-02; signature dates 1990-01-01, 2010-06-30,
2017-01-01, 2017-12-30 / 2018-01-01, 2018-12-31, 2019-09-01, 2019-12-31 / 2020-01-01,
2020-03-10, 2021-06-01, 2025-01-01: 467,640 evaluations, all giving the output of the
label's representative.

## 7. Official tests

None of the three test scopes of `tests_eligibilite_apl.catala_fr` maps onto this
table: Exemple1's household is a `Locataire`, and Exemple2 and Exemple3 test
`ÉligibilitéAllocationLogement`. `official_examples.csv` has the header only.
`python oracle.py --check-official`: 3/3 direct, 0/3 mapped.

## 8. Behaviour of the encoding recorded by this table

* Eligible rows (80): `AccessionPropriété…`, main residence, a loan that passes R832-5
  or R832-7, and either a signature before 2017-12-31, or a signature in 2018–2019 for
  an `Ancien` dwelling in `Zone3` with a decision date from 2019-10-01.
* `LocationAccession` is never eligible: `caractéristiques_prêt_l831_1_6` is declared
  (`aides_logement/prologue.catala_fr:387`) and used (`LEG:754-763`) but has no rule,
  so it is `faux`. R832-7, which the text writes for location-accession, is encoded
  under `caractéristiques_prêt_l831_1_1` and is reached only with mode
  `AccessionPropriété…`.
* A loan signed on 2017-12-31 is not eligible. L831-2 (quoted at `LEG:765-769`) covers
  loans "signé après le 31 décembre 2017"; the code tests `>= |2017-12-31|`, which
  includes that day, and its exception starts at 2018-01-01.
* The variable `logement_situé_commune_déséquilibre_l831_2` is true for the communes
  where the derogation applies (Zone III, `ARR:6064-6076`). L831-2 describes them as
  communes "ne se caractérisant pas par un déséquilibre important"; the variable's name
  says the opposite of its use, and the table follows its use.

## 9. Interpreter cross-check

A sample of 600 non-excluded rows was also run through the Catala interpreter: see
`paperC/catala_more/interpreter_crosscheck_report.txt` and `paperC/specs/README-FR2.md`.

Result: 600 rows run through the interpreter, 0 disagreements (600 rows whose label assertion passed, 0 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

2,880 rows: 80 `eligible`, 2,440 `not_eligible`, 360 EXCLUDED, 0 REJECTED. No
official example.
