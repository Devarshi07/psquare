"""Meta WhatsApp Business Cloud API adapter."""
import json
from typing import Optional

import httpx

from app.config import get_settings
from app.whatsapp.adapter_base import WhatsAppAdapter, WhatsAppMessage

settings = get_settings()


class MetaWhatsAppAdapter(WhatsAppAdapter):
    """WhatsApp adapter using Meta's Cloud API."""

    def __init__(self):
        self.api_key = settings.whatsapp_api_key
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"

    async def _post(self, endpoint: str, data: dict) -> dict:
        """Make a POST request to the Meta API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/{endpoint}",
                params={"access_token": self.api_key},
                json=data,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def send_message(
        self,
        to: str,
        text: str,
        buttons: Optional[list] = None,
        list_items: Optional[list] = None,
    ) -> dict:
        """Send a text message with optional interactive elements."""
        messaging = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        if buttons:
            messaging["type"] = "interactive"
            messaging["interactive"] = {
                "type": "button",
                "body": {"text": text},
                "action": {
                    "buttons": [
                        {"id": btn["id"], "title": btn["title"]}
                        for btn in buttons
                    ]
                },
            }
        elif list_items:
            messaging["type"] = "interactive"
            messaging["interactive"] = {
                "type": "list",
                "body": {"text": text},
                "action": {
                    "button": "Select an option",
                    "sections": [
                        {"title": "Options", "rows": list_items}
                    ],
                },
            }

        return await self._post("messages", messaging)

    async def send_document(self, to: str, url: str, caption: str) -> dict:
        """Send a document (PDF)."""
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"link": url, "caption": caption},
        }
        return await self._post("messages", data)

    async def send_image(self, to: str, url: str, caption: Optional[str] = None) -> dict:
        """Send an image."""
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": url, "caption": caption} if caption else {"link": url},
        }
        return await self._post("messages", data)

    async def send_voice(self, to: str, audio_url: str) -> dict:
        """Send a voice message."""
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "audio",
            "audio": {"link": audio_url},
        }
        return await self._post("messages", data)

    async def mark_as_read(self, message_id: str) -> dict:
        """Mark a message as read."""
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        return await self._post("messages", data)

    def parse_webhook(self, payload: dict) -> WhatsAppMessage:
        """Parse incoming webhook payload."""
        entry = payload.get("entry", [])
        if not entry:
            raise ValueError("Invalid webhook payload")

        changes = entry[0].get("changes", [])
        if not changes:
            raise ValueError("No changes in webhook")

        messaging = changes[0].get("value", {}).get("messages", [])
        if not messaging:
            raise ValueError("No messages in webhook")

        msg = messaging[0]
        msg_type = msg.get("type", "text")

        content = ""
        media_url = None

        if msg_type == "text":
            content = msg.get("text", {}).get("body", "")
        elif msg_type == "image":
            content = msg.get("image", {}).get("caption", "")
            media_url = msg.get("image", {}).get("link")
        elif msg_type == "audio":
            media_url = msg.get("audio", {}).get("link")
        elif msg_type == "document":
            content = msg.get("document", {}).get("caption", "")
            media_url = msg.get("document", {}).get("link")
        elif msg_type == "voice":
            media_url = msg.get("voice", {}).get("link")

        from_number = msg.get("from", "")

        return WhatsAppMessage(
            from_number=from_number,
            message_type=msg_type,
            content=content,
            media_url=media_url,
        )


def get_adapter() -> MetaWhatsAppAdapter:
    """Get the configured WhatsApp adapter."""
    return MetaWhatsAppAdapter()