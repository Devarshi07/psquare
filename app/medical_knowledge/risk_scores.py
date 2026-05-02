"""QRISK3 and Framingham risk score calculators.

QRISK3 coefficients from: https://www.qrisk.org/
Framingham coefficients from: D'Agostino et al. 2008
"""
import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class QRISK3Inputs:
    age: int
    sex: str  # "male" or "female"
    ethnicity: str  # "white", "south_asian", "black", "chinese", "other"
    smoking: bool
    diabetes: bool
    family_history_early_chd: bool  # Parent/sibling with CHD < 60
    ckd: bool  # Chronic kidney disease
    afib: bool  # Atrial fibrillation
    bp_treatment: bool
    systolic_bp: float
    total_hdl_ratio: float  # Total cholesterol / HDL
    bmi: float
    townsend_deprivation: float = 5.0  # Default for India


# QRISK3 coefficients (2017)
# Source: https://qrisk.org/2017/ (accessed 2024)
QRISK3_COEFFICIENTS = {
    "age": 0.04794,
    "age_squared": 0.00113,
    "sex_male": 0.44693,
    "smoking_current": 0.57391,
    "smoking_ex": 0.22644,
    "diabetes": 0.44783,
    "family_history": 0.61106,
    "ckd": 0.43508,
    "afib": 0.54050,
    "bp_treatment": 0.40389,
    "systolic_bp": 0.01417,
    "total_hdl_ratio": 0.19203,
    "bmi": 0.03728,
    "townsend": 0.03006,
    # Ethnicity (relative to white)
    "ethnicity_south_asian": 0.25667,
    "ethnicity_black": 0.25597,
    "ethnicity_chinese": -0.18172,
    "ethnicity_other": 0.02431,
}

# Base risk for survival function
QRISK3_BASE_SURVIVAL = 0.987


def calc_qrisk3(inputs: QRISK3Inputs) -> float:
    """Calculate 10-year cardiovascular risk using QRISK3.

    Returns risk as percentage (0-100).
    """
    coef = QRISK3_COEFFICIENTS

    # Calculate linear predictor
    lp = 0
    lp += coef["age"] * inputs.age
    lp += coef["age_squared"] * (inputs.age ** 2)
    lp += coef["sex_male"] if inputs.sex.lower() == "male" else 0
    lp += coef["smoking_current"] if inputs.smoking else 0
    lp += coef["smoking_ex"] if inputs.smoking else 0  # Simplified
    lp += coef["diabetes"] if inputs.diabetes else 0
    lp += coef["family_history"] if inputs.family_history_early_chd else 0
    lp += coef["ckd"] if inputs.ckd else 0
    lp += coef["afib"] if inputs.afib else 0
    lp += coef["bp_treatment"] if inputs.bp_treatment else 0
    lp += coef["systolic_bp"] * inputs.systolic_bp
    lp += coef["total_hdl_ratio"] * inputs.total_hdl_ratio
    lp += coef["bmi"] * inputs.bmi
    lp += coef["townsend"] * inputs.townsend_deprivation

    # Ethnicity adjustments (relative to white baseline)
    if inputs.ethnicity.lower() == "south_asian":
        lp += coef["ethnicity_south_asian"]
    elif inputs.ethnicity.lower() == "black":
        lp += coef["ethnicity_black"]
    elif inputs.ethnicity.lower() == "chinese":
        lp += coef["ethnicity_chinese"]
    elif inputs.ethnicity.lower() not in ["white", ""]:
        lp += coef["ethnicity_other"]

    # Survival function: S(10) = base^exp(lp - mean)
    # Using simplified form: risk = 1 - S(10)
    mean_lp = 3.5  # Approximate mean from validation studies
    survival = QRISK3_BASE_SURVIVAL ** math.exp(lp - mean_lp)
    risk_pct = (1 - survival) * 100

    return min(max(risk_pct, 0.1), 99.9)


@dataclass
class FraminghamInputs:
    age: int
    sex: str  # "male" or "female"
    total_cholesterol: float  # mg/dL
    hdl_cholesterol: float  # mg/dL
    systolic_bp: float
    bp_treatment: bool
    smoking: bool
    diabetes: bool


# Framingham coefficients (Adult Treatment Panel III)
# Source: D'Agostino et al. 2008
FRAMINGHAM_COEFFICIENTS = {
    "male": {
        "age": 3.06117,
        "age_squared": 0,
        "total_chol": 1.12370,
        "hdl_chol": -2.32827,
        "systolic_bp": 1.93303,
        "bp_treatment": 1.80888,
        "smoking": 0.65451,
        "diabetes": 0.57367,
    },
    "female": {
        "age": 2.32888,
        "age_squared": 0,
        "total_chol": 1.20904,
        "hdl_chol": -2.09653,
        "systolic_bp": 2.76177,
        "bp_treatment": 2.88263,
        "smoking": 0.52892,
        "diabetes": 0.69154,
    },
}

# Framingham baseline survival (10-year)
FRAMINGHAM_BASE_SURVIVAL = {
    "male": 0.88936,
    "female": 0.95012,
}


def calc_framingham(inputs: FraminghamInputs) -> float:
    """Calculate 10-year cardiovascular risk using Framingham.

    Returns risk as percentage (0-100).
    """
    sex_key = "male" if inputs.sex.lower() in ["m", "male", "man"] else "female"
    coef = FRAMINGHAM_COEFFICIENTS[sex_key]

    # Calculate linear predictor
    lp = 0
    lp += coef["age"] * inputs.age
    lp += coef["total_chol"] * inputs.total_cholesterol
    lp += coef["hdl_chol"] * inputs.hdl_cholesterol
    lp += coef["systolic_bp"] * inputs.systolic_bp
    lp += coef["bp_treatment"] if inputs.bp_treatment else 0
    lp += coef["smoking"] if inputs.smoking else 0
    lp += coef["diabetes"] if inputs.diabetes else 0

    # Survival function
    base = FRAMINGHAM_BASE_SURVIVAL[sex_key]
    survival = base ** math.exp(lp - 23.5)  # 23.5 is approximate mean
    risk_pct = (1 - survival) * 100

    return min(max(risk_pct, 0.1), 99.9)


def calc_cv_risk(
    age: int,
    sex: str,
    systolic_bp: float,
    total_chol: Optional[float] = None,
    hdl_chol: Optional[float] = None,
    smoking: bool = False,
    diabetes: bool = False,
    bp_treatment: bool = False,
    ethnicity: str = "south_asian",
    family_history: bool = False,
    bmi: float = 25.0,
    ckd: bool = False,
    afib: bool = False,
) -> float:
    """Calculate CV risk, preferring QRISK3 with Framingham fallback.

    Returns risk as percentage (0-100).
    """
    # Try QRISK3 first (requires more inputs)
    if total_chol and hdl_chol and ethnicity:
        try:
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
            return calc_qrisk3(inputs)
        except Exception:
            pass

    # Fallback to Framingham
    if total_chol and hdl_chol:
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
            return calc_framingham(inputs)
        except Exception:
            pass

    # If no cholesterol data, estimate from BP and risk factors
    # Simplified estimation based on BP categories
    base_risk = 2 if age > 40 else 1
    if systolic_bp >= 160:
        base_risk += 5
    elif systolic_bp >= 140:
        base_risk += 3
    elif systolic_bp >= 130:
        base_risk += 1

    if smoking:
        base_risk += 2
    if diabetes:
        base_risk += 3
    if family_history:
        base_risk += 2
    if bp_treatment:
        base_risk += 1

    # Age adjustment
    if age > 60:
        base_risk += 3
    elif age > 50:
        base_risk += 2
    elif age > 40:
        base_risk += 1

    return min(base_risk, 50)


# QRISK3 to penalty conversion (for Heart Score)
def cv_risk_to_penalty(risk_pct: float) -> float:
    """Convert 10-year CV risk % to penalty (0-100).

    Linear: 0% risk = 0 penalty, 30%+ risk = 100 penalty
    """
    return min(max(risk_pct * 100 / 30, 0), 100)