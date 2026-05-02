"""Biological age questionnaire - 5 questions max.

Per CLAUDE.md §11.2:
1. Sleep: hours/night
2. Sun: daily outdoor exposure
3. Sugar: processed food frequency
4. Smoking + alcohol
5. Stress + activity
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class BioAgeQuestionnaire:
    """The 5-question bio age questionnaire."""
    sleep: str  # "<5", "5-6", "6-7", "7-8", "8+"
    sun: str  # "none", "<15min", "15-60min", "1hr+"
    sugar: str  # "daily", "3-5x", "1-2x", "rarely"
    smoking_alcohol: str  # "both", "smoke_only", "drink_only", "neither"
    stress_activity: str  # "exhausted", "tired", "ok", "energized"


# WhatsApp interactive buttons format
QUESTIONNAIRE_BUTTONS = {
    "sleep": {
        "type": "button",
        "header": "Q1: Average hours of sleep per night?",
        "options": ["<5", "5-6", "6-7", "7-8", "8+"]
    },
    "sun": {
        "type": "button",
        "header": "Q2: Daily outdoor sun exposure (without sunscreen on body)?",
        "options": ["None", "<15 min", "15-60 min", "1+ hr"]
    },
    "sugar": {
        "type": "button",
        "header": "Q3: How often do you eat sweets, packaged snacks, sugary drinks?",
        "options": ["Daily", "3-5×/wk", "1-2×/wk", "Rarely"]
    },
    "smoking_alcohol": {
        "type": "button",
        "header": "Q4: Smoke or drink regularly?",
        "options": ["Both", "Smoke only", "Drink only", "Neither"]
    },
    "stress_activity": {
        "type": "button",
        "header": "Q5: Most days I feel...",
        "options": ["Energized & active", "OK", "Tired", "Exhausted"]
    },
}


def format_question_for_whatsapp(q_num: int, key: str) -> str:
    """Format a question for WhatsApp."""
    q = QUESTIONNAIRE_BUTTONS.get(key)
    if not q:
        return ""

    lines = [f"**Q{q_num}: {q['header']}**", ""]

    for i, opt in enumerate(q["options"], 1):
        lines.append(f"{i}. {opt}")

    return "\n".join(lines)


def format_all_questions_for_whatsapp() -> str:
    """Format all 5 questions."""
    lines = [
        "🧬 *Biological Age Questionnaire*",
        "",
        "These 5 questions help estimate your biological age.",
        "Answer each with the number or button.",
        "",
    ]

    for i, (key, q) in enumerate(QUESTIONNAIRE_BUTTONS.items(), 1):
        lines.append(f"**Q{i}: {q['header']}**")
        for j, opt in enumerate(q["options"], 1):
            lines.append(f"  {j}. {opt}")
        lines.append("")

    return "\n".join(lines)


def parse_questionnaire_response(question_num: int, answer: str, current: dict) -> dict:
    """Parse a single question answer."""
    answer_lower = answer.lower().strip()

    if question_num == 1:  # Sleep
        if "5" in answer_lower and "6" in answer_lower:
            current["sleep"] = "5-6"
        elif "6" in answer_lower and "7" in answer_lower:
            current["sleep"] = "6-7"
        elif "7" in answer_lower and "8" in answer_lower:
            current["sleep"] = "7-8"
        elif answer_lower.startswith("<5") or "under 5" in answer_lower:
            current["sleep"] = "<5"
        elif "8+" in answer_lower or "more than 8" in answer_lower:
            current["sleep"] = "8+"
        else:
            current["sleep"] = "7-8"  # Default

    elif question_num == 2:  # Sun
        if "none" in answer_lower or "no" in answer_lower:
            current["sun"] = "none"
        elif "15" in answer_lower:
            current["sun"] = "15-60min"
        elif "1 hr" in answer_lower or "1hr" in answer_lower or "more" in answer_lower:
            current["sun"] = "1hr+"
        elif "15" not in answer_lower and "min" in answer_lower:
            current["sun"] = "<15min"
        else:
            current["sun"] = "15-60min"

    elif question_num == 3:  # Sugar
        if "daily" in answer_lower or "every day" in answer_lower:
            current["sugar"] = "daily"
        elif "3-5" in answer_lower or "3 to 5" in answer_lower:
            current["sugar"] = "3-5x"
        elif "1-2" in answer_lower or "1 to 2" in answer_lower or "occasional" in answer_lower:
            current["sugar"] = "1-2x"
        else:
            current["sugar"] = "rarely"

    elif question_num == 4:  # Smoking + alcohol
        if "both" in answer_lower:
            current["smoking_alcohol"] = "both"
        elif "smoke" in answer_lower and "drink" not in answer_lower:
            current["smoking_alcohol"] = "smoke_only"
        elif "drink" in answer_lower and "smoke" not in answer_lower:
            current["smoking_alcohol"] = "drink_only"
        else:
            current["smoking_alcohol"] = "neither"

    elif question_num == 5:  # Stress + activity
        if "energized" in answer_lower or "active" in answer_lower:
            current["stress_activity"] = "energized"
        elif "exhausted" in answer_lower:
            current["stress_activity"] = "exhausted"
        elif "tired" in answer_lower:
            current["stress_activity"] = "tired"
        else:
            current["stress_activity"] = "ok"

    return current


def is_questionnaire_complete(answers: dict) -> bool:
    """Check if all 5 questions are answered."""
    required = ["sleep", "sun", "sugar", "smoking_alcohol", "stress_activity"]
    return all(answers.get(k) for k in required)


def questionnaire_to_answers(questions: dict) -> BioAgeQuestionnaire:
    """Convert questionnaire dict to typed object."""
    return BioAgeQuestionnaire(
        sleep=questions.get("sleep", "7-8"),
        sun=questions.get("sun", "15-60min"),
        sugar=questions.get("sugar", "rarely"),
        smoking_alcohol=questions.get("smoking_alcohol", "neither"),
        stress_activity=questions.get("stress_activity", "ok"),
    )