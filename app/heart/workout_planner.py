"""Personalized cardio + strength plan generator.

Equipment-aware, condition-aware, heart-healthy workouts.
"""
import structlog
from dataclasses import dataclass, field
from typing import Optional

from app.heart.rhr_log import get_rhr_average

log = structlog.get_logger()


@dataclass
class CardioPlan:
    """Weekly cardio plan."""
    week: int
    zone2_minutes: int
    zone2_intensity: str  # "low", "moderate"
    interval_sessions: int
    interval_format: str  # "30s on/30s off" etc.
    weekly_progression: str


@dataclass
class StrengthPlan:
    """Weekly strength plan."""
    week: int
    sessions_per_week: int
    exercises: list[str]
    sets_reps: str
    progression: str


@dataclass
class FullWorkoutPlan:
    """Complete workout plan."""
    cardio: list[CardioPlan]
    strength: list[StrengthPlan]
    notes: list[str]


def calculate_karvonen_hr(
    age: int,
    resting_hr: int,
    intensity_pct: float = 0.7,
) -> int:
    """Calculate target HR using Karvonen formula.

    Target HR = ((max HR - resting HR) × intensity%) + resting HR
    Max HR = 220 - age
    """
    max_hr = 220 - age
    hr_reserve = max_hr - resting_hr
    target_hr = int((hr_reserve * intensity_pct) + resting_hr)
    return target_hr


def calculate_zone2_hr(age: int, resting_hr: int) -> tuple[int, int]:
    """Calculate Zone 2 HR range (60-70%).

    Returns (lower, upper) HR.
    """
    lower = calculate_karvonen_hr(age, resting_hr, 0.60)
    upper = calculate_karvonen_hr(age, resting_hr, 0.70)
    return lower, upper


def get_equipment_plan(equipment: str, limitations: list[str] = None) -> StrengthPlan:
    """Get strength exercises based on available equipment."""
    equipment = equipment.lower() if equipment else "bodyweight"
    limitations = limitations or []

    # Exercise options by equipment
    bodyweight = [
        "Push-ups (or wall push-ups)",
        "Bodyweight squats",
        "Lunges",
        "Plank",
        "Glute bridges",
        "Calf raises",
    ]

    dumbbells = bodyweight + [
        "Dumbbell rows",
        "Dumbbell presses",
        "Dumbbell curls",
        "Tricep extensions",
    ]

    resistance_bands = bodyweight + [
        "Band pull-aparts",
        "Band rows",
        "Band chest press",
        "Band bicep curls",
    ]

    gym = [
        "Bench press",
        "Lat pulldown",
        "Cable rows",
        "Leg press",
        "Deadlift",
        "Shoulder press",
    ]

    # Filter based on limitations
    def filter_exercises(exercises):
        filtered = list(exercises)
        if "shoulder" in limitations or "joint_pain" in limitations:
            filtered = [e for e in filtered if "press" not in e.lower() or "wall" in e.lower()]
        if "knee" in limitations or "joint_pain" in limitations:
            filtered = [e for e in filtered if "lunge" not in e.lower() and "squat" not in e.lower()]
        return filtered[:5]  # Top 5

    if equipment == "gym":
        exercises = filter_exercises(gym)
    elif equipment in ["dumbbells", "dumbbell"]:
        exercises = filter_exercises(dumbbells)
    elif equipment in ["bands", "resistance_bands"]:
        exercises = filter_exercises(resistance_bands)
    else:
        exercises = filter_exercises(bodyweight)

    return StrengthPlan(
        week=1,
        sessions_per_week=2,
        exercises=exercises,
        sets_reps="3 sets × 8-12 reps",
        progression="Add 1 rep per set each week, then add weight at 12 reps",
    )


def generate_cardio_plan(
    age: int,
    resting_hr: int,
    current_activity: str = "sedentary",
    joint_limitations: list[str] = None,
) -> list[CardioPlan]:
    """Generate 4-week cardio progression."""
    joint_limitations = joint_limitations or []

    # Zone 2 baseline
    z2_lower, z2_upper = calculate_zone2_hr(age, resting_hr)

    # Activity-based starting point
    if current_activity == "sedentary":
        z2_start = 20  # minutes
        interval_start = 0
    elif current_activity == "low":
        z2_start = 30
        interval_start = 1
    elif current_activity == "moderate":
        z2_start = 45
        interval_start = 1
    else:  # active
        z2_start = 60
        interval_start = 2

    # Format cardio based on limitations
    if "knee" in joint_limitations or "hip" in joint_limitations:
        cardio_types = ["Walking", "Elliptical", "Swimming", "Cycling"]
    else:
        cardio_types = ["Walking", "Jogging", "Cycling", "Swimming"]

    plans = []
    for week in range(1, 5):
        z2_mins = z2_start + (week - 1) * 10
        intervals = interval_start + (1 if week == 2 else 0)

        plans.append(CardioPlan(
            week=week,
            zone2_minutes=z2_mins,
            zone2_intensity="moderate",
            interval_sessions=intervals,
            interval_format="30s effort / 30s easy" if intervals > 0 else "N/A",
            weekly_progression=f"Week {week}: {z2_mins} min Zone 2, {intervals} interval sessions",
        ))

    return plans


def generate_strength_plan(
    equipment: str = "bodyweight",
    limitations: list[str] = None,
) -> list[StrengthPlan]:
    """Generate 4-week strength progression."""
    base = get_equipment_plan(equipment, limitations)

    plans = []
    for week in range(1, 5):
        sets_reps = base.sets_reps
        if week > 1:
            # Progress: increase volume
            sets_reps = f"3-4 sets × {10-reps(week)} reps"

        plans.append(StrengthPlan(
            week=week,
            sessions_per_week=2,
            exercises=base.exercises,
            sets_reps=sets_reps,
            progression=f"Week {week}: {base.progression}",
        ))

    return plans


async def generate_full_plan(
    age: int,
    sex: str,
    resting_hr: int = None,
    current_steps: int = 5000,
    equipment: str = "bodyweight",
    limitations: list[str] = None,
    conditions: list[str] = None,
) -> FullWorkoutPlan:
    """Generate complete cardio + strength plan."""
    # Get RHR if not provided
    if resting_hr is None:
        resting_hr = 70  # Default

    # Determine activity level from steps
    if current_steps < 5000:
        activity = "sedentary"
    elif current_steps < 7500:
        activity = "low"
    elif current_steps < 10000:
        activity = "moderate"
    else:
        activity = "active"

    # Generate plans
    cardio = generate_cardio_plan(age, resting_hr, activity, limitations)
    strength = generate_strength_plan(equipment, limitations)

    notes = [
        f"Zone 2 target HR: {calculate_zone2_hr(age, resting_hr)[0]}-{calculate_zone2_hr(age, resting_hr)[1]} BPM",
        "Warm up 5 min before, cool down 5 min after",
        "If any exercise causes pain, stop and consult your doctor",
        "Aim for conversation test: you should be able to talk but not sing during Zone 2",
    ]

    # Add condition-specific notes
    if conditions:
        if "hypertension" in conditions:
            notes.append("Avoid holding breath during exertion (Valsalva)")
        if "heart_failure" in conditions:
            notes.append("Start very gradually, monitor for shortness of breath")

    return FullWorkoutPlan(
        cardio=cardio,
        strength=strength,
        notes=notes,
    )


def format_plan_for_whatsapp(plan: FullWorkoutPlan) -> str:
    """Format workout plan as WhatsApp message."""
    lines = ["💪 *Your Personalized Cardio + Strength Plan*\n"]

    # Cardio
    lines.append("*Cardio (Zone 2 + Intervals)*")
    for cp in plan.cardio:
        lines.append(f"Week {cp.week}: {cp.zone2_minutes} min Zone 2 @ {cp.zone2_intensity}")
        if cp.interval_sessions > 0:
            lines.append(f"  + {cp.interval_sessions} interval session(s)")
    lines.append("")

    # Strength
    lines.append("*Strength (2x per week)*")
    sp = plan.strength[0]
    for ex in sp.exercises[:4]:
        lines.append(f"• {ex}")
    lines.append(f"Sets/Reps: {sp.sets_reps}")
    lines.append("")

    # Notes
    lines.append("*Notes:*")
    for note in plan.notes[:3]:
        lines.append(f"• {note}")

    return "\n".join(lines)


def reps(week: int) -> int:
    """Calculate reps based on week."""
    return max(8, 12 - week)