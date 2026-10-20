# French family benefits (Catala) as LATC decision tables

Four tables built from the Catala encoding of the French family benefits
(CatalaLang/catala-examples commit `2694b17`, compiled with Catala 1.3.0 and run
through the unmodified Python build in `paperC/catala_family_benefits/`), in the
shared spec format: `spec.json`, `ground_truth.csv`, `official_examples.csv`,
`oracle.py`, `ENVIRONMENT.md`, `CONVERSION.md`, `SHA256SUMS`. `frcatala.py` is a
helper used by every oracle; the same file (same sha256) is in each folder, and
the three FR-AF folders share one `oracle.py` that reads the table layout from
`spec.json`. All tables are evaluated at `date_courante = 2020-05-01`.

| Table | What it tabulates | Attributes | Output |
|---|---|---|---|
| `FR-PF` | `PrestationsFamiliales.droit_ouvert` of one child | residence, obligation_scolaire, prise_en_charge, age (4 bands), remuneration (below / at / above the ceiling), apl | `entitled`, `not_entitled` |
| `FR-AF-1` | household amount regime by residence, resources, the three household conditions, ages of up to 3 children | residence, ressources (5 bands), avait_enfant_avant_2012, est_parent, titre_I, enfant1-3_age (absent + 7 bands) | `zero`, `general_t1`, `general_t2`, `general_t3`, `outre_mer_1_enfant`, `mayotte` |
| `FR-AF-2` | the same regime for exactly 2 children, with per-child earnings and care | residence, ressources (3 bands), enfant1-2: age (7), remuneration (2), prise_en_charge (5) | as FR-AF-1 |
| `FR-AF-3` | components of the amount for exactly 3 children in Métropole at 30 000 € | enfant1-3: age (7), remuneration (2), deja_ouvert, apl | `zero`, `base`, `base_majoration`, `base_forfaitaire`, `base_majoration_forfaitaire` |

FR-AF is split in three because the household attributes and full per-child
detail for several children together exceed 200 000 combinations.

## Sizes and counts

| Table | Rows | Valid | EXCLUDED | REJECTED | Valid rows by label |
|---|---|---|---|---|---|
| FR-PF | 3 240 | 1 080 | 2 160 | 0 | entitled 360, not_entitled 720 |
| FR-AF-1 | 184 320 | 138 240 | 0 | 46 080 | general_t1 41 472, general_t2 41 472, general_t3 20 736, mayotte 15 120, outre_mer_1_enfant 12 960, zero 6 480 |
| FR-AF-2 | 132 300 | 132 300 | 0 | 0 | outre_mer_1_enfant 29 088, zero 33 564, general_t1 19 200, general_t2 19 200, general_t3 19 200, mayotte 12 048 |
| FR-AF-3 | 175 616 | 175 616 | 0 | 0 | zero 124 416, base 22 032, base_majoration 20 566, base_majoration_forfaitaire 6 442, base_forfaitaire 2 160 |

* FR-PF EXCLUDED: X1 810, X2 810, X3 540. Each pairs `obligation_scolaire`
  with an age band that the Code de l'éducation L131-1 derivation in the
  encoding's own epilogue (epilogue.catala_fr:121-131) rules out.
* FR-AF-1 REJECTED: all 46 080 rows with `est_parent` = false and
  `titre_I` = false, where the encoding's L521-2 assertion fails
  (`AssertionFailed` at securite_sociale_L.catala_fr:241.3-246.6). It is kept as
  REJECTED and not declared as an exclusion, because the statute opens the right
  from the father or mother in that case; the encoding does not model it.
* FR-AF-2 and FR-AF-3 fix the parent conditions to the official tests' values
  and have no REJECTED rows. None of the FR-AF tables declares exclusions (each
  table's CONVERSION.md, T5 or T4, gives the reasons).

## Official tests

Run directly through the generated Python by every oracle's
`--check-official`: 15 of 15 scopes pass (the 4 `droit_ouvert` assertions of
`tests_ouverture_droits.catala_fr` Test1 and the 14 amount assertions of
`tests_allocations_familiales.catala_fr`).

| Table | Official examples | Agree with oracle | Cases |
|---|---|---|---|
| FR-PF | 4 | 4 | ouverture_droits Test1, enfant1-4 |
| FR-AF-1 | 3 | 3 | Test2, Test3, Test5 |
| FR-AF-2 | 4 | 4 | Test4, Test6, Test9, Test10 |
| FR-AF-3 | 1 | 1 | Test2 |

Tests that map onto no table: Test1 (four children: no table has four slots),
and Test7, Test8, Test11, Test12, Test13, Test14, which are dated 2019-08-26,
2021 or 2022, outside the 2020 parameter period [2020-04-01, 2020-12-31] in
which every date-dependent parameter equals its 2020-05-01 value. Test10 is
dated 2020-04-20, inside that period, and is mapped with its ages computed at
its own date. Every per-table reason is listed in that table's CONVERSION.md.
The 14 household tests contain no assertion on one child's `droit_ouvert`, so
FR-PF uses only the four children of the ouverture_droits test.

## Declared values the official examples never use

| Table | Attribute | Values never used |
|---|---|---|
| FR-PF | residence | Guadeloupe, Guyane, Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte |
| FR-PF | obligation_scolaire | Avant |
| FR-PF | prise_en_charge | GardeAlterneePartageAllocations, GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille, ServicesSociauxAllocationVerseeAuxServicesSociaux |
| FR-PF | age | a00_03 |
| FR-PF | remuneration | eq_plafond |
| FR-PF | apl | true |
| FR-AF-1 | residence | Guadeloupe, Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte |
| FR-AF-1 | ressources | eq_plafond_I, eq_plafond_II, gt_plafond_II |
| FR-AF-1 | avait_enfant_avant_2012 | true |
| FR-AF-1 | est_parent | false |
| FR-AF-1 | titre_I | true |
| FR-AF-1 | enfant1_age | absent, a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus |
| FR-AF-1 | enfant2_age | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus |
| FR-AF-1 | enfant3_age | a00_03, a03_11, a11_14, a14_16, a16_19, a19_20 |
| FR-AF-2 | residence | Guyane, Martinique, LaReunion, SaintBarthelemy, SaintMartin, SaintPierreEtMiquelon, Mayotte |
| FR-AF-2 | ressources | gt_plafond_II |
| FR-AF-2 | enfant1_age | a00_03, a14_16, a19_20, a20_plus |
| FR-AF-2 | enfant1_remuneration | (none) |
| FR-AF-2 | enfant1_prise_en_charge | GardeAlterneePartageAllocations, GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille |
| FR-AF-2 | enfant2_age | a14_16, a19_20, a20_plus |
| FR-AF-2 | enfant2_remuneration | (none) |
| FR-AF-2 | enfant2_prise_en_charge | GardeAlterneeAllocataireUnique, ServicesSociauxAllocationVerseeALaFamille |
| FR-AF-3 | enfant1_age, enfant2_age | a00_03, a03_11, a14_16, a16_19, a19_20, a20_plus |
| FR-AF-3 | enfant3_age | a00_03, a03_11, a11_14, a14_16, a16_19, a19_20 |
| FR-AF-3 | enfant1-3_remuneration | gt_plafond |
| FR-AF-3 | enfant1-3_deja_ouvert | false |
| FR-AF-3 | enfant1-3_apl | true |

Every output label appears in each table's ground truth.

## Checks beyond the official tests

`--self-check` (each oracle) verifies against the encoding itself:

* every age band's first and last birth dates lie inside the band and the
  neighbouring days outside, using the runtime's own date arithmetic;
* the child earnings ceiling the encoding applies, found by bisection:
  943,02 € (Mayotte 711,49 €);
* band robustness: each valid row is re-evaluated with other values inside one
  band at a time (band ends and extra probes). FR-PF: 4 140 evaluations (all
  rows), 0 label changes. FR-AF tables, every 25th row: FR-AF-1 53 089
  evaluations, FR-AF-2 55 944, FR-AF-3 90 322; 0 label changes whenever the
  children's birth order is kept. The only changes are 42 in FR-AF-2, all
  caused by reversing the order of two children in the same age band (see
  "Deviations").

For FR-AF-1, the 40 320 rows with an `absent` slot before a present one carry
the same label as every other row describing the same children list (0
conflicts).

## Deviations and points to know

1. **Rounded earnings ceiling.** `inputs.md` quotes the unrounded products of
   `(SMIC × 55 %) × 169`. The Catala 1.3.0 runtime rounds money to the cent
   after each multiplication, so at 2020-05-01 the encoding uses 943,02 €
   (5,58 € × 169) and 711,49 € for Mayotte (4,21 € × 169). FR-PF's
   `eq_plafond` representative is these values. It depends on residence, which
   `spec.json` records in an extra key `representative_by_residence`.
2. **Representatives that depend on other attributes.** The resource
   representatives at and between the household ceilings depend on n, the
   number of children with `droit_ouvert` (`plafond_I = 57 759 € + 5 775 € × n`,
   `plafond_II = 80 831 € + 5 775 € × n` for 2020). `spec.json` writes them as
   formulas (`plafond_I(n)`, midpoint); the oracle computes n from the encoding.
3. **Extra keys in `spec.json`.** Interval attributes carry an `intervals` key
   (exact predicate and first/last birth dates). Fixed inputs carry a `label`
   (the band they stand for) besides `value` and `why`. The FR-AF tables
   record their number of child slots as the fixed input `child_slots`.
4. **Output labels of the FR-AF tables are defined by this conversion.**
   `zero` comes from the encoding's amount. A positive amount gets the label of
   the statutory regime whose conditions hold (Mayotte, L755-12/D755-5 single
   child, or the D521-1 tier). FR-AF-3 labels the amount by its decomposition
   into base, majorations and forfaitaire, because with residence and
   resources fixed every positive amount there would be `general_t1`.
5. **FR-PF includes `prise_en_charge`, which `droit_ouvert` never reads**, as
   the protocol asked. The age thresholds 3 and 16 are not compared by the
   scope; they come from the epilogue's L131-1 derivation and serve the
   exclusions. The output is `droit_ouvert`; `conditions_hors_âge` reduces to the
   earnings test alone.
6. **Child earnings in the FR-AF tables have two bands.** "At the ceiling"
   behaves as "below" (`<=`). FR-PF keeps the three-way split.
7. **Same-band birth order (FR-AF-2).** Age bands do not fix which of two
   children in the same band is the elder. The tables use slot order (slot 1
   is one day older). In 42 of the sampled re-evaluations of FR-AF-2,
   reversing that order changes the label from `outre_mer_1_enfant` to `zero`:
   an L751-1 household where the only child with `droit_ouvert` has its share
   paid to the services sociaux, and a 16-19-year-old without `droit_ouvert`
   receives the majoration only when that child is not the eldest.
8. **Behaviour of the encoding reproduced as is** (FR-AF CONVERSION.md, A11):
   the allocation forfaitaire is paid for children past 20 without time limit;
   the majoration is paid to a non-eldest child aged 14 or more even without
   that child's own `droit_ouvert`; the D755-5 single-child majorations, which
   `inputs.md` marks as apparently unreachable, are reached when an L751-1
   household has one child with `droit_ouvert` and an elder child without it.
9. **Coverage limits.** No table has four children (the Mayotte fourth-child
   rate and official Test1 stay outside). Dates other than the 2020 period
   are outside every table, which leaves six official tests unmapped.
10. **Python.** The runtime needs Python 3.12 or later. All four ground-truth
    files are byte-identical on Python 3.12.3 and 3.13.16.

## Reproduce

```sh
cd paperC/specs/FR-AF-1      # or FR-PF, FR-AF-2, FR-AF-3
python3 oracle.py --check-official
python3 oracle.py --enumerate          # about 1-3 minutes on 4 cores for an FR-AF table
python3 oracle.py --self-check         # FR-AF tables: --self-check --sample 25
sha256sum -c SHA256SUMS
```
