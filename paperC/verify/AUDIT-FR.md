# Citation audit: FR-PF, FR-AF-1, FR-AF-2, FR-AF-3

Source checked: CatalaLang/catala-examples at `2694b17ddd7c2246e207e8f077d586349ee5abea`
(`git rev-parse HEAD` in the scratchpad clone returns exactly that commit). Paths below are
relative to that clone; `L`, `R`, `D` = `allocations_familiales/securite_sociale_{L,R,D}.catala_fr`,
`epi` = `allocations_familiales/epilogue.catala_fr`, `pro` = `allocations_familiales/prologue.catala_fr`,
`dd` = `allocations_familiales/decrets_divers.catala_fr`.

Read: the four `spec.json`, the four `CONVERSION.md`, `README-FR.md`, every cited Catala line,
`catala_family_benefits/inputs.md`, and the generated Python (`Allocations_familiales.py`,
`France.py`, runtime `Money.__mul__`). Not read: `paperC/harness/`, `paperC/results/`, any
`oracle.py` or `frcatala.py`. A few behaviours were confirmed by calling the generated Python
directly from a scratch script (`paperC/verify/audit/probe.py`); results are quoted where used.
No repository file was modified.

Verdict key: **match**; **minor citation offset** (range ends or starts within about 2 lines
of the right place, or a range is incomplete in a way that does not mislead about the rule);
**disagreement** (wrong place, wrong content, or a statement the source does not support).

---

## (a) Tables

### FR-PF

| Item | Citation checked | Values checked | Verdict | Note |
|---|---|---|---|---|
| attr `residence` | pro:53 `entrée résidence contenu France.Collectivité`; `prologue_france/France.catala_fr:9-18` | 9 values, ASCII names = generated `France.Collectivite.Code` (`LaReunion`='LaRéunion', `SaintBarthelemy`, `Metropole`); no extras, none missing | match | |
| attr `obligation_scolaire` | pro:24 field; pro:17-20 enum; L:54-71 | `Avant`, `Pendant`, `Apres` (='Après'); complete | match | L512-3 1° reads it at L:56-57, 2° at L:69 |
| attr `prise_en_charge` | pro:27 field; pro:10-15 enum | 5 values, ASCII renaming checked against generated `PriseEnCharge.Code`; complete | match | not read by `droit_ouvert`: generated `Allocations_familiales.py:498-533` reads only `beneficie_titre_personnel_aide_personnelle_logement`, `date_de_naissance`, `obligation_scolaire`, `remuneration_mensuelle` |
| attr `age` | pro:26; L:71 `enfant.date_de_naissance + âge_l512_3_2 > date_courante`; R:21 `définition âge_l512_3_2 égal à 20 an`; epi:121-131 (`+ 3 an >=` at 123, `+ 16 an >=` at 127) | thresholds 3/16/20 an; operators: `a00_03` `>=` (epi:123), `a03_16` `<`/`>=` (epi:123,127), `a16_20` `<`/`>` (epi:127, L:71), `a20_plus` `<=` (negation of L:71); birth_from/birth_to recomputed for dc 2020-05-01, all correct | match | probe: b=2000-05-01 (Après, 0 €) gives `faux`, b=2000-05-02 gives `vrai` |
| attr `remuneration` | pro:25; R:30-31 `(smic.brut_horaire * 55%) * 169,0`; R:219-223 (R755-0-2, same formula, `sous condition régime_outre_mer_l751_1`); L:70 `<=`; `smic/Smic.catala_fr:80-110` | 55 %, 169, SMIC 10,15 € (Smic:97) and Mayotte 7,66 € (Smic:112); ceiling after cent rounding 943,02 € / 711,49 € | minor citation offset | Smic range 80-110 stops 2 lines before the Mayotte constant `7,66 €` (line 112; block 102-113). Probe: Métropole/Guyane 943,02 → `vrai`, 943,03 → `faux`; Mayotte 711,49 → `vrai`, 711,50 → `faux` |
| attr `apl` | pro:29; `autres_codes.catala_fr:21-27` (`exception cas_base ... conséquence non rempli`) | bool | match | |
| output `droit_ouvert` | pro:47 `résultat droit_ouvert condition dépend de enfant` | entitled=vrai, not_entitled=faux | match | default faux when no rule fires (Catala `condition`) |
| excl X1 | epi:104-131, lines 123-124 | `Avant` ⇔ `b + 3 an >= dc` ⇔ `a00_03`; predicate `Avant and age != a00_03` | match | L131-1 (epi:106-107) "dès l'âge de trois ans" supports the age 3 split; boundary-day choice is the encoding's (see (d) 3) |
| excl X2 | epi:121-131, lines 123-128 | `Pendant` ⇔ `b+3 an < dc and b+16 an >= dc` ⇔ `a03_16` | match | L131-1 al. 2 (epi:109-110) allows a longer schooling, so X2 is stricter than the statute; CONVERSION C8 says so |
| excl X3 | epi:121-131, lines 127-129 | `Après` ⇔ `b+16 an < dc` ⇔ `a16_20 ∪ a20_plus` | match | |
| fixed `date_courante` | `tests_ouverture_droits.catala_fr:62` `|2020-05-01|`; Smic:80-110 | 2020-05-01 | disagreement (documentation) | "and of most AF tests": only 7 of 14 household tests use 2020-05-01 (Test1-6, Test9); CONVERSION C2 itself says "seven of the fourteen". Smic range: same 2-line offset as above |
| fixed `identifiant` | generated 498-533 | 1 | match | not read |
| fixed `a_deja_ouvert...` | generated 498-533; pro:28 | vrai | match | not read by `droit_ouvert` |
| notes (`conditions_hors_âge`) | L:76-84 | disjunction over all 3 values plus `<= plafond` | match | |

### Shared FR-AF citations (audited once)

Samples: 1 = FR-AF-1, 2 = FR-AF-2, 3 = FR-AF-3. Slot attributes `enfant2_*`, `enfant3_*`
carry exactly the same `source` and `intervals` as `enfant1_*` in each spec (checked
programmatically); only the representatives shift by one day per slot.

| Id | Item (samples) | Citation checked | Values checked | Verdict | Note |
|---|---|---|---|---|---|
| S1 | `residence` attr (1, 2); fixed in 3 | epi:79 `entrée i_résidence contenu France.Collectivité`; France:9-18 | 9 values, ASCII renaming | match | |
| S2 | `ressources` attr (1: 5 bands; 2: 3 bands); fixed 30 000 € in 3 | epi:78; dd:101-122 (57 759 € + 5 775 € × n; 80 831 € + 5 775 € × n, guarded `2020-01-01..2020-12-31`); D:35 `<= plafond_I`, D:58, D:77-78 `> I et <= II`, D:102-103, D:120 `> plafond_II`, D:142 | n = `nombre de enfants_à_charge_droit_ouvert_prestation_familiale` (dd:111, 122) | match | `eq_plafond_I` falls in tier 1 (`<=`), `eq_plafond_II` in tier 2, as the bands imply. "midpoint (rounded down to the euro)" in spec vs "a whole number of euros" in A5: the midpoint 69 295 € + 5 775 € × n is always whole, so no conflict |
| S3 | age bands `enfantK_age` (1 with `absent`, 2, 3) | epi:68; epi:123, 127; D:419-420 (11 an `<=`, 16 an `>`); L:315-321 (`+ âge_minimum <= dc`, L:319-320), R:54 (14 an); L:146-152 (`- date_courante < 365 jour`); L:71, R:21 | operators per band: `a03_11` `b+11 > dc` (complement of D:419), `a11_14` `b+11 <= dc` (D:419) and `b+14 > dc` (complement of L:319-320), `a14_16` `b+14 <= dc` and `b+16 >= dc` (epi:127), `a16_19` `b+16 < dc` and `>= 365 jour` (complement of L:151), `a19_20` `< 365 jour` and `b+20 > dc` (L:71), `a20_plus` `<=`. All birth_from/birth_to values recomputed: correct (dc+365 days = 2021-05-01 = dc + 1 an) | match | Feb 29 births raise an error in the encoding; see (d) 1 |
| S4 | `avait_enfant_avant_2012` attr (1); fixed faux (2, 3) | epi:83, 97-99; dd "Décret 2002-423 art. 7 and Annexe" | bool | disagreement (documentation, minor) | The flag is read only in the Annexe rules (dd:295, 306, ..., 394, 402), all under `sous condition résidence = Mayotte` (dd:286-287). The Article 7 code (dd:180-239) never reads it |
| S5 | `est_parent`, `titre_I` attrs (1); fixed vrai/faux (2, 3) | epi:81-82, 91-96; L:240-246 assertion | bool | match | probe: both false raises `AssertionFailed` at L:241.3-246.6 |
| S6 | `enfantK_remuneration` attr (2, 3); fixed 0 € (1) | epi:67; R:29-31, 218-223; L:70, 83 `<=` | 2 bands, ceiling 943,02 / 711,49 € | match | |
| S7 | `enfantK_prise_en_charge` attr (2); fixed EffectiveEtPermanente (1, 3) | epi:69; pro:10-15; L:186-280 | 5 values | match | T2 mapping to Complète/Partagée/Zéro matches L:189-192, 211-214, 223-226, 263-266, 273-276 |
| S8 | `enfantK_deja_ouvert` attr (3); fixed vrai (1, 2) | epi:70; L:153 `et (enfant.a_déjà_ouvert_droit_aux_allocations_familiales)` | bool | match | |
| S9 | `enfantK_apl` attr (3); fixed faux (1, 2) | epi:71; autres_codes:21-27 | bool | match | |
| S10 | output `regime_montant_verse` (1, 2) | epi:80, 90, 45-52 | `zero` = 0 € | match | |
| S10a | label `mayotte` | dd:170-215 | Mayotte base from first child, resource-independent | minor citation offset (documentation) | dd:170-215 covers Art. 7 heading, the `droit_ouvert_base` exception (dd:191-194) and 1°-2° only. 3° and 4° are dd:219-239, and the rates actually in force on 2020-05-01 are in the Annexe: 7,17 % (dd:389-398), 57,28 € if `avait_enfant` (dd:400-406), 30,68 % (dd:481-487), 14,30 % (dd:562-568). The label itself (positive amount and résidence Mayotte) is unaffected |
| S10b | label `outre_mer_1_enfant` | L:436-466; D:382-404 | L751-1 list (L:376-385), n = 1, 5,88 % (D:403) | minor citation offset | L file has 465 lines; the L755-12 code ends at L:465 |
| S10c | labels `general_t1/t2/t3` | D:35-142 | `<=` I / `> I, <= II` / `> II` | match | |
| S11 | output `composantes_montant_verse` (3) | epi:45-52; D:57-63 (`bmaf.montant * 16%`); D:231-235 (`bmaf.montant * 20,234%`); Bmaf:50-58 (414,4 € from 2020-04-01) | 414,4 × 16 % = 66,304 → 66,30 €; 414,4 × 20,234 % = 83,8497 → 83,85 €; base(2) = 32 % = 132,61 €; base(3) = 132,61 + 41 % (169,90) = 302,51 € | match | the (a, b) decomposition is unique for a, b in 0..3 |
| S12 | fixed `date_courante` (1, 2, 3) | test file dates; Smic:80-110; Bmaf:50-58; dd:101-122 | 2020-05-01; Test1-6, 9 at 2020-05-01, Test10 at 2020-04-20 | match | constancy on [2020-04-01, 2020-12-31] holds for SMIC (Smic:84-85, 106-107), BMAF (Bmaf:55-56), ceilings (dd:105, 116) and Mayotte rates (dd:392-393, 483, 564) |
| S13 | fixed `child_slots` (1: 3, 2: 2, 3: 3) | n/a | | match | |
| S14 | fixed `identifiants` (1, 2, 3) | epi:11-23, 33-35 | 0, 1, 2 | match | |
| S15 | FR-AF-2/3 fixed `est_parent` vrai / `titre_I` faux / `avait` faux "why" | test file | every test sets `est_parent` (e.g. lines 72, 86, 344, 366); none sets `titre_I`; only Test12 sets `avait` (line 343) | match | |

### FR-AF-1

| Item | Citation checked | Verdict | Note |
|---|---|---|---|
| `residence` | S1 | match | |
| `ressources` (5 bands) | S2 | match | |
| `avait_enfant_avant_2012` | S4 | disagreement (documentation, minor) | Art. 7 does not read it; only the Annexe does |
| `est_parent` | S5 | match | |
| `titre_I` | S5 | match | |
| `enfant1_age`, `enfant2_age`, `enfant3_age` | S3 | match | `absent` is a table convention, no Catala counterpart |
| output `regime_montant_verse` | S10, S10a, S10b, S10c | match, with two minor citation offsets | |
| exclusions | none declared | n/a | T5's reasons are consistent with the source |
| fixed `date_courante` | S12 | match | |
| fixed `child_slots` | S13 | match | |
| fixed `identifiants` | S14 | match | |
| fixed `enfant_remuneration` 0 € | S6 | match | |
| fixed `enfant_prise_en_charge` | S7 | match | |
| fixed `enfant_deja_ouvert` vrai | S8 | match | |
| fixed `enfant_apl` faux | S9 | match | |

### FR-AF-2

| Item | Citation checked | Verdict | Note |
|---|---|---|---|
| `residence` | S1 | match | |
| `ressources` (3 bands) | S2 | match | `le_plafond_I` `<=`, `gt_I_le_II`, `gt_plafond_II` match D:35, 77-78, 120 |
| `enfant1_age`, `enfant2_age` | S3 | match | |
| `enfant1_remuneration`, `enfant2_remuneration` | S6 | match | |
| `enfant1_prise_en_charge`, `enfant2_prise_en_charge` | S7 | match | |
| output | S10, S10a, S10b, S10c | match, two minor citation offsets | |
| exclusions | none | n/a | T4 cites L:52-58 correctly |
| fixed `date_courante`, `child_slots`, `identifiants` | S12-S14 | match | |
| fixed `est_parent`, `titre_I`, `avait_enfant_avant_2012` | S5, S4, S15 | match (S4 note applies) | |
| fixed `enfant_deja_ouvert`, `enfant_apl` | S8, S9 | match | T3: forfaitaire needs 3 children in the raw list (L:143, D:319), so `a_déjà_ouvert` has no effect with 2 children; correct |

### FR-AF-3

| Item | Citation checked | Verdict | Note |
|---|---|---|---|
| `enfant1-3_age` | S3 | match | |
| `enfant1-3_remuneration` | S6 | match | |
| `enfant1-3_deja_ouvert` | S8 | match | |
| `enfant1-3_apl` | S9 | match | |
| output `composantes_montant_verse` | S11 | match | |
| exclusions | none | n/a | |
| fixed `date_courante`, `child_slots`, `identifiants` | S12-S14 | match | |
| fixed `residence` Métropole | S1 | match | |
| fixed `ressources` 30 000 € | S2 | match | 30 000 < 57 759 € for every n, so tier 1 and no complément dégressif |
| fixed `est_parent`, `titre_I`, `avait` | S5, S4, S15 | match (S4 note applies) | |
| fixed `enfant_prise_en_charge` | S7 | match | |
| notes / T2 (L:140-156, D:319, L:330-342, R:62) | | match | |

### CONVERSION.md cross-references also checked (all match unless listed in (b))

FR-PF C1 (L:86-90, 76-84), C2, C4 (generated 498-533), C5 (epi:121-131), C6 (runtime
`catala_runtime.py:564-566`: `Money(Decimal(self) * Decimal(other))` rounds to the cent;
10,15 × 55 % = 5,5825 → 5,58; × 169 = 943,02; 7,66 × 55 % = 4,213 → 4,21; × 169 = 711,49), C8
(epi:104-110 quotes L131-1). Counts 3 240 / 810 / 810 / 540 / 1 080 / 360 recomputed by hand: correct.
FR-AF A1 (epi:73-100), A2 (Smic:18, Bmaf:12, Bmaf:50-58), A3 (L:261-271 = L521-2 al. 4),
A4 (L:240-246 = L521-2 al. 3), A6 (D:419, 420, 431; R:80-83; L:148-152, 319), A7, A8
(epi:33-35), A11 (epi:39-43, L:148-152, L:315-342). A11 numerical examples re-run through the
generated Python: 132,61 €, 216,46 €, 366,61 €, 39,66 € all reproduce. FR-AF-2 T2 (L:186-281).
FR-AF-3 T2/T5 (L:140-156, D:319, L:330-342, D:57-63, D:231-235).

---

## (b) Disagreements

No disagreement found affects a ground-truth label. Every enum is complete with correct ASCII
renaming, every threshold value is right, and every boundary operator in the interval
predicates is the one the Catala code uses.

1. **FR-PF fixed input `date_courante`, "why": "and of most AF tests".**
   Source: only Test1-Test6 and Test9 of `tests_allocations_familiales.catala_fr` set
   `définition f.i_date_courante égal à |2020-05-01|` (lines 70, 84, 97, 110, 123, 153, 227).
   That is 7 of 14, which is half. FR-PF CONVERSION C2 and FR-AF A2 correctly say "seven of
   the fourteen". Severity: documentation only.

2. **FR-AF-1 attribute `avait_enfant_avant_2012` source: "read only for Mayotte
   (decrets_divers.catala_fr, Décret n°2002-423 art. 7 and Annexe)".**
   Source: the Article 7 code (dd:180-239) never reads the flag. It is read only in the Annexe
   block, e.g. dd:394 `et non avait_enfant_à_charge_avant_1er_janvier_2012` and dd:402
   `sous condition avait_enfant_à_charge_avant_1er_janvier_2012` (→ `57,28€`, dd:405), under
   `sous condition résidence = Mayotte` (dd:286-287). "Read only for Mayotte" is correct; the
   location should be "Annexe (dd:241-406)". Severity: documentation only.

3. **FR-AF-1/2 output, label `mayotte`: "Décret n°2002-423 art. 7, decrets_divers.catala_fr:170-215".**
   Source: 170-215 ends after 2° (`bmaf.montant * 32%`, dd:215). Art. 7's 3° and 4° are at
   dd:219-239. The rates applied on 2020-05-01 come from the Annexe instead: dd:397
   `bmaf.montant * 7,17%`, dd:486 `bmaf.montant * 30,68%`, dd:567 `bmaf.montant * 14,30%`
   (the Art. 7 rates 5,88 %/32 % are overridden by `exception mayotte`). Correct location:
   dd:172-239 plus Annexe dd:241-569. Severity: documentation only (the label depends only on
   a positive amount and résidence Mayotte).

4. **Smic citation `smic/Smic.catala_fr:80-110` (FR-PF `remuneration`, FR-PF fixed input,
   FR-PF C2, FR-AF A2).** The Mayotte 2020 rule is the block Smic:102-113 and the value
   `7,66 €` is at Smic:112. The range stops 2 lines short. Classified as minor citation
   offset. Severity: documentation only.

5. **L755-12 citation `securite_sociale_L.catala_fr:436-466` (FR-AF-1/2 output, A3).** The file
   has 465 lines; the code ends at L:465. Minor citation offset. Severity: documentation only.

---

## (c) Encoding vs statute

These are places where the encoding (and the spec/CONVERSION text that describes it as the
statutory case) departs from the article text quoted in the `.catala_fr` files. The tables
reproduce the encoding, so none of these is a conversion error.

E1. **Allocation forfaitaire paid in the year before age 20 as well as after it (L521-1 al. 2).**
Quoted statute (L:130-136): forfaitaire "est versée pendant un an ... lorsque l'un ou plusieurs
des enfants qui ouvraient droit aux allocations familiales atteignent l'âge limite". Code
(L:148-152): `(enfant.date_de_naissance + prestations_familiales.âge_l512_3_2) - date_courante < 365 jour`.
This holds for a child less than 365 days *before* the 20th birthday, who still has
`droit_ouvert`. Probe (Métropole, 30 000 €): children 2007-01-01, 2009-01-01, 2003-01-01 →
368,81 €; with 2000-08-01 (`a19_20`) instead of 2003-01-01 → 452,66 € (+83,85 € forfaitaire
while the child still counts in the base). A11 point 1 and README item 8 record only the
"past 20, no time limit" half (negative durations). The spec's `a19_20` band is defined on this
comparison, so the table follows the encoding.

E2. **Forfaitaire without time limit after 20 (L521-1 al. 2, "pendant un an").** Recorded in A11
point 1; matches the quoted text departure. Correct as written.

E3. **Majoration not tied to the child's own entitlement, and the eldest taken over all children
(L521-3, L821-3).** Quoted L521-3 (L:310-311): "Chacun des enfants à charge, à l'exception du plus
âgé". Code: `est_enfant_le_plus_âgé` over all `enfants_à_charge` (epi:33-35), majoration summed over
all `enfants_à_charge` (epi:39-43), `droit_ouvert_majoration` (L:315-342) without `droit_ouvert`.
A11 point 2 records the "child past 20 receives the majoration" effect. Two further effects of
the same code, not stated in A11:
  * an older child without entitlement makes the eldest *entitled* child eligible for the
    majoration. Probe: children 2005-01-01, 2007-01-01 → 132,61 €; adding 1999-01-01 → 282,76 €
    (= 132,61 + 66,30 majoration for the 2005 child + 83,85 forfaitaire);
  * a child with personal housing aid, whom quoted L821-3 (autres_codes:17-19) says "n'est pas pris
    en compte, comme enfant à charge, pour le bénéfice des prestations familiales", still receives
    the majoration and the forfaitaire, and still counts in the forfaitaire's 3-child minimum and
    in the eldest test. Probes: 2003, 2005 (APL), 2009 → 198,91 € (= 132,61 + 66,30 for the APL
    child); 2007, 2009, 1995 (APL) → 216,46 € (forfaitaire for the APL child). FR-AF-3 T2 mentions
    only the raw-list count.

E4. **D755-5 single-child majoration (3,69 % from 11, 5,67 % from 16).** Quoted D755-5 (D:406-408):
"La majoration des allocations familiales pour un seul enfant à charge est fixée à 3,69 p. 100 ... à
partir de onze ans". Code (D:413-433) also requires `droit_ouvert_majoration`, which for one
entitled child requires a non-entitled elder sibling. Probe: Guadeloupe, single child born
2005-01-01 → 24,37 € (5,88 % only, no 3,69 %); with an elder child born 1999 → 39,66 €. A11 point 3
frames this as "reachable"; with respect to the statute, the household the article targets (a
genuinely single child) never receives it, and the household that does receive it has a second
child. Labels do not distinguish it (`outre_mer_1_enfant`).

E5. **L755-12 al. 2: which L521-1 paragraphs are disapplied for one child.** Quoted L755-12
(L:444-445): "les quatre derniers alinéas de l'article L. 521-1 ne sont pas applicables lorsque le
ménage ou la personne a un seul enfant à charge." In the L521-1 text quoted at L:121-180 there are
six paragraphs: (1) due from the second child, (2) forfaitaire, (3) amount varies with resources,
(4) varies with number of children, (5) ceilings revised, (6) complément dégressif. The last four
are (3)-(6). The encoding (L:451-464, comment "Ceci concerne l'ouverture du droit à l'allocation
forfaitaire et au complément dégressif") disapplies the forfaitaire (paragraph 2) and the
complément (paragraph 6). FR-AF A3 describes L755-12 as "no forfaitaire, no complément". By the
quoted text, paragraph 2 stays applicable. No label effect in these tables (a one-child L751-1
household with a positive base is `outre_mer_1_enfant` with or without a forfaitaire).

E6. **Mayotte base scale cumulates the per-rank rates (Décret 2002-423 art. 7 and Annexe).**
Quoted art. 7 (dd:197-228): "1° 5,88 % pour un seul enfant à charge; 2° 32 % pour deux enfants à
charge; 3° 16 % pour le troisième enfant ...". The quoted Annexe (dd:280) for 2020: one child
7,17 %, "familles ayant deux enfants à charge" 30,68 %, three children 44,98 % (= 30,68 + 14,30),
which reads as household totals. Code (dd:185-189) sums first + second + third ranks, with the
first-child rate paid whenever `nombre ... > 0` (dd:396). Probe at 2020-05-01: Mayotte, two children
→ 156,85 € = 7,17 % + 30,68 % of 414,4 €, where the Annexe total for two children is 30,68 %
(127,14 €). Labels unaffected (`mayotte` = any positive amount).

E7. **Child earnings ceiling rounded before the multiplication by 169 (R512-2, R755-0-2).** Quoted
R512-2 (R:24-26): "55 % du salaire minimum ... multiplié par 169", i.e. 10,15 × 0,55 × 169 =
943,4425 € (Mayotte 712,00 €). The Catala runtime rounds `smic.brut_horaire * 55%` to the cent
first, giving 943,02 € (711,49 €). A child earning 943,03-943,44 € (Mayotte 711,50-712,00 €) is
under the statutory ceiling but `faux` in the encoding. The spec's `eq_plafond` representative
(943,02 / 711,49) correctly follows the encoding; README item 1 records the rounding relative to
`inputs.md` only.

E8. **L131-1 boundary days.** Quoted L131-1 (epi:106-107): "dès l'âge de trois ans et jusqu'à l'âge
de seize ans". The encoding keeps a child `Avant` on the third birthday (`+ 3 an >= dc`, epi:123),
whereas "dès l'âge de trois ans" reads as compulsory from that day. FR-PF X1/X2 and the band edges
follow the encoding. One-day effect at a band edge only; not reached by any representative.

E9. **L521-2 al. 3 assertion (FR-AF-1 REJECTED rows).** A4's statement matches the quoted text
(L:234-237: the right "s'ouvre du chef du père ou, à défaut, du chef de la mère"); the encoding
aborts instead (L:241-246). Correctly recorded as REJECTED and not as an exclusion.

E10. **R512-2 / L512-3 2° age limit "jusqu'à l'âge de vingt ans".** The encoding ends entitlement
on the 20th birthday (`>` strict, L:71). This is a reasonable reading of "jusqu'à"; noted only
because the spec states the boundary as a fact of the source, which it is for the code, while
the statute text does not fix the boundary day.

---

## (d) Ambiguities

1. **29 February birth dates inside the age bands (FR-AF-1/2/3).** The wrapper computes
   `enfant.d_date_de_naissance + 3 an` with `AbortOnRound` (epi:123; generated line 1924) for
   every child. Probe: a child born 2008-02-29 or 2004-02-29 makes `interface_allocations_familiales`
   raise `DateError: ambiguous date computation with no rounding mode specified` at
   epi:123.16-123.49. Bands `a00_03` (2020-02-29), `a03_11` (2012-02-29, 2016-02-29), `a11_14`
   (2008-02-29), `a16_19` (2004-02-29) and `a20_plus` contain such dates; `a14_16` and `a19_20` do
   not. The interval predicates do not exclude them, so a band's label is not uniform over its
   stated birth-date range (those dates would be REJECTED). The specs only say "No representative
   is a 29 February". FR-PF is not affected in its scope (no `+ 3 an` in `PrestationsFamiliales`;
   leap day + 20 an is a leap day for the dates involved), but the X1-X3 predicates written as
   `b + 3 an` are undefined there too.
2. **`a00_03` includes births after `date_courante`** (birth_to null). Unborn "children" are
   evaluated by the encoding as `Avant`; statute meaning is unclear. Declared openly in A6/C5.
3. **"Enfant à charge" for the forfaitaire minimum (L521-1 al. 2 with D521-2 III).** The code
   counts the raw list `nombre de enfants_à_charge >= 3` (L:143), including children past 20 or
   with housing aid. Whether such children count as "enfants à charge" under the quoted text is
   open; it is related to E3.
4. **FR-PF X2 vs L131-1 al. 2.** The statute allows compulsory schooling beyond 16 in particular
   cases, so `Pendant` with `a16_20` is not impossible by statute; the exclusion relies on the
   encoding's own derivation. CONVERSION C8 discloses this.
5. **Within-band birth order (FR-AF-2).** Already documented in FR-AF-2 CONVERSION; the 42 label
   changes follow from E3/E4 (eldest test over all children). No citation issue.
