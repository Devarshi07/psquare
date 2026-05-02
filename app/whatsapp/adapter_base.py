"""WhatsApp adapter base class."""
from abc import ABC, abstractmethod
from typing import Optional


class WhatsAppMessage:
    """Represents an incoming WhatsApp message."""

    def __init__(
        self,
        from_number: str,
        message_type: str,
        content: str,
        media_url: Optional[str] = None,
    ):
        self.from_number = from_number
        self.message_type = message_type
        self.content = content
        self.media_url = media_url


class WhatsAppAdapter(ABC):
    """Abstract base class for WhatsApp providers."""

    @abstractmethod
    async def send_message(
        self,
        to: str,
        text: str,
        buttons: Optional[list] = None,
        list_items: Optional[list] = None,
    ) -> dict:
        """Send a text message with optional interactive elements."""
        pass

    @abstractmethod
    async def send_document(self, to: str, url: str, caption: str) -> dict:
        """Send a document (PDF)."""
        pass

    @abstractmethod
    async def send_image(self, to: str, url: str, caption: Optional[str] = None) -> dict:
        """Send an image."""
        pass

    @abstractmethod
    async def send_voice(self, to: str, audio_url: str) -> dict:
        """Send a voice message."""
        pass

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> dict:
        """Mark a message as read."""
        pass

    def parse_webhook(self, payload: dict) -> WhatsAppMessage:
        """Parse incoming webhook payload into a WhatsAppMessage."""
        raise NotImplementedError

    def verify_webhook(self, mode: str, token: str, verify_token: str) -> bool:
        """Verify webhook subscription."""
        if mode == "subscribe" and token == verify_token:
            return True
        return False