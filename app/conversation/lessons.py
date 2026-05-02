"""Educational micro-lessons.

60-second explainers on heart health topics.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Lesson:
    """A 60-second explainer lesson."""
    id: str
    title: str
    topic: str
    content: str  # ~150 words for ~60 sec reading
    key_points: list[str]


# Lesson library
LESSONS = {
    "ldl": Lesson(
        id="ldl",
        title="What is LDL Cholesterol?",
        topic="Cholesterol",
        content="""LDL stands for Low-Density Lipoprotein — often called "bad cholesterol." It's the cholesterol that can build up in your artery walls, forming plaque that narrows your arteries and increases heart attack risk.

Think of LDL as the delivery truck that drops off cholesterol to your tissues. When there's too much, some "falls off" along the way and sticks to your artery walls.

Lower LDL levels mean less plaque buildup. For most people, LDL below 100 mg/dL is optimal. Lifestyle changes — more fiber, less saturated fat, regular exercise — can lower LDL by 10-30%.""",
        key_points=[
            "LDL delivers cholesterol to tissues",
            "Too much LDL = plaque in arteries",
            "Target: below 100 mg/dL",
            "Diet + exercise can lower it 10-30%",
        ],
    ),

    "hrv": Lesson(
        id="hrv",
        title="What is HRV?",
        topic="PPG Metrics",
        content="""HRV stands for Heart Rate Variability — the variation in time between your heartbeats. A higher HRV generally means your heart is more adaptable and responsive to different situations.

Think of it as your heart's flexibility. A high HRV means your nervous system can easily switch between "rest and digest" (parasympathetic) and "fight or flight" (sympathetic) modes.

Low HRV can mean chronic stress, poor sleep, or overtraining. Things that improve HRV: quality sleep, breathing exercises, meditation, and regular moderate exercise.""",
        key_points=[
            "HRV = beat-to-beat variation",
            "Higher HRV = more adaptable heart",
            "Low HRV = stress, poor sleep, overtraining",
            "Breathing + sleep improve HRV",
        ],
    ),

    "rmssd": Lesson(
        id="rmssd",
        title="What is RMSSD?",
        topic="PPG Metrics",
        content="""RMSSD (Root Mean Square of Successive Differences) is the most common way to measure HRV. It specifically looks at how much your heart rate changes from one beat to the next.

It's like measuring how quickly your heart adjusts between beats. Higher RMSSD means your parasympathetic nervous system (the "rest and digest" mode) is active and healthy.

For adults, RMSSD typically ranges from 20-50 ms. Younger people tend to have higher values. What matters most is your own baseline — trends matter more than absolute numbers.""",
        key_points=[
            "RMSSD measures beat-to-beat changes",
            "Higher = more parasympathetic activity",
            "Typical range: 20-50 ms",
            "Your baseline is your benchmark",
        ],
    ),

    "heart_age": Lesson(
        id="heart_age",
        title="What is Heart Age?",
        topic="Risk Assessment",
        content="""Your heart age is the age at which a person with all optimal risk factors would have the same 10-year cardiovascular risk as you.

If you're 40 but your heart age is 50, your heart is "aging faster" than it should. The good news: improving your risk factors can lower your heart age.

Heart age accounts for factors like blood pressure, cholesterol, smoking, and family history. It's a more intuitive way to understand your heart health than just a risk percentage.""",
        key_points=[
            "Heart age = risk-equivalent age",
            "Higher = faster aging heart",
            "Lower BP, cholesterol, quit smoking",
            "Can be reduced with lifestyle changes",
        ],
    ),

    "qrisk3": Lesson(
        id="qrisk3",
        title="What is QRISK3?",
        topic="Risk Assessment",
        content="""QRISK3 is a calculator that estimates your 10-year risk of heart attack or stroke. It's widely used in the UK and considered more accurate than older tools because it includes more risk factors.

It considers: age, sex, ethnicity, smoking, diabetes, family history, blood pressure, cholesterol, BMI, and kidney disease. South Asian ethnicity is accounted for — we have higher cardiovascular risk.

A risk under 10% is considered low. 10-20% is moderate, over 20% is high. Even if your risk is low, lifestyle matters for long-term heart health.""",
        key_points=[
            "QRISK3 = 10-year risk calculator",
            "More accurate than older tools",
            "Includes South Asian ethnicity",
            "Under 10% = low risk",
        ],
    ),

    "lpa": Lesson(
        id="lpa",
        title="Why Does Lipoprotein(a) Matter?",
        topic="Advanced Metrics",
        content="""Lipoprotein(a) — written Lp(a) — is a particle in your blood that carries cholesterol. It's genetically determined and doesn't change much with lifestyle.

High Lp(a) (>50 mg/dL) is an independent risk factor for heart attack and stroke. It's particularly common in South Asian populations.

Unlike LDL, Lp(a) isn't usually affected by diet or exercise. Statins can help lower cardiovascular risk in people with high Lp(a), but you need a specific blood test to check it.""",
        key_points=[
            "Lp(a) = genetic cholesterol particle",
            "High levels increase heart risk",
            "Common in South Asians",
            "Check once in a lifetime",
        ],
    ),

    "bp": Lesson(
        id="bp",
        title="Understanding Blood Pressure",
        topic="Blood Pressure",
        content="""Blood pressure has two numbers: systolic (top) and diastolic (bottom). Systolic is the pressure when your heart beats, diastolic is the pressure between beats.

Normal is under 120/80 mmHg. Elevated is 120-129/under 80. Stage 1 hypertension is 130-139 or 80-89. Stage 2 is 140+ or 90+. A crisis is 180+/120+.

For South Asians, even slightly elevated BP matters more — we see complications at lower numbers. The good news: lifestyle changes can lower BP significantly.""",
        key_points=[
            "Systolic = beat pressure",
            "Diastolic = between beats",
            "Normal: under 120/80",
            "South Asians affected at lower numbers",
        ],
    ),

    "ppg": Lesson(
        id="ppg",
        title="How Does PPG Work?",
        topic="Technology",
        content="""PPG stands for Photoplethysmography — a way to measure heart rate using a camera and light. When you place your finger over the camera, the flash illuminates your blood vessels.

Your blood absorbs the light, and the camera detects the changes in light reflection with each heartbeat. This creates a waveform that can extract heart rate and heart rate variability.

PPG isn't as accurate as an ECG or medical pulse oximeter, but it's great for wellness tracking and spotting trends over time. It's a convenient way to monitor your heart daily.""",
        key_points=[
            "PPG = light-based pulse detection",
            "Uses camera + flash",
            "Extracts HR and HRV",
            "Good for trends, not diagnosis",
        ],
    ),
}


def get_lesson_by_id(lesson_id: str) -> Optional[Lesson]:
    """Get a specific lesson by ID."""
    return LESSONS.get(lesson_id)


def get_lesson_by_topic(topic: str) -> list[Lesson]:
    """Get all lessons for a topic."""
    return [l for l in LESSONS.values() if l.topic.lower() == topic.lower()]


def format_lesson_for_whatsapp(lesson: Lesson) -> str:
    """Format lesson as WhatsApp message."""
    lines = [
        f"📚 *{lesson.title}*",
        "",
        f"_{lesson.content}_",
        "",
        "*Key points:*",
    ]

    for point in lesson.key_points:
        lines.append(f"• {point}")

    lines.append("")
    lines.append("Want to learn about something else? Just ask!")

    return "\n".join(lines)


def get_available_topics() -> list[str]:
    """Get list of available lesson topics."""
    topics = set()
    for lesson in LESSONS.values():
        topics.add(lesson.topic)
    return sorted(list(topics))


async def handle_lesson_request(topic: str) -> str:
    """Handle user's lesson request."""
    # Map common requests to lesson IDs
    topic_map = {
        "cholesterol": "ldl",
        "ldl": "ldl",
        "hdl": "ldl",
        "hrv": "hrv",
        "heart rate variability": "hrv",
        "rmssd": "rmssd",
        "heart age": "heart_age",
        "qrisk": "qrisk3",
        "risk": "qrisk3",
        "lipoprotein": "lpa",
        "lpa": "lpa",
        "blood pressure": "bp",
        "bp": "bp",
        "ppg": "ppg",
        "how ppg works": "ppg",
    }

    topic_lower = topic.lower().strip()
    lesson_id = topic_map.get(topic_lower)

    if lesson_id and lesson_id in LESSONS:
        return format_lesson_for_whatsapp(LESSONS[lesson_id])

    # Topic not found - offer options
    topics = get_available_topics()
    lines = ["Here are topics I can explain:", ""]
    for t in topics:
        lessons_in_topic = get_lesson_by_topic(t)
        lesson_names = ", ".join([l.title for l in lessons_in_topic])
        lines.append(f"*{t}:* {lesson_names}")

    return "\n".join(lines)