---
phase: 02-whatsapp-bot-platform
plan: 01
subsystem: api
tags: [fastapi, twilio, gemini, python, whatsapp, webhook, session-management]

# Dependency graph
requires:
  - phase: 01-site-infrastructure
    provides: Traefik + Docker deployment pattern, VPS infrastructure
provides:
  - FastAPI app with /webhook and /health endpoints
  - Twilio webhook signature validation using WEBHOOK_BASE_URL
  - Business registry (BUSINESSES dict) keyed on Twilio number
  - SessionStore with TTL-based (business_id, phone) keyed isolation
  - GeminiClient wrapper for google-genai SDK with system_instruction
  - BaseHandler abstract class and QAHandler fallback
  - whatsapp-bot project scaffold with tests
affects: [02-02-product-handler, 02-03-deployment]

# Tech tracking
tech-stack:
  added:
    - fastapi>=0.110 (async webhook HTTP server)
    - uvicorn>=0.29 (ASGI server)
    - twilio>=9.0 (webhook validation + TwiML responses)
    - google-genai>=1.0 (Gemini AI SDK - new unified SDK)
    - google-api-python-client==2.134.0 (Google Sheets)
    - google-auth>=2.0 (service account credentials)
    - httpx>=0.27 (async HTTP for Amadeus)
    - python-dotenv==1.0.1 (env file loading)
    - pydantic>=2.0 + pydantic-settings>=2.0 (config validation)
    - python-multipart>=0.0.9 (FastAPI form parsing for Twilio)
    - pytest + pytest-asyncio (test framework)
  patterns:
    - Business registry as dict keyed on Twilio number for O(1) business lookup
    - SessionStore with (business_id, phone) tuple key for isolation
    - GeminiClient injected into SessionStore (testability)
    - WEBHOOK_BASE_URL env var for reliable HTTPS URL reconstruction behind Traefik
    - FastAPI lifespan for resource initialization
    - TestClient with context manager to trigger lifespan in tests

key-files:
  created:
    - whatsapp-bot/app/main.py
    - whatsapp-bot/app/businesses.py
    - whatsapp-bot/app/session_store.py
    - whatsapp-bot/app/gemini_client.py
    - whatsapp-bot/app/config.py
    - whatsapp-bot/app/handlers/base.py
    - whatsapp-bot/app/handlers/qa.py
    - whatsapp-bot/requirements.txt
    - whatsapp-bot/pytest.ini
    - whatsapp-bot/.env.example
    - whatsapp-bot/tests/test_config.py
    - whatsapp-bot/tests/test_session_store.py
    - whatsapp-bot/tests/test_webhook.py
    - whatsapp-bot/tests/test_health.py
  modified: []

key-decisions:
  - "GeminiClient injected into SessionStore constructor (not instantiated inside) enables testing without real API calls"
  - "WEBHOOK_BASE_URL setting used for Twilio URL reconstruction instead of header inspection (reliable behind Traefik)"
  - "python-multipart added to requirements — required by FastAPI for form parsing of Twilio webhook payloads"
  - "TestClient used with context manager (with TestClient(app) as client) to trigger FastAPI lifespan in tests"
  - "SESSION_TIMEOUT_SECONDS=1800 (30 minutes) chosen as inactivity TTL"

patterns-established:
  - "Business Registry: BUSINESSES[twilio_number] -> BusinessConfig — new business = new dict entry only"
  - "Session isolation: key=(business_id, phone) prevents cross-business context bleed"
  - "Handler chain: BaseHandler.can_handle() -> BaseHandler.handle() — QAHandler always returns True (fallback)"
  - "Twilio validation: validate_twilio dependency raises 403 HTTPException on invalid signature"

requirements-completed: [PLAT-01, PLAT-03, PLAT-04, BOT-01, BOT-02]

# Metrics
duration: 4min
completed: 2026-03-24
---

# Phase 2 Plan 1: WhatsApp Bot Foundation Summary

**FastAPI service with Twilio webhook validation, Gemini AI session store, and config-driven business registry for multi-tenant WhatsApp bot**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T19:45:27Z
- **Completed:** 2026-03-24T19:49:00Z
- **Tasks:** 2
- **Files modified:** 17 created, 0 modified

## Accomplishments

- WhatsApp bot service scaffold at `whatsapp-bot/` with all core modules
- FastAPI app with /webhook (Twilio signature validation) and /health endpoints
- Business registry with 2 fully configured businesses: Punto Clave MX (e-commerce) and travel agency
- SessionStore isolating conversations by (business_id, phone) tuple with 30-minute TTL
- GeminiClient wrapper using new `google-genai` SDK with system_instruction per business
- 19 unit tests passing: business lookup, session isolation/expiry/reuse, webhook routing, health check

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold, config, business registry, session store** - `fe70ecc` (feat)
2. **Task 2: FastAPI app with Twilio webhook and signature validation** - `b4d6001` (feat)

## Files Created/Modified

- `whatsapp-bot/app/main.py` - FastAPI app, /webhook endpoint, Twilio validation, lifespan init
- `whatsapp-bot/app/businesses.py` - BusinessConfig dataclass + BUSINESSES registry (2 entries)
- `whatsapp-bot/app/session_store.py` - SessionStore with TTL-based (business_id, phone) keyed sessions
- `whatsapp-bot/app/gemini_client.py` - GeminiClient wrapping google-genai, creates chat with system_instruction
- `whatsapp-bot/app/config.py` - pydantic-settings Settings class, singleton get_settings()
- `whatsapp-bot/app/handlers/base.py` - BaseHandler abstract class
- `whatsapp-bot/app/handlers/qa.py` - QAHandler fallback (always can_handle, calls Gemini)
- `whatsapp-bot/requirements.txt` - All dependencies including python-multipart fix
- `whatsapp-bot/tests/test_config.py` - Business registry tests (5 tests)
- `whatsapp-bot/tests/test_session_store.py` - Session isolation/expiry tests (7 tests)
- `whatsapp-bot/tests/test_webhook.py` - Webhook signature, routing, TwiML tests (5 tests)
- `whatsapp-bot/tests/test_health.py` - Health endpoint tests (2 tests)

## Decisions Made

- GeminiClient injected into SessionStore constructor rather than instantiated inside — enables mocking in tests without real Gemini API calls
- `WEBHOOK_BASE_URL` env var used for Twilio URL reconstruction instead of x-forwarded-proto header inspection — more reliable behind Traefik (per research pitfall #1)
- FastAPI TestClient must be used as context manager (`with TestClient(app) as client`) to trigger `lifespan` startup and initialize `app.state.session_store`
- `python-multipart` package is required by FastAPI for form parsing — not listed in original plan requirements but needed for Twilio webhook payload parsing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing python-multipart dependency**
- **Found during:** Task 2 (webhook endpoint implementation)
- **Issue:** FastAPI requires `python-multipart` to parse `application/x-www-form-urlencoded` form data. Twilio sends webhook payloads in this format. Tests failed with `AssertionError: The python-multipart library must be installed to use form parsing.`
- **Fix:** Added `python-multipart>=0.0.9` to `requirements.txt` and installed it
- **Files modified:** `whatsapp-bot/requirements.txt`
- **Verification:** All 7 webhook and health tests pass
- **Committed in:** `b4d6001` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed TestClient lifespan not triggering**
- **Found during:** Task 2 (test execution)
- **Issue:** Test fixtures created `TestClient(app)` without using it as a context manager. FastAPI's lifespan (startup) didn't run, so `app.state.session_store` was not initialized, causing `AttributeError: 'State' object has no attribute 'session_store'`
- **Fix:** Changed test fixtures to use `with TestClient(app) as client: yield client` pattern
- **Files modified:** `whatsapp-bot/tests/test_webhook.py`, `whatsapp-bot/tests/test_health.py`
- **Verification:** All 7 tests pass with proper lifespan initialization
- **Committed in:** `b4d6001` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking dependency, 1 bug in test setup)
**Impact on plan:** Both auto-fixes necessary for functionality and testability. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviations above.

## Known Stubs

- `whatsapp-bot/app/businesses.py` line 43: `sheets_id=None` for Punto Clave MX — real Google Spreadsheet ID needed before product lookups work (Plan 02 adds ProductHandler; credentials needed before production)
- Both business `twilio_number` values are Twilio test sandbox placeholders (`+15005550006`, `+15005550007`) — must be replaced with real Twilio WhatsApp numbers when credentials are obtained

These stubs do not block Plan 01's goal (service foundation). Real credentials are documented as pending in STATE.md.

## Next Phase Readiness

- Core message pipeline ready: receive → validate → route → respond
- Plan 02 (product/flight handlers) can build on BaseHandler abstract class and QAHandler pattern
- Plan 03 (deployment) can use the /health endpoint for Docker healthcheck
- Blockers: Twilio credentials and Gemini API key still pending — bot can be built and unit-tested but production testing requires real credentials

---
*Phase: 02-whatsapp-bot-platform*
*Completed: 2026-03-24*

## Self-Check: PASSED

All created files exist on disk. Both task commits verified in git history (fe70ecc, b4d6001).
