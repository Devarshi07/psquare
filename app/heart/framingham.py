"""Framingham calculator wrapper.

Provides easy-to-use interface to Framingham risk calculation.
Used as fallback when QRISK3 inputs are incomplete.
"""
import structlog
from dataclasses import dataclass

from app.medical_knowledge.risk_scores import (
    calc_framingham,
    FraminghamInputs,
)

log = structlog.get_logger()


@dataclass
class CVRiskResult:
    """Result of CV risk calculation."""
    risk_percent: float
    risk_category: str  # Low, Borderline, Moderate, High
    risk_color: str
    calculator_used: str = "framingham"
    confidence: str = "High"


def calculate_framingham(
    age: int,
    sex: str,
    total_chol: float,
    hdl_chol: float,
    systolic_bp: float,
    bp_treatment: bool = False,
    smoking: bool = False,
    diabetes: bool = False,
) -> CVRiskResult:
    """Calculate 10-year CV risk using Framingham.

    Args:
        age: Age in years
        sex: "male" or "female"
        total_chol: Total cholesterol (mg/dL)
        hdl_chol: HDL cholesterol (mg/dL)
        systolic_bp: Systolic blood pressure (mmHg)
        bp_treatment: On BP medication
        smoking: Current smoker
        diabetes: Has diabetes

    Returns:
        CVRiskResult with risk percentage and category
    """
    try:
        inputs = FraminghamInputs(
            age=age,
            sex=sex,
            total_cholesterol=total_chol,
            hdl_cholesterol=hdl_chol,
            systolic_bp=systolic_bp,
            bp_treatment=bp_treatment,
            smoking=smoking,
            diabetes=diabetes,
        )

        risk_pct = calc_framingham(inputs)

        # Determine category
        if risk_pct < 5:
            category = "Low"
            color = "#10B981"
        elif risk_pct < 10:
            category = "Borderline"
            color = "#F59E0B"
        elif risk_pct < 20:
            category = "Moderate"
            color = "#F97366"
        else:
            category = "High"
            color = "#EF4444"

        # Confidence is lower since Framingham is older algorithm
        confidence = "Medium"

        return CVRiskResult(
            risk_percent=round(risk_pct, 1),
            risk_category=category,
            risk_color=color,
            calculator_used="framingham",
            confidence=confidence,
        )

    except Exception as e:
        log.error("framingham_calc_error", error=str(e))
        return CVRiskResult(
            risk_percent=5.0,
            risk_category="Low",
            risk_color="#10B981",
            calculator_used="framingham",
            confidence="Low",
        )