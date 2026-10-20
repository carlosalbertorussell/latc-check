# FR-APL-1 conversion record

Table: eligibility for the *aide personnalisée au logement* (APL) by decision date,
territory of residence and nationality of the applicant. Sub-table 1 of the five
FR-APL tables, which split the APL eligibility decision by subject so that each stays
under 200,000 rows. The amount of the aid (scopes `CalculAidePersonnaliséeLogement*`,
`CalculetteAidesAuLogement`) is out of scope.

All file references are to CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`. Article numbers are those of the code de la
construction et de l'habitation (CCH) quoted in the encoding.

## 1. Scope and output

* Entry point: scope `ÉligibilitéAidePersonnaliséeLogement` of module `Aides_logement`
  (declared at `aides_logement/prologue.catala_fr:378-394`), called through the Catala
  1.3.0 Python build `paperC/catala_more/generated/Aides_logement.py`
  (`eligibilite_aide_personnalisee_logement`). Inputs: `ménage`, `demandeur`,
  `date_courante`.
* Output: `éligibilité` (a condition). Label `eligible` when it is `vrai`,
  `not_eligible` when it is `faux`. This is the value the official test Exemple1
  asserts (`assertion éligible`, `tests_eligibilite_apl.catala_fr:15`).
* The scope's rule: `éligibilité` holds when `condition_logement_bailleur`,
  `condition_logement_prêt` and `éligibilité_commune.éligibilité` hold
  (`code_construction_legislatif.catala_fr:631-645`), with an exception setting it to
  `faux` in Saint-Pierre-et-Miquelon from 2021-01-01 (L860-3,
  `code_construction_legislatif.catala_fr:1333-1339`). `éligibilité_commune` is the
  common scope `ÉligibilitéAidesPersonnelleLogement` (nationality, occupation mode,
  dwelling conditions).

## 2. Attributes

### `date_courante` (interval, 6 labels)

The code compares `date_courante` against many dates. The labels are cut at every
date at which the output, or the presence of a run-time error, changes for the inputs
of this table. A daily sweep (section 6) confirms that no other date inside a label
changes the output.

| Label | Days | Representative | Why the cut |
|---|---|---|---|
| `lt_2019-01-01` | before 2019-01-01 | 2018-06-01 | `Smic.brut_horaire` has no definition before 2019-01-01 (`smic/Smic.catala_fr:9-18`); the scope instantiates `Prestations_familiales.ÉligibilitéPrestationsFamiliales`, which computes it. The assertion `date_courante >= \|2018-04-01\|` (`aides_logement/prologue.catala_fr:369`) is never reached first. |
| `2019-01-01_to_2019-08-31` | 2019-01-01 to 2019-08-31 | 2019-05-01 | `personnes_à_charge_prises_en_compte` is defined from 2019-09-01 only (`aides_logement/archives.catala_fr:11-16`, then `code_construction_reglementaire.catala_fr:1129-1133` from 2023-09-01); `nombre_personnes_à_charge_prises_en_compte` counts it (`prologue.catala_fr:342-343`). |
| `2019-09-01_to_2020-12-31` | 2019-09-01 to 2020-12-31 | 2020-03-10 (Exemple1's date) | first day without a run-time error |
| `2021-01-01_to_2023-12-31` | 2021-01-01 to 2023-12-31 | 2022-06-01 | L860-3 I: no APL in Saint-Pierre-et-Miquelon from 2021-01-01 (`code_construction_legislatif.catala_fr:1333-1339`) |
| `2024-01-01_to_2024-10-31` | 2024-01-01 to 2024-10-31 | 2024-06-01 | Mayotte: `Smic.brut_horaire` has two definitions, 8,80 € for `[2024-01-01, 2024-11-01)` (`smic/Smic.catala_fr:434-443`) and 8,98 € from 2024-01-01 (`smic/Smic.catala_fr:481-489`, under the heading of the decree of 23 October 2024, which applies from 1 November 2024) |
| `ge_2024-11-01` | from 2024-11-01 | 2025-06-01 | the Mayotte overlap ends |

Dates the code compares against that do not change this table's output (checked by
the sweep): 2019-10-01 (zone III derogation, read only for home buyers),
2021-05-01 (deferred entry into force for home buyers), 2023-04-05 (DROM foyer rule),
2023-09-01 (new R823-4 dependants rules, which change who is counted as a dependant
but not eligibility for this household), the yearly ASPA ceilings of
`autres_sources.catala_fr` and `code_sécurité_sociale.catala_fr`.

### `residence` (enum, 9 labels)

`Ménage.résidence`, enumeration `France.Collectivité`
(`prologue_france/France.catala_fr:9-18`), all nine constructors in declared order.
Labels are the constructor names without accents (the representative gives the exact
constructor).

### `nationalite_demandeur` (enum, 5 labels)

`Demandeur.nationalité` (`aides_logement/prologue.catala_fr:228-247`) is `Française` or
`Étrangère` carrying two booleans (`ConditionsÉtrangers`). The five labels are
`Française` and the four combinations of the two booleans:

| Label | Value |
|---|---|
| `francaise` | `Française` |
| `etrangere_l512_2_et_art_4` | `Étrangère {l512_2: vrai, art_4_mayotte: vrai}` |
| `etrangere_l512_2_seulement` | `Étrangère {l512_2: vrai, art_4_mayotte: faux}` |
| `etrangere_art_4_seulement` | `Étrangère {l512_2: faux, art_4_mayotte: vrai}` |
| `etrangere_aucune` | `Étrangère {l512_2: faux, art_4_mayotte: faux}` |

Read by L822-2 I (`code_construction_legislatif.catala_fr:130-136`: Française → vrai,
Étrangère → `satisfait_conditions_l512_2_code_sécurité_sociale`) and, in Mayotte, by
L861-5 1° (`code_construction_legislatif.catala_fr:1389-1400`: Française → **faux**,
Étrangère → `satisfait_art_4_ordonnance_2002_mayotte`).

## 3. Fixed inputs

Every input other than the three attributes is the input of the official test
Exemple1 (`tests_eligibilite_apl.catala_fr:16-107`): Mariés |2010-11-26|, three
dependent children (born 2001-01-01 after compulsory schooling and in studies,
2009-01-01 and 2012-01-01 in compulsory schooling), one other occupant, the three
benefits received, Locataire of a conventioned social landlord, Zone1, main residence,
decent, 80 m², no family ownership, not let to third parties, no IFI, applicant born
1970-05-02. The oracle checks at import time that the Catala records it builds for
Exemple1's row are structurally equal to those of the test
(`fr_apl_common.inputs_equal_exemple1`).

## 4. Exclusions

None. Candidates considered and left out: (a) a foreign national meeting the Mayotte
condition of art. 4 of ordonnance 2002-149 while living elsewhere: the two booleans
describe facts about the applicant's residence permit and both can be true or false
anywhere; (b) a decision date before the APL rules existed: those rows are REJECTED by
the encoding itself, which is what the table records.

## 5. REJECTED rows (95)

| Error (Python runtime and Catala interpreter agree) | Rows |
|---|---|
| `NoValue` at `smic/Smic.catala_fr:13.12-13.24` (`brut_horaire`, no definition before 2019-01-01) | 45 (all of `lt_2019-01-01`) |
| `NoValue` at `aides_logement/prologue.catala_fr:343.15-343.50` (`personnes_à_charge_prises_en_compte` undefined) | 45 (all of `2019-01-01_to_2019-08-31`) |
| `Conflict` at `smic/Smic.catala_fr:443.5-443.11` and `489.5-489.11` (two Mayotte SMIC values) | 5 (Mayotte, `2024-01-01_to_2024-10-31`) |

Catala computes every variable of a scope and of its sub-scopes, so these errors occur
whatever the household; the encoding's own comment at
`aides_logement/code_sécurité_sociale.catala_fr:187-198` describes this semantics.

## 6. Band check (`python oracle.py --check-bands`)

Every calendar day from 2017-01-01 to 2027-12-31 was evaluated for every
(residence, nationality) pair, 180,495 evaluations away from the representatives. Each
gave the output of its label's representative: the six date labels are homogeneous
over that range.

## 7. Official tests

| Test | Mapped | Row / reason |
|---|---|---|
| `tests_eligibilite_apl/Exemple1` | yes | `2019-09-01_to_2020-12-31, Metropole, francaise` → `eligible` (asserted `éligible`) |
| `tests_eligibilite_apl/Exemple2` | no | tests `ÉligibilitéAllocationLogement` (allocation de logement), output `TypeÉligibilitéAllocationLogement` |
| `tests_eligibilite_apl/Exemple3` | no | same as Exemple2 |

`python oracle.py --check-official`: 3/3 test scopes pass when re-run directly through
the generated Python; 1/3 maps onto the table and the oracle gives the asserted output
for it (1/1).

## 8. Behaviour of the encoding recorded by this table

* A French applicant living in Mayotte is never eligible: the Mayotte exception of
  L861-5 1° replaces the whole definition of `condition_nationalité` and returns `faux`
  for `Française` (`code_construction_legislatif.catala_fr:1394-1400`). The article
  quoted above it only replaces the reference to L512-2 for foreign nationals.
* In Mayotte a foreign applicant is eligible exactly when the art. 4 condition holds,
  whatever the L512-2 condition; elsewhere, exactly when the L512-2 condition holds.
* Saint-Pierre-et-Miquelon households are eligible until 2020-12-31 and not from
  2021-01-01.
* The encoding returns `eligible` for households in Guadeloupe, Guyane, Martinique,
  La Réunion and Mayotte; a comment of the encoding states that the APL does not exist
  in the DROM (`code_construction_reglementaire.catala_fr:5918-5928`). The table
  records the encoding's output.

## 9. Interpreter cross-check

All 270 rows were also run through the Catala interpreter by
`paperC/catala_more/interpreter_crosscheck.py` (no Python involved): see
`paperC/catala_more/interpreter_crosscheck_report.txt` and `paperC/specs/README-FR2.md`.

Result: 270 rows run through the interpreter, 0 disagreements (175 rows whose label assertion passed, 95 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

270 rows: 93 `eligible`, 82 `not_eligible`, 0 EXCLUDED, 95 REJECTED. One official
example.
