"""Tests for /health endpoint."""
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def _clear_app_modules():
    """Remove app.* modules from sys.modules for a clean import."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("app."):
            del sys.modules[mod]


@pytest.fixture
def client():
    """FastAPI test client with mocked settings and lifespan triggered."""
    _clear_app_modules()
    mock_settings = MagicMock()
    mock_settings.twilio_auth_token = "test_auth_token"
    mock_settings.twilio_account_sid = "test_account_sid"
    mock_settings.gemini_api_key = "test_gemini_key"
    mock_settings.webhook_base_url = "https://bot.srv1175749.hstgr.cloud"

    with patch("app.config.get_settings", return_value=mock_settings):
        with patch("app.gemini_client.GeminiClient") as MockGeminiClient:
            MockGeminiClient.return_value.create_chat.return_value = MagicMock()
            from app.main import app
            with TestClient(app) as c:
                yield c


def test_health(client):
    """GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_service_name(client):
    """GET /health includes service name."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("service") == "whatsapp-bot"
