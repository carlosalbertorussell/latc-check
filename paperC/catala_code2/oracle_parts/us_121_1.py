# ---------------------------------------------------------------------------
# US-121-1: Section121SinglePerson.requirements_met
# ---------------------------------------------------------------------------
# Period lists, sale on 2021-01-01, so the 5-year mark is 2016-01-01. The
# window-day count is what aggregate_periods_from_last_five_years returns.
PERIOD_LISTS = [
    ("none", []),
    ("one_inside_window_over_730d", [FOUR_YEARS_RECENT]),                 # 1461 d
    ("one_inside_window_730d", [("2018-01-02", "2020-01-02")]),           # 730 d
    ("one_inside_window_under_730d", [ONE_YEAR_RECENT]),                  # 365 d
    ("one_across_5y_mark_over_730d", [("2010-01-01", "2019-01-01")]),     # 1095 d
    ("one_across_5y_mark_730d", [("2010-01-01", "2018-01-01")]),          # 730 d
    ("one_across_5y_mark_under_730d", [TWO_YEARS_MIDDLE]),                # 366 d
    ("one_ended_before_5y_mark", [("2005-01-01", "2015-06-01")]),         # 0 d
    ("two_total_730d_or_more", [TWO_YEARS_MIDDLE, ONE_YEAR_RECENT]),      # 366 + 365 = 731 d
    ("two_total_under_730d", [("2015-01-01", "2016-06-01"), ONE_YEAR_RECENT]),  # 151 + 365 = 516 d
]
OTHER_SALES = [("none", None), ("under_2_years_before", "2020-01-01"),
               ("exactly_2_years_before", "2019-01-01"), ("over_2_years_before", "2018-06-01")]


def _fmt(ps):
    return "[" + "; ".join("%s..%s" % p for p in ps) + "]"


_LIST_SRC = ("us_tax_code/section_121.catala_en:205-247 (aggregate_periods_from_last_five_years: three branches on "
             "begin + 5 year and end + 5 year against the sale date; requirement >= 730 day)")
SPEC = {
    "id": "US-121-1",
    "title": "US IRC section 121(a): Section121SinglePerson.requirements_met",
    "source": {"repository": "https://github.com/CatalaLang/catala-examples",
               "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
               "entry_point": "Us_tax_code.Section121SinglePerson (output requirements_met)",
               "files": ["us_tax_code/us_tax_code.catala_en", "us_tax_code/preamble.catala_en",
                         "us_tax_code/section_121.catala_en", "us_tax_code/tests/test_section_121.catala_en"]},
    "attributes": [
        {"name": "property_ownage", "kind": "enum", "values": [l for l, _ in PERIOD_LISTS],
         "representative": {l: _fmt(p) for l, p in PERIOD_LISTS}, "source": _LIST_SRC},
        {"name": "property_usage_as_principal_residence", "kind": "enum", "values": [l for l, _ in PERIOD_LISTS],
         "representative": {l: _fmt(p) for l, p in PERIOD_LISTS}, "source": _LIST_SRC},
        {"name": "other_section_121a_sale", "kind": "interval", "values": [l for l, _ in OTHER_SALES],
         "representative": {l: ("NoOtherSaleWhereSection121aApplied" if d is None else
                                "MostRecentSaleWhereSection121aApplied, sold " + d) for l, d in OTHER_SALES},
         "source": "us_tax_code/section_121.catala_en:369-383 (b)(3): date_of_sale_or_exchange - other_sale.date_of_sale_or_exchange <= 2 year"},
    ],
    "output": {"name": "requirements_met", "values": ["met", "not_met"],
               "source": "us_tax_code/section_121.catala_en:224-240"},
    "exclusions": [],
    "fixed_inputs": {
        "date_of_sale_or_exchange": {"value": SALE_DATE, "why": "date of every official test (Data, test_section_121.catala_en:19)"},
        "gain_from_sale_or_exchange_of_property": {"value": "$350,000", "why": "official test value (Data, line 21); requirements_met does not read it"},
    },
    "notes": "Every list with a MostRecentSaleWhereSection121aApplied value makes the scope raise a Catala DateError (days compared with years at section_121.catala_en:376), in the interpreter and in Python; those rows are REJECTED although requirements_met itself does not read (b)(3).",
}


def build_inputs(row):
    return (dict(PERIOD_LISTS)[row["property_ownage"]],
            dict(PERIOD_LISTS)[row["property_usage_as_principal_residence"]],
            dict(OTHER_SALES)[row["other_section_121a_sale"]])


def run_encoding(inputs):
    own, use, other = inputs
    return "met" if bool(single_person(own, use, other).requirements_met) else "not_met"


def _official(use):
    return lambda: run_encoding(([FOUR_YEARS_RECENT], use, None))


OFFICIAL_CASES = [
    {"case_id": "test_section_121.catala_en:Test1",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "one_inside_window_over_730d", "other_section_121a_sale": "none"},
     "expected": "met", "original": _official([FOUR_YEARS_RECENT])},
    {"case_id": "test_section_121.catala_en:Test2",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "one_inside_window_under_730d", "other_section_121a_sale": "none"},
     "expected": "not_met", "original": _official([ONE_YEAR_RECENT])},
    {"case_id": "test_section_121.catala_en:Test3",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "one_across_5y_mark_under_730d", "other_section_121a_sale": "none"},
     "expected": "not_met", "original": _official([TWO_YEARS_MIDDLE])},
    {"case_id": "test_section_121.catala_en:Test4",
     "row": {"property_ownage": "one_inside_window_over_730d",
             "property_usage_as_principal_residence": "two_total_730d_or_more", "other_section_121a_sale": "none"},
     "expected": "met", "original": _official([TWO_YEARS_MIDDLE, ONE_YEAR_RECENT])},
]
