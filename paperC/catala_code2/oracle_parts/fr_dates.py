# Date intervals shared by FR-APL-1, -2 and -3. Each cut is a date that the
# encoding compares date_courante against (see CONVERSION_2.md); the
# representative is the interval's first day, except for the interval holding
# the official test date, whose representative is that date (2020-03-10).
DATE_INTERVALS = [
    ("2019-09-01_to_2019-09-30", "2019-09-01"),
    ("2019-10-01_to_2020-12-31", "2020-03-10"),
    ("2021-01-01_to_2021-04-30", "2021-01-01"),
    ("2021-05-01_to_2023-04-04", "2021-05-01"),
    ("2023-04-05_to_2023-08-31", "2023-04-05"),
    ("2023-09-01_to_2023-12-31", "2023-09-01"),
    ("2024-01-01_to_2024-10-31", "2024-01-01"),
    ("from_2024-11-01", "2024-11-01"),
]
DATE_REP = dict(DATE_INTERVALS)
DATE_SOURCE = ("cuts: 2019-09-01 aides_logement/archives.catala_fr:10-12 (personnes_à_charge_prises_en_compte "
               "defined from this date; earlier dates raise NoValue); 2019-10-01 arrete_2019-09-27.catala_fr:6070-6074 "
               "(zone III rule); 2021-01-01 code_construction_legislatif.catala_fr:1333-1339 (Saint-Pierre-et-Miquelon) and "
               "code_construction_reglementaire.catala_fr:6207; 2021-05-01 code_construction_reglementaire.catala_fr:6209-6213; "
               "2023-04-05 code_construction_reglementaire.catala_fr:6001-6018; 2023-09-01 archives.catala_fr:10-24, "
               "code_sécurité_sociale.catala_fr:188-221; 2024-01-01 and 2024-11-01 smic/Smic.catala_fr:431-500 (Mayotte SMIC)")


def date_of(label):
    return DATE_REP[label]
