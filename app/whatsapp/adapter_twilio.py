"""Twilio WhatsApp adapter."""
from typing import Optional

import httpx

from app.config import get_settings
from app.whatsapp.adapter_base import WhatsAppAdapter, WhatsAppMessage

settings = get_settings()

_TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts"


class TwilioWhatsAppAdapter(WhatsAppAdapter):
    """WhatsApp adapter using Twilio's REST API."""

    def __init__(self):
        self.account_sid = settings.twilio_account_sid or ""
        self.auth_token = settings.twilio_auth_token or ""
        self.from_number = settings.twilio_phone_number or ""
        # Ensure whatsapp: prefix
        if self.from_number and not self.from_number.startswith("whatsapp:"):
            self.from_number = f"whatsapp:{self.from_number}"

    def _to_wa(self, number: str) -> str:
        """Ensure whatsapp: prefix on destination number."""
        if not number.startswith("whatsapp:"):
            return f"whatsapp:{number}"
        return number

    async def _post_message(self, to: str, body: str, media_url: Optional[str] = None) -> dict:
        url = f"{_TWILIO_API}/{self.account_sid}/Messages.json"
        data = {"From": self.from_number, "To": self._to_wa(to), "Body": body}
        if media_url:
            data["MediaUrl"] = media_url
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def send_message(
        self,
        to: str,
        text: str,
        buttons: Optional[list] = None,
        list_items: Optional[list] = None,
    ) -> dict:
        """Send a text message. Buttons/list items rendered as numbered text options."""
        body = text
        if buttons:
            options = "\n".join(
                f"{i + 1}. {btn.get('title', btn.get('id', ''))}"
                for i, btn in enumerate(buttons)
            )
            body = f"{text}\n\n{options}"
        elif list_items:
            options = "\n".join(
                f"{i + 1}. {item.get('title', '')}"
                for i, item in enumerate(list_items)
            )
            body = f"{text}\n\n{options}"
        return await self._post_message(to, body)

    async def send_document(self, to: str, url: str, caption: str) -> dict:
        return await self._post_message(to, caption, media_url=url)

    async def send_image(self, to: str, url: str, caption: Optional[str] = None) -> dict:
        return await self._post_message(to, caption or "", media_url=url)

    async def send_voice(self, to: str, audio_url: str) -> dict:
        return await self._post_message(to, "", media_url=audio_url)

    async def mark_as_read(self, message_id: str) -> dict:
        # Twilio does not have a separate mark-as-read API for WhatsApp
        return {}

    def parse_webhook(self, payload: dict) -> WhatsAppMessage:
        """Parse Twilio form-encoded webhook into a WhatsAppMessage."""
        from_wa = payload.get("From", "")
        # Strip whatsapp: prefix from stored number
        from_number = from_wa.replace("whatsapp:", "")

        body = payload.get("Body", "")
        num_media = int(payload.get("NumMedia", "0"))

        media_url = payload.get("MediaUrl0") if num_media > 0 else None
        media_type = payload.get("MediaContentType0", "")

        if num_media > 0 and media_type.startswith("image"):
            msg_type = "image"
        elif num_media > 0 and media_type.startswith("audio"):
            msg_type = "audio"
        elif num_media > 0 and "pdf" in media_type:
            msg_type = "document"
        else:
            msg_type = "text"

        return WhatsAppMessage(
            from_number=from_number,
            message_type=msg_type,
            content=body,
            media_url=media_url,
        )


def get_adapter() -> TwilioWhatsAppAdapter:
    return TwilioWhatsAppAdapter()
