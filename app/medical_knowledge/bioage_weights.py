"""Biological age weights (inspired by PhenoAge).

These weights combine face age estimate + lifestyle questionnaire
to produce a final biological age estimate.

This is NOT a clinical biomarker - it's a wellness estimation tool.
"""
from dataclasses import dataclass


@dataclass
class BioAgeWeight:
    """Weight for a biological age component."""
    factor: str
    weight: float  # 0-1, weight in final calculation
    max_years: int  # Maximum years this can add/subtract


# Face age influence (60% weight)
# The face model estimates visible age from skin/face features
FACE_AGE_WEIGHT = 0.6

# Lifestyle questionnaire influence (40% weight)
LIFESTYLE_WEIGHT = 0.4


# Questionnaire factor weights (must sum to 1.0 within lifestyle)
QUESTIONNAIRE_WEIGHTS = {
    "sleep": BioAgeWeight("sleep", 0.30, 10),  # Sleep has big impact
    "sun": BioAgeWeight("sun", 0.15, 5),  # Photoaging
    "sugar": BioAgeWeight("sugar", 0.20, 8),  # Glycation
    "smoking_alcohol": BioAgeWeight("smoking_alcohol", 0.25, 10),  # Major drivers
    "stress_activity": BioAgeWeight("stress_activity", 0.10, 5),  # Moderate impact
}


# Sleep adjustment (years added per category)
SLEEP_ADJUSTMENTS = {
    (0, 5): 8,  # <5 hours: +8 years
    (5, 6): 4,  # 5-6 hours: +4 years
    (6, 7): 1,  # 6-7 hours: +1 year
    (7, 8): 0,  # 7-8 hours: baseline
    (8, 100): -1,  # 8+ hours: -1 year (oversleeping slightly worse)
}


# Sun exposure adjustment
SUN_ADJUSTMENTS = {
    "none": 4,  # No sun: +4 years
    "<15min": 2,  # Little sun: +2 years
    "15-60min": 0,  # Moderate: baseline
    "1hr+": -1,  # Good sun: -1 year (with sunscreen note)
}


# Sugar/processed food adjustment
SUGAR_ADJUSTMENTS = {
    "daily": 6,  # Daily sweets: +6 years
    "3-5x": 3,  # Few times/week: +3 years
    "1-2x": 1,  # Occasional: +1 year
    "rarely": 0,  # Rare: baseline
}


# Smoking + alcohol adjustment
SMOKING_ALCOHOL_ADJUSTMENTS = {
    "both": 8,  # Both: +8 years
    "smoke_only": 10,  # Smoking: +10 years
    "drink_only": 3,  # Alcohol only: +3 years
    "neither": 0,  # Neither: baseline
}


# Stress + activity adjustment
STRESS_ACTIVITY_ADJUSTMENTS = {
    "exhausted": 6,  # Exhausted: +6 years
    "tired": 3,  # Tired: +3 years
    "ok": 0,  # OK: baseline
    "energized": -2,  # Energized: -2 years
}


# Objective data adjustments (used if available)
OBJECTIVE_ADJUSTMENTS = {
    "bp_elevated": 2,  # Stage 1+ HTN: +2 years
    "ldl_high": 3,  # LDL > 130: +3 years
    "hdl_low": 2,  # HDL < 40: +2 years
    "hbA1c_prediabetic": 2,  # HbA1c 5.7-6.4: +2 years
    "hbA1c_diabetic": 4,  # HbA1c 6.5+: +4 years
    "smoker": 5,  # Current smoker: +5 years
    "former_smoker": 2,  # Former smoker: +2 years
    "obese": 3,  # BMI 30+: +3 years
    "high_waist": 2,  # High waist risk: +2 years
    "low_hrv": 2,  # RMSSD below 25th percentile: +2 years
}


def calc_questionnaire_adjustment(answers: dict) -> float:
    """Calculate lifestyle adjustment from questionnaire answers.

    Args:
        answers: Dict with keys: sleep, sun, sugar, smoking_alcohol, stress_activity

    Returns:
        Years to add (positive) or subtract (negative) from chronological age
    """
    total = 0

    # Sleep
    sleep_hours = answers.get("sleep", "7-8")
    for (low, high), years in SLEEP_ADJUSTMENTS.items():
        if sleep_hours in ["<5", "5-6", "6-7", "7-8", "8+"]:
            if sleep_hours == "<5":
                total += years
                break
            # Parse and compare
            try:
                if sleep_hours == "8+":
                    if high >= 100:
                        total += years
                        break
            except:
                pass

    # Map answer strings to adjustments
    sleep_map = {"<5": 8, "5-6": 4, "6-7": 1, "7-8": 0, "8+": -1}
    total += sleep_map.get(answers.get("sleep", "7-8"), 0)

    sun_map = {"none": 4, "<15min": 2, "15-60min": 0, "1hr+": -1}
    total += sun_map.get(answers.get("sun", "15-60min"), 0)

    sugar_map = {"daily": 6, "3-5x": 3, "1-2x": 1, "rarely": 0}
    total += sugar_map.get(answers.get("sugar", "rarely"), 0)

    sa_map = {"both": 8, "smoke_only": 10, "drink_only": 3, "neither": 0}
    total += sa_map.get(answers.get("smoking_alcohol", "neither"), 0)

    sa2_map = {"exhausted": 6, "tired": 3, "ok": 0, "energized": -2}
    total += sa2_map.get(answers.get("stress_activity", "ok"), 0)

    return total


def calc_objective_adjustment(
    systolic_bp: float = None,
    ldl: float = None,
    hdl: float = None,
    hbA1c: float = None,
    smoking_status: str = None,
    bmi: float = None,
    waist: float = None,
    rmssd: float = None,
    age: int = None,
    sex: str = None,
) -> float:
    """Calculate objective data adjustment.

    Args:
        Various optional metrics. Pass None if not available.

    Returns:
        Years to add from objective data
    """
    total = 0

    if systolic_bp and systolic_bp >= 140:
        total += OBJECTIVE_ADJUSTMENTS["bp_elevated"]
    elif systolic_bp and systolic_bp >= 130:
        total += 1  # Elevated

    if ldl and ldl >= 130:
        total += OBJECTIVE_ADJUSTMENTS["ldl_high"]
    elif ldl and ldl >= 100:
        total += 1

    if hdl and hdl < 40:
        total += OBJECTIVE_ADJUSTMENTS["hdl_low"]

    if hbA1c:
        if hbA1c >= 6.5:
            total += OBJECTIVE_ADJUSTMENTS["hbA1c_diabetic"]
        elif hbA1c >= 5.7:
            total += OBJECTIVE_ADJUSTMENTS["hbA1c_prediabetic"]

    if smoking_status:
        if smoking_status.lower() == "current":
            total += OBJECTIVE_ADJUSTMENTS["smoker"]
        elif smoking_status.lower() == "former":
            total += OBJECTIVE_ADJUSTMENTS["former_smoker"]

    if bmi and bmi >= 30:
        total += OBJECTIVE_ADJUSTMENTS["obese"]

    if waist and (waist >= 102 or waist >= 88):  # Male/Female threshold
        total += OBJECTIVE_ADJUSTMENTS["high_waist"]

    # HRV check (requires age/sex for norm)
    if rmssd and age and sex:
        from app.medical_knowledge.hrv_norms import get_hrv_norm
        norm = get_hrv_norm(age, sex)
        if rmssd < norm.low:
            total += OBJECTIVE_ADJUSTMENTS["low_hrv"]

    return total


def calc_biological_age(
    chronological_age: int,
    face_age_estimate: float = None,
    questionnaire_answers: dict = None,
    objective_data: dict = None,
) -> float:
    """Calculate final biological age.

    Formula:
    biological_age = chronological_age
                   + 0.6 * (face_age - chronological_age)
                   + lifestyle_adjustment
                   + objective_data_adjustment
    """
    total_adjustment = 0

    # Face age component
    if face_age_estimate:
        face_gap = face_age_estimate - chronological_age
        total_adjustment += FACE_AGE_WEIGHT * face_gap

    # Lifestyle questionnaire
    if questionnaire_answers:
        lifestyle_adj = calc_questionnaire_adjustment(questionnaire_answers)
        total_adjustment += LIFESTYLE_WEIGHT * (lifestyle_adj / 5)  # Normalize to 0-2 range

    # Objective data
    if objective_data:
        obj_adj = calc_objective_adjustment(**objective_data)
        total_adjustment += obj_adj * 0.2  # Slight weight

    return chronological_age + total_adjustment