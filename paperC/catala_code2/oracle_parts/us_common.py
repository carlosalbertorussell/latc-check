# ---------------------------------------------------------------------------
# US-121 common part (identical in every US-121-* oracle): imports the Python
# that Catala 1.3.0 generated from catala-examples 2694b17
# (us_tax_code/us_tax_code.catala_en) and the official test data
# (us_tax_code/tests/test_section_121.catala_en, scope Data, lines 6-62).
# ---------------------------------------------------------------------------
import os as _os
import sys as _sys

_GEN = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "catala_code2"))
_sys.path.insert(0, _os.path.join(_GEN, "runtime"))
_sys.path.insert(0, _GEN)

from catala_runtime import Array, Date, Money, Option, Unit  # noqa: E402
from generated import Us_tax_code as us  # noqa: E402

D = lambda s: Date(*map(int, s.split("-")))  # noqa: E731

SALE_DATE = "2021-01-01"      # Data.date_of_sale_or_exchange
RETURN_DATE = "2021-01-01"    # Data.return_date
OFFICIAL_GAIN = "350000"      # Data.gain_from_sale_or_exchange_of_property

# Periods of the official test data (Data, lines 22-36).
FOUR_YEARS_RECENT = ("2017-01-01", "2021-01-01")
ONE_YEAR_RECENT = ("2019-01-01", "2020-01-01")
TWO_YEARS_MIDDLE = ("2015-01-01", "2017-01-02")


def period(p):
    return us.Period(begin=D(p[0]), end=D(p[1]))


def periods(ps):
    return Array([period(p) for p in ps])


def other_sale(date_or_none):
    if date_or_none is None:
        return us.OtherSection121aSale(us.OtherSection121aSale.Code.NoOtherSaleWhereSection121aApplied, Unit())
    return us.OtherSection121aSale(us.OtherSection121aSale.Code.MostRecentSaleWhereSection121aApplied,
                                   us.PreviousSaleWhereSection121aApplied(date_of_sale_or_exchange=D(date_or_none)))


def personal_data(own, use, other=None):
    return us.PersonalData(property_ownage=periods(own), property_usage_as_principal_residence=periods(use),
                           other_section_121a_sale=other_sale(other))


def single_person(own, use, other=None, gain=OFFICIAL_GAIN, sale=SALE_DATE):
    return us.section121_single_person(us.Section121SinglePersonIn(
        date_of_sale_or_exchange_in=D(sale), property_ownage_in=periods(own),
        property_usage_as_principal_residence_in=periods(use), gain_cap_in=Option(None),
        gain_from_sale_or_exchange_of_property_in=Money(gain + ".00"),
        section_121_b_3_applies_in=Option(None), other_section_121a_sale_in=other_sale(other)))


def two_persons(return_type, gain=OFFICIAL_GAIN, sale=SALE_DATE):
    return us.section121_two_persons(us.Section121TwoPersonsIn(
        person1_in=Option(None), person2_in=Option(None), gain_cap_in=Option(None),
        return_type_in=return_type, return_date_in=D(RETURN_DATE), date_of_sale_or_exchange_in=D(sale),
        gain_from_sale_or_exchange_of_property_in=Money(gain + ".00")))


def single_return(pd):
    return us.ReturnType(us.ReturnType.Code.SingleReturn, pd)


def joint_return(pd1, pd2):
    return us.ReturnType(us.ReturnType.Code.JointReturn, us.JointReturn(person1=pd1, person2=pd2))


def surviving_spouse_return(pd, death, dead_pd):
    return us.ReturnType(us.ReturnType.Code.SingleReturnSurvivingSpouse, us.DeadSpouseInfo(
        return__1=pd, date_of_spouse_death=D(death), death_spouse_info_at_time_of_death=dead_pd))


# Official PersonalData values (Data, lines 37-62).
PERSON_OK_1 = ([FOUR_YEARS_RECENT], [FOUR_YEARS_RECENT])
PERSON_OK_2 = ([FOUR_YEARS_RECENT], [TWO_YEARS_MIDDLE, ONE_YEAR_RECENT])
