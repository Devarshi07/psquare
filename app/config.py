"""P Square configuration management."""
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # WhatsApp
    whatsapp_provider: str = Field(default="meta", alias="WHATSAPP_PROVIDER")
    whatsapp_api_key: str = Field(default="", alias="WHATSAPP_API_KEY")
    whatsapp_phone_number_id: str = Field(default="", alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_verify_token: str = Field(default="", alias="WHATSAPP_VERIFY_TOKEN")

    # Twilio (alternative)
    twilio_account_sid: Optional[str] = Field(default=None, alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(default=None, alias="TWILIO_PHONE_NUMBER")

    # Database
    database_url: str = Field(default="", alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="", alias="REDIS_URL")

    # Supabase (DB + Storage)
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_KEY")

    # S3 (optional, for when you scale up)
    s3_bucket: str = Field(default="", alias="S3_BUCKET")
    s3_access_key: str = Field(default="", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="", alias="S3_SECRET_KEY")
    s3_endpoint_url: Optional[str] = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_region: str = Field(default="ap-south-1", alias="S3_REGION")

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")

    # App
    app_base_url: str = Field(default="http://localhost:8000", alias="APP_BASE_URL")
    miniapp_base_url: str = Field(default="http://localhost:5173", alias="MINIAPP_BASE_URL")
    miniapp_jwt_secret: str = Field(default="", alias="MINIAPP_JWT_SECRET")

    # Admin
    admin_phone_numbers: list[str] = Field(default_factory=list, alias="ADMIN_PHONE_NUMBERS")

    @field_validator("admin_phone_numbers", mode="before")
    @classmethod
    def parse_phone_list(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_base_url.startswith("https")


@lru_cache
def get_settings() -> Settings:
    return Settings()