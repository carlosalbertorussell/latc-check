# Inputs and thresholds of the Catala `allocations_familiales` program

Source: https://github.com/CatalaLang/catala-examples at commit `2694b17`. Files read:
`allocations_familiales/*.catala_fr` (prologue, epilogue, autres_codes, securite_sociale_L/R/D, decrets_divers, Allocations_familiales), `prologue_france/France.catala_fr`, `smic/Smic.catala_fr`, `base_mensuelle_allocations_familiales/Bmaf.catala_fr`.

Everything below is taken from those files. Points that are ambiguous or look inconsistent are marked **Unclear**.

Note: `Allocations_familiales.catala_fr` contains `> Usage de Prestations_familiales` (a separate module directory `prestations_familiales/` exists in the repo), yet `prologue.catala_fr` declares its own scope `PrestationsFamiliales`. This document describes the scope declared in `prologue.catala_fr`; the separate module was outside the reading list.

---

## 1. Scope `PrestationsFamiliales` (prologue.catala_fr)

### 1.1 Declaration

```catala
déclaration champ d'application PrestationsFamiliales:
  résultat droit_ouvert condition dépend de enfant contenu Enfant
  résultat conditions_hors_âge condition dépend de enfant contenu Enfant
  interne plafond_l512_3_2 contenu argent
  résultat âge_l512_3_2 contenu durée
  résultat régime_outre_mer_l751_1 condition
  entrée date_courante contenu date
  entrée résidence contenu France.Collectivité
  smic champ d'application Smic.Smic
```

| Input | Type |
|---|---|
| `date_courante` (entrée) | `date` |
| `résidence` (entrée) | `France.Collectivité` |
| `enfant` (argument of `droit_ouvert` and `conditions_hors_âge`) | `Enfant` |

Both scope inputs are forwarded to the sub-scope `smic` (`définition smic.résidence égal à résidence`, `définition smic.date_courante égal à date_courante`).

### 1.2 Structure `Enfant`

| Field | Type |
|---|---|
| `identifiant` | `entier` |
| `obligation_scolaire` | `SituationObligationScolaire` |
| `rémuneration_mensuelle` | `argent` |
| `date_de_naissance` | `date` |
| `prise_en_charge` | `PriseEnCharge` |
| `a_déjà_ouvert_droit_aux_allocations_familiales` | `booléen` |
| `bénéficie_titre_personnel_aide_personnelle_logement` | `booléen` |

(The field name is spelled `rémuneration_mensuelle`, with one accent, in the source.)

### 1.3 Enumerations

- **`France.Collectivité`** (9 values, France.catala_fr): `Guadeloupe`, `Guyane`, `Martinique`, `LaRéunion`, `SaintBarthélemy`, `SaintMartin`, `Métropole`, `SaintPierreEtMiquelon`, `Mayotte`.
- **`SituationObligationScolaire`** (3): `Avant`, `Pendant`, `Après`.
- **`PriseEnCharge`** (5): `GardeAlternéePartageAllocations`, `GardeAlternéeAllocataireUnique`, `EffectiveEtPermanente`, `ServicesSociauxAllocationVerséeÀLaFamille`, `ServicesSociauxAllocationVerséeAuxServicesSociaux`.

Other enumerations declared in the prologue, used by `AllocationsFamiliales`: `PriseEnCompte` (`Complète`, `Partagée`, `Zéro`) and `VersementAllocations` (`Normal`, `AllocationVerséeAuxServicesSociaux`).

### 1.4 Which `Enfant` fields the rules read

`droit_ouvert` (L512-3 1° and 2°, plus the L821-3 exception in autres_codes.catala_fr):

```catala
# L512-3 1°  (étiquette cas_base)
enfant.obligation_scolaire sous forme SituationObligationScolaire.Avant
ou enfant.obligation_scolaire sous forme SituationObligationScolaire.Pendant
# L512-3 2°  (étiquette cas_base)
enfant.obligation_scolaire sous forme SituationObligationScolaire.Après
et (enfant.rémuneration_mensuelle <= plafond_l512_3_2)
et (enfant.date_de_naissance + âge_l512_3_2 > date_courante)
# L821-3  (exception cas_base, conséquence non rempli)
enfant.bénéficie_titre_personnel_aide_personnelle_logement
```

`conditions_hors_âge` (L512-3 2°):

```catala
( enfant.obligation_scolaire sous forme SituationObligationScolaire.Avant
  ou enfant.obligation_scolaire sous forme SituationObligationScolaire.Pendant
  ou enfant.obligation_scolaire sous forme SituationObligationScolaire.Après )
et (enfant.rémuneration_mensuelle <= plafond_l512_3_2)
```

Fields read: `obligation_scolaire`, `rémuneration_mensuelle`, `date_de_naissance`, `bénéficie_titre_personnel_aide_personnelle_logement`.
Fields never read by these two rules: `identifiant`, `prise_en_charge`, `a_déjà_ouvert_droit_aux_allocations_familiales` (these are read in `AllocationsFamiliales`).

Observations:
- In `conditions_hors_âge` the disjunction over the three `obligation_scolaire` values is always true, so the condition reduces to the earnings test.
- The earnings test `rémuneration_mensuelle <= plafond_l512_3_2` applies only in the `Après` branch of `droit_ouvert`; a child `Avant`/`Pendant` qualifies whatever its earnings.
- The L821-3 exception (housing aid held personally, `exception cas_base ... conséquence non rempli`, autres_codes.catala_fr, Article L821-3) overrides both `cas_base` rules of `droit_ouvert`; it leaves `conditions_hors_âge` untouched. Confirmed with the generated Python: a `Pendant` child with the flag set gets `droit_ouvert = faux`.
- `régime_outre_mer_l751_1` depends only on `résidence`.

---

## 2. Scopes `AllocationsFamiliales` and `InterfaceAllocationsFamiliales`

### 2.1 `AllocationsFamiliales` inputs (prologue.catala_fr)

| Input (entrée) | Type |
|---|---|
| `personne_charge_effective_permanente_est_parent` | `condition` |
| `personne_charge_effective_permanente_remplit_titre_I` | `condition` |
| `ressources_ménage` | `argent` |
| `résidence` | `France.Collectivité` |
| `date_courante` | `date` |
| `enfants_à_charge` | `liste de Enfant` |
| `avait_enfant_à_charge_avant_1er_janvier_2012` | `condition` |

Forwarded to sub-scopes: `prestations_familiales.date_courante`, `prestations_familiales.résidence`, `bmaf.date_courante`. The sub-scope `version_avril_2008` (`AllocationFamilialesAvril2008`) has no inputs. `enfant_le_plus_âgé.enfants` is set to `enfants_à_charge` (epilogue).

Assertion on the household inputs (L521-2):

```catala
assertion
  personne_charge_effective_permanente_est_parent
  ou (
    (non personne_charge_effective_permanente_est_parent)
    et personne_charge_effective_permanente_remplit_titre_I
  )
```

Per-child fields read inside `AllocationsFamiliales`: `prise_en_charge` (L521-2: `prise_en_compte`, `versement`), `date_de_naissance` (majoration ages, forfaitaire, eldest child), `a_déjà_ouvert_droit_aux_allocations_familiales` (forfaitaire). The eldest-child check compares whole `Enfant` records (`enfant_le_plus_âgé.le_plus_âgé = enfant`), so every field participates in that equality.

### 2.2 `InterfaceAllocationsFamiliales` inputs (epilogue.catala_fr)

| Input (entrée) | Type | Mapped to `allocations_familiales.` |
|---|---|---|
| `i_date_courante` | `date` | `date_courante` |
| `i_enfants` | `liste de EnfantEntrée` | `enfants_à_charge` (via the transformation below) |
| `i_ressources_ménage` | `argent` | `ressources_ménage` |
| `i_résidence` | `France.Collectivité` | `résidence` |
| `i_personne_charge_effective_permanente_est_parent` | `condition` | `personne_charge_effective_permanente_est_parent` |
| `i_personne_charge_effective_permanente_remplit_titre_I` | `condition` | `personne_charge_effective_permanente_remplit_titre_I` |
| `i_avait_enfant_à_charge_avant_1er_janvier_2012` | `condition` | `avait_enfant_à_charge_avant_1er_janvier_2012` |

Output: `résultat i_montant_versé contenu argent` = `allocations_familiales.montant_versé`.

Structure `EnfantEntrée`:

| Field | Type |
|---|---|
| `d_identifiant` | `entier` |
| `d_rémuneration_mensuelle` | `argent` |
| `d_date_de_naissance` | `date` |
| `d_prise_en_charge` | `PriseEnCharge` |
| `d_a_déjà_ouvert_droit_aux_allocations_familiales` | `booléen` |
| `d_bénéficie_titre_personnel_aide_personnelle_logement` | `booléen` |

`EnfantEntrée` has no `obligation_scolaire` field; the interface derives it from date of birth under the heading "Code de l'éducation, Article L131-1" (compulsory schooling from age 3 to age 16):

```catala
-- obligation_scolaire:
  (
    si enfant.d_date_de_naissance + 3 an >= i_date_courante alors
      SituationObligationScolaire.Avant
    sinon
      (
        si enfant.d_date_de_naissance + 16 an >= i_date_courante alors
          SituationObligationScolaire.Pendant
        sinon SituationObligationScolaire.Après
      )
  )
```

All other fields are copied one-to-one (`d_x` to `x`). Boundary behaviour: on the exact 3rd birthday the child is still `Avant`; on the exact 16th birthday still `Pendant`; `Après` starts the day after the 16th birthday.

**Unclear:** the epilogue declares no `date arrondi` mode, so how `+ 3 an` / `+ 16 an` resolves for a birth on 29 February is left to Catala's default handling of date arithmetic. The same applies to every `date + n an` comparison in sections 1 and 3. Only the unused helper scopes in France.catala_fr (`VérificationÂgeInférieurOuÉgalÀ`, `VérificationÂgeSupérieurÀ`) declare `date arrondi supérieur`.

---

## 3. Statutory thresholds and the exact comparisons

### 3.1 Child eligibility (PrestationsFamiliales)

| Item | Value / expression | Heading |
|---|---|---|
| Age limit | `définition âge_l512_3_2 égal à 20 an` | Article R512-2 |
| Age comparison | `enfant.date_de_naissance + âge_l512_3_2 > date_courante` | Article L512-3 (2°) |
| Earnings ceiling (default) | `définition plafond_l512_3_2 égal à (smic.brut_horaire * 55%) * 169,0` | Article R512-2 |
| Earnings ceiling (overseas) | `exception définition plafond_l512_3_2 sous condition régime_outre_mer_l751_1 conséquence égal à (smic.brut_horaire * 55%) * 169,0` | Article R755-0-2 |
| Earnings comparison | `enfant.rémuneration_mensuelle <= plafond_l512_3_2` | Article L512-3 (2°) |

The R755-0-2 exception has the same formula as the default; the territorial difference comes entirely from `smic.brut_horaire`, which depends on `résidence` (section 3.8). Mayotte is outside `régime_outre_mer_l751_1`, so it uses the R512-2 default, still with the Mayotte SMIC.

### 3.2 Overseas regime set (Article L751-1)

```catala
règle régime_outre_mer_l751_1
sous condition
  (résidence = Guadeloupe) ou (résidence = Guyane) ou (résidence = Martinique)
  ou (résidence = LaRéunion) ou (résidence = SaintBarthélemy) ou (résidence = SaintMartin)
conséquence rempli
```

Six of the nine collectivités. `Métropole`, `SaintPierreEtMiquelon` and `Mayotte` are outside it. Mayotte has its own rules (3.6); Saint-Pierre-et-Miquelon receives no specific rule in these files and follows the metropolitan rules.

### 3.3 Number-of-children thresholds

| Rule | Exact expression | Heading |
|---|---|---|
| Base entitlement from the 2nd child | `nombre de enfants_à_charge_droit_ouvert_prestation_familiale >= 2` | Article L521-1 |
| Overseas: entitlement from 1 child (exception) | `prestations_familiales.régime_outre_mer_l751_1 et (nombre de enfants_à_charge_droit_ouvert_prestation_familiale >= 1)` | Article L755-12 |
| Overseas, exactly 1 child: no forfaitaire, no complément dégressif (exceptions, `non rempli`) | `prestations_familiales.régime_outre_mer_l751_1 et (nombre de enfants_à_charge_droit_ouvert_prestation_familiale = 1)` | Article L755-12 |
| Majoration for every child (including eldest) | `nombre de enfants_à_charge_droit_ouvert_prestation_familiale >= nombre_enfants_alinéa_2_l521_3`, with `nombre_enfants_alinéa_2_l521_3 égal à 3` | L521-3 (rule), R521-1 (value) |
| Forfaitaire minimum family size | `nombre de enfants_à_charge >= nombre_enfants_alinéa_2_l521_1`, with `nombre_enfants_alinéa_2_l521_1 égal à 3` | L521-1 (rule), D521-2 III (value) |
| Rate tiers: 2nd child / 3rd and later | `nombre de enfants_à_charge_droit_ouvert_prestation_familiale > 1` / `> 2` (multiplier `... - 2`) | Article D521-1 |
| Overseas single-child rate | `prestations_familiales.régime_outre_mer_l751_1 et nombre de enfants_à_charge_droit_ouvert_prestation_familiale = 1` | Article D755-5 |

`enfants_à_charge_droit_ouvert_prestation_familiale` is `liste de enfant parmi enfants_à_charge tel que prestations_familiales.droit_ouvert de enfant` (L512-3). Note that the forfaitaire count uses the raw list `enfants_à_charge`, while every other count uses the filtered list.

### 3.4 Age thresholds for majorations

| Rule | Exact expression | Heading |
|---|---|---|
| General age | `définition âge_minimum_alinéa_1_l521_3 de enfant égal à 14 an` | Article R521-1 |
| Old age (pre-2008 decree) | scope `AllocationFamilialesAvril2008`: `définition âge_minimum_alinéa_1_l521_3 égal à 16 an` | Article R521-1 (NOTA, décret 2008-409) |
| When the old age applies | `exception définition âge_minimum_alinéa_1_l521_3 de enfant sous condition (enfant.date_de_naissance + 11 an <= \|2008-04-30\|) conséquence égal à version_avril_2008.âge_minimum_alinéa_1_l521_3` | Article R521-1 |
| Majoration, eldest excluded | `(non (est_enfant_le_plus_âgé de enfant)) et (enfant.date_de_naissance + âge_minimum_alinéa_1_l521_3 de enfant <= date_courante)` | Article L521-3 al. 1 |
| Majoration, 3+ children (exception) | `(nombre de enfants_à_charge_droit_ouvert_prestation_familiale >= nombre_enfants_alinéa_2_l521_3) et (enfant.date_de_naissance + âge_minimum_alinéa_1_l521_3 de enfant <= date_courante)` | Article L521-3 al. 2 |
| Overseas single child, 11 to 16 | `enfant.date_de_naissance + 11 an <= date_courante et enfant.date_de_naissance + 16 an > date_courante` → `bmaf.montant * 3,69%` | Article D755-5 |
| Overseas single child, 16+ | `enfant.date_de_naissance + 16 an <= date_courante` → `bmaf.montant * 5,67%` | Article D755-5 |

The eldest child (`EnfantLePlusÂgé`, epilogue) is the one whose `date_de_naissance est minimum` among `enfants_à_charge`; an empty list yields a placeholder `Enfant` with `identifiant: -1` and `date_de_naissance: |2999-12-31|`.

**Unclear:** the two D755-5 majoration exceptions also require `droit_ouvert_majoration de enfant`. With a single child, that child is the eldest, and the 3-children exception cannot hold, so `droit_ouvert_majoration` appears to be false and these two rates appear unreachable as written.

### 3.5 Allocation forfaitaire (age reached)

The forfaitaire age is `prestations_familiales.âge_l512_3_2`, i.e. 20 ans from R512-2. No separate forfaitaire age is defined in L521-1, R521-1 or D521-2. The rule (Article L521-1, al. 2):

```catala
règle droit_ouvert_forfaitaire de enfant
sous condition
  (nombre de enfants_à_charge >= nombre_enfants_alinéa_2_l521_1)
  et (
    (enfant.date_de_naissance + prestations_familiales.âge_l512_3_2)
    - date_courante
    < 365 jour
  )
  et (enfant.a_déjà_ouvert_droit_aux_allocations_familiales)
  et (prestations_familiales.conditions_hors_âge de enfant)
conséquence rempli
```

Amounts (Article D521-2 I): `bmaf.montant * 20,234%` / `10,117%` / `5,059%` per child according to the resource tier (3.7).

**Unclear:** the source comment says the 365-day test limits the payment to one year. As written, `(birth + 20 an) - date_courante` is also below 365 days for any child already past 20 (negative duration) and for a child less than one year away from turning 20. The code comment and the expression do not obviously agree. Confirmed with the generated Python (Métropole, 2020-05-01, resources 30 000 €): children born 2010-01-01 and 2012-01-01 give 132,61 €; adding a third child born 1995-01-01 gives 216,46 €, the difference being the forfaitaire 20,234 % × BMAF 414,40 € = 83,85 € paid for the 25-year-old.

### 3.6 Mayotte-specific rules

These live in decrets_divers.catala_fr under "Décret n°2002-423 du 29 mars 2002 ... Article 7" and its "Annexe". No L755-x / D755-x article in these files mentions Mayotte. All of them are guarded by `sous condition résidence = Mayotte`.

- Entitlement from one child: `exception règle droit_ouvert_base sous condition (nombre de enfants_à_charge_droit_ouvert_prestation_familiale >= 1) conséquence rempli`.
- Base formula: `montant_initial_base_premier_enfant + montant_initial_base_deuxième_enfant + montant_initial_base_troisième_enfant_mayotte + montant_initial_base_quatrième_enfant_et_plus_mayotte`.
- Rates from 2021 onward (Article 7 defaults): 1st child `> 0` → 5,88%; 2nd `> 1` → 32%; 3rd `> 2` → 16%; 4th and later `> 3` → `(bmaf.montant * 4,63%) * (décimal de ((nombre ...) - 3))`.
- Yearly rates (Annexe), each guarded by `date_courante >= |YYYY-01-01| et date_courante <= |YYYY-12-31|`:

| Year | 1st child (only if `non avait_enfant_à_charge_avant_1er_janvier_2012`) | 2nd child | 3rd child |
|---|---|---|---|
| 2011 | 14,50% | 23,2% | 4,63% |
| 2012 | 13,93% | 23,79% | 5,39% |
| 2013 | 13,35% | 24,37% | 6,15% |
| 2014 | 12,78% | 24,96% | 6,90% |
| 2015 | 12,20% | 25,55% | 7,66% |
| 2016 | 11,63% | 26,13% | 8,42% |
| 2017 | 11,05% | 26,72% | 9,18% |
| 2018 | 9,76% | 28,04% | 10,89% |
| 2019 | 8,47% | 29,36% | 12,59% |
| 2020 | 7,17% | 30,68% | 14,30% |
| 2021 onward | 5,88% | 32% | 16% |

- Flat amount: `exception mayotte définition montant_initial_base_premier_enfant sous condition avait_enfant_à_charge_avant_1er_janvier_2012 conséquence égal à si nombre ... > 0 alors 57,28€ sinon 0 €` (no date bound).
- The Annexe table's column "familles ayant trois enfants à charge" (27,83% … 48%) is reproduced in prose and has no Catala counterpart.
- Mayotte overrides the base-amount components with `exception base` / `exception mayotte` labels, so its base rates do not vary with the resource tiers of D521-1. The age majorations, forfaitaire and complément dégressif for Mayotte fall back on the general rules.

Note on precedence: a Mayotte household with `avait_enfant_à_charge_avant_1er_janvier_2012` true gets the 57,28€ rule in every year, as an `exception mayotte` over the 5,88% rule. The yearly 1st-child rules require `non avait_enfant_à_charge_avant_1er_janvier_2012`, so they never overlap with the 57,28€ rule.

### 3.7 Household resource ceilings (Article D521-3 and decrets_divers)

Default values (Article D521-3, LEGIARTI000044809227), applied whenever no yearly exception matches:

```catala
définition plafond_I_d521_3 égal à
  55 950 € + 5 595 € * (décimal de (nombre de enfants_à_charge_droit_ouvert_prestation_familiale))
définition plafond_II_d521_3 égal à
  78 300 € + 5 595 € * (décimal de (nombre de enfants_à_charge_droit_ouvert_prestation_familiale))
```

Yearly exceptions (decrets_divers.catala_fr), each guarded by `date_courante >= |YYYY-01-01| et date_courante <= |YYYY-12-31|`:

| Year | Plafond I base | Plafond II base | Per child | Source heading |
|---|---|---|---|---|
| 2018 | 56 286 € | 78 770 € | 5 628 € | Circulaire DSS/SD2B/2017/352 du 22 décembre 2017 |
| 2019 | 56 849 € | 79 558 € | 5 684 € | Instruction DSS/SD2B/2018/279 du 17 décembre 2018 |
| 2020 | 57 759 € | 80 831 € | 5 775 € | Instruction DSS/SD2B/2019/261 du 18 décembre 2019 |
| 2021 | 58 279 € | 81 558 € | 5 827 € | Arrêté du 14 décembre 2020, Article 1 |
| other dates (2022 onward) | 55 950 € | 78 300 € | 5 595 € | Article D521-3 |

**Unclear:** the D521-3 defaults are lower than the 2021 values, and the files contain no yearly values for 2022 or later, so dates from 2022 onward fall back on 55 950 € / 78 300 €.

Comparisons against `ressources_ménage` (Articles D521-1 and D521-2):

- Tier 1: `ressources_ménage <= plafond_I_d521_3` → base 32% (2nd child), 41% (3rd and later), majoration 16%, forfaitaire 20,234%.
- Tier 2: `(ressources_ménage > plafond_I_d521_3) et (ressources_ménage <= plafond_II_d521_3)` → 16%, 20,5%, majoration 8%, forfaitaire 10,117%.
- Tier 3: `ressources_ménage > plafond_II_d521_3` → 8%, 10,25%, majoration 4%, forfaitaire 5,059%.
- Complément dégressif (D521-1 II), for `allocation` = `montant_versé_base + montant_versé_majoration`:
  `(ressources_ménage > plafond_I_d521_3) et (ressources_ménage <= plafond_I_d521_3 + allocation * 12,0)` → `(plafond_I_d521_3 + allocation * 12,0 - ressources_ménage) * (1,0 / 12,0)`; the same with `plafond_II_d521_3`; otherwise `0 €`.
- Complément for forfaitaire (D521-2 II): the same shape with `montant_versé_forfaitaire * 12,0`.
- `règle droit_ouvert_complément rempli` (epilogue), except overseas with exactly one child (L755-12).

### 3.8 SMIC brut horaire (smic/Smic.catala_fr)

"Others" = `Métropole`, `Guadeloupe`, `Guyane`, `Martinique`, `LaRéunion`, `SaintBarthélemy`, `SaintMartin`, `SaintPierreEtMiquelon`.

| Period (as coded) | Others | Mayotte | Heading |
|---|---|---|---|
| `>= 2019-01-01` and `<= 2019-12-31` | 10,03 € | 7,57 € | Décret n° 2018-1173, Article 1 |
| `>= 2020-01-01` and `<= 2020-12-31` | 10,15 € | 7,66 € | Décret n° 2019-1387, Article 1 |
| `>= 2021-01-01` and `<= 2021-12-31` | 10,25 € | 7,74 € | Décret n° 2020-1598, Article 1 |
| `>= 2022-01-01` and `<= 2022-04-30` | 10,57 € | 7,98 € | Décret n° 2021-1741, Article 1 |
| `>= 2022-05-01` and `<= 2022-07-31` | 10,85 € | 8,19 € | Arrêté du 19 avril 2022, Article 2 |
| `>= 2022-08-01` and `<= 2022-12-31` | 11,07 € | 8,35 € | Arrêté du 29 juillet 2022, Article 2 |
| `>= 2023-01-01` and `< 2023-05-01` | 11,27 € | 8,51 € | Décret n° 2022-1608, Article 1 |
| `>= 2023-05-01` and `< 2024-01-01` | 11,52 € | 8,70 € | Arrêté du 26 avril 2023, Article 2 |
| `>= 2024-01-01` and `< 2024-11-01` | 11,65 € | 8,80 € | Décret n° 2023-1216, Article 1 |
| Others: `>= 2024-11-01` (open-ended) / Mayotte: `>= 2024-01-01` (open-ended) | 11,88 € | 8,98 € | Décret n° 2024-951, Article 1 |

**Unclear (probable bug):** the last Mayotte rule is guarded by `date_courante >= |2024-01-01|` (the "others" rule uses `|2024-11-01|`). For Mayotte between 2024-01-01 and 2024-10-31 both the 8,80 € and the 8,98 € definitions apply, with no exception between them, which Catala reports as a conflict at run time. Confirmed with the generated Python: `prestations_familiales` for `Mayotte` on 2024-06-01 raises `Conflict` ("two or more concurring valid computations", Smic.catala_fr lines 443 and 489); on 2024-12-01 it runs.

Resulting monthly earnings ceiling `(brut_horaire * 55%) * 169,0`, e.g. 2019 others: 10,03 × 0,55 × 169 = 932,29 € (before Catala's money rounding); Mayotte 2019: 7,57 × 0,55 × 169 = 703,63 €.

### 3.9 BMAF (base_mensuelle_allocations_familiales/Bmaf.catala_fr)

Single value for all territories (the scope has no `résidence` input).

| Period (as coded) | `montant` | Heading |
|---|---|---|
| `>= 2019-04-01` and `< 2020-04-01` | 413,16 € | Instruction DSS/SD2B/2019/65 du 25 mars 2019 |
| `>= 2020-04-01` and `< 2021-04-01` | 414,4 € | Instruction DSS/SD2B/2020/33 du 18 février 2020 |
| `>= 2021-04-01` and `< 2022-04-01` | 414,81 € | Instruction DSS/2B/2021/65 du 19 mars 2021 |
| `>= 2022-04-01` and `< 2023-04-01` | 422,28 € | Instruction DSS/2B/2022/82 du 28 mars 2022 |
| `>= 2023-04-01` (open-ended) | 445,93 € | Instruction DSS/2B/2023/41 du 24 mars 2023 |

### 3.10 Date-of-validity assertions

- Smic: `assertion date_courante >= |2019-01-01|`.
- Bmaf: `assertion date_courante >= |2019-04-01|`.
- No assertion in `PrestationsFamiliales`, `AllocationsFamiliales` or `InterfaceAllocationsFamiliales` itself. Because `AllocationsFamiliales` calls `bmaf` and (through `prestations_familiales`) `smic`, the effective lower bound for a full computation is 2019-04-01. The Mayotte yearly rates for 2011–2018 and the ceilings for 2018 therefore sit below that bound and cannot be reached through the full computation.
- There is no upper bound: SMIC and BMAF have open-ended last periods, and the D521-3 defaults cover dates after 2021.
