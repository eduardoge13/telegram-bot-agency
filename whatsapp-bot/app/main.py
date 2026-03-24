"""FastAPI application: Twilio WhatsApp webhook, health endpoint, signature validation."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from app.config import get_settings
from app.businesses import BUSINESSES
from app.gemini_client import GeminiClient
from app.session_store import SessionStore
from app.dispatcher import dispatch

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize shared resources on startup."""
    settings = get_settings()
    gemini_client = GeminiClient(api_key=settings.gemini_api_key)
    application.state.session_store = SessionStore(gemini_client=gemini_client)
    application.state.settings = settings

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


app = FastAPI(title="WhatsApp Bot Service", version="1.0.0", lifespan=lifespan)


async def validate_twilio(request: Request):
    """FastAPI dependency: validate Twilio webhook signature.

    Reconstructs the public HTTPS URL using WEBHOOK_BASE_URL setting (most reliable
    behind Traefik — avoids x-forwarded-proto header reconstruction issues).
    Falls back to x-forwarded-proto + host if WEBHOOK_BASE_URL not set.
    """
    settings = get_settings()
    validator = RequestValidator(settings.twilio_auth_token)

    # Use configured WEBHOOK_BASE_URL if available (recommended for Traefik deployments)
    if settings.webhook_base_url:
        url = f"{settings.webhook_base_url}{request.url.path}"
    else:
        # Fallback: reconstruct from headers (may fail behind some proxies)
        forwarded_proto = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("host", "")
        url = f"{forwarded_proto}://{host}{request.url.path}"

    form = await request.form()
    signature = request.headers.get("x-twilio-signature", "")

    if not validator.validate(url, dict(form), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    return dict(form)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "whatsapp-bot"}


@app.post("/webhook")
async def webhook(
    request: Request,
    form: dict = Depends(validate_twilio),
):
    """Receive incoming WhatsApp messages via Twilio webhook.

    1. Extract To (business), From (customer), Body (message) from form data.
    2. Look up business config by Twilio number.
    3. Get or create session for (business_id, customer_phone).
    4. Dispatch to handler chain (product, flight, order, or QA fallback).
    5. Return TwiML XML response.
    """
    to_number = form.get("To", "")
    from_number = form.get("From", "")
    body = form.get("Body", "")

    # Look up business by Twilio destination number
    business = BUSINESSES.get(to_number)
    if business is None:
        resp = MessagingResponse()
        resp.message("Lo siento, este servicio no está disponible en este número.")
        return Response(content=str(resp), media_type="application/xml")

    # Get or create conversation session
    session_store: SessionStore = request.app.state.session_store
    session = session_store.get_or_create(
        business_id=business.business_id,
        phone=from_number,
        system_prompt=business.system_prompt,
    )

    # Retrieve shared resources from app state
    sheets_clients: dict = getattr(request.app.state, "sheets_clients", {})
    amadeus_provider = getattr(request.app.state, "amadeus_provider", None)

    # Dispatch to handler chain
    try:
        reply_text = await dispatch(
            business=business,
            session=session,
            message=body,
            sheets_clients=sheets_clients,
            amadeus_provider=amadeus_provider,
        )
    except Exception:
        logger.exception("Dispatch failed for business %s, phone %s", business.business_id, from_number)
        reply_text = "Lo siento, ocurrió un error al procesar tu mensaje. Por favor intenta de nuevo."

    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")
