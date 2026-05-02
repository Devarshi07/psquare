"""Biological age computation.

Combines face age + lifestyle questionnaire + objective data.
Formula per CLAUDE.md §11.5:
biological_age = chronological_age
               + 0.6 * (face_age − chronological_age)
               + lifestyle_adjustment_from_questionnaire
               + objective_data_adjustment
"""
import structlog
from dataclasses import dataclass
from typing import Optional

from app.medical_knowledge.bioage_weights import (
    calc_biological_age,
    calc_questionnaire_adjustment,
    calc_objective_adjustment,
    QUESTIONNAIRE_WEIGHTS,
)

log = structlog.get_logger()


@dataclass
class BioAgeResult:
    """Final biological age result."""
    biological_age: float
    chronological_age: int
    gap_years: float  # positive = older
    gap_status: str  # "Younger", "On par", "Older", "Much older"
    gap_color: str
    confidence: str
    face_age_estimate: Optional[float] = None
    face_drivers: list[dict] = None
    questionnaire_adjustment: float = 0
    objective_adjustment: float = 0


def compute_biological_age(
    chronological_age: int,
    face_age_estimate: float = None,
    questionnaire_answers: dict = None,
    objective_data: dict = None,
) -> BioAgeResult:
    """Compute final biological age.

    Args:
        chronological_age: User's actual age
        face_age_estimate: Age estimate from face selfie (optional)
        questionnaire_answers: Dict from bioage questionnaire (optional)
        objective_data: Dict with BP, lipids, BMI, smoking, HRV (optional)

    Returns:
        BioAgeResult with biological age and breakdown
    """
    # Calculate adjustments
    questionnaire_adj = 0
    if questionnaire_answers:
        questionnaire_adj = calc_questionnaire_adjustment(questionnaire_answers)

    objective_adj = 0
    if objective_data:
        objective_adj = calc_objective_adjustment(**objective_data)

    # Calculate final biological age
    if face_age_estimate:
        # Full formula with face age
        biological_age = chronological_age + 0.6 * (face_age_estimate - chronological_age)
        biological_age += questionnaire_adj * 0.4 / 5  # Normalize lifestyle
        biological_age += objective_adj * 0.2
    else:
        # Without face age, use questionnaire + objective only
        biological_age = chronological_age + questionnaire_adj + objective_adj * 0.5

    # Calculate gap
    gap = biological_age - chronological_age

    # Determine status
    if gap <= -3:
        status = "Younger"
        color = "#10B981"
    elif gap <= 3:
        status = "On par"
        color = "#10B981"
    elif gap <= 10:
        status = "Older"
        color = "#F59E0B"
    else:
        status = "Much older"
        color = "#EF4444"

    # Confidence
    confidence = "High"
    if not face_age_estimate and not questionnaire_answers:
        confidence = "Low"
    elif not face_age_estimate or not questionnaire_answers:
        confidence = "Medium"

    return BioAgeResult(
        biological_age=round(biological_age, 1),
        chronological_age=chronological_age,
        gap_years=round(gap, 1),
        gap_status=status,
        gap_color=color,
        confidence=confidence,
        face_age_estimate=face_age_estimate,
        questionnaire_adjustment=round(questionnaire_adj, 1),
        objective_adjustment=round(objective_adj, 1),
    )


def format_bioage_for_whatsapp(result: BioAgeResult) -> str:
    """Format biological age result for WhatsApp."""
    lines = ["🧬 *Your Biological Age*", ""]

    # Main number
    if result.gap_years < 0:
        gap_text = f"{abs(result.gap_years):.0f} years younger"
    elif result.gap_years > 0:
        gap_text = f"{result.gap_years:.0f} years older"
    else:
        gap_text = "on par"

    lines.append(f"*📊 Biological Age: {result.biological_age:.0f}*")
    lines.append(f"({result.chronological_age} years old — {gap_text})")
    lines.append("")

    # Confidence
    lines.append(f"Confidence: {result.confidence}")
    lines.append("")

    # Disclaimer
    lines.append("_This is an estimate from your face and lifestyle answers —_")
    lines.append("_it's a useful directional signal for tracking lifestyle changes,_")
    lines.append("_but it is not a medical biomarker._")

    return "\n".join(lines)