"""Daily heart habits checklist.

Six tappable buttons each evening:
1. Hit my step goal
2. ≥ 2 servings veg/fruit
3. Kept salt low
4. No smoke / vape today (smokers only)
5. In bed before 11 PM
6. Did the 5-min breathing practice
"""
import structlog
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional

from app.db.models import HabitLog
from app.db import get_db_session

log = structlog.get_logger()


class HabitType(str, Enum):
    """The six daily habits."""
    STEPS = "steps"
    VEGETABLES = "vegetables"
    LOW_SALT = "low_salt"
    NO_SMOKE = "no_smoke"
    EARLY_BED = "early_bed"
    BREATHING = "breathing"


@dataclass
class HabitStatus:
    """Status of a single habit."""
    habit: HabitType
    completed: bool


@dataclass
class DailyHabits:
    """All habits for a day."""
    date: date
    habits: list[HabitStatus]
    streak_count: int = 0
    total_completed: int = 0


# All habits (some conditional on user profile)
ALL_HABITS = [
    HabitType.STEPS,
    HabitType.VEGETABLES,
    HabitType.LOW_SALT,
    HabitType.EARLY_BED,
    HabitType.BREATHING,
]

# Smoker-only habit
SMOKER_HABIT = HabitType.NO_SMOKE


def get_user_habits(is_smoker: bool = False) -> list[HabitType]:
    """Get the habits list for a user."""
    habits = list(ALL_HABITS)
    if is_smoker:
        habits.append(SMOKER_HABIT)
    return habits


def format_habits_for_whatsapp(is_smoker: bool = False) -> str:
    """Format habits as WhatsApp interactive message."""
    habits = get_user_habits(is_smoker)

    text = "📝 *Daily Heart Habits* — Check off what you did today:\n\n"

    habit_labels = {
        HabitType.STEPS: "🚶 Hit my step goal",
        HabitType.VEGETABLES: "🥗 ≥ 2 servings veg/fruit",
        HabitType.LOW_SALT: "🧂 Kept salt low",
        HabitType.NO_SMOKE: "🚭 No smoke / vape today",
        HabitType.EARLY_BED: "😴 In bed before 11 PM",
        HabitType.BREATHING: "🧘 Did the 5-min breathing practice",
    }

    for i, habit in enumerate(habits, 1):
        text += f"{i}. {habit_labels.get(habit, habit.value)}\n"

    return text


async def log_habit(
    user_id: int,
    habit: HabitType,
    completed: bool = True,
    log_date: Optional[date] = None,
) -> HabitLog:
    """Log a single habit completion."""
    session = await get_db_session()

    if log_date is None:
        log_date = date.today()

    # Get or create today's log
    from sqlalchemy import select
    from sqlalchemy.sql import and_

    stmt = select(HabitLog).where(
        and_(
            HabitLog.user_id == user_id,
            HabitLog.date == log_date,
        )
    )
    existing = await session.scalar(stmt)

    if existing:
        habits_json = existing.habits_json or {}
    else:
        habits_json = {}

    # Update habit
    habits_json[habit.value] = completed

    if existing:
        existing.habits_json = habits_json
    else:
        # Calculate streak
        yesterday = log_date - timedelta(days=1)
        stmt_y = select(HabitLog).where(
            and_(
                HabitLog.user_id == user_id,
                HabitLog.date == yesterday,
            )
        )
        yesterday_log = await session.scalar(stmt_y)

        streak = 1
        if yesterday_log and yesterday_log.streak_count:
            # Check if yesterday had at least 3 habits
            y_habits = yesterday_log.habits_json or {}
            if sum(1 for v in y_habits.values() if v) >= 3:
                streak = yesterday_log.streak_count + 1

        new_log = HabitLog(
            user_id=user_id,
            date=log_date,
            habits_json=habits_json,
            streak_count=streak,
        )
        session.add(new_log)
        existing = new_log

    await session.commit()
    await session.refresh(existing)

    log.info("habit.logged", user_id=user_id, habit=habit.value, completed=completed)
    return existing


async def get_todays_habits(user_id: int, is_smoker: bool = False) -> DailyHabits:
    """Get today's habit status."""
    from datetime import timedelta
    from sqlalchemy import select
    from sqlalchemy.sql import and_

    session = await get_db_session()
    today = date.today()

    stmt = select(HabitLog).where(
        and_(
            HabitLog.user_id == user_id,
            HabitLog.date == today,
        )
    )
    log_entry = await session.scalar(stmt)

    habits = get_user_habits(is_smoker)
    habit_statuses = []

    if log_entry:
        habits_json = log_entry.habits_json or {}
        streak = log_entry.streak_count or 0

        for habit in habits:
            completed = habits_json.get(habit.value, False)
            habit_statuses.append(HabitStatus(habit=habit, completed=completed))

        total = sum(1 for h in habit_statuses if h.completed)
    else:
        streak = 0
        for habit in habits:
            habit_statuses.append(HabitStatus(habit=habit, completed=False))
        total = 0

    return DailyHabits(
        date=today,
        habits=habit_statuses,
        streak_count=streak,
        total_completed=total,
    )


async def get_streak(user_id: int) -> int:
    """Get current streak count."""
    from sqlalchemy import select
    from sqlalchemy.sql import and_

    session = await get_db_session()

    stmt = (
        select(HabitLog.streak_count)
        .where(HabitLog.user_id == user_id)
        .order_by(HabitLog.date.desc())
        .limit(1)
    )

    result = await session.scalar(stmt)
    return result or 0


from datetime import timedelta