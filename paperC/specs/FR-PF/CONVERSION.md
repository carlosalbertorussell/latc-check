# FR-PF: conversion record

Table: per-child entitlement `PrestationsFamiliales.droit_ouvert` of the Catala
encoding of the French family benefits, evaluated at `date_courante = 2020-05-01`.

Encoding: CatalaLang/catala-examples commit `2694b17ddd7c2246e207e8f077d586349ee5abea`,
compiled to Python with Catala 1.3.0 (`paperC/catala_family_benefits/`, unmodified).
File references `file:line` below point into that commit; `L`, `R`, `D` articles are
Code de la sécurité sociale articles as cited in the Catala source.

## Rule being tabulated

`droit_ouvert de enfant` is defined by three rules:

| Rule | Source | Condition |
|---|---|---|
| L512-3 1° (label `cas_base`) | securite_sociale_L.catala_fr:52-58 | `obligation_scolaire` is `Avant` or `Pendant` |
| L512-3 2° (label `cas_base`) | securite_sociale_L.catala_fr:65-72 | `obligation_scolaire` is `Après`, `rémuneration_mensuelle <= plafond_l512_3_2`, `date_de_naissance + âge_l512_3_2 > date_courante` |
| L821-3 (`exception cas_base`, `non rempli`) | autres_codes.catala_fr:21-27 | `bénéficie_titre_personnel_aide_personnelle_logement` |

`âge_l512_3_2 = 20 an` (R512-2, securite_sociale_R.catala_fr:20-21).
`plafond_l512_3_2 = (smic.brut_horaire * 55%) * 169,0` (R512-2,
securite_sociale_R.catala_fr:29-31; the R755-0-2 exception for the L751-1
territories has the same formula, securite_sociale_R.catala_fr:218-223).
Default when no rule applies: `faux` (Catala default of a `condition`).

## Interpretive choices

**C1. Output: `droit_ouvert`.** The protocol allowed `droit_ouvert` and/or
`conditions_hors_âge`. `droit_ouvert` was chosen because it is the per-child
entitlement, the official test `tests_ouverture_droits.catala_fr` asserts it,
and `AllocationsFamiliales` filters children with it
(securite_sociale_L.catala_fr:86-90). `conditions_hors_âge`
(securite_sociale_L.catala_fr:76-84) is a disjunction over the three values of
`obligation_scolaire`, which always holds, joined with the earnings test; it
reduces to `rémuneration_mensuelle <= plafond_l512_3_2` and would give a
one-attribute table. Labels: `entitled` = `vrai`, `not_entitled` = `faux`.

**C2. Fixed date `2020-05-01`.** This is the `date_courante` of the only
official test of the scope (`tests_ouverture_droits.catala_fr`, scope `Test1`,
`définition f.date_courante égal à |2020-05-01|`) and of seven of the fourteen
household tests. The SMIC rules for 2020 apply (smic/Smic.catala_fr:80-110:
10,15 € for Métropole, the L751-1 territories and Saint-Pierre-et-Miquelon;
7,66 € for Mayotte). The Mayotte SMIC conflict described in
`catala_family_benefits/README.md` (2024-01-01 to 2024-10-31) is outside this date.

**C3. Residence: all nine values of `France.Collectivité`.** Residence acts on
`droit_ouvert` only through the earnings ceiling (the SMIC differs for Mayotte).
Labels are the ASCII constructor names of the generated Python
(`LaReunion`, `SaintBarthelemy`, `Metropole`); the Catala names carry accents.

**C4. `prise_en_charge` is included and is not read by the rule.** The protocol
lists it as an attribute. No rule of `droit_ouvert` reads it
(`inputs.md` section 1.4; generated code `Allocations_familiales.py:498-533`
reads only `beneficie_titre_personnel_aide_personnelle_logement`,
`obligation_scolaire`, `remuneration_mensuelle` and `date_de_naissance`). It is
an attribute that does not influence the output.

**C5. Age bands.** The only age comparison the rule makes is
`date_de_naissance + 20 an > date_courante` (securite_sociale_L.catala_fr:71).
The protocol asks for every threshold; the thresholds 3 an and 16 an of the
Code de l'éducation L131-1, as the same codebase encodes them in the epilogue
(epilogue.catala_fr:121-131: `b + 3 an >= dc` → Avant, else `b + 16 an >= dc` →
Pendant, else Après), are added so that exclusions X1-X3 can be stated. Bands,
with `b` the date of birth and `dc = 2020-05-01`:

| Label | Definition | Birth dates | Representative |
|---|---|---|---|
| `a00_03` | `b + 3 an >= dc` | from 2017-05-01 (includes children born after `dc`) | 2019-01-01 |
| `a03_16` | `b + 3 an < dc` and `b + 16 an >= dc` | 2004-05-01 to 2017-04-30 | 2007-01-01 |
| `a16_20` | `b + 16 an < dc` and `b + 20 an > dc` | 2000-05-02 to 2004-04-30 | 2003-01-01 |
| `a20_plus` | `b + 20 an <= dc` | up to 2000-05-01 | 1999-01-01 |

The boundary days follow the encoding's comparisons: on the 3rd birthday a
child is still `Avant`, on the 16th still `Pendant`, and on the 20th birthday
the age condition already fails (`>` is strict). The representatives of
`a03_16`, `a16_20` and `a20_plus` are the birth dates of the official test
children. `--self-check` verifies with the runtime's own date arithmetic
(`AbortOnRound`, as in the generated code) that each band's first and last
birth dates fall inside it and the neighbouring days fall outside. No
representative is a 29 February.

**C6. Earnings bands and the rounded ceiling.** `rémuneration_mensuelle` is
split below, at and above `plafond_l512_3_2`. The Catala 1.3.0 runtime rounds
money to the cent after each multiplication (`Money.__mul__` in
`runtime/catala/catala_runtime.py:564-566`), so the encoding computes
`10,15 € × 55 % = 5,58 €` (5,5825 rounded), then `× 169 = 943,02 €`; for Mayotte
`7,66 € × 55 % = 4,21 €`, then `× 169 = 711,49 €`. `inputs.md` section 3.8
quotes the unrounded products 932,29 € (2019) and 703,63 €; at 2020-05-01 the
values that the encoding uses are 943,02 € and 711,49 €, found by bisection on
`conditions_hors_âge` (`--self-check`). Representatives: `lt_plafond` = 400,00 €
(the earnings of official child `enfant3`), `eq_plafond` = the ceiling of the
row's residence (943,02 €, Mayotte 711,49 €; this is the one representative that
depends on another attribute, recorded in `spec.json` under
`representative_by_residence`), `gt_plafond` = 1 000,00 € (the earnings of
official child `enfant2`; above both ceilings).

**C7. `apl`** is `bénéficie_titre_personnel_aide_personnelle_logement`. The other
Boolean field of `Enfant`, `a_déjà_ouvert_droit_aux_allocations_familiales`, is
not read by the scope and is fixed to `vrai`, as in every official test child.
`identifiant` is fixed to 1.

**C8. Exclusions X1-X3.** The scope `PrestationsFamiliales` accepts
`obligation_scolaire` and `date_de_naissance` as independent inputs, so any
pair can be evaluated. Code de l'éducation L131-1 (quoted at
epilogue.catala_fr:104-110) makes schooling compulsory from three to sixteen,
and the encoding's own interface derives `obligation_scolaire` from the date of
birth with exactly the comparisons in C5 (epilogue.catala_fr:121-131). A pair
that contradicts that derivation describes no real child, so it is excluded:

* X1: `Avant` with any band other than `a00_03`;
* X2: `Pendant` with any band other than `a03_16`;
* X3: `Après` with `a00_03` or `a03_16`.

L131-1 second paragraph ("ne fait pas obstacle à l'application des
prescriptions particulières imposant une scolarité plus longue") would allow a
later end of compulsory schooling in special cases; the encoding ignores it,
and so do the exclusions. With the exclusions removed, the encoding still
returns a value for every pair (condition 2 of the protocol evaluates them).

**C9. Official examples.** `tests_ouverture_droits.catala_fr` `Test1` asserts
`droit_ouvert` for four children (Métropole, 2020-05-01); each child becomes
one row of `official_examples.csv` (case ids `ouverture_droits.Test1.enfantN`).
The children's earnings 0 € map to `lt_plafond` (same band as the 400 €
representative). The 14 scopes of `tests_allocations_familiales.catala_fr`
assert only the household amount `i_montant_versé`; they contain no assertion
on a single child's `droit_ouvert`, so none maps onto this table.
`--check-official` re-runs all 15 official scopes through the generated Python
(15/15 pass), re-runs the four `droit_ouvert` assertions directly, maps each
child to its row and checks the oracle's label (4/4 agree).

**C10. REJECTED.** No row raises an error at 2020-05-01 (no `REJECTED` rows).

## Counts

3 240 rows = 9 × 3 × 5 × 4 × 3 × 2. EXCLUDED 2 160 (X1 810, X2 810, X3 540),
valid 1 080: `entitled` 360, `not_entitled` 720, REJECTED 0.

## Band robustness

`--self-check` re-evaluates each valid row with every alternative value of one
attribute at a time: the first and last birth dates of the age band (plus
2020-05-01 and the post-`dc` birth 2020-09-25 for `a00_03`, and 1990-01-01 and
1980-06-15 for `a20_plus`), and 0,00 € / ceiling − 0,01 € for `lt_plafond`,
ceiling + 0,01 € / 5 000,00 € for `gt_plafond`. Result: 4 140 alternative
evaluations, 0 label changes, so each band's label does not depend on the
representative chosen within it.
