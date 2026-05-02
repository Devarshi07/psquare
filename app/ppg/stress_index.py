"""Stress/Fatigue Index calculation.

Composite 0-100 (higher = more stress/fatigue), computed from:
- HR vs personal resting baseline
- RMSSD vs age/sex-adjusted norm
- HR/HRV ratio
- Pre-scan questionnaire metadata
"""
import structlog
from typing import Optional

from app.medical_knowledge.hrv_norms import get_hrv_norm

log = structlog.get_logger()


def calc_stress_index(
    hr_bpm: float,
    rmssd_ms: float,
    age: int,
    sex: str,
    resting_hr_baseline: float = 70.0,
    pre_scan_context: dict = None,
) -> int:
    """Calculate stress/fatigue index (0-100).

    Args:
        hr_bpm: Heart rate from PPG
        rmssd_ms: RMSSD from PPG
        age: User age
        sex: User sex
        resting_hr_baseline: User's typical resting HR
        pre_scan_context: Dict with keys: caffeine, just_exercised, anxious, state

    Returns:
        Stress index 0-100
    """
    pre_scan_context = pre_scan_context or {}

    # Component 1: HR elevation (0-30 points)
    hr_elevation = hr_bpm - resting_hr_baseline
    if hr_elevation <= 0:
        hr_score = 0
    elif hr_elevation <= 10:
        hr_score = hr_elevation * 1.5  # 0-15
    elif hr_elevation <= 20:
        hr_score = 15 + (hr_elevation - 10) * 1.5  # 15-30
    else:
        hr_score = 30
    hr_score = min(hr_score, 30)

    # Component 2: HRV vs norm (0-30 points)
    norm = get_hrv_norm(age, sex)
    if rmssd_ms >= norm.median:
        hrv_score = 0
    elif rmssd_ms >= norm.low:
        hrv_score = (1 - (rmssd_ms - norm.low) / (norm.median - norm.low)) * 20
    else:
        hrv_score = 20 + (1 - rmssd_ms / norm.low) * 10
    hrv_score = min(hrv_score, 30)

    # Component 3: HR/HRV ratio as stress proxy (0-20 points)
    if rmssd_ms > 0:
        ratio = hr_bpm / rmssd_ms
        # Normal ratio is roughly 1.5-3. Higher = more stress
        if ratio <= 2:
            ratio_score = 0
        elif ratio <= 4:
            ratio_score = (ratio - 2) * 10
        else:
            ratio_score = 20
        ratio_score = min(ratio_score, 20)
    else:
        ratio_score = 20

    # Component 4: Pre-scan context (0-20 points)
    context_score = 0

    if pre_scan_context.get("caffeine"):
        context_score += 8
    if pre_scan_context.get("just_exercised"):
        context_score += 10
    if pre_scan_context.get("anxious"):
        context_score += 8

    # State-based adjustments
    state = pre_scan_context.get("state", "").lower()
    if state == "stressed":
        context_score += 8
    elif state == "just exercised":
        context_score += 10
    elif state == "just woke up":
        context_score -= 5  # Lower stress if just woke
    elif state == "calm":
        context_score -= 3

    context_score = max(0, min(context_score, 20))

    # Total score
    total = int(hr_score + hrv_score + ratio_score + context_score)
    return min(max(total, 0), 100)


def get_stress_band(stress_index: int) -> tuple[str, str]:
    """Get stress band and color."""
    if stress_index <= 30:
        return "Low", "#10B981"
    elif stress_index <= 60:
        return "Moderate", "#F59E0B"
    else:
        return "High", "#EF4444"


def interpret_stress_index(
    stress_index: int,
    hr_bpm: float,
    rmssd_ms: float,
    age: int,
    sex: str,
) -> str:
    """Generate interpretation message."""
    band, _ = get_stress_band(stress_index)

    # Get norm for comparison
    norm = get_hrv_norm(age, sex)

    messages = []

    # HR comment
    if hr_bpm < 60:
        messages.append("Your HR is on the lower side - you may be very fit or at rest.")
    elif hr_bpm > 90:
        messages.append("Your HR is elevated - this could be due to activity, caffeine, or stress.")
    else:
        messages.append("Your HR is within normal range.")

    # HRV comment
    if rmssd_ms < norm.low:
        messages.append(f"Your HRV is below average for your age - likely stress, poor sleep, or recovery.")
    elif rmssd_ms > norm.high:
        messages.append("Your HRV is excellent - shows good recovery and parasympathetic tone.")
    else:
        messages.append("Your HRV is within normal range.")

    # Overall
    if band == "Low":
        messages.append("Overall: Low stress/fatigue. Keep doing what you're doing!")
    elif band == "Moderate":
        messages.append("Overall: Moderate levels. Try the 4-7-8 breathing practice today.")
    else:
        messages.append("Overall: High stress/fatigue. Prioritize rest and recovery today.")

    return " ".join(messages)


async def calculate_ppg_metrics(
    hr_bpm: float,
    rmssd_ms: float,
    sdnn_ms: float = None,
    pnn50_pct: float = None,
    age: int = 40,
    sex: str = "male",
    resting_hr: float = 70.0,
    pre_scan_context: dict = None,
) -> dict:
    """Calculate all PPG metrics."""
    stress_index = calc_stress_index(
        hr_bpm=hr_bpm,
        rmssd_ms=rmssd_ms,
        age=age,
        sex=sex,
        resting_hr_baseline=resting_hr,
        pre_scan_context=pre_scan_context,
    )

    band, color = get_stress_band(stress_index)

    return {
        "hr_bpm": hr_bpm,
        "rmssd_ms": rmssd_ms,
        "sdnn_ms": sdnn_ms,
        "pnn50_pct": pnn50_pct,
        "stress_index": stress_index,
        "stress_band": band,
        "stress_color": color,
        "interpretation": interpret_stress_index(
            stress_index, hr_bpm, rmssd_ms, age, sex
        ),
    }