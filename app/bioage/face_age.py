"""Face age estimation using Gemini Vision.

Per CLAUDE.md §11.4 - evaluate observable visible markers only.
"""
import structlog
from dataclasses import dataclass
from typing import Optional

from app.utils.gemini_client import get_gemini_client

log = structlog.get_logger()


@dataclass
class FaceAgeResult:
    """Result of face age estimation."""
    estimated_face_age: float
    confidence: str  # "High", "Medium", "Low"
    visible_drivers: list[dict]  # [{"factor": str, "evidence": str, "severity": str}]
    usable: bool = True
    reason_not_usable: Optional[str] = None


# System prompt for face analysis
FACE_ANALYSIS_SYSTEM_PROMPT = """You are a professional skincare/age assessment AI. Analyze this face selfie ONLY for visible age markers.

CRITICAL RULES:
1. Only evaluate OBSERVABLE markers - skin texture, lines, pigmentation
2. NEVER comment on: weight, ethnicity, attractiveness, gender expression, emotion, hair style/color (unless clearly age-related graying)
3. If image is unusable (blurry, dark, multiple faces, sunglasses, mask), return {"usable": false, "reason": "..."}
4. Be conservative - estimate slightly older if uncertain
5. Output ONLY valid JSON matching the schema provided."""


FACE_ANALYSIS_PROMPT = """Analyze this face selfie for visible age markers.

Look for:
- Skin texture and tone uniformity
- Periorbital fine lines, eye-area puffiness, dark circles
- Nasolabial folds (smile lines)
- Forehead lines
- Pigmentation, redness, dullness
- Lip volume
- Jawline definition

Return JSON with:
{
  "usable": true,
  "estimated_face_age": <number 20-80>,
  "confidence": "High|Medium|Low",
  "visible_drivers": [
    {"factor": "Sun damage", "evidence": "specific visible marker", "severity": "mild|moderate|significant"},
    {"factor": "Sleep deficit", "evidence": "specific visible marker", "severity": "mild|moderate|significant"},
    ...
  ]
}"""


async def estimate_face_age(image_url: str) -> FaceAgeResult:
    """Estimate biological age from face image using Gemini Vision."""
    from pydantic import BaseModel

    class FaceAgeResponse(BaseModel):
        usable: bool = True
        reason: Optional[str] = None
        estimated_face_age: Optional[float] = None
        confidence: Optional[str] = "Medium"
        visible_drivers: list[dict] = []

    gemini = get_gemini_client()

    try:
        result = await gemini.analyze_image_structured(
            image_url=image_url,
            prompt=FACE_ANALYSIS_PROMPT,
            response_model=FaceAgeResponse,
            system_prompt=FACE_ANALYSIS_SYSTEM_PROMPT,
        )

        if not result.usable:
            return FaceAgeResult(
                estimated_face_age=0,
                confidence="Low",
                visible_drivers=[],
                usable=False,
                reason_not_usable=result.reason or "Image not suitable for analysis",
            )

        return FaceAgeResult(
            estimated_face_age=result.estimated_face_age or 40,
            confidence=result.confidence or "Medium",
            visible_drivers=result.visible_drivers or [],
            usable=True,
        )

    except Exception as e:
        log.error("face_age.error", error=str(e))
        return FaceAgeResult(
            estimated_face_age=40,
            confidence="Low",
            visible_drivers=[],
            usable=False,
            reason_not_usable="Could not analyze image. Please try with better lighting.",
        )


def format_face_drivers_for_whatsapp(drivers: list[dict]) -> str:
    """Format visible drivers as WhatsApp message."""
    if not drivers:
        return ""

    lines = ["*Top visible drivers:*", ""]

    for driver in drivers[:3]:  # Top 3
        factor = driver.get("factor", "Unknown")
        evidence = driver.get("evidence", "")
        severity = driver.get("severity", "moderate")

        emoji = "🟡" if severity == "mild" else (
            "🟠" if severity == "moderate" else "🔴"
        )

        lines.append(f"{emoji} *{factor}*")
        lines.append(f"   {evidence}")

    return "\n".join(lines)