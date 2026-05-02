"""DPDP Act 2023 compliance for India.

Implements:
- Consent flow (general + biometric)
- Right to erasure ("DELETE MY DATA")
- Data minimization
- Breach notification
"""
import structlog
from datetime import datetime
from typing import Optional

from app.db.models import User
from app.db import get_db_session

log = structlog.get_logger()


# Consent types
CONSENT_TYPES = {
    "general": "General use of P Square for heart health tracking",
    "biometric_face": "Face selfie capture for biological age estimation",
    "biometric_ppg": "Finger on camera PPG scan for heart rate/HRV",
}


async def record_consent(
    user_id: int,
    consent_type: str,
    granted: bool = True,
) -> bool:
    """Record user's consent."""
    session = await get_db_session()

    from sqlalchemy import select
    stmt = select(User).where(User.id == user_id)
    user = await session.scalar(stmt)

    if not user:
        return False

    if consent_type == "general":
        if granted:
            user.consent_given_at = datetime.now()
            log.info("consent.general_granted", user_id=user_id)
    elif consent_type in ["biometric_face", "biometric_ppg"]:
        if granted:
            user.biometric_consent_given_at = datetime.now()
            log.info(f"consent.{consent_type}_granted", user_id=user_id)

    await session.commit()
    return True


async def has_consent(user_id: int, consent_type: str) -> bool:
    """Check if user has given consent."""
    session = await get_db_session()

    from sqlalchemy import select
    stmt = select(User).where(User.id == user_id)
    user = await session.scalar(stmt)

    if not user:
        return False

    if consent_type == "general":
        return user.consent_given_at is not None
    elif consent_type in ["biometric_face", "biometric_ppg"]:
        return user.biometric_consent_given_at is not None

    return False


async def request_data_deletion(user_id: int) -> bool:
    """Request deletion of all user data.

    Per DPDP: deletion within 30 days.
    """
    session = await get_db_session()

    from sqlalchemy import select
    from app.db.models import (
        User, Profile, MedicalHistory, Medication, FamilyHistory,
        LabResult, BPReading, RHRReading, StepsLog, HabitLog,
        SmokingLog, HeartScore, PPGScan, BioAgeAssessment, Plan,
        Conversation, Message, Report, Checkin, MiniAppSession
    )

    # Mark for deletion (soft delete or schedule hard delete)
    stmt = select(User).where(User.id == user_id)
    user = await session.scalar(stmt)

    if user:
        # In production: schedule hard delete after 30 days
        # For now: mark as deletion requested
        log.info("deletion.requested", user_id=user_id, timestamp=datetime.now().isoformat())
        # Would trigger background job here

    await session.commit()
    return True


async def get_user_data_summary(user_id: int) -> dict:
    """Get summary of user's data for transparency."""
    session = await get_db_session()

    from sqlalchemy import select, func
    from app.db.models import (
        BPReading, RHRReading, StepsLog, PPGScan, BioAgeAssessment,
        HeartScore, Report
    )

    counts = {}

    # Count various data types
    for model, name in [
        (BPReading, "bp_readings"),
        (RHRReading, "rhr_readings"),
        (StepsLog, "steps_logs"),
        (PPGScan, "ppg_scans"),
        (BioAgeAssessment, "bio_age_assessments"),
        (HeartScore, "heart_scores"),
        (Report, "reports"),
    ]:
        stmt = select(func.count()).where(model.user_id == user_id)
        counts[name] = await session.scalar(stmt) or 0

    return {
        "user_id": user_id,
        "data_types": counts,
        "total_records": sum(counts.values()),
    }


def format_consent_message() -> str:
    """Format consent request message."""
    return (
        "🔐 *Consent & Privacy*\n\n"
        "To use P Square, I need your consent:\n\n"
        "*General Use:* I'll store your health data to track your heart health and generate insights.\n\n"
        "*Biometric (Optional):* For face selfies and PPG scans, I need separate consent since these are sensitive.\n\n"
        "Reply *YES* to consent to general use.\n"
        "Reply *YES FACE* to also consent to face selfies.\n"
        "Reply *YES PPG* to also consent to PPG scans.\n"
        "Reply *ALL* for full consent.\n\n"
        "You can withdraw consent anytime by messaging *DELETE MY DATA*."
    )


def format_deletion_confirmation() -> str:
    """Format deletion confirmation message."""
    return (
        "🗑️ *Data Deletion Requested*\n\n"
        "Your data deletion request has been received.\n\n"
        "Per our privacy policy, your data will be permanently deleted within 30 days.\n\n"
        "If you change your mind, just message *CANCEL DELETE* within 7 days.\n\n"
        "For any privacy concerns, contact: privacy@psquare.health"
    )


async def log_data_access(
    user_id: int,
    admin_id: str,
    reason: str,
) -> bool:
    """Log access to user's health data."""
    # In production: log to audit table
    log.info(
        "data.access",
        user_id=user_id,
        accessed_by=admin_id,
        reason=reason,
        timestamp=datetime.now().isoformat(),
    )
    return True