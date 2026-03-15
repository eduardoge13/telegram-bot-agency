# Architecture Research — Spike Agency Platform

**Researched:** 2026-03-14
**Confidence:** MEDIUM (codebase analysis HIGH; deployment patterns MEDIUM)

## System Overview

Two repos, two services on one VPS, shared AI engine (Gemini), shared data layer (Google Sheets).

```
                    ┌─────────────────────────────┐
                    │     Hostinger VPS            │
                    │     72.60.228.135            │
                    │                              │
   Internet ──nginx─┤  :3000 Next.js (e-commerce)  │
                    │  :3001 WhatsApp Bot (Express) │
                    │                              │
                    └──────────┬──────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        Google Sheets    Gemini API      External APIs
        (products,       (AI responses)  (Stripe, MP,
         orders,                         Twilio, Amadeus)
         clients)
```

## Component Boundaries

### 1. Next.js E-commerce (spike-ecommerce-web)
- **Serves:** Punto Clave MX website
- **Port:** 3000
- **Responsibilities:**
  - Product catalog display
  - Stripe Checkout Session creation (API route)
  - Mercado Pago Preference creation (API route)
  - Payment webhook handling (API routes)
  - Order confirmation pages
- **Does NOT:** Handle WhatsApp messages, AI conversations, flight search

### 2. WhatsApp Bot Service (telegram-bot-agency or new service)
- **Serves:** Customer WhatsApp conversations for multiple businesses
- **Port:** 3001
- **Responsibilities:**
  - Twilio webhook receiver (Express)
  - Gemini AI conversation engine
  - Google Sheets data queries
  - Amadeus flight search
  - Multi-business context routing
  - Field editing (admin commands)
- **Does NOT:** Serve web pages, handle web payments directly

### 3. Telegram Bot (existing, stays as-is)
- **Serves:** Internal/team use
- **Runs:** Current hosting (unchanged)
- **Note:** Not migrated to VPS. Separate concern.

## Multi-Tenant Architecture

Business context resolves from the Twilio `To` phone number:

```
BUSINESS_CONTEXTS = {
  "+5572408666": {
    name: "Punto Clave MX",
    systemPrompt: "You are a tech product sales assistant...",
    sheetsId: "SHEETS_ID_TECH_STORE",
    features: ["product_lookup", "order_status", "field_edit"],
  },
  "+55XXXXXXXX": {
    name: "Travel Agency",
    systemPrompt: "You are a flight search assistant...",
    sheetsId: "SHEETS_ID_TRAVEL",
    features: ["flight_search", "general_qa"],
  }
}
```

- One Twilio number per business (simplest routing)
- Context passed per-request, never stored as global state
- Feature flags control which capabilities each business gets

## Data Flow

### Customer → WhatsApp Bot → Response
```
1. Customer sends WhatsApp message
2. Twilio POSTs webhook to VPS :3001/webhook/whatsapp
3. Express validates Twilio signature
4. Router resolves business context from To number
5. Handler checks message type (product query, flight search, order status, etc.)
6. If product query → Google Sheets lookup → format response
7. If general Q&A → Gemini API with business system prompt → response
8. If flight search → Amadeus API → format results
9. Send response via Twilio REST API
```

### Customer → Website → Payment
```
1. Customer browses products on Next.js site
2. Clicks "Pay with Stripe" or "Pay with Mercado Pago"
3. Next.js API route creates checkout session/preference
4. Customer redirected to Stripe/MP hosted checkout
5. Customer completes payment
6. Stripe/MP sends webhook to Next.js API route
7. Webhook handler logs order to Google Sheets
8. Customer redirected to confirmation page
```

## VPS Deployment Architecture

```
nginx (port 80/443)
├── puntoclavemx.com → proxy_pass localhost:3000 (Next.js)
├── puntoclavemx.com/api/webhooks/whatsapp → proxy_pass localhost:3001
└── SSL termination via Certbot/Let's Encrypt

PM2 ecosystem
├── spike-ecommerce-web (Next.js standalone, port 3000)
└── whatsapp-bot (Express, port 3001)
```

**HTTPS is mandatory:** Both Twilio webhooks and Stripe/MP webhooks require HTTPS. Certbot + nginx handles this. A domain name is needed for free SSL (can't get Let's Encrypt cert for raw IP).

## WhatsApp Bot Service Structure (Recommended)

```
whatsapp-bot/
├── src/
│   ├── index.ts              # Express server + Twilio webhook route
│   ├── routes/
│   │   └── webhook.ts        # POST /webhook/whatsapp handler
│   ├── handlers/
│   │   ├── message.ts        # Route message to correct handler
│   │   ├── product.ts        # Product lookup from Sheets
│   │   ├── flight.ts         # Amadeus flight search
│   │   ├── order.ts          # Order status lookup
│   │   └── admin.ts          # Field editing commands
│   ├── services/
│   │   ├── gemini.ts         # Gemini AI wrapper
│   │   ├── sheets.ts         # Google Sheets client
│   │   ├── amadeus.ts        # Amadeus API client
│   │   └── twilio.ts         # Twilio message sender
│   └── context/
│       ├── registry.ts       # Business context registry
│       └── conversation.ts   # Conversation state management
├── package.json
└── tsconfig.json
```

**Key principle:** Don't repeat the monolithic pattern from the Telegram bot. Separate handlers from services from routes.

## Build Order (Dependencies)

```
Phase 1: VPS Infrastructure
  └── nginx + PM2 + Node.js + Certbot/HTTPS
       └── Required by: everything else

Phase 2: E-commerce Fixes + Deploy
  └── WhatsApp number fix + Stripe/MP checkout + Deploy to VPS
       └── Required by: payment links via bot

Phase 3: WhatsApp Bot
  └── Twilio webhook + Gemini AI + Sheets + multi-tenant
       └── Required by: flight search, order tracking

Phase 4: Advanced Features
  └── Amadeus flights + order tracking + payment links via bot
```

## Open Questions
- Does Hostinger VPS support `systemd` for `pm2 startup`? (Verify on first SSH)
- Twilio sandbox vs production number? (Sandbox requires pairing step)
- Domain name for the VPS? (Needed for free SSL cert)
- Will WhatsApp bot code live in this repo or a third repo?

---
*Researched: 2026-03-14*
