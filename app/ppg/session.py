"""PPG session management - JWT issuance and result storage."""
import jwt
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.config import get_settings
from app.db.models import MiniAppSession, MiniAppSessionType, PPGScan
from app.db import get_db_session

log = structlog.get_logger()
settings = get_settings()


@dataclass
class PPGLinkResult:
    """Result of generating a PPG link."""
    link: str
    session_id: int
    expires_at: datetime


async def create_ppg_session(user_id: int) -> PPGLinkResult:
    """Create a new PPG session with signed JWT."""
    session = await get_db_session()

    # Generate unique JWT ID
    jti = str(uuid.uuid4())

    # Calculate expiry (15 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    # Create JWT payload
    payload = {
        "sub": str(user_id),
        "type": "ppg",
        "jti": jti,
        "exp": expires_at.timestamp(),
    }

    # Sign JWT
    token = jwt.encode(
        payload,
        settings.miniapp_jwt_secret,
        algorithm="HS256",
    )

    # Store session in DB
    db_session = MiniAppSession(
        user_id=user_id,
        type=MiniAppSessionType.PPG,
        jwt_jti=jti,
        expires_at=expires_at,
    )
    session.add(db_session)
    await session.commit()
    await session.refresh(db_session)

    # Generate link
    link = f"{settings.miniapp_base_url}/ppg?token={token}"

    log.info("ppg.session_created", user_id=user_id, session_id=db_session.id)

    return PPGLinkResult(
        link=link,
        session_id=db_session.id,
        expires_at=expires_at,
    )


async def verify_ppg_token(token: str) -> Optional[dict]:
    """Verify PPG JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            settings.miniapp_jwt_secret,
            algorithms=["HS256"],
        )

        # Check expiration
        exp = payload.get("exp", 0)
        if datetime.utcnow().timestamp() > exp:
            log.warning("ppg.token_expired")
            return None

        return payload

    except jwt.InvalidTokenError as e:
        log.error("ppg.token_invalid", error=str(e))
        return None


async def store_ppg_result(
    user_id: int,
    hr_bpm: float,
    rmssd_ms: float,
    sdnn_ms: float = None,
    pnn50_pct: float = None,
    stress_index: int = None,
    signal_quality: float = None,
    pre_scan_context: dict = None,
    raw_signal_url: str = None,
) -> PPGScan:
    """Store PPG scan result in database."""
    session = await get_db_session()

    scan = PPGScan(
        user_id=user_id,
        hr_bpm=int(hr_bpm),
        rmssd_ms=rmssd_ms,
        sdnn_ms=sdnn_ms,
        pnn50_pct=pnn50_pct,
        stress_index=stress_index,
        signal_quality=signal_quality,
        raw_signal_url=raw_signal_url,
        pre_scan_context_json=pre_scan_context,
        source_device="miniapp",
    )

    session.add(scan)
    await session.commit()
    await session.refresh(scan)

    log.info("ppg.result_stored", user_id=user_id, hr=hr_bpm, rmssd=rmssd_ms)

    return scan


async def get_latest_ppg(user_id: int) -> Optional[PPGScan]:
    """Get most recent PPG scan."""
    from sqlalchemy import select

    session = await get_db_session()

    stmt = (
        select(PPGScan)
        .where(PPGScan.user_id == user_id)
        .order_by(PPGScan.taken_at.desc())
        .limit(1)
    )

    result = await session.scalar(stmt)
    return result


async def get_ppg_trend(user_id: int, days: int = 7) -> list[PPGScan]:
    """Get PPG scans over last N days."""
    from sqlalchemy import select
    from datetime import timedelta

    session = await get_db_session()
    cutoff = datetime.utcnow() - timedelta(days=days)

    stmt = (
        select(PPGScan)
        .where(PPGScan.user_id == user_id)
        .where(PPGScan.taken_at >= cutoff)
        .order_by(PPGScan.taken_at.asc())
    )

    result = await session.scalars(stmt)
    return list(result)