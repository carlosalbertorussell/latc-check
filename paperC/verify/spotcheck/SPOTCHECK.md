# Paper C step 2: spot-check of the ground truth (FR-APL-1..5, US-121-1..2)

Branch `paperc-verify-fr2`. Code: `paperC/verify/spotcheck/spotcheck.py` (Python 3.12,
standard library, the bundled Catala runtime `paperC/catala_more/runtime/catala` and the
generated modules `paperC/catala_more/generated/Aides_logement.py`, `Us_tax_code.py`).
Per-row results: `paperC/verify/spotcheck/<ID>.csv`; machine-readable summary:
`summary.json`. Re-run with `python3.12 -I paperC/verify/spotcheck/spotcheck.py`
(add `--full` for the supplementary full-table run).

Independence: the script imports nothing from `paperC/harness/`, `latc_check`, any
`oracle.py`, `oracle_common.py`, `fr_apl_common.py`, `apl_inputs.py` or
`us121_inputs.py`, and none of those files was read. Inputs are built from the record
classes of the generated modules. The fixed FR-APL household was transcribed by hand
from the official test file `aides_logement/tests/tests_eligibilite_apl.catala_fr`
(catala-examples 2694b17, lines 16-107), and each attribute label is turned into a
concrete value by parsing its `representative` string in `spec.json` (regexes in the
script; an unexpected string fails loudly).

## 1. Draw method

For each sample: N = number of data rows of `ground_truth.csv` (index 0 = first data
row). If N > 50, a fresh `rng = random.Random(20261020)` is created for that sample and
`idx = sorted(rng.sample(range(N), 50))` (without replacement); otherwise every row is
checked. Because the generator is reseeded per sample, samples with similar N share
index patterns (FR-APL-3 and FR-APL-5 share most indices; so do FR-APL-4 and US-121-2):
this is a property of the stated method.

| Sample | N | Indices drawn |
|---|---|---|
| FR-APL-1 | 270 | 9, 12, 16, 23, 29, 31, 33, 39, 40, 41, 46, 52, 54, 56, 68, 70, 75, 81, 104, 108, 113, 119, 126, 135, 142, 148, 149, 160, 161, 165, 171, 175, 182, 186, 190, 191, 199, 201, 203, 204, 218, 224, 229, 231, 235, 237, 246, 253, 259, 269 |
| FR-APL-2 | 69,120 | 4196, 5111, 6040, 6465, 6616, 8174, 8584, 10729, 11835, 11878, 12036, 12163, 12201, 12447, 14925, 18160, 19401, 20149, 20737, 22279, 25135, 26687, 26780, 27038, 27121, 27869, 28006, 28265, 29153, 32266, 35313, 36055, 40843, 41120, 41833, 42039, 42276, 48080, 52079, 53346, 55974, 58281, 60013, 60256, 61017, 61019, 63094, 64907, 66339, 66631 |
| FR-APL-3 | 3,600 | 131, 159, 206, 255, 268, 335, 369, 371, 466, 606, 629, 648, 833, 844, 870, 875, 911, 1008, 1103, 1126, 1285, 1307, 1321, 1667, 1749, 1821, 1883, 1906, 1971, 2028, 2082, 2161, 2279, 2579, 2665, 2669, 2747, 2808, 2924, 2980, 3041, 3052, 3071, 3171, 3187, 3192, 3226, 3259, 3350, 3519 |
| FR-APL-4 | 1,440 | 65, 79, 101, 103, 127, 134, 167, 184, 185, 190, 233, 303, 314, 324, 348, 416, 418, 422, 423, 435, 437, 441, 455, 504, 551, 563, 638, 642, 653, 656, 660, 833, 874, 910, 937, 941, 953, 985, 1014, 1036, 1041, 1080, 1139, 1189, 1194, 1289, 1332, 1334, 1373, 1404 |
| FR-APL-5 | 2,880 | 131, 159, 202, 206, 255, 268, 335, 369, 371, 381, 466, 606, 629, 648, 696, 833, 836, 844, 847, 870, 875, 883, 911, 1008, 1103, 1126, 1276, 1285, 1307, 1313, 1321, 1667, 1749, 1821, 1875, 1883, 1906, 1971, 2028, 2073, 2082, 2161, 2279, 2378, 2389, 2579, 2665, 2669, 2747, 2808 |
| US-121-1 | 12 | all (0-11) |
| US-121-2 | 1,296 | 65, 79, 94, 101, 103, 127, 134, 167, 184, 185, 190, 233, 283, 303, 314, 324, 348, 416, 418, 422, 423, 435, 437, 441, 455, 504, 551, 563, 638, 642, 653, 656, 660, 833, 874, 910, 937, 941, 953, 985, 1014, 1036, 1041, 1080, 1139, 1165, 1189, 1194, 1238, 1289 |

## 2. Adapter validation against the official tests

All checks pass.

* `tests_eligibilite_apl/Exemple1`, transcribed literally and passed to
  `eligibilite_aide_personnalisee_logement`: `éligibilité = vrai` (asserted `éligible`).
* The parameterised FR-APL builder with no override is structurally equal (Catala `=`
  on `Ménage`, `Demandeur`, date) to that literal transcription.
* `test_section_121/Test1`-`Test4` (Section121SinglePerson, literal periods of the
  test's `Data` scope): `requirements_met` = true, false, false, true, as asserted.
  `Test5` (SingleReturn, person_ok_1): excluded $250,000; `Test6` (JointReturn,
  person_ok_1 and person_ok_2): excluded $350,000, as asserted.
* Every row of `official_examples.csv` run through the label adapter (representatives)
  gives the listed output: FR-APL-1, -2, -3 Exemple1 → `eligible`; US-121-1 Test1-4 →
  `requirements_met`, `requirements_not_met`, `requirements_not_met`, `requirements_met`;
  US-121-2 Test5 → `limited_to_250000`, Test6 → `entire_gain`. FR-APL-4 and FR-APL-5
  have no official example (header only). Exemple2 and Exemple3 test
  `ÉligibilitéAllocationLogement` and map onto none of these tables.

## 3. Results

| Sample | Rows checked | Agree | Labels in draw (GT) | Verdict |
|---|---|---|---|---|
| FR-APL-1 | 50 | 50 | 15 eligible, 16 not_eligible, 19 REJECTED | PASS |
| FR-APL-2 | 50 | 50 | 5 eligible, 45 not_eligible | PASS |
| FR-APL-3 | 50 | 50 | 50 not_eligible | PASS |
| FR-APL-4 | 50 | 50 | 20 eligible, 13 not_eligible, 16 EXCLUDED, 1 REJECTED | PASS |
| FR-APL-5 | 50 | 50 | 1 eligible, 42 not_eligible, 7 EXCLUDED | PASS |
| US-121-1 | 12 | 12 | 1 requirements_met, 3 requirements_not_met, 8 REJECTED | PASS |
| US-121-2 | 50 | 50 | 2 no_exclusion, 34 EXCLUDED, 14 REJECTED | PASS |

No row of any draw disagrees with `ground_truth.csv`.

### REJECTED rows

Every REJECTED row in the draws raised a Catala runtime error (subclass of
`catala_runtime.CatalaError`), at the positions CONVERSION.md gives:

| Sample | Rows | Exception and position |
|---|---|---|
| FR-APL-1 | 10 | `NoValue` at `smic/Smic.catala_fr:13.12-13.24` (all `lt_2019-01-01`) |
| FR-APL-1 | 8 | `NoValue` at `aides_logement/prologue.catala_fr:343.15-343.50` (all `2019-01-01_to_2019-08-31`) |
| FR-APL-1 | 1 | `Conflict` at `smic/Smic.catala_fr:443.5-443.11, 489.5-489.11` (Mayotte, `2024-01-01_to_2024-10-31`) |
| FR-APL-4 | 1 | same Mayotte SMIC `Conflict` |
| US-121-1 | 8 | `DateError` at `us_tax_code/section_121.catala_en:376.9-376.81` |
| US-121-2 | 14 | same `DateError` |

No row labelled with an output raised an error, and no REJECTED row returned a value.

### EXCLUDED rows

Every EXCLUDED row in the draws satisfies at least one exclusion predicate of its
`spec.json`, and no non-EXCLUDED row in the draws satisfies one. What the encoding
returns on the excluded rows (run with the representatives):

| Sample | Predicate(s) | Rows | Encoding output |
|---|---|---|---|
| FR-APL-4 | `drom_convention_outside_drom` | 11 | 7 not_eligible, 4 eligible |
| FR-APL-4 | `fjt_type_without_l353_2_convention` | 3 | 3 not_eligible |
| FR-APL-4 | both | 2 | 1 not_eligible, 1 eligible |
| FR-APL-5 | `loan_signed_after_decision_date` | 7 | 7 not_eligible |
| US-121-2 | `person2_differs_on_single_return` | 34 (19 single, 15 surviving_spouse) | 24 REJECTED (`DateError` at `section_121.catala_en:376`), 6 no_exclusion, 3 entire_gain, 1 limited_to_250000 |

Legal reading of each exclusion's stated source:

* **FR-APL-4 `drom_convention_outside_drom`: justified.** L861-5-1
  (`code_construction_legislatif.catala_fr:1463-1489`) rewrites L831-1 5° "pour
  l'application ... en Guadeloupe, en Guyane, en Martinique, à La Réunion et à
  Mayotte" only; the encoding's rule carries the same territorial condition. A
  "convention selon les règles DROM" has no legal basis elsewhere. The encoding ignores
  the flag outside the five territories, so these rows duplicate the corresponding
  `faux` rows (which is why 5 of them come out `eligible` through the livre III
  convention or R832-21).
* **FR-APL-4 `fjt_type_without_l353_2_convention`: plausible, open to challenge.** R832-20 3°
  (`code_construction_reglementaire.catala_fr:3725-3727`) defines the type as foyers
  "ayant fait l'objet d'une convention, prévue à l'article L. 353-2, signée avant le
  1er janvier 1995", and L353-2 is in livre III, titre V, chapitre III. The wording is
  in the past tense, while L831-1 5° (`code_construction_legislatif.catala_fr:731-733`)
  asks that the foyer "font l'objet" (present tense) of such a convention. A foyer
  whose pre-1995 convention has since expired or been terminated would fall under the
  R832-20 3° type and have `conventionné_livre_III_titre_V_chap_III = faux`, so the
  combination is not strictly impossible. The exclusion holds under the reading
  "the type implies a convention still in force". On one sampled excluded row the
  encoding gives `eligible` (via R832-21), so this exclusion removes rows the encoding
  decides in both directions.
* **FR-APL-5 `loan_signed_after_decision_date`: justified.** L831-1 1°
  (`code_construction_legislatif.catala_fr:648-657`) covers dwellings "construits,
  acquis ou améliorés au moyen ... de prêts"; at a decision date in September 2019 a
  loan signed in 2020 does not yet finance the dwelling. Every date of the
  `ge_2020-01-01` band follows every date of the `2019-09-01_to_2019-09-30` band, so
  the predicate holds for every concrete pair in the cell. The encoding gives
  `not_eligible` on all 7 sampled rows (L831-2 base exception, signature ≥ 2017-12-31).
* **US-121-2 `person2_differs_on_single_return`: justified for `single`; for
  `surviving_spouse` the statute gives it no support.**
  - `single`: `SingleReturn` carries one `PersonalData`; the scope reads it for both
    person 1 and person 2 (`section_121.catala_en:95-105`), and the representative
    ("SingleReturn content (person 1)") never uses the person-2 labels. A row whose
    person-2 labels differ names a second person that a single return does not have.
  - `surviving_spouse`: the spec's own representative builds
    `DeadSpouseInfo {return: (person 1), death_spouse_info_at_time_of_death: (person 2)}`,
    so the person-2 labels describe the deceased spouse, a real second person whose
    facts can differ from the survivor's. 26 U.S.C. 121(b)(4) reads exactly those facts:
    the $500,000 limitation applies to a surviving spouse when the sale occurs within 2
    years of the death and "the requirements of paragraph (2)(A) were met immediately
    before such date of death" (either spouse met ownership, both met use, neither
    barred by (b)(3)). A surviving-spouse row with different deceased-spouse labels is
    therefore a possible return. The exclusion's description ("the scope takes person 2
    to be person 1") describes the scope `Section121TwoPersons`, which reads only
    `DeadSpouseInfo.return` (`section_121.catala_en:99`, `105`); it is a property of the
    encoding, which lacks (b)(4) (CONVERSION.md section 8 says so). The predicate
    removes 396 of the table's 1,296 rows on this ground (15 in this draw). If Paper C
    treats E as "legally impossible" (PROTOCOL H2), these 396 rows are better
    described as "inputs the encoding ignores".

## 4. Supplementary checks (outside the pre-specified verdict)

**In-band probes.** For every drawn row, each interval attribute was re-evaluated with
one or two concrete values of the same label other than the representative (mostly the
band's other end, chosen by this verifier from CONVERSION.md's band definitions; listed
in `ALT` in the script), one attribute at a time, and compared with the row's output at
the representatives (same label; for REJECTED, same exception position). Column
`supplementary_band_probe` of each CSV.

| Sample | Probes | Rows | Differences |
|---|---|---|---|
| FR-APL-1 | 100 | 50 | 0 |
| FR-APL-2 | 53 | 50 | 0 |
| FR-APL-3 | 122 | 49 | 0 |
| FR-APL-4 | 100 | 50 | 0 |
| FR-APL-5 | 186 | 50 | 0 |
| US-121-1 | 38 | 12 | 0 |
| US-121-2 | 357 | 50 | 0 |

Examples of probed values: dates on the first and last day of each date band
(FR-APL-1 from 2018-04-01, the scope's lower assertion, to 2027-12-31); surfaces at the
top of each FR-APL-2 band; family shares 0, 0,0999, 0,5 and 1; a third party turning
30 on the decision date (1990-03-10) or the day after (1990-03-11); periods of 729 and
730 days and an empty list; an earlier §121(a) sale one day before the sale date and on
2018-12-31; gains of $0.01, $249,999.99, $250,000, $499,999.99, $500,000 and
$10,000,000.

**Full tables** (`--full`). Every row of every table was also run through the same
adapter: FR-APL-1 270/270, FR-APL-2 69,120/69,120, FR-APL-3 3,600/3,600, FR-APL-4
1,440/1,440, FR-APL-5 2,880/2,880, US-121-1 12/12, US-121-2 1,296/1,296 agree with
`ground_truth.csv` (outputs equal; every REJECTED row raises a Catala error; every
EXCLUDED row, and only those, satisfies an exclusion predicate). The CSV files hold the
50-row draws only; the full-run counts are in `summary.json` under `full`.

## 5. Assumptions made by this verifier

* FR-APL household: Exemple1 as written in the test file (lines 16-107), including
  `identifiant` 0, 1, 2 for the children in the listed order, prestations in the order
  [AllocationSoutienEnfantHandicapé; ComplémentFamilial; AllocationsFamiliales], and
  `enfant_à_naître_après_quatrième_mois_grossesse` faux.
* FR-APL-2 `personnes_a_charge = k`: the first k children of Exemple1's list (the
  representative's wording).
* FR-APL-3: `SousLocataire` carries the same `Location` record as `Locataire`
  (Exemple1's, with the label's `bailleur`); the shares 0,05 and 0,1 are Catala decimals.
* FR-APL-4 fixed `LogementFoyer` fields and FR-APL-5 fixed `Propriétaire` fields:
  taken from `spec.json` `fixed_inputs` ("every other boolean faux" read as
  `bénéficiaire_aide_adulte_ou_enfant_handicapés`, `logement_meublé_d842_2`,
  `logement_est_chambre`, `colocation` faux for the foyer, and
  `local_habité_première_fois_bénéficiaire`, `copropriété`, `situation_r822_11_13_17`,
  `opérations_logement_évolutifs_sociaux_accession_propriété_aidée_État` faux for the
  owner).
* US-121: context variables (`gain_cap`, `section_121_b_3_applies`, `person1`,
  `person2`) passed as absent (`Option(None)`), so the scopes use their own
  definitions, as in the tests. US-121-2 output mapping (written from the spec's
  `output.source`): `no_exclusion` when the uncapped amount is $0; otherwise, with cap
  = $500,000 when `section_121_b_2_A_condition` holds and else `gain_cap_person_1`,
  `limited_to_<cap>` when uncapped ≥ cap, else `entire_gain`; the script also asserts
  excluded = min(uncapped, cap).

## 6. Observations about coverage

* The draw of FR-APL-3 contains only `not_eligible` rows (the table has 32 eligible
  rows in 3,600), and FR-APL-5's draw has one eligible row; the draws alone say little
  about the eligible side of those tables. The supplementary full-table run covers it
(all 32 and all 80 eligible rows agree).
* US-121-2's draw has no `entire_gain`, `limited_to_250000` or `limited_to_500000` row
  (75 of 1,296 rows carry such a label); the official Test5/Test6 rows and the full run
  cover them.
