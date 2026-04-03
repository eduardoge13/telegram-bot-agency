"""Shared test fixtures for whatsapp-bot tests."""
import pytest
from unittest.mock import MagicMock
from app.businesses import BusinessConfig


@pytest.fixture
def puntoclave_config():
    """Sample BusinessConfig for Punto Clave MX."""
    return BusinessConfig(
        business_id="puntoclave",
        phone_number_id="123456789012345",
        system_prompt="Eres el asistente virtual de Punto Clave MX.",
        sheets_id="test-sheet-id",
        handlers=["product", "order", "qa"],
        display_phone_number="15550000001",
        language="es",
    )


@pytest.fixture
def travel_config():
    """Sample BusinessConfig for travel agency."""
    return BusinessConfig(
        business_id="travel",
        phone_number_id="987654321098765",
        system_prompt="Eres el asistente de viajes.",
        sheets_id=None,
        handlers=["flight", "qa"],
        display_phone_number="15550000002",
        language="es",
    )


@pytest.fixture
def mock_settings():
    """Mock settings to avoid real env var requirements."""
    settings = MagicMock()
    settings.whatsapp_access_token = "test_access_token"
    settings.whatsapp_verify_token = "test_verify_token"
    settings.whatsapp_app_secret = ""
    settings.whatsapp_api_version = "v24.0"
    settings.gemini_api_key = "test_gemini_key"
    settings.google_credentials_json = "{}"
    settings.amadeus_client_id = "test_amadeus_id"
    settings.amadeus_client_secret = "test_amadeus_secret"
    settings.amadeus_base_url = "https://test.api.amadeus.com"
    return settings


@pytest.fixture
def mock_gemini_client():
    """Mock GeminiClient to avoid real Gemini API calls."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_client.create_chat.return_value = mock_chat
    return mock_client
