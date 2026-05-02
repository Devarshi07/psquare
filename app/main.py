"""P Square FastAPI application."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.whatsapp.router import router as whatsapp_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    # Startup
    log.info("psquare.starting", version="1.1.0")
    await init_db()
    log.info("psquare.database.initialized")
    yield
    # Shutdown
    log.info("psquare.shutting_down")


app = FastAPI(
    title="P Square API",
    description="Hyper-Personalized Cardiovascular & Longevity Agent",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.1.0"}


# WhatsApp webhook
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])


# Mini-app API routes
@app.get("/miniapp/link/{session_type}")
async def create_miniapp_link(session_type: str, user_id: int = None):
    """Generate a signed JWT link for the mini-app."""
    if session_type == "ppg":
        from app.ppg.session import create_ppg_session
        result = await create_ppg_session(user_id)
        return {"link": result.link, "expires_at": result.expires_at.isoformat()}
    elif session_type == "bioage":
        from app.bioage.session import create_bioage_session
        result = await create_bioage_session(user_id)
        return {"link": result.link, "expires_at": result.expires_at.isoformat()}
    return {"error": "Invalid session type"}


@app.post("/miniapp/ppg/result")
async def receive_ppg_result(request: dict):
    """Receive PPG scan results from mini-app."""
    from app.ppg.session import verify_ppg_token, store_ppg_result
    from app.ppg.stress_index import calculate_ppg_metrics
    from app.ppg.interpreter import interpret_ppg_for_whatsapp

    token = request.get("token")
    payload = await verify_ppg_token(token)
    if not payload:
        return {"error": "Invalid or expired token"}

    user_id = int(payload.get("sub"))

    # Validate and store
    hr = request.get("hr_bpm")
    rmssd = request.get("rmssd_ms")

    if hr and rmssd:
        # Calculate stress index
        metrics = await calculate_ppg_metrics(
            hr_bpm=hr,
            rmssd_ms=rmssd,
            age=40,  # Would get from user profile
            sex="male",
        )
        metrics["stress_index"] = metrics.get("stress_index", 50)

        # Store
        await store_ppg_result(
            user_id=user_id,
            hr_bpm=hr,
            rmssd_ms=rmssd,
            sdnn_ms=request.get("sdnn_ms"),
            pnn50_pct=request.get("pnn50_pct"),
            stress_index=metrics["stress_index"],
            signal_quality=request.get("signal_quality"),
        )

        # Generate interpretation
        interpretation = await interpret_ppg_for_whatsapp(hr, rmssd, metrics["stress_index"], 40)
        return {"success": True, "interpretation": interpretation}

    return {"error": "Invalid PPG data"}


@app.post("/miniapp/bioage/upload")
async def receive_bioage_photo(request: dict):
    """Receive face photo from mini-app."""
    # This would handle the multipart upload
    return {"success": True, "message": "Photo received"}


@app.get("/api/heart/score/{user_id}")
async def get_heart_score(user_id: int):
    """Get the latest heart score for a user."""
    # TODO: Implement - pull from DB
    return {"error": "Not implemented yet"}


# Heart score endpoint (placeholder for now)
@app.get("/api/heart/score/{user_id}")
async def get_heart_score(user_id: int):
    """Get the latest heart score for a user."""
    # TODO: Implement in Phase 2
    return {"error": "Not implemented yet"}


# Bio age endpoint (placeholder for now)
@app.get("/api/bioage/{user_id}")
async def get_bio_age(user_id: int):
    """Get the latest biological age for a user."""
    # TODO: Implement in Phase 5
    return {"error": "Not implemented yet"}


# PPG endpoint (placeholder for now)
@app.get("/api/ppg/{user_id}")
async def get_ppg_scans(user_id: int):
    """Get PPG scans for a user."""
    # TODO: Implement in Phase 4
    return {"error": "Not implemented yet"}


# Reports endpoint (placeholder for now)
@app.get("/api/reports/{user_id}")
async def get_reports(user_id: int):
    """Get generated reports for a user."""
    # TODO: Implement in Phase 6
    return {"error": "Not implemented yet"}


@app.get("/")
async def root():
    return {
        "name": "P Square API",
        "version": "1.1.0",
        "docs": "/docs",
    }