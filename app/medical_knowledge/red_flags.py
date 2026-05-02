"""Red flag detection for cardiovascular emergencies.

These trigger immediate escalation regardless of conversation state.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RedFlagSeverity(str, Enum):
    EMERGENCY = "emergency"  # Call 112/108 now
    URGENT = "urgent"  # See doctor within 24-48 hours
    WARNING = "warning"  # Recommend doctor visit


@dataclass
class RedFlag:
    severity: RedFlagSeverity
    keywords: list[str]
    message: str
    escalation: str


# Heart attack symptoms
HEART_ATTACK_FLAGS = [
    RedFlag(
        severity=RedFlagSeverity.EMERGENCY,
        keywords=[
            "chest pain", "chest pressure", "chest tightness", "chest heaviness",
            "pain in chest", "squeezing chest", "crushing chest", "heavy chest",
            "arm pain", "left arm pain", "jaw pain", "neck pain",
            "shoulder pain", "back pain", "pain spreading",
        ],
        message="Chest pain or pressure can be a heart attack. Call 112 now.",
        escalation="Call 112 (India emergency) or 911. Do not drive. Ask someone to take you or call ambulance.",
    ),
]

# Stroke symptoms (FAST)
STROKE_FLAGS = [
    RedFlag(
        severity=RedFlagSeverity.EMERGENCY,
        keywords=[
            "face drooping", "face droop", "drooping face", "smile uneven",
            "arm weakness", "arm numbness", "cant lift arm", "cant raise arm",
            "speech slurred", "cant speak", "cant talk", "confused speech",
            "dizzy", "loss of balance", "cant walk", "lost balance",
            "numbness", "tingling one side", "one side weak",
        ],
        message="These symptoms could be a stroke. Act FAST.",
        escalation="Call 112 immediately. F=Face drooping, A=Arm weakness, S=Speech difficulty, T=Time to call.",
    ),
]

# Breathing emergencies
BREATHING_FLAGS = [
    RedFlag(
        severity=RedFlagSeverity.EMERGENCY,
        keywords=[
            "cant breathe", "cant breath", "shortness of breath at rest",
            "sudden breathlessness", "breathing difficulty", "wheezing severe",
            "blue lips", "blue fingers", "turning blue",
        ],
        message="Severe breathing difficulty needs immediate attention.",
        escalation="Call 112 or 108. Do not lie down. Sit upright and wait for help.",
    ),
]

# Syncope/fainting
SYNCOPE_FLAGS = [
    RedFlag(
        severity=RedFlagSeverity.EMERGENCY,
        keywords=[
            "fainted", "faint", "passed out", "lost consciousness",
            "passed out", "unconscious", "blacked out",
        ],
        message="Fainting can be serious, especially with no warning.",
        escalation="Call 112 if fainting was sudden, accompanied by chest pain, or person doesn't wake quickly.",
    ),
]

# Hypertensive crisis
BP_CRISIS_FLAGS = [
    RedFlag(
        severity=RedFlagSeverity.EMERGENCY,
        keywords=["bp 180", "blood pressure 180", "over 180"],
        message="Very high blood pressure detected.",
        escalation="Call 112 if you have symptoms like chest pain, breathlessness, headache, or vision changes.",
    ),
]

# Severe palpitations
PALPITATION_FLAGS = [
    RedFlag(
        severity=RedFlagSeverity.URGENT,
        keywords=[
            "heart racing", "heart beating fast", "palpitations",
            "irregular heartbeat", "heart skipped", "heart fluttering",
        ],
        message="Rapid or irregular heartbeat can be serious.",
        escalation="See a cardiologist within 48 hours. If accompanied by chest pain, dizziness, or shortness of breath, call 112.",
    ),
]

# All flags combined for scanning
ALL_FLAGS = (
    HEART_ATTACK_FLAGS + STROKE_FLAGS + BREATHING_FLAGS + SYNCOPE_FLAGS + BP_CRISIS_FLAGS + PALPITATION_FLAGS
)


def check_red_flags(text: str) -> Optional[RedFlag]:
    """Check text for red flag keywords.

    Returns the highest severity flag found, or None.
    """
    text_lower = text.lower()

    # Check in order of severity (emergency first)
    severity_order = [
        RedFlagSeverity.EMERGENCY,
        RedFlagSeverity.URGENT,
        RedFlagSeverity.WARNING,
    ]

    for severity in severity_order:
        for flag in ALL_FLAGS:
            if flag.severity == severity:
                for keyword in flag.keywords:
                    if keyword in text_lower:
                        return flag

    return None


def check_bp_emergency(systolic: int, diastolic: int, has_symptoms: bool = False) -> Optional[RedFlag]:
    """Check if BP reading is in crisis range."""
    if systolic >= 180 or diastolic >= 120:
        if has_symptoms or systolic >= 200 or diastolic >= 130:
            return RedFlag(
                severity=RedFlagSeverity.EMERGENCY,
                keywords=["bp crisis"],
                message=f"BP {systolic}/{diastolic} is in crisis range.",
                escalation="Call 112 now. This is a hypertensive emergency.",
            )
        else:
            return RedFlag(
                severity=RedFlagSeverity.URGENT,
                keywords=["bp very high"],
                message=f"BP {systolic}/{diastolic} is very high.",
                escalation="Consult a doctor today or go to emergency if you have symptoms.",
            )
    return None


def check_ppg_emergency(hr: float, rmssd: float, is_irregular: bool = False) -> Optional[RedFlag]:
    """Check if PPG results indicate emergency."""
    # Very low or high heart rate
    if hr < 40:
        return RedFlag(
            severity=RedFlagSeverity.URGENT,
            keywords=["hr very low"],
            message=f"Heart rate {hr} BPM is very low.",
            escalation="This can be serious. Please consult a doctor today.",
        )
    if hr > 130:
        return RedFlag(
            severity=RedFlagSeverity.URGENT,
            keywords=["hr very high"],
            message=f"Heart rate {hr} BPM is very high.",
            escalation="Please see a doctor if this persists. Call 112 if you have chest pain or dizziness.",
        )

    # Irregular heartbeat detected
    if is_irregular:
        return RedFlag(
            severity=RedFlagSeverity.URGENT,
            keywords=["irregular heartbeat"],
            message="Irregular heartbeat pattern detected.",
            escalation="PPG cannot diagnose, but please get an ECG within the week. If you feel unwell, call 112.",
        )

    return None


# Hindi/Hinglish translations for common flags (for India)
HINDI_FLAGS = [
    # Chest pain
    "दर्द", "छाती में दर्द", "छाती में दबाव", "छाती में जकड़न",
    # Breathing
    "साँस नहीं आती", "साँस फूलना", "साँस में तकलीफ",
    # Fainting
    "बेहोश हो गया", "बेहोश", "होश नहीं आता",
    # Stroke
    "बोल नहीं पाता", "बात नहीं आती", "चेहरा टेड़ा", "हाथ नहीं उठा पाता",
]


def check_red_flags_hindi(text: str) -> Optional[RedFlag]:
    """Check Hindi text for red flags."""
    text_lower = text.lower()

    for keyword in HINDI_FLAGS:
        if keyword in text_lower:
            # Return generic emergency for Hindi matches
            return RedFlag(
                severity=RedFlagSeverity.EMERGENCY,
                keywords=[keyword],
                message="तुरंत डॉक्टर को दिखाएं या 112 पर कॉल करें।",
                escalation="Call 112 or see a doctor immediately.",
            )

    return None