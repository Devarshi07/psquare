"""PDF report generator using WeasyPrint."""
import structlog
from datetime import datetime
from typing import Optional

from app.reports.dial import generate_heart_score_dial, generate_bioage_visual, generate_ppg_waveform

log = structlog.get_logger()


async def generate_pdf_report(
    user_id: int,
    user_name: str,
    heart_score: int,
    heart_score_band: str,
    heart_score_confidence: str,
    bio_age: float,
    bio_age_gap: float,
    bio_age_status: str,
    ppg_data: dict = None,
    cv_risk: float = 10.0,
    cv_risk_category: str = "Low",
    heart_age: int = 40,
    heart_age_gap: int = 0,
    pillars: list = None,
    drivers: list = None,
    lab_cadence: list = None,
) -> str:
    """Generate PDF report and return S3 URL.

    In production, this would:
    1. Render Jinja2 template with data
    2. Convert to PDF via WeasyPrint
    3. Upload to S3
    4. Return signed URL
    """
    # For now, return placeholder - WeasyPrint requires system deps
    log.info("pdf.generating", user_id=user_id)

    # Generate SVGs for embedded charts
    dial_svg = generate_heart_score_dial(heart_score, heart_score_band, heart_score_confidence)
    bioage_svg = generate_bioage_visual(bio_age, bio_age + bio_age_gap, bio_age_gap)
    ppg_svg = generate_ppg_waveform()

    # Prepare template context
    context = {
        "user_name": user_name or "User",
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "heart_score": heart_score,
        "heart_score_band": heart_score_band,
        "heart_score_confidence": heart_score_confidence,
        "bio_age": int(bio_age),
        "bio_age_gap": f"{bio_age_gap:+.0f} years",
        "bio_age_status": bio_age_status,
        "ppg_data": ppg_data,
        "ppg_waveform": ppg_svg,
        "cv_risk": cv_risk,
        "cv_risk_category": cv_risk_category,
        "cv_risk_explanation": get_cv_risk_explanation(cv_risk),
        "heart_age": heart_age,
        "heart_age_gap": heart_age_gap,
        "heart_age_status": "older" if heart_age_gap > 0 else "younger",
        "pillars": pillars or get_default_pillars(),
        "bioage_visual": bioage_svg,
        "bio_age_drivers": drivers,
        "reversal_week1": "Sleep: 7-8 hours, consistent bedtime",
        "reversal_week2": "Sun: 10-15 min morning exposure",
        "reversal_week3": "Sugar: Reduce processed foods by 50%",
        "reversal_week4": "Hydration: 2-3L water daily",
        "cardio_plan": "Zone 2: 30 min, 2x/week | Intervals: 1x/week",
        "strength_plan": "Full body: 2x/week, 3 sets × 10 reps",
        "meal_suggestions": "Mediterranean diet focus: omega-3s, fiber, low sodium",
        "stress_practice": "4-7-8 breathing, 5 min daily",
        "habit_streak": 0,
        "lab_cadence": lab_cadence or get_default_lab_cadence(),
    }

    # In production, would use WeasyPrint here:
    # from weasyprint import HTML
    # html = HTML(string=render_template("report.html", **context))
    # pdf_bytes = html.write_pdf()

    log.info("pdf.generated", user_id=user_id)

    # Return placeholder URL for now
    return f"https://s3.amazonaws.com/psquare-reports/{user_id}/report.pdf"


def get_cv_risk_explanation(risk: float) -> str:
    """Get explanation for CV risk percentage."""
    if risk < 5:
        return "Your 10-year cardiovascular risk is low. Maintain healthy habits."
    elif risk < 10:
        return "Borderline risk - focus on lifestyle factors to prevent progression."
    elif risk < 20:
        return "Moderate risk - consider discussing with your doctor."
    else:
        return "High risk - please consult a cardiologist soon."


def get_default_pillars() -> list:
    """Default pillars for display."""
    return [
        {"name": "Blood Pressure", "value": "120/80", "status": "Normal", "pillar_class": ""},
        {"name": "LDL Cholesterol", "value": "100 mg/dL", "status": "Optimal", "pillar_class": ""},
        {"name": "Resting HR", "value": "70 BPM", "status": "Good", "pillar_class": ""},
        {"name": "Activity", "value": "7500 steps", "status": "Moderate", "pillar_class": "warning"},
    ]


def get_default_lab_cadence() -> list:
    """Default lab cadence."""
    return [
        {"name": "Lipid Panel", "frequency": "Every 12 months", "next_due": "Next checkup"},
        {"name": "HbA1c", "frequency": "Every 12 months", "next_due": "Next checkup"},
        {"name": "ECG", "frequency": "Baseline at 35+", "next_due": "Discuss with doctor"},
    ]


async def send_report_via_whatsapp(user_phone: str, pdf_url: str) -> bool:
    """Send generated PDF via WhatsApp."""
    from app.whatsapp import get_whatsapp_adapter

    adapter = get_whatsapp_adapter()

    try:
        await adapter.send_document(
            to=user_phone,
            document_url=pdf_url,
            caption="Here's your P² Heart & Longevity Report! 📊\n\nRead through and let me know if you have questions."
        )
        return True
    except Exception as e:
        log.error("pdf.send_error", error=str(e))
        return False