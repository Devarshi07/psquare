"""Lab cadence recommender.

When to get lipid panel, ECG, Lp(a), hsCRP based on risk profile.
"""
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

log = structlog.get_logger()


@dataclass
class LabRecommendation:
    """A lab test recommendation."""
    test_name: str
    frequency_months: int
    urgency: str  # "now", "soon", "routine"
    reason: str
    last_test_date: Optional[datetime] = None
    next_test_date: Optional[datetime] = None


def recommend_lab_cadence(
    age: int,
    cv_risk_percent: float = 10.0,
    has_high_cholesterol: bool = False,
    on_statin: bool = False,
    has_diabetes: bool = False,
    ldl: float = None,
    hba1c: float = None,
    lpa_done: bool = False,  # Lp(a) once done
    last_lipid: datetime = None,
    last_ecg: datetime = None,
    last_hba1c: datetime = None,
    ppg_irregular: bool = False,
) -> list[LabRecommendation]:
    """Recommend lab test cadence based on risk profile."""
    recommendations = []
    now = datetime.now()

    # Lipid Panel
    if on_statin or has_high_cholesterol or ldl and ldl >= 130:
        freq = 6 if on_statin else 12
        urgency = "now" if on_statin else "soon"
        reason = "On cholesterol medication or high LDL"
    elif cv_risk_percent >= 20 or has_diabetes:
        freq = 12
        urgency = "routine"
        reason = "High CV risk or diabetes"
    else:
        freq = 24  # Every 2 years if normal
        urgency = "routine"
        reason = "Routine monitoring"

    if last_lipid:
        next_date = last_lipid + timedelta(days=30 * freq)
    else:
        next_date = now + timedelta(days=30)

    recommendations.append(LabRecommendation(
        test_name="Lipid Panel",
        frequency_months=freq,
        urgency=urgency,
        reason=reason,
        last_test_date=last_lipid,
        next_test_date=next_date,
    ))

    # HbA1c / Fasting Glucose
    if has_diabetes:
        freq = 6
        urgency = "now"
        reason = "Diabetes - monitor regularly"
    elif hba1c and hba1c >= 5.7:
        freq = 12
        urgency = "soon"
        reason = "Prediabetes - yearly monitoring"
    else:
        freq = 36  # Every 3 years if normal
        urgency = "routine"
        reason = "Routine screening"

    if last_hba1c:
        next_date = last_hba1c + timedelta(days=30 * freq)
    else:
        next_date = now + timedelta(days=30)

    recommendations.append(LabRecommendation(
        test_name="HbA1c / Fasting Glucose",
        frequency_months=freq,
        urgency=urgency,
        reason=reason,
        last_test_date=last_hba1c,
        next_test_date=next_date,
    ))

    # ECG
    if age >= 45 or ppg_irregular:
        freq = 12
        urgency = "now" if ppg_irregular else "routine"
        reason = "Age-based or PPG showed irregular rhythm"
    elif age >= 35:
        freq = 24
        urgency = "routine"
        reason = "Baseline ECG recommended"
    else:
        # Not needed yet
        pass

    if last_ecg:
        next_date = last_ecg + timedelta(days=30 * (freq or 24))
    else:
        next_date = now + timedelta(days=60)

    if freq:
        recommendations.append(LabRecommendation(
            test_name="ECG (Electrocardiogram)",
            frequency_months=freq or 24,
            urgency=urgency,
            reason=reason,
            last_test_date=last_ecg,
            next_test_date=next_date,
        ))

    # Lipoprotein(a) - once in a lifetime for South Asians
    if not lpa_done:
        recommendations.append(LabRecommendation(
            test_name="Lipoprotein(a)",
            frequency_months=0,  # One-time
            urgency="soon",
            reason="Lp(a) is highly elevated in South Asians; affects heart risk",
            last_test_date=None,
            next_test_date=now + timedelta(days=30),
        ))

    # hsCRP (inflammatory marker)
    if cv_risk_percent >= 20:
        recommendations.append(LabRecommendation(
            test_name="hsCRP (High-sensitivity CRP)",
            frequency_months=12,
            urgency="routine",
            reason="Inflammation marker for high CV risk",
            last_test_date=None,
            next_test_date=now + timedelta(days=90),
        ))

    # ApoB (advanced lipid)
    if cv_risk_percent >= 15:
        recommendations.append(LabRecommendation(
            test_name="ApoB",
            frequency_months=24,
            urgency="routine",
            reason="More accurate atherogenic particle count",
            last_test_date=None,
            next_test_date=now + timedelta(days=180),
        ))

    return recommendations


def format_lab_cadence_for_whatsapp(recommendations: list[LabRecommendation]) -> str:
    """Format lab recommendations as WhatsApp message."""
    lines = ["🧪 *Your Lab Test Cadence*", ""]

    # Sort by urgency
    urgency_order = {"now": 0, "soon": 1, "routine": 2}
    sorted_recs = sorted(recommendations, key=lambda x: urgency_order.get(x.urgency, 2))

    for rec in sorted_recs:
        emoji = "🔴" if rec.urgency == "now" else (
            "🟡" if rec.urgency == "soon" else "🟢"
        )

        if rec.frequency_months == 0:
            freq_text = "One-time test"
        else:
            freq_text = f"Every {rec.frequency_months} months"

        lines.append(f"{emoji} *{rec.test_name}*")
        lines.append(f"   {freq_text}")
        lines.append(f"   Why: {rec.reason}")

        if rec.next_test_date:
            lines.append(f"   Next: ~{rec.next_test_date.strftime('%b %Y')}")

        lines.append("")

    return "\n".join(lines)


async def get_user_lab_recommendations(user_id: int) -> str:
    """Get lab recommendations for a user."""
    # This would pull from user profile in DB
    # For now, return a placeholder
    return format_lab_cadence_for_whatsapp([
        LabRecommendation(
            test_name="Lipid Panel",
            frequency_months=12,
            urgency="routine",
            reason="Routine heart health monitoring",
        ),
    ])