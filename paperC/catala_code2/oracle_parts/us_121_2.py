# ---------------------------------------------------------------------------
# US-121-2: Section121TwoPersons.income_excluded_from_gross_income
# ---------------------------------------------------------------------------
AGG = [("under_730d", [ONE_YEAR_RECENT]), ("730d_or_more", [FOUR_YEARS_RECENT])]
OTHER_SALES = [("none", None), ("under_2_years_before", "2020-01-01"),
               ("exactly_2_years_before", "2019-01-01"), ("over_2_years_before", "2018-06-01")]
NA = "not_applicable"
GAINS = [("under_250000", "100000"), ("250000_to_500000", "350000"), ("over_500000", "600000")]
RETURNS = ["single_return", "joint_return", "surviving_spouse_return"]
SPOUSE_DEATH = "2020-06-01"


def _fmt(ps):
    return "[" + "; ".join("%s..%s" % p for p in ps) + "]"


_AGG_SRC = ("us_tax_code/section_121.catala_en:205-247 (aggregate over the last five years >= 730 day); "
            "the class holds every list whose window-day total is on that side of 730")
_OS_SRC = "us_tax_code/section_121.catala_en:369-383 ((b)(3), <= 2 year)"


def _person_attrs(prefix, na):
    extra = [NA] if na else []
    rep_na = {NA: "absent: the return carries one PersonalData"} if na else {}
    return [
        {"name": prefix + "_property_ownage", "kind": "enum", "values": [l for l, _ in AGG] + extra,
         "representative": dict({l: _fmt(p) for l, p in AGG}, **rep_na), "source": _AGG_SRC},
        {"name": prefix + "_property_usage_as_principal_residence", "kind": "enum", "values": [l for l, _ in AGG] + extra,
         "representative": dict({l: _fmt(p) for l, p in AGG}, **rep_na), "source": _AGG_SRC},
        {"name": prefix + "_other_section_121a_sale", "kind": "interval", "values": [l for l, _ in OTHER_SALES] + extra,
         "representative": dict({l: ("NoOtherSaleWhereSection121aApplied" if d is None else
                                     "MostRecentSaleWhereSection121aApplied, sold " + d) for l, d in OTHER_SALES}, **rep_na),
         "source": _OS_SRC},
    ]


SPEC = {
    "id": "US-121-2",
    "title": "US IRC section 121(a)-(b)(3): Section121TwoPersons.income_excluded_from_gross_income",
    "source": {"repository": "https://github.com/CatalaLang/catala-examples",
               "commit": "2694b17ddd7c2246e207e8f077d586349ee5abea",
               "entry_point": "Us_tax_code.Section121TwoPersons (output income_excluded_from_gross_income)",
               "files": ["us_tax_code/us_tax_code.catala_en", "us_tax_code/preamble.catala_en",
                         "us_tax_code/section_121.catala_en", "us_tax_code/tests/test_section_121.catala_en"]},
    "attributes": [
        {"name": "return_type", "kind": "enum", "values": RETURNS,
         "representative": {"single_return": "ReturnType.SingleReturn contenu person1",
                            "joint_return": "ReturnType.JointReturn contenu {person1; person2}",
                            "surviving_spouse_return": "ReturnType.SingleReturnSurvivingSpouse contenu {return: person1, date_of_spouse_death: %s, death_spouse_info_at_time_of_death: person_ok_1 of Data}" % SPOUSE_DEATH},
         "source": "us_tax_code/section_121.catala_en:66-74, 96-108"},
    ] + _person_attrs("person1", False) + _person_attrs("person2", True) + [
        {"name": "gain_from_sale_or_exchange_of_property", "kind": "interval", "values": [l for l, _ in GAINS],
         "representative": {l: "$" + g for l, g in GAINS},
         "source": "us_tax_code/section_121.catala_en:254-282 ((b)(1) cap $250,000 compared with >=), 300-323 ((b)(2)(A) $500,000)"},
    ],
    "output": {"name": "income_excluded_from_gross_income",
               "values": ["zero", "full_gain", "capped_at_250000", "capped_at_500000"],
               "source": "us_tax_code/section_121.catala_en:241-246, 276-282; label from the amount: 0 -> zero, = gain -> full_gain, $250,000 -> capped_at_250000, $500,000 -> capped_at_500000"},
    "exclusions": [
        {"id": "person2_iff_joint_return",
         "description": "a second PersonalData exists exactly when the return is a joint return",
         "predicate": "(return_type == 'joint_return') == (person2_property_ownage == 'not_applicable' or person2_property_usage_as_principal_residence == 'not_applicable' or person2_other_section_121a_sale == 'not_applicable')",
         "source": "us_tax_code/section_121.catala_en:66-74 (ReturnType: only JointReturn carries two PersonalData)"},
    ],
    "fixed_inputs": {
        "date_of_sale_or_exchange": {"value": SALE_DATE, "why": "official test value (Data, line 19)"},
        "return_date": {"value": RETURN_DATE, "why": "official test value (Data, line 20); not read by the scope's outputs"},
        "date_of_spouse_death": {"value": SPOUSE_DEATH, "why": "needed to build SingleReturnSurvivingSpouse; Section121TwoPersons reads only its return field"},
        "death_spouse_info_at_time_of_death": {"value": "person_ok_1 of Data", "why": "needed to build SingleReturnSurvivingSpouse; not read by Section121TwoPersons"},
    },
    "notes": "Section121TwoPersons alone, as the official tests call it; the joint-return cap sum of (b)(2)(B) and the surviving-spouse rule of (b)(4) live in Section121TwoPasses and are outside this table. For a single or surviving-spouse return the scope uses the same PersonalData for both persons. Any MostRecentSaleWhereSection121aApplied raises a DateError (REJECTED), as in US-121-1.",
}


def _pd(row, prefix):
    return personal_data(dict(AGG)[row[prefix + "_property_ownage"]],
                         dict(AGG)[row[prefix + "_property_usage_as_principal_residence"]],
                         dict(OTHER_SALES)[row[prefix + "_other_section_121a_sale"]])


def build_inputs(row):
    p1 = _pd(row, "person1")
    rt = row["return_type"]
    if rt == "single_return":
        ret = single_return(p1)
    elif rt == "joint_return":
        ret = joint_return(p1, _pd(row, "person2"))
    else:
        ret = surviving_spouse_return(p1, SPOUSE_DEATH, personal_data(*PERSON_OK_1))
    return ret, dict(GAINS)[row["gain_from_sale_or_exchange_of_property"]]


def label_amount(amount, gain):
    cents = int(amount)
    if cents == 0:
        return "zero"
    if cents == int(Money(gain + ".00")):
        return "full_gain"
    if cents == int(Money("250000.00")):
        return "capped_at_250000"
    if cents == int(Money("500000.00")):
        return "capped_at_500000"
    raise ValueError("unexpected amount %s" % amount)


def run_encoding(inputs):
    ret, gain = inputs
    return label_amount(two_persons(ret, gain).income_excluded_from_gross_income, gain)


OFFICIAL_CASES = [
    {"case_id": "test_section_121.catala_en:Test5",
     "row": {"return_type": "single_return", "person1_property_ownage": "730d_or_more",
             "person1_property_usage_as_principal_residence": "730d_or_more", "person1_other_section_121a_sale": "none",
             "person2_property_ownage": NA, "person2_property_usage_as_principal_residence": NA,
             "person2_other_section_121a_sale": NA, "gain_from_sale_or_exchange_of_property": "250000_to_500000"},
     "expected": "capped_at_250000",
     "original": lambda: run_encoding((single_return(personal_data(*PERSON_OK_1)), OFFICIAL_GAIN))},
    {"case_id": "test_section_121.catala_en:Test6",
     "row": {"return_type": "joint_return", "person1_property_ownage": "730d_or_more",
             "person1_property_usage_as_principal_residence": "730d_or_more", "person1_other_section_121a_sale": "none",
             "person2_property_ownage": "730d_or_more", "person2_property_usage_as_principal_residence": "730d_or_more",
             "person2_other_section_121a_sale": "none", "gain_from_sale_or_exchange_of_property": "250000_to_500000"},
     "expected": "full_gain",
     "original": lambda: run_encoding((joint_return(personal_data(*PERSON_OK_1), personal_data(*PERSON_OK_2)), OFFICIAL_GAIN))},
]
