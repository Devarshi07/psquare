"""Heart age calculator wrapper.

Calculates heart age using the JBS3/QRISK3 method.
"""
import structlog
from dataclasses import dataclass

from app.medical_knowledge.heart_age_table import (
    calc_heart_age,
    calc_heart_age_gap,
    heart_age_gap_to_penalty,
)
from app.medical_knowledge.risk_scores import calc_cv_risk

log = structlog.get_logger()


@dataclass
class HeartAgeResult:
    """Result of heart age calculation."""
    heart_age: int
    chronological_age: int
    gap_years: int  # Positive = older heart
    gap_status: str  # Younger, On par, Older
    gap_color: str
    penalty: float  # 0-100 for Heart Score


def calculate_heart_age(
    age: int,
    sex: str,
    systolic_bp: float = 120,
    total_chol: float = None,
    hdl_chol: float = None,
    smoking: bool = False,
    diabetes: bool = False,
    ethnicity: str = "south_asian",
    family_history: bool = False,
    bmi: float = 25.0,
    ckd: bool = False,
    afib: bool = False,
    bp_treatment: bool = False,
) -> HeartAgeResult:
    """Calculate heart age.

    Args:
        age: Chronological age
        sex: "male" or "female"
        systolic_bp: Systolic BP (mmHg)
        total_chol: Total cholesterol (mg/dL)
        hdl_chol: HDL cholesterol (mg/dL)
        smoking: Current smoker
        diabetes: Has diabetes
        ethnicity: Ethnicity for QRISK3
        family_history: Family history of early CHD
        bmi: BMI
        ckd: Chronic kidney disease
        afib: Atrial fibrillation
        bp_treatment: On BP medication

    Returns:
        HeartAgeResult with heart age and gap
    """
    try:
        # First get CV risk
        cv_risk = calc_cv_risk(
            age=age,
            sex=sex,
            systolic_bp=systolic_bp,
            total_chol=total_chol,
            hdl_chol=hdl_chol,
            smoking=smoking,
            diabetes=diabetes,
            ethnicity=ethnicity,
            family_history=family_history,
            bmi=bmi,
            ckd=ckd,
            afib=afib,
            bp_treatment=bp_treatment,
        )

        # Then calculate heart age from CV risk
        heart_age = calc_heart_age(
            age=age,
            sex=sex,
            cv_risk_pct=cv_risk,
            systolic_bp=systolic_bp,
            total_chol=total_chol or 180,
            hdl_chol=hdl_chol or 50,
            smoking=smoking,
            diabetes=diabetes,
            ethnicity=ethnicity,
        )

        # Calculate gap
        gap = calc_heart_age_gap(heart_age, age)
        penalty = heart_age_gap_to_penalty(gap)

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

        return HeartAgeResult(
            heart_age=heart_age,
            chronological_age=age,
            gap_years=gap,
            gap_status=status,
            gap_color=color,
            penalty=round(penalty, 1),
        )

    except Exception as e:
        log.error("heart_age_calc_error", error=str(e))
        # Fallback to age
        return HeartAgeResult(
            heart_age=age,
            chronological_age=age,
            gap_years=0,
            gap_status="On par",
            gap_color="#10B981",
            penalty=0,
        )