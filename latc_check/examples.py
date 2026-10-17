"""Worked examples.

Pension rule (Raggio & Russell 2021)
------------------------------------
Transcribed from the authors' English draft "Business Rules (BR); Expert
Systems (KBS); LATC Algorithm (English)" (Google Doc, last edited 2020-07-22,
Drive folder "Raul Raggio LATC").  In the final IJSER .docx (Feb 2021) the
tables are embedded as images and could not be machine-read, so the rows below
**must be checked against the published Table 1a / Table 8 of the IJSER
article before the numbers are quoted** (status: TRANSCRIBED_FROM_DRAFT).

Value labels are ASCII renderings of the source:

    Contribution years: '>=30'  '<30'
    Age (normalised):   '>=65'  '60-64' (source: 60 <= x < 65)  '<60'

Domain value order follows the source's frequency table (Table 2 in the
IJSER numbering): order of first appearance in Table 1a.
"""

from __future__ import annotations

from .model import DecisionTable, Row, RV, attrs

SOURCE_STATUS = "TRANSCRIBED_FROM_DRAFT"  # verify against published Table 1a

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

# Published complementary table ("Table 2" in the draft, "Table 8" in IJSER)
# with the experts' valuation ("2 bis" / "8 bis").  The leading number is the
# row's position in the 24-row Table 3 / Table 9.
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
