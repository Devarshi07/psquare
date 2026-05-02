"""Safety module for red flag detection and escalation."""
import structlog
from typing import Optional

from app.medical_knowledge.red_flags import (
    check_red_flags,
    check_red_flags_hindi,
    check_bp_emergency,
    check_ppg_emergency,
    RedFlag,
    RedFlagSeverity,
)

log = structlog.get_logger()


class SafetyChecker:
    """Safety checker for P Square - runs on every message."""

    def __init__(self):
        self.last_flag: Optional[RedFlag] = None

    async def check_message(self, text: str) -> Optional[RedFlag]:
        """Check incoming message for red flags.

        Returns RedFlag if found, None otherwise.
        """
        if not text:
            return None

        # Check English
        flag = check_red_flags(text)
        if flag:
            self.last_flag = flag
            log.warning(
                "safety.red_flag_detected",
                severity=flag.severity.value,
                keywords=flag.keywords,
            )
            return flag

        # Check Hindi/Hinglish
        flag_hindi = check_red_flags_hindi(text)
        if flag_hindi:
            self.last_flag = flag_hindi
            log.warning(
                "safety.red_flag_detected_hindi",
                severity=flag_hindi.severity.value,
            )
            return flag_hindi

        return None

    async def check_bp(
        self,
        systolic: int,
        diastolic: int,
        has_symptoms: bool = False,
    ) -> Optional[RedFlag]:
        """Check BP reading for emergency."""
        flag = check_bp_emergency(systolic, diastolic, has_symptoms)
        if flag:
            self.last_flag = flag
            log.warning(
                "safety.bp_emergency",
                systolic=systolic,
                diastolic=diastolic,
                severity=flag.severity.value,
            )
        return flag

    async def check_ppg(
        self,
        hr_bpm: float,
        rmssd_ms: float,
        is_irregular: bool = False,
    ) -> Optional[RedFlag]:
        """Check PPG results for emergencies."""
        flag = check_ppg_emergency(hr_bpm, rmssd_ms, is_irregular)
        if flag:
            self.last_flag = flag
            log.warning(
                "safety.ppg_emergency",
                hr=hr_bpm,
                rmssd=rmssd_ms,
                is_irregular=is_irregular,
                severity=flag.severity.value,
            )
        return flag

    def format_escalation(self, flag: RedFlag) -> str:
        """Format red flag for WhatsApp message."""
        if flag.severity == RedFlagSeverity.EMERGENCY:
            return (
                f"⚠️ {flag.message}\n\n"
                f"{flag.escalation}\n\n"
                f"I'm here to help, but this needs immediate attention. "
                f"Please get help first, then we can continue."
            )
        elif flag.severity == RedFlagSeverity.URGENT:
            return (
                f"⚠️ {flag.message}\n\n"
                f"{flag.escalation}\n\n"
                f"Let me know when you've seen a doctor, and we can continue."
            )
        else:
            return (
                f"💡 {flag.message}\n\n"
                f"{flag.escalation}"
            )


# Singleton instance
_safety_checker: Optional[SafetyChecker] = None


def get_safety_checker() -> SafetyChecker:
    """Get safety checker singleton."""
    global _safety_checker
    if _safety_checker is None:
        _safety_checker = SafetyChecker()
    return _safety_checker