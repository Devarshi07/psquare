"""BioAge session management - similar to PPG."""
import jwt
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.config import get_settings
from app.db.models import MiniAppSession, MiniAppSessionType, BioAgeAssessment
from app.db import get_db_session

log = structlog.get_logger()
settings = get_settings()


@dataclass
class BioAgeLinkResult:
    """Result of generating a BioAge link."""
    link: str
    session_id: int
    expires_at: datetime


async def create_bioage_session(user_id: int) -> BioAgeLinkResult:
    """Create a new BioAge session with signed JWT."""
    session = await get_db_session()

    jti = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    payload = {
        "sub": str(user_id),
        "type": "bioage",
        "jti": jti,
        "exp": expires_at.timestamp(),
    }

    token = jwt.encode(
        payload,
        settings.miniapp_jwt_secret,
        algorithm="HS256",
    )

    db_session = MiniAppSession(
        user_id=user_id,
        type=MiniAppSessionType.BIOAGE,
        jwt_jti=jti,
        expires_at=expires_at,
    )
    session.add(db_session)
    await session.commit()
    await session.refresh(db_session)

    link = f"{settings.miniapp_base_url}/face?token={token}"

    log.info("bioage.session_created", user_id=user_id, session_id=db_session.id)

    return BioAgeLinkResult(
        link=link,
        session_id=db_session.id,
        expires_at=expires_at,
    )


async def verify_bioage_token(token: str) -> Optional[dict]:
    """Verify BioAge JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.miniapp_jwt_secret,
            algorithms=["HS256"],
        )

        exp = payload.get("exp", 0)
        if datetime.utcnow().timestamp() > exp:
            log.warning("bioage.token_expired")
            return None

        return payload

    except jwt.InvalidTokenError as e:
        log.error("bioage.token_invalid", error=str(e))
        return None


async def store_bioage_result(
    user_id: int,
    chronological_age: int,
    biological_age: float,
    face_image_url: str = None,
    face_age_estimate: float = None,
    face_drivers: list[dict] = None,
    questionnaire_json: dict = None,
    computed_breakdown_json: dict = None,
) -> BioAgeAssessment:
    """Store BioAge assessment in database."""
    session = await get_db_session()

    assessment = BioAgeAssessment(
        user_id=user_id,
        chronological_age=chronological_age,
        biological_age=biological_age,
        face_image_url=face_image_url,
        face_age_estimate=face_age_estimate,
        face_drivers_json=face_drivers or [],
        questionnaire_json=questionnaire_json or {},
        computed_breakdown_json=computed_breakdown_json or {},
    )

    session.add(assessment)
    await session.commit()
    await session.refresh(assessment)

    log.info("bioage.result_stored", user_id=user_id, bio_age=biological_age)

    return assessment


async def get_latest_bioage(user_id: int) -> Optional[BioAgeAssessment]:
    """Get most recent BioAge assessment."""
    from sqlalchemy import select

    session = await get_db_session()

    stmt = (
        select(BioAgeAssessment)
        .where(BioAgeAssessment.user_id == user_id)
        .order_by(BioAgeAssessment.taken_at.desc())
        .limit(1)
    )

    result = await session.scalar(stmt)
    return result