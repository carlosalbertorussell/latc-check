"""Builders for the inputs of the Catala encoding of US Internal Revenue Code section 121.

The generated module `generated/Us_tax_code.py` (Catala 1.3.0, catala-examples
commit 2694b17, us_tax_code/section_121.catala_en) takes Catala structures as
input. The functions below build them from plain Python values. Context
variables (`gain_cap`, `section_121_b_3_applies`, `person1`, `person2`) are
passed as `Option(None)`, which makes the scope use its own definitions, exactly
as the official tests do by not redefining them.

Used by run_official_tests_us121.py and by the oracles in paperC/specs/US-121/.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "runtime", "catala"))
sys.path.insert(0, HERE)

if sys.version_info < (3, 12):
    sys.exit(f"Python 3.12 or later is required by the Catala 1.3.0 runtime (found {sys.version.split()[0]})")

from catala_runtime import Array, CatalaError, Date, Lang, Money, Option, Unit, catala_set_lang  # noqa: E402
from generated import Us_tax_code as T  # noqa: E402

catala_set_lang(Lang.En)


def date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return Date(y, m, d)


def period(begin, end):
    return T.Period(begin=date(begin), end=date(end))


def periods(pairs):
    return Array([period(b, e) for b, e in pairs])


def other_sale(previous_sale_date=None):
    """NoOtherSaleWhereSection121aApplied, or MostRecentSaleWhereSection121aApplied
    with the date of that earlier sale."""
    if previous_sale_date is None:
        return T.OtherSection121aSale(T.OtherSection121aSale.Code.NoOtherSaleWhereSection121aApplied, Unit())
    return T.OtherSection121aSale(
        T.OtherSection121aSale.Code.MostRecentSaleWhereSection121aApplied,
        T.PreviousSaleWhereSection121aApplied(date_of_sale_or_exchange=date(previous_sale_date)))


def personal_data(ownage, usage, previous_sale_date=None):
    return T.PersonalData(
        property_ownage=periods(ownage),
        property_usage_as_principal_residence=periods(usage),
        other_section_121a_sale=other_sale(previous_sale_date),
    )


def single_return(p):
    return T.ReturnType(T.ReturnType.Code.SingleReturn, p)


def joint_return(p1, p2):
    return T.ReturnType(T.ReturnType.Code.JointReturn, T.JointReturn(person1=p1, person2=p2))


def surviving_spouse_return(p, date_of_spouse_death, dead_spouse):
    return T.ReturnType(T.ReturnType.Code.SingleReturnSurvivingSpouse, T.DeadSpouseInfo(
        return__1=p, date_of_spouse_death=date(date_of_spouse_death),
        death_spouse_info_at_time_of_death=dead_spouse))


def single_person(date_of_sale, ownage, usage, gain, previous_sale_date=None):
    """Scope Section121SinglePerson; returns its output record."""
    return T.section121_single_person(T.Section121SinglePersonIn(
        date_of_sale_or_exchange_in=date(date_of_sale),
        property_ownage_in=periods(ownage),
        property_usage_as_principal_residence_in=periods(usage),
        gain_cap_in=Option(None),
        gain_from_sale_or_exchange_of_property_in=Money(gain),
        section_121_b_3_applies_in=Option(None),
        other_section_121a_sale_in=other_sale(previous_sale_date),
    ))


def two_persons(return_type, date_of_sale, return_date, gain):
    """Scope Section121TwoPersons; returns its output record."""
    return T.section121_two_persons(T.Section121TwoPersonsIn(
        person1_in=Option(None), person2_in=Option(None), gain_cap_in=Option(None),
        return_type_in=return_type,
        return_date_in=date(return_date),
        date_of_sale_or_exchange_in=date(date_of_sale),
        gain_from_sale_or_exchange_of_property_in=Money(gain),
    ))


def add_years(iso, years):
    import datetime
    d = datetime.date.fromisoformat(iso)
    return d.replace(year=d.year + years)


def aggregate_days_last_five_years(date_of_sale, pairs):
    """Days counted by the encoding's aggregate_periods_from_last_five_years
    (us_tax_code/section_121.catala_en:179-191), recomputed with datetime:
    a period whose begin is at most 5 years before the sale counts in full
    (end - begin), a period that ended 5 years or more before the sale counts 0,
    and a period straddling the 5-year mark counts (end + 5 years) - sale."""
    import datetime
    sale = datetime.date.fromisoformat(date_of_sale)
    total = 0
    for b, e in pairs:
        begin, end = datetime.date.fromisoformat(b), datetime.date.fromisoformat(e)
        if sale <= add_years(b, 5):
            total += (end - begin).days
        elif sale >= add_years(e, 5):
            total += 0
        else:
            total += (add_years(e, 5) - sale).days
    return total
