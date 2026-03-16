# Phase 2: WhatsApp Bot Platform - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Multi-tenant WhatsApp bot live on VPS, receiving Twilio webhooks, responding in Spanish via Gemini AI, and looking up products from Google Sheets. Two businesses configured: Punto Clave MX (e-commerce) and a travel agency (flight search via Amadeus API). Adding a new business requires only a config entry — no code changes. Deployment on the existing Hostinger VPS using Traefik + Docker.

</domain>

<decisions>
## Implementation Decisions

### Conversation Flow
- Free-form AI chat — no menus, no guided flows for e-commerce. Customer writes naturally, Gemini interprets intent
- Auto-detect product intent — Gemini recognizes "quiero una laptop" or "cuánto cuesta X?" and triggers Google Sheets search automatically
- When product not found: suggest similar products (partial match) and offer to connect with a human
- Session memory: retain last ~10 messages per conversation for context. Customer can say "y el otro?" and bot understands. Resets after inactivity

### Product Presentation
- Conversational inline format — product info woven naturally into the AI response, not a structured card
- Example: "El MacBook Pro está a $25,999 MXN y sí lo tenemos disponible"
- Prices displayed as $25,999 MXN (dollar sign, comma separators, MXN suffix)
- After showing product info, bot proactively asks "¿Te gustaría hacer un pedido?"

### Order Handling (MVP)
- Bot collects basic order info: customer name, product, quantity
- Order saved to Google Sheets
- Business owner notified (via Telegram bot or flag in the sheet)
- No in-chat payment — order collection only

### Multi-Business Architecture
- Both businesses fully configured and live from day one: Punto Clave MX + travel agency
- Separate Twilio WhatsApp numbers per business — config maps incoming number → business context
- Each business defined by: Twilio number, system prompt, Google Sheets ID, enabled features/handlers
- New business onboarding requires only a config entry

### Travel Agency — Flight Search
- Uses real Amadeus API integration from existing `flights-price-panel` project (`/Users/eduardogaitan/Documents/projects/flights-price-panel`)
- Guided step-by-step flow: bot asks "¿De dónde sales?" → "¿A dónde vas?" → "¿Fecha?" → searches Amadeus
- Present top 3-5 cheapest flight options with airline, price, stops, duration
- Existing `AmadeusProvider` class has: OAuth2 auth, flight search, response parsing — reuse directly

### Claude's Discretion
- Bot personality and tone (formal/informal Spanish)
- Technical architecture (language choice, framework, project structure)
- How to integrate AmadeusProvider into the WhatsApp bot service
- Session timeout duration
- Error handling and retry strategies
- Notification mechanism for orders (Telegram vs Sheets flag)
- Exact system prompts per business

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `bot_telegram_polling.py` → `GoogleSheetsManager` class: Full Google Sheets integration with caching, retry, async wrappers — pattern to replicate for WhatsApp bot
- `bot_telegram_polling.py` → Gemini AI integration: System prompt + context-aware responses in Spanish — blueprint for WhatsApp AI
- `flights-price-panel/app/providers/amadeus.py` → `AmadeusProvider`: Working Amadeus flight search with OAuth2, async httpx, response parsing
- `flights-price-panel/app/providers/base.py` → `FlightProvider` base class + `FlightOfferData`/`SearchResult` data models
- `flights-price-panel/app/config.py` → Settings with Amadeus credentials (client_id, client_secret, base_url)

### Established Patterns
- Python + async for bot services (existing Telegram bot is Python 3.12)
- Google Sheets as data store via `google-api-python-client`
- GCP Secret Manager for credentials (may switch to env vars for VPS deployment)
- Health check endpoints via Flask
- Docker containerization for deployment

### Integration Points
- VPS uses Traefik (not nginx) — new service needs Docker labels + n8n_default network
- Bot service on port 3001 per INFRA-05 requirement
- Twilio webhook URL: needs HTTPS endpoint on VPS for incoming WhatsApp messages
- Google Sheets: same client data sheet (SPREADSHEET_ID) for Punto Clave MX products
- Amadeus API: credentials from flights-price-panel config (amadeus_client_id, amadeus_client_secret)

</code_context>

<specifics>
## Specific Ideas

- User has a working Amadeus integration in `/Users/eduardogaitan/Documents/projects/flights-price-panel` — reuse the `AmadeusProvider` class directly rather than building from scratch
- Travel agency flight search should feel guided (step-by-step questions), not free-form, to avoid misinterpreting cities/dates
- E-commerce bot should feel like texting a real person — conversational, not robotic
- Order collection is MVP — no payment processing in the bot

</specifics>

<deferred>
## Deferred Ideas

- Payment links via WhatsApp (PAY-05) — v2
- Order status tracking via WhatsApp (ADV-02) — v2
- Working-hours awareness with auto-reply (ADV-04) — v2
- Admin field editing via WhatsApp (ADV-03) — v2

</deferred>

---

*Phase: 02-whatsapp-bot-platform*
*Context gathered: 2026-03-16*
