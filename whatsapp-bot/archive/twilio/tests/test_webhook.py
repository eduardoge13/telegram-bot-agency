"""Tests for /webhook endpoint: Twilio signature validation, routing, TwiML responses."""
import pytest
import sys
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


# Shared test constants
VALID_TWILIO_NUMBER = "whatsapp:+15005550006"
CUSTOMER_NUMBER = "whatsapp:+521234567890"
WEBHOOK_BASE_URL = "https://bot.srv1175749.hstgr.cloud"


def _clear_app_modules():
    """Remove app.* modules from sys.modules for a clean import."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("app."):
            del sys.modules[mod]


def _make_mock_settings():
    settings = MagicMock()
    settings.twilio_auth_token = "test_auth_token"
    settings.twilio_account_sid = "test_account_sid"
    settings.gemini_api_key = "test_gemini_key"
    settings.webhook_base_url = WEBHOOK_BASE_URL
    return settings


def _make_mock_chat():
    mock_chat = MagicMock()
    mock_chat.send_message_async = AsyncMock(
        return_value=MagicMock(text="Hola, ¿en qué te puedo ayudar?")
    )
    return mock_chat


def _webhook_form_data(to=VALID_TWILIO_NUMBER, from_=CUSTOMER_NUMBER, body="Hola"):
    """Build form data for a webhook POST."""
    return {
        "To": to,
        "From": from_,
        "Body": body,
        "MessageSid": "SM123456789",
    }


@pytest.fixture
def valid_client():
    """TestClient with valid Twilio signature (bypassed validator)."""
    _clear_app_modules()
    mock_settings = _make_mock_settings()
    mock_chat = _make_mock_chat()

    with patch("app.config.get_settings", return_value=mock_settings):
        with patch("app.gemini_client.GeminiClient") as MockGeminiClient:
            MockGeminiClient.return_value.create_chat.return_value = mock_chat
            with patch(
                "twilio.request_validator.RequestValidator.validate",
                return_value=True,
            ):
                from app.main import app
                with TestClient(app) as client:
                    yield client


@pytest.fixture
def invalid_client():
    """TestClient where Twilio signature validation always fails."""
    _clear_app_modules()
    mock_settings = _make_mock_settings()

    with patch("app.config.get_settings", return_value=mock_settings):
        with patch("app.gemini_client.GeminiClient") as MockGeminiClient:
            MockGeminiClient.return_value.create_chat.return_value = MagicMock()
            with patch(
                "twilio.request_validator.RequestValidator.validate",
                return_value=False,
            ):
                from app.main import app
                with TestClient(app) as client:
                    yield client


def test_signature_valid(valid_client):
    """POST /webhook with valid Twilio signature returns 200 with TwiML XML."""
    response = valid_client.post(
        "/webhook",
        data=_webhook_form_data(),
        headers={
            "X-Twilio-Signature": "valid_signature",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text


def test_signature_invalid(invalid_client):
    """POST /webhook with invalid Twilio signature returns 403."""
    response = invalid_client.post(
        "/webhook",
        data=_webhook_form_data(),
        headers={
            "X-Twilio-Signature": "invalid_signature",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert response.status_code == 403


def test_url_reconstruction():
    """validate_twilio reconstructs HTTPS URL using WEBHOOK_BASE_URL env setting."""
    _clear_app_modules()
    mock_settings = _make_mock_settings()
    captured_url = {}

    def capture_validate(url, form, sig):
        captured_url["url"] = url
        return True

    with patch("app.config.get_settings", return_value=mock_settings):
        with patch("app.gemini_client.GeminiClient") as MockGeminiClient:
            MockGeminiClient.return_value.create_chat.return_value = _make_mock_chat()
            with patch(
                "twilio.request_validator.RequestValidator.validate",
                side_effect=capture_validate,
            ):
                from app.main import app
                with TestClient(app) as client:
                    client.post(
                        "/webhook",
                        data=_webhook_form_data(),
                        headers={
                            "X-Twilio-Signature": "test_sig",
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                    )

    assert WEBHOOK_BASE_URL in captured_url.get("url", ""), (
        f"Expected WEBHOOK_BASE_URL in reconstructed URL, got: {captured_url.get('url')}"
    )


def test_unknown_business(valid_client):
    """POST /webhook with valid signature but unknown To number returns graceful TwiML."""
    response = valid_client.post(
        "/webhook",
        data=_webhook_form_data(to="whatsapp:+19999999999"),
        headers={
            "X-Twilio-Signature": "valid_signature",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text
    # Should return a graceful error message in Spanish
    assert "Lo siento" in response.text or "disponible" in response.text.lower()


def test_webhook_returns_twiml_message(valid_client):
    """POST /webhook returns TwiML with <Message> element."""
    response = valid_client.post(
        "/webhook",
        data=_webhook_form_data(),
        headers={
            "X-Twilio-Signature": "valid_signature",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert response.status_code == 200
    assert "<Message>" in response.text
