"""Resting heart rate logging."""
import re
import structlog
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.db.models import RHRReading
from app.db import get_db_session

log = structlog.get_logger()


@dataclass
class RHRLogResult:
    """Result of RHR logging."""
    bpm: int
    source: str = "text"  # text, voice, photo, ppg
    success: bool = True
    error: Optional[str] = None


async def parse_rhr_text(text: str) -> Optional[RHRLogResult]:
    """Parse RHR from text.

    Accepts: "72", "72 bpm", "heart rate 72", "pulse 72"
    Also accepts "count 36 x2" style (count for 30s then multiply by 2)
    """
    text = text.lower().strip()

    # Handle "count X x2" style (user counted pulse for 30s)
    match = re.search(r"(\d+)\s*[x×]\s*2", text)
    if match:
        count30 = int(match.group(1))
        bpm = count30 * 2
        if 30 <= bpm <= 200:
            return RHRLogResult(bpm=bpm, source="text")

    # Remove common prefixes
    text = re.sub(r"^(pulse|heart rate|bpm|hr)\s*", "", text)

    # Find number
    numbers = [int(n) for n in re.findall(r"\d+", text)]

    if numbers:
        bpm = numbers[0]
        if 30 <= bpm <= 200:
            return RHRLogResult(bpm=bpm, source="text")

    return None


async def log_rhr(
    user_id: int,
    bpm: int,
    source: str = "self_reported",
) -> RHRReading:
    """Log an RHR reading to the database."""
    session = await get_db_session()

    reading = RHRReading(
        user_id=user_id,
        bpm=bpm,
        source=source,
        taken_at=datetime.now(),
    )

    session.add(reading)
    await session.commit()
    await session.refresh(reading)

    log.info("rhr.logged", user_id=user_id, bpm=bpm)
    return reading


async def get_rhr_average(user_id: int, days: int = 7) -> Optional[float]:
    """Get average RHR over last N days."""
    from datetime import timedelta
    from sqlalchemy import select, func
    from sqlalchemy.sql import and_

    session = await get_db_session()
    cutoff = datetime.now() - timedelta(days=days)

    stmt = select(func.avg(RHRReading.bpm)).where(
        and_(
            RHRReading.user_id == user_id,
            RHRReading.taken_at >= cutoff,
        )
    )

    result = await session.scalar(stmt)
    return round(result, 1) if result else None


async def process_rhr_input(user_id: int, content: str) -> RHRLogResult:
    """Process RHR input."""
    result = await parse_rhr_text(content)

    if result:
        await log_rhr(user_id, result.bpm, result.source)
        return result

    return RHRLogResult(0, success=False, error="Could not parse RHR from input")


async def get_resting_hr_from_ppg(user_id: int) -> Optional[int]:
    """Get most recent RHR from PPG scan."""
    from sqlalchemy import select
    from app.db.models import PPGScan

    session = await get_db_session()

    stmt = (
        select(PPGScan.hr_bpm)
        .where(PPGScan.user_id == user_id)
        .order_by(PPGScan.taken_at.desc())
        .limit(1)
    )

    result = await session.scalar(stmt)
    return result