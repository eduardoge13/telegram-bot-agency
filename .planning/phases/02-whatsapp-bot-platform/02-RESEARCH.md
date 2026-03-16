# Phase 2: WhatsApp Bot Platform - Research

**Researched:** 2026-03-16
**Domain:** Twilio WhatsApp webhooks, Gemini AI chat, Google Sheets product lookup, multi-tenant bot architecture, Python/FastAPI, Docker/Traefik VPS deployment
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Free-form AI chat — no menus, no guided flows for e-commerce. Gemini interprets intent
- Auto-detect product intent — Gemini triggers Google Sheets search automatically
- When product not found: suggest similar products (partial match) and offer human handoff
- Session memory: retain last ~10 messages per conversation. Resets after inactivity
- Conversational inline product format — info woven into AI response, not a card
- Prices displayed as $25,999 MXN (dollar sign, comma separators, MXN suffix)
- After product info: bot proactively asks "¿Te gustaría hacer un pedido?"
- Order collection MVP: collect name, product, quantity → save to Google Sheets → notify owner
- No in-chat payment — order collection only
- Both businesses fully configured from day one: Punto Clave MX + travel agency
- Separate Twilio WhatsApp numbers per business — config maps incoming number → business context
- Each business defined by: Twilio number, system prompt, Google Sheets ID, enabled features/handlers
- New business onboarding requires only a config entry
- Travel agency uses guided step-by-step flight search: origin → destination → date → Amadeus search
- Present top 3-5 cheapest flight options with airline, price, stops, duration
- Reuse `AmadeusProvider` class from `/Users/eduardogaitan/Documents/projects/flights-price-panel`
- Bot service on port 3001 per INFRA-05
- VPS uses Traefik + Docker labels + n8n_default network (established pattern from Phase 1)
- Google Sheets as data store (no database)
- Python + async for the bot service (consistent with existing codebase)
- Credentials via env vars / .env file for VPS deployment (not GCP Secret Manager)

### Claude's Discretion
- Bot personality and tone (formal/informal Spanish)
- Technical architecture (language choice, framework, project structure)
- How to integrate AmadeusProvider into the WhatsApp bot service
- Session timeout duration
- Error handling and retry strategies
- Notification mechanism for orders (Telegram vs Sheets flag)
- Exact system prompts per business

### Deferred Ideas (OUT OF SCOPE)
- Payment links via WhatsApp (PAY-05) — v2
- Order status tracking via WhatsApp (ADV-02) — v2
- Working-hours awareness with auto-reply (ADV-04) — v2
- Admin field editing via WhatsApp (ADV-03) — v2
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-05 | WhatsApp bot service running on VPS port 3001 | Docker Compose with Traefik labels pattern established in Phase 1; port 3001 mapped internally, Traefik routes by hostname |
| BOT-01 | Express server receives Twilio WhatsApp webhook messages with signature validation | `twilio` Python SDK `RequestValidator`; `twilio.request_validator` class with URL + form + X-Twilio-Signature header; must reconstruct HTTPS URL behind Traefik |
| BOT-02 | Gemini AI generates contextual responses in Spanish based on business system prompt | New `google-genai` SDK (`google.genai`); `client.chats.create()` with `system_instruction` + `send_message()`; chat object maintains history automatically |
| BOT-03 | Bot looks up product info from Google Sheets when customer asks about products | Existing `GoogleSheetsManager` pattern from `bot_telegram_polling.py`; service account JSON as env var; `google-api-python-client` v2 |
| BOT-04 | Bot sends formatted product details (name, price, availability) via WhatsApp | `twilio.twiml.messaging_response.MessagingResponse` to reply inline; plain text woven into Gemini response |
| PLAT-01 | Config-driven business registry: Twilio number, system prompt, Google Sheets ID, enabled features | Python dataclass/dict config; businesses.py or config.yaml with per-business settings |
| PLAT-02 | Modular message handler architecture — pluggable handlers per business | Handler pattern: `ProductHandler`, `FlightHandler`, `QAHandler` — each handler checks intent and returns result; dispatcher routes per business feature list |
| PLAT-03 | Conversation context isolation — state keyed on (businessId, customerPhone) | In-memory dict `sessions[(business_id, customer_phone)]` with TTL expiry; no cross-business bleed |
| PLAT-04 | New business onboarding requires only config changes for basic Q&A + product lookup | Config-driven — new business dict entry with twilio_number, system_prompt, sheets_id, handlers list |
</phase_requirements>

---

## Summary

The WhatsApp bot platform is a Python (FastAPI or Flask) service that receives Twilio webhook POSTs, routes incoming messages to the correct business context based on the destination Twilio number, invokes Gemini AI with a business-specific system prompt and per-customer conversation history, optionally queries Google Sheets for product data or Amadeus for flight prices, and replies via TwiML. The service is containerized and deployed on the existing Hostinger VPS using the established Traefik + Docker pattern.

The core technical challenges are: (1) correct Twilio webhook signature validation behind Traefik (HTTPS URL reconstruction), (2) per-(business, customer) session isolation with in-memory state and TTL expiry, (3) intent detection integrated into the Gemini conversation flow rather than a separate classifier, and (4) shipping AmadeusProvider from the flights-price-panel project as a local dependency.

The existing codebase provides most building blocks: `GoogleSheetsManager` (in `bot_telegram_polling.py`) covers Sheets integration with retry and caching; `AmadeusProvider` (in `flights-price-panel/app/providers/`) covers OAuth2 Amadeus search; both are production-tested. The new code is the HTTP layer (Twilio webhook), the Gemini integration, the business registry, and the session store.

**Primary recommendation:** Use FastAPI + uvicorn (async-native, better than Flask for async Sheets/Amadeus calls), the new `google-genai` SDK for Gemini, and plain `twilio` Python SDK for webhook validation and TwiML responses.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | >=0.110 | HTTP server for Twilio webhook endpoint | Async-native; matches existing async patterns in flights-price-panel; better than Flask for concurrent requests |
| uvicorn | >=0.29 | ASGI server (replaces gunicorn for async) | Standard FastAPI server; supports `--reload` in dev |
| twilio | >=9.0 | Webhook signature validation + TwiML response generation | Official SDK; `RequestValidator` is the only safe way to validate signatures |
| google-genai | >=1.0 | Gemini AI chat with system_instruction and multi-turn history | New unified Google Gen AI SDK; older `google-generativeai` is deprecated |
| google-api-python-client | 2.134.0 | Google Sheets read/write | Already in project requirements.txt; battle-tested pattern in `bot_telegram_polling.py` |
| google-auth | >=2.0 | Service account credentials for Sheets | Paired with google-api-python-client |
| httpx | >=0.27 | Async HTTP for Amadeus API calls | Already used in AmadeusProvider; async-native |
| python-dotenv | 1.0.1 | Load .env file on VPS | Already in project; standard for VPS env management |
| pydantic | >=2.0 | Config validation, request models | FastAPI dependency; also used in flights-price-panel |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | >=2.0 | Settings from env vars with type validation | Config management — used in flights-price-panel already |
| pytz | 2024.1 | Mexico City timezone for session expiry | Already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI | Flask | Flask is synchronous by default and already in the project, but requires async wrappers for Sheets/Amadeus. FastAPI is cleaner for async; migration cost is low since new service |
| google-genai (new) | google-generativeai (old) | Old SDK is officially deprecated as of late 2024. New SDK has `client.chats.create()` with cleaner multi-turn API. Use the new one. |
| in-memory session dict | Redis | Redis adds operational complexity (another Docker service). For MVP traffic volumes, an in-memory TTL dict is sufficient. |

**Installation:**
```bash
pip install fastapi uvicorn twilio google-genai google-api-python-client google-auth httpx python-dotenv pydantic pydantic-settings pytz
```

---

## Architecture Patterns

### Recommended Project Structure
```
whatsapp-bot/
├── app/
│   ├── main.py              # FastAPI app, /webhook endpoint, /health
│   ├── config.py            # Settings (pydantic-settings), business registry loader
│   ├── businesses.py        # Business config definitions (Punto Clave MX, travel agency)
│   ├── dispatcher.py        # Routes incoming message to correct business + handler chain
│   ├── session_store.py     # In-memory (businessId, phone) → ConversationSession with TTL
│   ├── gemini_client.py     # Wraps google-genai SDK; manages chat objects per session
│   ├── handlers/
│   │   ├── base.py          # BaseHandler abstract class
│   │   ├── product.py       # ProductHandler: intent detection + Sheets lookup
│   │   ├── flight.py        # FlightHandler: guided step flow + AmadeusProvider
│   │   ├── order.py         # OrderHandler: collect name/product/qty, append to Sheets
│   │   └── qa.py            # QAHandler: pure AI Q&A fallback
│   ├── sheets/
│   │   └── client.py        # ProductSheetsClient (adapted from GoogleSheetsManager)
│   └── providers/
│       ├── amadeus.py       # Copy/symlink of AmadeusProvider from flights-price-panel
│       └── base.py          # Copy/symlink of FlightProvider base
├── Dockerfile
├── docker-compose.yml       # Traefik labels, n8n_default network, port 3001 internal
├── .env.example
└── requirements.txt
```

### Pattern 1: Business Registry (PLAT-01, PLAT-04)
**What:** A Python dict keyed on the Twilio number. Each entry is a `BusinessConfig` dataclass.
**When to use:** Every incoming webhook — dispatcher looks up `businesses[to_number]`
**Example:**
```python
# app/businesses.py
from dataclasses import dataclass, field

@dataclass
class BusinessConfig:
    business_id: str
    twilio_number: str        # e.g. "whatsapp:+15005550006"
    system_prompt: str
    sheets_id: str | None     # None if no product lookup
    handlers: list[str]       # e.g. ["product", "order", "qa"]
    language: str = "es"

BUSINESSES: dict[str, BusinessConfig] = {
    "whatsapp:+15005550006": BusinessConfig(
        business_id="puntoclave",
        twilio_number="whatsapp:+15005550006",
        system_prompt="Eres el asistente virtual de Punto Clave MX...",
        sheets_id="<SPREADSHEET_ID>",
        handlers=["product", "order", "qa"],
    ),
    "whatsapp:+15005550007": BusinessConfig(
        business_id="travel",
        twilio_number="whatsapp:+15005550007",
        system_prompt="Eres el asistente de viajes...",
        sheets_id=None,
        handlers=["flight", "qa"],
    ),
}
```

### Pattern 2: Twilio Webhook Handler with Signature Validation (BOT-01)
**What:** FastAPI dependency that validates X-Twilio-Signature before processing any request.
**Critical note:** Behind Traefik, FastAPI sees an HTTP request internally. Must reconstruct the public HTTPS URL using `X-Forwarded-Proto` and `Host` headers — or hardcode the public URL. Twilio validates against the exact URL it called.
**Example:**
```python
# app/main.py
from fastapi import FastAPI, Request, Depends, HTTPException
from twilio.request_validator import RequestValidator
import os

app = FastAPI()
validator = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"])

async def validate_twilio(request: Request):
    # Reconstruct the original HTTPS URL Twilio used
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "")
    url = f"{forwarded_proto}://{host}{request.url.path}"

    form = await request.form()
    signature = request.headers.get("x-twilio-signature", "")

    if not validator.validate(url, dict(form), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    return dict(form)

@app.post("/webhook")
async def webhook(form: dict = Depends(validate_twilio)):
    to_number = form["To"]    # destination Twilio number (identifies business)
    from_number = form["From"] # sender WhatsApp number
    body = form["Body"]        # message text
    # ... dispatch to handler
```

### Pattern 3: Session Store with TTL (PLAT-03)
**What:** In-memory dict keyed on `(business_id, customer_phone)`. Each session holds the Gemini chat object and last-active timestamp.
**When to use:** Every message — look up or create session before calling Gemini.
**Example:**
```python
# app/session_store.py
import time
from dataclasses import dataclass, field
from google import genai
from google.genai import types

SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes of inactivity

@dataclass
class ConversationSession:
    chat: object  # google.genai Chat object
    last_active: float = field(default_factory=time.time)
    state: dict = field(default_factory=dict)  # for flight search multi-step state

class SessionStore:
    def __init__(self):
        self._sessions: dict[tuple, ConversationSession] = {}
        self._gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def get_or_create(self, business_id: str, phone: str, system_prompt: str) -> ConversationSession:
        key = (business_id, phone)
        session = self._sessions.get(key)

        # Expire session on timeout
        if session and time.time() - session.last_active > SESSION_TIMEOUT_SECONDS:
            del self._sessions[key]
            session = None

        if not session:
            chat = self._gemini_client.chats.create(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=1024,
                    temperature=0.7,
                )
            )
            session = ConversationSession(chat=chat)
            self._sessions[key] = session

        session.last_active = time.time()
        return session
```

### Pattern 4: Handler Chain with Intent Detection (PLAT-02)
**What:** Each handler has a `can_handle(message, session_state)` check. Dispatcher iterates the business's handler list and uses the first match. Product and flight handlers detect intent via Gemini's response or keywords.
**When to use:** After session lookup, before sending to Gemini.
**Example:**
```python
# app/dispatcher.py
async def dispatch(business: BusinessConfig, session: ConversationSession, message: str) -> str:
    for handler_name in business.handlers:
        handler = handler_registry[handler_name]
        if await handler.can_handle(message, session.state):
            return await handler.handle(message, session, business)
    # Fallback: pure AI
    return (await session.chat.send_message_async(message)).text
```

### Pattern 5: Google Sheets Product Lookup (BOT-03)
**What:** Adapted `GoogleSheetsManager` pattern — load sheet on startup, build in-memory index, fuzzy search by product name.
**Critical detail:** Use service account JSON stored as env var `GOOGLE_CREDENTIALS_JSON` (string), not a file path. Parse with `Credentials.from_service_account_info(json.loads(...))`. This is the VPS-safe pattern (no GCP Secret Manager needed).
**Example:**
```python
# app/sheets/client.py
import json, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class ProductSheetsClient:
    def __init__(self, spreadsheet_id: str):
        creds_json = os.environ["GOOGLE_CREDENTIALS_JSON"]
        creds = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        self.spreadsheet_id = spreadsheet_id

    def search_product(self, query: str) -> list[dict]:
        """Returns matching products with name, price, availability columns."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range="Sheet1!A:D"
        ).execute()
        rows = result.get("values", [])
        headers = rows[0] if rows else []
        query_lower = query.lower()
        matches = []
        for row in rows[1:]:
            row_dict = dict(zip(headers, row))
            name = row_dict.get("nombre", "")
            if query_lower in name.lower():
                matches.append(row_dict)
        return matches
```

### Pattern 6: AmadeusProvider Integration
**What:** Copy `amadeus.py` and `base.py` from `flights-price-panel/app/providers/` into the new service's `app/providers/` directory. The `AmadeusProvider` is self-contained and only depends on `httpx` and its own `base.py`. Extract credentials from env vars instead of pydantic-settings.
**Critical:** The AmadeusProvider's `__init__` calls `get_settings()` which reads from flights-price-panel's config. For the WhatsApp bot, patch it to read directly from `os.environ["AMADEUS_CLIENT_ID"]` and `os.environ["AMADEUS_CLIENT_SECRET"]`.

### Pattern 7: Docker Compose with Traefik (INFRA-05)
**What:** Follow the exact same pattern as the ecommerce site deployment. Use Docker labels for Traefik routing on the `n8n_default` network. No host port binding — Traefik discovers the container.
**Example:**
```yaml
# docker-compose.yml
services:
  whatsapp-bot:
    build: .
    restart: unless-stopped
    networks:
      - n8n_default
    expose:
      - "3001"
    environment:
      - PORT=3001
    env_file:
      - .env
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.whatsapp-bot.rule=Host(`bot.srv1175749.hstgr.cloud`)"
      - "traefik.http.routers.whatsapp-bot.tls=true"
      - "traefik.http.routers.whatsapp-bot.tls.certresolver=myresolver"
      - "traefik.http.services.whatsapp-bot.loadbalancer.server.port=3001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  n8n_default:
    external: true
```

The Twilio webhook URL will be: `https://bot.srv1175749.hstgr.cloud/webhook`

### Anti-Patterns to Avoid
- **Storing Gemini chat objects in a database:** The `google-genai` Chat object is in-memory only. History must be reconstructed if the process restarts. For MVP, in-memory is acceptable.
- **Using Flask sync views for Sheets/Amadeus calls:** Flask sync handlers block the thread. Use FastAPI async endpoints with `await` throughout.
- **Reconstructing URL from `request.url`:** FastAPI's `request.url` may use the internal HTTP scheme. Always check `x-forwarded-proto` header to get the public HTTPS URL for Twilio signature validation.
- **Single Sheets client for all businesses:** Each business has its own `sheets_id`. The `ProductSheetsClient` must be instantiated per-business at startup.
- **Blocking Gemini call in webhook handler:** Always use `await chat.send_message_async(message)` to avoid blocking uvicorn's event loop.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Twilio signature validation | Custom HMAC validation | `twilio.request_validator.RequestValidator` | Subtle URL encoding edge cases will break custom impl |
| TwiML XML response | Hand-craft XML strings | `twilio.twiml.messaging_response.MessagingResponse` | Reply must be exact TwiML — SDK handles encoding |
| Gemini chat history | Manual message list | `google-genai` Chat object (`client.chats.create()`) | SDK manages history ordering, roles, and context window automatically |
| Amadeus OAuth2 token refresh | Custom token refresh logic | `AmadeusProvider.authenticate()` (existing) | Already handles expiry, refresh, and error cases |
| Product fuzzy match | Levenshtein distance library | Case-insensitive substring search in-memory | For MVP product catalog size, substring match is sufficient; Gemini does intent extraction |

**Key insight:** The Twilio URL reconstruction behind a reverse proxy is the most likely source of 403 errors during testing. Always verify `X-Forwarded-Proto` is set in Traefik config.

---

## Common Pitfalls

### Pitfall 1: Twilio Signature Validation Fails Behind Traefik
**What goes wrong:** Webhook returns 403 for all incoming messages. Twilio retries, bot appears silent.
**Why it happens:** Traefik terminates SSL. FastAPI sees `http://` internally. `RequestValidator.validate(url, ...)` hashes the internal HTTP URL but Twilio signed the external HTTPS URL.
**How to avoid:** Reconstruct URL using `x-forwarded-proto` and `host` headers: `f"{request.headers.get('x-forwarded-proto', 'https')}://{request.headers.get('host')}{request.url.path}"`. Or set `WEBHOOK_BASE_URL` env var with the public HTTPS URL and use it directly.
**Warning signs:** All webhook requests return 403; Twilio console shows "Webhook Failure" errors.

### Pitfall 2: google-generativeai vs google-genai Confusion
**What goes wrong:** Import errors or `AttributeError: module 'google.generativeai' has no attribute 'Client'` at runtime.
**Why it happens:** There are two packages: the old deprecated `google-generativeai` and the new `google-genai`. The new SDK uses `from google import genai` and `client = genai.Client()`. The old used `import google.generativeai as genai`.
**How to avoid:** Install `google-genai` (not `google-generativeai`). Use `from google import genai; client = genai.Client(api_key=...)`.
**Warning signs:** Import succeeds but `genai.Client` doesn't exist, or you see `GenerativeModel` instead of `Client`.

### Pitfall 3: Session Cross-Contamination
**What goes wrong:** Customer A's conversation history bleeds into Customer B's response.
**Why it happens:** Gemini chat objects are shared or session key uses only phone number (not business_id).
**How to avoid:** Key sessions as `(business_id, customer_phone)` tuple. Each key gets its own Chat object. Verified: `sessions[(business_id, phone)]`.
**Warning signs:** Bot uses context from a different customer's conversation.

### Pitfall 4: Blocking Event Loop with Sync Sheets API
**What goes wrong:** Bot response time exceeds Twilio's 15-second timeout; Twilio retries; double responses.
**Why it happens:** `google-api-python-client` is synchronous. Calling it directly in an async FastAPI handler blocks the event loop.
**How to avoid:** Wrap Sheets calls in `asyncio.get_event_loop().run_in_executor(None, sync_func)`. Or cache the product catalog in memory at startup and refresh periodically (10-minute TTL like the existing `GoogleSheetsManager`).
**Warning signs:** Response times creep above 5 seconds; Twilio timeout errors in logs.

### Pitfall 5: Twilio 15-Second Webhook Timeout
**What goes wrong:** Bot doesn't reply; Twilio shows timeout; customer receives no message.
**Why it happens:** Gemini + Sheets lookup chain takes >15s (rare but possible under cold start or API slowness).
**How to avoid:** Respond immediately with an empty TwiML and send the actual reply via outbound message using `twilio.rest.Client.messages.create()`. For MVP, optimize request chain to stay under 10s: product cache in memory, Gemini 1024-token limit.
**Warning signs:** Occasional "no reply" for the first message after container cold start.

### Pitfall 6: AmadeusProvider Credential Coupling
**What goes wrong:** `AmadeusProvider.__init__` calls `get_settings()` which reads from `flights-price-panel`'s pydantic settings, raising `ValidationError` about missing database_url etc.
**Why it happens:** The flights-price-panel config has fields (database_url, etc.) with no defaults that will fail if not present.
**How to avoid:** When copying `amadeus.py` into the new service, replace `settings = get_settings()` with direct `os.environ` reads: `self._client_id = os.environ["AMADEUS_CLIENT_ID"]`.

---

## Code Examples

Verified patterns from official sources:

### Twilio Webhook — Receive and Reply
```python
# Source: https://www.twilio.com/docs/messaging/tutorials/how-to-receive-and-reply/python
from twilio.twiml.messaging_response import MessagingResponse

@app.post("/webhook")
async def webhook(form: dict = Depends(validate_twilio)):
    body = form["Body"]
    from_number = form["From"]  # e.g. "whatsapp:+521234567890"
    to_number = form["To"]      # e.g. "whatsapp:+15005550006"

    ai_reply = await process_message(to_number, from_number, body)

    resp = MessagingResponse()
    resp.message(ai_reply)
    return Response(content=str(resp), media_type="application/xml")
```

### Gemini Chat with System Instruction (Multi-Turn)
```python
# Source: https://googleapis.github.io/python-genai/
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

chat = client.chats.create(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction="Eres el asistente de Punto Clave MX. Responde en español informal...",
        max_output_tokens=1024,
        temperature=0.7,
    )
)

# Each send_message call automatically includes all prior history
response = await chat.send_message_async("¿Tienen laptops disponibles?")
print(response.text)  # "¡Claro! Tenemos varias opciones de laptops..."
```

### Google Sheets Service Account from Env Var
```python
# Source: https://mljar.com/blog/authenticate-python-google-sheets-service-account-json-credentials/
import json, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build("sheets", "v4", credentials=creds, cache_discovery=False)
```

### Amadeus Flight Search (Existing, Verified)
```python
# Source: flights-price-panel/app/providers/amadeus.py (production code)
from datetime import date

provider = AmadeusProvider()  # reads AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET from env
result = await provider.search_flights(
    origin="MEX",
    destination="CUN",
    departure_date=date(2026, 4, 15),
    adults=1,
    max_results=5,
)
# result.offers sorted by price: result.offers[0].price, .airline, .stops, .duration
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `google-generativeai` package | `google-genai` package (`from google import genai`) | Late 2024 | Old package deprecated; new SDK has cleaner Chat API |
| Flask + Twilio | FastAPI + Twilio | Ongoing preference shift | FastAPI is async-native; better for concurrent webhook handling |
| GCP Secret Manager for credentials | Env vars / .env file on VPS | Project decision | Simpler for single-VPS deployment without GCP infrastructure |

**Deprecated/outdated:**
- `google-generativeai`: Deprecated; do not use. Use `google-genai` instead.
- `GenerativeModel` class: From old SDK. New SDK uses `client.chats.create()`.

---

## Open Questions

1. **Twilio number assignment**
   - What we know: Two businesses need two separate Twilio WhatsApp numbers
   - What's unclear: Twilio credentials and sandbox numbers not yet obtained; sandbox uses shared number with join code
   - Recommendation: Build with configurable number env vars; test with Twilio sandbox; document switch to production numbers

2. **Order notification mechanism (Claude's Discretion)**
   - What we know: Owner must be notified when an order is collected
   - What's unclear: Telegram bot notification requires the existing bot to be running; Sheets flag is simpler
   - Recommendation: Write to a dedicated "Pedidos" sheet tab with status="Nuevo"; owner checks the sheet. Add Telegram notification as an optional second step after sheet write.

3. **Gemini API key**
   - What we know: Need `GEMINI_API_KEY` from Google AI Studio (not Google Cloud)
   - What's unclear: Key not yet confirmed as available
   - Recommendation: Obtain from https://aistudio.google.com/apikey; free tier supports MVP volume

4. **AmadeusProvider test vs production URL**
   - What we know: `amadeus_base_url` defaults to `https://test.api.amadeus.com` in flights-price-panel
   - What's unclear: Production Amadeus credentials not confirmed
   - Recommendation: Use test environment during development; add `AMADEUS_ENV=test|production` env var to switch

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (standard; existing `tests/` directory in telegram-bot-agency) |
| Config file | `pytest.ini` or `pyproject.toml` — none detected; Wave 0 creates `pytest.ini` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-05 | Bot service starts on port 3001, /health returns 200 | smoke | `pytest tests/test_health.py -x` | Wave 0 |
| BOT-01 | Valid Twilio signature accepted; invalid signature returns 403 | unit | `pytest tests/test_webhook.py::test_signature_valid -x` | Wave 0 |
| BOT-01 | HTTPS URL reconstructed correctly from X-Forwarded-Proto header | unit | `pytest tests/test_webhook.py::test_url_reconstruction -x` | Wave 0 |
| BOT-02 | Gemini generates Spanish response given system prompt | integration | `pytest tests/test_gemini.py::test_spanish_response -x` | Wave 0 |
| BOT-03 | Product search returns results for known product name | unit | `pytest tests/test_sheets.py::test_product_search -x` | Wave 0 |
| BOT-04 | TwiML response contains product info inline | unit | `pytest tests/test_handlers.py::test_product_handler_output -x` | Wave 0 |
| PLAT-01 | Business registry resolves correct config by Twilio number | unit | `pytest tests/test_config.py::test_business_lookup -x` | Wave 0 |
| PLAT-02 | Handler chain picks correct handler for product vs flight intent | unit | `pytest tests/test_dispatcher.py::test_handler_routing -x` | Wave 0 |
| PLAT-03 | Two sessions with different (business_id, phone) keys are isolated | unit | `pytest tests/test_session_store.py::test_session_isolation -x` | Wave 0 |
| PLAT-03 | Session expires after inactivity timeout | unit | `pytest tests/test_session_store.py::test_session_expiry -x` | Wave 0 |
| PLAT-04 | Adding a third business config entry routes correctly without code change | unit | `pytest tests/test_config.py::test_new_business_no_code_change -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `whatsapp-bot/tests/test_webhook.py` — covers BOT-01 (signature validation, URL reconstruction)
- [ ] `whatsapp-bot/tests/test_gemini.py` — covers BOT-02 (Gemini Spanish response; requires GEMINI_API_KEY)
- [ ] `whatsapp-bot/tests/test_sheets.py` — covers BOT-03 (product search; can use mock Sheets service)
- [ ] `whatsapp-bot/tests/test_handlers.py` — covers BOT-04, PLAT-02
- [ ] `whatsapp-bot/tests/test_config.py` — covers PLAT-01, PLAT-04
- [ ] `whatsapp-bot/tests/test_session_store.py` — covers PLAT-03
- [ ] `whatsapp-bot/tests/test_health.py` — covers INFRA-05 (smoke test)
- [ ] `whatsapp-bot/pytest.ini` — basic config pointing to tests/
- [ ] Framework install: `pip install pytest pytest-asyncio` if not present

---

## Sources

### Primary (HIGH confidence)
- Twilio official docs — webhook request parameters, signature validation: https://www.twilio.com/docs/messaging/guides/webhook-request
- Twilio official docs — Flask signature validation: https://www.twilio.com/docs/usage/tutorials/how-to-secure-your-flask-app-by-validating-incoming-twilio-requests
- Google Gen AI SDK official docs: https://googleapis.github.io/python-genai/
- Existing project code (directly inspected): `bot_telegram_polling.py` (GoogleSheetsManager), `flights-price-panel/app/providers/amadeus.py` (AmadeusProvider)
- Phase 1 deployment summary: `.planning/phases/01-site-infrastructure/01-02-SUMMARY.md` (Traefik pattern)

### Secondary (MEDIUM confidence)
- Google Gen AI SDK GitHub: https://github.com/googleapis/python-genai (verified new SDK vs deprecated old one)
- Twilio WhatsApp send/receive tutorial: https://www.twilio.com/en-us/blog/receive-whatsapp-messages-python-flask-twilio
- Twilio webhook security behind proxy: https://github.com/twilio/twilio-node/issues/321 (pattern confirmed applicable to Python)
- Google Sheets service account from env var: https://mljar.com/blog/authenticate-python-google-sheets-service-account-json-credentials/

### Tertiary (LOW confidence)
- Docker Compose health check + Traefik patterns: multiple blog posts (2025) — recommend verifying against official Docker docs for exact syntax

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — twilio, fastapi, google-genai verified against official docs; existing httpx/google-api-python-client already in project
- Architecture: HIGH — patterns derived from existing production code (GoogleSheetsManager, AmadeusProvider) + Twilio/Google official docs
- Pitfalls: HIGH — Traefik SSL proxy URL issue confirmed in Twilio GitHub issues; deprecated SDK issue confirmed from Google's own docs
- Validation architecture: MEDIUM — pytest assumed standard; test file paths are proposals pending project structure confirmation

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (Gemini SDK evolving fast — re-verify model names like `gemini-2.0-flash` before implementation)
