---
phase: 02-whatsapp-bot-platform
verified: 2026-03-24T21:00:00Z
status: human_needed
score: 14/14 automated must-haves verified
re_verification: false
human_verification:
  - test: "End-to-end WhatsApp message gets AI response in Spanish"
    expected: "Send a WhatsApp message to the Twilio sandbox number. Within 10 seconds receive a conversational AI reply in Spanish."
    why_human: "Requires Twilio credentials, Twilio Console webhook config, and Gemini API key — all pending credential provisioning. Cannot test programmatically without live external services."
  - test: "Product lookup returns real product data from Google Sheets"
    expected: "Ask the e-commerce bot about a product. The bot replies with product name, price in $X,XXX MXN format, and availability from the actual spreadsheet."
    why_human: "sheets_id=None for both businesses in businesses.py (real Spreadsheet ID not yet set). Requires GOOGLE_CREDENTIALS_JSON + a real sheets_id to test live data flow."
  - test: "Flight search returns real Amadeus results"
    expected: "Ask the travel bot about a flight. Complete the guided origin/destination/date flow. Receive up to 5 real flight offers in MXN."
    why_human: "Requires AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in VPS .env. Cannot verify Amadeus API response parsing without live credentials."
  - test: "Container auto-restarts after crash"
    expected: "docker restart whatsapp-bot on VPS — container returns to running state within 40 seconds."
    why_human: "Requires SSH access to VPS to run docker restart and confirm recovery. restart: unless-stopped is configured correctly in code."
---

# Phase 2: WhatsApp Bot Platform Verification Report

**Phase Goal:** Build and deploy the WhatsApp bot platform — a FastAPI service that receives WhatsApp messages via Twilio, routes them to AI-powered handlers (product lookup, flight search, order collection), and replies using Gemini AI. Deployed to VPS at https://bot.srv1175749.hstgr.cloud.
**Verified:** 2026-03-24T21:00:00Z
**Status:** human_needed (all automated checks PASSED; 4 items require human verification with live credentials)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Twilio webhook receives POST at /webhook and validates signature correctly | VERIFIED | `main.py` L100: `@app.post("/webhook")` with `Depends(validate_twilio)`. `validate_twilio` uses `RequestValidator` + `WEBHOOK_BASE_URL`. Test `test_signature_valid` passes. |
| 2 | Invalid Twilio signature returns 403 | VERIFIED | `main.py` L89: raises `HTTPException(status_code=403)`. Test `test_signature_invalid` passes. |
| 3 | Business registry resolves correct config by Twilio number | VERIFIED | `businesses.py`: `BUSINESSES` dict with 2 entries keyed on `whatsapp:+15005550006` and `+15005550007`. 5 tests pass in `test_config.py`. |
| 4 | Adding a third business config entry routes correctly without code change | VERIFIED | `test_new_business_no_code_change` passes: adds dict entry, resolves it, removes it. No code changes required. |
| 5 | Two sessions with different (business_id, phone) keys are isolated | VERIFIED | `session_store.py` L35: key = `(business_id, phone)`. `test_session_isolation` passes. |
| 6 | Session expires after inactivity timeout | VERIFIED | `session_store.py` L39: TTL check against `SESSION_TIMEOUT_SECONDS=1800`. `test_session_expiry` passes. |
| 7 | Gemini generates Spanish response using business system_prompt | VERIFIED | `gemini_client.py` L22: `system_instruction=system_prompt` passed to `GenerateContentConfig`. Businesses have Spanish system prompts. `QAHandler` calls `send_message_async`. |
| 8 | /health returns 200 | VERIFIED | `main.py` L94-97: `GET /health` returns `{"status": "ok", "service": "whatsapp-bot"}`. VPS live: `curl -k https://bot.srv1175749.hstgr.cloud/health` returned `{"status":"ok","service":"whatsapp-bot"}`. |
| 9 | Product search returns matching products from Google Sheets by name substring | VERIFIED | `sheets/client.py` L88-95: case-insensitive substring match on `nombre` column. 6 tests pass. |
| 10 | Bot weaves product info (name, price as $X,XXX MXN, availability) conversationally into AI response | VERIFIED | `handlers/product.py` L53-58: injects `formatted_products` into Gemini prompt with "$X,XXX MXN" format instruction. `test_product_handler_output_includes_pricing` passes. |
| 11 | Handler chain picks correct handler for product vs flight vs general intent | VERIFIED | `dispatcher.py` L46-61: iterates `business.handlers` list, calls `can_handle()`, routes to first match. 5 dispatcher tests pass. |
| 12 | Flight handler guides step-by-step: origin, destination, date, then searches Amadeus | VERIFIED | `handlers/flight.py`: state machine with steps origin→destination→date, IATA mapping, date parsing, calls `amadeus.search_flights()`. |
| 13 | Bot service container starts and /health returns 200 on VPS | VERIFIED | Live: `curl -k https://bot.srv1175749.hstgr.cloud/health` returns `{"status":"ok","service":"whatsapp-bot"}`. Container running with `restart: unless-stopped`. |
| 14 | Traefik routes https://bot.srv1175749.hstgr.cloud to the bot container | VERIFIED | `docker-compose.yml` L13-16: Traefik labels with `Host(\`bot.srv1175749.hstgr.cloud\`)`, TLS certresolver, port 3001. VPS /health responds over HTTPS with valid SSL. |

**Score:** 14/14 truths verified (automated)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `whatsapp-bot/app/main.py` | FastAPI app with /webhook and /health | VERIFIED | 152 lines. Both endpoints present. lifespan initializes session_store, sheets_clients, amadeus_provider. `dispatch()` called in webhook. |
| `whatsapp-bot/app/businesses.py` | BusinessConfig + BUSINESSES registry | VERIFIED | 53 lines. Dataclass with 7 fields. Dict with 2 fully configured entries. |
| `whatsapp-bot/app/session_store.py` | TTL session isolation | VERIFIED | 62 lines. SessionStore + ConversationSession. TTL=1800s. `get_or_create()` and `cleanup_expired()` both implemented. |
| `whatsapp-bot/app/config.py` | Pydantic-settings Settings class | VERIFIED | 38 lines. All required env vars. `get_settings()` singleton with `@lru_cache`. |
| `whatsapp-bot/app/gemini_client.py` | Gemini AI wrapper | VERIFIED | 29 lines. `create_chat()` uses `system_instruction`, `gemini-2.0-flash`, `max_output_tokens=1024`. Lazy init (no startup crash if key absent). |
| `whatsapp-bot/app/handlers/base.py` | BaseHandler abstract class | VERIFIED | 24 lines. ABC with `can_handle()` and `handle()` abstract methods. |
| `whatsapp-bot/app/handlers/qa.py` | QAHandler fallback | VERIFIED | 22 lines. `can_handle()` always True. `handle()` calls `send_message_async()`. |
| `whatsapp-bot/app/handlers/product.py` | ProductHandler with Sheets lookup | VERIFIED | 95 lines. Keyword detection, `search_product()` call, Gemini prompt injection with MXN pricing. |
| `whatsapp-bot/app/handlers/flight.py` | FlightHandler with guided Amadeus search | VERIFIED | 269 lines. Full state machine. IATA mapping 30+ cities. Spanish date parsing. `search_flights()` call. |
| `whatsapp-bot/app/handlers/order.py` | OrderHandler multi-step order collection | VERIFIED | 103 lines. 4-step state machine. `append_order()` writes to Pedidos sheet. Graceful Sheets failure (order never silently lost). |
| `whatsapp-bot/app/sheets/client.py` | ProductSheetsClient with case-insensitive search | VERIFIED | 147 lines. Sheets API v4 integration. 10-min cache. `run_in_executor` wrapping. `search_product()` and `append_order()` both implemented. |
| `whatsapp-bot/app/providers/amadeus.py` | AmadeusProvider adapted from flights-price-panel | VERIFIED | 181 lines. OAuth2 auth, `search_flights()`, `_parse_offers()`, `close()`. Reads from `os.environ` directly (decoupled). |
| `whatsapp-bot/app/dispatcher.py` | Message dispatcher routing | VERIFIED | 84 lines. `dispatch()` iterates handler chain. `_make_handler()` instantiates with dependencies. Module-level `FlightHandler` lookup enables test patching. |
| `whatsapp-bot/Dockerfile` | Multi-stage Python Docker image | VERIFIED | Multi-stage (builder + runner). Python 3.12-slim. curl HEALTHCHECK. `uvicorn` CMD on port 3001. |
| `whatsapp-bot/docker-compose.yml` | Docker Compose with Traefik labels | VERIFIED | Traefik labels for `bot.srv1175749.hstgr.cloud`, n8n_default network, env_file .env, `restart: unless-stopped`, healthcheck. |
| `whatsapp-bot/.dockerignore` | Excludes tests and dev artifacts | VERIFIED | Excludes tests/, .env, .git/, __pycache__/, *.pyc, .pytest_cache/, .mypy_cache/ |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main.py` | `businesses.py` | `BUSINESSES.get(to_number)` | WIRED | `main.py` L118: `business = BUSINESSES.get(to_number)` |
| `main.py` | `session_store.py` | `session_store.get_or_create()` | WIRED | `main.py` L126-130: `session_store.get_or_create(business_id, phone, system_prompt)` |
| `session_store.py` | `gemini_client.py` | `GeminiClient.create_chat()` | WIRED | `session_store.py` L44: `chat = self._gemini_client.create_chat(system_prompt)` |
| `dispatcher.py` | `handlers/product.py` | `handler_registry` / `_make_handler` | WIRED | `dispatcher.py` L68-69: `if name == "product": return ProductHandler(sheets_client=sheets_client)` |
| `handlers/product.py` | `sheets/client.py` | `search_product(query)` | WIRED | `product.py` L46: `products = await self._sheets.search_product(message)` |
| `handlers/flight.py` | `providers/amadeus.py` | `search_flights()` | WIRED | `flight.py` L166: `result = await self._amadeus.search_flights(...)` |
| `main.py` | `dispatcher.py` | `dispatch()` called in webhook | WIRED | `main.py` L138: `reply_text = await dispatch(business, session, message, sheets_clients, amadeus_provider)` |
| `docker-compose.yml` | Traefik on VPS | Docker labels on n8n_default network | WIRED | Labels verified in docker-compose.yml. VPS /health responds over HTTPS confirming Traefik routing active. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `handlers/product.py` | `products` | `ProductSheetsClient.search_product()` → Google Sheets API | Yes, when `sheets_id` is set | CONDITIONAL — flows when `sheets_id` provided; `sheets_id=None` in both business configs (pending real Spreadsheet ID). Handler gracefully returns no-match Gemini prompt when `sheets_id=None` causes empty results. |
| `handlers/flight.py` | `result.offers` | `AmadeusProvider.search_flights()` → Amadeus REST API | Yes, when AMADEUS credentials set | CONDITIONAL — flows when env vars populated on VPS. `AmadeusProvider` init raises `KeyError` if missing (caught in lifespan, provider set to None). FlightHandler returns graceful "service unavailable" when `_amadeus is None`. |
| `handlers/qa.py` | `response.text` | `session.chat.send_message_async()` → Gemini API | Yes, when GEMINI_API_KEY set | CONDITIONAL — `GeminiClient.__init__` sets `_client=None` if `api_key` empty; `create_chat()` raises `RuntimeError` when called. Handled at dispatch level. |
| `main.py` /health | `{"status": "ok"}` | Hardcoded | Yes — returns static health object | VERIFIED — static health response by design. |

Note: All conditional data flows are properly guarded with graceful degradation. The platform is designed to start without credentials and activate when they are provisioned on VPS.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| /health endpoint returns 200 with correct JSON | `curl -sk https://bot.srv1175749.hstgr.cloud/health` | `{"status":"ok","service":"whatsapp-bot"}` | PASS |
| All 40 unit tests pass | `cd whatsapp-bot && python3 -m pytest tests/ -x` | `40 passed in 0.84s` | PASS |
| Business registry resolves puntoclave by Twilio number | `test_business_lookup` in pytest | PASSED | PASS |
| Session isolation by (business_id, phone) key | `test_session_isolation` in pytest | PASSED | PASS |
| Dispatcher routes product message to ProductHandler | `test_dispatcher_routes_product_for_puntoclave` | PASSED | PASS |
| End-to-end WhatsApp message → AI response | Requires live Twilio + Gemini credentials | N/A | SKIP — human required |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| INFRA-05 | 02-03-PLAN | WhatsApp bot service running on VPS port 3001 | SATISFIED | Container running on VPS port 3001. Traefik routes HTTPS traffic. `/health` returns 200 from `https://bot.srv1175749.hstgr.cloud`. |
| BOT-01 | 02-01-PLAN | Express/FastAPI server receives Twilio webhook messages with signature validation | SATISFIED | `main.py`: `/webhook` endpoint with `validate_twilio` dependency using `RequestValidator`. Tests `test_signature_valid` and `test_signature_invalid` both pass. |
| BOT-02 | 02-01-PLAN | Gemini AI generates contextual responses in Spanish based on business system prompt | SATISFIED | `gemini_client.py`: `system_instruction=system_prompt` in `GenerateContentConfig`. Both business configs have Spanish `system_prompt`. QAHandler calls Gemini. |
| BOT-03 | 02-02-PLAN | Bot looks up product info from Google Sheets when customer asks about products | SATISFIED | `sheets/client.py`: full Sheets API integration with `search_product()`. `product.py` calls it and injects results into Gemini prompt. 6 Sheets tests + handler tests pass. |
| BOT-04 | 02-02-PLAN | Bot sends formatted product details (name, price, availability) via WhatsApp | SATISFIED | `product.py` `_format_products()`: formats as `$X,XXX MXN` with availability string. Injected into Gemini prompt. TwiML response returned to Twilio. |
| PLAT-01 | 02-01-PLAN | Business context registry — config-driven system with Twilio number, system prompt, Sheets ID, enabled features | SATISFIED | `businesses.py`: `BusinessConfig` dataclass. `BUSINESSES` dict with 2 fully configured entries. `test_business_lookup` and `test_business_config_has_required_fields` pass. |
| PLAT-02 | 02-02-PLAN | Message handler architecture is modular (separate handlers for product lookup, Q&A, etc.) | SATISFIED | `handlers/`: 5 handlers (base, qa, product, flight, order). `dispatcher.py` iterates `business.handlers` list. `handlers/__init__.py` exports all. Adding handler = new class + registry entry. |
| PLAT-03 | 02-01-PLAN | Conversation context isolation — state keyed on (businessId, customerPhone), no cross-business bleed | SATISFIED | `session_store.py` L35: `key = (business_id, phone)`. `test_session_isolation` verifies two sessions with same phone but different business_id are independent objects. |
| PLAT-04 | 02-01-PLAN | New business onboarding requires only config changes for basic Q&A + product lookup | SATISFIED | `test_new_business_no_code_change` adds a third entry to `BUSINESSES` dict and resolves it without any code change. Business handlers list is config-driven. |

All 9 required requirement IDs are covered. No orphaned requirements found in REQUIREMENTS.md for Phase 2.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app/businesses.py` | 33, 50 | `sheets_id=None` for both business configs | Warning | Product lookup is disabled at runtime until a real Google Spreadsheet ID is added. Handler gracefully returns no-match prompt. Does NOT block core bot operation or PLAT-01/04 goals. |
| `app/handlers/flight.py` | 192 | Hardcoded USD→MXN multiplier `* 17` | Info | Approximate exchange rate used for display. Does not break functionality. Documented in SUMMARY as known limitation. |
| `app/session_store.py` | (config) | Twilio test numbers `+15005550006`, `+15005550007` as placeholders | Info | Production numbers pending Twilio credentials. Webhook routing logic correct; numbers are config values not code. |

No stub implementations (empty return, placeholder text, no-op handlers) found in source code. All handlers have substantive implementations with real logic, error handling, and test coverage.

---

### Human Verification Required

#### 1. End-to-End WhatsApp Messaging

**Test:** With Twilio credentials configured on VPS, send a WhatsApp message to the Twilio sandbox number. Ask about a product (e.g. "¿Cuánto cuesta una laptop?")
**Expected:** Receive a conversational AI response in Spanish within 10 seconds. Response should be in TwiML format and delivered via WhatsApp.
**Why human:** Requires Twilio account credentials, Twilio Console webhook configuration pointing to `https://bot.srv1175749.hstgr.cloud/webhook`, and GEMINI_API_KEY in VPS .env file. All are pending credential provisioning per STATE.md.

#### 2. Product Lookup with Real Google Sheets Data

**Test:** After adding a real `sheets_id` (Google Spreadsheet ID) to `businesses.py` and deploying, ask the e-commerce bot about a product that exists in the sheet.
**Expected:** Bot replies mentioning the product by name, price in `$X,XXX MXN` format, and availability.
**Why human:** `sheets_id=None` in both business configs. Requires a real Spreadsheet with products and GOOGLE_CREDENTIALS_JSON service account key.

#### 3. Flight Search End-to-End via Amadeus

**Test:** With Amadeus credentials configured, ask the travel bot "quiero buscar un vuelo". Complete the guided flow: provide origin city, destination, date. Receive flight results.
**Expected:** Bot guides step-by-step, shows up to 5 flight options with airline, MXN price, stops, duration.
**Why human:** Requires AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in VPS .env. AmadeusProvider `__init__` raises KeyError without them (caught gracefully, but flight search returns "service unavailable" message).

#### 4. Container Auto-Restart After Crash

**Test:** SSH into VPS. Run `docker restart whatsapp-bot`. Wait and check `docker ps | grep whatsapp-bot`.
**Expected:** Container returns to `Up` status within 40 seconds (start-period in healthcheck). `curl -k https://bot.srv1175749.hstgr.cloud/health` returns 200 again.
**Why human:** Requires SSH access to VPS. The `restart: unless-stopped` policy is correctly configured in code; this test confirms it works end-to-end on the actual VPS environment.

---

### Gaps Summary

No blocking gaps found. All automated checks passed.

The platform is fully built and deployed. The 4 human verification items are not gaps in the implementation — they require live external service credentials (Twilio, Gemini, Google Sheets, Amadeus) that are documented as pending in STATE.md. The code handles all credential-absent cases gracefully:
- No credentials: container starts, /health returns 200, bot replies with graceful error messages
- Credentials added to VPS .env + `docker compose restart`: full functionality activates without code changes

The one noteworthy pending item for product lookup is `sheets_id=None` in `businesses.py` for both businesses. This must be updated with a real Google Spreadsheet ID before product lookup works in production. The bot operates correctly without it (falls through to QA handler).

---

_Verified: 2026-03-24T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
