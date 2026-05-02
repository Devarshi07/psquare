"""Smoker's reduction protocol.

Progressive reduction with replacement behaviors.
Connects to Indian National Tobacco Cessation helpline: 1800-11-2356
"""
import structlog
from dataclasses import dataclass
from typing import Optional

log = structlog.get_logger()


@dataclass
class ReductionWeek:
    """One week of the reduction protocol."""
    week: int
    target_cigs: int
    reduction_from_baseline: int  # cigarettes reduced
    strategies: list[str]
    replacement_behaviors: list[str]


# 8-week reduction protocol
REDUCTION_PROTOCOL = [
    ReductionWeek(
        week=1,
        target_cigs=8,
        reduction_from_baseline=2,
        strategies=[
            "Smoke only after meals",
            "Drink water immediately after waking instead of smoking",
            "Brush teeth right after smoking to reduce appeal",
        ],
        replacement_behaviors=[
            "Chew sugar-free gum when urge hits",
            "Take deep breaths (4-7-8 technique)",
            "Call a friend instead of stepping out for a smoke",
        ],
    ),
    ReductionWeek(
        week=2,
        target_cigs=6,
        reduction_from_baseline=4,
        strategies=[
            "No smoking before noon",
            "Identify your triggers and plan alternatives",
            "Tell friends you're cutting down for support",
        ],
        replacement_behaviors=[
            "Go for a short walk when urge hits",
            "Eat a healthy snack (carrot, apple)",
            "Practice box breathing for 2 minutes",
        ],
    ),
    ReductionWeek(
        week=3,
        target_cigs=4,
        reduction_from_baseline=6,
        strategies=[
            "Smoke only at designated times (e.g., after dinner)",
            "Keep cigarettes in a different place",
            "Stop buying cigarettes - only smoke what you have",
        ],
        replacement_behaviors=[
            "Do 10 jumping jacks when urge hits",
            "Drink chai without tobacco",
            "Clean your hands/have a hand sanitizer",
        ],
    ),
    ReductionWeek(
        week=4,
        target_cigs=3,
        reduction_from_baseline=7,
        strategies=[
            "No smoking in the house",
            "Use nicotine patch if needed (consult doctor)",
            "Plan your day to avoid smoking triggers",
        ],
        replacement_behaviors=[
            "Squeeze a stress ball",
            "Apply a scent you dislike (peppermint)",
            "Play a game on your phone",
        ],
    ),
    ReductionWeek(
        week=5,
        target_cigs=2,
        reduction_from_baseline=8,
        strategies=[
            "Smoke only one cigarette per day maximum",
            "Write down why you want to quit",
            "Remove all smoking accessories from sight",
        ],
        replacement_behaviors=[
            "Take a hot shower",
            "Stretch for 2 minutes",
            "Write in your journal",
        ],
    ),
    ReductionWeek(
        week=6,
        target_cigs=1,
        reduction_from_baseline=9,
        strategies=[
            "Only smoke on special occasions",
            "Think of yourself as a non-smoker",
            "Reward yourself with something nice",
        ],
        replacement_behaviors=[
            "Meditate for 5 minutes",
            "Call the quitline for support",
            "Talk to a supportive friend",
        ],
    ),
    ReductionWeek(
        week=7,
        target_cigs=0,
        reduction_from_baseline=10,
        strategies=[
            "Quit day - mark it in your calendar",
            "Stay busy the first few days",
            "Avoid alcohol (triggers smoking)",
        ],
        replacement_behaviors=[
            "Chew nicotine gum if needed",
            "Eat healthy, regular meals",
            "Exercise to boost mood",
        ],
    ),
    ReductionWeek(
        week=8,
        target_cigs=0,
        reduction_from_baseline=10,
        strategies=[
            "Stay smoke-free - one day at a time",
            "If you slip up, don't give up - get back on track",
            "See a doctor for long-term support",
        ],
        replacement_behaviors=[
            "Celebrate milestones",
            "Join a support group",
            "Practice the breathing exercises daily",
        ],
    ),
]


def get_protocol_for_cigarettes_per_day(cigs_per_day: int) -> list[ReductionWeek]:
    """Get the reduction protocol based on current smoking."""
    if cigs_per_day <= 5:
        # Already low - faster protocol
        return REDUCTION_PROTOCOL[4:]  # Start from week 5
    elif cigs_per_day <= 10:
        return REDUCTION_PROTOCOL[2:]  # Start from week 3
    else:
        return REDUCTION_PROTOCOL  # Full 8-week


def get_current_week(cigs_per_day: int) -> int:
    """Calculate which week of protocol user is on."""
    if cigs_per_day >= 10:
        return 1
    elif cigs_per_day >= 8:
        return 2
    elif cigs_per_day >= 6:
        return 3
    elif cigs_per_day >= 4:
        return 4
    elif cigs_per_day >= 2:
        return 5
    elif cigs_per_day >= 1:
        return 6
    else:
        return 7  # Quit


def format_protocol_for_whatsapp(
    cigs_per_day: int,
    protocol: list[ReductionWeek] = None,
) -> str:
    """Format smoker protocol as WhatsApp message."""
    if protocol is None:
        protocol = get_protocol_for_cigarettes_per_day(cigs_per_day)

    current_week = get_current_week(cigs_per_day)

    lines = [
        "🚭 *Your Smoking Reduction Plan*",
        "",
        f"Current: {cigs_per_day} cigarettes/day",
        f"Goal: Quit in {len(protocol)} weeks",
        "",
        "*This week's focus:*",
    ]

    if current_week <= len(protocol):
        week = protocol[current_week - 1]
        lines.append(f"Week {week.week}: Target {week.target_cigs} cigarettes")
        lines.append("")
        lines.append("*Strategies:*")
        for s in week.strategies[:2]:
            lines.append(f"• {s}")
        lines.append("")
        lines.append("*When craving hits:*")
        for r in week.replacement_behaviors[:2]:
            lines.append(f"• {r}")

    lines.append("")
    lines.append("📞 *Need support?*")
    lines.append("Call National Tobacco Quitline: 1800-11-2356")

    return "\n".join(lines)


def format_encouragement(cigs_per_day: int, streak_days: int) -> str:
    """Format encouragement message."""
    if cigs_per_day == 0 and streak_days > 0:
        return (
            f"🎉 *{streak_days} days smoke-free!* "
            "You're doing amazing. Keep going - it gets easier!"
        )
    elif streak_days >= 3:
        return (
            f"💪 *{streak_days} day streak!* "
            "You've reduced by a lot. The cravings are getting weaker - stay strong!"
        )
    elif cigs_per_day <= 3:
        return (
            "🌟 Almost there! You're so close to being smoke-free. "
            "Think about how much better you'll feel."
        )
    else:
        return (
            "💪 Every cigarette you don't smoke is a win. "
            "Your heart is thanking you with every reduction."
        )