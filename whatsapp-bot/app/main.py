"""FastAPI application: Twilio WhatsApp webhook, health endpoint, signature validation."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from app.config import get_settings
from app.businesses import BUSINESSES
from app.gemini_client import GeminiClient
from app.session_store import SessionStore
from app.handlers.qa import QAHandler


# Module-level handler instances
_qa_handler = QAHandler()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize shared resources on startup."""
    settings = get_settings()
    gemini_client = GeminiClient(api_key=settings.gemini_api_key)
    application.state.session_store = SessionStore(gemini_client=gemini_client)
    application.state.settings = settings
    yield
    # Cleanup (if needed) goes here


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
    4. Route to QAHandler (dispatcher comes in Plan 02).
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

    # Process message with QAHandler (Plan 02 adds full dispatcher)
    try:
        reply_text = await _qa_handler.handle(body, session, business)
    except Exception:
        reply_text = "Lo siento, ocurrió un error al procesar tu mensaje. Por favor intenta de nuevo."

    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")
