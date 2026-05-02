"""India-specific thresholds for heart health.

Indian guidelines often use lower thresholds than Western guidelines,
particularly for BMI, waist circumference, and cholesterol.
Sources:
- Indian Council of Medical Research (ICMR) guidelines
- National Cholesterol Education Program (NCEP) adaptations for India
- WHO South Asia guidelines
"""
from app.medical_knowledge.reference_ranges import get_bmi_status, get_waist_status


# BMI thresholds (Indian) - lower than WHO
# WHO: 18.5-23 = normal, 23-25 = overweight, 25+ = obese
# India: 18.5-23 = normal, 23-25 = overweight, 25+ = obese (with different cutoffs)
INDIAN_BMI_THRESHOLDS = {
    "underweight": 18.5,
    "normal": 23.0,
    "overweight": 25.0,
    "obese_1": 30.0,
    "obese_2": 35.0,
    "obese_3": 40.0,
}


# Waist circumference thresholds (Indian) - lower than Western
# Western: M<102cm, F<88cm
# Indian: M<90cm, F<80cm (higher risk at lower values)
INDIAN_WAIST_THRESHOLDS = {
    "male": {
        "healthy": 90,
        "increased_risk": 102,
        "high_risk": 120,
    },
    "female": {
        "healthy": 80,
        "increased_risk": 88,
        "high_risk": 100,
    },
}


# Cholesterol thresholds (Indian) - more aggressive
# NCEP: LDL <100 optimal, 100-129 near optimal, 130-159 borderline
# India: LDL <100 optimal, 100-130 moderate, 130+ high (due to higher CV risk)
INDIAN_LDL_THRESHOLDS = {
    "optimal": 100,
    "near_optimal": 130,
    "borderline": 160,
    "high": 190,
}


# HDL (lower thresholds for risk in Indians)
INDIAN_HDL_THRESHOLDS = {
    "high_risk": 40,  # Below this = high risk
    "moderate": 45,
    "acceptable": 50,
}


# Triglycerides (more liberal upper limit for Indians)
INDIAN_TG_THRESHOLDS = {
    "normal": 150,
    "borderline": 200,
    "high": 500,
}


# Blood Pressure (same as global for emergency, but lower for treatment)
# Same as ACC/AHA but Indian guidelines emphasize earlier intervention
INDIAN_BP_THRESHOLDS = {
    "normal_systolic": 120,
    "elevated_systolic": 130,
    "stage1_systolic": 140,
    "stage2_systolic": 160,
    "crisis_systolic": 180,
    "normal_diastolic": 80,
    "elevated_diastolic": 85,
    "stage1_diastolic": 90,
    "stage2_diastolic": 100,
    "crisis_diastolic": 120,
}


# LDL/HDL ratio - more important for South Asians
INDIAN_LDL_HDL_RATIO = {
    "optimal": 2.5,
    "acceptable": 3.0,
    "borderline": 4.0,
    "high": 5.0,
    "very_high": 6.0,
}


# Non-HDL cholesterol target (more practical)
INDIAN_NON_HDL_TARGET = {
    "lowest_risk": 100,
    "moderate_risk": 130,
    "high_risk": 160,
    "very_high_risk": 190,
}


# Lipoprotein(a) - particularly important for South Asians
# Elevated Lp(a) > 50 mg/dL is independently atherogenic
LP_A_THRESHOLD = 50  # mg/dL


# hsCRP (inflammation marker)
HS_CRP_THRESHOLDS = {
    "low_risk": 1.0,  # mg/L
    "moderate_risk": 3.0,
    "high_risk": 10.0,
}


# HbA1c (diabetes/diabetes prevention)
INDIAN_HBA1C_THRESHOLDS = {
    "normal": 5.6,  # %
    "prediabetes": 6.5,
    "diabetes": 6.5,  # Above this = diabetes
}


def get_indian_bmi_status(bmi: float) -> tuple[str, str]:
    """Get BMI status using Indian thresholds."""
    if bmi < 18.5:
        return "Underweight", "#F59E0B"
    elif bmi < 23:
        return "Normal", "#10B981"
    elif bmi < 25:
        return "Overweight", "#F59E0B"
    elif bmi < 30:
        return "Obese Class 1", "#F97366"
    elif bmi < 35:
        return "Obese Class 2", "#EF4444"
    else:
        return "Obese Class 3", "#DC2626"


def get_indian_waist_status(waist_cm: float, sex: str) -> tuple[str, str]:
    """Get waist status using Indian thresholds."""
    sex_key = "male" if sex.lower() in ["m", "male", "man"] else "female"
    thresholds = INDIAN_WAIST_THRESHOLDS.get(sex_key, INDIAN_WAIST_THRESHOLDS["male"])

    if waist_cm < thresholds["healthy"]:
        return "Healthy", "#10B981"
    elif waist_cm < thresholds["increased_risk"]:
        return "Increased Risk", "#F59E0B"
    else:
        return "High Risk", "#EF4444"


def get_indian_ldl_status(ldl: float) -> tuple[str, str]:
    """Get LDL status using Indian thresholds."""
    if ldl < INDIAN_LDL_THRESHOLDS["optimal"]:
        return "Optimal", "#10B981"
    elif ldl < INDIAN_LDL_THRESHOLDS["near_optimal"]:
        return "Near Optimal", "#10B981"
    elif ldl < INDIAN_LDL_THRESHOLDS["borderline"]:
        return "Moderate", "#F59E0B"
    elif ldl < INDIAN_LDL_THRESHOLDS["high"]:
        return "High", "#F97366"
    else:
        return "Very High", "#EF4444"


def use_indian_thresholds() -> bool:
    """Check if Indian thresholds should be used.

    This can be based on user preference or ethnicity.
    """
    return True  # Default to Indian thresholds for Indian users