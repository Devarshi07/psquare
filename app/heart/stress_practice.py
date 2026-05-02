"""Stress & HRV micro-practices.

Daily 5-minute protocols picked for the user.
"""
import structlog
from dataclasses import dataclass
from enum import Enum
from typing import Optional

log = structlog.get_logger()


class PracticeType(str, Enum):
    """Available stress practices."""
    BOX_BREATHING = "box_breathing"
    BREATHING_478 = "breathing_478"
    WALK_BREATHING = "walk_breathing"
    GRATITUDE = "gratitude"
    MEDITATION = "meditation"
    PRAYER = "prayer"


@dataclass
class StressPractice:
    """A stress reduction practice."""
    name: str
    practice_type: PracticeType
    duration_minutes: int
    instructions: list[str]
    benefits: list[str]
    why_this: str = ""  # Why picked for this user


# Practice library
PRACTICES = {
    PracticeType.BOX_BREATHING: StressPractice(
        name="Box Breathing",
        practice_type=PracticeType.BOX_BREATHING,
        duration_minutes=5,
        instructions=[
            "1. Inhale for 4 seconds",
            "2. Hold for 4 seconds",
            "3. Exhale for 4 seconds",
            "4. Hold for 4 seconds",
            "5. Repeat 5-10 cycles",
        ],
        benefits=["Reduces cortisol", "Lowers HR", "Calms nervous system"],
        why_this="Great for anxiety; simple to remember",
    ),
    PracticeType.BREATHING_478: StressPractice(
        name="4-7-8 Breathing",
        practice_type=PracticeType.BREATHING_478,
        duration_minutes=5,
        instructions=[
            "1. Inhale through nose for 4 seconds",
            "2. Hold for 7 seconds",
            "3. Exhale through mouth for 8 seconds",
            "4. Repeat 3-4 cycles",
        ],
        benefits=["Promotes sleep", "Reduces anxiety", "Activates parasympathetic"],
        why_this="Excellent for sleep; calms racing thoughts",
    ),
    PracticeType.WALK_BREATHING: StressPractice(
        name="Walk + Slow Breathing",
        practice_type=PracticeType.WALK_BREATHING,
        duration_minutes=10,  # 5 min walk + breathing
        instructions=[
            "1. Take a brisk 5-minute walk",
            "2. Walk at a pace where you can speak but not sing",
            "3. Focus on taking 6 breaths per minute",
            "4. Count: inhale 1-2-3, exhale 1-2-3-4-5-6",
        ],
        benefits=["Movement + breath", "Reduces stress hormones", "Improves circulation"],
        why_this="Combines movement with breath for high stress days",
    ),
    PracticeType.GRATITUDE: StressPractice(
        name="Gratitude Journal",
        practice_type=PracticeType.GRATITUDE,
        duration_minutes=5,
        instructions=[
            "1. Write down 3 things you're grateful for today",
            "2. Write 1 thing that went well",
            "3. Write 1 thing you're looking forward to",
        ],
        benefits=["Shifts mindset", "Improves sleep", "Increases positive emotions"],
        why_this="Builds resilience; great for low-mood days",
    ),
    PracticeType.MEDITATION: StressPractice(
        name="Body Scan Meditation",
        practice_type=PracticeType.MEDITATION,
        duration_minutes=5,
        instructions=[
            "1. Sit or lie down comfortably",
            "2. Close eyes, breathe naturally",
            "3. Focus attention on toes, then feet, ankles...",
            "4. Slowly move up body, noticing sensations",
            "5. Release tension in each area",
        ],
        benefits=["Reduces physical tension", "Increases body awareness", "Calms mind"],
        why_this="Good for stress manifesting as physical tension",
    ),
    PracticeType.PRAYER: StressPractice(
        name="Prayer / Reflection",
        practice_type=PracticeType.PRAYER,
        duration_minutes=5,
        instructions=[
            "1. Find a quiet space",
            "2. Close eyes, breathe slowly",
            "3. Speak or think your prayer/reflection",
            "4. Focus on what you can control",
            "5. Release what you cannot",
        ],
        benefits=["Provides meaning", "Reduces anxiety", "Creates perspective"],
        why_this="Good for those who find comfort in spirituality",
    ),
}


def pick_practice_for_user(
    hrv_trend: str = "stable",  # "up", "down", "stable"
    stress_score: int = 5,  # 1-10
    sleep_hours: float = 7.0,
    user_preference: str = None,  # User's preferred practice
) -> StressPractice:
    """Pick the best practice for the user's current state.

    If HRV trending down for 3+ days, switch to different practice.
    """
    # If user has preference, use that
    if user_preference:
        practice_type = PracticeType(user_preference.lower())
        if practice_type in PRACTICES:
            return PRACTICES[practice_type]

    # Otherwise, pick based on state
    if hrv_trend == "down" and stress_score >= 7:
        # High stress + declining HRV = most calming
        return PRACTICES[PracticeType.BREATHING_478]

    if sleep_hours < 6:
        # Poor sleep = focus on sleep-inducing
        return PRACTICES[PracticeType.BREATHING_478]

    if stress_score >= 7:
        # High stress
        return PRACTICES[PracticeType.BOX_BREATHING]

    if stress_score >= 5:
        # Moderate stress
        return PRACTICES[PracticeType.MEDITATION]

    # Low stress - maintenance
    return PRACTICES[PracticeType.GRATITUDE]


def format_practice_for_whatsapp(practice: StressPractice, user_name: str = None) -> str:
    """Format practice as WhatsApp message."""
    name = user_name or "there"

    lines = [
        f"🧘 *5-Minute Practice for {name}*",
        "",
        f"*{practice.name}* ({practice.duration_minutes} min)",
        "",
        "*How to do it:*",
    ]

    for instruction in practice.instructions:
        lines.append(instruction)

    lines.append("")
    lines.append("*Benefits:*")
    for benefit in practice.benefits:
        lines.append(f"• {benefit}")

    lines.append("")
    lines.append(f"_Why this: {practice.why_this}_")

    return "\n".join(lines)


async def get_daily_practice(user_profile: dict) -> str:
    """Get today's practice recommendation."""
    hrv_trend = user_profile.get("hrv_trend", "stable")
    stress_score = user_profile.get("stress_score", 5)
    sleep_hours = user_profile.get("sleep_hours", 7.0)
    preferred = user_profile.get("preferred_practice")

    practice = pick_practice_for_user(
        hrv_trend=hrv_trend,
        stress_score=stress_score,
        sleep_hours=sleep_hours,
        user_preference=preferred,
    )

    return format_practice_for_whatsapp(practice, user_profile.get("name"))