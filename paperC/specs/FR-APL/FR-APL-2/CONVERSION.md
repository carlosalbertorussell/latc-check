# FR-APL-2 conversion record

Table: APL eligibility by household size and floor area (the *conditions de
peuplement* of L822-10, made concrete by R822-25, its Mayotte version in R861-5 3°, and
R844-4). Sub-table 2 of the five FR-APL tables. The amount of the aid is out of scope.

All file references are to CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`; `REG` stands for
`aides_logement/code_construction_reglementaire.catala_fr`.

## 1. Scope and output

As in FR-APL-1: scope `ÉligibilitéAidePersonnaliséeLogement`, output `éligibilité`,
labels `eligible` / `not_eligible`. The floor-area condition enters through
`condition_ouverture_l822_10_peuplement_logement`, which holds when
`condition_logement_surface` holds (`code_construction_legislatif.catala_fr:407-410`),
and `éligibilité_logement` requires it (`code_construction_legislatif.catala_fr:76-97`).

## 2. Attributes

| Attribute | Kind | Labels (declared order) | Read by |
|---|---|---|---|
| `residence` | enum | the 9 constructors of `France.Collectivité` | Mayotte version of R822-25 (`REG:5614-5645`), L861-5 1° |
| `nationalite_demandeur` | enum | the 5 labels of FR-APL-1 | L822-2 I and L861-5 1° |
| `situation_familiale` | enum | the 6 constructors of `SituationFamiliale` (`code_construction_legislatif.catala_fr:107-117`); `Mariés` carries the marriage date \|2010-11-26\| of Exemple1 | R822-25 (`REG:1015-1058`): 1 adult for Célibataire and CélibataireSéparéDeFait, 2 for the four others |
| `personnes_a_charge` | enum | `0`, `1`, `2`, `3` | `nombre de ménage.personnes_à_charge` (`REG:1027`, `1044`, `5631`) |
| `autres_occupants` | enum | `0`, `1` | `ménage.nombre_autres_occupants_logement` (same lines) |
| `surface_m_carres` | interval | 16 bands, below | R822-25 (`REG:1029-1058`), R844-4 (`REG:5531-5545`), Mayotte R822-25 (`REG:5614-5645`) |
| `personnes_agees_handicapees_r844_4` | bool | `faux`, `vrai` | R844-4 (`REG:5531-5545`) |

`personnes_a_charge` = k means the first k children of Exemple1, in the test's order
(born 2001-01-01, 2009-01-01, 2012-01-01). k = 3 reproduces Exemple1. The rules of this
table count the list; which child is counted as a dependant for the amount does not
matter here.

### Floor-area bands

The minimum area the encoding requires is:

* R822-25 (all territories except Mayotte): `base + 9 × (autres_occupants +
  personnes_à_charge)` with base 9 for one adult and 16 for two, and 70 m² when that
  minimum reaches 70 with 8 persons or more (`REG:1029-1058`);
* Mayotte (`REG:5614-5645`, an exception to the same base rule): base 9 or 13, plus
  9 per further person in the code, and 54 m² from 9 persons;
* R844-4 when `personnes_agees_handicapees_r844_4` holds (`REG:5531-5545`): 9 m² for
  one person, 16 m² for more, and never eligible with more than 2 persons.

With 1 or 2 adults, 0 or 1 other occupant and 0 to 3 dependants (1 to 6 persons), the
minima the code can compare against are 9, 13, 16, 18, 22, 25, 27, 31, 34, 36, 40, 43,
45, 49 and 52 m². The bands are the 16 intervals between consecutive minima:

`lt_9` [0, 9) representative 8; `9_to_12` [9, 13); `13_to_15` [13, 16);
`16_to_17` [16, 18); `18_to_21` [18, 22); `22_to_24` [22, 25); `25_to_26` [25, 27);
`27_to_30` [27, 31); `31_to_33` [31, 34); `34_to_35` [34, 36); `36_to_39` [36, 40);
`40_to_42` [40, 43); `43_to_44` [43, 45); `45_to_48` [45, 49); `49_to_51` [49, 52);
`ge_52` [52, ∞).

Every band except `lt_9` has its lower bound as representative (the code compares with
`>=`, so the lower bound is the first area that meets a minimum). `surface_m_carrés` is
an integer. The caps (70 m² from 8 persons, 54 m² from 9 persons in Mayotte) cannot be
reached with at most 6 persons; they are recorded here and left untested.

## 3. Fixed inputs

Every other input is Exemple1's (`tests_eligibilite_apl.catala_fr:16-107`), including
`date_courante` \|2020-03-10\| and Locataire of a conventioned social landlord. For
Exemple1's row the oracle builds the inputs with Exemple1's surface (80 m²) in place of
the band representative and checks that they are structurally equal to the test's.

## 4. Exclusions

None. Candidates considered and left out: (a) R844-4 households with dependent
children or other occupants: R844-4 concerns persons in an EHPAD or long-term care unit
(`REG:5515-5528`); a room shared by more than two persons is the case the rule itself
decides (not eligible), so it is a legal outcome to record; (b) a foreign national with
the Mayotte condition outside Mayotte: as in FR-APL-1.

## 5. REJECTED rows (1,980)

All are `Conflict` at `REG:5645.15-5645.21` (Python runtime) /
`REG:5645.16-22` (interpreter), in Mayotte with `personnes_agees_handicapees_r844_4 =
vrai`. The Mayotte surface rule (`exception base`, `REG:5614-5645`) and R844-4
(`étiquette r_844_4 exception base`, `REG:5532`, with its own exception at `REG:5540`)
are two exceptions to the same base rule. When the Mayotte minimum is met and an R844-4
rule also applies, both give a value and Catala raises a conflict. The count is
1,980 = 5 nationalities × (sum over the 72 household shapes of the number of bands in
which both rules fire).

## 6. Band check (`python oracle.py --check-bands`)

For every row, every integer area from 0 to 120 m² other than the band representative
was evaluated: 453,600 evaluations, all giving the output of the band's representative.

## 7. Official tests

| Test | Mapped | Row / reason |
|---|---|---|
| `tests_eligibilite_apl/Exemple1` | yes | `Metropole, francaise, Maries, 3, 1, ge_52, faux` → `eligible` (80 m² is in `ge_52`) |
| `tests_eligibilite_apl/Exemple2` | no | tests `ÉligibilitéAllocationLogement` (allocation de logement) |
| `tests_eligibilite_apl/Exemple3` | no | same as Exemple2 |

`python oracle.py --check-official`: 3/3 direct, 1/3 mapped, 1/1 agreeing.

## 8. Behaviour of the encoding recorded by this table

* One adult with one dependant or one other occupant (two persons) needs 18 m² in the
  encoding (9 + 9). R822-25 as quoted at `REG:1007-1012` sets 16 m² for "un ménage sans
  enfant ou deux personnes". The encoding gives 16 m² to couples only.
* The Mayotte version quoted at `REG:5605-5611` adds six m² per further person; the
  code adds 9 (`REG:5629-5633`). The ground truth follows the code.
* With R844-4, more than two persons are never eligible, and in Mayotte the two
  exception rules conflict (section 5).
* A French applicant in Mayotte is never eligible (FR-APL-1), so the Mayotte surface
  rule shows only in the rows with a foreign applicant meeting the art. 4 condition.

## 9. Interpreter cross-check

A sample of 600 rows (random.Random(2026)) was also run through the Catala interpreter
by `paperC/catala_more/interpreter_crosscheck.py`: see
`paperC/catala_more/interpreter_crosscheck_report.txt` and `paperC/specs/README-FR2.md`.

Result: 600 rows run through the interpreter, 0 disagreements (579 rows whose label assertion passed, 21 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

69,120 rows: 12,864 `eligible`, 54,276 `not_eligible`, 0 EXCLUDED, 1,980 REJECTED. One
official example.
