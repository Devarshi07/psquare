"""Conversation state machine for onboarding and ongoing conversations."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import structlog

from app.db import get_db_session
from app.db.models import (
    User,
    Profile,
    MedicalHistory,
    Medication,
    FamilyHistory,
    LabResult,
    BPReading,
    SmokingLog,
    Conversation,
    Message,
    MessageDirection,
)

log = structlog.get_logger()


class ConversationState(str, Enum):
    """States in the conversation flow."""
    NEW = "new"
    ONBOARDING = "onboarding"
    COMPLETED = "completed"
    PPG_SCAN = "ppg_scan"
    BIOAGE_SCAN = "bioage_scan"
    DAILY_CHECKIN = "daily_checkin"
    WEEKLY_CHECKIN = "weekly_checkin"


class OnboardingStep(int, Enum):
    """The 12 onboarding questions."""
    Q1_NAME_AGE_SEX = 1  # Combined: name, age, sex
    Q2_CITY = 2
    Q3_HEIGHT_WEIGHT_WAIST = 3  # Combined
    Q4_BP = 4
    Q5_LIPIDS = 5  # LDL, HDL, Trig, Total
    Q6_GLUCOSE = 6  # HbA1c or fasting glucose
    Q7_CONDITIONS = 7  # Multi-select
    Q8_MEDICATIONS = 8
    Q9_FAMILY_HISTORY = 9
    Q10_SMOKING = 10
    Q11_ACTIVITY_DIET = 11
    Q12_SLEEP_STRESS = 12
    COMPLETE = 99


@dataclass
class UserState:
    """Current state of a user's conversation."""
    phone: str
    state: ConversationState = ConversationState.NEW
    onboarding_step: OnboardingStep = OnboardingStep.Q1_NAME_AGE_SEX
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None

    # Parsed answers (accumulated)
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    city: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    waist_cm: Optional[float] = None

    # BP
    systolic: Optional[float] = None
    diastolic: Optional[float] = None

    # Lipids
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    tg: Optional[float] = None
    total_chol: Optional[float] = None

    # Glucose
    hba1c: Optional[float] = None
    fasting_glucose: Optional[float] = None

    # Medical
    conditions: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)

    # Family history
    family_history_early_chd: Optional[bool] = None
    family_history_age: Optional[int] = None

    # Smoking
    smoking_status: str = "never"  # never, former, current
    cigarettes_per_day: Optional[int] = None

    # Lifestyle
    daily_steps: Optional[int] = None
    diet_type: Optional[str] = None  # veg, non-veg, eggetarian
    cuisine: Optional[str] = None

    # Sleep/stress
    sleep_hours: Optional[float] = None
    stress_score: Optional[int] = None  # 1-10


# Question prompts for onboarding
ONBOARDING_PROMPTS = {
    OnboardingStep.Q1_NAME_AGE_SEX: {
        "text": "Let's get started! First, tell me about yourself.\n\n"
                "**Q1: What's your name, age, and sex?**\n"
                "Example: Rahul, 42, Male",
        "type": "text",
    },
    OnboardingStep.Q2_CITY: {
        "text": "**Q2: What city do you live in?**",
        "type": "text",
    },
    OnboardingStep.Q3_HEIGHT_WEIGHT_WAIST: {
        "text": "**Q3: Your height, weight, and waist circumference?**\n"
                "Example: 175 cm, 78 kg, 85 cm\n\n"
                "💡 To measure waist: use a tape at your belly button level, "
                "exhale naturally and measure.",
        "type": "text",
    },
    OnboardingStep.Q4_BP: {
        "text": "**Q4: What's your most recent blood pressure?**\n"
                "Example: 120/80\n\n"
                "Reply with the numbers, or 'Don't know' if you haven't checked recently.",
        "type": "text",
    },
    OnboardingStep.Q5_LIPIDS: {
        "text": "**Q5: Your latest cholesterol panel?**\n"
                "Please share: LDL, HDL, Triglycerides, Total Cholesterol\n"
                "Example: 130, 45, 140, 210\n\n"
                "Or 'Don't know' if you haven't gotten a lipid test.",
        "type": "text",
    },
    OnboardingStep.Q6_GLUCOSE: {
        "text": "**Q6: Blood sugar / HbA1c?**\n"
                "Example: 5.8% (HbA1c) or 105 mg/dL (fasting)\n\n"
                "Or 'Don't know'.",
        "type": "text",
    },
    OnboardingStep.Q7_CONDITIONS: {
        "text": "**Q7: Any diagnosed conditions?**\n\n"
                "Select all that apply:\n"
                "• None\n"
                "• High blood pressure (Hypertension)\n"
                "• High cholesterol\n"
                "• Type 2 Diabetes\n"
                "• Heart attack (in the past)\n"
                "• Stent / Angioplasty\n"
                "• Bypass surgery (CABG)\n"
                "• Atrial fibrillation (AFib)\n"
                "• Heart failure\n"
                "• Stroke / TIA",
        "type": "list",  # Would use WhatsApp interactive list
    },
    OnboardingStep.Q8_MEDICATIONS: {
        "text": "**Q8: Current medications?**\n\n"
                "List any heart/BP/cholesterol/diabetes meds you're taking.\n"
                "Example: Amlodipine 5mg, Atorvastatin 20mg\n\n"
                "Or 'None' if not taking any.",
        "type": "text",
    },
    OnboardingStep.Q9_FAMILY_HISTORY: {
        "text": "**Q9: Family heart history?**\n\n"
                "Did any parent or sibling have a heart attack, stroke, or sudden "
                "cardiac death?\n\n"
                "• No\n"
                "• Yes - under age 55\n"
                "• Yes - under age 65\n"
                "• Yes - age 65 or older\n"
                "• Don't know",
        "type": "buttons",
    },
    OnboardingStep.Q10_SMOKING: {
        "text": "**Q10: Smoking status?**\n\n"
                "• Never smoked\n"
                "• Former smoker (quit)\n"
                "• Current smoker",
        "type": "buttons",
    },
    OnboardingStep.Q11_ACTIVITY_DIET: {
        "text": "**Q11: Activity & Diet**\n\n"
                "1. Typical daily steps (estimate):\n"
                "   • <5000 • 5000-7500 • 7500-10000 • 10000+\n\n"
                "2. Diet: Vegetarian / Non-vegetarian / Eggetarian\n\n"
                "3. Your cuisine type (for meal suggestions): North Indian / South Indian / "
                "Mixed / Other",
        "type": "text",
    },
    OnboardingStep.Q12_SLEEP_STRESS: {
        "text": "**Q12: Sleep & Stress**\n\n"
                "1. Average hours of sleep per night? ⏰\n"
                "   • <5 • 5-6 • 6-7 • 7-8 • 8+\n\n"
                "2. Stress level (1-10): 1 = calm, 10 = very stressed",
        "type": "text",
    },
}


def get_next_prompt(step: OnboardingStep) -> dict:
    """Get the next question prompt."""
    if step == OnboardingStep.COMPLETE:
        return None
    return ONBOARDING_PROMPTS.get(step, {})


def parse_q1_name_age_sex(text: str) -> dict:
    """Parse Q1: Name, age, sex."""
    parts = [p.strip() for p in text.split(",")]
    result = {}

    for part in parts:
        part_lower = part.lower()
        # Try to extract age
        if any(w in part_lower for w in ["year", "yr", "y"]):
            try:
                nums = [int(s) for s in part.split() if s.isdigit()]
                if nums:
                    result["age"] = nums[0]
            except:
                pass
        # Try to extract sex
        if any(w in part_lower for w in ["male", "m", "man", "boy"]):
            result["sex"] = "male"
        elif any(w in part_lower for w in ["female", "f", "woman", "girl"]):
            result["sex"] = "female"
        # Rest is name
        if "age" not in result and "sex" not in result:
            if part.strip():
                result["name"] = part.strip()

    # Try to parse just numbers as age
    try:
        for part in parts:
            num = int(part.strip())
            if 10 <= num <= 120:
                result["age"] = num
    except:
        pass

    return result


def parse_q3_height_weight_waist(text: str) -> dict:
    """Parse Q3: Height, weight, waist."""
    result = {}

    # Common patterns: "175 cm, 78 kg, 85 cm" or "175/78/85"
    text = text.lower().replace(",", " ").replace("cm", " ").replace("kg", " ")

    # Extract numbers
    import re
    numbers = [float(n) for n in re.findall(r"\d+\.?\d*", text)]

    if len(numbers) >= 1:
        # Height: typically 120-220 cm
        for n in numbers:
            if 100 <= n <= 220:
                result["height_cm"] = n
                break

    if len(numbers) >= 2:
        # Weight: typically 30-200 kg
        for n in numbers:
            if 20 <= n <= 200:
                result["weight_kg"] = n
                break

    if len(numbers) >= 3:
        # Waist: typically 40-150 cm
        for n in numbers:
            if 30 <= n <= 150:
                result["waist_cm"] = n
                break

    return result


def parse_q4_bp(text: str) -> dict:
    """Parse Q4: Blood pressure."""
    text = text.lower().replace("/", " ").replace("over", " ")

    if "don't know" in text or "dont know" in text or "dk" in text:
        return {}

    import re
    numbers = [int(n) for n in re.findall(r"\d+", text)]

    result = {}
    if len(numbers) >= 2:
        result["systolic"] = numbers[0]
        result["diastolic"] = numbers[1]
    elif len(numbers) == 1:
        # Assume systolic if only one
        result["systolic"] = numbers[0]

    return result


def parse_q5_lipids(text: str) -> dict:
    """Parse Q5: Lipid panel."""
    text = text.lower().replace(",", " ").replace("mg/dl", "").replace("dl", "")

    if "don't know" in text or "dont know" in text or "dk" in text:
        return {}

    import re
    numbers = [float(n) for n in re.findall(r"\d+\.?\d*", text)]

    result = {}
    # Try to assign: LDL, HDL, TG, Total
    # Common order: Total, LDL, HDL, TG
    if len(numbers) >= 1:
        result["total_chol"] = numbers[0]
    if len(numbers) >= 2:
        result["ldl"] = numbers[1]
    if len(numbers) >= 3:
        result["hdl"] = numbers[2]
    if len(numbers) >= 4:
        result["tg"] = numbers[3]

    return result


def parse_q6_glucose(text: str) -> dict:
    """Parse Q6: Glucose/HbA1c."""
    text = text.lower()

    if "don't know" in text or "dont know" in text or "dk" in text:
        return {}

    import re
    numbers = [float(n) for n in re.findall(r"\d+\.?\d*", text)]

    result = {}
    if len(numbers) >= 1:
        val = numbers[0]
        # HbA1c is typically 4-14%
        if 4 <= val <= 14:
            result["hba1c"] = val
        # Glucose is typically 50-400 mg/dL
        elif 30 <= val <= 500:
            result["fasting_glucose"] = val

    return result


def parse_q9_family_history(text: str) -> dict:
    """Parse Q9: Family history."""
    text = text.lower()

    if "no" in text:
        return {"family_history_early_chd": False}

    if "under 55" in text:
        return {"family_history_early_chd": True, "family_history_age": 55}
    if "under 65" in text:
        return {"family_history_early_chd": True, "family_history_age": 65}
    if "65" in text or "older" in text:
        return {"family_history_early_chd": False, "family_history_age": 65}

    return {}


def parse_q10_smoking(text: str) -> dict:
    """Parse Q10: Smoking status."""
    text = text.lower()

    if "current" in text or "smoke" in text:
        return {"smoking_status": "current"}
    if "former" in text or "quit" in text:
        return {"smoking_status": "former"}
    if "never" in text:
        return {"smoking_status": "never"}

    return {}


class ConversationManager:
    """Manages conversation state for all users."""

    def __init__(self):
        # In-memory state (in production, would use Redis)
        self.states: dict[str, UserState] = {}

    def get_or_create_state(self, phone: str) -> UserState:
        """Get or create user state."""
        if phone not in self.states:
            self.states[phone] = UserState(phone=phone)
        return self.states[phone]

    async def handle_message(self, phone: str, text: str) -> dict:
        """Handle incoming message and return response."""
        state = self.get_or_create_state(phone)

        # Run safety check first
        from app.utils.safety import get_safety_checker
        safety = get_safety_checker()
        flag = await safety.check_message(text)

        if flag:
            return {
                "type": "red_flag",
                "message": safety.format_escalation(flag),
                "escalate": True,
            }

        # Handle based on state
        if state.state == ConversationState.NEW:
            return await self.handle_new(phone, text, state)
        elif state.state == ConversationState.ONBOARDING:
            return await self.handle_onboarding(phone, text, state)
        else:
            return await self.handle_onboarding(phone, text, state)

    async def handle_new(self, phone: str, text: str, state: UserState) -> dict:
        """Handle new user."""
        text_lower = text.lower().strip()

        if text_lower in ["hi", "hello", "hey", "start"]:
            return {
                "type": "welcome",
                "message": (
                    "Hi 👋 I'm P Square — I help you understand your heart health and "
                    "biological age, personally. I'll ask 12 quick questions, then offer "
                    "a 30-second finger-on-camera scan and a face selfie. You'll get "
                    "your **Heart Score**, **Biological Age**, and a plan that's actually yours. "
                    "Reply **YES** to start."
                ),
            }
        elif text_lower == "yes":
            state.state = ConversationState.ONBOARDING
            state.onboarding_step = OnboardingStep.Q1_NAME_AGE_SEX
            return {
                "type": "question",
                "step": OnboardingStep.Q1_NAME_AGE_SEX,
                "message": get_next_prompt(OnboardingStep.Q1_NAME_AGE_SEX)["text"],
            }
        elif text_lower in ["stop", "delete", "delete my data"]:
            return {
                "type": "delete_request",
                "message": (
                    "I understand you'd like to delete your data. This request has been "
                    "noted. Your data will be permanently deleted within 30 days as per "
                    "our privacy policy."
                ),
            }
        else:
            return {
                "type": "help",
                "message": (
                    "I'm here to help you understand your heart health. Reply **YES** to "
                    "start your onboarding, or ask me anything about heart health."
                ),
            }

    async def handle_onboarding(self, phone: str, text: str, state: UserState) -> dict:
        """Handle onboarding question answer."""
        current_step = state.onboarding_step

        # Parse answer based on question
        parsed = {}
        if current_step == OnboardingStep.Q1_NAME_AGE_SEX:
            parsed = parse_q1_name_age_sex(text)
        elif current_step == OnboardingStep.Q2_CITY:
            parsed = {"city": text.strip()}
        elif current_step == OnboardingStep.Q3_HEIGHT_WEIGHT_WAIST:
            parsed = parse_q3_height_weight_waist(text)
        elif current_step == OnboardingStep.Q4_BP:
            parsed = parse_q4_bp(text)
        elif current_step == OnboardingStep.Q5_LIPIDS:
            parsed = parse_q5_lipids(text)
        elif current_step == OnboardingStep.Q6_GLUCOSE:
            parsed = parse_q6_glucose(text)
        elif current_step == OnboardingStep.Q7_CONDITIONS:
            # Parse conditions list
            conditions = []
            text_lower = text.lower()
            condition_keywords = {
                "none": [],
                "hypertension": ["hypertension", "high blood pressure"],
                "high cholesterol": ["cholesterol", "high chol"],
                "diabetes": ["diabetes", "sugar"],
                "heart attack": ["heart attack", "mi", "myocardial"],
                "stent": ["stent", "angioplasty"],
                "bypass": ["bypass", "cabg"],
                "afib": ["afib", "fibrillation", "atrial"],
                "heart failure": ["heart failure"],
                "stroke": ["stroke", "tia"],
            }
            for cond, keywords in condition_keywords.items():
                if "none" in keywords:
                    if text_lower == "none":
                        conditions = []
                        break
                elif any(k in text_lower for k in keywords):
                    conditions.append(cond)
            parsed = {"conditions": conditions}
        elif current_step == OnboardingStep.Q8_MEDICATIONS:
            text_lower = text.lower()
            if "none" in text_lower:
                parsed = {"medications": []}
            else:
                parsed = {"medications": [text.strip()]}
        elif current_step == OnboardingStep.Q9_FAMILY_HISTORY:
            parsed = parse_q9_family_history(text)
        elif current_step == OnboardingStep.Q10_SMOKING:
            parsed = parse_q10_smoking(text)
            # If current smoker, might have cigs/day
            if parsed.get("smoking_status") == "current":
                import re
                nums = [int(n) for n in re.findall(r"\d+", text)]
                if nums:
                    parsed["cigarettes_per_day"] = nums[0]
        elif current_step == OnboardingStep.Q11_ACTIVITY_DIET:
            # Parse activity level and diet
            text_lower = text.lower()
            steps = 5000  # default
            if "5000" in text_lower:
                steps = 5000
            elif "7500" in text_lower:
                steps = 7500
            elif "10000" in text_lower:
                steps = 10000

            diet = "mixed"
            if "veg" in text_lower and "non" not in text_lower:
                diet = "vegetarian"
            elif "non-veg" in text_lower or "non veg" in text_lower:
                diet = "non_vegetarian"
            elif "eggetarian" in text_lower or "egg" in text_lower:
                diet = "eggetarian"

            parsed = {"daily_steps": steps, "diet_type": diet}
        elif current_step == OnboardingStep.Q12_SLEEP_STRESS:
            import re
            text_lower = text.lower()
            # Parse sleep hours
            sleep_hours = 7.0
            if "<5" in text_lower or "under 5" in text_lower:
                sleep_hours = 4.5
            elif "5-6" in text_lower:
                sleep_hours = 5.5
            elif "6-7" in text_lower:
                sleep_hours = 6.5
            elif "7-8" in text_lower:
                sleep_hours = 7.5
            elif "8+" in text_lower:
                sleep_hours = 8.5

            # Parse stress (1-10)
            stress_score = 5
            nums = re.findall(r"\d+", text)
            for n in nums:
                if 1 <= int(n) <= 10:
                    stress_score = int(n)
                    break

            parsed = {"sleep_hours": sleep_hours, "stress_score": stress_score}

        # Update state with parsed values
        for key, value in parsed.items():
            setattr(state, key, value)

        # Move to next step (Q12 → COMPLETE)
        if current_step == OnboardingStep.Q12_SLEEP_STRESS:
            next_step = OnboardingStep.COMPLETE
        else:
            next_step = OnboardingStep(current_step + 1)
        state.onboarding_step = next_step

        # Check if onboarding complete
        if next_step == OnboardingStep.COMPLETE:
            state.state = ConversationState.COMPLETED
            # TODO: Save to database
            return {
                "type": "onboarding_complete",
                "message": (
                    "That's it — 12 questions done 🎉\n\n"
                    "Let me compute your Heart Score now. This will take a moment..."
                ),
                "trigger_heart_score": True,
            }
        else:
            return {
                "type": "question",
                "step": next_step,
                "message": get_next_prompt(next_step)["text"],
            }


# Singleton
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get conversation manager singleton."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager