# Paper C verification, step 3: audit of the conversion (FR-APL-1..5, US-121-1..2)

Auditor scope: `paperC/specs/FR-APL/<ID>/{spec.json,CONVERSION.md}` and
`paperC/specs/US-121/<ID>/{spec.json,CONVERSION.md}` checked against the Catala sources of
CatalaLang/catala-examples at commit `2694b17ddd7c2246e207e8f077d586349ee5abea` (local clone,
`git log -1` confirmed the commit). Nothing under `paperC/harness/` and no `paperC/results/` of a
`paperc-run-*` branch was read. The only other repository files read were
`paperC/catala_more/probes/probe_b3*` and the bundled Catala Python runtime
(`paperC/catala_more/runtime/catala/catala_runtime.py`) to confirm the duration-comparison rule.

Abbreviations (all paths relative to the catala-examples root):
`PRO` = `aides_logement/prologue.catala_fr`, `LEG` = `aides_logement/code_construction_legislatif.catala_fr`,
`REG` = `aides_logement/code_construction_reglementaire.catala_fr`, `ARR` = `aides_logement/arrete_2019-09-27.catala_fr`,
`ARCH` = `aides_logement/archives.catala_fr`, `FRA` = `prologue_france/France.catala_fr`, `SMIC` = `smic/Smic.catala_fr`,
`TAPL` = `aides_logement/tests/tests_eligibilite_apl.catala_fr`, `S121` = `us_tax_code/section_121.catala_en`,
`T121` = `us_tax_code/tests/test_section_121.catala_en`.

Checks: (a) declared values vs Catala source (enum constructors, cut points vs comparisons, bool
mapping); (b) representatives inside their label; (c) cited file:line contains what is claimed;
(d) statute article cited is the right one.

---

## FR-APL-1 (date x territory x nationality)

| item | check | verdict | evidence |
|---|---|---|---|
| `date_courante` | (a) cuts | OK | 2019-01-01: SMIC has no `brut_horaire` rule before 2019 (first rules `SMIC:37`, `59`; assertion `SMIC:18`). 2019-09-01: `personnes_à_charge_prises_en_compte` defined only from 2019-09-01 (`ARCH:11-15`), then `REG:1129-1133`; counted at `PRO:342-343`. 2021-01-01: SPM exception `LEG:1333-1339`. 2024-01-01/2024-11-01: Mayotte SMIC 8,80 € on [2024-01-01, 2024-11-01) (`SMIC:434-443`) overlaps 8,98 € from 2024-01-01 (`SMIC:481-489`). Other compared dates (2019-10-01 `ARR:6071`, 2021-05-01 `REG:6213`, 2023-04-05 `REG:6003`, 2023-09-01) are read only for home buyers / foyers / dependants and are left to the band sweep, which the record documents. |
| `date_courante` | (b) reps | OK | 2018-06-01, 2019-05-01, 2020-03-10, 2022-06-01, 2024-06-01, 2025-06-01 each lie in their label. |
| `date_courante` | (c) citations | OK | `PRO:378-381` is the scope declaration with `date_courante`; every cut-point citation opens on the claimed rule. |
| `date_courante` | (d) statute | MINOR | L860-3 I as quoted (`LEG:1325-1328`) states no date; the 2021-01-01 start comes from the encoding (`LEG:1337`), while the record writes "L860-3 I: no APL in SPM from 2021-01-01". |
| `residence` | (a) enum | OK | `FRA:9-18`: 9 constructors (Guadeloupe, Guyane, Martinique, LaRéunion, SaintBarthélemy, SaintMartin, Métropole, SaintPierreEtMiquelon, Mayotte); all 9 present, none extra. |
| `residence` | (b)/(c) | MINOR | Representatives are the exact constructors. CONVERSION.md says "all nine constructors in declared order"; the spec lists Metropole first, the source declares it seventh (`FRA:16`). |
| `nationalite_demandeur` | (a) enum | OK | `Nationalité` = `Française` or `Étrangère` with `ConditionsÉtrangers` of two booleans (`PRO:237-244`); 1 + 2x2 = 5 labels, exhaustive. Read at `LEG:130-136` (L822-2 I) and `LEG:1389-1400` (L861-5 1°, Mayotte). |
| `nationalite_demandeur` | (c) citation | MINOR | Cited `PRO:228-247`; the struct `Demandeur` is 228-235, `ConditionsÉtrangers` 237-240, the enum 242-244; 245-247 are an unrelated comment on zones. |
| `nationalite_demandeur` | (d) statute | OK | L822-2 I quoted at `LEG:119-127`, L861-5 1° at `LEG:1378-1386`. |
| output `eligibilite_apl` | values/source | MINOR | `PRO:391` declares `résultat éligibilité condition` (OK). Rule cited `LEG:631-645`; the rule runs 631-646 (`conséquence rempli` at 646). Exception `LEG:1333-1339` OK. |
| exclusions | none | OK | Rationale for not excluding (foreigner with Mayotte art. 4 condition elsewhere; dates before the encoding) is sound. |
| fixed inputs | Exemple1 | MINOR | Matches `TAPL:16-107` field by field (checked all Ménage/Logement/Location/Demandeur fields). The value text lists `date_courante` and `résidence Métropole` and `Française`, which are attributes of this table, under the heading "every field that is not an attribute". |
| notes: REJECTED rows | spot check | OK | NoValue at `SMIC:13` (no rule before 2019) and at `PRO:343` (no `personnes_à_charge_prises_en_compte` before 2019-09-01) and Conflict at `SMIC:443`/`489` are all consistent with the source. |
| CONVERSION §8 claims | spot check | OK | French applicant in Mayotte → `faux` (`LEG:1398`); DROM comment at `REG:5926-5927`. |

**FR-APL-1: PASS** (only MINOR items).

---

## FR-APL-2 (household size x floor area)

| item | check | verdict | evidence |
|---|---|---|---|
| `residence` | (a)-(d) | OK / MINOR | Same as FR-APL-1 (all 9 constructors; "declared order" claim in CONVERSION.md table header is inaccurate, MINOR). |
| `nationalite_demandeur` | (a)-(d) | OK / MINOR | Same as FR-APL-1 (`PRO:228-247` overshoots, MINOR). |
| `situation_familiale` | (a) enum | OK | `LEG:107-117`: Célibataire, Mariés (contenu date), Pacsés, Concubins, CélibataireSéparéDeFait, ConcubinageDontSéparéDeFait; all 6 present. Adult counts 1/2/2/2/1/2 at `REG:1018-1024`, base areas 9/16 at `REG:1034-1040`, Mayotte 9/13 at `REG:5621-5627`. |
| `situation_familiale` | (b)/(c)/(d) | OK | Mariés rep. carries Exemple1's date. R822-25 quoted `REG:1005-1012`; R861-5 3° quoted `REG:5579-5611` ("Pour leur application à Mayotte"). |
| `personnes_a_charge` | (a) values | MINOR | List length enters only through `nombre de ménage.personnes_à_charge` (`REG:1027`, `1044`, `5631`); 0..3 is a sampled sub-domain (any length is possible). The restriction is stated only indirectly (caps "out of reach with these sizes"). |
| `personnes_a_charge` | (b)/(c) | OK | First k children of Exemple1 (`TAPL:27-65`); cited lines contain the count. `PRO:217-226` is `Ménage`. |
| `autres_occupants` | (a) values | MINOR | Integer field `PRO:221`; 0..1 is a sampled sub-domain, same remark as above. Used at `REG:1026`, `1043`, `5630`. |
| `surface_m_carres` | (a) cuts | OK | Recomputed independently. Minima: non-Mayotte single 9+9n, couple 16+9n; Mayotte single 9+9n, couple 13+9n; R844-4 9 (1 person) / 16 (more) (`REG:5537`); n = 0..4. Union = {9,13,16,18,22,25,27,31,34,36,40,43,45,49,52} = the 15 cut points; comparisons are `>=` (`REG:1055-1056`, `5642-5643`, `5536-5537`), so lower bounds belong to the upper band. Caps (70 m2 at >= 8 persons `REG:1049-1052`; 54 m2 at >= 9 persons `REG:5636-5639`) unreachable with <= 6 persons. |
| `surface_m_carres` | (b) reps | OK | 8 in [0,9); each other rep is its band's lower bound. Field is `entier` (`PRO:170`). |
| `surface_m_carres` | (c) citations | OK | `PRO:163-171` (Logement), `REG:1029-1058`, `REG:5531-5545`, `REG:5614-5645` all contain the comparisons. |
| `personnes_agees_handicapees_r844_4` | (a)/(c)/(d) | OK | `PRO:225`; read at `REG:5535`, `5543`; R844-4 quoted `REG:5515-5528`. |
| output | values/source | MINOR | As FR-APL-1 (`LEG:631-645` vs 631-646). |
| exclusions | none | OK | Not excluding R844-4 households of > 2 persons is right: R844-4 itself decides that case (`REG:5527-5528`, `5540-5545`). |
| fixed inputs | Exemple1 | MINOR | Same boilerplate as FR-APL-1; lists Mariés, 1 other occupant, 80 m2, "not R844-4", which are attributes here. |
| notes: REJECTED (Conflict at `REG:5645`) | spot check | OK | Mayotte rule `exception base` (`REG:5615`) and R844-4 `étiquette r_844_4 exception base` (`REG:5532`) are sibling exceptions; both fire when both minima are met → conflict. |
| CONVERSION §8 claims | spot check | OK | Single + 1 person needs 18 m2 in code vs 16 m2 in R822-25 text (`REG:1009-1010`); Mayotte text "six mètres carrés" (`REG:5609`) vs code `* 9` (`REG:5633`). Both confirmed. |

**FR-APL-2: PASS** (only MINOR items).

---

## FR-APL-3 (tenants and sub-tenants)

| item | check | verdict | evidence |
|---|---|---|---|
| `mode_occupation` | (a) enum | OK | `ModeOccupation` (`PRO:143-149`) has 5 constructors; this table takes Locataire and SousLocataire, the other three are covered by FR-APL-4 (RésidentLogementFoyer) and FR-APL-5 (Accession, LocationAccession). Split is documented. |
| `mode_occupation` | (c)/(d) | OK | `LEG:146-161` (L822-2 II, SousLocataire → vrai at 156), `LEG:171-222` (L822-3, Locataire only at 189), `LEG:689-706` (L831-1 2°, Locataire only). |
| `bailleur` | (a) enum | OK | `TypeBailleur` (`PRO:23-27`): BailleurSocial(ConventionBailleurSocial), BailleurPrivéAvecConventionnementSocial(ConventionANHA), BailleurPrivé; 2+2+1 = 5 labels on the convention booleans. RLS amount fixed at 0 €; it is read only in amount rules (`REG:1515`, `1614`). |
| `bailleur` | (c) citation | OK | `PRO:16-38` covers both convention structs, the enum and `Location`. Read at `LEG:696-702`. |
| `part_propriete_famille` / `part_usufruit_famille` | (a) cut | OK | `ParentOuAutre` (`PRO:151-153`); share compared `< seuil` (`LEG:206-216`), seuil = 10 % (`REG:105-106`). Labels Autre / [0,10 %) / >= 10 % match. |
| same | (b) reps | OK | 0,05 < 0,1; 0,1 is not < 0,1, so it lies in `famille_10pc_ou_plus`. |
| same | (d) statute | OK | L822-3 quoted `LEG:163-169`, `194-197`; R822-1 quoted `REG:96-101`. The record's note on the "ensemble de ces parts" sentence (`REG:100-101`) not being encoded is accurate. |
| `loue_ou_sous_loue_a_des_tiers` | (a) enum + cut | OK | `LouéOuSousLouéÀDesTiers` = Non / Oui(PersonneSousLocation{date, conforme_l442_1}) (`PRO:155-161`); age test `date_naissance + 30 an > date_courante` (`FRA:38`) used at `LEG:246-251`, so cut at 30th birthday; 1 + 2x2 = 5 labels. |
| same | (b) reps | OK | Born 2000-01-01 (20 at 2020-03-10) and 1980-01-01 (40). |
| same | (c)/(d) | OK | `LEG:232-254` contains the rule; L822-4 quoted `LEG:224-230`. |
| `logement_decent_l89_462` | (a)/(c) | OK | `PRO:169`; `LEG:382-385` (L822-9). |
| `residence_principale` | (a)/(c) | OK | `PRO:164`; `LEG:42-47` (L821-2). |
| `condition_rattache_foyer_fiscal_parent_ifi` | (a)/(c) | OK | `PRO:223`; `LEG:368-371` (L822-8). |
| output | values/source | MINOR | As FR-APL-1. |
| exclusions | none | OK | Candidates discussed are rightly kept. |
| fixed inputs | Exemple1 | MINOR | Boilerplate lists Locataire/BailleurSocial conventionné, résidence principale, décent, propriétaire/usufruit Autre, not let, no IFI, which are attributes here. |
| notes: SousLocataire never eligible | spot check | OK | All `condition_logement_bailleur` rules (`LEG:669`, `691`, `738`, `756`, `1482`, `REG:3744`, `3804`, `6012`) match only Locataire, RésidentLogementFoyer, Accession or LocationAccession. |

**FR-APL-3: PASS** (only MINOR items).

---

## FR-APL-4 (logement-foyer)

| item | check | verdict | evidence |
|---|---|---|---|
| `residence` | (a)-(d) | OK | All 9 constructors. |
| `date_courante` | (a) cuts | OK | 2021-01-01 (`LEG:1337`), 2023-04-05 (`REG:6003`), 2024-01-01 / 2024-11-01 (`SMIC:437-438`, `484`). Domain start 2019-09-01 justified by FR-APL-1. |
| `date_courante` | (b)/(c) | OK | Reps inside labels; cited lines contain the comparisons. |
| `type_logement_foyer` | (a) enum | OK | `TypeLogementFoyer` (`REG:3732-3736`): 4 constructors, all present. Read at `REG:3748` (Autre → faux) and `REG:6016` (FJT, DROM, from 2023-04-05). |
| `type_logement_foyer` | (d) statute | OK | R832-20 quoted `REG:3712-3727`; R861-20 1° (`REG:5988-5993`) is the article behind `REG:5995-6019`. |
| `conventionne_livre_III_titre_V_chap_III` | (a)/(c) | OK | `PRO:121`; read `LEG:741-742` (L831-1 5°). |
| `remplit_conditions_r832_21` | (a)/(c) | OK | `PRO:120`; read `REG:3807-3808`. |
| `conventionne_selon_regles_drom` | (a)/(c)/(d) | OK | `PRO:122`; read `LEG:1484-1486` under the five-DROM condition `LEG:1471-1480`; L861-5-1 quoted `LEG:1462-1468`. |
| output | values/source | MINOR | As FR-APL-1. |
| exclusion `fjt_type_without_l353_2_convention` | predicate vs description | OK | Predicate expresses exactly "type FJT and not conventioned under livre III titre V ch. III". |
| exclusion `fjt_type_without_l353_2_convention` | legal justification | MINOR | R832-20 3° (`REG:3725-3727`) describes foyers "ayant fait l'objet d'une convention ... signée avant le 1er janvier 1995" (past fact), while the boolean is read at `LEG:741-742` as a convention currently in force ("font l'objet des conventions", `LEG:733`). A pre-1995 L353-2 convention that has since ended is legally conceivable, so the claim "cannot be unconventioned" rests on an unstated assumption that the convention is still running. L353-2 does sit in livre III, titre V, chapitre III. |
| exclusion `drom_convention_outside_drom` | predicate / justification | OK | Predicate matches the description; L861-5-1 creates that convention only for the five DROM (`LEG:1464-1468`), and the code reads the boolean only there (`LEG:1471-1480`). |
| fixed input `demandeur.nationalité` | value/why | OK | Étrangère{vrai, vrai} passes `LEG:135` and `LEG:1400`. |
| fixed input `logement.mode_occupation` | value/why | OK | `logement_foyer_jeunes_travailleurs`, `date_conventionnement`, `construit_application_loi_1957_12_III`, `redevance`, `catégorie_équivalence_loyer_d842_16` are read only by amount scopes (`REG:3966-3975`, `PRO:937-1041`) or the AL scope (`REG:5014-5018`). |
| fixed input "every other ménage and demandeur field" | value text | MINOR | Boilerplate says "Locataire of a BailleurSocial conventionné" and "Française", both overridden by the two preceding fixed inputs; the text contradicts them as written. |
| CONVERSION §8 claim (DROM: livre III route kept) | spot check | OK | Three rules share label `logement_foyer` (`LEG:737`, `REG:3803`, `LEG:1481`); L861-5-1 "est ainsi rédigé" (`LEG:1465`). |

**FR-APL-4: PASS** (only MINOR items; the FJT exclusion rationale should state its assumption).

---

## FR-APL-5 (home buyers)

| item | check | verdict | evidence |
|---|---|---|---|
| `mode_occupation` | (a) enum | OK | Accession and LocationAccession of `ModeOccupation` (`PRO:146-149`); rest covered by FR-APL-3/4. |
| `mode_occupation` | (c) | OK | `LEG:147-160`, `658-676`, `754-763`, `771-815` contain the claimed rules. |
| `type_pret` | (a) enum | OK | `TypePrêt` (`PRO:44-49`): D331_32, D331_63_64, D331_59_8, D331_76_1, Autre; all 5. Read `REG:3070-3071`, `3108-3109`. |
| `type_pret` | (d) | OK | R832-5 quoted `REG:3055-3062`, R832-7 quoted `REG:3098-3100`. |
| `titulaire_pret` | (a)/(c) | OK | `TitulairePrêt` (`PRO:51-53`), both constructors; read `REG:3068`, `3106`. |
| `date_signature_pret` | (a) cuts | OK | Comparisons `>= 2017-12-31` (`LEG:781`, `783`), `>= 2018-01-01` and `< 2020-01-01` (`LEG:804-805`, `809-810`). Four labels incl. the single day 2017-12-31 are exactly the induced partition. |
| `date_signature_pret` | (b) reps | OK | 2015-06-01, 2017-12-31, 2018-06-01, 2020-01-15. |
| `anciennete_logement` | (a) enum | OK | `NeufOuAncien` with `AmélioréParOccupant` (`PRO:87-93`): 1 + 2 = 3 labels; eligibility only tests `sous forme Ancien` (`LEG:806`, `811`). |
| `zone` | (a)/(c) | OK | `ZoneDHabitation` (`PRO:258-261`), 3 constructors; read `ARR:6074`. |
| `date_courante` | (a)/(c) | OK | Only eligibility comparison in range: `ARR:6071` (>= 2019-10-01). 2021-05-01 (`REG:6209-6213`) is an entry-into-force date passed to the common scope; the record leaves it to the sweep. |
| `residence_principale` | (a)/(c) | OK | `PRO:164`; `LEG:42-46`, and `LEG:154-155` for Accession. |
| output | values/source | MINOR | As FR-APL-1. |
| exclusion `loan_signed_after_decision_date` | predicate vs description | OK | Every date >= 2020-01-01 is after every date in 2019-09-01..2019-09-30. |
| exclusion `loan_signed_after_decision_date` | legal justification / citation | MINOR | Justified (the APL presupposes an existing loan). The citation `LEG:648-657` starts on a blank line (heading at 649); R832-5 "titulaire et supporte les charges correspondantes" (`REG:3055-3056`) would be the more direct reference. |
| fixed input Propriétaire record | value/why | OK | Non-attribute fields are read by amount rules (`REG:1569-1677`, `3471`, `3692`) or the AL scope (`LEG:1688`). |
| fixed input "every other field" | value text | MINOR | Boilerplate says "Locataire of a BailleurSocial", "Zone1", "résidence principale", which are attributes or overridden here. |
| notes: LocationAccession never eligible | spot check | OK | `caractéristiques_prêt_l831_1_6` declared `PRO:387`, used `LEG:760`, no rule anywhere (grep). |
| CONVERSION §8 (2017-12-31 off by one; variable name inverted) | spot check | OK | L831-2 "signé après le 31 décembre 2017" (`LEG:768`) vs `>= |2017-12-31|` (`LEG:781`); art. 49 "communes auxquelles s'applique la dérogation" (`ARR:6066-6067`). |

**FR-APL-5: PASS** (only MINOR items).

---

## US-121-1 (Section121SinglePerson.requirements_met)

| item | check | verdict | evidence |
|---|---|---|---|
| `ownership_days_in_5_years` | (a) cut | OK | Aggregation `S121:179-191`; compared `>= 730 day` at `S121:197`. Two labels = two sides. |
| same | (b) reps | OK | 2020-01-01..2021-01-01 = 366 days; 2017-01-01..2021-01-01 = 1,461 days (begin + 5 y = 2022-01-01 >= sale, so counted in full, `S121:183-184`). |
| same | (c)/(d) | OK | `S121:36` input; `S121:193` cites Reg. 1.121-1(c)(1) (2 years = 730 days); §121(a) quoted `S121:164-167`. |
| `use_days_in_5_years` | (a)-(d) | OK | `S121:38-39`; `S121:200-205`. |
| `other_section_121a_sale` | (a) enum | OK | `OtherSection121aSale` (`S121:26-29`): None, or MostRecent with a date. Three labels cover None plus the two sides of `<= 2 year`; the same-day earlier sale (0 days, comparable without error) is left outside every label and documented. |
| same | (b) reps | OK | 2020-01-01 (366 days before) and 2018-06-01 (more than 2 years before). |
| same | (c)/(d) | OK | `S121:48`, `S121:371-377`; §121(b)(3) quoted `S121:366-368`. |
| output `requirements_met` | values/source | OK | `S121:32`, rule `S121:207-209`. |
| exclusions | none | OK | |
| fixed `date_of_sale_or_exchange`, `gain` | source | OK | `T121:19`, `T121:21`. |
| fixed context vars | | OK | Tests do not redefine `gain_cap` / `section_121_b_3_applies`. |
| notes: REJECTED via `S121:376` | spot check | OK | Date minus date yields a day duration; the runtime's `Duration.compare` raises "ambiguous comparison between durations in different units" unless both sides are in months/years or both in days (`paperC/catala_more/runtime/catala/catala_runtime.py:729-737`). 0 days vs 2 years passes (both have days = 0), matching the record's same-day finding. Interpreter probe output agrees (`paperC/catala_more/probes/probe_b3_output.txt`). |
| official tests mapping | spot check | OK | Test3 use 2015-01-01..2017-01-02: straddles the mark, counts 2022-01-02 − 2021-01-01 = 366 days; Test4: 366 + 365 = 731. |

**US-121-1: PASS.**

---

## US-121-2 (Section121TwoPersons.income_excluded_from_gross_income)

| item | check | verdict | evidence |
|---|---|---|---|
| `return_type` | (a) enum | OK | `ReturnType` (`S121:65-68`): 3 constructors, all present; person1/person2 built at `S121:95-105`. |
| `return_type` | (b) rep `surviving_spouse` | OK | DeadSpouseInfo fields match `S121:60-63`; death 2020-06-01. |
| `return_type` | (d) | OK | §121(b)(2) `S121:257-322`, (b)(4) `S121:392-396`. |
| person1/person2 ownership, use | (a)-(c) | OK | As US-121-1; `PersonalData` `S121:50-54` (`50-57` for person 2 overshoots into `JointReturn`, harmless). |
| person1/person2 `other_section_121a_sale` | (a)-(c) | OK | As US-121-1; `S121:54`, `S121:371-383`. |
| `gain` | (a) cuts | OK | Compared `>= gain_cap` (`S121:251`), caps $250,000 (`S121:236`, `248`) and $500,000 (`S121:309-313`). Labels (0,250k), [250k,500k), [500k,∞); $0 omitted with a stated reason. |
| `gain` | (b) reps | OK | $200,000, $350,000, $600,000. |
| output `excluded_gain` | values/source | OK | `S121:84-85`, `219-224`, `250-254`. Recomputed the label counts from the rules (single 1/2/0/9, surviving 1/2/0/9, joint 10/8/3/27 for entire/250k/500k/none) = 12/12/3/45 as recorded. |
| exclusion `person2_differs_on_single_return`, `single` part | predicate / justification | OK | Predicate lists all 10 unequal label pairs over 3 attributes (2+2+6); on `SingleReturn` both persons read the same `PersonalData` (`S121:97`, `103`). 2 x 396 = 792 rows checks out. |
| exclusion `person2_differs_on_single_return`, `surviving_spouse` part | justification | **DISAGREE** | The spec's own representative builds `surviving_spouse` with `death_spouse_info_at_time_of_death: (person 2)`, so for that return type the person-2 labels describe the deceased spouse, a real second person (`S121:60-63`, used at `S121:420`). A survivor whose deceased spouse had a different ownership/use history describes a valid return under §121(b)(4) (`S121:392-396`). The description "there is one taxpayer ... describes no return" is therefore false for these 396 rows. The scope used here ignores `death_spouse_info_at_time_of_death` (it takes person 2 from `return`, `S121:105`), so outputs of kept rows are unaffected; the defect is an unjustified exclusion and an inconsistent mapping. |
| exclusion | (d) statute | MINOR | Cites "26 U.S.C. 121(b)(1)"; (b)(1) is the $250,000 limitation and says nothing on who the taxpayer is on a single return. |
| fixed `date_of_sale_or_exchange`, `return_date` | source | OK | `T121:19-20`; `return_date` is only passed through (`S121:81`, `146-147`), never compared. |
| fixed `date_of_spouse_death` | why | OK | Read only in `Section121TwoPasses` (`S121:403-409`). Cited range `398-431` correct. |
| fixed context vars | | OK | |
| notes: (b)(2)(B)/(b)(4) absent from TwoPersons | spot check | OK | They live only in `Section121TwoPasses` (`S121:324-361`, `398-431`); `PeriodMerge` returns `[]` (`S121:21`); joint failing (b)(2)(A) gets `section121Person1.gain_cap` = $250,000 (`S121:248`). |
| notes: REJECTED | spot check | OK | Same `S121:376` mechanism as US-121-1; 384 joint + 24 single + 24 surviving rows have a non-`none` sale and are not excluded. |

**US-121-2: FAIL** (one substantive disagreement: the surviving-spouse half of the
exclusion is unjustified as written; ground-truth outputs of the kept rows are not affected).

---

## Disagreements

### Substantive (DISAGREE)

1. **US-121-2, exclusion `person2_differs_on_single_return` for `surviving_spouse`.** The
   representative of `surviving_spouse` maps person 2 to `death_spouse_info_at_time_of_death`
   (spec.json and CONVERSION.md §2), so a row whose person-2 labels differ from person 1's
   describes a surviving spouse whose late spouse had a different history: a legally valid
   return (26 U.S.C. 121(b)(4), quoted at `S121:392-396`; `DeadSpouseInfo` at `S121:60-63`).
   The exclusion's description ("there is one taxpayer ... describes no return") holds for
   `single` and is false for `surviving_spouse`, so 396 of the 792 excluded rows are excluded on
   a wrong ground. Since `Section121TwoPersons` never reads the deceased spouse's data
   (`S121:105`), the kept rows' outputs stay right. Fix: either keep these rows (they would
   carry the same outputs as the matching rows) or change the representative so that person 2
   is ignored for `surviving_spouse` and state that the deceased spouse's data are fixed, with a
   rationale that is a design choice of the table and not a legal impossibility.

### Minor (MINOR)

2. **All FR-APL tables, output source**: rule cited `LEG:631-645`; it ends at 646
   (`conséquence rempli`) / closes at 647.
3. **FR-APL-1/2, `residence`**: CONVERSION.md states the labels are in declared order;
   `Métropole` is declared seventh (`FRA:16`) and listed first.
4. **FR-APL-1/2, `nationalite_demandeur` source** `PRO:228-247`: relevant text is 228-244;
   245-247 are an unrelated comment.
5. **FR-APL-1, SPM cut 2021-01-01**: attributed to "L860-3 I"; the article as quoted
   (`LEG:1327-1328`) has no date; the date comes from the encoding (`LEG:1337`).
6. **FR-APL-1..5, fixed-input boilerplate**: the "every field that is not an attribute" text
   repeats Exemple1 values for fields that are attributes of the table (FR-APL-1: date,
   résidence, nationalité; FR-APL-2: Mariés, 1 other occupant, 80 m², not R844-4; FR-APL-3:
   Locataire/BailleurSocial, résidence principale, décent, propriétaire/usufruit, letting, IFI;
   FR-APL-4/5: Locataire/BailleurSocial and Française or Zone1/résidence principale, which
   contradict the table-specific fixed inputs or attributes).
7. **FR-APL-2, `personnes_a_charge` 0..3 and `autres_occupants` 0..1**: sampled sub-domains of
   integer/list inputs; the restriction is a size choice that the spec does not state
   explicitly (only its consequence, the untested caps, is noted).
8. **FR-APL-4, exclusion `fjt_type_without_l353_2_convention`**: R832-20 3° speaks of a
   convention that was signed before 1995 (past fact, `REG:3725-3727`), and the boolean is read
   as a convention in force (`LEG:733`, `741-742`). The exclusion assumes the convention is still
   running; that assumption should be stated, or the 180 rows kept.
9. **FR-APL-5, exclusion source** `LEG:648-657` starts on a blank line; R832-5 (`REG:3055-3056`,
   "titulaire et supporte les charges") is the more direct authority for "a loan must exist".
10. **US-121-2, exclusion statute citation** "26 U.S.C. 121(b)(1)" does not bear on the
    single-taxpayer point.
11. **US-121-2, person 2 ownership source** `S121:50-57` overshoots `PersonalData` (50-54) into
    `JointReturn`.

## Verdicts

| sample | verdict | substantive disagreements | minor items |
|---|---|---|---|
| FR-APL-1 | PASS | 0 | 2, 3, 4, 5, 6 |
| FR-APL-2 | PASS | 0 | 2, 3, 4, 6, 7 |
| FR-APL-3 | PASS | 0 | 2, 6 |
| FR-APL-4 | PASS | 0 | 2, 6, 8 |
| FR-APL-5 | PASS | 0 | 2, 6, 9 |
| US-121-1 | PASS | 0 | none |
| US-121-2 | FAIL | 1 (item 1) | 10, 11 |

Encoding behaviours recorded in the CONVERSION.md files and confirmed against the source
(these are statements about the Catala encoding and are accurate): French applicants never
eligible in Mayotte (`LEG:1398`); 18 m² for a single adult with one dependant versus 16 m² in
R822-25's text; Mayotte +9 m² in code versus +6 m² in text; R822-1 total-share cap not encoded;
sub-tenants and location-accession never eligible; L831-2 2017-12-31 off-by-one; inverted
meaning of `logement_situé_commune_déséquilibre_l831_2`; §121(b)(3) unevaluable because of the
days-vs-years comparison at `S121:376`.
