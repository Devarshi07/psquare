"""Heart Scoreboard - pillar-by-pillar breakdown.

Outputs all 10 pillars with status, explanations, actions, and point costs.
"""
import structlog
from dataclasses import dataclass
from typing import Optional

from app.medical_knowledge.reference_ranges import (
    get_bp_status,
    get_cholesterol_status,
    get_rhr_status,
    get_bmi_status,
    get_waist_status,
    get_sleep_status,
    get_stress_status,
    get_cv_risk_status,
)
from app.medical_knowledge.hrv_norms import get_hrv_status, get_hrv_norm
from app.medical_knowledge.indian_thresholds import get_indian_bmi_status

log = structlog.get_logger()


@dataclass
class Pillar:
    """A single pillar in the scoreboard."""
    name: str
    value: str  # Current value as string
    status: str  # Status band
    color: str  # Hex color
    explanation: str  # Plain English explanation
    action: str  # Highest-impact action
    points_cost: int  # Points this pillar is costing


@dataclass
class HeartScoreboard:
    """Complete scoreboard with 10 pillars."""
    pillars: list[Pillar]
    summary: str


def build_scoreboard(inputs) -> HeartScoreboard:
    """Build the heart scoreboard from user inputs.

    Args:
        inputs: HeartScoreInput or similar object with all user data

    Returns:
        HeartScoreboard with all 10 pillars
    """
    pillars = []

    # 1. 10-Year CV Risk
    if inputs.systolic_bp and inputs.total_chol and inputs.hdl:
        from app.heart.qrisk3 import calculate_qrisk3
        cv_result = calculate_qrisk3(
            age=inputs.age,
            sex=inputs.sex,
            systolic_bp=inputs.systolic_bp,
            total_chol=inputs.total_chol,
            hdl_chol=inputs.hdl,
            smoking=inputs.smoking_status == "current",
            diabetes=inputs.has_diabetes,
            bp_treatment=inputs.on_bp_meds,
            ethnicity=inputs.ethnicity or "south_asian",
            family_history=inputs.family_history_early_chd,
            bmi=inputs.bmi or 25,
        )
        risk_val = cv_result.risk_percent
    else:
        risk_val = 10.0

    risk_status, risk_color = get_cv_risk_status(risk_val)
    cv_points = int(risk_val * 3.5)  # Rough penalty conversion
    pillars.append(Pillar(
        name="10-Year CV Risk",
        value=f"{risk_val:.1f}%",
        status=risk_status,
        color=risk_color,
        explanation=(
            f"Your {risk_val:.1f}% risk means you have a "
            f"{risk_status.lower()} chance of a cardiovascular event in the next 10 years."
        ),
        action="Focus on lowering LDL cholesterol and increasing activity.",
        points_cost=cv_points,
    ))

    # 2. Heart Age
    from app.heart.heart_age import calculate_heart_age
    ha_result = calculate_heart_age(
        age=inputs.age,
        sex=inputs.sex,
        systolic_bp=inputs.systolic_bp or 120,
        total_chol=inputs.total_chol,
        hdl_chol=inputs.hdl,
        smoking=inputs.smoking_status == "current",
        diabetes=inputs.has_diabetes,
        ethnicity=inputs.ethnicity or "south_asian",
    )
    gap = ha_result.gap_years
    if gap <= 0:
        ha_val = f"{ha_result.heart_age} (younger by {-gap} yrs)"
    else:
        ha_val = f"{ha_result.heart_age} (older by {gap} yrs)"

    pillars.append(Pillar(
        name="Heart Age",
        value=ha_val,
        status=ha_result.gap_status,
        color=ha_result.gap_color,
        explanation=(
            f"Your heart age is {ha_result.heart_age} years. "
            f"This is {abs(gap)} years {abs(gap) and 'older' or 'younger'} than your "
            f"chronological age of {inputs.age}."
        ),
        action="Improve BP and cholesterol to bring heart age down.",
        points_cost=int(ha_result.penalty * 0.15),
    ))

    # 3. Blood Pressure
    if inputs.systolic_bp and inputs.diastolic_bp:
        bp_status, bp_color = get_bp_status(int(inputs.systolic_bp), int(inputs.diastolic_bp))
        bp_val = f"{int(inputs.systolic_bp)}/{int(inputs.diastolic_bp)}"
    else:
        bp_status = "Unknown"
        bp_color = "#6B7280"
        bp_val = "Not recorded"

    bp_points = 0
    if inputs.systolic_bp:
        if inputs.systolic_bp >= 160:
            bp_points = 20
        elif inputs.systolic_bp >= 140:
            bp_points = 12
        elif inputs.systolic_bp >= 130:
            bp_points = 6
        else:
            bp_points = 0

    pillars.append(Pillar(
        name="Blood Pressure",
        value=bp_val,
        status=bp_status,
        color=bp_color,
        explanation=(
            f"Your blood pressure is {bp_val} mmHg, which is {bp_status.lower()}."
        ),
        action="Reduce sodium intake to under 5g/day; check BP daily.",
        points_cost=bp_points,
    ))

    # 4. Cholesterol
    if inputs.ldl:
        chol_status, chol_color = get_cholesterol_status(inputs.ldl, "ldl")
        ldl_val = f"LDL {inputs.ldl:.0f}"
    else:
        chol_status = "Unknown"
        chol_color = "#6B7280"
        ldl_val = "Not recorded"

    chol_points = 0
    if inputs.ldl:
        if inputs.ldl >= 160:
            chol_points = 15
        elif inputs.ldl >= 130:
            chol_points = 8
        elif inputs.ldl >= 100:
            chol_points = 3

    pillars.append(Pillar(
        name="Cholesterol",
        value=ldl_val,
        status=chol_status,
        color=chol_color,
        explanation=(
            f"Your LDL is {inputs.ldl:.0f} mg/dL, which is {chol_status.lower()}."
            if inputs.ldl
            else "LDL not recorded — share a recent lipid panel to unlock this pillar."
        ),
        action="Reduce saturated fats; consider Mediterranean diet.",
        points_cost=chol_points,
    ))

    # 5. Resting Heart Rate
    if hasattr(inputs, 'recent_hr_bpm') and inputs.recent_hr_bpm:
        rhr_status, rhr_color = get_rhr_status(inputs.recent_hr_bpm)
        rhr_val = f"{inputs.recent_hr_bpm} BPM"
    else:
        rhr_status = "Unknown"
        rhr_color = "#6B7280"
        rhr_val = "Not recorded"

    pillars.append(Pillar(
        name="Resting Heart Rate",
        value=rhr_val,
        status=rhr_status,
        color=rhr_color,
        explanation=(
            f"Your resting heart rate is {rhr_val}, which is {rhr_status.lower()}."
        ),
        action="Regular cardio exercise will lower RHR over time.",
        points_cost=0 if rhr_status in ["Excellent", "Good"] else 5,
    ))

    # 6. HRV
    if hasattr(inputs, 'recent_rmssd_ms') and inputs.recent_rmssd_ms:
        hrv_status, hrv_color = get_hrv_status(inputs.recent_rmssd_ms, inputs.age, inputs.sex)
        hrv_val = f"RMSSD {inputs.recent_rmssd_ms:.0f} ms"
    else:
        hrv_status = "No PPG scan"
        hrv_color = "#6B7280"
        hrv_val = "No scan"

    pillars.append(Pillar(
        name="HRV",
        value=hrv_val,
        status=hrv_status,
        color=hrv_color,
        explanation=(
            f"Your HRV (RMSSD) is {inputs.recent_rmssd_ms or 'not recorded'} ms."
        ),
        action="Try daily breathing exercises to improve HRV.",
        points_cost=10 if hrv_status in ["Low", "Below Average"] else 0,
    ))

    # 7. Activity
    if inputs.daily_steps:
        if inputs.daily_steps >= 10000:
            act_status = "Active"
            act_color = "#10B981"
            act_points = 0
        elif inputs.daily_steps >= 7500:
            act_status = "Moderate"
            act_color = "#10B981"
            act_points = 3
        elif inputs.daily_steps >= 5000:
            act_status = "Low"
            act_color = "#F59E0B"
            act_points = 8
        else:
            act_status = "Sedentary"
            act_color = "#F97366"
            act_points = 15
    else:
        act_status = "Unknown"
        act_color = "#6B7280"
        act_points = 10
        inputs.daily_steps = 0

    pillars.append(Pillar(
        name="Activity",
        value=f"{inputs.daily_steps} steps/day",
        status=act_status,
        color=act_color,
        explanation=(
            f"You're averaging {inputs.daily_steps} steps per day."
        ),
        action=f"Add {1500} steps to your daily goal.",
        points_cost=act_points,
    ))

    # 8. BMI/Waist
    if inputs.bmi:
        bmi_status, bmi_color = get_bmi_status(inputs.bmi)
        bmi_val = f"BMI {inputs.bmi:.1f}"
    else:
        bmi_status = "Unknown"
        bmi_color = "#6B7280"
        bmi_val = "Not recorded"

    waist_val = ""
    waist_points = 0
    if inputs.waist_cm:
        waist_status, waist_color = get_waist_status(inputs.waist_cm, inputs.sex)
        waist_val = f", Waist {inputs.waist_cm:.0f}cm"
        waist_points = 8 if "Risk" in waist_status else 0

    pillars.append(Pillar(
        name="BMI / Waist",
        value=bmi_val + waist_val,
        status=bmi_status,
        color=bmi_color,
        explanation=(
            f"Your BMI is {inputs.bmi or 'not recorded'}."
            f" Waist {inputs.waist_cm or 'not recorded'}cm."
        ),
        action="Focus on waist reduction - aim for <90cm (men) or <80cm (women).",
        points_cost=waist_points,
    ))

    # 9. Sleep
    if inputs.sleep_hours:
        sleep_status, sleep_color = get_sleep_status(inputs.sleep_hours)
        sleep_val = f"{inputs.sleep_hours:.1f} hrs"
    else:
        sleep_status = "Unknown"
        sleep_color = "#6B7280"
        sleep_val = "Not recorded"

    sleep_points = 0
    if inputs.sleep_hours:
        if inputs.sleep_hours < 6:
            sleep_points = 10
        elif inputs.sleep_hours < 7:
            sleep_points = 5

    pillars.append(Pillar(
        name="Sleep",
        value=sleep_val,
        status=sleep_status,
        color=sleep_color,
        explanation=f"You're sleeping {inputs.sleep_hours or 'not recorded'} hours/night.",
        action="Target 7-8 hours; sleep before 11 PM.",
        points_cost=sleep_points,
    ))

    # 10. Stress
    if inputs.stress_score:
        stress_status, stress_color = get_stress_status(inputs.stress_score)
        stress_val = f"{inputs.stress_score}/10"
    else:
        stress_status = "Unknown"
        stress_color = "#6B7280"
        stress_val = "Not recorded"

    stress_points = 0
    if inputs.stress_score and inputs.stress_score >= 7:
        stress_points = 10

    pillars.append(Pillar(
        name="Stress",
        value=stress_val,
        status=stress_status,
        color=stress_color,
        explanation=f"Your stress level is {inputs.stress_score or 'not recorded'}/10.",
        action="Practice 4-7-8 breathing for 5 minutes daily.",
        points_cost=stress_points,
    ))

    # Summary
    total_cost = sum(p.points_cost for p in pillars)
    summary = (
        f"Your Heart Score is being dragged down by {total_cost} points. "
        f"Focus on the highest-impact actions to improve."
    )

    return HeartScoreboard(pillars=pillars, summary=summary)


def format_scoreboard_for_whatsapp(board: HeartScoreboard) -> str:
    """Format scoreboard as WhatsApp message."""
    lines = ["📊 *Your Heart Scoreboard*\n"]

    for p in board.pillars:
        emoji = "🔴" if p.color == "#EF4444" else (
            "🟠" if p.color == "#F97366" else (
                "🟡" if p.color == "#F59E0B" else "🟢"
            )
        )
        lines.append(
            f"{emoji} *{p.name}* — {p.value} ({p.status})\n"
            f"   {p.explanation[:80]}...\n"
            f"   → {p.action}\n"
        )

    lines.append(f"\n{board.summary}")
    return "\n".join(lines)