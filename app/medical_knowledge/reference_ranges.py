"""Reference ranges for heart health metrics."""
from dataclasses import dataclass
from enum import Enum


class BPStatus(str, Enum):
    OPTIMAL = "Optimal"
    NORMAL = "Normal"
    ELEVATED = "Elevated"
    STAGE_1_HTN = "Stage 1"
    STAGE_2_HTN = "Stage 2"


class CholesterolStatus(str, Enum):
    OPTIMAL = "Optimal"
    NEAR_OPTIMAL = "Near Optimal"
    BORDERLINE = "Borderline"
    HIGH = "High"
    VERY_HIGH = "Very High"


class RHRStatus(str, Enum):
    ATHLETIC = "Athletic"
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    POOR = "Poor"


@dataclass
class ReferenceRange:
    low: float
    high: float
    unit: str
    status: str


# Blood Pressure (ACC/AHA 2017 guidelines)
# Systolic
BP_SYSTOLIC = {
    (0, 120): ("Optimal", "#10B981"),
    (120, 130): ("Normal", "#10B981"),
    (130, 140): ("Elevated", "#F59E0B"),
    (140, 160): ("Stage 1 HTN", "#F97366"),
    (160, 180): ("Stage 2 HTN", "#EF4444"),
    (180, 500): ("Hypertensive Crisis", "#DC2626"),
}

# Diastolic
BP_DIASTOLIC = {
    (0, 80): ("Optimal", "#10B981"),
    (80, 85): ("Normal", "#10B981"),
    (85, 90): ("Elevated", "#F59E0B"),
    (90, 100): ("Stage 1 HTN", "#F97366"),
    (100, 120): ("Stage 2 HTN", "#EF4444"),
    (120, 500): ("Hypertensive Crisis", "#DC2626"),
}


def get_bp_status(systolic: int, diastolic: int) -> tuple[str, str]:
    """Get BP status and color from systolic/diastolic values."""
    sys_status = "Normal"
    dia_status = "Normal"
    color = "#10B981"

    for (low, high), (status, c) in BP_SYSTOLIC.items():
        if low <= systolic < high:
            sys_status = status
            color = c
            break

    for (low, high), (status, c) in BP_DIASTOLIC.items():
        if low <= diastolic < high:
            dia_status = status
            # Use the higher-risk color
            if c == "#EF4444" or c == "#DC2626":
                color = c
            elif c == "#F97366" and color != "#EF4444":
                color = c
            elif c == "#F59E0B" and color not in ["#EF4444", "#F97366"]:
                color = c
            break

    # Combined status
    if "Crisis" in sys_status or "Crisis" in dia_status:
        return "Hypertensive Crisis", "#DC2626"
    elif "Stage 2" in sys_status or "Stage 2" in dia_status:
        return "Stage 2 Hypertension", "#EF4444"
    elif "Stage 1" in sys_status or "Stage 1" in dia_status:
        return "Stage 1 Hypertension", "#F97366"
    elif "Elevated" in sys_status or "Elevated" in dia_status:
        return "Elevated", "#F59E0B"
    elif "Normal" in sys_status:
        return "Normal", "#10B981"
    else:
        return "Optimal", "#10B981"


# Cholesterol (ACC/AHA + Indian targets)
# LDL: mg/dL
LDL_RANGES = {
    (0, 70): ("Optimal", "#10B981"),
    (70, 100): ("Near Optimal", "#10B981"),
    (100, 130): ("Borderline", "#F59E0B"),
    (130, 160): ("High", "#F97366"),
    (160, 500): ("Very High", "#EF4444"),
}

# HDL: mg/dL (higher is better)
HDL_RANGES = {
    (0, 40): ("Low (Risk)", "#EF4444"),
    (40, 50): ("Borderline", "#F59E0B"),
    (50, 60): ("Good", "#10B981"),
    (60, 200): ("Excellent", "#10B981"),
}

# Triglycerides: mg/dL
TG_RANGES = {
    (0, 100): ("Optimal", "#10B981"),
    (100, 150): ("Normal", "#10B981"),
    (150, 200): ("Borderline", "#F59E0B"),
    (200, 500): ("High", "#F97366"),
    (500, 5000): ("Very High", "#EF4444"),
}

# Total Cholesterol
TC_RANGES = {
    (0, 150): ("Desirable", "#10B981"),
    (150, 200): ("Borderline", "#F59E0B"),
    (200, 240): ("High", "#F97366"),
    (240, 1000): ("Very High", "#EF4444"),
}

# Total/HDL Ratio (important for South Asians)
TC_HDL_RANGES = {
    (0, 3.0): ("Optimal", "#10B981"),
    (3.0, 4.0): ("Average", "#10B981"),
    (4.0, 5.0): ("Increased Risk", "#F59E0B"),
    (5.0, 6.0): ("High Risk", "#F97366"),
    (6.0, 100): ("Very High Risk", "#EF4444"),
}


def get_cholesterol_status(value: float, metric: str) -> tuple[str, str]:
    """Get cholesterol status from value and metric type."""
    ranges = {
        "ldl": LDL_RANGES,
        "hdl": HDL_RANGES,
        "tg": TG_RANGES,
        "tc": TC_RANGES,
        "tc_hdl": TC_HDL_RANGES,
    }.get(metric, LDL_RANGES)

    for (low, high), (status, color) in ranges.items():
        if low <= value < high:
            return status, color
    return "Unknown", "#6B7280"


# Resting Heart Rate (no official guidelines, clinical consensus)
RHR_RANGES = {
    (0, 50): ("Athletic", "#10B981"),
    (50, 60): ("Excellent", "#10B981"),
    (60, 70): ("Good", "#10B981"),
    (70, 80): ("Average", "#F59E0B"),
    (80, 100): ("Elevated", "#F97366"),
    (100, 200): ("High", "#EF4444"),
}


def get_rhr_status(bpm: int) -> tuple[str, str]:
    """Get RHR status from BPM."""
    for (low, high), (status, color) in RHR_RANGES.items():
        if low <= bpm < high:
            return status, color
    return "Unknown", "#6B7280"


# BMI (WHO + Indian modified)
BMI_RANGES = {
    (0, 18.5): ("Underweight", "#F59E0B"),
    (18.5, 23): ("Normal", "#10B981"),
    (23, 25): ("Overweight", "#F59E0B"),
    (25, 30): ("Obese Class 1", "#F97366"),
    (30, 35): ("Obese Class 2", "#EF4444"),
    (35, 100): ("Obese Class 3", "#DC2626"),
}


# Waist (Indian thresholds - lower for South Asians)
WAIST_RANGES = {
    ("M", 0, 90): ("Healthy", "#10B981"),
    ("M", 90, 102): ("Increased Risk", "#F59E0B"),
    ("M", 102, 200): ("High Risk", "#EF4444"),
    ("F", 0, 80): ("Healthy", "#10B981"),
    ("F", 80, 88): ("Increased Risk", "#F59E0B"),
    ("F", 88, 200): ("High Risk", "#EF4444"),
}


def get_bmi_status(bmi: float) -> tuple[str, str]:
    """Get BMI status."""
    for (low, high), (status, color) in BMI_RANGES.items():
        if low <= bmi < high:
            return status, color
    return "Unknown", "#6B7280"


def get_waist_status(waist_cm: float, sex: str) -> tuple[str, str]:
    """Get waist risk status."""
    sex_key = "M" if sex.lower() in ["m", "male", "man"] else "F"
    for (s, low, high), (status, color) in WAIST_RANGES.items():
        if s == sex_key and low <= waist_cm < high:
            return status, color
    return "Unknown", "#6B7280"


# Step goals (personalized)
def get_step_goal(current_avg: int) -> int:
    """Get personalized step goal."""
    return min(current_avg + 1500, 12000)


# Sleep hours
SLEEP_RANGES = {
    (0, 5): ("Insufficient", "#EF4444"),
    (5, 6): ("Below Recommended", "#F59E0B"),
    (6, 7): ("Borderline", "#10B981"),
    (7, 9): ("Optimal", "#10B981"),
    (9, 24): ("Excessive", "#F59E0B"),
}


def get_sleep_status(hours: float) -> tuple[str, str]:
    """Get sleep status."""
    for (low, high), (status, color) in SLEEP_RANGES.items():
        if low <= hours < high:
            return status, color
    return "Unknown", "#6B7280"


# Stress scale (1-10)
STRESS_RANGES = {
    (0, 3): ("Low", "#10B981"),
    (3, 5): ("Moderate", "#F59E0B"),
    (5, 7): ("Elevated", "#F97366"),
    (7, 11): ("High", "#EF4444"),
}


def get_stress_status(score: int) -> tuple[str, str]:
    """Get stress status from 1-10 score."""
    for (low, high), (status, color) in STRESS_RANGES.items():
        if low <= score < high:
            return status, color
    return "Unknown", "#6B7280"


# CV Risk categories
CV_RISK_RANGES = {
    (0, 5): ("Low", "#10B981"),
    (5, 10): ("Borderline", "#F59E0B"),
    (10, 20): ("Moderate", "#F97366"),
    (20, 100): ("High", "#EF4444"),
}


def get_cv_risk_status(risk_pct: float) -> tuple[str, str]:
    """Get 10-year CV risk status."""
    for (low, high), (status, color) in CV_RISK_RANGES.items():
        if low <= risk_pct < high:
            return status, color
    return "Unknown", "#6B7280"