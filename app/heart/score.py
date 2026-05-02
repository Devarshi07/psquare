"""P² Heart Score calculator.

The core scoring algorithm per CLAUDE.md §7:
P² Heart Score (0–100) = 100 − weighted_penalty

weighted_penalty = (
    0.35 * cv_risk_penalty       # from QRISK3 / Framingham, 10-yr risk %
  + 0.15 * heart_age_penalty     # heart age − chronological age
  + 0.25 * lifestyle_penalty     # composite of BP, lipids, smoking, activity, diet, sleep, stress, alcohol, BMI/waist
  + 0.15 * condition_penalty     # known CVD, diabetes, family history modifiers
  + 0.10 * ppg_penalty           # NEW: HR, HRV, stress index from PPG scan (within last 7 days)
)

If no recent PPG (<7 days), the 10% PPG weight is redistributed proportionally.
"""
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.heart.qrisk3 import calculate_qrisk3
from app.heart.framingham import calculate_framingham
from app.heart.heart_age import calculate_heart_age
from app.medical_knowledge.risk_scores import cv_risk_to_penalty
from app.medical_knowledge.reference_ranges import get_bp_status, get_rhr_status

log = structlog.get_logger()


@dataclass
class HeartScoreInput:
    """All inputs needed for Heart Score calculation."""
    # Demographics
    age: int
    sex: str  # "male" or "female"
    ethnicity: str = "south_asian"

    # BP
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None

    # Lipids
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    tg: Optional[float] = None
    total_chol: Optional[float] = None

    # Glucose
    hba1c: Optional[float] = None

    # Body
    bmi: Optional[float] = None
    waist_cm: Optional[float] = None

    # Lifestyle
    daily_steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    stress_score: Optional[int] = None  # 1-10

    # Smoking
    smoking_status: str = "never"  # never, former, current
    cigarettes_per_day: Optional[int] = None

    # Alcohol
    alcohol_units_per_week: Optional[int] = None

    # Medical history
    has_hypertension: bool = False
    has_high_cholesterol: bool = False
    has_diabetes: bool = False
    has_prior_mi: bool = False
    has_prior_stroke: bool = False
    has_stent: bool = False
    has_bypass: bool = False
    has_afib: bool = False
    has_heart_failure: bool = False
    family_history_early_chd: bool = False

    # Medications
    on_bp_meds: bool = False
    on_statin: bool = False

    # PPG (optional)
    recent_hr_bpm: Optional[int] = None
    recent_rmssd_ms: Optional[float] = None
    recent_stress_index: Optional[int] = None
    ppg_scan_date: Optional[datetime] = None


@dataclass
class HeartScoreResult:
    """Result of P² Heart Score calculation."""
    score: int  # 0-100
    score_band: str  # Excellent, Good, Fair, At Risk, High Risk
    score_color: str
    confidence: str  # High, Medium, Low (based on missing data)
    confidence_percent: float  # % of inputs available

    # Breakdown
    cv_risk_percent: float
    cv_risk_penalty: float
    heart_age_gap: int
    heart_age_penalty: float
    lifestyle_penalty: float
    condition_penalty: float
    ppg_penalty: float

    # Weights (may be redistributed)
    weights: dict  # Shows actual weights used

    computed_at: datetime


# Score bands
SCORE_BANDS = {
    (85, 100): ("Excellent", "#10B981"),
    (70, 84): ("Good", "#10B981"),
    (55, 69): ("Fair", "#F59E0B"),
    (40, 54): ("At Risk", "#F97366"),
    (0, 39): ("High Risk", "#EF4444"),
}


def calculate_lifestyle_penalty(inputs: HeartScoreInput) -> float:
    """Calculate lifestyle penalty (0-100).

    Composite of BP, lipids, smoking, activity, diet, sleep, stress, alcohol, BMI/waist.
    """
    penalties = []
    weights = []

    # BP (20% of lifestyle)
    if inputs.systolic_bp and inputs.diastolic_bp:
        status, _ = get_bp_status(int(inputs.systolic_bp), int(inputs.diastolic_bp))
        if "Optimal" in status:
            penalties.append(0)
        elif "Normal" in status:
            penalties.append(5)
        elif "Elevated" in status:
            penalties.append(20)
        elif "Stage 1" in status:
            penalties.append(40)
        else:
            penalties.append(70)
    else:
        penalties.append(25)  # Unknown = moderate penalty
    weights.append(0.20)

    # Cholesterol (20%)
    if inputs.ldl:
        if inputs.ldl < 100:
            penalties.append(0)
        elif inputs.ldl < 130:
            penalties.append(10)
        elif inputs.ldl < 160:
            penalties.append(30)
        else:
            penalties.append(50)
    else:
        penalties.append(25)
    weights.append(0.20)

    # Smoking (20%)
    if inputs.smoking_status == "current":
        penalties.append(60)
    elif inputs.smoking_status == "former":
        penalties.append(20)
    else:
        penalties.append(0)
    weights.append(0.20)

    # Activity (15%)
    if inputs.daily_steps:
        if inputs.daily_steps >= 10000:
            penalties.append(0)
        elif inputs.daily_steps >= 7500:
            penalties.append(5)
        elif inputs.daily_steps >= 5000:
            penalties.append(15)
        else:
            penalties.append(35)
    else:
        penalties.append(25)
    weights.append(0.15)

    # Sleep (10%)
    if inputs.sleep_hours:
        if 7 <= inputs.sleep_hours <= 8:
            penalties.append(0)
        elif 6 <= inputs.sleep_hours < 7:
            penalties.append(10)
        elif 5 <= inputs.sleep_hours < 6:
            penalties.append(25)
        else:
            penalties.append(40)
    else:
        penalties.append(15)
    weights.append(0.10)

    # Stress (10%)
    if inputs.stress_score:
        if inputs.stress_score <= 3:
            penalties.append(0)
        elif inputs.stress_score <= 5:
            penalties.append(15)
        elif inputs.stress_score <= 7:
            penalties.append(30)
        else:
            penalties.append(50)
    else:
        penalties.append(15)
    weights.append(0.10)

    # Alcohol (5%)
    if inputs.alcohol_units_per_week:
        if inputs.alcohol_units_per_week <= 7:
            penalties.append(0)
        elif inputs.alcohol_units_per_week <= 14:
            penalties.append(20)
        else:
            penalties.append(40)
    else:
        penalties.append(5)
    weights.append(0.05)

    # Calculate weighted average
    total_weight = sum(weights)
    weighted = sum(p * w / total_weight for p, w in zip(penalties, weights))
    return weighted


def calculate_condition_penalty(inputs: HeartScoreInput) -> float:
    """Calculate condition penalty (0-100).

    Based on known CVD, diabetes, family history.
    """
    penalty = 0

    # Prior cardiovascular events = highest
    if inputs.has_prior_mi:
        penalty += 100
    if inputs.has_prior_stroke:
        penalty += 100
    if inputs.has_stent:
        penalty += 80
    if inputs.has_bypass:
        penalty += 80

    # Atrial fibrillation
    if inputs.has_afib:
        penalty += 30

    # Heart failure
    if inputs.has_heart_failure:
        penalty += 50

    # Diabetes (unmedicated = higher)
    if inputs.has_diabetes:
        penalty += 40

    # Hypertension
    if inputs.has_hypertension:
        penalty += 20

    # High cholesterol
    if inputs.has_high_cholesterol:
        penalty += 15

    # Family history
    if inputs.family_history_early_chd:
        penalty += 30

    return min(penalty, 100)


def calculate_ppg_penalty(inputs: HeartScoreInput) -> float:
    """Calculate PPG penalty from recent scan."""
    # Check if PPG is recent (< 7 days)
    if not inputs.ppg_scan_date:
        return 50  # No scan = moderate penalty

    days_since = (datetime.now() - inputs.ppg_scan_date).days
    if days_since > 7:
        return 50  # Old scan

    penalty = 0

    # Heart rate penalty
    if inputs.recent_hr_bpm:
        if inputs.recent_hr_bpm < 50:
            penalty += 20  # Too low
        elif inputs.recent_hr_bpm > 100:
            penalty += 30  # Too high
        else:
            penalty += 0

    # HRV penalty
    if inputs.recent_rmssd_ms:
        # This would ideally use age-adjusted norms
        if inputs.recent_rmssd_ms < 20:
            penalty += 40
        elif inputs.recent_rmssd_ms < 30:
            penalty += 20
        else:
            penalty += 0

    # Stress index penalty
    if inputs.recent_stress_index:
        penalty += inputs.recent_stress_index  # Already 0-100

    return min(penalty / 2, 100)  # Average and cap


def calculate_heart_score(inputs: HeartScoreInput) -> HeartScoreResult:
    """Calculate the P² Heart Score.

    This is a deterministic calculation - the LLM only explains, never computes.
    """
    # Count available inputs for confidence
    total_inputs = 25  # Total expected inputs
    available = 0

    if inputs.systolic_bp: available += 1
    if inputs.ldl: available += 1
    if inputs.hdl: available += 1
    if inputs.bmi: available += 1
    if inputs.waist_cm: available += 1
    if inputs.daily_steps: available += 1
    if inputs.sleep_hours: available += 1
    if inputs.stress_score: available += 1
    if inputs.smoking_status != "never": available += 1
    if inputs.alcohol_units_per_week: available += 1
    if inputs.has_hypertension: available += 1
    if inputs.has_diabetes: available += 1
    if inputs.family_history_early_chd: available += 1

    # CV risk + heart age require more data
    has_full_data = all([
        inputs.systolic_bp,
        inputs.total_chol,
        inputs.hdl,
    ])

    confidence_percent = min(available / total_inputs * 100, 100)

    # Determine confidence level
    if confidence_percent >= 70:
        confidence = "High"
    elif confidence_percent >= 40:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Calculate CV risk
    if has_full_data:
        if inputs.ethnicity:
            cv_result = calculate_qrisk3(
                age=inputs.age,
                sex=inputs.sex,
                systolic_bp=inputs.systolic_bp or 120,
                total_chol=inputs.total_chol or 180,
                hdl_chol=inputs.hdl or 50,
                smoking=inputs.smoking_status == "current",
                diabetes=inputs.has_diabetes,
                bp_treatment=inputs.on_bp_meds,
                ethnicity=inputs.ethnicity,
                family_history=inputs.family_history_early_chd,
                bmi=inputs.bmi or 25,
            )
            cv_risk = cv_result.risk_percent
        else:
            cv_result = calculate_framingham(
                age=inputs.age,
                sex=inputs.sex,
                total_chol=inputs.total_chol or 180,
                hdl_chol=inputs.hdl or 50,
                systolic_bp=inputs.systolic_bp or 120,
                bp_treatment=inputs.on_bp_meds,
                smoking=inputs.smoking_status == "current",
                diabetes=inputs.has_diabetes,
            )
            cv_risk = cv_result.risk_percent
    else:
        cv_risk = 10.0  # Default estimate
    cv_risk_penalty = cv_risk_to_penalty(cv_risk)

    # Calculate heart age
    heart_age_result = calculate_heart_age(
        age=inputs.age,
        sex=inputs.sex,
        systolic_bp=inputs.systolic_bp or 120,
        total_chol=inputs.total_chol,
        hdl_chol=inputs.hdl,
        smoking=inputs.smoking_status == "current",
        diabetes=inputs.has_diabetes,
        ethnicity=inputs.ethnicity or "white",
        family_history=inputs.family_history_early_chd,
        bmi=inputs.bmi or 25,
    )
    heart_age_penalty = heart_age_result.penalty

    # Lifestyle penalty
    lifestyle_penalty = calculate_lifestyle_penalty(inputs)

    # Condition penalty
    condition_penalty = calculate_condition_penalty(inputs)

    # PPG penalty
    ppg_penalty = calculate_ppg_penalty(inputs)

    # Determine if PPG is available
    has_ppg = inputs.ppg_scan_date and (datetime.now() - inputs.ppg_scan_date).days <= 7

    # Adjust weights if no PPG
    if has_ppg:
        weights = {
            "cv_risk": 0.35,
            "heart_age": 0.15,
            "lifestyle": 0.25,
            "condition": 0.15,
            "ppg": 0.10,
        }
    else:
        # Redistribute PPG weight proportionally
        total = 0.35 + 0.15 + 0.25 + 0.15  # 0.90
        weights = {
            "cv_risk": 0.35 / total * 0.90,
            "heart_age": 0.15 / total * 0.90,
            "lifestyle": 0.25 / total * 0.90,
            "condition": 0.15 / total * 0.90,
            "ppg": 0.10,  # This is the redistributed amount to conditions
        }

    # Calculate weighted penalty
    weighted_penalty = (
        weights["cv_risk"] * cv_risk_penalty +
        weights["heart_age"] * heart_age_penalty +
        weights["lifestyle"] * lifestyle_penalty +
        weights["condition"] * condition_penalty +
        weights["ppg"] * ppg_penalty
    )

    # Final score
    score = int(100 - weighted_penalty)
    score = max(0, min(100, score))

    # Score band
    for (low, high), (band, color) in SCORE_BANDS.items():
        if low <= score <= high:
            break

    return HeartScoreResult(
        score=score,
        score_band=band,
        score_color=color,
        confidence=confidence,
        confidence_percent=confidence_percent,
        cv_risk_percent=round(cv_risk, 1),
        cv_risk_penalty=round(cv_risk_penalty, 1),
        heart_age_gap=heart_age_result.gap_years,
        heart_age_penalty=round(heart_age_penalty, 1),
        lifestyle_penalty=round(lifestyle_penalty, 1),
        condition_penalty=round(condition_penalty, 1),
        ppg_penalty=round(ppg_penalty, 1),
        weights=weights,
        computed_at=datetime.now(),
    )