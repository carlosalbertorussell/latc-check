# FR-APL-3 conversion record

Table: APL eligibility of tenants and sub-tenants: type of landlord and its
convention, family ownership or usufruct of the dwelling, letting part of it to a
third party, decency, main residence and the IFI condition. Sub-table 3 of the five
FR-APL tables. The amount of the aid is out of scope.

File references are to CatalaLang/catala-examples at commit
`2694b17ddd7c2246e207e8f077d586349ee5abea`; `LEG` is
`aides_logement/code_construction_legislatif.catala_fr`, `REG` is
`aides_logement/code_construction_reglementaire.catala_fr`.

## 1. Scope and output

As in FR-APL-1: scope `ÉligibilitéAidePersonnaliséeLogement`, output `éligibilité`,
labels `eligible` / `not_eligible`.

## 2. Attributes

| Attribute | Kind | Labels | Rule that reads it |
|---|---|---|---|
| `mode_occupation` | enum | `Locataire`, `SousLocataire` (both carry a `Location` record) | L822-2 II (`LEG:146-161`), L822-3 (`LEG:171-222`), L831-1 2° (`LEG:689-706`) |
| `bailleur` | enum | `BailleurSocial_conventionne`, `BailleurSocial_non_conventionne`, `BailleurPriveAvecConventionnementSocial_conventionne`, `BailleurPriveAvecConventionnementSocial_non_conventionne`, `BailleurPrive` | L831-1 2° (`LEG:689-706`) |
| `part_propriete_famille` | interval | `Autre`, `famille_moins_de_10pc` (rep. 0,05), `famille_10pc_ou_plus` (rep. 0,1) | L822-3 (`LEG:171-222`) with R822-1 (`REG:103-107`) |
| `part_usufruit_famille` | interval | same three labels | same rules |
| `loue_ou_sous_loue_a_des_tiers` | enum | `Non`; `Oui_moins_de_30_ans_non_conforme_l442_1`; `Oui_moins_de_30_ans_conforme_l442_1`; `Oui_30_ans_ou_plus_non_conforme_l442_1`; `Oui_30_ans_ou_plus_conforme_l442_1` | L822-4 (`LEG:232-254`) |
| `logement_decent_l89_462` | bool | `faux`, `vrai` | L822-9 (`LEG:382-385`) |
| `residence_principale` | bool | `faux`, `vrai` | L821-2 (`LEG:42-47`) |
| `condition_rattache_foyer_fiscal_parent_ifi` | bool | `faux`, `vrai` | L822-8 (`LEG:368-371`) |

Choices made:

* **Landlord.** `TypeBailleur` has three constructors, two of which carry one boolean
  (the convention). The five labels are every value of the type.
* **Family shares.** `ParentOuAutre` is `Autre` or
  `DemandeurOuConjointOuParentOuViaPartsSociétés` carrying a decimal share. The code
  compares the share with 10 % using `<` (`LEG:199-222`, threshold from R822-1 at
  `REG:103-107`), so the labels are `Autre`, a family share below 10 % (including 0)
  and a family share of 10 % or more. Representatives 0,05 and 0,1 (the lower bound
  of the second band).
* **Letting to a third party.** `LouéOuSousLouéÀDesTiers` is `Non` or `Oui` carrying
  the third party's birth date and whether the contract complies with L442-1 of the
  code de l'action sociale. The code tests "under 30 at `date_courante`" with
  `France.VérificationÂgeSupérieurÀ`, whose output `est_supérieur` is
  `date_naissance + 30 an > date_courante` (`prologue_france/France.catala_fr:37-39`):
  despite its name it is true for a person who has **not** reached 30. The age band is
  cut at the 30th birthday (representatives: born 2000-01-01 and 1980-01-01 against
  `date_courante` 2020-03-10).

## 3. Fixed inputs

Every other input is Exemple1's (`tests_eligibilite_apl.catala_fr:16-107`); the
`Location` record keeps Exemple1's other fields (rent 750 €, every boolean `faux`,
`PasDeChangement`), and a `SousLocataire` gets the same record. The oracle checks that
the inputs it builds for Exemple1's row are structurally equal to the test's.

## 4. Exclusions

None. Candidates considered and left out: (a) a social landlord partly owned by the
tenant's family: the code itself provides for ownership "via parts sociales" and
L822-3 decides the case; (b) a sub-tenant whose dwelling has a conventioned landlord:
nothing in the law prevents it; (c) a non-decent dwelling let by a social landlord:
L822-9 decides it.

## 5. REJECTED rows

None.

## 6. Band check (`python oracle.py --check-bands`)

Shares 0, 0,01 and 0,0999 for `famille_moins_de_10pc`; 0,1001, 0,15, 0,19, 0,5 and 1 for
`famille_10pc_ou_plus`; third-party birth dates 1990-03-11, 1995-06-30 and 2019-01-01
for the under-30 labels and 1990-03-10 (30th birthday on the decision date), 1990-03-09
and 1940-01-01 for the 30-or-more labels: 27,840 evaluations, all giving the output of
the label's representative.

## 7. Official tests

| Test | Mapped | Row / reason |
|---|---|---|
| `tests_eligibilite_apl/Exemple1` | yes | `Locataire, BailleurSocial_conventionne, Autre, Autre, Non, vrai, vrai, faux` → `eligible` |
| `tests_eligibilite_apl/Exemple2` | no | tests `ÉligibilitéAllocationLogement` (allocation de logement) |
| `tests_eligibilite_apl/Exemple3` | no | same as Exemple2 |

`python oracle.py --check-official`: 3/3 direct, 1/3 mapped, 1/1 agreeing.

## 8. Behaviour of the encoding recorded by this table

* Eligible rows (32): `Locataire` with a conventioned social or private landlord, both
  family shares `Autre` or below 10 %, letting `Non`, or to a person under 30, or to a
  person of 30 or more under an L442-1 contract, a decent main residence and no IFI.
* A `SousLocataire` is never eligible: `condition_logement_bailleur` has rules for
  `Locataire` (`LEG:689-706`), `RésidentLogementFoyer`, `AccessionPropriété…` and
  `LocationAccession` only, so it is `faux` for sub-tenants.
* R822-1 (quoted at `REG:97-101`) adds "sans que l'ensemble de ces parts puisse
  égaler ou dépasser 10 % de la propriété ou de l'usufruit du logement". The code
  compares the ownership share and the usufruct share with 10 % one at a time
  (`LEG:199-222`) and has no test on their total. Read as a cap on ownership and
  usufruct shares taken together, the text would refuse the row with both shares at
  0,05 (the representatives); the code gives `eligible`, and the table follows the
  code.
* L822-4 extends L822-3 to sub-tenants and owners (`LEG:263-266`); the code applies
  L822-3 to `Locataire` only (`LEG:185-196`). For sub-tenants this makes no difference
  here since they are never eligible.

## 9. Interpreter cross-check

A sample of 600 rows was also run through the Catala interpreter: see
`paperC/catala_more/interpreter_crosscheck_report.txt` and `paperC/specs/README-FR2.md`.

Result: 600 rows run through the interpreter, 0 disagreements (600 rows whose label assertion passed, 0 REJECTED rows that failed with a run-time error at the same source position as in the Python runtime).

## 10. Counts

3,600 rows: 32 `eligible`, 3,568 `not_eligible`, 0 EXCLUDED, 0 REJECTED. One official
example.
