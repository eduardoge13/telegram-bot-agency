"""Tests for /webhook endpoint using Meta WhatsApp Cloud API payloads."""
import hashlib
import hmac
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


VALID_PHONE_NUMBER_ID = "123456789012345"
CUSTOMER_NUMBER = "521234567890"


def _clear_app_modules():
    """Remove app.* modules from sys.modules for a clean import."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("app."):
            del sys.modules[mod]


def _make_mock_settings():
    settings = MagicMock()
    settings.whatsapp_access_token = "test_access_token"
    settings.whatsapp_verify_token = "verify-me"
    settings.whatsapp_app_secret = ""
    settings.whatsapp_api_version = "v24.0"
    settings.gemini_api_key = "test_gemini_key"
    settings.google_credentials_json = "{}"
    settings.amadeus_client_id = "test_amadeus_id"
    settings.amadeus_client_secret = "test_amadeus_secret"
    settings.amadeus_base_url = "https://test.api.amadeus.com"
    return settings


def _meta_text_payload(phone_number_id=VALID_PHONE_NUMBER_ID, body="Hola"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550000001",
                                "phone_number_id": phone_number_id,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Cliente Demo"},
                                    "wa_id": CUSTOMER_NUMBER,
                                }
                            ],
                            "messages": [
                                {
                                    "from": CUSTOMER_NUMBER,
                                    "id": "wamid.ABC123",
                                    "timestamp": "1710000000",
                                    "text": {"body": body},
                                    "type": "text",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def _meta_status_payload():
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550000001",
                                "phone_number_id": VALID_PHONE_NUMBER_ID,
                            },
                            "statuses": [
                                {
                                    "id": "wamid.ABC123",
                                    "status": "delivered",
                                    "timestamp": "1710000001",
                                    "recipient_id": CUSTOMER_NUMBER,
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


@pytest.fixture
def client():
    """FastAPI test client with mocked settings and lifespan triggered."""
    _clear_app_modules()
    mock_settings = _make_mock_settings()

    with patch("app.config.get_settings", return_value=mock_settings):
        with patch("app.gemini_client.GeminiClient") as MockGeminiClient:
            MockGeminiClient.return_value.create_chat.return_value = MagicMock()
            from app.main import app
            with TestClient(app) as test_client:
                test_client.app.state.whatsapp_client.send_text_message = AsyncMock(
                    return_value={"messages": [{"id": "wamid.REPLY"}]}
                )
                yield test_client


def test_webhook_verification_success(client):
    """GET /webhook returns the hub challenge when verify token matches."""
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "123456",
        },
    )
    assert response.status_code == 200
    assert response.text == "123456"


def test_webhook_verification_invalid_token(client):
    """GET /webhook rejects invalid verification tokens."""
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "123456",
        },
    )
    assert response.status_code == 403


def test_webhook_processes_incoming_text_message(client):
    """POST /webhook dispatches an inbound text message and sends a reply through Meta."""
    with patch(
        "app.main.dispatch",
        new=AsyncMock(return_value="Hola, ¿en qué te puedo ayudar?"),
    ) as mock_dispatch:
        response = client.post("/webhook", json=_meta_text_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_dispatch.assert_awaited_once()
    client.app.state.whatsapp_client.send_text_message.assert_awaited_once_with(
        phone_number_id=VALID_PHONE_NUMBER_ID,
        to=CUSTOMER_NUMBER,
        body="Hola, ¿en qué te puedo ayudar?",
    )


def test_webhook_ignores_unknown_business(client):
    """POST /webhook returns 200 but skips dispatch when phone number ID is unknown."""
    with patch("app.main.dispatch", new=AsyncMock()) as mock_dispatch:
        response = client.post("/webhook", json=_meta_text_payload(phone_number_id="000000000000000"))

    assert response.status_code == 200
    mock_dispatch.assert_not_awaited()
    client.app.state.whatsapp_client.send_text_message.assert_not_awaited()


def test_webhook_ignores_status_updates(client):
    """POST /webhook returns 200 for status updates without generating replies."""
    with patch("app.main.dispatch", new=AsyncMock()) as mock_dispatch:
        response = client.post("/webhook", json=_meta_status_payload())

    assert response.status_code == 200
    mock_dispatch.assert_not_awaited()
    client.app.state.whatsapp_client.send_text_message.assert_not_awaited()


def test_webhook_validates_meta_signature_when_app_secret_set(client):
    """POST /webhook rejects requests with an invalid Meta signature."""
    client.app.state.settings.whatsapp_app_secret = "super-secret"
    response = client.post(
        "/webhook",
        json=_meta_text_payload(),
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 403


def test_webhook_accepts_valid_meta_signature(client):
    """POST /webhook accepts valid HMAC signatures when an app secret is configured."""
    client.app.state.settings.whatsapp_app_secret = "super-secret"
    raw_body = json.dumps(_meta_text_payload(), separators=(",", ":")).encode("utf-8")
    signature = "sha256=" + hmac.new(
        b"super-secret",
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    with patch(
        "app.main.dispatch",
        new=AsyncMock(return_value="Hola, ¿en qué te puedo ayudar?"),
    ):
        response = client.post(
            "/webhook",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature,
            },
        )

    assert response.status_code == 200
