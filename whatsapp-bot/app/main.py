"""FastAPI application: Meta WhatsApp webhook, health endpoint, outbound messaging."""
import hashlib
import hmac
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.businesses import BUSINESSES
from app.gemini_client import GeminiClient
from app.meta_client import MetaWhatsAppClient
from app.session_store import SessionStore
from app.dispatcher import dispatch

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize shared resources on startup."""
    settings = get_settings()
    gemini_client = GeminiClient(api_key=settings.gemini_api_key)
    whatsapp_client = MetaWhatsAppClient(
        access_token=settings.whatsapp_access_token,
        api_version=settings.whatsapp_api_version,
    )
    application.state.session_store = SessionStore(gemini_client=gemini_client)
    application.state.settings = settings
    application.state.whatsapp_client = whatsapp_client

    # Initialize ProductSheetsClient for each business that has a sheets_id
    sheets_clients: dict = {}
    for number, business in BUSINESSES.items():
        if business.sheets_id:
            try:
                from app.sheets.client import ProductSheetsClient
                sheets_clients[business.business_id] = ProductSheetsClient(
                    spreadsheet_id=business.sheets_id,
                    sheets_range=business.sheets_range,
                )
                logger.info("Initialized ProductSheetsClient for business: %s", business.business_id)
            except Exception:
                logger.exception("Failed to init ProductSheetsClient for %s — product lookup disabled", business.business_id)
    application.state.sheets_clients = sheets_clients

    # Initialize AmadeusProvider (best-effort — if credentials missing, log and skip)
    amadeus_provider = None
    try:
        from app.providers.amadeus import AmadeusProvider
        amadeus_provider = AmadeusProvider()
        logger.info("AmadeusProvider initialized")
    except KeyError as exc:
        logger.warning("AmadeusProvider not initialized — missing env var: %s", exc)
    except Exception:
        logger.exception("AmadeusProvider initialization failed")
    application.state.amadeus_provider = amadeus_provider

    yield

    # Cleanup
    if amadeus_provider is not None:
        try:
            await amadeus_provider.close()
        except Exception:
            pass
    try:
        await whatsapp_client.close()
    except Exception:
        pass


app = FastAPI(title="WhatsApp Bot Service", version="1.0.0", lifespan=lifespan)


def _validate_meta_signature(raw_body: bytes, signature: str, app_secret: str) -> None:
    """Validate Meta webhook signature when an app secret is configured."""
    if not app_secret:
        return

    if not signature:
        raise HTTPException(status_code=403, detail="Missing Meta signature")

    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail="Invalid Meta signature")


def _extract_message_text(message: dict) -> str:
    """Extract a user-visible text value from supported inbound message types."""
    message_type = message.get("type")
    if message_type == "text":
        return (message.get("text") or {}).get("body", "").strip()
    if message_type == "button":
        return (message.get("button") or {}).get("text", "").strip()
    if message_type == "interactive":
        interactive = message.get("interactive") or {}
        interactive_type = interactive.get("type")
        if interactive_type == "button_reply":
            return (interactive.get("button_reply") or {}).get("title", "").strip()
        if interactive_type == "list_reply":
            return (interactive.get("list_reply") or {}).get("title", "").strip()
    return ""


async def _process_whatsapp_events(application: FastAPI, payload: dict) -> None:
    """Process inbound webhook events and reply through the Meta API."""
    session_store: SessionStore = application.state.session_store
    sheets_clients: dict = getattr(application.state, "sheets_clients", {})
    amadeus_provider = getattr(application.state, "amadeus_provider", None)
    whatsapp_client: MetaWhatsAppClient = application.state.whatsapp_client

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            phone_number_id = metadata.get("phone_number_id", "")
            business = BUSINESSES.get(phone_number_id)
            if business is None:
                if value.get("messages"):
                    logger.warning("No business is configured for phone_number_id=%s", phone_number_id)
                continue

            for message in value.get("messages") or []:
                from_number = message.get("from", "")
                body = _extract_message_text(message)
                if not from_number or not body:
                    logger.info(
                        "Skipping unsupported or empty inbound message for business %s: type=%s",
                        business.business_id,
                        message.get("type"),
                    )
                    continue

                session = session_store.get_or_create(
                    business_id=business.business_id,
                    phone=from_number,
                    system_prompt=business.system_prompt,
                )

                try:
                    reply_text = await dispatch(
                        business=business,
                        session=session,
                        message=body,
                        sheets_clients=sheets_clients,
                        amadeus_provider=amadeus_provider,
                    )
                except Exception:
                    logger.exception(
                        "Dispatch failed for business %s, phone %s",
                        business.business_id,
                        from_number,
                    )
                    reply_text = (
                        "Lo siento, ocurrió un error al procesar tu mensaje. "
                        "Por favor intenta de nuevo."
                    )

                try:
                    await whatsapp_client.send_text_message(
                        phone_number_id=business.phone_number_id,
                        to=from_number,
                        body=reply_text,
                    )
                except Exception:
                    logger.exception(
                        "Failed to send WhatsApp reply for business %s, phone %s",
                        business.business_id,
                        from_number,
                    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "whatsapp-bot"}


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Handle Meta webhook verification challenge."""
    settings = get_settings()
    if (
        hub_mode == "subscribe"
        and hub_verify_token == settings.whatsapp_verify_token
        and hub_challenge is not None
    ):
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Invalid webhook verification token")


@app.post("/webhook")
async def webhook(request: Request):
    """Receive incoming WhatsApp webhook events from Meta."""
    raw_body = await request.body()
    settings = request.app.state.settings

    _validate_meta_signature(
        raw_body=raw_body,
        signature=request.headers.get("x-hub-signature-256", ""),
        app_secret=settings.whatsapp_app_secret,
    )

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if payload.get("object") != "whatsapp_business_account":
        raise HTTPException(status_code=404, detail="Unsupported webhook object")

    await _process_whatsapp_events(request.app, payload)
    return {"status": "ok"}
