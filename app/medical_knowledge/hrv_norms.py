"""HRV reference values stratified by age and sex.

Sources:
- Task Force of the European Society of Cardiology (1996)
- Custom population studies (scaled for age decline)
- U.S. normative data compilation

RMSSD is the primary HRV metric - represents parasympathetic activity.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class HRVNorm:
    """HRV normal reference values."""
    median: float  # ms
    low: float  # 25th percentile
    high: float  # 75th percentile
    unit: str = "ms"


# RMSSD norms by age group and sex (in ms)
# Based on population studies, scaled for age-related decline
HRV_NORMS = {
    ("M", 20, 29): HRVNorm(median=55, low=35, high=75),
    ("M", 30, 39): HRVNorm(median=45, low=28, high=62),
    ("M", 40, 49): HRVNorm(median=38, low=22, high=52),
    ("M", 50, 59): HRVNorm(median=30, low=18, high=42),
    ("M", 60, 69): HRVNorm(median=25, low=15, high=35),
    ("M", 70, 100): HRVNorm(median=20, low=12, high=28),
    ("F", 20, 29): HRVNorm(median=60, low=40, high=80),
    ("F", 30, 39): HRVNorm(median=52, low=32, high=70),
    ("F", 40, 49): HRVNorm(median=44, low=26, high=60),
    ("F", 50, 59): HRVNorm(median=36, low=20, high=50),
    ("F", 60, 69): HRVNorm(median=28, low=16, high=40),
    ("F", 70, 100): HRVNorm(median=22, low=14, high=30),
}


def get_hrv_norm(age: int, sex: str) -> HRVNorm:
    """Get HRV norm for given age and sex."""
    sex_key = "M" if sex.lower() in ["m", "male", "man"] else "F"

    # Find appropriate age bracket
    for (s, low_age, high_age), norm in HRV_NORMS.items():
        if s == sex_key and low_age <= age <= high_age:
            return norm

    # Default to 40-49 bracket if not found
    return HRV_NORMS.get((sex_key, 40, 49), HRVNorm(median=35, low=20, high=50))


def get_hrv_status(rmssd: float, age: int, sex: str) -> tuple[str, str]:
    """Get HRV status from RMSSD value.

    Returns: (status, color)
    """
    norm = get_hrv_norm(age, sex)

    if rmssd >= norm.high:
        return "Excellent", "#10B981"
    elif rmssd >= norm.median:
        return "Good", "#10B981"
    elif rmssd >= norm.low:
        return "Average", "#F59E0B"
    elif rmssd >= norm.low * 0.7:
        return "Below Average", "#F97366"
    else:
        return "Low", "#EF4444"


def hrv_to_penalty(rmssd: float, age: int, sex: str) -> float:
    """Convert RMSSD to HRV penalty (0-100).

    Above median = 0 penalty
    Below 25th percentile = higher penalty
    """
    norm = get_hrv_norm(age, sex)

    if rmssd >= norm.median:
        return 0

    # Linear scale from median to 0
    if rmssd <= 0:
        return 100

    # Penalty increases as RMSSD drops below median
    ratio = rmssd / norm.median
    return (1 - ratio) * 100


# SDNN norms (total HRV - less age-sensitive)
SDNN_NORMS = {
    ("M", 20, 29): HRVNorm(median=65, low=45, high=90),
    ("M", 30, 39): HRVNorm(median=55, low=38, high=75),
    ("M", 40, 49): HRVNorm(median=48, low=32, high=65),
    ("M", 50, 59): HRVNorm(median=40, low=25, high=55),
    ("M", 60, 69): HRVNorm(median=32, low=20, high=45),
    ("M", 70, 100): HRVNorm(median=25, low=15, high=35),
    ("F", 20, 29): HRVNorm(median=70, low=48, high=95),
    ("F", 30, 39): HRVNorm(median=60, low=40, high=82),
    ("F", 40, 49): HRVNorm(median=52, low=34, high=70),
    ("F", 50, 59): HRVNorm(median=42, low=26, high=58),
    ("F", 60, 69): HRVNorm(median=34, low=20, high=48),
    ("F", 70, 100): HRVNorm(median=26, low=16, high=38),
}


def get_sdnn_norm(age: int, sex: str) -> HRVNorm:
    """Get SDNN norm for given age and sex."""
    sex_key = "M" if sex.lower() in ["m", "male", "man"] else "F"

    for (s, low_age, high_age), norm in SDNN_NORMS.items():
        if s == sex_key and low_age <= age <= high_age:
            return norm

    return SDNN_NORMS.get((sex_key, 40, 49), HRVNorm(median=45, low=28, high=62))


# pNN50 norms (percentage of successive intervals >50ms)
PNN50_NORMS = {
    ("M", 20, 29): HRVNorm(median=20, low=8, high=35),
    ("M", 30, 39): HRVNorm(median=15, low=5, high=28),
    ("M", 40, 49): HRVNorm(median=10, low=3, high=20),
    ("M", 50, 59): HRVNorm(median=6, low=2, high=12),
    ("M", 60, 69): HRVNorm(median=4, low=1, high=8),
    ("M", 70, 100): HRVNorm(median=2, low=0, high=5),
    ("F", 20, 29): HRVNorm(median=25, low=10, high=42),
    ("F", 30, 39): HRVNorm(median=20, low=7, high=35),
    ("F", 40, 49): HRVNorm(median=14, low=4, high=25),
    ("F", 50, 59): HRVNorm(median=9, low=3, high=16),
    ("F", 60, 69): HRVNorm(median=5, low=1, high=10),
    ("F", 70, 100): HRVNorm(median=3, low=0, high=6),
}


def get_pnn50_norm(age: int, sex: str) -> HRVNorm:
    """Get pNN50 norm for given age and sex."""
    sex_key = "M" if sex.lower() in ["m", "male", "man"] else "F"

    for (s, low_age, high_age), norm in PNN50_NORMS.items():
        if s == sex_key and low_age <= age <= high_age:
            return norm

    return PNN50_NORMS.get((sex_key, 40, 49), HRVNorm(median=10, low=3, high=20))