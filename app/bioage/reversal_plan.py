"""Biological age reversal plan generator.

60-day plan with weekly milestones based on top drivers.
"""
import structlog
from dataclasses import dataclass
from typing import Optional

log = structlog.get_logger()


@dataclass
class ReversalWeek:
    """One week of the reversal plan."""
    week: int
    focus: str
    daily_actions: list[str]
    weekly_goal: str
    milestone: str


# 8-week reversal plan (60 days)
REVERSAL_PLAN = [
    ReversalWeek(
        week=1,
        focus="Sleep foundation",
        daily_actions=[
            "Target 7-8 hours sleep",
            "No screens 1 hour before bed",
            "Consistent sleep time (within 30 min)",
            "Cool, dark room",
        ],
        weekly_goal="Establish consistent sleep schedule",
        milestone="Sleep 7+ hours for 5+ nights",
    ),
    ReversalWeek(
        week=2,
        focus="Sun exposure",
        daily_actions=[
            "10-15 min morning sun (before 10am)",
            "Vitamin D rich foods",
            "SPF on face, allow body sun",
            "Antioxidant skincare",
        ],
        weekly_goal="Build morning sun habit",
        milestone="Get 10+ min sun on 5+ days",
    ),
    ReversalWeek(
        week=3,
        focus="Sugar reduction",
        daily_actions=[
            "No added sugar in drinks",
            "Limit processed snacks",
            "Read labels",
            "Natural sweeteners only",
        ],
        weekly_goal="Reduce added sugar by 50%",
        milestone="Notice less sugar cravings",
    ),
    ReversalWeek(
        week=4,
        focus="Hydration",
        daily_actions=[
            "2-3 liters water daily",
            "Cucumber/lemon water",
            "Limit alcohol",
            "Herbal teas",
        ],
        weekly_goal="Improve hydration",
        milestone="Clearer skin, more energy",
    ),
    ReversalWeek(
        week=5,
        focus="Stress management",
        daily_actions=[
            "5-min breathing daily",
            "Meditation or prayer",
            "Nature walk",
            "Gratitude practice",
        ],
        weekly_goal="Daily stress practice",
        milestone="Feel calmer, better sleep",
    ),
    ReversalWeek(
        week=6,
        focus="Movement",
        daily_actions=[
            "30 min moderate exercise",
            "Walking meetings",
            "Stretch breaks",
            "Zone 2 cardio 2x/week",
        ],
        weekly_goal="Increase movement",
        milestone="More energy, better mood",
    ),
    ReversalWeek(
        week=7,
        focus="Skin health",
        daily_actions=[
            "Retinol/retinoid (evening)",
            "Vitamin C (morning)",
            "Moisturize twice daily",
            "Gentle cleansing",
        ],
        weekly_goal="Establish skincare routine",
        milestone="Notice skin improvements",
    ),
    ReversalWeek(
        week=8,
        focus="Maintenance",
        daily_actions=[
            "Continue all habits",
            "Track progress",
            "Plan next phase",
            "Celebrate wins",
        ],
        weekly_goal="Sustain improvements",
        milestone="Complete 60-day program",
    ),
]


def get_reversal_plan_for_drivers(drivers: list[dict]) -> list[ReversalWeek]:
    """Get personalized reversal plan based on top drivers.

    Reorders weeks to prioritize user's biggest drivers.
    """
    if not drivers:
        return REVERSAL_PLAN

    # Map drivers to week focus
    driver_focus_map = {
        "Sun damage": 2,
        "Sleep deficit": 1,
        "Sugar": 3,
        "Dehydration": 4,
        "Stress": 5,
        "Smoking": 6,
        "Alcohol": 4,
    }

    # Create ordered plan
    ordered_weeks = []
    prioritized = []

    for driver in drivers:
        factor = driver.get("factor", "")
        severity = driver.get("severity", "moderate")

        # Get week number for this driver
        week_num = driver_focus_map.get(factor, 8)

        if severity == "significant" and week_num < 8:
            prioritized.append(week_num)
        elif severity == "moderate" and week_num < 8:
            prioritized.append(week_num + 8)

    # Add remaining weeks
    all_weeks = list(range(1, 9))
    for w in prioritized:
        if w in all_weeks:
            all_weeks.remove(w)

    ordered_weeks = prioritized + all_weeks

    # Build plan in new order
    plan = []
    seen = set()
    for w in ordered_weeks:
        if w not in seen:
            week = next((wp for wp in REVERSAL_PLAN if wp.week == w), REVERSAL_PLAN[w-1])
            plan.append(week)
            seen.add(w)

    return plan


def format_reversal_plan_for_whatsapp(
    plan: list[ReversalWeek],
    user_name: str = None,
) -> str:
    """Format reversal plan as WhatsApp message."""
    name = user_name or ""

    lines = [f"💪 *60-Day Reversal Plan{name}*", ""]

    lines.append("*Your personalized plan (first 4 weeks):*")

    for wp in plan[:4]:
        lines.append("")
        lines.append(f"*Week {wp.week}: {wp.focus}*")
        for action in wp.daily_actions[:2]:
            lines.append(f"  • {action}")
        lines.append(f"  🎯 {wp.weekly_goal}")

    lines.append("")
    lines.append("Re-scan recommended every 30 days to track progress!")

    return "\n".join(lines)


async def generate_reversal_plan(
    user_id: int,
    drivers: list[dict],
    user_name: str = None,
) -> str:
    """Generate reversal plan for user."""
    plan = get_reversal_plan_for_drivers(drivers)
    return format_reversal_plan_for_whatsapp(plan, user_name)