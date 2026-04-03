"""
Merit calculation logic for all 3 categories.

Category 1  — Core Agriculture  (B-group only)
  merit = (theory_obtained / theory_total) × 200 + (gujcet / 120) × 100
  farming bonus: +5% on final merit

Category 2  — Technical Agriculture (A or B group)
  PCM: merit = (theory / total) × 200 + (gujcet / 120) × 100
  PCB: same formula

Category 3  — Home & Community Science
  Same formula as category 1 but different course pool
"""

from dataclasses import dataclass
from typing import Literal


CATEGORY_WEIGHTS = {
    "1": {"theory_out_of": 200, "gujcet_out_of": 100},
    "2": {"theory_out_of": 200, "gujcet_out_of": 100},
    "3": {"theory_out_of": 200, "gujcet_out_of": 100},
}

FARMING_BONUS_PERCENT = 5.0
MAX_MERIT = 300.0


@dataclass
class MeritInput:
    category: Literal["1", "2", "3"]
    theory_obtained: float
    theory_total: int          # 300 / 240 / 210
    gujcet_marks: float        # out of 120
    student_category: str      # OPEN, SEBC, SC, ST, EWS, PH, EX, OB
    farming_background: bool = False
    subject_group: str = ""    # "PCM" or "PCB" for category 2


@dataclass
class MeritResult:
    raw_merit: float
    final_merit: float
    farming_bonus_applied: bool
    theory_component: float
    gujcet_component: float


def calculate_merit(inp: MeritInput) -> MeritResult:
    """Return merit score rounded to 4 decimal places."""
    weights = CATEGORY_WEIGHTS[inp.category]

    # Normalise theory to 200
    theory_component = (inp.theory_obtained / inp.theory_total) * weights["theory_out_of"]
    # Normalise GUJCET to 100
    gujcet_component = (inp.gujcet_marks / 120.0) * weights["gujcet_out_of"]

    raw_merit = theory_component + gujcet_component

    # Farming bonus: +5% of raw merit (capped at MAX_MERIT)
    if inp.farming_background:
        bonus = raw_merit * (FARMING_BONUS_PERCENT / 100)
        final_merit = min(raw_merit + bonus, MAX_MERIT)
    else:
        final_merit = raw_merit

    return MeritResult(
        raw_merit=round(raw_merit, 4),
        final_merit=round(final_merit, 4),
        farming_bonus_applied=inp.farming_background,
        theory_component=round(theory_component, 4),
        gujcet_component=round(gujcet_component, 4),
    )


def get_admission_probability(merit: float, last_cutoff: float) -> str:
    """Rough probability label based on merit vs last year cutoff."""
    diff = merit - last_cutoff
    if diff >= 5:
        return "high"
    elif diff >= 0:
        return "medium"
    elif diff >= -5:
        return "low"
    else:
        return "unlikely"
