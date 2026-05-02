"""WhatsApp webhook router."""
from typing import Optional

import structlog
from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response

from app.config import get_settings
from app.whatsapp import get_whatsapp_adapter
from app.conversation.state_machine import get_conversation_manager
from app.heart.score import calculate_heart_score, HeartScoreInput
from app.heart.scoreboard import build_scoreboard, format_scoreboard_for_whatsapp

log = structlog.get_logger()
settings = get_settings()

router = APIRouter()
adapter = get_whatsapp_adapter()
conversation_mgr = get_conversation_manager()


@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(...),
    token: str = Query(...),
    challenge: str = Query(...),
):
    """Verify webhook subscription with Meta."""
    if adapter.verify_webhook(mode, token, settings.whatsapp_verify_token):
        log.info("whatsapp.webhook.verified")
        return Response(content=challenge, media_type="text/plain")
    log.warning("whatsapp.webhook.verification_failed", mode=mode)
    return JSONResponse(status_code=403, content={"error": "Verification failed"})


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    x_hub_signature: Optional[str] = Header(None),
):
    """Handle incoming WhatsApp messages (Meta JSON or Twilio form-encoded)."""
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        payload = dict(await request.form())
    else:
        payload = await request.json()

    try:
        message = adapter.parse_webhook(payload)
    except ValueError as e:
        log.warning("whatsapp.webhook.parse_error", error=str(e))
        return JSONResponse(status_code=200, content={"ok": True})

    log.info(
        "whatsapp.message.received",
        from_number=message.from_number,
        type=message.message_type,
    )

    # Process through conversation manager
    response_data = await conversation_mgr.handle_message(
        message.from_number,
        message.content or ""
    )

    # Handle different response types
    if response_data.get("type") == "red_flag":
        # Safety flag triggered
        await adapter.send_message(
            to=message.from_number,
            text=response_data["message"],
        )
    elif response_data.get("trigger_heart_score"):
        # Onboarding complete - compute and send score
        await adapter.send_message(
            to=message.from_number,
            text=response_data["message"],
        )
        # Compute heart score
        state = conversation_mgr.get_or_create_state(message.from_number)
        score_inputs = build_score_inputs(state)
        score_result = calculate_heart_score(score_inputs)

        # Send score
        await adapter.send_message(
            to=message.from_number,
            text=f"🎯 *Your P² Heart Score: {score_result.score}/100* ({score_result.score_band})",
        )

        # Send confidence
        await adapter.send_message(
            to=message.from_number,
            text=f"Confidence: {score_result.confidence} ({score_result.confidence_percent:.0f}% data available)",
        )

        # Send scoreboard
        board = build_scoreboard(score_inputs)
        board_text = format_scoreboard_for_whatsapp(board)
        await adapter.send_message(
            to=message.from_number,
            text=board_text,
        )

        # Offer PPG/BioAge
        await adapter.send_message(
            to=message.from_number,
            text=(
                "That's your Heart Score! 🎉\n\n"
                "Want to add more data?\n"
                "• Add a PPG scan (finger on camera) for HR, HRV & stress\n"
                "• Add Biological Age check (5 questions + selfie)\n\n"
                "Or reply *Report* to get your full PDF report."
            ),
        )
    elif response_data.get("type") == "question":
        # Send question
        await adapter.send_message(
            to=message.from_number,
            text=response_data["message"],
        )
    elif response_data.get("type") == "welcome":
        await adapter.send_message(
            to=message.from_number,
            text=response_data["message"],
        )
    else:
        # Default/other
        await adapter.send_message(
            to=message.from_number,
            text=response_data.get("message", "I'm here to help!"),
        )

    return JSONResponse(status_code=200, content={"ok": True})


def build_score_inputs(state) -> HeartScoreInput:
    """Build HeartScoreInput from user state."""
    return HeartScoreInput(
        age=state.age or 40,
        sex=state.sex or "male",
        ethnicity="south_asian",
        systolic_bp=state.systolic,
        diastolic_bp=state.diastolic,
        ldl=state.ldl,
        hdl=state.hdl,
        tg=state.tg,
        total_chol=state.total_chol,
        hba1c=state.hba1c,
        bmi=calculate_bmi(state.weight_kg, state.height_cm),
        waist_cm=state.waist_cm,
        daily_steps=state.daily_steps,
        sleep_hours=state.sleep_hours,
        stress_score=state.stress_score,
        smoking_status=state.smoking_status,
        has_hypertension=("hypertension" in state.conditions) if state.conditions else False,
        has_high_cholesterol=("high cholesterol" in state.conditions) if state.conditions else False,
        has_diabetes=("diabetes" in state.conditions) if state.conditions else False,
        has_prior_mi=("heart attack" in state.conditions) if state.conditions else False,
        has_prior_stroke=("stroke" in state.conditions) if state.conditions else False,
        has_stent=("stent" in state.conditions) if state.conditions else False,
        has_bypass=("bypass" in state.conditions) if state.conditions else False,
        has_afib=("afib" in state.conditions) if state.conditions else False,
        has_heart_failure=("heart failure" in state.conditions) if state.conditions else False,
        family_history_early_chd=state.family_history_early_chd or False,
    )


def calculate_bmi(weight_kg: float, height_cm: float) -> Optional[float]:
    """Calculate BMI from weight and height."""
    if weight_kg and height_cm:
        height_m = height_cm / 100
        return weight_kg / (height_m * height_m)
    return None