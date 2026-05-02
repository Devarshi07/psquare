"""QRISK3 calculator wrapper.

Provides easy-to-use interface to QRISK3 calculation.
"""
import structlog
from dataclasses import dataclass

from app.medical_knowledge.risk_scores import (
    calc_qrisk3,
    QRISK3Inputs,
    QRISK3_COEFFICIENTS,
)

log = structlog.get_logger()


@dataclass
class CVRiskResult:
    """Result of CV risk calculation."""
    risk_percent: float
    risk_category: str  # Low, Borderline, Moderate, High
    risk_color: str
    calculator_used: str = "qrisk3"
    confidence: str = "High"  # Based on input completeness


def calculate_qrisk3(
    age: int,
    sex: str,
    systolic_bp: float,
    total_chol: float,
    hdl_chol: float,
    smoking: bool = False,
    diabetes: bool = False,
    bp_treatment: bool = False,
    ethnicity: str = "south_asian",
    family_history: bool = False,
    bmi: float = 25.0,
    ckd: bool = False,
    afib: bool = False,
) -> CVRiskResult:
    """Calculate 10-year CV risk using QRISK3.

    Args:
        age: Age in years
        sex: "male" or "female"
        systolic_bp: Systolic blood pressure (mmHg)
        total_chol: Total cholesterol (mg/dL)
        hdl_chol: HDL cholesterol (mg/dL)
        smoking: Current smoker
        diabetes: Has diabetes
        bp_treatment: On BP medication
        ethnicity: "white", "south_asian", "black", "chinese", "other"
        family_history: Family history of early CHD
        bmi: Body mass index
        ckd: Chronic kidney disease
        afib: Atrial fibrillation

    Returns:
        CVRiskResult with risk percentage and category
    """
    try:
        # Build inputs
        inputs = QRISK3Inputs(
            age=age,
            sex=sex,
            ethnicity=ethnicity,
            smoking=smoking,
            diabetes=diabetes,
            family_history_early_chd=family_history,
            ckd=ckd,
            afib=afib,
            bp_treatment=bp_treatment,
            systolic_bp=systolic_bp,
            total_hdl_ratio=total_chol / hdl_chol if hdl_chol else 3.5,
            bmi=bmi,
        )

        risk_pct = calc_qrisk3(inputs)

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

        # Determine confidence based on input completeness
        confidence = "High"
        if not total_chol or not hdl_chol:
            confidence = "Medium"
        if not ethnicity:
            confidence = "Low"

        return CVRiskResult(
            risk_percent=round(risk_pct, 1),
            risk_category=category,
            risk_color=color,
            calculator_used="qrisk3",
            confidence=confidence,
        )

    except Exception as e:
        log.error("qrisk3_calc_error", error=str(e))
        # Return minimal risk estimate
        return CVRiskResult(
            risk_percent=5.0,
            risk_category="Low",
            risk_color="#10B981",
            calculator_used="qrisk3",
            confidence="Low",
        )