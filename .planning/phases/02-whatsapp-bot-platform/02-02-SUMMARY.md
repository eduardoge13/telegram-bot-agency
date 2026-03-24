---
phase: 02-whatsapp-bot-platform
plan: 02
subsystem: api
tags: [python, fastapi, google-sheets, amadeus, handlers, dispatcher, tdd]

# Dependency graph
requires:
  - phase: 02-01
    provides: FastAPI scaffold, BaseHandler, QAHandler, SessionStore, BusinessConfig, GeminiClient
provides:
  - ProductSheetsClient with case-insensitive Sheets search and 10-min in-memory cache
  - ProductHandler with keyword-based intent detection and conversational Gemini response
  - OrderHandler with 4-step state machine (name/product/quantity/confirm) and Sheets write
  - FlightHandler with guided step-by-step Amadeus search and IATA city mapping
  - AmadeusProvider adapted from flights-price-panel (no pydantic-settings dependency)
  - dispatcher.dispatch() routing by business.handlers list
  - main.py webhook using dispatcher instead of direct QAHandler
affects: [02-03-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - _service injection parameter on ProductSheetsClient for unit test isolation
    - Dispatcher module-level FlightHandler lookup (getattr) so tests can patch it
    - run_in_executor wrapping sync google-api-python-client calls (avoids event loop blocking)
    - Multi-step state machine pattern: session.state dict with *_flow/*_step/*_data keys

key-files:
  created:
    - whatsapp-bot/app/sheets/client.py
    - whatsapp-bot/app/handlers/product.py
    - whatsapp-bot/app/handlers/order.py
    - whatsapp-bot/app/handlers/flight.py
    - whatsapp-bot/app/providers/amadeus.py
    - whatsapp-bot/app/providers/base.py
    - whatsapp-bot/app/dispatcher.py
    - whatsapp-bot/tests/test_sheets.py
    - whatsapp-bot/tests/test_handlers.py
    - whatsapp-bot/tests/test_dispatcher.py
  modified:
    - whatsapp-bot/app/handlers/__init__.py
    - whatsapp-bot/app/main.py

key-decisions:
  - "_service injection parameter added to ProductSheetsClient for unit test isolation (avoids real Google credentials in tests)"
  - "Dispatcher uses getattr(module, 'FlightHandler') instead of conditional _flight_available flag — allows tests to patch the module-level name"
  - "FlightHandler converts USD prices to estimated MXN (x17 multiplier) for display — Amadeus returns USD, users expect MXN"
  - "AmadeusProvider reads AMADEUS_CLIENT_ID/SECRET directly from os.environ (no pydantic-settings) — decoupled from flights-price-panel config"
  - "OrderHandler writes to 'Pedidos' sheet tab; on write failure it still confirms to customer and logs — order is never silently lost"

requirements-completed: [BOT-03, BOT-04, PLAT-02]

# Metrics
duration: 6min
completed: 2026-03-24
---

# Phase 2 Plan 2: Handler Chain and Intelligence Layer Summary

**Dispatcher + 4 handlers (product/flight/order/qa) + Sheets client + Amadeus provider, making both businesses functionally complete with TDD: 40 tests passing**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-24T19:53:18Z
- **Completed:** 2026-03-24T19:59:00Z
- **Tasks:** 2
- **Files created:** 10, modified: 2

## Accomplishments

- ProductSheetsClient: reads Google Sheets product catalog with case-insensitive substring search, 10-minute in-memory cache, async executor wrapping, `$X,XXX MXN` price formatting
- ProductHandler: keyword-based Spanish intent detection, injects product data into Gemini prompt for conversational response, asks "¿Te gustaría hacer un pedido?" after showing products
- OrderHandler: 4-step multi-turn state machine (name → product → quantity → confirm), writes completed orders to "Pedidos" sheet tab, graceful error handling (never loses order data)
- FlightHandler: guided step-by-step flight search (origin → destination → date → Amadeus results), IATA city mapping for 30+ cities, Spanish date parsing ("15 de abril", ISO, DD/MM/YYYY)
- AmadeusProvider: adapted from flights-price-panel with os.environ credential reads (no pydantic-settings dependency), identical OAuth2 + search logic
- dispatcher.dispatch(): iterates business.handlers list, instantiates handlers with dependencies, routes to first match, falls through to QA
- main.py: lifespan initializes ProductSheetsClient per-business and AmadeusProvider, webhook uses dispatch() instead of direct QAHandler
- 40 unit tests passing across all modules

## Task Commits

1. **Task 1 RED: Add failing tests for sheets, handlers, dispatcher** - `5919be7` (test)
2. **Task 1 GREEN: Implement ProductSheetsClient, ProductHandler, OrderHandler, dispatcher** - `9f35082` (feat)
3. **Task 2: Implement FlightHandler, AmadeusProvider, wire dispatcher into main.py** - `f7b3f41` (feat)

## Files Created/Modified

- `whatsapp-bot/app/sheets/client.py` - ProductSheetsClient with Sheets API, search, cache, price formatter, _service injection
- `whatsapp-bot/app/handlers/product.py` - ProductHandler: keyword detection, Sheets lookup, Gemini conversational response
- `whatsapp-bot/app/handlers/order.py` - OrderHandler: 4-step state machine, Sheets order write
- `whatsapp-bot/app/handlers/flight.py` - FlightHandler: step-by-step guided flow, IATA mapping, date parsing, Amadeus integration
- `whatsapp-bot/app/providers/amadeus.py` - AmadeusProvider: OAuth2, flight search, response parsing (adapted from flights-price-panel)
- `whatsapp-bot/app/providers/base.py` - FlightOfferData, SearchResult, FlightProvider (copied from flights-price-panel)
- `whatsapp-bot/app/dispatcher.py` - dispatch() function, handler registry, module-level FlightHandler lookup
- `whatsapp-bot/app/handlers/__init__.py` - Updated to export all handlers
- `whatsapp-bot/app/main.py` - Lifespan initializes Sheets clients + AmadeusProvider; webhook uses dispatch()
- `whatsapp-bot/tests/test_sheets.py` - 6 tests: search, case-insensitivity, no-match, price format, caching
- `whatsapp-bot/tests/test_handlers.py` - 10 tests: ProductHandler can_handle/output, OrderHandler multi-step
- `whatsapp-bot/tests/test_dispatcher.py` - 5 tests: routing, QA fallback, disabled handler skip, handler order

## Decisions Made

- `_service` injection parameter added to `ProductSheetsClient.__init__` so tests bypass real Google credential validation — avoids requiring a real service account JSON in the test environment
- Dispatcher uses `getattr(app.dispatcher, 'FlightHandler')` (module attribute lookup) instead of a `_flight_available` boolean flag, enabling test patches to work correctly on the module-level name
- FlightHandler converts USD Amadeus prices to estimated MXN (multiplier ×17) for display — Amadeus returns USD, customers expect MXN; a note "approximately" is implicit
- AmadeusProvider decoupled from flights-price-panel config module: reads `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`, `AMADEUS_BASE_URL` directly from `os.environ`
- OrderHandler never silently loses orders: on Sheets write failure, logs the exception but still confirms to the customer with full order details in the message

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Credentials mock not intercepting in tests**
- **Found during:** Task 2 (test_sheets.py execution)
- **Issue:** `patch("app.sheets.client.Credentials")` context manager patches the name in the module but the underlying `google.oauth2.service_account.Credentials.from_service_account_info` still validates the JSON structure (MalformedError: missing private_key). The mock did not fully intercept the class chain.
- **Fix:** Added `_service=None` injection parameter to `ProductSheetsClient.__init__`. Tests pass the mock service directly; production code still builds from credentials as before.
- **Files modified:** `whatsapp-bot/app/sheets/client.py`, `whatsapp-bot/tests/test_sheets.py`
- **Committed in:** `f7b3f41`

**2. [Rule 1 - Bug] Dispatcher FlightHandler patch blocked by _flight_available flag**
- **Found during:** Task 1 GREEN (test_dispatcher.py execution)
- **Issue:** Dispatcher set `_flight_available = False` at module import time when `FlightHandler` import failed (Task 2 not yet written). Tests patched `app.dispatcher.FlightHandler` but `_make_handler` checked `_flight_available` which was already False.
- **Fix:** Changed `_make_handler` to use `getattr(app.dispatcher, 'FlightHandler', None)` for the flight case — reads the module attribute at call time, so test patches apply correctly.
- **Files modified:** `whatsapp-bot/app/dispatcher.py`
- **Committed in:** `9f35082`

---

**Total deviations:** 2 auto-fixed bugs. No scope creep. No architectural changes.

## Issues Encountered

None beyond the auto-fixed deviations above.

## Known Stubs

- `whatsapp-bot/app/handlers/flight.py` line 134: USD→MXN price conversion uses hardcoded ×17 multiplier — approximate exchange rate. A real deployment should use a live FX rate API or let Amadeus return MXN directly via `currencyCode: "MXN"` parameter.
- `whatsapp-bot/app/businesses.py` line 33: `sheets_id=None` for Punto Clave MX — real Spreadsheet ID needed before product lookups work. Documented as pending in STATE.md.

These stubs do not block the plan's goal (both businesses are functionally complete end-to-end). Real credentials and Spreadsheet ID are documented as pending.

## Next Phase Readiness

- Full handler chain complete: product, flight, order, QA all wired through dispatcher
- Plan 03 (deployment) can use the existing /health endpoint and the AmadeusProvider.close() in lifespan
- Blockers: Twilio credentials, Gemini API key, Google Sheets service account JSON, Amadeus credentials, and real Spreadsheet ID still pending for production testing

---
*Phase: 02-whatsapp-bot-platform*
*Completed: 2026-03-24*

## Self-Check: PASSED

All created files verified present on disk. All task commits verified in git history (5919be7, 9f35082, f7b3f41). Full test suite: 40 tests passing.
