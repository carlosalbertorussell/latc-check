"""Worked examples.

Pension rule (Raggio & Russell 2021)
------------------------------------
Transcribed from Raggio & Russell, IJSER 12(1), 2021.  Table 1a and the
completed 24-row table were checked cell by cell against the manuscript
submitted to IJSER, where the tables are images (status:
CHECKED_AGAINST_IJSER_MANUSCRIPT).  That manuscript prints row 6 of the
completed table as "SI"; it is read here as YES.

Value labels are ASCII renderings of the source:

    Contribution years: '>=30'  '<30'
    Age (normalised):   '>=65'  '60-64' (source: 60 <= x < 65)  '<60'

Domain value order follows the source's frequency table (Table 2 in the
IJSER numbering): order of first appearance in Table 1a.
"""

from __future__ import annotations

from .model import DecisionTable, Row, RV, attrs

SOURCE_STATUS = "CHECKED_AGAINST_IJSER_MANUSCRIPT"

PENSION_ATTRS = attrs([
    ("Sex", ("M", "F")),
    ("Activity", ("D", "I")),
    ("ContributionYears", (">=30", "<30")),
    ("Age", (">=65", "60-64", "<60")),
])

# Table 1a - Initial Table, with Normalized Domains (8 rows).
PENSION_T0 = [
    Row(("M", "D", ">=30", ">=65"), "YES"),
    Row(("M", "I", ">=30", ">=65"), "YES"),
    Row(("F", "D", ">=30", "60-64"), "YES"),
    Row(("F", "I", ">=30", "60-64"), "YES"),
    Row(("F", "I", ">=30", "<60"), "NO"),
    Row(("M", "I", "<30", ">=65"), RV),
    Row(("M", "I", "<30", "60-64"), "NO"),
    Row(("F", "D", "<30", "60-64"), "YES"),
]

# Published complementary table (Table 8 in IJSER) with the experts'
# valuation (Table 8 Bis).  The leading number is the row's position in the
# 24-row completed table (Table 9).
PENSION_PUBLISHED_COMPLEMENT = [
    (1, ("M", "D", ">=30", "<60"), "NO"),
    (2, ("M", "D", ">=30", "60-64"), "NO"),
    (4, ("M", "D", "<30", "<60"), "NO"),
    (5, ("M", "D", "<30", "60-64"), "NO"),
    (6, ("M", "D", "<30", ">=65"), "YES"),
    (7, ("M", "I", ">=30", "<60"), "NO"),
    (8, ("M", "I", ">=30", "60-64"), "NO"),
    (11, ("M", "I", "<30", "<60"), "NO"),
    (13, ("F", "D", ">=30", "<60"), "NO"),
    (15, ("F", "D", ">=30", ">=65"), "YES"),
    (16, ("F", "D", "<30", "<60"), "NO"),
    (18, ("F", "D", "<30", ">=65"), "YES"),
    (21, ("F", "I", ">=30", ">=65"), "YES"),
    (22, ("F", "I", "<30", "<60"), "NO"),
    (23, ("F", "I", "<30", "60-64"), RV),
    (24, ("F", "I", "<30", ">=65"), RV),
]


def pension_table() -> DecisionTable:
    return DecisionTable(PENSION_ATTRS, list(PENSION_T0), outcomes=("YES", "NO", RV))


def pension_completed() -> DecisionTable:
    """T0 plus the published complement with the experts' outcomes."""
    extra = [Row(c, o) for _, c, o in PENSION_PUBLISHED_COMPLEMENT]
    return pension_table().with_rows(list(PENSION_T0) + extra)


# Raw-input binning for the evaluator.  The operating ranges are ASSUMPTIONS
# made for the out-of-range tests; the source does not state them.
AGE_RANGE = (18, 120)          # years, inclusive
CONTRIBUTION_RANGE = (0, 60)   # years, inclusive


def bin_age(years):
    lo, hi = AGE_RANGE
    if not isinstance(years, int) or not lo <= years <= hi:
        return None
    return ">=65" if years >= 65 else "60-64" if years >= 60 else "<60"


def bin_contribution(years):
    lo, hi = CONTRIBUTION_RANGE
    if not isinstance(years, int) or not lo <= years <= hi:
        return None
    return ">=30" if years >= 30 else "<30"


PENSION_BINNERS = {"ContributionYears": bin_contribution, "Age": bin_age}


# Two-attribute counterexample: the two tables below have identical frequency
# tables but disjoint complements, so no procedure that reads only the
# frequency table can complete both correctly.
COUNTER_ATTRS = attrs([("Sex", ("M", "F")), ("Activity", ("D", "I"))])
COUNTER_T0 = [Row(("M", "D"), "YES"), Row(("F", "I"), "NO")]
COUNTER_T0_TWIN = [Row(("M", "I"), "YES"), Row(("F", "D"), "NO")]


def counterexample_table() -> DecisionTable:
    return DecisionTable(COUNTER_ATTRS, list(COUNTER_T0))


def counterexample_twin() -> DecisionTable:
    return DecisionTable(COUNTER_ATTRS, list(COUNTER_T0_TWIN))
