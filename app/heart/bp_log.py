"""Blood pressure logging with text/voice/photo parsing."""
import re
import structlog
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.utils.gemini_client import get_gemini_client
from app.db.models import BPReading
from app.db import get_db_session

log = structlog.get_logger()


@dataclass
class BPLogResult:
    """Result of BP logging."""
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    source: str = "text"  # text, voice, photo
    success: bool = True
    error: Optional[str] = None


async def parse_bp_text(text: str) -> Optional[BPLogResult]:
    """Parse BP from text message.

    Accepts: "120/80", "120 over 80", "BP 120/80", "120/80/72" (with pulse)
    """
    text = text.lower().strip()

    # Remove common prefixes
    text = re.sub(r"^(bp|blood pressure)\s*", "", text)
    text = text.replace("over", " ").replace("/", " ")

    # Find numbers
    numbers = [int(n) for n in re.findall(r"\d+", text)]

    if len(numbers) >= 2:
        systolic = numbers[0]
        diastolic = numbers[1]
        pulse = numbers[2] if len(numbers) >= 3 else None

        # Validate ranges
        if 60 <= systolic <= 250 and 40 <= diastolic <= 150:
            return BPLogResult(
                systolic=systolic,
                diastolic=diastolic,
                pulse=pulse,
                source="text",
            )

    return None


async def parse_bp_voice(audio_url: str) -> Optional[BPLogResult]:
    """Transcribe voice note and parse BP.

    Uses Gemini to transcribe and extract BP values.
    """
    gemini = get_gemini_client()

    prompt = """
    Listen to this voice note about blood pressure.
    Extract and return the blood pressure reading in this exact format:
    {"systolic": <number>, "diastolic": <number>, "pulse": <number or null>}

    If no BP is mentioned, return {"systolic": null, "diastolic": null, "pulse": null}
    """

    try:
        # Gemini doesn't do audio transcription natively in the same API
        # For now, return None and ask user to type
        log.info("bp.voice.transcription_not_implemented")
        return None
    except Exception as e:
        log.error("bp.voice_error", error=str(e))
        return None


async def parse_bp_photo(image_url: str) -> Optional[BPLogResult]:
    """Extract BP from photo of BP monitor.

    Uses Gemini Vision to read the display.
    """
    from pydantic import BaseModel

    class BPResponse(BaseModel):
        systolic: Optional[int] = None
        diastolic: Optional[int] = None
        pulse: Optional[int] = None

    gemini = get_gemini_client()

    prompt = """
    Look at this image of a blood pressure monitor.
    Extract and return the readings in this exact format:
    {"systolic": <number>, "diastolic": <number>, "pulse": <number or null>}

    If no BP reading is visible, return {"systolic": null, "diastolic": null, "pulse": null}
    """

    try:
        result = await gemini.analyze_image_structured(
            image_url=image_url,
            prompt=prompt,
            response_model=BPResponse,
            system_prompt="You are a medical device reader. Only extract the numbers shown.",
        )

        if result.systolic and result.diastolic:
            return BPLogResult(
                systolic=result.systolic,
                diastolic=result.diastolic,
                pulse=result.pulse,
                source="photo",
            )

        return None

    except Exception as e:
        log.error("bp.photo_error", error=str(e))
        return None


async def log_bp(
    user_id: int,
    systolic: int,
    diastolic: int,
    pulse: Optional[int] = None,
    source: str = "self_reported",
    posture: str = "seated",
) -> BPReading:
    """Log a BP reading to the database."""
    session = await get_db_session()

    reading = BPReading(
        user_id=user_id,
        systolic=systolic,
        diastolic=diastolic,
        pulse=pulse,
        source=source,
        posture=posture,
        taken_at=datetime.now(),
    )

    session.add(reading)
    await session.commit()
    await session.refresh(reading)

    log.info("bp.logged", user_id=user_id, systolic=systolic, diastolic=diastolic)
    return reading


async def get_bp_average(user_id: int, days: int = 7) -> Optional[dict]:
    """Get average BP over last N days."""
    from datetime import timedelta
    from sqlalchemy import select, func
    from sqlalchemy.sql import and_

    session = await get_db_session()
    cutoff = datetime.now() - timedelta(days=days)

    # Average systolic
    stmt_sys = select(func.avg(BPReading.systolic)).where(
        and_(
            BPReading.user_id == user_id,
            BPReading.taken_at >= cutoff,
        )
    )
    result_sys = await session.scalar(stmt_sys)

    # Average diastolic
    stmt_dia = select(func.avg(BPReading.diastolic)).where(
        and_(
            BPReading.user_id == user_id,
            BPReading.taken_at >= cutoff,
        )
    )
    result_dia = await session.scalar(stmt_dia)

    if result_sys and result_dia:
        return {
            "systolic": round(result_sys, 1),
            "diastolic": round(result_dia, 1),
            "days": days,
        }

    return None


async def process_bp_input(user_id: int, content: str, media_url: str = None) -> BPLogResult:
    """Process any BP input - text, voice, or photo."""
    # Try text first
    if content:
        result = await parse_bp_text(content)
        if result:
            await log_bp(user_id, result.systolic, result.diastolic, result.pulse, "text")
            return result

    # Try photo
    if media_url:
        result = await parse_bp_photo(media_url)
        if result:
            await log_bp(user_id, result.systolic, result.diastolic, result.pulse, "photo")
            return result

    # Try voice (not implemented yet)
    if media_url and media_url.endswith(('.mp3', '.wav', '.ogg')):
        result = await parse_bp_voice(media_url)
        if result:
            await log_bp(user_id, result.systolic, result.diastolic, result.pulse, "voice")
            return result

    return BPLogResult(0, 0, success=False, error="Could not parse BP from input")