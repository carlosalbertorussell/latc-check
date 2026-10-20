# FR-AF-1: conversion choices (second coder)

Rule: allocations familiales of a household with exactly one child, amount regime. This
file is `CONVERSION_2.md`: it plays the part of the `CONVERSION.md` of FORMAT.md,
named as the second-coder task asks. Sections C1 to C4 and A1 to A7 are shared with the
other French samples of the second coder; the section for FR-AF-1 comes last.

## Sources

* Rules: CatalaLang/catala-examples, commit `2694b17ddd7c2246e207e8f077d586349ee5abea`.
  Paths below are relative to that repository; `L:`, `R:`, `D:` abbreviate
  `allocations_familiales/securite_sociale_{L,R,D}.catala_fr`, `epi:` abbreviates
  `allocations_familiales/epilogue.catala_fr`, `pro:` abbreviates
  `allocations_familiales/prologue.catala_fr`, `dec:` abbreviates
  `allocations_familiales/decrets_divers.catala_fr`.
* Executable: `paperC/catala_family_benefits/generated/` (Catala 1.3.0 Python build of
  the same commit), unedited. The line references `gen:` are to
  `generated/Allocations_familiales.py`.
* Every choice below was made by reading these sources and running the encoding. No
  other conversion of these rules was consulted (see `../README-FR-CODE2.md`).

## Choices shared by the French samples of the second coder

### C1. Fixed date: 2020-05-01

`date_courante` is fixed at 2020-05-01. Reasons: it is the date of the only
`PrestationsFamiliales` test (`tests/tests_ouverture_droits.catala_fr:62`) and of 7 of the
14 household tests; and on the period 2020-04-01 to 2020-12-31 every date-dependent
parameter is constant: BMAF 414,40 EUR (`base_mensuelle_allocations_familiales/Bmaf.catala_fr:52-58`),
SMIC 10,15 EUR and 7,66 EUR for Mayotte (`smic/Smic.catala_fr:81-112`), plafonds of
D521-3 for 2020 (`dec:102-123`), Mayotte rates for 2020 (`dec:389-398`, `dec:481-487`,
`dec:562-568`). The date is later than both validity assertions (SMIC from 2019-01-01,
BMAF from 2019-04-01) and earlier than the 2024 Mayotte SMIC overlap, so no cell can
raise a Catala error because of the date.

An official test is mapped only when its date lies in that period; its ages are then
measured at its own date. Test10 (2020-04-20) is mapped this way.

### C2. Residence: three labels

`France.Collectivité` has nine values (`prologue_france/France.catala_fr:9-18`). The
encoding distinguishes them only through three predicates: `régime_outre_mer_l751_1`
(six values, `L:376-385`), `résidence = Mayotte` (`dec:181-238`, `dec:286-569`,
`smic/Smic.catala_fr:103-112`), and the SMIC rule for every other value
(`smic/Smic.catala_fr:81-95`, which lists Métropole and Saint-Pierre-et-Miquelon with
the six overseas values). Labels:

| label | members | representative |
|---|---|---|
| `metropole` | Métropole, SaintPierreEtMiquelon | Métropole |
| `drom_l751_1` | Guadeloupe, Guyane, Martinique, LaRéunion, SaintBarthélemy, SaintMartin | Guadeloupe |
| `mayotte` | Mayotte | Mayotte |

`oracle.py --check-groups` re-evaluates rows with every other member in place of the
representative; the result is in `../README-FR-CODE2.md`.

### C3. Child's monthly earnings: three intervals

The only comparison on `rémuneration_mensuelle` is `<= plafond_l512_3_2` (`L:70`, `L:83`),
with `plafond_l512_3_2 = (smic.brut_horaire * 55%) * 169,0` (R512-2 `R:29-31`; R755-0-2
`R:218-223` gives the same formula overseas). At 2020-05-01 the encoding gives
711,49 EUR for Mayotte and 943,02 EUR elsewhere (checked by bisection through the
encoding; `oracle.py` re-checks both cut points on every run). Cutting at both values
gives `jusqu_plafond_mayotte` = [0; 711,49] (representative 0,00),
`entre_plafonds` = (711,49; 943,02] (800,00), `au_dessus_plafonds` = (943,02; +inf)
(1500,00). Negative earnings are outside the domain.

### C4. Who has `droit_ouvert`

Not a choice: the encoding computes it (L512-3 `L:52-72`; L821-3 exception
`autres_codes.catala_fr:22-26`). Facts used in the choices below: a child before or
within compulsory schooling is entitled whatever its earnings; after compulsory
schooling, it needs earnings under the ceiling and age under 20; holding personal
housing aid removes the entitlement in every case.

## Mapping official tests

An official test maps onto a table when (i) it uses the table's entry point and number
of children, (ii) its date lies in the period of C1, (iii) each input falls in the region
of a declared label, and (iv) each input that is fixed in the table falls in the region of
the fixed value (for earnings: the band of 0,00 EUR). Its `output` is the label computed
from the encoding at the official inputs; `--check-official` checks that the encoding
reproduces the official expected value, and that the oracle at the representatives of
the mapped row returns the same label. Every official test is run through the encoding
in every folder; the per-folder list of unmapped tests with reasons is below.

## Choices shared by FR-AF-1, FR-AF-2 and FR-AF-3

Rule: the household allowance, scope `AllocationsFamiliales` (`pro:71-153`), reached
through the wrapper `InterfaceAllocationsFamiliales` (`epi:73-136`) that the official
tests use; Python `generated.Allocations_familiales.interface_allocations_familiales`.

### A1. Split into sub-tables by number of children

With every input that the rule reads as an attribute (labels as in A2 to A4), one child
gives 29,160 combinations; two children give 3,149,280 and three children 1,020,366,720
even with `attributaire` fixed.
The statute's own cases are organised by number of children: one child (no allowance in
metropolitan France; overseas L755-12 `L:436-442` and D755-5 `D:384-433`; Mayotte
`dec:191-194`), two children (base from the second child, D521-1 `D:34-50`), three
children (rate of the third child, majoration of every child L521-3 al. 2 `L:330-342`,
allocation forfaitaire L521-1 al. 2 `L:139-155` which requires `nombre de enfants_à_charge
>= 3`). The sub-tables follow that split:

| sample | children | per-child attributes | per-child inputs fixed |
|---|---|---|---|
| FR-AF-1 | 1 | age, earnings, prise en charge, déjà ouvert, housing aid | none |
| FR-AF-2 | 2 | age, earnings, prise en charge | déjà ouvert = vrai, housing aid = faux |
| FR-AF-3 | 3 | age, déjà ouvert | earnings = 0, prise en charge = EffectiveEtPermanente, housing aid = faux |

Each per-child set is the largest that keeps the table under 200,000 combinations
(FR-AF-2: 196,830; FR-AF-3: 174,960), chosen so that every per-child input is varied in
at least one sub-table and each sub-table keeps the inputs that matter most for its case:
with two children, which child is counted (earnings, care) decides the base; with three
children, the forfaitaire is new, and it reads `a_déjà_ouvert_droit_aux_allocations_familiales`.
In FR-AF-2 `déjà ouvert` is fixed because it is read only by the forfaitaire, which needs
three children (`L:143`); a check on 1,500 random rows of FR-AF-2 with the value flipped
gave no difference. Housing aid is fixed in FR-AF-2 and FR-AF-3; its only effect is to
remove the child from the entitled list (C4), which FR-AF-1 and FR-PF cover.

Households with four or more children are left out. In the general scale a fourth child
only repeats the third-child rate (`D:44-49`, multiplier `n - 2`); the Mayotte fourth-child
rate (`dec:230-238`) is therefore the one statutory case not covered by these tables.

### A2. Household attributes

| attribute | values | source |
|---|---|---|
| `residence` | C2 | C2 |
| `attributaire` (FR-AF-1 only) | parent, tiers_titre_I, aucun | L521-2 assertion `L:240-246`; wrapper `epi:91-96` |
| `ressources` | A4 | A4 |
| `avant_2012` | false, true | `avait_enfant_à_charge_avant_1er_janvier_2012`, read only for Mayotte, `dec:295-407` |

`attributaire` combines the two inputs `personne_charge_effective_permanente_est_parent`
and `personne_charge_effective_permanente_remplit_titre_I`, which are read only by the
L521-2 assertion. `parent` = (vrai, faux), `tiers_titre_I` = (faux, vrai), `aucun` =
(faux, faux). The pair (vrai, vrai) behaves as `parent`, since the assertion holds as soon
as the person is a parent; it is not a label of its own. In FR-AF-2 and FR-AF-3 the pair is
fixed to (vrai, faux), the value every official test uses (`règle
f.i_personne_charge_effective_permanente_est_parent rempli` in each test scope).

Exclusion X-AF-ATTRIB (FR-AF-1): `attributaire == 'aucun'`. The encoding asserts that the
person in charge is a parent or meets Title I; an input outside that assertion is outside
the domain of the rule, so it is declared impossible here, and the encoding is not run on it.

### A3. Per-child attributes

**Age** (`eN_age`). The household wrapper derives school status from the birth date
(`epi:121-131`), so the child's age is the attribute and `obligation_scolaire` follows. The
bands cut at every comparison the code makes with a birth date, at `date_courante`
2020-05-01:

| label | region (b = date_de_naissance, t = date_courante) | representative b | comparison |
|---|---|---|---|
| `moins_3` | b + 3 an >= t | 2019-05-01 | `epi:123` (Avant) |
| `3_11` | b + 3 an < t and b + 11 an > t | 2013-05-01 | `D:419` |
| `11_14` | b + 11 an <= t and b + 14 an > t | 2008-05-01 | `D:419`; 14 an `R:54` compared at `L:319`, `L:339` |
| `14_16` | b + 14 an <= t and b + 16 an > t | 2005-05-01 | `D:420` |
| `anniversaire_16` | b + 16 an = t | 2004-05-01 | `epi:127` counts the day as Pendant, `D:431` as 16 or more |
| `16_19` | b + 16 an < t and (b + 20 an) - t >= 365 jour | 2002-05-01 | `epi:127` (Après), `L:149-151` |
| `19_20` | (b + 20 an) - t < 365 jour and b + 20 an > t | 2000-11-01 | `L:149-151`, `L:71` |
| `20_23` | b + 20 an <= t and b + 11 an > 2008-04-30 | 1999-05-01 | `L:71`, `R:81` |
| `23_plus` | b + 11 an <= 2008-04-30 | 1995-05-01 | `R:79-83` (majoration age 16 for children born on or before 1997-04-30) |

The 16th birthday is a band of one day because the two comparisons at 16 differ in
strictness (`>=` at `epi:127`, `>` and `<=` at `D:420`, `D:431`). The band `moins_3` has
no lower bound, as in the code, so a birth date after `date_courante` falls in it (official
Test6 has a child born 2020-09-25 with `date_courante` 2020-05-01). The `23_plus` cut
comes from a fixed calendar date (2008-04-30); at 2020-05-01 it separates children born on
or before 1997-04-30. Every child in the same band has the same representative birth
date; when two children share a birth date the encoding treats the last of them in list
order as the eldest (`epi:12-14`; the reduction at `gen:574-578` keeps the second argument
on ties). The table keeps that behaviour.

**Earnings** (`eN_remuneration`): C3.

**Prise en charge** (`eN_prise_en_charge`). `PriseEnCharge` has five values
(`pro:10-15`). The amount reads it only through `prise_en_compte` (Complète, Partagée,
Zéro; `L:188-281`), which weights the base (`R:122-166`) and the majorations
(`R:188-201`); `versement` is a separate output that `montant_versé` never reads. Labels:

| label | members | representative |
|---|---|---|
| `complete` | EffectiveEtPermanente, GardeAlternéeAllocataireUnique, ServicesSociauxAllocationVerséeÀLaFamille | EffectiveEtPermanente |
| `partagee` | GardeAlternéePartageAllocations | GardeAlternéePartageAllocations |
| `services_sociaux` | ServicesSociauxAllocationVerséeAuxServicesSociaux | the same |

**Déjà ouvert** (`eN_deja_ouvert`): `a_déjà_ouvert_droit_aux_allocations_familiales`,
false or true (`L:153`).

**Housing aid** (`eN_aide_logement`): false or true (C4).

`d_identifiant` is the child's position in the list (1, 2, 3).

### A4. Household resources: five labels relative to the D521-3 ceilings

`ressources_ménage` is compared with `plafond_I_d521_3` and `plafond_II_d521_3`
(D521-1 `D:35`, `D:76-78`, `D:120`; D521-2 `D:233`, `D:247-249`, `D:262`), which at 2020 are
57 759 EUR + 5 775 EUR x n and 80 831 EUR + 5 775 EUR x n, n being the number of children
with `droit_ouvert` (`dec:102-123`). The complément dégressif adds the comparisons
`ressources <= plafond + allocation x 12` (`D:169-185` for base and majorations,
`D:277-308` for the forfaitaire), whose right side depends on the computed amount. A
fixed list of euro cut points cannot follow thresholds that move with n and with the
amount, so the labels are defined relative to the household's own ceilings, with
a = max(montant_versé_base + montant_versé_majoration, montant_versé_forfaitaire):

| label | region | representative |
|---|---|---|
| `jusqu_plafond_I` | r <= plafond_I | 30 000,00 EUR (below plafond_I for every n) |
| `zone_degressive_I` | plafond_I < r <= plafond_I + 12 a | plafond_I + 1,00 EUR |
| `entre_plafonds_I_II` | plafond_I + 12 a < r <= plafond_II | plafond_II |
| `zone_degressive_II` | plafond_II < r <= plafond_II + 12 a | plafond_II + 1,00 EUR |
| `au_dela_plafond_II` | r > plafond_II + 12 a | 200 000,00 EUR |

The oracle obtains plafond_I and plafond_II for a row by running the encoding once with
r = 0 (the ceilings depend on n only), then runs it again with the representative. The
`zone_degressive_*` label is the part of a tier where the complément dégressif can be
paid; whether it is paid also depends on `droit_ouvert_complément`, which L755-12 turns off
overseas with a single entitled child (`L:459-464`).

When a = 0 (or less than 1/12 EUR), a `zone_degressive_*` region is empty and its
representative plafond + 1,00 EUR lies in the next region. Such cells are kept and
evaluated at the representative; `oracle.py --enumerate` counts them (FR-AF-1: 6,624;
FR-AF-2: 30,796; FR-AF-3: 720 rows). Their output then equals that of the next label, which
is the encoding's answer for the representative value.

### A5. Output: amount regime

The encoding returns `montant_versé` (`epi:45-52`) and `versement`. The output label
names the statutory regime that produced the amount, read from the components the
encoding computed (locals of the generated function, see `ENVIRONMENT.md`):

* `sans_droit` when `droit_ouvert_base` is false (fewer than 2 entitled children, L521-1
  `L:124-127`; overseas fewer than 1, L755-12 `L:436-442`; Mayotte fewer than 1,
  `dec:191-194`). The amount is then 0.
* otherwise `bareme/tier/parts`:
  * `bareme`: `mayotte` (`dec:181-238` and the 2020 rates), `mayotte_avant_2012` (Mayotte
    with `avait_enfant_à_charge_avant_1er_janvier_2012`, flat 57,28 EUR for the first child,
    `dec:400-407`), `outre_mer_un_enfant` (L751-1 territory with exactly one entitled
    child, D755-5 `D:384-433`), else `general` (D521-1 to D521-3);
  * `tier`: `T1` if r <= plafond_I, `T2` if r <= plafond_II, else `T3` (the three
    paragraphs of D521-1 and D521-2). Left out for `outre_mer_un_enfant`, whose D755-5
    rates do not depend on resources and whose forfaitaire and complément are turned
    off (`L:451-464`): the label is then `outre_mer_un_enfant/parts`;
  * `parts`: the non-zero components joined by `+`, in the order `B` (montant_versé_base),
    `M` (montant_versé_majoration), `F` (montant_versé_forfaitaire), `C`
    (montant_versé_complément_pour_base_et_majoration plus
    montant_versé_complément_pour_forfaitaire); `nul` when all are zero (for instance
    every entitled child placed with the social services, weight 0).

`output.values` lists the labels that occur in `ground_truth.csv` or
`official_examples.csv`, in the order sans_droit, then by bareme, tier and parts.

### A6. Behaviour of the encoding that the table reproduces

Kept as the ground truth; none of these is corrected:

* Majorations are summed over every child in `enfants_à_charge` (`epi:39-43`), and
  `droit_ouvert_majoration` (`L:314-342`) does not test `droit_ouvert`. A child without
  entitlement (for instance 20 or older) who is not the eldest and has reached the
  majoration age adds a majoration. This also makes the D755-5 majoration rates reachable
  overseas with one entitled child and an older sibling (labels `outre_mer_un_enfant/B+M`,
  and `.../M` when the entitled child is placed with the social services).
* The forfaitaire test `(b + 20 an) - t < 365 jour` (`L:148-152`) also holds for every
  child already past 20, so a child of 21 or 25 with `déjà ouvert` gives `F` (FR-AF-3).
* Mayotte with one child can receive the complément dégressif: L755-12 turns it off only
  in L751-1 territories (`L:459-464`), and Mayotte is not one of them.

### A7. Errors

No cell raises a Catala error at 2020-05-01 (REJECTED = 0 in every sub-table). The cells
excluded by X-AF-ATTRIB are not run through the encoding, which would fail its L521-2
assertion on them.

## Choices for FR-AF-1 (one child)

Attributes in order: `residence`, `attributaire`, `ressources`, `avant_2012`, `e1_age`,
`e1_remuneration`, `e1_prise_en_charge`, `e1_deja_ouvert`, `e1_aide_logement`
(3 x 3 x 5 x 2 x 9 x 3 x 3 x 2 x 2 = 29,160). Every input of the wrapper is an attribute
or the fixed date. Exclusion X-AF-ATTRIB removes the 9,720 rows with `attributaire =
aucun`. In metropolitan France one child never opens the allowance (L521-1 `L:124-127`),
so every metropolitan row is `sans_droit`; the overseas and Mayotte rows carry the
statutory cases of a single child.

Official examples (2 rows): Test3 (`tests/tests_allocations_familiales.catala_fr:94-100`,
Guyane, one child born 2007, 63 540 EUR, 24,37 EUR) -> `outre_mer_un_enfant/B`, with
resources in `zone_degressive_I` (plafond_I = 63 534 EUR for one entitled child; the
complément is off under L755-12); Test5 (`:120-126`, Métropole, same child, 30 000 EUR,
0 EUR) -> `sans_droit`.

Unmapped official tests, with reasons (all 18 official cases pass through the encoding):

* `tests_ouverture_droits/Test1/enfant1` to `enfant4`: they assert `droit_ouvert` of
  `PrestationsFamiliales`, which is sample FR-PF; the household amount is not asserted.
* Test1 (`:66-73`), Test7 (`:163-170`), Test12 (`:304-345`): four children.
* Test2 (`:80-87`), Test11 (`:266-298`): three children.
* Test4, Test6, Test8, Test9, Test10, Test14: two children.
* Test13 (`:351-367`, Mayotte, one child): date 2019-08-26 lies outside the period of C1
  (BMAF 413,16 EUR and the 2019 Mayotte rates apply there).
