"""WhatsApp adapter factory."""
from app.config import get_settings
from app.whatsapp.adapter_base import WhatsAppAdapter


def get_whatsapp_adapter() -> WhatsAppAdapter:
    """Return the configured WhatsApp adapter based on WHATSAPP_PROVIDER."""
    provider = get_settings().whatsapp_provider.lower()
    if provider == "twilio":
        from app.whatsapp.adapter_twilio import TwilioWhatsAppAdapter
        return TwilioWhatsAppAdapter()
    # Default: Meta Cloud API
    from app.whatsapp.adapter_meta import MetaWhatsAppAdapter
    return MetaWhatsAppAdapter()
