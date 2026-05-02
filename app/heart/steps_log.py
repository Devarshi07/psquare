"""Steps tracking via text or screenshot."""
import re
import structlog
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from app.db.models import StepsLog
from app.db import get_db_session
from app.utils.gemini_client import get_gemini_client

log = structlog.get_logger()


@dataclass
class StepsLogResult:
    """Result of steps logging."""
    steps: int
    active_minutes: Optional[int] = None
    source: str = "text"  # text, screenshot
    success: bool = True
    error: Optional[str] = None


async def parse_steps_text(text: str) -> Optional[StepsLogResult]:
    """Parse steps from text.

    Accepts: "8000 steps", "steps 8500", "walked 7k", "7,500 steps today"
    """
    text = text.lower().strip()

    # Handle "7k", "10k" style
    match = re.search(r"(\d+)\s*k", text)
    if match:
        steps = int(match.group(1)) * 1000
        return StepsLogResult(steps=steps, source="text")

    # Remove common prefixes
    text = re.sub(r"^(steps|walked|ran)\s*", "", text)

    # Find number (allow commas)
    numbers = [int(n.replace(",", "")) for n in re.findall(r"[\d,]+", text)]

    if numbers:
        steps = numbers[0]
        if 0 <= steps <= 100000:
            return StepsLogResult(steps=steps, source="text")

    return None


async def parse_steps_screenshot(image_url: str) -> Optional[StepsLogResult]:
    """Extract steps from fitness app screenshot.

    Uses Gemini Vision to read the step count.
    """
    from pydantic import BaseModel

    class StepsResponse(BaseModel):
        steps: Optional[int] = None
        active_minutes: Optional[int] = None

    gemini = get_gemini_client()

    prompt = """
    Look at this fitness app screenshot.
    Extract and return the step count and active minutes in this exact format:
    {"steps": <number>, "active_minutes": <number or null>}

    If no step count is visible, return {"steps": null, "active_minutes": null}
    """

    try:
        result = await gemini.analyze_image_structured(
            image_url=image_url,
            prompt=prompt,
            response_model=StepsResponse,
            system_prompt="You are a fitness app display reader. Only extract step counts.",
        )

        if result.steps is not None:
            return StepsLogResult(
                steps=result.steps,
                active_minutes=result.active_minutes,
                source="screenshot",
            )

        return None

    except Exception as e:
        log.error("steps.screenshot_error", error=str(e))
        return None


async def log_steps(
    user_id: int,
    steps: int,
    active_minutes: Optional[int] = None,
    log_date: Optional[date] = None,
    source: str = "self_reported",
) -> StepsLog:
    """Log steps to the database."""
    session = await get_db_session()

    if log_date is None:
        log_date = date.today()

    # Check if already logged for this date
    from sqlalchemy import select
    from sqlalchemy.sql import and_

    stmt = select(StepsLog).where(
        and_(
            StepsLog.user_id == user_id,
            StepsLog.date == log_date,
        )
    )
    existing = await session.scalar(stmt)

    if existing:
        # Update existing
        existing.steps = max(existing.steps, steps)  # Take higher of existing or new
        if active_minutes:
            existing.active_minutes = max(existing.active_minutes or 0, active_minutes)
        await session.commit()
        await session.refresh(existing)
        return existing

    # Create new
    log_entry = StepsLog(
        user_id=user_id,
        date=log_date,
        steps=steps,
        active_minutes=active_minutes,
        source=source,
    )

    session.add(log_entry)
    await session.commit()
    await session.refresh(log_entry)

    log.info("steps.logged", user_id=user_id, steps=steps, date=log_date)
    return log_entry


async def get_steps_average(user_id: int, days: int = 7) -> Optional[float]:
    """Get average steps over last N days."""
    from sqlalchemy import select, func
    from sqlalchemy.sql import and_

    session = await get_db_session()
    cutoff = date.today() - timedelta(days=days)

    stmt = select(func.avg(StepsLog.steps)).where(
        and_(
            StepsLog.user_id == user_id,
            StepsLog.date >= cutoff,
        )
    )

    result = await session.scalar(stmt)
    return round(result, 0) if result else None


async def get_personalized_step_goal(current_avg: int) -> int:
    """Get personalized step goal."""
    # Start at current + 1500, cap at 12000
    goal = min(current_avg + 1500, 12000)
    # Round to nearest 500
    goal = round(goal / 500) * 500
    return goal


async def process_steps_input(user_id: int, content: str = None, image_url: str = None) -> StepsLogResult:
    """Process any steps input."""
    # Try text first
    if content:
        result = await parse_steps_text(content)
        if result:
            await log_steps(user_id, result.steps, result.active_minutes, source="text")
            return result

    # Try screenshot
    if image_url:
        result = await parse_steps_screenshot(image_url)
        if result:
            await log_steps(user_id, result.steps, result.active_minutes, source="screenshot")
            return result

    return StepsLogResult(0, success=False, error="Could not parse steps from input")