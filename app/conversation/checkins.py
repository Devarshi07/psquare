"""Check-in scheduler for daily/weekly prompts.

Schedules: morning (8am), evening (9pm), Sunday weekly, monthly bio age re-scan.
"""
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.db.models import Checkin, CheckinType
from app.db import get_db_session

log = structlog.get_logger()


@dataclass
class CheckinSchedule:
    """Check-in schedule for a user."""
    morning_time: str = "08:00"  # 8 AM
    evening_time: str = "21:00"  # 9 PM
    weekly_day: str = "Sunday"
    weekly_time: str = "10:00"  # 10 AM


async def schedule_checkins(
    user_id: int,
    schedule: CheckinSchedule = None,
) -> list[Checkin]:
    """Schedule all check-ins for a user."""
    if schedule is None:
        schedule = CheckinSchedule()

    session = await get_db_session()
    checkins = []

    # Morning check-in (daily)
    # Next 7 days
    for i in range(7):
        checkin_date = datetime.now() + timedelta(days=i)
        if checkin_date.hour < 8:  # Before 8 AM
            checkin_date = checkin_date.replace(hour=8, minute=0, second=0)
        else:
            checkin_date = (checkin_date + timedelta(days=1)).replace(hour=8, minute=0, second=0)

        checkin = Checkin(
            user_id=user_id,
            type=CheckinType.MORNING,
            scheduled_for=checkin_date,
        )
        session.add(checkin)
        checkins.append(checkin)

    # Evening check-in (daily)
    for i in range(7):
        checkin_date = datetime.now() + timedelta(days=i)
        if checkin_date.hour < 21:
            checkin_date = checkin_date.replace(hour=21, minute=0, second=0)
        else:
            checkin_date = (checkin_date + timedelta(days=1)).replace(hour=21, minute=0, second=0)

        checkin = Checkin(
            user_id=user_id,
            type=CheckinType.EVENING,
            scheduled_for=checkin_date,
        )
        session.add(checkin)
        checkins.append(checkin)

    # Weekly check-in (Sunday)
    # Next 4 Sundays
    for i in range(28):
        checkin_date = datetime.now() + timedelta(days=i)
        if checkin_date.strftime("%A") == "Sunday":
            checkin_date = checkin_date.replace(hour=10, minute=0, second=0)
            checkin = Checkin(
                user_id=user_id,
                type=CheckinType.WEEKLY,
                scheduled_for=checkin_date,
            )
            session.add(checkin)
            checkins.append(checkin)

    await session.commit()

    log.info("checkins.scheduled", user_id=user_id, count=len(checkins))
    return checkins


def format_morning_prompt(user_name: str = None) -> str:
    """Format morning check-in prompt."""
    name = user_name or ""
    return (
        f"Good morning{name} ☀️\n\n"
        "Quick morning check-in:\n"
        "1. Count your pulse for 30 seconds and reply with the number (×2 for BPM)\n"
        "2. How are you feeling today?\n\n"
        "Tap → [PPG Scan Link] for a 30-second finger scan."
    )


def format_evening_prompt(streak: int = 0) -> str:
    """Format evening habits check-in."""
    streak_text = f"\n🔥 Current streak: {streak} days!" if streak > 0 else ""

    return (
        "📝 *Evening Heart Habits Check* — Which did you complete today?\n\n"
        "1. 🚶 Hit my step goal\n"
        "2. 🥗 ≥ 2 servings veg/fruit\n"
        "3. 🧂 Kept salt low\n"
        "4. 🚭 No smoke / vape (smokers)\n"
        "5. 😴 In bed before 11 PM\n"
        "6. 🧘 Did 5-min breathing"
        f"{streak_text}\n\n"
        "Reply with the numbers (e.g., 1,2,3,6)"
    )


def format_weekly_prompt(
    score_this_week: int = None,
    score_last_week: int = None,
    bio_age_gap: float = None,
) -> str:
    """Format Sunday weekly review."""
    lines = ["📊 *Weekly Heart Review*\n"]

    if score_this_week is not None:
        delta = 0
        if score_last_week is not None:
            delta = score_this_week - score_last_week

        delta_text = f"+{delta}" if delta > 0 else str(delta)
        emoji = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")

        lines.append(f"This week: *{score_this_week}* ({delta_text} {emoji})")

        if score_last_week is not None:
            lines.append(f"Last week: {score_last_week}")

    if bio_age_gap is not None:
        gap_text = f"{bio_age_gap:+.1f} years"
        lines.append(f"\nBio age gap: {gap_text}")

    lines.append("\nWhat went well? What needs attention?\n")
    lines.append("Reply with what's working and what you'd like to improve.")

    return "\n".join(lines)


def format_monthly_prompt() -> str:
    """Format monthly re-check prompt."""
    return (
        "📅 *Monthly Check-In*\n\n"
        "It's been a month since your last scan!\n\n"
        "Time for:\n"
        "• Fresh PPG scan\n"
        "• Updated face selfie for bio age\n"
        "• Updated BP if you have a monitor\n\n"
        "This helps track your reversal plan progress. Ready?"
    )


async def get_due_checkins(user_id: int) -> list[Checkin]:
    """Get check-ins that are due now."""
    from sqlalchemy import select
    from sqlalchemy.sql import and_

    session = await get_db_session()
    now = datetime.now()

    stmt = select(Checkin).where(
        and_(
            Checkin.user_id == user_id,
            Checkin.scheduled_for <= now,
            Checkin.completed_at == None,
        )
    ).order_by(Checkin.scheduled_for.asc()).limit(10)

    result = await session.scalars(stmt)
    return list(result)


async def mark_checkin_complete(checkin_id: int) -> Checkin:
    """Mark a check-in as completed."""
    from sqlalchemy import select

    session = await get_db_session()

    stmt = select(Checkin).where(Checkin.id == checkin_id)
    checkin = await session.scalar(stmt)

    if checkin:
        checkin.completed_at = datetime.now()
        await session.commit()

    return checkin


async def process_checkin_response(
    user_id: int,
    checkin_type: CheckinType,
    response: str,
) -> str:
    """Process user's check-in response and return next prompt."""
    if checkin_type == CheckinType.MORNING:
        # Parse pulse or offer PPG link
        return "Thanks! Keep tracking daily for best results."
    elif checkin_type == CheckinType.EVENING:
        # Parse habit completions
        return "Great work! See you tomorrow."
    elif checkin_type == CheckinType.WEEKLY:
        # Acknowledge and note for next week
        return "Thanks for the update! See you next Sunday."
    else:
        return "Got it! See you next time."