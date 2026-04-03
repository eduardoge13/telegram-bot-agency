"""Application settings via pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Twilio credentials
    twilio_auth_token: str = ""
    twilio_account_sid: str = ""

    # Google Gemini API
    gemini_api_key: str = ""

    # Google Sheets (service account JSON as string)
    google_credentials_json: str = "{}"

    # Amadeus API (flight search)
    amadeus_client_id: str = ""
    amadeus_client_secret: str = ""
    amadeus_base_url: str = "https://test.api.amadeus.com"

    # Webhook public URL (required for Twilio signature validation behind Traefik)
    webhook_base_url: str = "https://bot.srv1175749.hstgr.cloud"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance (singleton)."""
    return Settings()
