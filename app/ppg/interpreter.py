"""PPG result interpreter - LLM-powered plain English explanations."""
import structlog
from typing import Optional

from app.utils.gemini_client import get_gemini_client

log = structlog.get_logger()


async def interpret_ppg_for_whatsapp(
    hr_bpm: int,
    rmssd_ms: float,
    stress_index: int,
    age: int,
    user_data: dict = None,
) -> list[str]:
    """Generate WhatsApp-friendly interpretation.

    Returns 2-3 short messages:
    1. One sentence summary
    2. One sentence personalized insight
    3. One specific action
    """
    user_data = user_data or {}

    # Get context from user data
    sleep_hours = user_data.get("sleep_hours", 7)
    stress_score = user_data.get("stress_score", 5)
    recent_bp = user_data.get("systolic_bp", 120)

    # Build prompt
    system_prompt = """You are a P Square heart health specialist. Give short, friendly, personalized insights.
    - NEVER mention "as an AI" or "I don't have access to"
    - Use the user's data to personalize
    - Keep messages short (under 30 words each)
    - Output only valid JSON array of 3 strings"""

    prompt = f"""Generate 3 WhatsApp message bubbles about this PPG scan:

User info:
- Age: {age}
- Sleep last night: {sleep_hours} hours
- Stress level (1-10): {stress_score}
- Recent BP: {recent_bp}/~80

PPG results:
- Heart Rate: {hr_bpm} BPM
- HRV (RMSSD): {rmssd_ms} ms
- Stress Index: {stress_index}/100

Output as JSON array:
["summary message", "personalized insight", "specific action"]"""

    gemini = get_gemini_client()

    try:
        result = await gemini.generate_structured(
            prompt=prompt,
            response_model=list,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=300,
        )
        return result
    except Exception as e:
        log.error("ppg.interpretation_error", error=str(e))
        # Fallback interpretation
        return [
            f"Your HR was {hr_bpm} bpm, HRV {rmssd_ms:.0f} ms — that's {get_band(stress_index).lower()}.",
            f"{get_fallback_insight(hr_bpm, rmssd_ms, sleep_hours)}",
            get_fallback_action(hr_bpm, rmssd_ms, stress_index),
        ]


def get_band(stress_index: int) -> str:
    if stress_index <= 30:
        return "Low"
    elif stress_index <= 60:
        return "Moderate"
    else:
        return "High"


def get_fallback_insight(hr_bpm: int, rmssd_ms: float, sleep_hours: float) -> str:
    """Fallback insight when LLM fails."""
    if rmssd_ms < 25:
        if sleep_hours < 6:
            return "Your low HRV is likely tied to your under 6 hours of sleep."
        else:
            return "Your HRV is below average — consider your stress levels."
    elif hr_bpm > 85:
        return "Your elevated HR may be from today's activity or stress."
    else:
        return "Your metrics are within normal range for your age."


def get_fallback_action(hr_bpm: int, rmssd_ms: float, stress_index: int) -> str:
    """Fallback action when LLM fails."""
    if stress_index > 60:
        return "Try the 4-7-8 breathing practice tonight before bed."
    elif rmssd_ms < 25:
        return "Prioritize 7-8 hours of sleep this week to improve HRV."
    else:
        return "Keep up the good work! A PPG scan weekly helps track your progress."


async def format_ppg_result_for_whatsapp(ppg_data: dict) -> str:
    """Format complete PPG result as WhatsApp message."""
    lines = [
        "📊 *Your PPG Scan Results*",
        "",
        f"❤️ *Heart Rate:* {ppg_data['hr_bpm']} BPM",
        f"💫 *HRV (RMSSD):* {ppg_data['rmssd_ms']:.0f} ms",
        f"😰 *Stress Index:* {ppg_data['stress_index']}/100 ({ppg_data['stress_band']})",
        "",
    ]

    if ppg_data.get("interpretation"):
        lines.append(f"_{ppg_data['interpretation']}_")

    return "\n".join(lines)


def check_ppg_safety(
    hr_bpm: float,
    rmssd_ms: float,
    is_irregular: bool = False,
) -> Optional[dict]:
    """Check PPG results for safety concerns."""
    warnings = []

    # Heart rate checks
    if hr_bpm < 40:
        warnings.append({
            "level": "urgent",
            "message": f"Heart rate {hr_bpm} BPM is very low.",
            "action": "Please consult a doctor. If you feel dizzy or faint, call 112.",
        })
    elif hr_bpm > 130:
        warnings.append({
            "level": "urgent",
            "message": f"Heart rate {hr_bpm} BPM is very high.",
            "action": "If accompanied by chest pain or dizziness, call 112. Otherwise see a doctor this week.",
        })

    # Irregular rhythm
    if is_irregular:
        warnings.append({
            "level": "warning",
            "message": "Irregular heartbeat pattern detected.",
            "action": "PPG cannot diagnose, but please get an ECG within the week.",
        })

    # Very low HRV
    if rmssd_ms < 10:
        warnings.append({
            "level": "warning",
            "message": "Very low HRV indicates high stress or poor recovery.",
            "action": "Prioritize rest, sleep, and relaxation techniques.",
        })

    return warnings if warnings else None